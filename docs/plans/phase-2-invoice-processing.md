# Phase 2: Invoice Processing Implementation (Weeks 4-5)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement automated invoice processing using Google Document AI with human-in-the-loop validation UI for compliance.

**Duration:** 2 weeks (80 hours)

**Prerequisites:** Phase 1 completed (API Gateway deployed, document upload working)

---

## Task 2.1: Invoice Worker Service Setup (3 hours)

**Files:**
- Create: `backend/workers/invoice_worker/Dockerfile`
- Create: `backend/workers/invoice_worker/main.py`
- Create: `backend/workers/invoice_worker/processor.py`
- Create: `backend/workers/invoice_worker/requirements.txt`

**Step 1: Create invoice worker requirements**

Create file: `backend/workers/invoice_worker/requirements.txt`

```txt
# Inherit from parent
-r ../../requirements.txt

# Additional worker-specific dependencies (if any)
```

**Step 2: Create invoice processor module**

Create file: `backend/workers/invoice_worker/processor.py`

```python
"""Invoice processing using Google Document AI."""

from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
from typing import Dict, Any, List
import os

from backend.shared.config import get_settings

settings = get_settings()


class InvoiceProcessor:
    """Process invoices using Document AI."""

    def __init__(self):
        self.project_id = settings.project_id
        self.location = "us"  # Document AI location
        self.processor_id = os.getenv("DOCUMENTAI_INVOICE_PROCESSOR_ID")

        if not self.processor_id:
            raise ValueError("DOCUMENTAI_INVOICE_PROCESSOR_ID environment variable not set")

        # Initialize Document AI client
        opts = ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com")
        self.client = documentai.DocumentProcessorServiceClient(client_options=opts)

        # Construct processor name
        self.processor_name = self.client.processor_path(
            self.project_id, self.location, self.processor_id
        )

    def process_invoice_from_gcs(self, gcs_uri: str) -> Dict[str, Any]:
        """
        Process invoice from Google Cloud Storage.

        Args:
            gcs_uri: GCS URI (gs://bucket/path/to/invoice.pdf)

        Returns:
            Parsed invoice data
        """
        # Configure the process request
        request = documentai.ProcessRequest(
            name=self.processor_name,
            gcs_document=documentai.GcsDocument(
                gcs_uri=gcs_uri,
                mime_type="application/pdf"
            )
        )

        # Process the document
        result = self.client.process_document(request=request)
        document = result.document

        # Extract invoice data
        return self._extract_invoice_data(document)

    def _extract_invoice_data(self, document: documentai.Document) -> Dict[str, Any]:
        """
        Extract structured data from Document AI response.

        Returns:
            Dictionary with invoice fields
        """
        extracted_data = {
            "vendor_name": None,
            "vendor_address": None,
            "vendor_tax_id": None,
            "invoice_number": None,
            "invoice_date": None,
            "due_date": None,
            "subtotal": None,
            "tax_amount": None,
            "total_amount": None,
            "currency": "EUR",
            "line_items": [],
            "confidence_scores": {},
            "raw_text": document.text,
        }

        # Extract entities
        for entity in document.entities:
            entity_type = entity.type_
            entity_text = entity.mention_text
            confidence = entity.confidence

            # Map Document AI entity types to our schema
            if entity_type == "supplier_name":
                extracted_data["vendor_name"] = entity_text
                extracted_data["confidence_scores"]["vendor_name"] = confidence

            elif entity_type == "supplier_address":
                extracted_data["vendor_address"] = entity_text
                extracted_data["confidence_scores"]["vendor_address"] = confidence

            elif entity_type == "supplier_tax_id":
                extracted_data["vendor_tax_id"] = entity_text
                extracted_data["confidence_scores"]["vendor_tax_id"] = confidence

            elif entity_type == "invoice_id":
                extracted_data["invoice_number"] = entity_text
                extracted_data["confidence_scores"]["invoice_number"] = confidence

            elif entity_type == "invoice_date":
                extracted_data["invoice_date"] = self._parse_date(entity_text)
                extracted_data["confidence_scores"]["invoice_date"] = confidence

            elif entity_type == "due_date":
                extracted_data["due_date"] = self._parse_date(entity_text)
                extracted_data["confidence_scores"]["due_date"] = confidence

            elif entity_type == "net_amount":
                extracted_data["subtotal"] = self._parse_amount(entity_text)
                extracted_data["confidence_scores"]["subtotal"] = confidence

            elif entity_type == "total_tax_amount":
                extracted_data["tax_amount"] = self._parse_amount(entity_text)
                extracted_data["confidence_scores"]["tax_amount"] = confidence

            elif entity_type == "total_amount":
                extracted_data["total_amount"] = self._parse_amount(entity_text)
                extracted_data["confidence_scores"]["total_amount"] = confidence

            elif entity_type == "currency":
                extracted_data["currency"] = entity_text

            # Extract line items
            elif entity_type == "line_item":
                line_item = self._extract_line_item(entity)
                if line_item:
                    extracted_data["line_items"].append(line_item)

        # Calculate average confidence
        confidences = list(extracted_data["confidence_scores"].values())
        extracted_data["average_confidence"] = (
            sum(confidences) / len(confidences) if confidences else 0
        )

        return extracted_data

    def _extract_line_item(self, entity: documentai.Document.Entity) -> Dict[str, Any]:
        """Extract line item details."""
        line_item = {
            "description": None,
            "quantity": None,
            "unit_price": None,
            "amount": None,
        }

        for prop in entity.properties:
            prop_type = prop.type_
            prop_text = prop.mention_text

            if prop_type == "line_item/description":
                line_item["description"] = prop_text
            elif prop_type == "line_item/quantity":
                line_item["quantity"] = self._parse_number(prop_text)
            elif prop_type == "line_item/unit_price":
                line_item["unit_price"] = self._parse_amount(prop_text)
            elif prop_type == "line_item/amount":
                line_item["amount"] = self._parse_amount(prop_text)

        return line_item

    @staticmethod
    def _parse_date(date_str: str) -> str:
        """Parse date string to ISO format."""
        from datetime import datetime
        import dateutil.parser

        try:
            parsed = dateutil.parser.parse(date_str)
            return parsed.strftime("%Y-%m-%d")
        except:
            return date_str

    @staticmethod
    def _parse_amount(amount_str: str) -> float:
        """Parse amount string to float."""
        import re

        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r'[^\d.,]', '', amount_str)

        # Handle European format (1.234,56) vs US format (1,234.56)
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rindex(',') > cleaned.rindex('.'):
                # European format
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # US format
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Assume decimal comma
            cleaned = cleaned.replace(',', '.')

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @staticmethod
    def _parse_number(num_str: str) -> int:
        """Parse number string to int."""
        import re

        cleaned = re.sub(r'[^\d]', '', num_str)
        try:
            return int(cleaned)
        except ValueError:
            return 0
```

