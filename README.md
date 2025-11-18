# DocProc AI - Document Processing Platform

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![React](https://img.shields.io/badge/React-18-blue)
![GCP](https://img.shields.io/badge/Platform-Google%20Cloud-blue)

AI-powered document processing platform for B2B customers. Built with an all-Python architecture on Google Cloud Platform.

## Features

### Document Processing
- **Invoice Processing** - Automated invoice data extraction with human-in-the-loop validation
- **Generic OCR** - Document AI + Gemini Vision for text extraction
- **Document Summarization** - AI-powered summaries using Vertex AI (Gemini Flash/Pro)
- **Chat with PDF** - RAG-powered Q&A with document context
- **Document Filling** - Automated PDF form filling from ID card extraction

### Platform Features
- **Multi-Tenancy** - Secure tenant isolation with row-level security
- **Firebase Authentication** - User management with JWT tokens
- **Real-time Processing** - Pub/Sub-based async job processing
- **Vector Search** - pgvector for semantic document search
- **Audit Logging** - Full compliance trail for GDPR/EU AI Act

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  React Frontend (Vite + TypeScript)          │
│            Firebase Auth + React Router + React Query        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI API Gateway (Cloud Run)                │
│  Firebase Auth • Multi-tenancy • Request Routing             │
└────────┬───────────────────────────────────┬────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────────┐          ┌──────────────────────────┐
│  Google Pub/Sub     │          │  Cloud SQL PostgreSQL    │
│  Message Queue      │          │  + pgvector extension    │
└────────┬────────────┘          └──────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                AI Worker Services (Cloud Run)                │
│  Invoice • OCR • Summarizer • RAG Ingest • DocFill          │
└──────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Backend
- **Language:** Python 3.11+
- **API Framework:** FastAPI 0.104+
- **Database:** PostgreSQL 15 with pgvector extension
- **ORM:** SQLAlchemy 2.0+
- **Migrations:** Alembic
- **Authentication:** Firebase Admin SDK
- **Validation:** Pydantic

### Frontend
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite
- **Routing:** React Router v6
- **State Management:** React Query (TanStack Query)
- **HTTP Client:** Axios
- **Authentication:** Firebase SDK
- **Styling:** Tailwind CSS (planned)

### Infrastructure (GCP)
- **Compute:** Cloud Run (serverless containers)
- **Database:** Cloud SQL PostgreSQL
- **Storage:** Cloud Storage (GCS)
- **Messaging:** Pub/Sub
- **AI Services:**
  - Document AI (Invoice parsing, OCR, ID extraction)
  - Vertex AI (Gemini 1.5 Flash/Pro, Claude 3.5 Sonnet)
  - Vision API (fallback OCR)
  - Embeddings (textembedding-gecko@003, 768 dimensions)
- **Auth:** Firebase Authentication
- **Secrets:** Secret Manager
- **IaC:** Terraform

## Project Structure

```
docproc_ai/
├── backend/
│   ├── shared/                      # Shared modules
│   │   ├── models.py                # SQLAlchemy database models
│   │   ├── schemas.py               # Pydantic validation schemas
│   │   ├── database.py              # Database connection & session
│   │   ├── config.py                # Settings management
│   │   ├── auth.py                  # Firebase auth utilities
│   │   ├── gcs.py                   # Cloud Storage utilities
│   │   └── pubsub.py                # Pub/Sub publisher
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
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── workers/                     # AI worker services
│   │   ├── invoice_worker/          # Invoice extraction worker
│   │   ├── ocr_worker/              # OCR processing worker
│   │   ├── summarizer_worker/       # Text summarization worker
│   │   ├── rag_ingest_worker/       # RAG indexing worker
│   │   └── docfill_worker/          # Document filling worker
│   │
│   └── migrations/                  # Alembic database migrations
│       ├── alembic.ini
│       ├── env.py
│       └── versions/
│           └── 20251117_001_initial_schema.py
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Auth/                # Login, Signup, ProtectedRoute
│       │   ├── Chat/                # Chat interface components
│       │   ├── OCR/                 # OCR results display
│       │   ├── Invoices/            # Invoice validation UI
│       │   ├── Summaries/           # Summary generation & display
│       │   ├── Filling/             # Document filling UI
│       │   └── common/              # Shared components
│       ├── pages/                   # Page components
│       │   ├── Dashboard.tsx        # Main dashboard
│       │   ├── Invoices.tsx
│       │   ├── Summaries.tsx
│       │   ├── ChatWithPDF.tsx
│       │   └── DocumentFilling.tsx
│       ├── services/
│       │   ├── api.ts               # API client with axios
│       │   └── auth.ts              # Firebase auth service
│       ├── App.tsx                  # Main app with routing
│       └── main.tsx                 # Entry point
│
├── scripts/                         # Deployment scripts
│   ├── deploy-api-gateway.sh
│   ├── deploy-invoice-worker.sh
│   ├── deploy-ocr-worker.sh
│   ├── deploy-summarizer-worker.sh
│   └── deploy-rag-ingest-worker.sh
│
├── terraform/                       # Infrastructure as Code
│   ├── main.tf
│   ├── cloud_run.tf
│   ├── cloud_sql.tf
│   └── pubsub.tf
│
└── docs/                            # Documentation
    ├── plans/                       # Phase implementation plans
    ├── technical_specification.md   # Full technical spec
    └── COMPLETE_IMPLEMENTATION_PLAN.md
```

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18+
- PostgreSQL 15+ (with pgvector extension)
- Google Cloud Platform account
- Firebase project
- Docker (for deployment)

### Local Development Setup

#### 1. Clone the repository
```bash
git clone https://github.com/rauly2k/docproc_ai.git
cd docproc_ai
```

#### 2. Backend Setup

```bash
cd backend/api_gateway

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

#### 3. Database Setup

```bash
# Create database
createdb docproc_ai_dev

# Enable pgvector extension
psql docproc_ai_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql docproc_ai_dev -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"

# Run migrations
cd backend/migrations
alembic upgrade head
```

#### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with Firebase config and API URL

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

#### 5. Run API Gateway

```bash
cd backend/api_gateway
uvicorn main:app --reload --port 8000
```

API Gateway will be available at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Environment Variables

#### Backend (.env)

```bash
# Application
ENVIRONMENT=dev
DEBUG=true

# GCP Configuration
PROJECT_ID=docai-mvp-prod
REGION=europe-west1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/docproc_ai_dev
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Firebase
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-adminsdk.json
FIREBASE_PROJECT_ID=your-firebase-project

# Cloud Storage
GCS_BUCKET_UPLOADS=docai-uploads-dev
GCS_BUCKET_PROCESSED=docai-processed-dev

# Document AI Processors
DOCUMENTAI_INVOICE_PROCESSOR_ID=your-invoice-processor-id
DOCUMENTAI_OCR_PROCESSOR_ID=your-ocr-processor-id
DOCUMENTAI_ID_PROCESSOR_ID=your-id-processor-id

# Vertex AI
VERTEX_AI_LOCATION=us-central1
```

#### Frontend (.env)

```bash
VITE_API_BASE_URL=http://localhost:8000/v1
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
```

## API Documentation

### Authentication

All endpoints (except `/auth/signup` and `/health`) require Firebase JWT authentication:

```bash
curl -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
     http://localhost:8000/v1/documents
```

### Key Endpoints

**Authentication**
- `POST /v1/auth/signup` - Create new user and tenant
- `GET /v1/auth/me` - Get current user info

**Documents**
- `POST /v1/documents/upload` - Upload document
- `GET /v1/documents` - List documents (paginated)
- `GET /v1/documents/{id}` - Get document details
- `DELETE /v1/documents/{id}` - Delete document

**Invoice Processing**
- `POST /v1/invoices/{document_id}/process` - Trigger invoice processing
- `GET /v1/invoices/{document_id}` - Get extracted invoice data
- `PATCH /v1/invoices/{document_id}/validate` - Validate/correct invoice data
- `GET /v1/invoices` - List all invoices

**OCR**
- `POST /v1/ocr/{document_id}/extract` - Trigger OCR extraction
- `GET /v1/ocr/{document_id}` - Get OCR results

**Summarization**
- `POST /v1/summaries/{document_id}/generate` - Generate summary
- `GET /v1/summaries/{document_id}` - Get summary
- `GET /v1/summaries` - List all summaries
- `DELETE /v1/summaries/{document_id}` - Delete summary

**Chat with PDF (RAG)**
- `POST /v1/chat/{document_id}/index` - Index document for RAG
- `POST /v1/chat/query` - Query documents with natural language
- `GET /v1/chat/{document_id}/chunks` - Get document chunks

**Document Filling**
- `GET /v1/filling/templates` - List available templates
- `POST /v1/filling/{document_id}/fill` - Fill PDF form from ID

**Admin**
- `GET /v1/admin/stats` - Get tenant usage statistics
- `GET /v1/admin/users` - List tenant users
- `GET /v1/admin/audit-logs` - Get compliance audit logs

## Deployment

### Deploy to Google Cloud Run

#### 1. Authenticate with GCP

```bash
gcloud auth login
gcloud config set project docai-mvp-prod
```

#### 2. Deploy API Gateway

```bash
cd backend/api_gateway
docker build -t gcr.io/docai-mvp-prod/api-gateway:latest .
docker push gcr.io/docai-mvp-prod/api-gateway:latest

gcloud run deploy api-gateway \
  --image gcr.io/docai-mvp-prod/api-gateway:latest \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 10 \
  --cpu 1 \
  --memory 512Mi \
  --set-env-vars PROJECT_ID=docai-mvp-prod,DATABASE_URL=$DATABASE_URL
```

#### 3. Deploy Workers

```bash
# Invoice Worker
./scripts/deploy-invoice-worker.sh

# OCR Worker
./scripts/deploy-ocr-worker.sh

# Summarizer Worker
./scripts/deploy-summarizer-worker.sh

# RAG Ingest Worker
./scripts/deploy-rag-ingest-worker.sh
```

### Frontend Deployment

Deploy frontend to Vercel, Netlify, or Firebase Hosting:

```bash
cd frontend
npm run build
# Follow hosting provider's deployment steps
```

## Database Schema

### Key Tables

- **tenants** - Multi-tenant organizations
- **users** - User accounts with roles
- **documents** - Uploaded documents metadata
- **invoice_data** - Extracted invoice data
- **ocr_results** - OCR extraction results
- **document_summaries** - Generated summaries
- **document_chunks** - RAG document chunks with embeddings (vector(768))
- **audit_logs** - Compliance audit trail

### Vector Search

The platform uses pgvector for semantic search:

```sql
CREATE EXTENSION vector;

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    tenant_id UUID REFERENCES tenants(id),
    chunk_index INTEGER,
    content TEXT,
    token_count INTEGER,
    embedding VECTOR(768),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vector similarity index (HNSW for fast approximate search)
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## Implementation Status

- [x] **Phase 0:** Infrastructure setup
- [x] **Phase 1:** Core platform (API Gateway, Auth, Multi-tenancy)
- [x] **Phase 2:** Invoice processing
- [x] **Phase 3:** Generic OCR
- [x] **Phase 4:** Text summarization
- [x] **Phase 5:** Chat with PDF (RAG)
- [x] **Phase 6:** Document filling
- [ ] **Phase 7:** Polish & beta launch (in progress)

## Security & Compliance

### Security Features
- Firebase JWT authentication
- Multi-tenant row-level security
- SQL injection protection (SQLAlchemy ORM)
- Input validation (Pydantic schemas)
- CORS configuration
- Secrets management (GCP Secret Manager)
- File upload validation (type, size)

### Compliance
- **GDPR:** Data residency in EU (europe-west1), audit logs, right to erasure
- **EU AI Act:** Human-in-the-loop validation, transparency, audit trails

## Monitoring & Logging

- **Health Check:** `GET /health`
- **Structured Logging:** Google Cloud Logging integration
- **Monitoring:** Cloud Monitoring dashboards
- **Alerts:** Error rate alerts, cost alerts
- **Tracing:** Cloud Trace integration (planned)

## Cost Estimation (MVP Phase)

| Service | Monthly Cost |
|---------|--------------|
| Cloud Run (API + Workers) | $10-50 |
| Cloud SQL (db-f1-micro) | $10-15 |
| Pub/Sub | $5-15 |
| Cloud Storage | $2-5 |
| Document AI | $50-150 (usage-based) |
| Vertex AI | $20-100 (usage-based) |
| **Total** | **~$100-350/month** |

## Contributing

This is currently a solo developer project. Contributions will be opened after MVP launch.

## License

Proprietary - All rights reserved.

## Support

For questions or issues, please create a GitHub issue or contact the development team.

---

**Built with ❤️ using Python, FastAPI, React, and Google Cloud Platform**
