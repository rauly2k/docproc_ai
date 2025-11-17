# Phase 5: Chat with PDF (RAG) Implementation (Weeks 8-9)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement complete RAG (Retrieval-Augmented Generation) pipeline with pgvector for semantic search and document Q&A.

**Duration:** 2 weeks (80 hours)

**Prerequisites:** Phase 4 completed (summarization working), PostgreSQL with pgvector installed

---

## Task 5.1: RAG Ingestion Worker Service (8 hours)

**Files:**
- Create: `backend/workers/rag_ingest_worker/Dockerfile`
- Create: `backend/workers/rag_ingest_worker/main.py`
- Create: `backend/workers/rag_ingest_worker/ingestion.py`
- Create: `backend/workers/rag_ingest_worker/requirements.txt`

**Step 1: Create RAG ingestion requirements**

Create file: `backend/workers/rag_ingest_worker/requirements.txt`

```txt
# Inherit from parent
-r ../../requirements.txt

# Additional dependencies for RAG
langchain==0.0.340
langchain-google-vertexai==0.0.6
tiktoken==0.5.1
```

**Step 2: Create RAG ingestion pipeline module**

Create file: `backend/workers/rag_ingest_worker/ingestion.py`

```python
"""RAG ingestion pipeline - chunk documents and generate embeddings."""

from google.cloud import storage
from vertexai.language_models import TextEmbeddingModel
import vertexai
from langchain.text_splitter import RecursiveCharacterTextSplitter
import PyPDF2
import io
from typing import List, Dict, Any
import tiktoken

from backend.shared.config import get_settings
from backend.shared.models import DocumentChunk

settings = get_settings()


class RAGIngestionPipeline:
    """Process documents for RAG: extract text, chunk, embed, store."""

    def __init__(self):
        # Initialize Vertex AI
        vertexai.init(project=settings.project_id, location=settings.vertex_ai_location)

        # Initialize embedding model
        self.embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")

        # Storage client
        self.storage_client = storage.Client()

        # Text splitter configuration
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Characters per chunk
            chunk_overlap=200,  # Overlap between chunks for context
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],  # Try these in order
        )

        # Tokenizer for counting tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def ingest_document(
        self,
        gcs_uri: str,
        document_id: str,
        tenant_id: str,
        db_session
    ) -> Dict[str, Any]:
        """
        Complete ingestion pipeline for a document.

        Steps:
        1. Extract text from PDF
        2. Split into chunks
        3. Generate embeddings for each chunk
        4. Store chunks with embeddings in database

        Args:
            gcs_uri: GCS URI of document
            document_id: Document UUID
            tenant_id: Tenant UUID
            db_session: SQLAlchemy session

        Returns:
            Ingestion statistics
        """
        # Step 1: Extract text
        print(f"Extracting text from {gcs_uri}")
        text, metadata = self._extract_text_from_pdf(gcs_uri)

        # Step 2: Split into chunks
        print(f"Splitting text into chunks (size=1000, overlap=200)")
        chunks = self._split_text(text)

        print(f"Created {len(chunks)} chunks")

        # Step 3 & 4: Generate embeddings and store
        print(f"Generating embeddings and storing chunks...")
        stored_count = self._embed_and_store_chunks(
            chunks=chunks,
            document_id=document_id,
            tenant_id=tenant_id,
            db_session=db_session,
            metadata=metadata
        )

        return {
            "total_chunks": len(chunks),
            "stored_chunks": stored_count,
            "total_pages": metadata["page_count"],
            "total_characters": len(text),
        }

    def _extract_text_from_pdf(self, gcs_uri: str) -> tuple[str, Dict[str, Any]]:
        """Extract text from PDF in GCS."""
        # Parse GCS URI
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])

        # Download PDF
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        pdf_bytes = blob.download_as_bytes()

        # Extract text with page tracking
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        page_texts = []

        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            page_texts.append({
                "page_number": page_num + 1,
                "text": page_text,
                "char_count": len(page_text)
            })
            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"

        metadata = {
            "page_count": len(pdf_reader.pages),
            "page_texts": page_texts,
        }

        return text, metadata

    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks using LangChain text splitter."""
        chunks = self.text_splitter.split_text(text)
        return chunks

    def _embed_and_store_chunks(
        self,
        chunks: List[str],
        document_id: str,
        tenant_id: str,
        db_session,
        metadata: Dict[str, Any]
    ) -> int:
        """
        Generate embeddings for chunks and store in database.

        Batches embedding API calls for efficiency.
        """
        stored_count = 0
        batch_size = 5  # Process 5 chunks at a time

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]

            # Generate embeddings for batch
            embeddings = self._get_embeddings_batch(batch_chunks)

            # Store each chunk with its embedding
            for j, (chunk_text, embedding) in enumerate(zip(batch_chunks, embeddings)):
                chunk_index = i + j

                # Determine which page this chunk likely belongs to
                page_number = self._estimate_page_number(chunk_index, len(chunks), metadata["page_count"])

                # Count tokens
                token_count = len(self.tokenizer.encode(chunk_text))

                # Create chunk record
                chunk_record = DocumentChunk(
                    document_id=document_id,
                    tenant_id=tenant_id,
                    chunk_index=chunk_index,
                    content=chunk_text,
                    token_count=token_count,
                    embedding=embedding,
                    metadata={
                        "page_number": page_number,
                        "chunk_size": len(chunk_text),
                    }
                )

                db_session.add(chunk_record)
                stored_count += 1

            # Commit after each batch
            db_session.commit()
            print(f"Stored batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size}")

        return stored_count

    def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts."""
        embeddings = self.embedding_model.get_embeddings(texts)
        return [emb.values for emb in embeddings]

    @staticmethod
    def _estimate_page_number(chunk_index: int, total_chunks: int, total_pages: int) -> int:
        """Estimate which page a chunk belongs to."""
        # Simple estimation: distribute chunks evenly across pages
        chunks_per_page = total_chunks / total_pages if total_pages > 0 else 1
        estimated_page = int(chunk_index / chunks_per_page) + 1
        return min(estimated_page, total_pages)


class ChunkRetriever:
    """Retrieve relevant chunks for a query using vector similarity."""

    def __init__(self):
        vertexai.init(project=settings.project_id, location=settings.vertex_ai_location)
        self.embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")

    def retrieve_chunks(
        self,
        query: str,
        tenant_id: str,
        db_session,
        document_ids: List[str] = None,
        max_chunks: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant chunks for a query using vector similarity.

        Args:
            query: User's question
            tenant_id: Tenant ID (for multi-tenancy)
            db_session: SQLAlchemy session
            document_ids: Optional list of document IDs to search within
            max_chunks: Maximum number of chunks to return

        Returns:
            List of relevant chunks with similarity scores
        """
        # Generate embedding for query
        query_embedding = self.embedding_model.get_embeddings([query])[0].values

        # Build SQL query for vector similarity search
        # Using pgvector's <-> operator for cosine distance
        from sqlalchemy import text as sql_text

        if document_ids:
            # Search within specific documents
            doc_filter = "AND document_id IN :document_ids"
            params = {
                "query_vector": str(query_embedding),
                "tenant_id": tenant_id,
                "document_ids": tuple(document_ids),
                "max_chunks": max_chunks
            }
        else:
            # Search across all tenant documents
            doc_filter = ""
            params = {
                "query_vector": str(query_embedding),
                "tenant_id": tenant_id,
                "max_chunks": max_chunks
            }

        query_sql = sql_text(f"""
            SELECT
                id,
                document_id,
                chunk_index,
                content,
                metadata,
                1 - (embedding <=> :query_vector::vector) as similarity
            FROM document_chunks
            WHERE tenant_id = :tenant_id
            {doc_filter}
            ORDER BY embedding <=> :query_vector::vector
            LIMIT :max_chunks
        """)

        results = db_session.execute(query_sql, params).fetchall()

        # Format results
        chunks = []
        for row in results:
            chunks.append({
                "id": str(row.id),
                "document_id": str(row.document_id),
                "chunk_index": row.chunk_index,
                "content": row.content,
                "metadata": row.metadata,
                "similarity": float(row.similarity),
                "relevance_score": round(float(row.similarity) * 100, 1)
            })

        return chunks
```

