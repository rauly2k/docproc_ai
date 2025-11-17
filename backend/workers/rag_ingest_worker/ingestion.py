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
