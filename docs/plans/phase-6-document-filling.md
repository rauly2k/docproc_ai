# Phase 6: Document Filling Implementation (Week 10)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement automated document filling: extract data from ID cards using Document AI and auto-fill PDF forms.

**Duration:** 1 week (40 hours)

**Prerequisites:** Phase 5 completed (RAG/Chat working)

---

## Task 6.1: Document Filling Worker Service (8 hours)

**Files:**
- Create: `backend/workers/docfill_worker/Dockerfile`
- Create: `backend/workers/docfill_worker/main.py`
- Create: `backend/workers/docfill_worker/processor.py`
- Create: `backend/workers/docfill_worker/requirements.txt`
- Create: `backend/shared/pdf_templates/` (directory for templates)

**Step 1: Create document filling requirements**

Create file: `backend/workers/docfill_worker/requirements.txt`

```txt
# Inherit from parent
-r ../../requirements.txt

# Additional dependencies
pypdfform==1.4.30
pillow==10.1.0
```

**Step 2: Create document filling processor module**

Create file: `backend/workers/docfill_worker/processor.py`

```python
"""Document filling processor - extract ID data and fill PDF forms."""

from google.cloud import documentai_v1 as documentai, storage
from google.api_core.client_options import ClientOptions
from pypdfform import PdfWrapper
from typing import Dict, Any, Optional
import os
import tempfile
import re
from datetime import datetime

from backend.shared.config import get_settings

settings = get_settings()


class DocumentFillingProcessor:
    """Extract data from IDs and fill PDF forms."""

    def __init__(self):
        self.project_id = settings.project_id
        self.location = "eu"  # EU location for Document AI
        self.id_processor_id = os.getenv("DOCUMENTAI_ID_PROCESSOR_ID")

        if not self.id_processor_id:
            raise ValueError("DOCUMENTAI_ID_PROCESSOR_ID not set")

        # Initialize Document AI client
        opts = ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com")
        self.documentai_client = documentai.DocumentProcessorServiceClient(client_options=opts)

        # Storage client
        self.storage_client = storage.Client()

        # Processor name
        self.processor_name = self.documentai_client.processor_path(
            self.project_id, self.location, self.id_processor_id
        )

    def extract_id_data(self, gcs_uri: str) -> Dict[str, Any]:
        """
        Extract data from ID card using Document AI.

        Supports:
        - Romanian ID cards (Carte de Identitate)
        - EU ID cards
        - Passports

        Args:
            gcs_uri: GCS URI of ID card image

        Returns:
            Extracted ID data
        """
        # Configure process request
        request = documentai.ProcessRequest(
            name=self.processor_name,
            gcs_document=documentai.GcsDocument(
                gcs_uri=gcs_uri,
                mime_type="image/jpeg"  # Or auto-detect
            )
        )

        # Process document
        result = self.documentai_client.process_document(request=request)
        document = result.document

        # Extract ID fields
        extracted_data = {
            "document_type": None,
            "family_name": None,
            "given_names": None,
            "date_of_birth": None,
            "place_of_birth": None,
            "nationality": None,
            "document_number": None,
            "issue_date": None,
            "expiry_date": None,
            "address": None,
            "cnp": None,  # Romanian Personal Numeric Code
            "confidence_scores": {},
            "raw_text": document.text,
        }

        # Parse entities
        for entity in document.entities:
            entity_type = entity.type_
            entity_text = entity.mention_text
            confidence = entity.confidence

            # Map Document AI entity types
            field_mapping = {
                "document_type": "document_type",
                "family_name": "family_name",
                "given_name": "given_names",
                "given_names": "given_names",
                "date_of_birth": "date_of_birth",
                "birth_date": "date_of_birth",
                "place_of_birth": "place_of_birth",
                "nationality": "nationality",
                "document_number": "document_number",
                "national_id": "document_number",
                "issue_date": "issue_date",
                "expiration_date": "expiry_date",
                "expiry_date": "expiry_date",
                "address": "address",
            }

            if entity_type in field_mapping:
                field_name = field_mapping[entity_type]
                extracted_data[field_name] = entity_text
                extracted_data["confidence_scores"][field_name] = confidence

            # Romanian-specific: CNP (Cod Numeric Personal)
            if entity_type == "personal_number" or entity_type == "national_id":
                # Validate CNP format (13 digits)
                if re.match(r'^\d{13}$', entity_text):
                    extracted_data["cnp"] = entity_text
                    extracted_data["confidence_scores"]["cnp"] = confidence

        # Post-process dates
        for date_field in ["date_of_birth", "issue_date", "expiry_date"]:
            if extracted_data[date_field]:
                extracted_data[date_field] = self._normalize_date(extracted_data[date_field])

        # Calculate average confidence
        confidences = list(extracted_data["confidence_scores"].values())
        extracted_data["average_confidence"] = (
            sum(confidences) / len(confidences) if confidences else 0
        )

        return extracted_data

    def fill_pdf_form(
        self,
        template_name: str,
        data: Dict[str, Any],
        output_gcs_path: str
    ) -> str:
        """
        Fill PDF form with extracted data.

        Args:
            template_name: Name of PDF template
            data: Extracted ID data
            output_gcs_path: Where to save filled PDF

        Returns:
            GCS URI of filled PDF
        """
        # Get template path
        template_path = self._get_template_path(template_name)
        if not template_path:
            raise ValueError(f"Template {template_name} not found")

        # Map data fields to PDF form fields
        form_data = self._map_data_to_form_fields(data, template_name)

        # Create temporary file for output
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_output_path = temp_file.name

        try:
            # Fill PDF form
            pdf = PdfWrapper(template_path)
            filled_pdf = pdf.fill(form_data)

            # Save to temporary file
            with open(temp_output_path, "wb+") as output_file:
                filled_pdf.stream.write_to(output_file)

            # Upload to GCS
            gcs_uri = self._upload_to_gcs(temp_output_path, output_gcs_path)

            return gcs_uri

        finally:
            # Clean up temporary file
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)

    def _get_template_path(self, template_name: str) -> Optional[str]:
        """Get path to PDF template."""
        # Templates stored in backend/shared/pdf_templates/
        templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "shared",
            "pdf_templates"
        )

        template_path = os.path.join(templates_dir, f"{template_name}.pdf")

        if os.path.exists(template_path):
            return template_path

        return None

    def _map_data_to_form_fields(
        self,
        data: Dict[str, Any],
        template_name: str
    ) -> Dict[str, str]:
        """
        Map extracted data to PDF form field names.

        Different templates have different field names.
        """
        # Standard Romanian form field mapping
        if template_name == "romanian_standard_form":
            return {
                "nume": data.get("family_name", ""),
                "prenume": data.get("given_names", ""),
                "cnp": data.get("cnp", ""),
                "data_nasterii": data.get("date_of_birth", ""),
                "locul_nasterii": data.get("place_of_birth", ""),
                "adresa": data.get("address", ""),
                "seria_ci": data.get("document_number", "")[:2] if data.get("document_number") else "",
                "numar_ci": data.get("document_number", "")[2:] if data.get("document_number") else "",
                "emis_la": data.get("issue_date", ""),
                "valabil_pana": data.get("expiry_date", ""),
            }

        # Generic mapping
        return {
            "family_name": data.get("family_name", ""),
            "given_names": data.get("given_names", ""),
            "date_of_birth": data.get("date_of_birth", ""),
            "place_of_birth": data.get("place_of_birth", ""),
            "nationality": data.get("nationality", ""),
            "document_number": data.get("document_number", ""),
            "address": data.get("address", ""),
            "cnp": data.get("cnp", ""),
        }

    def _upload_to_gcs(self, local_path: str, gcs_path: str) -> str:
        """Upload file to GCS and return URI."""
        # Parse GCS path
        parts = gcs_path.replace("gs://", "").split("/", 1)
        bucket_name = parts[0]
        blob_path = parts[1] if len(parts) > 1 else ""

        # Upload
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        blob.upload_from_filename(local_path, content_type="application/pdf")

        return f"gs://{bucket_name}/{blob_path}"

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format."""
        import dateutil.parser

        try:
            parsed = dateutil.parser.parse(date_str)
            return parsed.strftime("%Y-%m-%d")
        except:
            return date_str
```