**Step 3: Create RAG ingestion worker main application**

Create file: `backend/workers/rag_ingest_worker/main.py`

```python
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
```

**Step 4: Create Dockerfile**

Create file: `backend/workers/rag_ingest_worker/Dockerfile`

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
COPY . /app/backend/workers/rag_ingest_worker/

WORKDIR /app/backend/workers/rag_ingest_worker

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8004/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
```

**Step 5: Test locally**

```bash
cd backend/workers/rag_ingest_worker

# Build
docker build -t rag-ingest-worker:local -f Dockerfile ../..

# Run
docker run -p 8004:8004 \
  -e PROJECT_ID=docai-mvp-prod \
  -e VERTEX_AI_LOCATION=us-central1 \
  -e DATABASE_URL=postgresql://docai:password@host.docker.internal:5432/docai \
  -v ~/.config/gcloud:/root/.config/gcloud \
  rag-ingest-worker:local
```

**Step 6: Commit**

```bash
git add backend/workers/rag_ingest_worker/
git commit -m "feat: add RAG ingestion worker with chunking and embedding"
```

---

## Task 5.2: Deploy RAG Ingestion Worker (2 hours)

**Files:**
- Create: `scripts/deploy-rag-ingest-worker.sh`

**Step 1: Create deployment script**

Create file: `scripts/deploy-rag-ingest-worker.sh`

```bash
#!/bin/bash