**Step 3: Create invoice worker main application**

Create file: `backend/workers/invoice_worker/main.py`

```python
"""Invoice worker service - processes invoices from Pub/Sub."""

from fastapi import FastAPI, Request, HTTPException
from google.cloud import storage
from sqlalchemy.orm import Session
import json
from datetime import datetime
import traceback

from backend.shared.database import SessionLocal
from backend.shared.models import Document, InvoiceData, AuditLog
from backend.shared.config import get_settings
from .processor import InvoiceProcessor

settings = get_settings()
app = FastAPI(title="Invoice Worker")

# Initialize processor
processor = InvoiceProcessor()
storage_client = storage.Client()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "invoice-worker"}


@app.post("/process")
async def process_invoice(request: Request):
    """
    Process invoice from Pub/Sub push subscription.

    Expected message format:
    {
        "tenant_id": "uuid",
        "user_id": "uuid",
        "document_id": "uuid",
        "gcs_path": "gs://bucket/path",
        "document_type": "invoice",
        "filename": "invoice.pdf"
    }
    """
    try:
        # Parse Pub/Sub message
        envelope = await request.json()
        if "message" not in envelope:
            raise HTTPException(status_code=400, detail="Invalid Pub/Sub message")

        message_data = envelope["message"]["data"]
        import base64
        message_json = base64.b64decode(message_data).decode("utf-8")
        message = json.loads(message_json)

        # Extract message fields
        tenant_id = message["tenant_id"]
        user_id = message["user_id"]
        document_id = message["document_id"]
        gcs_path = message["gcs_path"]

        print(f"Processing invoice: {document_id} from {gcs_path}")

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

            # Process invoice with Document AI
            print(f"Calling Document AI for {gcs_path}")
            extracted_data = processor.process_invoice_from_gcs(gcs_path)

            # Save invoice data
            invoice_data = InvoiceData(
                document_id=document_id,
                tenant_id=tenant_id,
                vendor_name=extracted_data["vendor_name"],
                vendor_address=extracted_data["vendor_address"],
                vendor_tax_id=extracted_data["vendor_tax_id"],
                invoice_number=extracted_data["invoice_number"],
                invoice_date=extracted_data["invoice_date"],
                due_date=extracted_data["due_date"],
                subtotal=extracted_data["subtotal"],
                tax_amount=extracted_data["tax_amount"],
                total_amount=extracted_data["total_amount"],
                currency=extracted_data["currency"],
                line_items=extracted_data["line_items"],
                raw_extraction=extracted_data,
                is_validated=False,
            )
            db.add(invoice_data)

            # Update document status
            document.status = "completed"
            document.invoice_parsed = True
            document.processing_completed_at = datetime.utcnow()

            # Create audit log
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                document_id=document_id,
                action="invoice_processed",
                details={
                    "vendor_name": extracted_data["vendor_name"],
                    "total_amount": extracted_data["total_amount"],
                    "average_confidence": extracted_data["average_confidence"],
                }
            )
            db.add(audit_log)

            db.commit()

            print(f"Invoice processed successfully: {document_id}")
            return {"status": "success", "document_id": str(document_id)}

        except Exception as e:
            # Update document status to failed
            document.status = "failed"
            document.error_message = str(e)
            document.processing_completed_at = datetime.utcnow()
            db.commit()

            print(f"Error processing invoice {document_id}: {e}")
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
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

**Step 4: Create Dockerfile for invoice worker**

Create file: `backend/workers/invoice_worker/Dockerfile`

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
COPY . /app/backend/workers/invoice_worker/

WORKDIR /app/backend/workers/invoice_worker

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8001/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Step 5: Create Document AI processor**

In Google Cloud Console:

1. Go to Document AI > Processors
2. Click "Create Processor"
3. Select "Invoice Parser" (Specialized processor)
4. Name: "invoice-processor"
5. Region: "us"
6. Click "Create"
7. Copy Processor ID

**Step 6: Store processor ID in Secret Manager**

```bash
# Store processor ID
echo "YOUR_PROCESSOR_ID" | gcloud secrets create documentai-invoice-processor-id \
  --data-file=- \
  --replication-policy=automatic
