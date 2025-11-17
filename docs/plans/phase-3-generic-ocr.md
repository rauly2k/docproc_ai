# Phase 3: Generic OCR Implementation (Week 6)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement generic OCR for any document type using hybrid approach (Document AI, Vision API, Gemini Vision).

**Duration:** 1 week (40 hours)

**Prerequisites:** Phase 2 completed (invoice processing working)

---

## Task 3.1: OCR Worker Service (6 hours)

**Files:**
- Create: `backend/workers/ocr_worker/Dockerfile`
- Create: `backend/workers/ocr_worker/main.py`
- Create: `backend/workers/ocr_worker/ocr_methods.py`
- Create: `scripts/deploy-ocr-worker.sh`

**Step 1: Create OCR methods module**

Create file: `backend/workers/ocr_worker/ocr_methods.py`

```python
"""Multiple OCR methods for different document types."""

from google.cloud import documentai_v1 as documentai, vision, storage
from google.api_core.client_options import ClientOptions
from vertexai.preview.generative_models import GenerativeModel, Part
from typing import Dict, Any
import os

from backend.shared.config import get_settings

settings = get_settings()


class OCRProcessor:
    """Hybrid OCR processor using multiple methods."""

    def __init__(self):
        self.project_id = settings.project_id
        self.location = "us"

        # Document AI client
        opts = ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com")
        self.documentai_client = documentai.DocumentProcessorServiceClient(client_options=opts)

        # Vision API client
        self.vision_client = vision.ImageAnnotatorClient()

        # Gemini model
        self.gemini_model = GenerativeModel("gemini-1.5-flash")

        # OCR processor ID
        self.ocr_processor_id = os.getenv("DOCUMENTAI_OCR_PROCESSOR_ID")

    def process_document(self, gcs_uri: str, method: str = "auto") -> Dict[str, Any]:
        """
        Process document with specified OCR method.

        Args:
            gcs_uri: GCS URI of document
            method: OCR method to use (auto, documentai, vision, gemini)

        Returns:
            Extracted text and metadata
        """
        if method == "auto":
            # Auto-select based on file type
            method = self._select_best_method(gcs_uri)

        if method == "documentai":
            return self._ocr_with_documentai(gcs_uri)
        elif method == "vision":
            return self._ocr_with_vision(gcs_uri)
        elif method == "gemini":
            return self._ocr_with_gemini(gcs_uri)
        else:
            raise ValueError(f"Unknown OCR method: {method}")

    def _select_best_method(self, gcs_uri: str) -> str:
        """Auto-select best OCR method based on file."""
        # For MVP, default to Document AI
        # Future: analyze file and choose method
        return "documentai"

    def _ocr_with_documentai(self, gcs_uri: str) -> Dict[str, Any]:
        """OCR using Document AI OCR Processor."""
        processor_name = self.documentai_client.processor_path(
            self.project_id, self.location, self.ocr_processor_id
        )

        request = documentai.ProcessRequest(
            name=processor_name,
            gcs_document=documentai.GcsDocument(
                gcs_uri=gcs_uri,
                mime_type="application/pdf"
            )
        )

        result = self.documentai_client.process_document(request=request)
        document = result.document

        return {
            "extracted_text": document.text,
            "confidence_score": self._calculate_confidence(document),
            "page_count": len(document.pages),
            "ocr_method": "document-ai",
            "layout_data": self._extract_layout(document),
        }

    def _ocr_with_vision(self, gcs_uri: str) -> Dict[str, Any]:
        """OCR using Vision API."""
        image = vision.Image()
        image.source.image_uri = gcs_uri

        response = self.vision_client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")

        text = response.full_text_annotation.text if response.full_text_annotation else ""

        return {
            "extracted_text": text,
            "confidence_score": 0.95,  # Vision API doesn't provide per-doc confidence
            "page_count": len(response.full_text_annotation.pages) if response.full_text_annotation else 1,
            "ocr_method": "vision-api",
            "layout_data": None,
        }

    def _ocr_with_gemini(self, gcs_uri: str) -> Dict[str, Any]:
        """OCR using Gemini Vision (best for handwritten/messy docs)."""
        # Load image from GCS
        image_part = Part.from_uri(gcs_uri, mime_type="image/jpeg")

        prompt = """Extract all text from this image.
        Return only the text content, maintaining the original layout and formatting.
        Do not add any commentary or explanations."""

        response = self.gemini_model.generate_content([prompt, image_part])
        extracted_text = response.text

        return {
            "extracted_text": extracted_text,
            "confidence_score": 0.90,  # Estimate
            "page_count": 1,
            "ocr_method": "gemini-vision",
            "layout_data": None,
        }

    @staticmethod
    def _calculate_confidence(document: documentai.Document) -> float:
        """Calculate average confidence from Document AI response."""
        if not document.pages:
            return 0.0

        confidences = []
        for page in document.pages:
            for token in page.tokens:
                if token.layout and token.layout.confidence:
                    confidences.append(token.layout.confidence)

        return sum(confidences) / len(confidences) if confidences else 0.0

    @staticmethod
    def _extract_layout(document: documentai.Document) -> Dict[str, Any]:
        """Extract layout information from Document AI response."""
        layout = {
            "pages": [],
            "blocks": [],
            "paragraphs": [],
        }

        for page in document.pages:
            page_data = {
                "page_number": page.page_number,
                "width": page.dimension.width if page.dimension else 0,
                "height": page.dimension.height if page.dimension else 0,
            }
            layout["pages"].append(page_data)

        return layout
```

