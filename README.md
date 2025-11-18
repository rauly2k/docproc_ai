# Document AI SaaS Platform

AI-powered document processing platform for B2B customers.

## Features

- Invoice Processing with human-in-the-loop validation
- Generic OCR (Document AI + Gemini Vision)
- **Document Summarization (Vertex AI)** ✅ Phase 4 Implemented
- Chat with PDF (RAG with pgvector)
- Document Filling (ID extraction + PDF form filling)

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy
- **Frontend:** React, TypeScript, Tailwind CSS
- **Cloud:** Google Cloud Platform
- **Database:** Cloud SQL PostgreSQL with pgvector
- **Infrastructure:** Terraform, Docker, Cloud Run
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

### Phase 6: Document Filling (Current)
- ✅ Document filling worker with Document AI ID extraction
- ✅ ID data extraction from Romanian ID cards, EU IDs, and passports
- ✅ PDF form filling using PyPDFForm
- ✅ Template system for different form types
- ✅ Filling API endpoints
- ✅ Frontend UI with template selection
- ✅ Download filled PDFs

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
# Document AI Processing Platform

AI-driven document processing SaaS platform built on Google Cloud Platform.

## Overview

This platform provides intelligent document processing capabilities including:
- Generic OCR (Optical Character Recognition)
- Invoice processing with human-in-the-loop validation
- Document summarization
- Chat with PDF (RAG)
- Automated document filling

## Architecture

- **Backend**: Python FastAPI microservices
- **Frontend**: React with TypeScript
- **Cloud**: Google Cloud Platform
  - Cloud Run (serverless containers)
  - Cloud SQL (PostgreSQL with pgvector)
  - Pub/Sub (message queue)
  - Cloud Storage (file storage)
  - Document AI (OCR and invoice parsing)
  - Vertex AI (LLM services)
- **Authentication**: Firebase Auth

## Project Structure

```
docprocessing_ai/
├── backend/           # Python FastAPI services
│   ├── shared/        # Shared modules (config, auth, models)
│   ├── api_gateway/   # API Gateway service
│   └── workers/       # AI worker services
│       └── summarizer_worker/  # Phase 4: Text summarization
├── frontend/          # React TypeScript app
│   └── src/
│       ├── components/Summaries/  # Summary UI components
│       ├── pages/     # Page components
│       └── services/  # API client
├── scripts/           # Deployment scripts
├── docs/              # Documentation and plans
└── tests/             # Integration tests
```

## Phase 4: Text Summarization Implementation

### Backend Components

1. **Summarizer Worker** (`backend/workers/summarizer_worker/`)
   - `summarizer.py`: Document summarization using Vertex AI (Gemini Flash/Pro)
   - `main.py`: FastAPI worker service with Pub/Sub integration
   - `Dockerfile`: Container configuration
   - `requirements.txt`: Python dependencies

2. **API Gateway** (`backend/api_gateway/`)
   - `routes/summaries.py`: Summary API endpoints
   - Integration with Pub/Sub for async processing

3. **Shared Modules** (`backend/shared/`)
   - `config.py`: Configuration management
   - `models.py`: SQLAlchemy database models
   - `schemas.py`: Pydantic request/response schemas
   - `pubsub.py`: Pub/Sub publisher utilities
   - `auth.py`: Firebase authentication

### Frontend Components

1. **Summary Components** (`frontend/src/components/Summaries/`)
   - `SummaryGenerator.tsx`: UI for generating summaries with model selection
   - `SummaryView.tsx`: Display generated summaries with key points

2. **Pages** (`frontend/src/pages/`)
   - `Summaries.tsx`: Summary list and detail page

3. **API Client** (`frontend/src/services/`)
   - `api.ts`: API client with summary endpoints

### Deployment