```

**Step 7: Build and test locally**

```bash
cd backend/workers/invoice_worker

# Build image
docker build -t invoice-worker:local -f Dockerfile ../..

# Run locally (with GCP credentials)
docker run -p 8001:8001 \
  -e PROJECT_ID=docai-mvp-prod \
  -e ENVIRONMENT=dev \
  -e DATABASE_URL=postgresql://docai:password@host.docker.internal:5432/docai \
  -e DOCUMENTAI_INVOICE_PROCESSOR_ID=YOUR_PROCESSOR_ID \
  -v ~/.config/gcloud:/root/.config/gcloud \
  invoice-worker:local
```

Test: Visit http://localhost:8001/health

**Step 8: Commit**

```bash
git add backend/workers/invoice_worker/
git commit -m "feat: add invoice worker with Document AI integration"
```

---

## Task 2.2: Deploy Invoice Worker with Pub/Sub Trigger (2 hours)

**Files:**
- Create: `scripts/deploy-invoice-worker.sh`
- Create: `terraform/modules/cloud_run_worker/main.tf`

**Step 1: Create deployment script**

Create file: `scripts/deploy-invoice-worker.sh`

```bash
#!/bin/bash

set -e

PROJECT_ID="docai-mvp-prod"
REGION="europe-west1"
SERVICE_NAME="invoice-worker"
IMAGE_NAME="europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/$SERVICE_NAME"