**Step 3: Create document filling worker main application**

Create file: `backend/workers/docfill_worker/main.py`

```python
"""Document filling worker - extract ID data and fill forms."""

from fastapi import FastAPI, Request, HTTPException
from sqlalchemy.orm import Session
import json
from datetime import datetime
import traceback
import base64

from backend.shared.database import SessionLocal
from backend.shared.models import Document, AuditLog
from backend.shared.config import get_settings
from .processor import DocumentFillingProcessor

settings = get_settings()
app = FastAPI(title="Document Filling Worker")

# Initialize processor
processor = DocumentFillingProcessor()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "docfill-worker"}


@app.post("/process")
async def process_document_filling(request: Request):
    """
    Process document filling from Pub/Sub push subscription.

    Expected message format:
    {
        "tenant_id": "uuid",
        "user_id": "uuid",
        "id_document_id": "uuid",  # ID card document
        "template_name": "romanian_standard_form",
        "output_document_id": "uuid"  # Where to save filled form
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
        id_document_id = message["id_document_id"]
        template_name = message["template_name"]
        output_document_id = message["output_document_id"]

        print(f"Processing document filling: ID={id_document_id}, Template={template_name}")

        # Get database session
        db = SessionLocal()

        try:
            # Get ID document
            id_document = db.query(Document).filter(
                Document.id == id_document_id
            ).first()

            if not id_document:
                raise ValueError(f"ID document {id_document_id} not found")

            # Get output document
            output_document = db.query(Document).filter(
                Document.id == output_document_id
            ).first()

            if not output_document:
                raise ValueError(f"Output document {output_document_id} not found")

            # Update status
            output_document.status = "processing"
            output_document.processing_started_at = datetime.utcnow()
            db.commit()

            # Step 1: Extract ID data
            print(f"Extracting ID data from {id_document.gcs_path}")
            extracted_data = processor.extract_id_data(id_document.gcs_path)

            print(f"Extracted: {extracted_data.get('family_name')} {extracted_data.get('given_names')}")

            # Step 2: Fill PDF form
            output_gcs_path = f"gs://{settings.gcs_bucket_processed}/{tenant_id}/{output_document_id}/filled_form.pdf"

            print(f"Filling PDF form: {template_name}")
            filled_pdf_uri = processor.fill_pdf_form(
                template_name=template_name,
                data=extracted_data,
                output_gcs_path=output_gcs_path
            )

            print(f"Filled PDF saved to {filled_pdf_uri}")

            # Update output document
            output_document.gcs_processed_path = filled_pdf_uri
            output_document.status = "completed"
            output_document.processing_completed_at = datetime.utcnow()

            # Create audit log
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                document_id=output_document_id,
                action="document_filled",
                details={
                    "id_document_id": str(id_document_id),
                    "template_name": template_name,
                    "extracted_fields": list(extracted_data.keys()),
                    "confidence": extracted_data.get("average_confidence"),
                }
            )
            db.add(audit_log)

            db.commit()

            print(f"Document filling completed successfully: {output_document_id}")
            return {
                "status": "success",
                "output_document_id": str(output_document_id),
                "filled_pdf_uri": filled_pdf_uri
            }

        except Exception as e:
            # Update document status to failed
            if output_document:
                output_document.status = "failed"
                output_document.error_message = str(e)
                output_document.processing_completed_at = datetime.utcnow()
                db.commit()

            print(f"Error in document filling: {e}")
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
    uvicorn.run(app, host="0.0.0.0", port=8005)
```