set -e

PROJECT_ID="docai-mvp-prod"
REGION="europe-west1"
SERVICE_NAME="rag-ingest-worker"
IMAGE_NAME="europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/$SERVICE_NAME"

echo "Building Docker image..."
cd backend
docker build -t $IMAGE_NAME:latest -f workers/rag_ingest_worker/Dockerfile .

echo "Pushing to Artifact Registry..."
docker push $IMAGE_NAME:latest

echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --service-account ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,VERTEX_AI_LOCATION=us-central1,ENVIRONMENT=prod \
  --set-secrets DATABASE_URL=database-url:latest,DB_PASSWORD=database-password:latest \
  --min-instances 0 \
  --max-instances 5 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 1

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')

echo "Creating Pub/Sub push subscription..."
gcloud pubsub subscriptions create rag-ingestion-sub \
  --topic=rag-ingestion \
  --push-endpoint="$SERVICE_URL/process" \
  --push-auth-service-account=ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=600 \
  --message-retention-duration=7d

echo "Deployment complete!"
echo "Worker URL: $SERVICE_URL"
```

**Step 2: Deploy**

```bash
chmod +x scripts/deploy-rag-ingest-worker.sh
./scripts/deploy-rag-ingest-worker.sh
```

**Step 3: Commit**

```bash
git add scripts/deploy-rag-ingest-worker.sh
git commit -m "feat: add RAG ingestion worker deployment"
```

---

## Task 5.3: Chat API Endpoints (6 hours)

**Files:**
- Create: `backend/api_gateway/routes/chat.py`
- Modify: `backend/api_gateway/main.py`
- Modify: `backend/shared/schemas.py`

**Step 1: Add chat schemas**

Edit `backend/shared/schemas.py`, add:

```python
from typing import List, Optional

# Chat schemas
class ChatQueryRequest(BaseModel):
    """Request to query documents via chat."""
    question: str = Field(..., min_length=1, max_length=500)
    document_ids: Optional[List[UUID]] = None  # If None, search all documents
    max_chunks: int = Field(default=5, ge=1, le=10)
    model: str = Field(default="flash", pattern="^(flash|pro)$")


class ChatSource(BaseModel):
    """Source chunk for chat answer."""
    document_id: UUID
    chunk_index: int
    content: str
    relevance_score: float
    metadata: dict


class ChatResponse(BaseModel):
    """Chat response with answer and sources."""
    answer: str
    sources: List[ChatSource]
    model_used: str
    total_chunks_searched: int
```

**Step 2: Create chat routes**

Create file: `backend/api_gateway/routes/chat.py`

```python
"""Chat with PDF routes - RAG-powered Q&A."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from typing import List
import uuid

from backend.shared.database import get_db
from backend.shared.models import Document, DocumentChunk
from backend.shared.schemas import ChatQueryRequest, ChatResponse, ChatSource
from backend.shared.auth import verify_firebase_token, get_tenant_id_from_token
from backend.shared.pubsub import PubSubPublisher

# Import RAG components
from vertexai.language_models import TextEmbeddingModel
from vertexai.preview.generative_models import GenerativeModel
import vertexai
from backend.shared.config import get_settings

settings = get_settings()
vertexai.init(project=settings.project_id, location=settings.vertex_ai_location)

router = APIRouter()
pubsub_publisher = PubSubPublisher()

# Initialize models
embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
flash_model = GenerativeModel("gemini-1.5-flash")
pro_model = GenerativeModel("gemini-1.5-pro")


@router.post("/{document_id}/index", status_code=202)
async def index_document_for_chat(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Trigger RAG indexing for a document (chunking + embedding)."""
    tenant_id = get_tenant_id_from_token(token_data)

    # Get document
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
    }

    pubsub_publisher.publish_rag_ingestion(message)

    return {
        "message": "Document indexing started",
        "document_id": str(document_id)
    }


