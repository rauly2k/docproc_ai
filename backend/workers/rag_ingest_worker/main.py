"""RAG ingestion worker - processes documents for semantic search."""

from fastapi import FastAPI, Request, HTTPException
from sqlalchemy.orm import Session
import json
from datetime import datetime
import traceback
import base64

from backend.shared.database import SessionLocal
from backend.shared.models import Document, AuditLog
from backend.shared.config import get_settings
from .ingestion import RAGIngestionPipeline

settings = get_settings()
app = FastAPI(title="RAG Ingestion Worker")

# Initialize pipeline
pipeline = RAGIngestionPipeline()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rag-ingest-worker"}


@app.post("/process")
async def process_rag_ingestion(request: Request):
    """
    Process RAG ingestion from Pub/Sub push subscription.

    Expected message format:
    {
        "tenant_id": "uuid",
        "user_id": "uuid",
        "document_id": "uuid",
        "gcs_path": "gs://bucket/path"
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

        print(f"Processing RAG ingestion: {document_id} from {gcs_path}")

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

            # Run ingestion pipeline
            print(f"Running RAG ingestion pipeline...")
            stats = pipeline.ingest_document(
                gcs_uri=gcs_path,
                document_id=document_id,
                tenant_id=tenant_id,
                db_session=db
            )

            print(f"Ingestion complete: {stats['stored_chunks']} chunks stored")

            # Update document status
            document.status = "completed"
            document.rag_indexed = True
            document.processing_completed_at = datetime.utcnow()

            # Create audit log
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                document_id=document_id,
                action="rag_indexed",
                details={
                    "total_chunks": stats["total_chunks"],
                    "stored_chunks": stats["stored_chunks"],
                    "total_pages": stats["total_pages"],
                }
            )
            db.add(audit_log)

            db.commit()

            print(f"RAG ingestion completed successfully: {document_id}")
            return {
                "status": "success",
                "document_id": str(document_id),
                "chunks_created": stats["stored_chunks"]
            }

        except Exception as e:
            # Update document status to failed
            document.status = "failed"
            document.error_message = str(e)
            document.processing_completed_at = datetime.utcnow()
            db.commit()

            print(f"Error in RAG ingestion {document_id}: {e}")
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
    uvicorn.run(app, host="0.0.0.0", port=8004)
