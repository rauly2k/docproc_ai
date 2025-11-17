# Phase 4: Text Summarization Implementation (Week 7)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement document summarization using Vertex AI (Gemini Flash/Pro and Claude) with quality selection and key points extraction.

**Duration:** 1 week (40 hours)

**Prerequisites:** Phase 3 completed (OCR working)

---

## Task 4.1: Summarizer Worker Service Setup (6 hours)

**Files:**
- Create: `backend/workers/summarizer_worker/Dockerfile`
- Create: `backend/workers/summarizer_worker/main.py`
- Create: `backend/workers/summarizer_worker/summarizer.py`
- Create: `backend/workers/summarizer_worker/requirements.txt`

**Step 1: Create summarizer requirements**

Create file: `backend/workers/summarizer_worker/requirements.txt`

```txt
# Inherit from parent
-r ../../requirements.txt

# Additional dependencies
PyPDF2==3.0.1
langchain==0.0.340
langchain-google-vertexai==0.0.6
```

**Step 2: Create summarizer processor module**

Create file: `backend/workers/summarizer_worker/summarizer.py`

```python
"""Document summarization using Vertex AI (Gemini and Claude)."""

from google.cloud import storage
from vertexai.preview.generative_models import GenerativeModel
import vertexai
import PyPDF2
import io
from typing import Dict, Any, List
import re

from backend.shared.config import get_settings

settings = get_settings()


class DocumentSummarizer:
    """Summarize documents using Vertex AI models."""

    def __init__(self):
        # Initialize Vertex AI
        vertexai.init(project=settings.project_id, location=settings.vertex_ai_location)

        # Initialize models
        self.flash_model = GenerativeModel("gemini-1.5-flash")
        self.pro_model = GenerativeModel("gemini-1.5-pro")

        # Storage client
        self.storage_client = storage.Client()

        # Model configurations
        self.generation_config = {
            "temperature": 0.3,  # Lower temperature for more focused summaries
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

    def summarize_document(
        self,
        gcs_uri: str,
        model_preference: str = "flash",
        summary_type: str = "concise"
    ) -> Dict[str, Any]:
        """
        Summarize document from GCS.

        Args:
            gcs_uri: GCS URI of document
            model_preference: "flash" (fast), "pro" (high quality), or "auto"
            summary_type: "concise" (3-5 points) or "detailed" (comprehensive)

        Returns:
            Summary data with key points
        """
        # Extract text from document
        text = self._extract_text_from_pdf(gcs_uri)

        # Check document length to auto-select model
        if model_preference == "auto":
            model_preference = self._auto_select_model(text)

        # Select model
        model = self.pro_model if model_preference == "pro" else self.flash_model

        # Generate summary
        summary_text = self._generate_summary(text, model, summary_type)

        # Extract key points
        key_points = self._extract_key_points(summary_text)

        # Calculate metrics
        word_count = len(summary_text.split())

        return {
            "summary": summary_text,
            "key_points": key_points,
            "word_count": word_count,
            "model_used": f"gemini-1.5-{model_preference}",
            "summary_type": summary_type,
            "original_length": len(text.split()),
            "compression_ratio": round(len(text.split()) / word_count, 2) if word_count > 0 else 0,
        }

    def _extract_text_from_pdf(self, gcs_uri: str) -> str:
        """Extract text from PDF in GCS."""
        # Parse GCS URI
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])

        # Download PDF
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        pdf_bytes = blob.download_as_bytes()

        # Extract text
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""

        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"

        return text

    def _auto_select_model(self, text: str) -> str:
        """Auto-select model based on document characteristics."""
        word_count = len(text.split())

        # For very long documents or complex content, use Pro
        if word_count > 10000:
            return "pro"

        # Check for complex indicators (tables, technical terms, etc.)
        has_tables = bool(re.search(r'\|\s+\w+\s+\|', text))
        has_numbers = len(re.findall(r'\d+', text)) > 100

        if has_tables or has_numbers:
            return "pro"

        # Default to Flash for speed and cost
        return "flash"

    def _generate_summary(
        self,
        text: str,
        model: GenerativeModel,
        summary_type: str
    ) -> str:
        """Generate summary using selected model."""
        # Truncate text if too long (50k characters max)
        max_chars = 50000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Document truncated for processing]"

        # Build prompt based on summary type
        if summary_type == "concise":
            prompt = f"""Summarize the following document in 3-5 concise bullet points.
Focus on the main ideas, key findings, and important takeaways.
Use clear, professional language.

Document:
{text}

Summary (3-5 bullet points):"""

        else:  # detailed
            prompt = f"""Provide a comprehensive summary of the following document.

Include:
1. Main topic and purpose (1-2 sentences)
2. Key points and findings (5-7 bullet points)
3. Important details, data, or conclusions (3-4 bullet points)
4. Overall significance or implications (1-2 sentences)

Use clear, professional language suitable for business use.

Document:
{text}

Detailed Summary:"""

        # Generate summary
        response = model.generate_content(
            prompt,
            generation_config=self.generation_config,
        )

        return response.text

    def _extract_key_points(self, summary: str) -> List[str]:
        """Extract bullet points from summary text."""
        key_points = []

        # Split by lines
        lines = summary.split("\n")

        for line in lines:
            line = line.strip()

            # Match various bullet point formats
            # - Bullet point
            # • Bullet point
            # * Bullet point
            # 1. Numbered point
            # - **Bold:** point

            bullet_patterns = [
                r'^[-•*]\s+(.+)$',  # Dash, bullet, asterisk
                r'^\d+\.\s+(.+)$',  # Numbered
                r'^[-•*]\s+\*\*[^:]+:\*\*\s+(.+)$',  # Bold prefix
            ]

            for pattern in bullet_patterns:
                match = re.match(pattern, line)
                if match:
                    point = match.group(1).strip()
                    # Clean up markdown
                    point = re.sub(r'\*\*(.+?)\*\*', r'\1', point)  # Remove bold
                    point = re.sub(r'\*(.+?)\*', r'\1', point)  # Remove italics
                    key_points.append(point)
                    break

        # If no bullet points found, extract sentences as key points
        if not key_points:
            sentences = re.split(r'[.!?]\s+', summary)
            key_points = [s.strip() for s in sentences if len(s.strip()) > 20][:5]

        return key_points[:10]  # Limit to 10 points


class ClaudeSummarizer:
    """Summarize using Claude via Vertex AI (for premium tier)."""

    def __init__(self):
        # Initialize Vertex AI
        vertexai.init(project=settings.project_id, location=settings.vertex_ai_location)

        # Note: Claude on Vertex AI requires special setup
        # This is a placeholder for future premium feature
        self.available = False

    def summarize_document(self, gcs_uri: str) -> Dict[str, Any]:
        """Summarize using Claude (premium feature)."""
        if not self.available:
            raise NotImplementedError("Claude summarization not yet available")

        # Implementation would be similar to Gemini
        # but using Anthropic's Claude model via Vertex AI
        pass
```

