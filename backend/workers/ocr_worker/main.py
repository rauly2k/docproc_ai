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