**Step 4: Create Dockerfile**

Create file: `backend/workers/docfill_worker/Dockerfile`

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
COPY . /app/backend/workers/docfill_worker/

WORKDIR /app/backend/workers/docfill_worker

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8005/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
```

**Step 5: Create sample PDF template**

Create directory: `backend/shared/pdf_templates/`

Create a sample fillable PDF form named `romanian_standard_form.pdf` with fields:
- nume (family name)
- prenume (given names)
- cnp (personal numeric code)
- data_nasterii (date of birth)
- locul_nasterii (place of birth)
- adresa (address)
- seria_ci (ID series)
- numar_ci (ID number)
- emis_la (issue date)
- valabil_pana (expiry date)

**Step 6: Create Document AI ID processor**

```bash
# In Cloud Console: Document AI > Create Processor
# Type: Identity Document Processor (EU)
# Name: id-processor-eu
# Region: eu
# Copy processor ID and store:

echo "YOUR_ID_PROCESSOR_ID" | gcloud secrets create documentai-id-processor-id \
  --data-file=- \
  --replication-policy=automatic
```

**Step 7: Test locally**

```bash
cd backend/workers/docfill_worker

# Build
docker build -t docfill-worker:local -f Dockerfile ../..

# Run
docker run -p 8005:8005 \
  -e PROJECT_ID=docai-mvp-prod \
  -e DATABASE_URL=postgresql://docai:password@host.docker.internal:5432/docai \
  -e DOCUMENTAI_ID_PROCESSOR_ID=YOUR_PROCESSOR_ID \
  -v ~/.config/gcloud:/root/.config/gcloud \
  docfill-worker:local