**Step 3: Create summarizer worker main application**

Create file: `backend/workers/summarizer_worker/main.py`

```python
"""Summarizer worker service - generates document summaries."""

from fastapi import FastAPI, Request, HTTPException
from sqlalchemy.orm import Session
import json
from datetime import datetime
import traceback
import base64

from backend.shared.database import SessionLocal
from backend.shared.models import Document, DocumentSummary, AuditLog
from backend.shared.config import get_settings
from .summarizer import DocumentSummarizer

settings = get_settings()
app = FastAPI(title="Summarizer Worker")

# Initialize summarizer
summarizer = DocumentSummarizer()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "summarizer-worker"}


@app.post("/process")
async def process_summarization(request: Request):
    """
    Process summarization from Pub/Sub push subscription.

    Expected message format:
    {
        "tenant_id": "uuid",
        "user_id": "uuid",
        "document_id": "uuid",
        "gcs_path": "gs://bucket/path",
        "model_preference": "flash|pro|auto",
        "summary_type": "concise|detailed"
    }
    """
    try:
        # Parse Pub/Sub message
        envelope = await request.json()
        if "message" not in envelope:
            raise HTTPException(status_code=400, detail="Invalid Pub/Sub message")

        message_data = envelope["message"]["data"]
        message_json = base64.b64decode(message_data).decode("utf-8")
        message = json.loads(message_json)

        # Extract message fields
        tenant_id = message["tenant_id"]
        user_id = message["user_id"]
        document_id = message["document_id"]
        gcs_path = message["gcs_path"]
        model_preference = message.get("model_preference", "auto")
        summary_type = message.get("summary_type", "concise")

        print(f"Generating summary: {document_id} from {gcs_path}")
        print(f"Model: {model_preference}, Type: {summary_type}")

        # Get database session
        db = SessionLocal()

        try:
            # Get document record
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Update status
            document.status = "processing"
            document.processing_started_at = datetime.utcnow()
            db.commit()

            # Generate summary
            print(f"Calling Vertex AI for summarization...")
            summary_data = summarizer.summarize_document(
                gcs_uri=gcs_path,
                model_preference=model_preference,
                summary_type=summary_type
            )

            print(f"Summary generated: {summary_data['word_count']} words")

            # Save summary
            doc_summary = DocumentSummary(
                document_id=document_id,
                tenant_id=tenant_id,
                summary=summary_data["summary"],
                model_used=summary_data["model_used"],
                word_count=summary_data["word_count"],
                key_points=summary_data["key_points"],
            )
            db.add(doc_summary)

            # Update document status
            document.status = "completed"
            document.summarized = True
            document.processing_completed_at = datetime.utcnow()

            # Create audit log
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                document_id=document_id,
                action="summary_generated",
                details={
                    "model": summary_data["model_used"],
                    "word_count": summary_data["word_count"],
                    "compression_ratio": summary_data["compression_ratio"],
                }
            )
            db.add(audit_log)

            db.commit()

            print(f"Summary completed successfully: {document_id}")
            return {
                "status": "success",
                "document_id": str(document_id),
                "word_count": summary_data["word_count"]
            }

        except Exception as e:
            # Update document status to failed
            document.status = "failed"
            document.error_message = str(e)
            document.processing_completed_at = datetime.utcnow()
            db.commit()

            print(f"Error generating summary {document_id}: {e}")
            print(traceback.format_exc())

            raise HTTPException(status_code=500, detail=str(e))

        finally:
            db.close()

    except Exception as e:
        print(f"Error handling Pub/Sub message: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
```

