"""Invoice worker service - processes invoices from Pub/Sub."""

from fastapi import FastAPI, Request, HTTPException
from google.cloud import storage
from sqlalchemy.orm import Session
import json
from datetime import datetime
import traceback
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.shared.database import SessionLocal
from backend.shared.models import Document, InvoiceData, AuditLog
from backend.shared.config import get_settings
from processor import InvoiceProcessor

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