**Step 2: Create OCR worker main application**

Create file: `backend/workers/ocr_worker/main.py`

```python
"""OCR worker service - extracts text from documents."""

from fastapi import FastAPI, Request, HTTPException
from sqlalchemy.orm import Session
import json
from datetime import datetime
import traceback
import base64

from backend.shared.database import SessionLocal
from backend.shared.models import Document, OCRResult, AuditLog
from backend.shared.config import get_settings
from .ocr_methods import OCRProcessor

settings = get_settings()
app = FastAPI(title="OCR Worker")

# Initialize processor
ocr_processor = OCRProcessor()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ocr-worker"}


@app.post("/process")
async def process_ocr(request: Request):
    """Process OCR from Pub/Sub push subscription."""
    try:
        envelope = await request.json()
        message_data = envelope["message"]["data"]
        message_json = base64.b64decode(message_data).decode("utf-8")
        message = json.loads(message_json)

        tenant_id = message["tenant_id"]
        user_id = message["user_id"]
        document_id = message["document_id"]
        gcs_path = message["gcs_path"]

        print(f"Processing OCR: {document_id} from {gcs_path}")

        db = SessionLocal()

        try:
            # Get document
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Update status
            document.status = "processing"
            document.processing_started_at = datetime.utcnow()
            db.commit()

            # Process with OCR
            print(f"Running OCR on {gcs_path}")
            result = ocr_processor.process_document(gcs_path, method="auto")

            # Save OCR result
            ocr_result = OCRResult(
                document_id=document_id,
                tenant_id=tenant_id,
                extracted_text=result["extracted_text"],
                confidence_score=result["confidence_score"],
                page_count=result["page_count"],
                ocr_method=result["ocr_method"],
                layout_data=result.get("layout_data"),
            )
            db.add(ocr_result)

            # Update document
            document.status = "completed"
            document.ocr_completed = True
            document.processing_completed_at = datetime.utcnow()

            # Audit log
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                document_id=document_id,
                action="ocr_completed",
                details={
                    "method": result["ocr_method"],
                    "page_count": result["page_count"],
                    "confidence": result["confidence_score"],
                }
            )
            db.add(audit_log)

            db.commit()

            print(f"OCR completed: {document_id}")
            return {"status": "success", "document_id": str(document_id)}

        except Exception as e:
            document.status = "failed"
            document.error_message = str(e)
            document.processing_completed_at = datetime.utcnow()
            db.commit()
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            db.close()

    except Exception as e:
        print(f"Error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

**Step 3: Create Document AI OCR processor**

```bash
# In Cloud Console: Document AI > Create Processor > OCR Processor
# Name: ocr-processor
# Region: us
# Copy processor ID and store:

echo "YOUR_OCR_PROCESSOR_ID" | gcloud secrets create documentai-ocr-processor-id \
  --data-file=- \
  --replication-policy=automatic
```

**Step 4: Create Dockerfile**

Create file: `backend/workers/ocr_worker/Dockerfile`

```dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY ../../shared/ /app/backend/shared/
COPY . /app/backend/workers/ocr_worker/
WORKDIR /app/backend/workers/ocr_worker
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

**Step 5: Deploy OCR worker**

Create file: `scripts/deploy-ocr-worker.sh`

```bash
#!/bin/bash
set -e

PROJECT_ID="docai-mvp-prod"
REGION="europe-west1"
SERVICE_NAME="ocr-worker"
IMAGE_NAME="europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/$SERVICE_NAME"

cd backend
docker build -t $IMAGE_NAME:latest -f workers/ocr_worker/Dockerfile .
docker push $IMAGE_NAME:latest

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --service-account ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,REGION=$REGION,ENVIRONMENT=prod \
  --set-secrets DATABASE_URL=database-url:latest,DB_PASSWORD=database-password:latest,DOCUMENTAI_OCR_PROCESSOR_ID=documentai-ocr-processor-id:latest \
  --min-instances 0 \
  --max-instances 5 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 1

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')

gcloud pubsub subscriptions create ocr-processing-sub \
  --topic=ocr-processing \
  --push-endpoint="$SERVICE_URL/process" \
  --push-auth-service-account=ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=600 \
  --message-retention-duration=7d

echo "Deployment complete!"
```

```bash
chmod +x scripts/deploy-ocr-worker.sh
./scripts/deploy-ocr-worker.sh
```

**Step 6: Commit**