```bash
# Deploy summarizer worker to Cloud Run
./scripts/deploy-summarizer-worker.sh
docproc_ai/
├── backend/
│   ├── shared/           # Shared modules (database, models, auth, etc.)
│   ├── api_gateway/      # Main API Gateway service
│   └── workers/          # AI worker services
│       ├── ocr_worker/   # OCR processing worker
│       ├── invoice_worker/  # Invoice processing worker
│       ├── summarizer_worker/  # Text summarization worker
│       ├── rag_ingest_worker/  # RAG document indexing worker
│       └── docfill_worker/  # Document filling worker (Phase 6)
├── frontend/             # React frontend
│   └── src/
│       ├── components/
│       ├── services/
│       └── pages/
├── scripts/              # Deployment and utility scripts
├── docs/                 # Documentation
│   └── plans/           # Implementation phase plans
└── terraform/           # Infrastructure as Code
```

## Phase 3: Generic OCR (Current Implementation)

This repository currently implements **Phase 3: Generic OCR** with the following features:

### Backend Components

1. **OCR Worker Service** (`backend/workers/ocr_worker/`)
   - Hybrid OCR approach supporting multiple methods:
     - Document AI OCR Processor (default)
     - Vision API (fallback)
     - Gemini Vision (for handwritten/messy docs)
   - Pub/Sub integration for asynchronous processing
   - Automatic confidence scoring and layout extraction

2. **OCR API Routes** (`backend/api_gateway/routes/ocr.py`)
   - `POST /v1/ocr/{document_id}/extract` - Trigger OCR extraction
   - `GET /v1/ocr/{document_id}` - Get OCR results

3. **Shared Backend Modules** (`backend/shared/`)
   - Database models and schemas
   - Firebase authentication utilities
   - Pub/Sub publisher
   - Configuration management

### Frontend Components

1. **OCR Results Component** (`frontend/src/components/OCR/OCRResults.tsx`)
   - Display extracted text
   - Show confidence scores and metadata
   - Copy to clipboard functionality
   - Download as TXT file

2. **API Client** (`frontend/src/services/api.ts`)
   - Typed API client for all backend endpoints
   - OCR methods integration
   - Authentication token management

## Getting Started

### Prerequisites
# Document AI SaaS Platform - Phase 2 Implementation

This repository contains the implementation of Phase 2 (Invoice Processing) of the Document AI SaaS platform.
# Anima X - AI-Powered Document Processing Platform