**Step 4: Create Dockerfile**

Create file: `backend/workers/summarizer_worker/Dockerfile`

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY ../../shared/ /app/backend/shared/
COPY . /app/backend/workers/summarizer_worker/

WORKDIR /app/backend/workers/summarizer_worker

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8003/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
```

**Step 5: Build and test locally**

```bash
cd backend/workers/summarizer_worker

# Build image
docker build -t summarizer-worker:local -f Dockerfile ../..

# Test locally
docker run -p 8003:8003 \
  -e PROJECT_ID=docai-mvp-prod \
  -e VERTEX_AI_LOCATION=us-central1 \
  -e ENVIRONMENT=dev \
  -e DATABASE_URL=postgresql://docai:password@host.docker.internal:5432/docai \
  -v ~/.config/gcloud:/root/.config/gcloud \
  summarizer-worker:local
```

Test: Visit http://localhost:8003/health

**Step 6: Commit**

```bash
git add backend/workers/summarizer_worker/
git commit -m "feat: add summarizer worker with Gemini Flash and Pro"
```

---

## Task 4.2: Deploy Summarizer Worker (2 hours)

**Files:**
- Create: `scripts/deploy-summarizer-worker.sh`

**Step 1: Create deployment script**

Create file: `scripts/deploy-summarizer-worker.sh`

```bash
#!/bin/bash

set -e

PROJECT_ID="docai-mvp-prod"
REGION="europe-west1"
SERVICE_NAME="summarizer-worker"
IMAGE_NAME="europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/$SERVICE_NAME"

echo "Building Docker image..."
cd backend
docker build -t $IMAGE_NAME:latest -f workers/summarizer_worker/Dockerfile .

echo "Pushing to Artifact Registry..."
docker push $IMAGE_NAME:latest

echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --service-account ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,REGION=$REGION,ENVIRONMENT=prod,VERTEX_AI_LOCATION=us-central1 \
  --set-secrets DATABASE_URL=database-url:latest,DB_PASSWORD=database-password:latest \
  --min-instances 0 \
  --max-instances 5 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 1

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')