```bash
git add backend/workers/ocr_worker/ scripts/deploy-ocr-worker.sh
git commit -m "feat: add OCR worker with hybrid method support"
```

---

## Task 3.2: OCR API Endpoints & UI (4 hours)

**Files:**
- Create: `backend/api_gateway/routes/ocr.py`
- Create: `frontend/src/components/OCR/OCRResults.tsx`
- Create: `frontend/src/pages/OCRDocuments.tsx`

**Step 1: Create OCR API routes**

Create file: `backend/api_gateway/routes/ocr.py`

```python
"""OCR routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from backend.shared.database import get_db
from backend.shared.models import Document, OCRResult
from backend.shared.schemas import DocumentResponse
from backend.shared.auth import verify_firebase_token, get_tenant_id_from_token
from backend.shared.pubsub import PubSubPublisher

router = APIRouter()
pubsub_publisher = PubSubPublisher()


@router.post("/{document_id}/extract", status_code=202)
async def extract_text(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Trigger OCR extraction for document."""
    tenant_id = get_tenant_id_from_token(token_data)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Publish to Pub/Sub
    message = {
        "tenant_id": str(tenant_id),
        "user_id": str(document.user_id),
        "document_id": str(document_id),
        "gcs_path": document.gcs_path,
        "document_type": document.document_type,
        "filename": document.filename,
    }

    pubsub_publisher.publish_ocr_processing(message)

    return {"message": "OCR extraction started", "document_id": str(document_id)}


@router.get("/{document_id}")
async def get_ocr_result(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Get OCR extraction result."""
    tenant_id = get_tenant_id_from_token(token_data)

    ocr_result = db.query(OCRResult).filter(
        OCRResult.document_id == document_id,
        OCRResult.tenant_id == tenant_id
    ).first()

    if not ocr_result:
        raise HTTPException(status_code=404, detail="OCR result not found")

    return {
        "id": str(ocr_result.id),
        "document_id": str(ocr_result.document_id),
        "extracted_text": ocr_result.extracted_text,
        "confidence_score": float(ocr_result.confidence_score) if ocr_result.confidence_score else None,
        "page_count": ocr_result.page_count,
        "ocr_method": ocr_result.ocr_method,
        "created_at": ocr_result.created_at.isoformat(),
    }
```

**Step 2: Add OCR router to main app**

Edit `backend/api_gateway/main.py`:

```python
from .routes import auth, documents, invoices, ocr

app.include_router(ocr.router, prefix="/v1/ocr", tags=["OCR"])
```

**Step 3: Create OCR results component**

Create file: `frontend/src/components/OCR/OCRResults.tsx`

```typescript
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface OCRResultsProps {
  documentId: string;
}

export const OCRResults: React.FC<OCRResultsProps> = ({ documentId }) => {
  const { data: ocrResult, isLoading, error } = useQuery({
    queryKey: ['ocr', documentId],
    queryFn: () => apiClient.getOCRResult(documentId),
  });

  if (isLoading) return <div>Loading OCR results...</div>;
  if (error) return <div>OCR not completed yet</div>;

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="mb-4">
        <h3 className="text-lg font-medium">Extracted Text</h3>
        <div className="text-sm text-gray-500">
          Method: {ocrResult.ocr_method} •
          Pages: {ocrResult.page_count} •
          Confidence: {(ocrResult.confidence_score * 100).toFixed(1)}%
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded border border-gray-200">
        <pre className="whitespace-pre-wrap text-sm font-mono">
          {ocrResult.extracted_text}
        </pre>
      </div>

      <div className="mt-4 flex space-x-2">
        <button
          onClick={() => navigator.clipboard.writeText(ocrResult.extracted_text)}
          className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        >
          Copy to Clipboard
        </button>
        <button
          onClick={() => {
            const blob = new Blob([ocrResult.extracted_text], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `extracted-text-${documentId}.txt`;
            a.click();
          }}
          className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Download as TXT
        </button>
      </div>
    </div>
  );
};
```

**Step 4: Add OCR methods to API client**

Edit `frontend/src/services/api.ts`:

```typescript
async getOCRResult(documentId: string) {
  const response = await this.client.get(`/ocr/${documentId}`);
  return response.data;
}

async extractText(documentId: string) {
  const response = await this.client.post(`/ocr/${documentId}/extract`);
  return response.data;
}
```

**Step 5: Deploy and test**

```bash
./scripts/deploy-api-gateway.sh
npm run dev
```

Test: Upload generic document, extract text, view results

**Step 6: Commit**

```bash
git add backend/api_gateway/routes/ocr.py frontend/src/components/OCR/ frontend/src/services/api.ts
git commit -m "feat: add OCR API endpoints and results UI"
```

---

## Phase 3 Complete ✓

**Summary:** Generic OCR implemented
- ✅ Hybrid OCR approach (Document AI, Vision API, Gemini)
- ✅ OCR worker deployed
- ✅ Text extraction API
- ✅ OCR results display UI
- ✅ Copy and download functionality

**Next:** Phase 4 - Text Summarization (Week 7)