```

**Step 8: Commit**

```bash
git add backend/workers/docfill_worker/ backend/shared/pdf_templates/
git commit -m "feat: add document filling worker with ID extraction"
```

---

## Task 6.2: Deploy Document Filling Worker (2 hours)

**Files:**
- Create: `scripts/deploy-docfill-worker.sh`

**Step 1: Create deployment script**

Create file: `scripts/deploy-docfill-worker.sh`

```bash
#!/bin/bash

set -e

PROJECT_ID="docai-mvp-prod"
REGION="europe-west1"
SERVICE_NAME="docfill-worker"
IMAGE_NAME="europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/$SERVICE_NAME"

echo "Building Docker image..."
cd backend
docker build -t $IMAGE_NAME:latest -f workers/docfill_worker/Dockerfile .

echo "Pushing to Artifact Registry..."
docker push $IMAGE_NAME:latest

echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --service-account ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,REGION=$REGION,ENVIRONMENT=prod \
  --set-secrets DATABASE_URL=database-url:latest,DB_PASSWORD=database-password:latest,DOCUMENTAI_ID_PROCESSOR_ID=documentai-id-processor-id:latest \
  --min-instances 0 \
  --max-instances 5 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 1

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')

echo "Creating Pub/Sub push subscription..."
gcloud pubsub subscriptions create document-filling-sub \
  --topic=document-filling \
  --push-endpoint="$SERVICE_URL/process" \
  --push-auth-service-account=ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=600 \
  --message-retention-duration=7d

echo "Deployment complete!"
echo "Worker URL: $SERVICE_URL"
```

**Step 2: Deploy**

```bash
chmod +x scripts/deploy-docfill-worker.sh
./scripts/deploy-docfill-worker.sh
```

**Step 3: Commit**

```bash
git add scripts/deploy-docfill-worker.sh
git commit -m "feat: add document filling worker deployment"
```

---

## Task 6.3: Document Filling API Endpoints (3 hours)

**Files:**
- Create: `backend/api_gateway/routes/filling.py`
- Modify: `backend/api_gateway/main.py`
- Modify: `backend/shared/schemas.py`

**Step 1: Add filling schemas**

Edit `backend/shared/schemas.py`, add:

```python
# Document filling schemas
class DocumentFillingRequest(BaseModel):
    """Request to fill document."""
    id_document_id: UUID
    template_name: str


class FillingTemplateInfo(BaseModel):
    """PDF template information."""
    name: str
    display_name: str
    description: str
    fields: List[str]


class FilledDocumentResponse(BaseModel):
    """Filled document response."""
    output_document_id: UUID
    download_url: str
    extracted_data: dict
    template_used: str
    created_at: datetime
```

**Step 2: Create filling routes**

Create file: `backend/api_gateway/routes/filling.py`

```python
"""Document filling routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from backend.shared.database import get_db
from backend.shared.models import Document, User
from backend.shared.schemas import DocumentFillingRequest, FillingTemplateInfo, FilledDocumentResponse
from backend.shared.auth import verify_firebase_token, get_tenant_id_from_token
from backend.shared.pubsub import PubSubPublisher
from backend.shared.gcs import GCSManager

router = APIRouter()
pubsub_publisher = PubSubPublisher()
gcs_manager = GCSManager()


@router.get("/templates", response_model=List[FillingTemplateInfo])
async def list_templates():
    """List available PDF form templates."""
    # Hardcoded for MVP, could be made dynamic
    templates = [
        FillingTemplateInfo(
            name="romanian_standard_form",
            display_name="Romanian Standard Form",
            description="Standard form for Romanian documents",
            fields=["nume", "prenume", "cnp", "data_nasterii", "adresa"]
        ),
    ]
    return templates


@router.post("/extract-and-fill", status_code=202)
async def extract_and_fill(
    request: DocumentFillingRequest,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """
    Extract data from ID document and fill PDF form.

    Flow:
    1. Validate ID document exists
    2. Create output document record
    3. Publish job to Pub/Sub
    4. Return output document ID
    """
    tenant_id = get_tenant_id_from_token(token_data)

    # Get ID document
    id_document = db.query(Document).filter(
        Document.id == request.id_document_id,
        Document.tenant_id == tenant_id
    ).first()

    if not id_document:
        raise HTTPException(status_code=404, detail="ID document not found")

    # Get user
    user = db.query(User).filter(User.firebase_uid == token_data["uid"]).first()

    # Create output document record
    output_document_id = uuid.uuid4()
    output_document = Document(
        id=output_document_id,
        tenant_id=tenant_id,
        user_id=user.id,
        filename=f"filled_{request.template_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf",
        document_type="filled_form",
        gcs_path=f"gs://placeholder/{output_document_id}",  # Will be updated by worker
        status="processing",
        processing_started_at=datetime.utcnow()
    )
    db.add(output_document)
    db.commit()

    # Publish to Pub/Sub
    message = {
        "tenant_id": str(tenant_id),
        "user_id": str(user.id),
        "id_document_id": str(request.id_document_id),
        "template_name": request.template_name,
        "output_document_id": str(output_document_id)
    }

    pubsub_publisher.publish_document_filling(message)

    return {
        "message": "Document filling started",
        "output_document_id": str(output_document_id)
    }


@router.get("/{document_id}/download")
async def get_filled_pdf(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Get download URL for filled PDF."""
    tenant_id = get_tenant_id_from_token(token_data)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.gcs_processed_path:
        raise HTTPException(status_code=400, detail="Document not yet processed")

    # Generate signed URL
    download_url = gcs_manager.get_signed_url(
        document.gcs_processed_path,
        expiration_minutes=15
    )

    return {
        "download_url": download_url,
        "expires_in_minutes": 15,
        "filename": document.filename
    }