echo "Creating Pub/Sub push subscription..."
gcloud pubsub subscriptions create summarization-processing-sub \
  --topic=summarization-processing \
  --push-endpoint="$SERVICE_URL/process" \
  --push-auth-service-account=ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=600 \
  --message-retention-duration=7d \
  --max-retry-delay=600s \
  --min-retry-delay=10s

echo "Deployment complete!"
echo "Worker URL: $SERVICE_URL"
```

**Step 2: Make executable and deploy**

```bash
chmod +x scripts/deploy-summarizer-worker.sh
./scripts/deploy-summarizer-worker.sh
```

Expected: Service deployed, subscription created

**Step 3: Test end-to-end**

```bash
# View logs
gcloud run services logs read summarizer-worker --region europe-west1 --limit 50 --format json
```

**Step 4: Commit**

```bash
git add scripts/deploy-summarizer-worker.sh
git commit -m "feat: add summarizer worker deployment script"
```

---

## Task 4.3: Summary API Endpoints (3 hours)

**Files:**
- Create: `backend/api_gateway/routes/summaries.py`
- Modify: `backend/api_gateway/main.py`
- Modify: `backend/shared/schemas.py`

**Step 1: Add summary schemas**

Edit `backend/shared/schemas.py`, add:

```python
from typing import List, Optional

# Summary schemas
class SummaryRequest(BaseModel):
    """Request to generate summary."""
    model_preference: str = Field(default="auto", pattern="^(auto|flash|pro)$")
    summary_type: str = Field(default="concise", pattern="^(concise|detailed)$")


class SummaryResponse(BaseModel):
    """Summary response."""
    id: UUID
    document_id: UUID
    summary: str
    key_points: List[str]
    word_count: int
    model_used: str
    created_at: datetime

    class Config:
        from_attributes = True
```

**Step 2: Create summary routes**

Create file: `backend/api_gateway/routes/summaries.py`

```python
"""Document summarization routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from backend.shared.database import get_db
from backend.shared.models import Document, DocumentSummary, User
from backend.shared.schemas import SummaryRequest, SummaryResponse
from backend.shared.auth import verify_firebase_token, get_tenant_id_from_token
from backend.shared.pubsub import PubSubPublisher

router = APIRouter()
pubsub_publisher = PubSubPublisher()


@router.post("/{document_id}/generate", status_code=202)
async def generate_summary(
    document_id: uuid.UUID,
    request: SummaryRequest,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """
    Trigger summary generation for a document.

    Model preferences:
    - auto: Automatically select best model based on document
    - flash: Fast, cost-effective (Gemini 1.5 Flash)
    - pro: High quality (Gemini 1.5 Pro)

    Summary types:
    - concise: 3-5 bullet points
    - detailed: Comprehensive summary with sections
    """
    tenant_id = get_tenant_id_from_token(token_data)

    # Get document
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if document has OCR text (required for summarization)
    ocr_result = db.query(OCRResult).filter(
        OCRResult.document_id == document_id
    ).first()

    if not ocr_result and not document.ocr_completed:
        raise HTTPException(
            status_code=400,
            detail="Document must be OCR'd before summarization. Run OCR first."
        )

    # Get user
    user = db.query(User).filter(User.firebase_uid == token_data["uid"]).first()

    # Publish to Pub/Sub
    message = {
        "tenant_id": str(tenant_id),
        "user_id": str(user.id),
        "document_id": str(document_id),
        "gcs_path": document.gcs_path,
        "model_preference": request.model_preference,
        "summary_type": request.summary_type,
    }

    pubsub_publisher.publish_summarization(message)

    # Update status
    document.status = "processing"
    document.processing_started_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Summary generation started",
        "document_id": str(document_id),
        "model_preference": request.model_preference,
        "summary_type": request.summary_type,
        "status": "processing"
    }


@router.get("/{document_id}", response_model=SummaryResponse)
async def get_summary(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Get generated summary for a document."""
    tenant_id = get_tenant_id_from_token(token_data)

    summary = (
        db.query(DocumentSummary)
        .filter(
            DocumentSummary.document_id == document_id,
            DocumentSummary.tenant_id == tenant_id
        )
        .first()
    )

    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    return SummaryResponse.from_orm(summary)