@router.post("/query", response_model=ChatResponse)
async def query_documents(
    request: ChatQueryRequest,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """
    Query documents using RAG (Retrieval-Augmented Generation).

    Steps:
    1. Embed the question
    2. Retrieve most relevant chunks using vector similarity
    3. Build context from retrieved chunks
    4. Generate answer using LLM with context
    5. Return answer with sources
    """
    tenant_id = get_tenant_id_from_token(token_data)

    # Step 1: Embed question
    query_embedding = embedding_model.get_embeddings([request.question])[0].values

    # Step 2: Vector similarity search
    if request.document_ids:
        # Search within specific documents
        doc_ids_str = ", ".join([f"'{str(doc_id)}'" for doc_id in request.document_ids])
        doc_filter = f"AND document_id IN ({doc_ids_str})"
    else:
        doc_filter = ""

    # pgvector similarity search
    query_sql = sql_text(f"""
        SELECT
            id,
            document_id,
            chunk_index,
            content,
            metadata,
            1 - (embedding <=> :query_vector::vector) as similarity
        FROM document_chunks
        WHERE tenant_id = :tenant_id
        {doc_filter}
        ORDER BY embedding <=> :query_vector::vector
        LIMIT :max_chunks
    """)

    results = db.execute(query_sql, {
        "query_vector": str(query_embedding),
        "tenant_id": str(tenant_id),
        "max_chunks": request.max_chunks
    }).fetchall()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No relevant documents found. Please index documents first."
        )

    # Step 3: Build context from chunks
    context_chunks = []
    sources = []

    for row in results:
        context_chunks.append(row.content)
        sources.append(ChatSource(
            document_id=row.document_id,
            chunk_index=row.chunk_index,
            content=row.content[:200] + "..." if len(row.content) > 200 else row.content,
            relevance_score=round(float(row.similarity) * 100, 1),
            metadata=row.metadata or {}
        ))

    context = "\n\n---\n\n".join(context_chunks)

    # Step 4: Generate answer with LLM
    model = pro_model if request.model == "pro" else flash_model

    prompt = f"""Answer the following question based ONLY on the provided context from the documents.

IMPORTANT RULES:
1. If the answer cannot be found in the context, say "I don't have enough information in the provided documents to answer that question."
2. Do not make up information or use external knowledge
3. Quote relevant parts from the context when appropriate
4. Be concise but complete
5. If multiple documents provide relevant info, synthesize the answer

Context from documents:
{context}

Question: {request.question}

Answer:"""

    response = model.generate_content(prompt)
    answer = response.text

    # Step 5: Return answer with sources
    return ChatResponse(
        answer=answer,
        sources=sources,
        model_used=f"gemini-1.5-{request.model}",
        total_chunks_searched=len(results)
    )


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Get all chunks for a document (for debugging/inspection)."""
    tenant_id = get_tenant_id_from_token(token_data)

    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id,
        DocumentChunk.tenant_id == tenant_id
    ).order_by(DocumentChunk.chunk_index).all()

    return {
        "document_id": str(document_id),
        "total_chunks": len(chunks),
        "chunks": [
            {
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "token_count": chunk.token_count,
                "metadata": chunk.metadata
            }
            for chunk in chunks
        ]
    }
```

**Step 3: Add chat router to main app**

Edit `backend/api_gateway/main.py`:

```python
from .routes import auth, documents, invoices, ocr, summaries, chat

app.include_router(chat.router, prefix="/v1/chat", tags=["Chat with PDF"])
```

**Step 4: Test chat API**

Create file: `tests/backend/test_chat.py`

```python
"""Tests for chat endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.api_gateway.main import app

client = TestClient(app)


