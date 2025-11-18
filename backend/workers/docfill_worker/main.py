"""Document filling worker - extract ID data and fill forms."""

from fastapi import FastAPI, Request, HTTPException
from sqlalchemy.orm import Session
import json
from datetime import datetime
import traceback
import base64
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import SessionLocal
from shared.models import Document, DocumentFillingResult, AuditLog
from shared.config import get_settings
from processor import DocumentFillingProcessor

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
        "document_id": "uuid",  # ID card document
        "gcs_path": "gs://...",
        "template_name": "romanian_standard_form"
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
        template_name = message["template_name"]

        print(f"Processing document filling: Document={document_id}, Template={template_name}")

        # Get database session
        db = SessionLocal()

        try:
            # Get document
            document = db.query(Document).filter(
                Document.id == document_id
            ).first()

            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Update status
            document.status = "processing"
            document.processing_started_at = datetime.utcnow()
            db.commit()

            # Step 1: Extract ID data
            print(f"Extracting ID data from {gcs_path}")
            extracted_data = processor.extract_id_data(gcs_path)

            print(f"Extracted: {extracted_data.get('family_name')} {extracted_data.get('given_names')}")

            # Step 2: Check if template exists, if not, skip PDF filling
            template_path = processor._get_template_path(template_name)
            filled_pdf_uri = None

            if template_path:
                # Fill PDF form
                output_gcs_path = f"gs://{settings.gcs_bucket_processed}/{tenant_id}/{document_id}/filled_form.pdf"

                print(f"Filling PDF form: {template_name}")
                filled_pdf_uri = processor.fill_pdf_form(
                    template_name=template_name,
                    data=extracted_data,
                    output_gcs_path=output_gcs_path
                )

                print(f"Filled PDF saved to {filled_pdf_uri}")
            else:
                print(f"Template {template_name} not found, skipping PDF filling")

            # Update document
            document.gcs_processed_path = filled_pdf_uri
            document.status = "completed"
            document.processing_completed_at = datetime.utcnow()

            # Save filling result
            filling_result = DocumentFillingResult(
                document_id=document_id,
                tenant_id=tenant_id,
                source_document_type="id_card",
                extracted_fields=extracted_data,
                filled_pdf_gcs_path=filled_pdf_uri,
                template_used=template_name
            )
            db.add(filling_result)

            # Create audit log
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                document_id=document_id,
                action="document_filled",
                details={
                    "template_name": template_name,
                    "extracted_fields": list(extracted_data.keys()),
                    "confidence": extracted_data.get("average_confidence"),
                }
            )
            db.add(audit_log)

            db.commit()

            print(f"Document filling completed successfully: {document_id}")
            return {
                "status": "success",
                "document_id": str(document_id),
                "filled_pdf_uri": filled_pdf_uri
            }

        except Exception as e:
            # Update document status to failed
            if document:
                document.status = "failed"
                document.error_message = str(e)
                document.processing_completed_at = datetime.utcnow()
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
    uvicorn.run(app, host="0.0.0.0", port=8006)