@router.get("", response_model=List[SummaryResponse])
async def list_summaries(
    skip: int = 0,
    limit: int = 50,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """List all summaries for tenant."""
    tenant_id = get_tenant_id_from_token(token_data)

    summaries = (
        db.query(DocumentSummary)
        .filter(DocumentSummary.tenant_id == tenant_id)
        .order_by(DocumentSummary.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [SummaryResponse.from_orm(s) for s in summaries]


@router.delete("/{document_id}", status_code=204)
async def delete_summary(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Delete summary for a document."""
    tenant_id = get_tenant_id_from_token(token_data)

    summary = (
        db.query(DocumentSummary)
        .filter(
            DocumentSummary.document_id == document_id,
            DocumentSummary.tenant_id == tenant_id
        )
        .first()
    )

    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    db.delete(summary)
    db.commit()
```

**Step 3: Add summaries router to main app**

Edit `backend/api_gateway/main.py`:

```python
from .routes import auth, documents, invoices, ocr, summaries

# Include routers
app.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/v1/documents", tags=["Documents"])
app.include_router(invoices.router, prefix="/v1/invoices", tags=["Invoices"])
app.include_router(ocr.router, prefix="/v1/ocr", tags=["OCR"])
app.include_router(summaries.router, prefix="/v1/summaries", tags=["Summaries"])  # Add this
```

**Step 4: Test summary API**

Create file: `tests/backend/test_summaries.py`

```python
"""Tests for summary endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.api_gateway.main import app
import io

client = TestClient(app)


def get_auth_token():
    """Helper to get auth token."""
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": "summarytest@example.com",
            "password": "SecurePass123!",
            "full_name": "Summary Test",
            "tenant_name": "Summary Test Co"
        }
    )
    return response.json()["access_token"]


def test_generate_summary():
    """Test summary generation."""
    token = get_auth_token()

    # Upload document first
    fake_pdf = io.BytesIO(b"%PDF-1.4 test document")
    upload_response = client.post(
        "/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.pdf", fake_pdf, "application/pdf")},
        data={"document_type": "generic"}
    )

    document_id = upload_response.json()["id"]

    # Generate summary
    summary_response = client.post(
        f"/v1/summaries/{document_id}/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "model_preference": "flash",
            "summary_type": "concise"
        }
    )

    assert summary_response.status_code == 202
    assert summary_response.json()["message"] == "Summary generation started"
```

**Step 5: Deploy updated API Gateway**

```bash
./scripts/deploy-api-gateway.sh
```

**Step 6: Commit**

```bash
git add backend/api_gateway/routes/summaries.py backend/shared/schemas.py tests/backend/test_summaries.py
git commit -m "feat: add summary API endpoints with model selection"
```

---

## Task 4.4: Summary UI Components (4 hours)

**Files:**
- Create: `frontend/src/components/Summaries/SummaryView.tsx`
- Create: `frontend/src/components/Summaries/SummaryGenerator.tsx`
- Create: `frontend/src/pages/Summaries.tsx`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/App.tsx`

**Step 1: Update API client with summary methods**

Edit `frontend/src/services/api.ts`, add:

```typescript
// Summary endpoints
async generateSummary(documentId: string, options: {
  model_preference?: 'auto' | 'flash' | 'pro';
  summary_type?: 'concise' | 'detailed';
}) {
  const response = await this.client.post(
    `/summaries/${documentId}/generate`,
    options
  );
  return response.data;
}

async getSummary(documentId: string) {
  const response = await this.client.get(`/summaries/${documentId}`);
  return response.data;
}

async listSummaries(skip = 0, limit = 50) {
  const response = await this.client.get('/summaries', {
    params: { skip, limit },
  });
  return response.data;
}

async deleteSummary(documentId: string) {
  await this.client.delete(`/summaries/${documentId}`);
}
```

**Step 2: Create summary generator component**

Create file: `frontend/src/components/Summaries/SummaryGenerator.tsx`