```

**Step 3: Add filling router to main app**

Edit `backend/api_gateway/main.py`:

```python
from .routes import auth, documents, invoices, ocr, summaries, chat, filling

app.include_router(filling.router, prefix="/v1/filling", tags=["Document Filling"])
```

**Step 4: Deploy updated API Gateway**

```bash
./scripts/deploy-api-gateway.sh
```

**Step 5: Commit**

```bash
git add backend/api_gateway/routes/filling.py backend/shared/schemas.py
git commit -m "feat: add document filling API endpoints"
```

---

## Task 6.4: Document Filling UI (5 hours)

**Files:**
- Create: `frontend/src/components/Filling/DocumentFillingForm.tsx`
- Create: `frontend/src/pages/DocumentFilling.tsx`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/App.tsx`

**Step 1: Update API client**

Edit `frontend/src/services/api.ts`, add:

```typescript
// Document filling endpoints
async getFillingTemplates() {
  const response = await this.client.get('/filling/templates');
  return response.data;
}

async extractAndFill(idDocumentId: string, templateName: string) {
  const response = await this.client.post('/filling/extract-and-fill', {
    id_document_id: idDocumentId,
    template_name: templateName,
  });
  return response.data;
}

async getFilledPdfDownloadUrl(documentId: string) {
  const response = await this.client.get(`/filling/${documentId}/download`);
  return response.data;
}
```

**Step 2: Create document filling form component**

Create file: `frontend/src/components/Filling/DocumentFillingForm.tsx`