def test_query_documents():
    """Test RAG query."""
    # This requires documents to be indexed first
    # Basic structure test
    token = "test-token"  # Mock

    response = client.post(
        "/v1/chat/query",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "What is this document about?",
            "max_chunks": 5,
            "model": "flash"
        }
    )

    # Will fail without auth, but tests structure
    assert response.status_code in [200, 401, 404]
```

**Step 5: Deploy updated API Gateway**

```bash
./scripts/deploy-api-gateway.sh
```

**Step 6: Commit**

```bash
git add backend/api_gateway/routes/chat.py backend/shared/schemas.py tests/backend/test_chat.py
git commit -m "feat: add chat API with RAG vector search"
```

---

## Task 5.4: Chat UI Interface (8 hours)

**Files:**
- Create: `frontend/src/components/Chat/ChatInterface.tsx`
- Create: `frontend/src/components/Chat/ChatMessage.tsx`
- Create: `frontend/src/components/Chat/ChatSources.tsx`
- Create: `frontend/src/pages/ChatWithPDF.tsx`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/App.tsx`

**Step 1: Update API client with chat methods**

Edit `frontend/src/services/api.ts`, add:

```typescript
// Chat endpoints
async indexDocumentForChat(documentId: string) {
  const response = await this.client.post(`/chat/${documentId}/index`);
  return response.data;
}

async queryChatRAG(query: {
  question: string;
  document_ids?: string[];
  max_chunks?: number;
  model?: 'flash' | 'pro';
}) {
  const response = await this.client.post('/chat/query', query);
  return response.data;
}

async getDocumentChunks(documentId: string) {
  const response = await this.client.get(`/chat/${documentId}/chunks`);
  return response.data;
}
```

**Step 2: Create chat message component**

Create file: `frontend/src/components/Chat/ChatMessage.tsx`