```typescript
import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface SummaryGeneratorProps {
  documentId: string;
  onComplete?: () => void;
}

export const SummaryGenerator: React.FC<SummaryGeneratorProps> = ({
  documentId,
  onComplete
}) => {
  const queryClient = useQueryClient();
  const [modelPreference, setModelPreference] = useState<'auto' | 'flash' | 'pro'>('auto');
  const [summaryType, setSummaryType] = useState<'concise' | 'detailed'>('concise');

  const generateMutation = useMutation({
    mutationFn: () => apiClient.generateSummary(documentId, {
      model_preference: modelPreference,
      summary_type: summaryType,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['summary', documentId] });
      if (onComplete) onComplete();
    },
  });

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-medium mb-4">Generate Summary</h3>

      <div className="space-y-4">
        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quality Level
          </label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="radio"
                value="auto"
                checked={modelPreference === 'auto'}
                onChange={(e) => setModelPreference('auto')}
                className="mr-2"
              />
              <div>
                <div className="font-medium">Auto (Recommended)</div>
                <div className="text-sm text-gray-500">
                  Automatically selects the best model based on document complexity
                </div>
              </div>
            </label>

            <label className="flex items-center">
              <input
                type="radio"
                value="flash"
                checked={modelPreference === 'flash'}
                onChange={(e) => setModelPreference('flash')}
                className="mr-2"
              />
              <div>
                <div className="font-medium">Fast (Gemini Flash)</div>
                <div className="text-sm text-gray-500">
                  Quick summaries for straightforward documents
                </div>
              </div>
            </label>

            <label className="flex items-center">
              <input
                type="radio"
                value="pro"
                checked={modelPreference === 'pro'}
                onChange={(e) => setModelPreference('pro')}
                className="mr-2"
              />
              <div>
                <div className="font-medium">High Quality (Gemini Pro)</div>
                <div className="text-sm text-gray-500">
                  Best quality for complex or technical documents
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Summary Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Summary Length
          </label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="radio"
                value="concise"
                checked={summaryType === 'concise'}
                onChange={(e) => setSummaryType('concise')}
                className="mr-2"
              />
              <div>
                <div className="font-medium">Concise (3-5 bullet points)</div>
                <div className="text-sm text-gray-500">
                  Quick overview of main points
                </div>
              </div>
            </label>

            <label className="flex items-center">
              <input
                type="radio"
                value="detailed"
                checked={summaryType === 'detailed'}
                onChange={(e) => setSummaryType('detailed')}
                className="mr-2"
              />
              <div>
                <div className="font-medium">Detailed (Comprehensive)</div>
                <div className="text-sm text-gray-500">
                  Full summary with key sections and findings
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Generate Button */}
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md font-medium disabled:opacity-50"
        >
          {generateMutation.isPending ? 'Generating...' : 'Generate Summary'}
        </button>

        {generateMutation.isError && (
          <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
            Failed to generate summary. Please try again.
          </div>
        )}

        {generateMutation.isSuccess && (
          <div className="bg-green-50 border border-green-400 text-green-700 px-4 py-3 rounded">
            Summary generation started! It will appear below when ready.
          </div>
        )}
      </div>
    </div>
  );
};
```

**Step 3: Create summary view component**

Create file: `frontend/src/components/Summaries/SummaryView.tsx`

```typescript
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface SummaryViewProps {
  documentId: string;
}

export const SummaryView: React.FC<SummaryViewProps> = ({ documentId }) => {
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['summary', documentId],
    queryFn: () => apiClient.getSummary(documentId),
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return null; // No summary yet
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-medium">Document Summary</h3>
        <div className="text-sm text-gray-500">
          <span className="font-medium">{summary.model_used}</span>
          <span className="mx-2">•</span>
          <span>{summary.word_count} words</span>
        </div>
      </div>

      {/* Key Points */}
      {summary.key_points && summary.key_points.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Key Points:</h4>
          <ul className="space-y-2">
            {summary.key_points.map((point: string, index: number) => (
              <li key={index} className="flex items-start">
                <span className="inline-block w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span className="text-gray-700">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Full Summary */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Full Summary:</h4>
        <div className="prose max-w-none">
          <p className="text-gray-700 whitespace-pre-wrap">{summary.summary}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-4 flex space-x-2">
        <button
          onClick={() => navigator.clipboard.writeText(summary.summary)}
          className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm"
        >
          Copy Summary
        </button>
        <button
          onClick={() => {
            const text = `Key Points:\n${summary.key_points.map((p: string) => `- ${p}`).join('\n')}\n\nFull Summary:\n${summary.summary}`;
            const blob = new Blob([text], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `summary-${documentId}.txt`;
            a.click();
          }}
          className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-sm"
        >
          Download as TXT
        </button>
      </div>

      <div className="mt-4 text-xs text-gray-500">
        Generated on {new Date(summary.created_at).toLocaleString()}
      </div>
    </div>
  );
};
```