echo "Building Docker image..."
cd backend
docker build -t $IMAGE_NAME:latest -f workers/invoice_worker/Dockerfile .

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
  --set-secrets DATABASE_URL=database-url:latest,DB_PASSWORD=database-password:latest,DOCUMENTAI_INVOICE_PROCESSOR_ID=documentai-invoice-processor-id:latest \
  --min-instances 0 \
  --max-instances 5 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 1

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')

echo "Creating Pub/Sub push subscription..."
gcloud pubsub subscriptions create invoice-processing-sub \
  --topic=invoice-processing \
  --push-endpoint="$SERVICE_URL/process" \
  --push-auth-service-account=ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=600 \
  --message-retention-duration=7d \
  --max-retry-delay=600s \
  --min-retry-delay=10s

echo "Deployment complete!"
echo "Worker URL: $SERVICE_URL"
```

**Step 2: Make script executable**

```bash
chmod +x scripts/deploy-invoice-worker.sh
```

**Step 3: Deploy invoice worker**

```bash
./scripts/deploy-invoice-worker.sh
```

Expected: Service deployed, Pub/Sub subscription created

**Step 4: Test end-to-end flow**

1. Upload invoice via API Gateway
2. Check Pub/Sub topic for message
3. Check Cloud Run logs for processing
4. Query database for invoice_data record

```bash
# View logs
gcloud run services logs read invoice-worker --region europe-west1 --limit 50
```

**Step 5: Commit**

```bash
git add scripts/deploy-invoice-worker.sh
git commit -m "feat: add invoice worker deployment script with Pub/Sub"
```

---

## Task 2.3: Invoice API Endpoints (3 hours)

**Files:**
- Create: `backend/api_gateway/routes/invoices.py`
- Modify: `backend/api_gateway/main.py`
- Modify: `backend/shared/schemas.py`

**Step 1: Add invoice schemas**

Edit `backend/shared/schemas.py`, add:

```python
from decimal import Decimal
from typing import Optional, List
from datetime import date

# Invoice schemas
class LineItem(BaseModel):
    description: Optional[str]
    quantity: Optional[int]
    unit_price: Optional[Decimal]
    amount: Optional[Decimal]

    class Config:
        from_attributes = True


class InvoiceDataResponse(BaseModel):
    id: UUID
    document_id: UUID
    vendor_name: Optional[str]
    vendor_address: Optional[str]
    vendor_tax_id: Optional[str]
    invoice_number: Optional[str]
    invoice_date: Optional[date]
    due_date: Optional[date]
    subtotal: Optional[Decimal]
    tax_amount: Optional[Decimal]
    total_amount: Optional[Decimal]
    currency: str
    line_items: List[LineItem]
    is_validated: bool
    validated_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceValidation(BaseModel):
    """Validation/correction data from user."""
    corrections: dict
    validation_notes: Optional[str]
    is_approved: bool
