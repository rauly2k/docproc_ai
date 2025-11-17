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
