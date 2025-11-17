# Document AI SaaS Platform

AI-powered document processing platform with Phase 5 (Chat with PDF RAG) implementation complete.

## Project Overview

This is a multi-vertical B2B SaaS platform for AI-driven document processing, targeting legal, logistics, finance, healthcare, and administrative sectors.

## Features Implemented

### Phase 5: Chat with PDF (RAG)
- ✅ RAG ingestion pipeline with document chunking
- ✅ Vector embeddings using Vertex AI (textembedding-gecko@003)
- ✅ PostgreSQL with pgvector for similarity search
- ✅ Chat API with context-aware Q&A
- ✅ React frontend with chat interface
- ✅ Document selection and source citations
- ✅ Model quality selection (Gemini Flash/Pro)

## Architecture

### Backend Services
- **API Gateway** (FastAPI): REST API endpoints for chat functionality
- **RAG Ingestion Worker** (FastAPI): Document chunking and embedding generation
- **Shared Modules**: Database models, config, auth, schemas

### Frontend
- **React + TypeScript + Vite**: Modern, fast frontend
- **TailwindCSS**: Utility-first styling
- **React Query**: Data fetching and caching
- **Chat Interface**: Real-time Q&A with source attribution

### Infrastructure (GCP)
- Cloud Run: Serverless deployment
- Cloud SQL (PostgreSQL + pgvector): Vector database
- Pub/Sub: Asynchronous job processing
- Cloud Storage: Document storage
- Vertex AI: Embeddings and LLM

## Directory Structure

```
docproc_ai/
├── backend/
│   ├── shared/                    # Shared modules
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── schemas.py            # Pydantic schemas
│   │   ├── database.py           # Database config
│   │   ├── config.py             # Settings
│   │   ├── auth.py               # Firebase auth
│   │   └── pubsub.py             # Pub/Sub client
│   ├── workers/
│   │   └── rag_ingest_worker/    # RAG ingestion service
│   │       ├── main.py
│   │       ├── ingestion.py      # RAG pipeline
│   │       ├── Dockerfile
│   │       └── requirements.txt
│   └── api_gateway/              # API Gateway
│       ├── main.py
│       ├── routes/
│       │   └── chat.py           # Chat endpoints
│       └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── Chat/             # Chat components
│   │   ├── pages/
│   │   │   └── ChatWithPDF.tsx   # Main chat page
│   │   └── services/
│   │       └── api.ts            # API client
│   └── package.json
├── scripts/
│   └── deploy-rag-ingest-worker.sh
└── docs/
    └── plans/
        └── phase-5-chat-with-pdf-rag.md
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker
- Google Cloud SDK
- PostgreSQL with pgvector extension

### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

2. Install dependencies:
```bash
pip install -r shared/requirements.txt
```

3. Set environment variables:
```bash
export PROJECT_ID=docai-mvp-prod
export VERTEX_AI_LOCATION=us-central1
export DATABASE_URL=postgresql://user:password@localhost:5432/docai
```

4. Initialize database with pgvector:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

5. Run API Gateway:
```bash
cd api_gateway
uvicorn main:app --reload --port 8000
```

6. Run RAG Ingestion Worker:
```bash
cd workers/rag_ingest_worker
uvicorn main:app --reload --port 8004
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Start development server:
```bash
npm run dev
```

4. Open http://localhost:5173

## Database Schema

### Key Tables

**document_chunks** - Stores document chunks with embeddings
```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    tenant_id UUID REFERENCES tenants(id),
    chunk_index INTEGER,
    content TEXT,
    token_count INTEGER,
    embedding VECTOR(768),
    metadata JSONB,
    created_at TIMESTAMP
);

-- Vector similarity index
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

## API Endpoints

### Chat API

**POST `/v1/chat/{document_id}/index`**
- Triggers RAG indexing for a document
- Response: 202 Accepted

**POST `/v1/chat/query`**
- Query documents using RAG
- Request body:
```json
{
  "question": "What is this document about?",
  "document_ids": ["uuid1", "uuid2"],  // optional
  "max_chunks": 5,
  "model": "flash"  // or "pro"
}
```
- Response:
```json
{
  "answer": "The document is about...",
  "sources": [
    {
      "document_id": "uuid",
      "chunk_index": 0,
      "content": "...",
      "relevance_score": 95.3,
      "metadata": {}
    }
  ],
  "model_used": "gemini-1.5-flash",
  "total_chunks_searched": 5
}
```

**GET `/v1/chat/{document_id}/chunks`**
- Get all chunks for a document (debugging)

## Deployment

### Deploy RAG Ingestion Worker

```bash
./scripts/deploy-rag-ingest-worker.sh
```

This will:
1. Build Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run
4. Create Pub/Sub subscription

### Deploy API Gateway

```bash
cd backend
docker build -t api-gateway -f api_gateway/Dockerfile .
docker tag api-gateway europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/api-gateway
docker push europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/api-gateway

gcloud run deploy api-gateway \
  --image europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/api-gateway \
  --region europe-west1 \
  --allow-unauthenticated
```

## Testing

### Test RAG Pipeline

1. Index a document:
```bash
curl -X POST http://localhost:8000/v1/chat/{document_id}/index \
  -H "Authorization: Bearer YOUR_TOKEN"
```

2. Query the document:
```bash
curl -X POST http://localhost:8000/v1/chat/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "question": "What is the main topic?",
    "max_chunks": 5,
    "model": "flash"
  }'
```

### Test Frontend

1. Open http://localhost:5173
2. Select documents from the sidebar
3. Ask questions in the chat interface
4. View answers with source citations

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation
- **Vertex AI**: Embeddings and LLM (Gemini)
- **LangChain**: Text splitting and chunking
- **pgvector**: Vector similarity search
- **PyPDF2**: PDF text extraction

### Frontend
- **React 18**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool
- **TailwindCSS**: Utility-first CSS
- **React Query**: Data fetching
- **Axios**: HTTP client

### Infrastructure
- **Google Cloud Run**: Serverless containers
- **Cloud SQL**: Managed PostgreSQL
- **Pub/Sub**: Message queue
- **Cloud Storage**: File storage
- **Vertex AI**: ML/AI services

## Cost Estimates

### MVP Phase (Monthly)
- Cloud Run (API Gateway + Workers): $10-50
- Cloud SQL (db-f1-micro): $10
- Cloud Storage: $2-5
- Pub/Sub: $5-15
- Vertex AI (Embeddings + LLM): $50-150 (usage-based)

**Total: $77-230/month**

## Next Steps

### Phase 6: Document Filling (Week 10)
- ID extraction with Document AI
- PDF form filling
- Romanian ID card support

### Phase 7: Polish & Beta Launch (Weeks 11-12)
- Frontend polish
- Monitoring & logging
- Performance optimization
- Security review
- Beta user onboarding

## Contributing

This is currently a solo developer project. For questions or issues, please create a GitHub issue.

## License

Proprietary - All rights reserved

## Support

For support, email: support@docai.example.com