**Step 4: Create Summaries page**

Create file: `frontend/src/pages/Summaries.tsx`

```typescript
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { SummaryView } from '../components/Summaries/SummaryView';
import { SummaryGenerator } from '../components/Summaries/SummaryGenerator';

export const Summaries: React.FC = () => {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const { data: summaries, isLoading } = useQuery({
    queryKey: ['summaries'],
    queryFn: () => apiClient.listSummaries(),
  });

  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  if (selectedDocId) {
    const document = documents?.find((d: any) => d.id === selectedDocId);

    return (
      <div>
        <button
          onClick={() => setSelectedDocId(null)}
          className="mb-4 text-primary-600 hover:text-primary-800 flex items-center"
        >
          ← Back to list
        </button>

        <h2 className="text-2xl font-bold mb-4">
          Summary: {document?.filename || 'Document'}
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <SummaryView documentId={selectedDocId} />
          </div>
          <div>
            <SummaryGenerator
              documentId={selectedDocId}
              onComplete={() => {
                // Refresh summary view
              }}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Document Summaries</h2>

      {isLoading ? (
        <div className="text-center py-8">Loading summaries...</div>
      ) : summaries?.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No summaries yet. Generate a summary from the Documents page.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {summaries?.map((summary: any) => {
            const document = documents?.find((d: any) => d.id === summary.document_id);

            return (
              <div
                key={summary.id}
                className="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedDocId(summary.document_id)}
              >
                <h3 className="font-medium text-gray-900 mb-2">
                  {document?.filename || 'Document'}
                </h3>
                <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                  {summary.key_points[0] || summary.summary.substring(0, 100)}...
                </p>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>{summary.word_count} words</span>
                  <span>{summary.model_used}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
```

**Step 5: Add Summaries route to App**

Edit `frontend/src/App.tsx`:

```typescript
import { Summaries } from './pages/Summaries';

// Inside Routes:
<Route
  path="/summaries"
  element={
    <PrivateRoute>
      <Summaries />
    </PrivateRoute>
  }
/>
```

**Step 6: Update Dashboard navigation**

Edit `frontend/src/pages/Dashboard.tsx` to add Summaries link in navigation.

**Step 7: Test summary flow**

```bash
npm run dev
```

1. Upload a document
2. Run OCR if needed
3. Navigate to document
4. Generate summary with options
5. View generated summary
6. Copy or download summary

**Step 8: Deploy frontend**

```bash
cd frontend
vercel --prod
```

**Step 9: Commit**

```bash
git add frontend/src/components/Summaries/ frontend/src/pages/Summaries.tsx frontend/src/services/api.ts
git commit -m "feat: add summary generation UI with model selection"
```

---

## Phase 4 Complete ✓

**Summary:** Text summarization implemented
- ✅ Summarizer worker with Gemini Flash and Pro
- ✅ Auto model selection based on document complexity
- ✅ Concise and detailed summary types
- ✅ Key points extraction
- ✅ Summary API with quality options
- ✅ Summary UI with model selection
- ✅ Copy and download functionality

**Verification:**
- [ ] Summarizer worker deployed and healthy
- [ ] Pub/Sub subscription triggering worker
- [ ] Summaries generated successfully
- [ ] Key points extracted correctly
- [ ] API endpoints functional
- [ ] UI displays summaries correctly
- [ ] Model selection working
- [ ] Summary quality satisfactory

**Next:** Phase 5 - Chat with PDF (RAG) (Weeks 8-9)