![Phase](https://img.shields.io/badge/Phase-1%20Complete-success)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![GCP](https://img.shields.io/badge/Platform-Google%20Cloud-blue)

Anima X is a B2B SaaS platform for AI-powered document processing, built with an all-Python architecture on Google Cloud Platform. It provides intelligent document processing capabilities including OCR, invoice parsing, document summarization, and RAG-powered chat with PDFs.

## Features

### Phase 1 (Current - Core Platform)
✅ **API Gateway** - FastAPI-based REST API with Firebase Authentication
✅ **Multi-Tenancy** - Secure tenant isolation with row-level security
✅ **Document Upload** - File upload to Google Cloud Storage
✅ **Authentication** - Firebase Auth integration with custom claims
✅ **Database** - PostgreSQL with pgvector for RAG
✅ **Pub/Sub Integration** - Async job processing architecture

### Upcoming Phases
🔜 **Phase 2** - Invoice Processing with Document AI
🔜 **Phase 3** - Generic OCR
🔜 **Phase 4** - Text Summarization with Vertex AI
🔜 **Phase 5** - Chat with PDF (RAG)
🔜 **Phase 6** - Document Filling (ID extraction + PDF forms)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend (Vercel)                  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI API Gateway (Cloud Run)                │
│  - Firebase Auth  - Multi-tenancy  - Request routing        │
└────────┬───────────────────────────────────┬────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────────┐          ┌──────────────────────────┐
│  Google Pub/Sub     │          │  Cloud SQL (PostgreSQL)  │
│  Message Queue      │          │  + pgvector extension    │
└────────┬────────────┘          └──────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│           Python AI Workers (Cloud Run)                      │
│  Invoice | OCR | Summarizer | RAG Ingest | RAG Query        │
└──────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Backend
- **Language:** Python 3.11+
- **API Framework:** FastAPI 0.104+
- **Database:** PostgreSQL 15 with pgvector
- **ORM:** SQLAlchemy 2.0+
- **Migrations:** Alembic
- **Authentication:** Firebase Admin SDK

### Infrastructure (GCP)
- **Compute:** Cloud Run (serverless containers)
- **Database:** Cloud SQL PostgreSQL
- **Storage:** Google Cloud Storage
- **Messaging:** Pub/Sub
- **AI Services:** Document AI, Vertex AI, Vision API
- **Auth:** Firebase Authentication
- **Secrets:** Secret Manager

### AI/ML
- **Document AI:** Invoice parsing, OCR, ID extraction
- **Vertex AI:** Gemini 1.5 Flash/Pro, Claude 3.5 Sonnet
- **Embeddings:** textembedding-gecko@003 (768 dimensions)
- **Vector DB:** pgvector (PostgreSQL extension)

## Project Structure

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

See [docs/plans/phase-4-text-summarization.md](docs/plans/phase-4-text-summarization.md) for detailed implementation steps.

## Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Summary Endpoints

- `POST /v1/summaries/{document_id}/generate` - Trigger summary generation
- `GET /v1/summaries/{document_id}` - Get document summary
- `GET /v1/summaries` - List all summaries
- `DELETE /v1/summaries/{document_id}` - Delete summary

## Features

### Summary Generation Options

**Model Preferences:**
- `auto`: Automatically select best model based on document
- `flash`: Fast, cost-effective (Gemini 1.5 Flash)
- `pro`: High quality (Gemini 1.5 Pro)

**Summary Types:**
- `concise`: 3-5 bullet points
- `detailed`: Comprehensive summary with sections

## License

MIT License
### Prerequisites
│   ├── shared/              # Shared modules (database, models, auth, etc.)
│   ├── api_gateway/         # FastAPI API Gateway
│   ├── workers/
│   │   └── invoice_worker/  # Invoice processing worker
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── Invoices/    # Invoice validation UI
│   │   ├── pages/
│   │   ├── services/
│   │   └── main.tsx
│   └── package.json
├── scripts/                 # Deployment scripts
├── tests/                   # Tests
└── docs/                    # Documentation

```

## Features Implemented (Phase 2)

✅ **Invoice Worker Service**
- Document AI integration for invoice parsing
- Automatic extraction of vendor info, amounts, line items
- Error handling and retry logic

✅ **Invoice API Endpoints**
- `POST /v1/invoices/{document_id}/process` - Trigger processing
- `GET /v1/invoices/{document_id}` - Get extracted data
- `GET /v1/invoices` - List all invoices
- `PATCH /v1/invoices/{document_id}/validate` - Human validation

✅ **Invoice Validation UI**
- Split-screen: PDF preview + editable fields
- Human-in-the-loop validation (EU AI Act compliance)
- Real-time editing and approval workflow

✅ **Database Models**
- Multi-tenant support
- Complete invoice data schema
- Audit logging for compliance

## Prerequisites

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
- GCP Project with required APIs enabled

### Backend Setup

```bash
# Create virtual environment
cd backend
- Google Cloud Platform account
- Google Cloud CLI (`gcloud`)

## Local Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run API Gateway
cd api_gateway
python main.py
```

### Frontend Setup
export PROJECT_ID="docai-mvp-prod"
export DATABASE_URL="postgresql://user:password@localhost:5432/docai"
export DOCUMENTAI_INVOICE_PROCESSOR_ID="your-processor-id"

# Run API Gateway
cd api_gateway
uvicorn main:app --reload --port 8000

# Run Invoice Worker (in another terminal)
cd workers/invoice_worker
uvicorn main:app --reload --port 8001
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# Edit .env with your API base URL
# Edit .env with your configuration

# Run development server
npm run dev
```

### Running OCR Worker

```bash
cd backend/workers/ocr_worker
python main.py
```

## Deployment

### Deploy OCR Worker to Cloud Run

```bash
# Make sure you're authenticated with GCP
gcloud auth login
gcloud config set project docai-mvp-prod

# Run deployment script
./scripts/deploy-ocr-worker.sh
```

This will:
1. Build Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run
4. Create Pub/Sub subscription
## Deployment

### Deploy Invoice Worker

```bash
./scripts/deploy-invoice-worker.sh
```

This script will:
1. Build Docker image for invoice worker
2. Push to Google Artifact Registry
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
./scripts/deploy-api-gateway.sh
```

This script will:
1. Build Docker image for API gateway
2. Push to Google Artifact Registry
3. Deploy to Cloud Run

## Environment Variables

### Backend

- `PROJECT_ID` - GCP Project ID
- `REGION` - GCP Region (default: europe-west1)
- `ENVIRONMENT` - Environment (dev/prod)
- `DATABASE_URL` - PostgreSQL connection string
- `DOCUMENTAI_OCR_PROCESSOR_ID` - Document AI OCR Processor ID
- `FIREBASE_CREDENTIALS_PATH` - Path to Firebase credentials JSON

### Frontend

- `VITE_API_BASE_URL` - Backend API base URL
- `VITE_FIREBASE_CONFIG` - Firebase configuration

## Database Schema

The platform uses PostgreSQL with the following key tables:
- `tenants` - Multi-tenancy support
- `users` - User accounts
- `documents` - Uploaded documents
- `ocr_results` - OCR extraction results
- `invoice_data` - Extracted invoice data
- `document_summaries` - Generated summaries
- `document_chunks` - RAG embeddings
- `audit_logs` - Compliance audit trail
- `PROJECT_ID` - GCP project ID
- `REGION` - GCP region (default: europe-west1)
- `ENVIRONMENT` - dev/prod
- `DATABASE_URL` - PostgreSQL connection string
- `DOCUMENTAI_INVOICE_PROCESSOR_ID` - Document AI processor ID
- `GCS_BUCKET_UPLOADS` - GCS bucket for uploads
- `GCS_BUCKET_PROCESSED` - GCS bucket for processed files

### Frontend

- `VITE_API_URL` - API Gateway URL
- `VITE_FIREBASE_*` - Firebase configuration

## Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm test
```

## API Documentation

Once the API Gateway is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Local: http://localhost:8000/docs
- Production: https://your-api-gateway-url/docs

## Phase 2 Verification Checklist

- [ ] Invoice worker deployed to Cloud Run
- [ ] Pub/Sub subscription working
- [ ] Document AI processor created
- [ ] Invoice data extracted and saved
- [ ] Invoice API endpoints functional
- [ ] Validation UI displays correctly
- [ ] Users can validate invoices
- [ ] Audit logs created
- [ ] Multi-tenancy working

## Next Steps

See `docs/plans/phase-3-generic-ocr.md` for Phase 3 implementation.

## License

Private - All Rights Reserved
│   ├── shared/                      # Shared utilities across services
│   │   ├── models.py                # SQLAlchemy database models
│   │   ├── schemas.py               # Pydantic validation schemas
│   │   ├── database.py              # Database connection
│   │   ├── config.py                # Configuration management
│   │   ├── auth.py                  # Firebase Auth utilities
│   │   ├── gcs.py                   # Google Cloud Storage utilities
│   │   └── pubsub.py                # Pub/Sub utilities
│   │
│   ├── api_gateway/                 # Main API Gateway service
│   │   ├── main.py                  # FastAPI application
│   │   ├── routes/                  # API endpoints
│   │   │   ├── auth.py              # Authentication
│   │   │   ├── documents.py         # Document management
│   │   │   ├── invoices.py          # Invoice processing
│   │   │   ├── ocr.py               # OCR
│   │   │   ├── summaries.py         # Summarization
│   │   │   ├── chat.py              # Chat with PDF (RAG)
│   │   │   ├── filling.py           # Document filling
│   │   │   └── admin.py             # Admin endpoints
│   │   ├── middleware/              # Custom middleware
│   │   │   ├── auth_middleware.py   # Authentication
│   │   │   └── tenant_middleware.py # Multi-tenancy
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── workers/                     # AI worker services (Phase 2+)
│   │   ├── invoice_worker/
│   │   ├── ocr_worker/
│   │   ├── summarizer_worker/
│   │   ├── rag_ingest_worker/
│   │   ├── rag_query_worker/
│   │   └── docfill_worker/
│   │
│   └── migrations/                  # Alembic migrations
│       ├── alembic.ini
│       ├── env.py
│       └── versions/
│           └── 20251117_001_initial_schema.py
│
├── frontend/                        # React frontend (Phase 1.5+)
├── docs/                            # Documentation
├── .env.example                     # Environment variables template
├── technical_specification.md       # Technical specification
└── README.md                        # This file
```

## Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+ (with pgvector extension)
- Google Cloud Platform account
- Firebase project
- Docker (for local development and deployment)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/docproc_ai.git
   cd docproc_ai
   ```

2. **Set up Python virtual environment**
   ```bash
   cd backend/api_gateway
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**
   ```bash
   # Create database
   createdb animax_dev

   # Enable pgvector extension
   psql animax_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

4. **Configure environment variables**
   ```bash
   # Copy example env file
   cp .env.example .env

   # Edit .env with your actual values
   nano .env
   ```

5. **Run database migrations**
   ```bash
   cd backend/migrations
   alembic upgrade head
   ```

6. **Run the API Gateway locally**
   ```bash
   cd backend/api_gateway
   python main.py
   ```

   The API will be available at `http://localhost:8080`
   - API Docs: `http://localhost:8080/docs`
   - ReDoc: `http://localhost:8080/redoc`

### Environment Variables

See `.env.example` for all required environment variables. Key variables:

- `DATABASE_URL`: PostgreSQL connection string
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `FIREBASE_CREDENTIALS_PATH`: Path to Firebase service account JSON
- `GCS_UPLOADS_BUCKET`: GCS bucket for uploads
- `DOCUMENTAI_*_PROCESSOR_ID`: Document AI processor IDs

### Database Migrations

```bash
# Create a new migration
cd backend/migrations
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## API Documentation

### Authentication

All endpoints (except `/auth/signup`, `/auth/login`, and `/health`) require authentication via Firebase ID token:

```bash
curl -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
     https://api.animax.com/v1/documents
```

### Key Endpoints

**Authentication**
- `POST /v1/auth/signup` - Create new user account
- `POST /v1/auth/login` - Login (client-side Firebase)
- `GET /v1/auth/me` - Get current user info

**Documents**
- `POST /v1/documents/upload` - Upload document
- `GET /v1/documents` - List documents (paginated)
- `GET /v1/documents/{id}` - Get document details
- `DELETE /v1/documents/{id}` - Delete document

**Invoice Processing** (Phase 2)
- `POST /v1/invoices/process` - Process invoice (async)
- `GET /v1/invoices/{document_id}` - Get extracted invoice data
- `PATCH /v1/invoices/{document_id}/validate` - Validate/correct invoice

**OCR** (Phase 3)
- `POST /v1/ocr/extract` - Extract text (async)
- `GET /v1/ocr/{document_id}` - Get OCR results

**Summarization** (Phase 4)
- `POST /v1/summaries/generate` - Generate summary (async)
- `GET /v1/summaries/{document_id}` - Get summary

**Chat with PDF** (Phase 5)
- `POST /v1/chat/index` - Index document for RAG
- `POST /v1/chat/query` - Ask questions about documents

**Admin**
- `GET /v1/admin/stats` - Tenant usage statistics
- `GET /v1/admin/users` - List tenant users
- `GET /v1/admin/audit-logs` - Compliance audit logs

## Deployment

### Google Cloud Run Deployment

1. **Build Docker image**
   ```bash
   cd backend/api_gateway
   docker build -t gcr.io/YOUR_PROJECT_ID/animax-api-gateway:latest .
   ```

2. **Push to Artifact Registry**
   ```bash
   docker push gcr.io/YOUR_PROJECT_ID/animax-api-gateway:latest
   ```

3. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy animax-api-gateway \
     --image gcr.io/YOUR_PROJECT_ID/animax-api-gateway:latest \
     --platform managed \
     --region europe-west1 \
     --allow-unauthenticated \
     --min-instances 1 \
     --max-instances 10 \
     --cpu 1 \
     --memory 512Mi \
     --set-env-vars DATABASE_URL=$DATABASE_URL,GCP_PROJECT_ID=$GCP_PROJECT_ID
   ```

### CI/CD with GitHub Actions

See `.github/workflows/backend-ci.yml` for automated deployment pipeline.

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Implementation Phases

- [x] Phase 0: Infrastructure Setup
- [x] Phase 1: Core Platform
- [x] Phase 2: Invoice Processing
- [x] **Phase 3: Generic OCR** (Current)
- [ ] Phase 4: Text Summarization
- [ ] Phase 5: Chat with PDF (RAG)
- [ ] Phase 6: Document Filling
- [ ] Phase 7: Polish & Beta Launch

## Documentation

See `/docs` directory for:
- [Technical Specification](technical_specification.md)
- [Phase Plans](docs/plans/)
- [Starting Ideas](starting_ideas.md)

## Security

- Firebase Authentication for user management
- Multi-tenant isolation at database level
- Secret management via GCP Secret Manager
- HTTPS/TLS for all communications
- GDPR and EU AI Act compliance measures

## License

Proprietary - All rights reserved

## Support

For support, email: support@docai.example.com
For issues and questions, please contact the development team.
# Run tests (to be implemented)
cd backend
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

## Security

- **Multi-Tenancy:** All queries automatically filtered by tenant_id
- **Authentication:** Firebase JWT token verification
- **Authorization:** Role-based access control (admin, user, viewer)
- **Input Validation:** Pydantic schemas for all API inputs
- **SQL Injection:** SQLAlchemy ORM with parameterized queries
- **File Upload:** MIME type validation, size limits
- **Secrets:** Stored in Google Secret Manager (not in code)
- **CORS:** Configured for frontend domains only

## Compliance

- **GDPR:** Data residency in EU (europe-west1), audit logs, right to erasure
- **EU AI Act:** Human-in-the-loop validation, transparency, traceability

## Monitoring & Logging

- **Health Check:** `GET /health`
- **Logging:** Google Cloud Logging (structured logs)
- **Monitoring:** Cloud Monitoring dashboards
- **Alerts:** Cost alerts, error rate alerts

## Cost Estimation (MVP Phase)

- **Cloud Run:** $10-50/month (API Gateway + Workers)
- **Cloud SQL:** $10-15/month (db-f1-micro)
- **Pub/Sub:** $5-15/month
- **Cloud Storage:** $2-5/month
- **Document AI:** ~$50-150/month (usage-based)
- **Vertex AI:** ~$20-100/month (usage-based)

**Total:** ~$100-350/month for MVP phase

## Roadmap

- [x] **Phase 0:** Infrastructure setup
- [x] **Phase 1:** Core platform (API Gateway, Auth, File Upload)
- [ ] **Phase 2:** Invoice processing (Week 4-5)
- [ ] **Phase 3:** Generic OCR (Week 6)
- [ ] **Phase 4:** Summarization (Week 7)
- [ ] **Phase 5:** Chat with PDF (Week 8-9)
- [ ] **Phase 6:** Document filling (Week 10)
- [ ] **Phase 7:** Beta launch (Week 11-12)

## Contributing

This is a solo developer project. Contributions will be opened after MVP launch.

## License

Proprietary - All rights reserved.

## Contact

For questions or support, please contact: [your-email@example.com]

---

**Built with ❤️ using Python, FastAPI, and Google Cloud Platform**