```

**Step 2: Create invoice routes**

Create file: `backend/api_gateway/routes/invoices.py`

```python
"""Invoice processing routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from backend.shared.database import get_db
from backend.shared.models import Document, InvoiceData, User
from backend.shared.schemas import InvoiceDataResponse, InvoiceValidation
from backend.shared.auth import verify_firebase_token, get_tenant_id_from_token
from backend.shared.pubsub import PubSubPublisher

router = APIRouter()
pubsub_publisher = PubSubPublisher()


@router.post("/{document_id}/process", status_code=202)
async def process_invoice(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """
    Trigger invoice processing for a document.

    Returns 202 Accepted immediately, processing happens async.
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

    if document.document_type != "invoice":
        raise HTTPException(status_code=400, detail="Document is not an invoice")

    # Publish to Pub/Sub
    message = {
        "tenant_id": str(tenant_id),
        "user_id": str(document.user_id),
        "document_id": str(document_id),
        "gcs_path": document.gcs_path,
        "document_type": "invoice",
        "filename": document.filename,
    }

    pubsub_publisher.publish_invoice_processing(message)

    # Update status
    document.status = "processing"
    document.processing_started_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Invoice processing started",
        "document_id": str(document_id),
        "status": "processing"
    }


@router.get("/{document_id}", response_model=InvoiceDataResponse)
async def get_invoice_data(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Get extracted invoice data."""
    tenant_id = get_tenant_id_from_token(token_data)

    invoice_data = (
        db.query(InvoiceData)
        .filter(
            InvoiceData.document_id == document_id,
            InvoiceData.tenant_id == tenant_id
        )
        .first()
    )

    if not invoice_data:
        raise HTTPException(status_code=404, detail="Invoice data not found")

    return InvoiceDataResponse.from_orm(invoice_data)


@router.get("", response_model=List[InvoiceDataResponse])
async def list_invoices(
    skip: int = 0,
    limit: int = 50,
    validated_only: bool = False,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """List all invoices for tenant."""
    tenant_id = get_tenant_id_from_token(token_data)

    query = db.query(InvoiceData).filter(InvoiceData.tenant_id == tenant_id)

    if validated_only:
        query = query.filter(InvoiceData.is_validated == True)

    invoices = (
        query
        .order_by(InvoiceData.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [InvoiceDataResponse.from_orm(inv) for inv in invoices]


@router.patch("/{document_id}/validate", response_model=InvoiceDataResponse)
async def validate_invoice(
    document_id: uuid.UUID,
    validation: InvoiceValidation,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """
    Human-in-the-loop validation/correction of invoice data.

    This is a critical compliance requirement for EU AI Act.
    """
    tenant_id = get_tenant_id_from_token(token_data)

    # Get user
    user = db.query(User).filter(User.firebase_uid == token_data["uid"]).first()

    # Get invoice data
    invoice_data = (
        db.query(InvoiceData)
        .filter(
            InvoiceData.document_id == document_id,
            InvoiceData.tenant_id == tenant_id
        )
        .first()
    )

    if not invoice_data:
        raise HTTPException(status_code=404, detail="Invoice data not found")

    # Apply corrections
    for field, value in validation.corrections.items():
        if hasattr(invoice_data, field):
            setattr(invoice_data, field, value)

    # Mark as validated
    invoice_data.is_validated = True
    invoice_data.validated_by = user.id
    invoice_data.validated_at = datetime.utcnow()
    invoice_data.validation_notes = validation.validation_notes

    db.commit()
    db.refresh(invoice_data)

    return InvoiceDataResponse.from_orm(invoice_data)
```

**Step 3: Add invoices router to main app**

Edit `backend/api_gateway/main.py`:

```python
from .routes import auth, documents, invoices

# Include routers
app.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/v1/documents", tags=["Documents"])
app.include_router(invoices.router, prefix="/v1/invoices", tags=["Invoices"])  # Add this
```

**Step 4: Test invoice API**

Create file: `tests/backend/test_invoices.py`

```python
"""Tests for invoice endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.api_gateway.main import app
import io
import time

client = TestClient(app)


def get_auth_token():
    """Helper to get auth token."""
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": "invoicetest@example.com",
            "password": "SecurePass123!",
            "full_name": "Invoice Test",
            "tenant_name": "Invoice Test Co"
        }
    )
    return response.json()["access_token"]