```typescript
import React from 'react';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  timestamp?: Date;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  role,
  content,
  sources,
  timestamp
}) => {
  const isUser = role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-3xl ${isUser ? 'order-2' : 'order-1'}`}>
        <div
          className={`rounded-lg px-4 py-2 ${
            isUser
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 text-gray-900'
          }`}
        >
          <p className="whitespace-pre-wrap">{content}</p>
        </div>

        {sources && sources.length > 0 && (
          <div className="mt-2 text-sm">
            <details className="cursor-pointer">
              <summary className="text-gray-600 hover:text-gray-900">
                📚 Sources ({sources.length})
              </summary>
              <div className="mt-2 space-y-2">
                {sources.map((source, idx) => (
                  <div key={idx} className="bg-gray-50 p-2 rounded border border-gray-200">
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-xs font-medium text-gray-700">
                        Chunk {source.chunk_index + 1}
                      </span>
                      <span className="text-xs text-gray-500">
                        {source.relevance_score}% relevant
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">{source.content}</p>
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}

        {timestamp && (
          <div className="mt-1 text-xs text-gray-500">
            {timestamp.toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
};
```

**Step 3: Create chat interface component**

Create file: `frontend/src/components/Chat/ChatInterface.tsx`

```typescript
import React, { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../services/api';
import { ChatMessage } from './ChatMessage';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  timestamp: Date;
}

interface ChatInterfaceProps {
  documentIds?: string[];
  showDocumentSelector?: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  documentIds,
  showDocumentSelector = false
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedModel, setSelectedModel] = useState<'flash' | 'pro'>('flash');
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const queryMutation = useMutation({
    mutationFn: (question: string) =>
      apiClient.queryChatRAG({
        question,
        document_ids: documentIds,
        max_chunks: 5,
        model: selectedModel,
      }),
    onSuccess: (data, question) => {
      // Add user message
      setMessages((prev) => [
        ...prev,
        {
          role: 'user',
          content: question,
          timestamp: new Date(),
        },
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          timestamp: new Date(),
        },
      ]);
    },
    onError: (error: any) => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${error.response?.data?.detail || 'Failed to get answer'}`,
          timestamp: new Date(),
        },
      ]);
    },
  });

  const handleSend = () => {
    if (!input.trim() || queryMutation.isPending) return;

    queryMutation.mutate(input);
    setInput('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-medium">Chat with PDF</h3>
            <p className="text-sm text-gray-500">
              Ask questions about your documents
            </p>
          </div>
          <div className="flex space-x-2">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value as 'flash' | 'pro')}
              className="text-sm border border-gray-300 rounded-md px-2 py-1"
            >
              <option value="flash">Fast (Flash)</option>
              <option value="pro">High Quality (Pro)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg mb-2">👋 Ask me anything about your documents!</p>
            <p className="text-sm">Try questions like:</p>
            <ul className="text-sm mt-2 space-y-1">
              <li>"What is the main topic of this document?"</li>
              <li>"Summarize the key findings"</li>
              <li>"What are the important dates mentioned?"</li>
            </ul>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <ChatMessage
              key={idx}
              role={msg.role}
              content={msg.content}
              sources={msg.sources}
              timestamp={msg.timestamp}
            />
          ))
        )}

        {queryMutation.isPending && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question..."
            rows={2}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || queryMutation.isPending}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
};
```

**Step 4: Create Chat with PDF page**

Create file: `frontend/src/pages/ChatWithPDF.tsx`

```typescript
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { ChatInterface } from '../components/Chat/ChatInterface';

export const ChatWithPDF: React.FC = () => {
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
  });

  // Filter to only indexed documents
  const indexedDocs = documents?.filter((d: any) => d.rag_indexed) || [];

  const toggleDocument = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId)
        ? prev.filter((id) => id !== docId)
        : [...prev, docId]
    );
  };

  return (
    <div className="h-screen flex flex-col p-6">
      <h2 className="text-2xl font-bold mb-4">Chat with Your Documents</h2>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 overflow-hidden">
        {/* Document Selector */}
        <div className="lg:col-span-1 bg-white rounded-lg shadow p-4 overflow-y-auto">
          <h3 className="font-medium mb-3">Select Documents</h3>

          {isLoading ? (
            <div className="text-sm text-gray-500">Loading...</div>
          ) : indexedDocs.length === 0 ? (
            <div className="text-sm text-gray-500">
              No indexed documents. Index a document from the Documents page.
            </div>
          ) : (
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedDocIds.length === 0}
                  onChange={() => setSelectedDocIds([])}
                  className="mr-2"
                />
                <span className="text-sm">All documents</span>
              </label>

              <hr className="my-2" />

              {indexedDocs.map((doc: any) => (
                <label key={doc.id} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedDocIds.includes(doc.id)}
                    onChange={() => toggleDocument(doc.id)}
                    className="mr-2"
                  />
                  <span className="text-sm truncate">{doc.filename}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Chat Interface */}
        <div className="lg:col-span-3 overflow-hidden">
          <ChatInterface
            documentIds={selectedDocIds.length > 0 ? selectedDocIds : undefined}
          />
        </div>
      </div>
    </div>
  );
};
```

**Step 5: Add Chat route to App**

Edit `frontend/src/App.tsx`:

```typescript
import { ChatWithPDF } from './pages/ChatWithPDF';

// Inside Routes:
<Route
  path="/chat"
  element={
    <PrivateRoute>
      <ChatWithPDF />
    </PrivateRoute>
  }
/>
```

**Step 6: Update Dashboard navigation to include Chat**

Edit navigation to add "Chat with PDF" link.

**Step 7: Test chat flow**

```bash
npm run dev
```

1. Index a document
2. Navigate to Chat page
3. Select document(s)
4. Ask questions
5. View answers with sources
6. Test relevance scoring

**Step 8: Deploy frontend**

```bash
cd frontend
vercel --prod
```

**Step 9: Commit**

```bash
git add frontend/src/components/Chat/ frontend/src/pages/ChatWithPDF.tsx frontend/src/services/api.ts
git commit -m "feat: add Chat with PDF UI with document selection"
```

---

## Phase 5 Complete ✓

**Summary:** RAG/Chat with PDF implemented
- ✅ RAG ingestion worker (chunking + embeddings)
- ✅ pgvector similarity search
- ✅ Chat API with context retrieval
- ✅ Chat interface with sources
- ✅ Document selection
- ✅ Model quality selection (Flash/Pro)
- ✅ Source attribution with relevance scores

**Verification:**
- [ ] RAG ingestion worker deployed
- [ ] Documents chunked and embedded
- [ ] pgvector index created
- [ ] Vector similarity search working
- [ ] Chat API returning relevant answers
- [ ] Sources displayed with relevance scores
- [ ] Multi-document chat working
- [ ] Answers accurate and contextual

**Next:** Phase 6 - Document Filling (Week 10)
