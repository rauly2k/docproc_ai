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