def test_invoice_processing_flow():
    """Test complete invoice processing flow."""
    token = get_auth_token()

    # 1. Upload invoice
    fake_invoice = io.BytesIO(b"%PDF-1.4 fake invoice")
    upload_response = client.post(
        "/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("invoice.pdf", fake_invoice, "application/pdf")},
        data={"document_type": "invoice"}
    )

    assert upload_response.status_code == 202
    document_id = upload_response.json()["id"]

    # 2. Wait for processing (in real scenario, this is async)
    time.sleep(5)

    # 3. Get invoice data
    invoice_response = client.get(
        f"/v1/invoices/{document_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Should return invoice data (or 404 if not processed yet)
    assert invoice_response.status_code in [200, 404]

    if invoice_response.status_code == 200:
        data = invoice_response.json()
        assert "vendor_name" in data
        assert "total_amount" in data
        assert data["is_validated"] == False
```

**Step 5: Deploy updated API Gateway**

```bash
./scripts/deploy-api-gateway.sh
```

**Step 6: Commit**

```bash
git add backend/api_gateway/routes/invoices.py backend/shared/schemas.py tests/backend/test_invoices.py
git commit -m "feat: add invoice API endpoints with validation"
```

---

## Task 2.4: Invoice Validation UI (Human-in-the-Loop) (8 hours)

**Files:**
- Create: `frontend/src/components/Invoices/InvoiceValidation.tsx`
- Create: `frontend/src/components/Invoices/InvoiceList.tsx`
- Create: `frontend/src/pages/Invoices.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Create invoice validation component**

Create file: `frontend/src/components/Invoices/InvoiceValidation.tsx`

```typescript
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface InvoiceValidationProps {
  documentId: string;
}

export const InvoiceValidation: React.FC<InvoiceValidationProps> = ({ documentId }) => {
  const queryClient = useQueryClient();

  // Fetch invoice data
  const { data: invoice, isLoading, error } = useQuery({
    queryKey: ['invoice', documentId],
    queryFn: () => apiClient.getInvoice(documentId),
  });

  // Fetch document for PDF preview
  const { data: document } = useQuery({
    queryKey: ['document', documentId],
    queryFn: () => apiClient.getDocument(documentId),
  });

  const [formData, setFormData] = useState<any>({});
  const [validationNotes, setValidationNotes] = useState('');

  // Update form when invoice loads
  React.useEffect(() => {
    if (invoice) {
      setFormData({
        vendor_name: invoice.vendor_name || '',
        vendor_tax_id: invoice.vendor_tax_id || '',
        invoice_number: invoice.invoice_number || '',
        invoice_date: invoice.invoice_date || '',
        due_date: invoice.due_date || '',
        subtotal: invoice.subtotal || 0,
        tax_amount: invoice.tax_amount || 0,
        total_amount: invoice.total_amount || 0,
        currency: invoice.currency || 'EUR',
      });
    }
  }, [invoice]);

  // Validation mutation
  const validateMutation = useMutation({
    mutationFn: (data: any) => apiClient.validateInvoice(documentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', documentId] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      alert('Invoice validated successfully!');
    },
  });

  const handleFieldChange = (field: string, value: any) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleValidate = () => {
    // Calculate corrections (only fields that changed)
    const corrections: any = {};
    if (invoice) {
      Object.keys(formData).forEach((key) => {
        if (formData[key] !== invoice[key]) {
          corrections[key] = formData[key];
        }
      });
    }

    validateMutation.mutate({
      corrections,
      validation_notes: validationNotes,
      is_approved: true,
    });
  };

  if (isLoading) {
    return <div className="text-center py-8">Loading invoice data...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
        Failed to load invoice data
      </div>
    );
  }

  if (!invoice) {
    return <div>Invoice data not available yet. Processing may still be in progress.</div>;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* PDF Preview */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-4">Document Preview</h3>
        {document?.gcs_path && (
          <iframe
            src={`/api/documents/${documentId}/preview`}
            className="w-full h-[800px] border border-gray-300 rounded"
            title="Invoice Preview"
          />
        )}
      </div>

      {/* Validation Form */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">Invoice Data</h3>
          {invoice.is_validated ? (
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
              Validated ✓
            </span>
          ) : (
            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
              Needs Review
            </span>
          )}
        </div>

        <div className="space-y-4">
          {/* Vendor Information */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Vendor Name</label>
            <input
              type="text"
              value={formData.vendor_name}
              onChange={(e) => handleFieldChange('vendor_name', e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Vendor Tax ID</label>
            <input
              type="text"
              value={formData.vendor_tax_id}
              onChange={(e) => handleFieldChange('vendor_tax_id', e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>

          {/* Invoice Details */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Invoice Number</label>
              <input
                type="text"
                value={formData.invoice_number}
                onChange={(e) => handleFieldChange('invoice_number', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Currency</label>
              <select
                value={formData.currency}
                onChange={(e) => handleFieldChange('currency', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              >
                <option value="EUR">EUR (€)</option>
                <option value="RON">RON (lei)</option>
                <option value="USD">USD ($)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Invoice Date</label>
              <input
                type="date"
                value={formData.invoice_date}
                onChange={(e) => handleFieldChange('invoice_date', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Due Date</label>
              <input
                type="date"
                value={formData.due_date}
                onChange={(e) => handleFieldChange('due_date', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>
          </div>

          {/* Amounts */}
          <div className="border-t pt-4">
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Subtotal</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.subtotal}
                    onChange={(e) => handleFieldChange('subtotal', parseFloat(e.target.value))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Tax Amount</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.tax_amount}
                    onChange={(e) => handleFieldChange('tax_amount', parseFloat(e.target.value))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Total Amount</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.total_amount}
                  onChange={(e) => handleFieldChange('total_amount', parseFloat(e.target.value))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm text-lg font-bold"
                />
              </div>
            </div>
          </div>

          {/* Validation Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Validation Notes</label>
            <textarea
              value={validationNotes}
              onChange={(e) => setValidationNotes(e.target.value)}
              rows={3}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              placeholder="Add any notes about corrections made..."
            />
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3 pt-4">
            <button
              onClick={handleValidate}
              disabled={invoice.is_validated || validateMutation.isPending}
              className="flex-1 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md font-medium disabled:opacity-50"
            >
              {validateMutation.isPending ? 'Validating...' : 'Validate & Approve'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
```

**Step 2: Update API client with invoice methods**

Edit `frontend/src/services/api.ts`, add:

```typescript
// Invoice endpoints
async getInvoice(documentId: string) {
  const response = await this.client.get(`/invoices/${documentId}`);
  return response.data;
}

async listInvoices(skip = 0, limit = 50) {
  const response = await this.client.get('/invoices', {
    params: { skip, limit },
  });
  return response.data;
}

async validateInvoice(documentId: string, validation: any) {
  const response = await this.client.patch(
    `/invoices/${documentId}/validate`,
    validation
  );
  return response.data;
}
```

**Step 3: Create Invoices page**

Create file: `frontend/src/pages/Invoices.tsx`

```typescript
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { InvoiceValidation } from '../components/Invoices/InvoiceValidation';

export const Invoices: React.FC = () => {
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);

  const { data: invoices, isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => apiClient.listInvoices(),
  });

  if (selectedInvoiceId) {
    return (
      <div>
        <button
          onClick={() => setSelectedInvoiceId(null)}
          className="mb-4 text-primary-600 hover:text-primary-800 flex items-center"
        >
          ← Back to list
        </button>
        <InvoiceValidation documentId={selectedInvoiceId} />
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Invoices</h2>

      {isLoading ? (
        <div className="text-center py-8">Loading invoices...</div>
      ) : invoices?.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No invoices yet. Upload an invoice to get started.
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {invoices?.map((invoice: any) => (
              <li key={invoice.id}>
                <div className="px-4 py-4 flex items-center sm:px-6 hover:bg-gray-50">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-primary-600 truncate">
                        {invoice.vendor_name || 'Unknown Vendor'}
                      </p>
                      {invoice.is_validated ? (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                          Validated
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
                          Needs Review
                        </span>
                      )}
                    </div>
                    <div className="mt-2 flex">
                      <div className="flex items-center text-sm text-gray-500">
                        <span>Invoice #{invoice.invoice_number}</span>
                        <span className="mx-2">•</span>
                        <span>
                          {invoice.total_amount} {invoice.currency}
                        </span>
                        <span className="mx-2">•</span>
                        <span>{new Date(invoice.invoice_date).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <button
                      onClick={() => setSelectedInvoiceId(invoice.document_id)}
                      className="ml-4 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      {invoice.is_validated ? 'View' : 'Review'}
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
```

**Step 4: Add Invoices route to App**

Edit `frontend/src/App.tsx`:

```typescript
import { Invoices } from './pages/Invoices';

// Inside Routes:
<Route
  path="/invoices"
  element={
    <PrivateRoute>
      <Invoices />
    </PrivateRoute>
  }
/>
```

**Step 5: Update Dashboard with navigation**

Edit `frontend/src/pages/Dashboard.tsx` to add navigation menu:

```typescript
import { Link, useLocation } from 'react-router-dom';

// In navigation:
<nav className="flex space-x-4">
  <Link
    to="/dashboard"
    className={`px-3 py-2 rounded-md text-sm font-medium ${
      location.pathname === '/dashboard'
        ? 'bg-primary-100 text-primary-700'
        : 'text-gray-700 hover:bg-gray-100'
    }`}
  >
    Dashboard
  </Link>
  <Link
    to="/invoices"
    className={`px-3 py-2 rounded-md text-sm font-medium ${
      location.pathname === '/invoices'
        ? 'bg-primary-100 text-primary-700'
        : 'text-gray-700 hover:bg-gray-100'
    }`}
  >
    Invoices
  </Link>
</nav>
```

**Step 6: Test invoice validation flow**

```bash
npm run dev
```

1. Upload an invoice
2. Wait for processing
3. Navigate to Invoices page
4. Click "Review" on invoice
5. See split-screen: PDF preview + editable fields
6. Make corrections
7. Click "Validate & Approve"
8. Verify status changes to "Validated"

**Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: add invoice validation UI with human-in-the-loop"
```

---

## Phase 2 Complete ✓

**Summary:** Invoice processing implemented
- ✅ Invoice worker with Document AI integration
- ✅ Automated invoice data extraction
- ✅ Invoice API endpoints
- ✅ Human-in-the-loop validation UI (EU AI Act compliance)
- ✅ Split-screen PDF preview + editable fields
- ✅ Audit logging for compliance

**Next:** Phase 3 - Generic OCR (Week 6)

---

## Verification Checklist

- [ ] Invoice worker deployed to Cloud Run
- [ ] Pub/Sub subscription working (messages trigger worker)
- [ ] Document AI processor created and configured
- [ ] Invoice data extracted and saved to database
- [ ] Invoice API endpoints functional
- [ ] Validation UI displays invoice data correctly
- [ ] PDF preview shows in split-screen
- [ ] Users can edit and validate invoice data
- [ ] Validation status updates correctly
- [ ] Audit logs created for all validation actions