```typescript
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

export const DocumentFillingForm: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedIdDoc, setSelectedIdDoc] = useState<string>('');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [filledDocId, setFilledDocId] = useState<string | null>(null);

  // Fetch ID documents
  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  // Fetch templates
  const { data: templates } = useQuery({
    queryKey: ['filling-templates'],
    queryFn: () => apiClient.getFillingTemplates(),
  });

  // Extract and fill mutation
  const fillMutation = useMutation({
    mutationFn: () => apiClient.extractAndFill(selectedIdDoc, selectedTemplate),
    onSuccess: (data) => {
      setFilledDocId(data.output_document_id);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  // Download mutation
  const downloadMutation = useMutation({
    mutationFn: () => apiClient.getFilledPdfDownloadUrl(filledDocId!),
    onSuccess: (data) => {
      window.open(data.download_url, '_blank');
    },
  });

  const handleFill = () => {
    if (!selectedIdDoc || !selectedTemplate) {
      alert('Please select both an ID document and a template');
      return;
    }
    fillMutation.mutate();
  };

  const idDocuments = documents?.filter((d: any) => d.document_type === 'id') || [];

  return (
    <div className="bg-white p-6 rounded-lg shadow max-w-2xl">
      <h3 className="text-lg font-medium mb-4">Fill PDF Form from ID</h3>

      <div className="space-y-4">
        {/* Select ID Document */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select ID Document
          </label>
          <select
            value={selectedIdDoc}
            onChange={(e) => setSelectedIdDoc(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">-- Choose ID Document --</option>
            {idDocuments.map((doc: any) => (
              <option key={doc.id} value={doc.id}>
                {doc.filename}
              </option>
            ))}
          </select>
          {idDocuments.length === 0 && (
            <p className="text-sm text-gray-500 mt-1">
              No ID documents found. Upload an ID document first.
            </p>
          )}
        </div>

        {/* Select Template */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Form Template
          </label>
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">-- Choose Template --</option>
            {templates?.map((template: any) => (
              <option key={template.name} value={template.name}>
                {template.display_name}
              </option>
            ))}
          </select>
          {selectedTemplate && (
            <p className="text-sm text-gray-600 mt-1">
              {templates?.find((t: any) => t.name === selectedTemplate)?.description}
            </p>
          )}
        </div>

        {/* Fill Button */}
        <button
          onClick={handleFill}
          disabled={!selectedIdDoc || !selectedTemplate || fillMutation.isPending}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md font-medium disabled:opacity-50"
        >
          {fillMutation.isPending ? 'Processing...' : 'Extract Data & Fill Form'}
        </button>

        {/* Status Messages */}
        {fillMutation.isError && (
          <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
            Failed to fill document. Please try again.
          </div>
        )}

        {fillMutation.isSuccess && (
          <div className="bg-green-50 border border-green-400 text-green-700 px-4 py-3 rounded">
            <p className="font-medium">Document filled successfully!</p>
            <p className="text-sm mt-1">Processing... The filled PDF will be ready shortly.</p>
          </div>
        )}

        {/* Download Button */}
        {filledDocId && (
          <div className="pt-4 border-t">
            <button
              onClick={() => downloadMutation.mutate()}
              disabled={downloadMutation.isPending}
              className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium"
            >
              {downloadMutation.isPending ? 'Getting download link...' : 'Download Filled PDF'}
            </button>
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">How it works:</h4>
        <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
          <li>Upload an ID card or identity document</li>
          <li>Select a PDF form template to fill</li>
          <li>AI extracts data from your ID (name, address, ID number, etc.)</li>
          <li>Data is automatically filled into the PDF form</li>
          <li>Download the completed, filled PDF</li>
        </ol>
      </div>
    </div>
  );
};
```

**Step 3: Create document filling page**

Create file: `frontend/src/pages/DocumentFilling.tsx`

```typescript
import React from 'react';
import { DocumentFillingForm } from '../components/Filling/DocumentFillingForm';

export const DocumentFilling: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto py-8">
      <h2 className="text-2xl font-bold mb-6">Automatic Document Filling</h2>

      <div className="mb-6 bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-2">What is Document Filling?</h3>
        <p className="text-gray-700 mb-4">
          Automatically extract data from identity documents (ID cards, passports) and use that
          information to fill out PDF forms. No manual typing required!
        </p>

        <h4 className="font-medium mb-2">Supported Documents:</h4>
        <ul className="list-disc list-inside text-gray-700 space-y-1">
          <li>Romanian ID Cards (Carte de Identitate)</li>
          <li>EU Identity Cards</li>
          <li>Passports</li>
        </ul>
      </div>

      <DocumentFillingForm />
    </div>
  );
};
```

**Step 4: Add route to App**

Edit `frontend/src/App.tsx`:

```typescript
import { DocumentFilling } from './pages/DocumentFilling';

// Inside Routes:
<Route
  path="/filling"
  element={
    <PrivateRoute>
      <DocumentFilling />
    </PrivateRoute>
  }
/>
```

**Step 5: Update navigation**

Add "Document Filling" link to dashboard navigation.

**Step 6: Test filling flow**

```bash
npm run dev
```

1. Upload an ID document
2. Navigate to Document Filling page
3. Select ID document and template
4. Click "Extract Data & Fill Form"
5. Download filled PDF

**Step 7: Deploy frontend**

```bash
cd frontend
vercel --prod
```

**Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: add document filling UI with template selection"
```

---

## Phase 6 Complete ✓

**Summary:** Document filling implemented
- ✅ Document filling worker with Document AI ID extraction
- ✅ PDF form filling with PyPDFForm
- ✅ Romanian ID card support
- ✅ Template system for different forms
- ✅ Filling API endpoints
- ✅ Document filling UI with template selector
- ✅ Download filled PDFs

**Verification:**
- [ ] Document filling worker deployed
- [ ] ID processor configured in Document AI
- [ ] ID data extracted correctly
- [ ] PDF forms filled accurately
- [ ] Templates working
- [ ] API endpoints functional
- [ ] UI shows template selection
- [ ] Filled PDFs downloadable

**Next:** Phase 7 - Polish & Beta Launch (Weeks 11-12)
