# Technical Specification: AI-Driven Document Processing SaaS
## Google Cloud Platform Implementation for Solo Developer

**Document Version:** 1.0
**Last Updated:** 2025-11-17
**Target Launch:** ASAP (3-4 month MVP timeline)
**Budget:** $500-2000/month during MVP phase

---

## Executive Summary

This technical specification provides a complete implementation blueprint for a B2B AI document processing SaaS platform, optimized for:

- **Solo Python developer** building all components
- **Google Cloud Platform** as the exclusive cloud provider
- **All-Python architecture** using FastAPI for both API Gateway and AI services
- **Multi-vertical market approach** targeting legal, logistics, finance, healthcare, and document-heavy firms (car registration, contract processing, etc.)
- **Standard MVP scope** including all 5 core AI features
- **Free beta pricing model** to validate product-market fit
- **English-only MVP** with internationalization architecture for future Romanian/multilingual support

### Strategic Positioning

Unlike the original Azure-focused horizontal approach, this platform will:

1. **Multi-Vertical Launch**: Target multiple document-heavy industries simultaneously (legal, logistics, finance, healthcare, administrative services) to identify the highest-traction vertical during beta phase
2. **Rapid Validation**: Free beta model to gather usage data and determine which vertical to focus on for paid launch
3. **Python-Native Stack**: Simplified all-Python architecture reducing context switching and leveraging solo developer's core expertise
4. **Google Cloud First**: Utilize GCP's serverless capabilities (Cloud Run, Pub/Sub, Cloud SQL) for minimal operational overhead

---

## I. System Architecture: All-Python Event-Driven Microservices

### A. Architectural Overview

The platform uses a **simplified all-Python hybrid architecture** that maintains the microservices pattern but removes Node.js complexity:

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend (Vercel)                  │
│                  (TypeScript + Tailwind CSS)                 │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS/REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI API Gateway (Cloud Run)                │
│  - Firebase Auth integration                                 │
│  - Request validation & routing                              │
│  - Multi-tenant security                                     │
│  - Sync endpoints (auth, uploads, queries)                  │
└────────┬───────────────────────────────────┬────────────────┘
         │                                   │
         │ Publish jobs                      │ Read/Write
         ▼                                   ▼
┌─────────────────────┐          ┌──────────────────────────┐
│  Google Pub/Sub     │          │  Cloud SQL (PostgreSQL)  │
│  Message Queue      │          │  + pgvector extension    │
└────────┬────────────┘          └──────────────────────────┘
         │                                   ▲
         │ Consume jobs                      │ Store results
         ▼                                   │
┌─────────────────────────────────────────────┴───────────────┐
│           Python AI Microservices (Cloud Run)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Invoice      │  │ OCR          │  │ Summarizer   │     │
│  │ Worker       │  │ Worker       │  │ Worker       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ RAG Ingest   │  │ RAG Query    │                        │
│  │ Worker       │  │ Worker       │                        │
│  └──────────────┘  └──────────────┘                        │
│  ┌──────────────┐                                           │
│  │ Doc Filling  │                                           │
│  │ Worker       │                                           │
│  └──────────────┘                                           │
└──────────────────────────────────────────────────────────────┘
         │ Read files                        │ Write files
         ▼                                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Google Cloud Storage (Buckets)                  │
│  - Raw uploaded documents                                    │
│  - Processed/filled PDFs                                     │
└──────────────────────────────────────────────────────────────┘
```

### B. Why All-Python Architecture

**Original Concern (from Blueprint):** Node.js for I/O-bound API, Python for CPU-bound AI

**Solo Developer Reality:**
- **Single Language Proficiency**: No context switching between JavaScript and Python
- **Unified Dependency Management**: One `requirements.txt`, one virtual environment
- **Code Reuse**: Share data models, utilities, validation logic across all services
- **FastAPI Performance**: Modern async FastAPI with Starlette performs comparably to Node.js Express for I/O operations
- **Faster Development**: 30-40% faster iteration without dual-language overhead

**Trade-off Accepted:**
- Slightly lower throughput for pure I/O operations (user auth, simple queries)
- **Mitigation**: Cloud Run auto-scaling handles any performance gaps

### C. Service Breakdown

#### 1. API Gateway Service (FastAPI on Cloud Run)

**Responsibilities:**
- User authentication via Firebase Auth SDK
- File upload handling (multipart/form-data to GCS)
- Request validation with Pydantic models
- Multi-tenant security (tenant_id injection)
- Pub/Sub job publishing
- Synchronous query endpoints (get document status, list documents)
- WebSocket connections for real-time updates (optional)

**Key Dependencies:**
```python
fastapi==0.104.1
uvicorn[standard]==0.24.0
firebase-admin==6.3.0
google-cloud-storage==2.10.0
google-cloud-pubsub==2.18.4
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
```

**Deployment:**
- Cloud Run service with 1-10 instances (auto-scale)
- Min instances: 1 (reduce cold starts)
- CPU: 1 vCPU, Memory: 512 MB
- Max concurrent requests: 80

#### 2. AI Worker Services (FastAPI on Cloud Run)

Each worker is a separate Cloud Run service that:
- Subscribes to specific Pub/Sub topics
- Pulls jobs from the queue
- Calls Google Cloud AI APIs or Vertex AI
- Writes results to Cloud SQL
- Publishes completion events

**Workers:**
1. **invoice-worker**: Processes invoices via Document AI
2. **ocr-worker**: Generic OCR via Vision API or Gemini Vision
3. **summarizer-worker**: Summarizes documents via Vertex AI (Gemini/Claude)
4. **rag-ingest-worker**: Chunks and embeds documents for RAG
5. **rag-query-worker**: Retrieves context and generates answers
6. **docfill-worker**: Extracts ID data and fills PDF forms

**Deployment per worker:**
- CPU: 2 vCPU, Memory: 2 GB (AI tasks are CPU-bound)
- Max instances: 5 (control costs)
- Timeout: 600 seconds (10 minutes for long documents)

### D. Asynchronous Processing Flow

**Example: User uploads invoice for processing**

1. User uploads `invoice.pdf` via React frontend
2. Frontend sends file to API Gateway endpoint: `POST /api/documents/upload`
3. API Gateway:
   - Validates auth (Firebase token)
   - Extracts tenant_id from user token
   - Uploads file to GCS: `gs://docai-uploads/{tenant_id}/{doc_id}/invoice.pdf`
   - Creates database record: `documents` table (status: "processing")
   - Publishes message to Pub/Sub topic `invoice-processing`:
     ```json
     {
       "tenant_id": "tenant_abc123",
       "doc_id": "doc_xyz789",
       "gcs_path": "gs://docai-uploads/tenant_abc123/doc_xyz789/invoice.pdf",
       "document_type": "invoice",
       "user_id": "user_456"
     }
     ```
   - Returns `202 Accepted` with document ID
4. Invoice Worker (Cloud Run):
   - Receives Pub/Sub message (push subscription)
   - Downloads file from GCS
   - Calls Google Document AI Invoice Processor
   - Parses JSON response
   - Writes extracted data to `invoice_data` table
   - Updates document status: "completed"
   - (Optional) Publishes completion event for frontend notifications
5. Frontend polls `GET /api/documents/{doc_id}` or receives WebSocket update
6. User sees extracted invoice data in validation UI

**Resilience:**
- If worker fails, Pub/Sub automatically retries (configurable retry policy)
- Dead Letter Queue (DLQ) for permanent failures
- Each worker is stateless and independently scalable

---

## II. Google Cloud Platform Services: Complete Stack

### A. Core Infrastructure

| Component | GCP Service | Configuration | Cost Estimate (MVP) |
|-----------|-------------|---------------|---------------------|
| **API Gateway** | Cloud Run | 1-10 instances, 1 vCPU, 512MB | $10-50/month |
| **AI Workers (6 services)** | Cloud Run | 0-5 instances each, 2 vCPU, 2GB | $50-300/month |
| **Message Queue** | Pub/Sub | Standard tier, ~10k msgs/day | $5-15/month |
| **Database** | Cloud SQL PostgreSQL | db-f1-micro (shared CPU, 0.6GB RAM) | $7-15/month |
| **Vector Extension** | pgvector | Installed on Cloud SQL (no extra cost) | $0 |
| **File Storage** | Cloud Storage | Standard class, ~100GB | $2-5/month |
| **Authentication** | Firebase Auth | Free tier (up to 50k MAU) | $0 |
| **CDN/Frontend** | Vercel/Netlify | Hobby/Free tier | $0 |
| **Container Registry** | Artifact Registry | Store Docker images | $1-3/month |
| **Secret Management** | Secret Manager | Store API keys | $1/month |

**Total Estimated Monthly Cost (MVP Phase):** $76-$389/month (well within $500-2000 budget)

**Note:** AI API costs (Document AI, Vertex AI) are variable and usage-based. Estimated additional costs:
- Document AI OCR: $1.50 per 1,000 pages
- Document AI Invoice: $10 per 1,000 pages
- Vertex AI Gemini: $0.00025/1k input tokens, $0.0005/1k output tokens
- Vertex AI Claude 3 Sonnet: $3/1M input tokens, $15/1M output tokens

**Projected AI API costs for 1,000 documents/month:** $50-150

**Grand Total MVP Phase:** $126-$539/month (comfortably within budget)

### B. AI/ML Services Detailed

#### 1. Document AI (OCR & Invoice Processing)

**Service:** Google Cloud Document AI
**API:** `documentai.googleapis.com`

**Processors to Enable:**

| Processor Type | Use Case | Accuracy (Google's Data) | Cost per 1k pages |
|----------------|----------|--------------------------|-------------------|
| **OCR Processor** | Generic text extraction | 95%+ on clean docs | $1.50 |
| **Invoice Parser** | Structured invoice data | ~85% (vendor, amount, line items) | $10 |
| **ID Processor (US/EU)** | Identity document parsing | ~90% (name, DOB, ID number) | $10 |
| **Form Parser** | Custom forms | 80-90% (custom training possible) | $10 |

**Implementation Notes:**
- **Invoice Processing**: Use prebuilt "Invoice Parser" processor
  - Extracts: vendor_name, invoice_date, total_amount, tax, line_items[]
  - Returns structured JSON
  - Handles multiple currencies including EUR, RON
- **Generic OCR**: Use "OCR Processor" for simple text extraction
  - Returns plain text + bounding boxes
  - Good for contracts, letters, general documents
- **ID Documents**: Use "ID Processor" for Romanian ID cards (Carte de Identitate)
  - Extracts: Nume, Prenume, CNP, Adresă, Data Nașterii
  - May need custom training for Romanian-specific fields

**API Call Example (Python):**
```python
from google.cloud import documentai_v1 as documentai

def process_invoice(gcs_uri: str, processor_id: str) -> dict:
    client = documentai.DocumentProcessorServiceClient()

    # Configure request
    request = documentai.ProcessRequest(
        name=processor_id,
        gcs_document=documentai.GcsDocument(
            gcs_uri=gcs_uri,
            mime_type="application/pdf"
        )
    )

    result = client.process_document(request=request)
    document = result.document

    # Extract invoice-specific entities
    invoice_data = {}
    for entity in document.entities:
        if entity.type_ == "total_amount":
            invoice_data["total"] = entity.mention_text
        elif entity.type_ == "vendor_name":
            invoice_data["vendor"] = entity.mention_text
        # ... extract line_items, dates, etc.

    return invoice_data
```

#### 2. Vertex AI (LLM Services)

**Service:** Google Vertex AI
**API:** `aiplatform.googleapis.com`

**Models to Use:**

| Model | Use Case | Context Window | Cost (Input/Output per 1M tokens) | When to Use |
|-------|----------|----------------|-----------------------------------|-------------|
| **Gemini 1.5 Flash** | Fast OCR, summaries, Q&A | 1M tokens | $0.075 / $0.30 | Cost-effective for most tasks |
| **Gemini 1.5 Pro** | Complex analysis, long docs | 2M tokens | $1.25 / $5.00 | High-quality summarization, complex RAG |
| **Claude 3.5 Sonnet** | Premium summarization, legal | 200k tokens | $3.00 / $15.00 | When accuracy is critical (legal, finance) |
| **Claude 3 Haiku** | Fast extraction, classification | 200k tokens | $0.25 / $1.25 | Quick document classification |

**Recommended Strategy (Hybrid):**
- **Default to Gemini 1.5 Flash**: 80% of tasks (summaries, basic Q&A, OCR via vision)
- **Upgrade to Gemini 1.5 Pro**: Long documents (>50 pages), complex RAG queries
- **Use Claude 3.5 Sonnet**: User explicitly requests premium processing or document type is legal/financial
- **Use Gemini Vision for OCR**: Multimodal approach for handwritten/messy documents

**API Call Example (Python with Vertex AI SDK):**
```python
from vertexai.preview.generative_models import GenerativeModel

def summarize_document(document_text: str, model_name: str = "gemini-1.5-flash") -> str:
    model = GenerativeModel(model_name)

    prompt = f"""Summarize the following document concisely in 3-5 bullet points:

{document_text}

Summary:"""

    response = model.generate_content(prompt)
    return response.text
```

**Gemini Vision for OCR (Advanced):**
```python
from vertexai.preview.generative_models import GenerativeModel, Part

def ocr_with_gemini_vision(image_gcs_uri: str) -> str:
    model = GenerativeModel("gemini-1.5-flash")

    image_part = Part.from_uri(image_gcs_uri, mime_type="image/jpeg")
    prompt = "Extract all text from this image. Return only the text, no commentary."

    response = model.generate_content([prompt, image_part])
    return response.text
```

#### 3. Text Embeddings for RAG

**Service:** Vertex AI Text Embeddings
**Model:** `textembedding-gecko@003` (Google's latest)

**Specifications:**
- Vector dimensions: 768
- Max input tokens: 3,072 (~2,300 words)
- Cost: $0.00025 per 1,000 characters (~$0.10 per 1M characters)
- Multilingual support: 100+ languages including English and Romanian

**Alternative (Future):** `text-embedding-004` (1,408 dimensions, higher quality)

**Comparison to OpenAI:**
- OpenAI `text-embedding-3-small`: 1,536 dimensions, $0.02 per 1M tokens
- Google `textembedding-gecko`: 768 dimensions, $0.025 per 1M tokens (comparable cost)
- **Recommendation**: Use Vertex AI embeddings to keep everything in GCP ecosystem

**API Call Example:**
```python
from vertexai.language_models import TextEmbeddingModel

def embed_text_chunks(chunks: list[str]) -> list[list[float]]:
    model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
    embeddings = model.get_embeddings(chunks)
    return [emb.values for emb in embeddings]
```

### C. Infrastructure Services

#### 1. Cloud SQL (PostgreSQL with pgvector)

**Configuration:**
- **Instance Tier**: db-f1-micro (MVP), upgrade to db-n1-standard-1 (production)
- **Storage**: 10 GB SSD (auto-increase enabled)
- **PostgreSQL Version**: 15
- **Extensions**: `pgvector` (for RAG), `uuid-ossp` (for UUIDs)
- **Backups**: Automated daily backups (7-day retention)
- **Region**: europe-west1 (Belgium) or europe-west3 (Frankfurt) for EU compliance
- **High Availability**: Disabled for MVP (save costs), enable for production

**Connection:**
- Use Cloud SQL Proxy for secure connections from Cloud Run
- Connection pooling with SQLAlchemy (max 5 connections per service)

**pgvector Setup:**
```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table for document embeddings
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    document_id UUID NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768),  -- 768 for textembedding-gecko
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for vector similarity search (HNSW algorithm)
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- Index for tenant isolation
CREATE INDEX ON document_chunks (tenant_id);
```

**Cost Estimate:**
- db-f1-micro: ~$7.67/month
- Storage (10 GB SSD): ~$1.70/month
- **Total**: ~$9.37/month

#### 2. Google Cloud Storage

**Bucket Structure:**
```
docai-uploads-{env}/          # Raw uploaded documents
  ├── {tenant_id}/
  │   ├── {document_id}/
  │   │   ├── original.pdf
  │   │   └── metadata.json
  │   └── ...
  └── ...

docai-processed-{env}/        # Processed/filled documents
  ├── {tenant_id}/
  │   ├── {document_id}/
  │   │   ├── filled_form.pdf
  │   │   └── extracted_data.json
  │   └── ...
  └── ...

docai-temp-{env}/             # Temporary files (7-day lifecycle)
```

**Configuration:**
- **Storage Class**: Standard (frequent access)
- **Region**: europe-west1 (Belgium) - EU data residency
- **Lifecycle Policy**: Delete files in `docai-temp-*` after 7 days
- **Versioning**: Disabled for MVP (enable for production)
- **IAM**: Service account per Cloud Run service (least privilege)

**Access Pattern:**
- API Gateway: Write-only to `docai-uploads`, Read-only to `docai-processed`
- AI Workers: Read from `docai-uploads`, Write to `docai-processed`

#### 3. Google Pub/Sub

**Topics:**
- `invoice-processing`: Jobs for invoice parsing
- `ocr-processing`: Jobs for generic OCR
- `summarization-processing`: Jobs for document summarization
- `rag-ingestion`: Jobs for document embedding
- `rag-query`: Jobs for RAG Q&A (optional, can be synchronous)
- `document-filling`: Jobs for ID extraction + PDF filling
- `processing-complete`: Notifications for frontend (optional)

**Subscriptions:**
- Each worker service has a **push subscription** to its topic
- Push endpoint: `https://{worker-service-url}/process`
- Acknowledgement deadline: 600 seconds (10 minutes)
- Retry policy: Exponential backoff, max 7 days
- Dead Letter Topic: `processing-failures` (for monitoring)

**Message Format (Standard):**
```json
{
  "tenant_id": "tenant_abc123",
  "user_id": "user_xyz789",
  "document_id": "doc_123456",
  "gcs_path": "gs://docai-uploads/tenant_abc123/doc_123456/file.pdf",
  "document_type": "invoice",
  "options": {
    "language": "en",
    "premium_processing": false
  },
  "callback_url": "https://api.example.com/webhooks/processing-complete"
}
```

#### 4. Firebase Authentication

**Configuration:**
- **Auth Providers**: Email/Password (MVP), Google OAuth (Phase 2)
- **Custom Claims**: Used for storing `tenant_id` and `role`
- **Email Verification**: Enabled
- **Password Requirements**: Min 8 chars, complexity enforced
- **Session Duration**: 1 hour (refresh tokens for 30 days)

**Integration with FastAPI:**
```python
from firebase_admin import auth, credentials, initialize_app

# Initialize Firebase Admin SDK
cred = credentials.ApplicationDefault()
initialize_app(cred)

# Middleware to verify Firebase tokens
async def verify_firebase_token(authorization: str) -> dict:
    try:
        token = authorization.replace("Bearer ", "")
        decoded_token = auth.verify_id_token(token)
        return decoded_token  # Contains uid, email, custom claims
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")
```

**Custom Claims for Multi-Tenancy:**
```python
# After user signup, set tenant_id claim
auth.set_custom_user_claims(user_id, {
    "tenant_id": "tenant_abc123",
    "role": "admin"  # or "user", "viewer"
})
```

#### 5. Secret Manager

**Secrets to Store:**
- `DATABASE_URL`: Cloud SQL connection string
- `GCP_PROJECT_ID`: Project ID
- `FIREBASE_CREDENTIALS`: Service account JSON (if needed)
- `VERTEX_AI_LOCATION`: Region for Vertex AI (e.g., "us-central1")
- `ENCRYPTION_KEY`: For sensitive data encryption
- Future: Payment gateway API keys, webhook secrets

**Access from Cloud Run:**
```python
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Usage
DATABASE_URL = get_secret("DATABASE_URL")
```

---

## III. Database Schema (PostgreSQL)

### A. Core Tables

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Tenants table (multi-tenancy)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(100) UNIQUE,  -- e.g., "acme" for acme.docai.com
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb,  -- Tenant-specific config
    is_active BOOLEAN DEFAULT TRUE
);

-- Users table (linked to Firebase Auth)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    firebase_uid VARCHAR(255) UNIQUE NOT NULL,  -- Firebase user ID
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',  -- 'admin', 'user', 'viewer'
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(tenant_id, email)
);

-- Documents table (all uploaded documents)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Document metadata
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500),
    mime_type VARCHAR(100),
    file_size_bytes BIGINT,
    document_type VARCHAR(50),  -- 'invoice', 'contract', 'id', 'generic'

    -- Storage
    gcs_path TEXT NOT NULL,  -- gs://bucket/path/to/file.pdf
    gcs_processed_path TEXT,  -- For filled PDFs

    -- Processing status
    status VARCHAR(50) DEFAULT 'uploaded',  -- 'uploaded', 'processing', 'completed', 'failed'
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    error_message TEXT,

    -- AI processing flags
    ocr_completed BOOLEAN DEFAULT FALSE,
    invoice_parsed BOOLEAN DEFAULT FALSE,
    summarized BOOLEAN DEFAULT FALSE,
    rag_indexed BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_tenant_documents (tenant_id, created_at DESC),
    INDEX idx_user_documents (user_id, created_at DESC),
    INDEX idx_document_status (status)
);

-- Invoice data table (extracted invoice information)
CREATE TABLE invoice_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Vendor information
    vendor_name VARCHAR(500),
    vendor_address TEXT,
    vendor_tax_id VARCHAR(100),

    -- Invoice details
    invoice_number VARCHAR(100),
    invoice_date DATE,
    due_date DATE,

    -- Amounts
    subtotal DECIMAL(15, 2),
    tax_amount DECIMAL(15, 2),
    total_amount DECIMAL(15, 2),
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Line items (stored as JSONB for flexibility)
    line_items JSONB DEFAULT '[]'::jsonb,

    -- Raw extraction
    raw_extraction JSONB,  -- Full Document AI response

    -- Human validation
    is_validated BOOLEAN DEFAULT FALSE,
    validated_by UUID REFERENCES users(id),
    validated_at TIMESTAMP,
    validation_notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_tenant_invoices (tenant_id, invoice_date DESC),
    INDEX idx_invoice_validation (is_validated)
);

-- Document summaries table
CREATE TABLE document_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    summary TEXT NOT NULL,
    model_used VARCHAR(100),  -- 'gemini-1.5-flash', 'claude-3-sonnet', etc.
    word_count INT,
    key_points JSONB,  -- Structured bullet points

    created_at TIMESTAMP DEFAULT NOW()
);

-- OCR results table (generic text extraction)
CREATE TABLE ocr_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    extracted_text TEXT NOT NULL,
    confidence_score DECIMAL(5, 4),  -- 0.0 to 1.0
    page_count INT,
    ocr_method VARCHAR(50),  -- 'document-ai', 'vision-api', 'gemini-vision'

    -- Bounding boxes and layout (optional)
    layout_data JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Document chunks table (for RAG)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    chunk_index INT NOT NULL,  -- Order of chunk in document
    content TEXT NOT NULL,
    token_count INT,

    -- Vector embedding (768 dimensions for textembedding-gecko)
    embedding VECTOR(768),

    -- Metadata for better retrieval
    metadata JSONB DEFAULT '{}'::jsonb,  -- Page number, section, etc.

    created_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_tenant_chunks (tenant_id),
    INDEX idx_document_chunks (document_id, chunk_index)
);

-- HNSW index for vector similarity search
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- Document filling results table (ID extraction + PDF filling)
CREATE TABLE document_filling_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Source document (ID card, etc.)
    source_document_type VARCHAR(50),  -- 'romanian_id', 'passport', etc.

    -- Extracted data
    extracted_fields JSONB NOT NULL,  -- {nume, prenume, cnp, etc.}

    -- Filled PDF
    filled_pdf_gcs_path TEXT,
    template_used VARCHAR(255),

    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit logs table (for EU AI Act compliance)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    document_id UUID REFERENCES documents(id),

    action VARCHAR(100) NOT NULL,  -- 'document_uploaded', 'invoice_processed', 'data_validated', etc.
    details JSONB,
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_audit_tenant (tenant_id, created_at DESC),
    INDEX idx_audit_user (user_id, created_at DESC)
);
```

### B. Multi-Tenancy Security

**Every query MUST include tenant_id filter:**

```python
# CORRECT - Tenant-isolated query
invoices = db.query(InvoiceData).filter(
    InvoiceData.tenant_id == current_user.tenant_id
).all()

# WRONG - No tenant isolation, security vulnerability!
invoices = db.query(InvoiceData).all()
```

**SQLAlchemy Filter Implementation:**

```python
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

def get_current_user_from_token(token: str) -> dict:
    # Verify Firebase token, extract tenant_id
    decoded = verify_firebase_token(token)
    return {
        "user_id": decoded["uid"],
        "tenant_id": decoded.get("tenant_id"),
        "role": decoded.get("role", "user")
    }

def get_filtered_db(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token)
) -> Session:
    # Add tenant_id filter to all queries automatically
    db.tenant_id = current_user["tenant_id"]
    return db
```

---

## IV. API Design (FastAPI Endpoints)

### A. API Gateway Endpoints

**Base URL:** `https://api.docai.example.com/v1`

#### Authentication

```
POST   /auth/signup          # Create new user account
POST   /auth/login           # Login (returns Firebase token)
POST   /auth/refresh         # Refresh authentication token
POST   /auth/logout          # Logout
GET    /auth/me              # Get current user info
```

#### Documents

```
POST   /documents/upload                    # Upload single document
GET    /documents                           # List user's documents (paginated)
GET    /documents/{document_id}             # Get document details
DELETE /documents/{document_id}             # Delete document
PATCH  /documents/{document_id}/metadata    # Update document metadata
```

#### Invoice Processing

```
POST   /invoices/process                    # Process invoice (async)
GET    /invoices/{document_id}              # Get extracted invoice data
PATCH  /invoices/{document_id}/validate     # Human validation/correction
GET    /invoices                            # List all invoices for tenant
```

#### OCR

```
POST   /ocr/extract                         # Extract text from document (async)
GET    /ocr/{document_id}                   # Get OCR results
```

#### Summarization

```
POST   /summaries/generate                  # Generate summary (async)
GET    /summaries/{document_id}             # Get document summary
```

#### Chat with PDF (RAG)

```
POST   /chat/index                          # Index document for chat (async)
POST   /chat/query                          # Ask question about documents
GET    /chat/{document_id}/history          # Get chat history for document
```

#### Document Filling

```
POST   /filling/extract-and-fill            # Extract ID + fill PDF (async)
GET    /filling/{document_id}               # Get filled PDF
GET    /filling/templates                   # List available form templates
```

#### Admin

```
GET    /admin/stats                         # Tenant usage statistics
GET    /admin/users                         # List tenant users
POST   /admin/users/{user_id}/role          # Update user role
GET    /admin/audit-logs                    # Compliance audit logs
```

### B. Request/Response Examples

#### Upload Document

**Request:**
```http
POST /v1/documents/upload
Authorization: Bearer {firebase_token}
Content-Type: multipart/form-data

file: (binary)
document_type: "invoice"
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "uploaded",
  "filename": "invoice_march_2025.pdf",
  "gcs_path": "gs://docai-uploads/tenant123/550e8400.../invoice.pdf",
  "created_at": "2025-03-15T10:30:00Z"
}
```

#### Process Invoice (Async)

**Request:**
```http
POST /v1/invoices/process
Authorization: Bearer {firebase_token}
Content-Type: application/json

{
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "job_id": "job_abc123",
  "status": "processing",
  "message": "Invoice processing started. Poll /invoices/{document_id} for results.",
  "estimated_completion": "2025-03-15T10:35:00Z"
}
```

#### Get Invoice Data

**Request:**
```http
GET /v1/invoices/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {firebase_token}
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "invoice_data": {
    "vendor_name": "Acme Supplies SRL",
    "vendor_tax_id": "RO12345678",
    "invoice_number": "INV-2025-001",
    "invoice_date": "2025-03-01",
    "due_date": "2025-03-31",
    "subtotal": 1000.00,
    "tax_amount": 190.00,
    "total_amount": 1190.00,
    "currency": "RON",
    "line_items": [
      {
        "description": "Office Supplies",
        "quantity": 10,
        "unit_price": 50.00,
        "amount": 500.00
      },
      {
        "description": "Printer Paper",
        "quantity": 20,
        "unit_price": 25.00,
        "amount": 500.00
      }
    ]
  },
  "confidence_score": 0.92,
  "is_validated": false,
  "requires_review": true
}
```

#### Validate Invoice (Human-in-the-Loop)

**Request:**
```http
PATCH /v1/invoices/550e8400-e29b-41d4-a716-446655440000/validate
Authorization: Bearer {firebase_token}
Content-Type: application/json

{
  "corrections": {
    "total_amount": 1200.00,
    "line_items[0].amount": 700.00
  },
  "validation_notes": "Corrected line item 1 amount from 500 to 700",
  "is_approved": true
}
```

**Response:**
```json
{
  "status": "validated",
  "validated_by": "user_xyz789",
  "validated_at": "2025-03-15T11:00:00Z",
  "updated_invoice_data": {
    "total_amount": 1200.00,
    "line_items": [...]
  }
}
```

#### Chat with PDF

**Request:**
```http
POST /v1/chat/query
Authorization: Bearer {firebase_token}
Content-Type: application/json

{
  "document_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "question": "What is the total amount on this invoice?",
  "max_chunks": 5
}
```

**Response:**
```json
{
  "answer": "According to the invoice, the total amount is 1,190.00 RON, which includes a subtotal of 1,000.00 RON and tax of 190.00 RON.",
  "sources": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "chunk_index": 2,
      "relevance_score": 0.94,
      "content": "Total Amount: 1,190.00 RON\nSubtotal: 1,000.00 RON\nTax (19%): 190.00 RON"
    }
  ],
  "model_used": "gemini-1.5-flash"
}
```

---

## V. Implementation Phases

### Phase 0: Infrastructure Setup (Week 1)

**Goal:** Set up GCP project, Terraform infrastructure, CI/CD

**Tasks:**
1. Create GCP project (`docai-mvp-prod`)
2. Enable required APIs:
   - Cloud Run
   - Cloud SQL
   - Pub/Sub
   - Cloud Storage
   - Document AI
   - Vertex AI
   - Secret Manager
   - Artifact Registry
3. Set up Terraform:
   - Project structure
   - State backend (GCS bucket)
   - Modules for each service
4. Create Firebase project, enable Auth
5. Set up GitHub repository (monorepo structure)
6. Configure GitHub Actions for CI/CD:
   - Build Docker images
   - Push to Artifact Registry
   - Deploy to Cloud Run
7. Set up local development environment:
   - Python 3.11+ virtual environment
   - Docker Desktop
   - gcloud CLI
   - Firebase CLI
8. Initialize Cloud SQL PostgreSQL instance
9. Run database migrations (create tables)

**Deliverables:**
- GCP project fully configured
- Terraform code in `/terraform` directory
- CI/CD pipeline working
- Local dev environment documented in `README.md`

### Phase 1: Core Platform (Weeks 2-3)

**Goal:** Build API Gateway, authentication, file upload/storage

**Tasks:**
1. **API Gateway Service (FastAPI)**
   - Project structure: `/backend/api_gateway`
   - FastAPI app with basic routes
   - Firebase Auth integration
   - SQLAlchemy models and database connection
   - Multi-tenancy middleware
   - Error handling and logging
2. **Database Migrations**
   - Set up Alembic for migrations
   - Create initial tables (tenants, users, documents)
3. **File Upload Endpoint**
   - Handle multipart/form-data
   - Upload to GCS with proper naming
   - Create document record in database
   - Return document ID
4. **Pub/Sub Integration**
   - Publisher client setup
   - Publish jobs to topics
   - Message format standardization
5. **Basic Frontend (React)**
   - Project setup: `/frontend`
   - Login page (Firebase Auth)
   - Document upload page
   - Document list page
   - Deploy to Vercel

**Deliverables:**
- API Gateway deployed to Cloud Run
- Users can sign up, log in
- Users can upload documents
- Documents are stored in GCS
- Basic React frontend deployed

### Phase 2: Invoice Processing (Weeks 4-5)

**Goal:** Implement invoice parsing with human-in-the-loop validation

**Tasks:**
1. **Invoice Worker Service**
   - Project structure: `/backend/workers/invoice_worker`
   - Pub/Sub push subscription handler
   - Document AI Invoice Parser integration
   - Parse JSON response, extract fields
   - Save to `invoice_data` table
   - Update document status
   - Error handling and retries
2. **Invoice API Endpoints**
   - POST `/invoices/process`
   - GET `/invoices/{document_id}`
   - PATCH `/invoices/{document_id}/validate`
   - GET `/invoices` (list with filters)
3. **Human-in-the-Loop Validation UI**
   - Split-screen view: PDF preview + extracted fields
   - Editable form fields
   - Highlight low-confidence extractions
   - Approve/reject workflow
   - Save corrections to database
4. **Audit Logging**
   - Log all processing events
   - Log all human validations/corrections
   - Store in `audit_logs` table

**Deliverables:**
- Invoice processing fully functional
- Human validation UI working
- Compliance audit trail in place

### Phase 3: Generic OCR (Week 6)

**Goal:** Extract text from any document type

**Tasks:**
1. **OCR Worker Service**
   - Project structure: `/backend/workers/ocr_worker`
   - Implement three OCR methods:
     - Document AI OCR Processor (default)
     - Vision API (fallback)
     - Gemini Vision (for handwritten/messy docs)
   - Save to `ocr_results` table
2. **OCR API Endpoints**
   - POST `/ocr/extract`
   - GET `/ocr/{document_id}`
3. **OCR Results UI**
   - Display extracted text
   - Show confidence scores
   - Allow text editing/export

**Deliverables:**
- Generic OCR working for all document types
- UI to view/download extracted text

### Phase 4: Text Summarization (Week 7)

**Goal:** Generate concise summaries of long documents

**Tasks:**
1. **Summarizer Worker Service**
   - Project structure: `/backend/workers/summarizer_worker`
   - Vertex AI integration (Gemini 1.5 Flash default)
   - Read document text (from OCR or direct PDF extraction)
   - Generate summary
   - Save to `document_summaries` table
   - Option to upgrade to Gemini Pro or Claude for premium
2. **Summarization API Endpoints**
   - POST `/summaries/generate`
   - GET `/summaries/{document_id}`
3. **Summary Display UI**
   - Show summary with bullet points
   - Display key insights
   - Regenerate option

**Deliverables:**
- Summarization working for documents up to 100 pages
- Summaries displayed in frontend

### Phase 5: Chat with PDF (RAG) (Weeks 8-9)

**Goal:** Enable users to ask questions about their documents

**Tasks:**
1. **RAG Ingestion Worker**
   - Project structure: `/backend/workers/rag_ingest_worker`
   - PDF text extraction
   - Text chunking (LangChain or custom)
   - Generate embeddings via Vertex AI
   - Store chunks + embeddings in `document_chunks` table
   - Create pgvector index
2. **RAG Query Worker**
   - Project structure: `/backend/workers/rag_query_worker`
   - Embed user question
   - Vector similarity search (pgvector)
   - Retrieve top K chunks (with tenant_id filter!)
   - Build context for LLM
   - Call Vertex AI (Gemini) with context
   - Return answer + sources
3. **Chat API Endpoints**
   - POST `/chat/index` (trigger RAG ingestion)
   - POST `/chat/query`
   - GET `/chat/{document_id}/history`
4. **Chat UI**
   - Chat interface (message bubbles)
   - Display sources with highlighting
   - Multi-document chat (select multiple docs)

**Deliverables:**
- RAG pipeline fully functional
- Users can chat with their uploaded PDFs
- Accurate answers with source citations

### Phase 6: Document Filling (Week 10)

**Goal:** Extract data from IDs and auto-fill PDF forms

**Tasks:**
1. **Document Filling Worker**
   - Project structure: `/backend/workers/docfill_worker`
   - Document AI ID Processor integration
   - Extract Romanian ID fields (Nume, Prenume, CNP, etc.)
   - Load PDF template
   - Fill PDF form fields using PyPDFForm
   - Save filled PDF to GCS
   - Save metadata to `document_filling_results` table
2. **Document Filling API Endpoints**
   - POST `/filling/extract-and-fill`
   - GET `/filling/{document_id}`
   - GET `/filling/templates`
3. **Document Filling UI**
   - Upload ID card image
   - Select form template
   - Preview filled PDF
   - Download filled PDF

**Deliverables:**
- ID extraction working for Romanian IDs
- PDF form filling functional
- Users can download filled forms

### Phase 7: Polish & Beta Launch (Weeks 11-12)

**Goal:** Finalize MVP, deploy, invite beta users

**Tasks:**
1. **Frontend Polish**
   - Responsive design (mobile support)
   - Loading states, error messages
   - User onboarding flow
   - Dashboard with usage stats
2. **Documentation**
   - User guide
   - API documentation (auto-generated from FastAPI)
   - Admin guide
3. **Monitoring & Logging**
   - Set up Cloud Logging
   - Set up error tracking (Sentry or similar)
   - Set up uptime monitoring
   - Create Cloud Monitoring dashboards
4. **Performance Optimization**
   - Optimize database queries
   - Add caching where appropriate
   - Review Cloud Run configurations
5. **Beta User Onboarding**
   - Create landing page
   - Email invites to 10-20 beta users
   - Collect feedback via in-app surveys
6. **Security Review**
   - Penetration testing (basic)
   - Review IAM permissions
   - Ensure HTTPS everywhere
   - GDPR compliance checklist

**Deliverables:**
- Fully functional MVP deployed
- 10-20 beta users actively using the platform
- Feedback collection in progress

---

## VI. Monorepo Structure

```
docprocessing_ai/
├── README.md                          # Project overview, setup instructions
├── .gitignore
├── .github/
│   └── workflows/
│       ├── backend-ci.yml             # CI/CD for backend services
│       └── frontend-ci.yml            # CI/CD for frontend
│
├── terraform/                         # Infrastructure as Code
│   ├── main.tf                        # Main Terraform configuration
│   ├── variables.tf
│   ├── outputs.tf
│   ├── modules/
│   │   ├── cloud_run/
│   │   ├── cloud_sql/
│   │   ├── pub_sub/
│   │   ├── storage/
│   │   └── iam/
│   └── environments/
│       ├── dev.tfvars
│       └── prod.tfvars
│
├── backend/                           # Python backend (all services)
│   ├── shared/                        # Shared code across services
│   │   ├── __init__.py
│   │   ├── database.py                # SQLAlchemy setup
│   │   ├── models.py                  # Database models
│   │   ├── schemas.py                 # Pydantic schemas
│   │   ├── auth.py                    # Firebase Auth utilities
│   │   ├── gcs.py                     # Cloud Storage utilities
│   │   ├── pubsub.py                  # Pub/Sub utilities
│   │   └── config.py                  # Configuration management
│   │
│   ├── api_gateway/                   # Main API Gateway service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py                    # FastAPI app
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── documents.py
│   │   │   ├── invoices.py
│   │   │   ├── ocr.py
│   │   │   ├── summaries.py
│   │   │   ├── chat.py
│   │   │   ├── filling.py
│   │   │   └── admin.py
│   │   └── middleware/
│   │       ├── auth_middleware.py
│   │       └── tenant_middleware.py
│   │
│   ├── workers/                       # AI worker services
│   │   ├── invoice_worker/
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   ├── main.py
│   │   │   └── processor.py           # Invoice processing logic
│   │   ├── ocr_worker/
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   ├── main.py
│   │   │   └── ocr_methods.py
│   │   ├── summarizer_worker/
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   ├── main.py
│   │   │   └── summarizer.py
│   │   ├── rag_ingest_worker/
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   ├── main.py
│   │   │   └── ingestion.py
│   │   ├── rag_query_worker/
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   ├── main.py
│   │   │   └── query.py
│   │   └── docfill_worker/
│   │       ├── Dockerfile
│   │       ├── requirements.txt
│   │       ├── main.py
│   │       ├── id_extractor.py
│   │       └── pdf_filler.py
│   │
│   ├── migrations/                    # Alembic database migrations
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   │
│   └── scripts/                       # Utility scripts
│       ├── seed_database.py
│       ├── run_migration.py
│       └── test_gcp_apis.py
│
├── frontend/                          # React frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── public/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Auth/
│   │   │   │   ├── Login.tsx
│   │   │   │   └── Signup.tsx
│   │   │   ├── Documents/
│   │   │   │   ├── DocumentList.tsx
│   │   │   │   ├── DocumentUpload.tsx
│   │   │   │   └── DocumentViewer.tsx
│   │   │   ├── Invoices/
│   │   │   │   ├── InvoiceList.tsx
│   │   │   │   └── InvoiceValidation.tsx
│   │   │   ├── Chat/
│   │   │   │   └── ChatInterface.tsx
│   │   │   └── Common/
│   │   │       ├── Header.tsx
│   │   │       ├── Sidebar.tsx
│   │   │       └── LoadingSpinner.tsx
│   │   ├── services/
│   │   │   ├── api.ts                 # API client
│   │   │   └── firebase.ts            # Firebase setup
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useDocuments.ts
│   │   └── utils/
│   │       └── formatters.ts
│   └── Dockerfile                     # Optional: containerize frontend
│
├── docs/                              # Documentation
│   ├── architecture.md
│   ├── api_reference.md
│   ├── user_guide.md
│   ├── deployment.md
│   └── compliance.md
│
├── tests/                             # Tests
│   ├── backend/
│   │   ├── test_api_gateway.py
│   │   └── test_workers.py
│   └── frontend/
│       └── e2e/
│
└── starting_ideas.md                  # Original blueprint (this file)
└── technical_specification.md         # This document
```

---

## VII. Technology Stack Summary

### Backend
- **Language:** Python 3.11+
- **API Framework:** FastAPI 0.104+
- **ASGI Server:** Uvicorn
- **ORM:** SQLAlchemy 2.0+
- **Migrations:** Alembic
- **Authentication:** Firebase Admin SDK
- **Async Tasks:** Google Pub/Sub
- **AI/ML Libraries:**
  - `google-cloud-documentai`
  - `google-cloud-aiplatform` (Vertex AI)
  - `google-cloud-vision`
  - `langchain` (for chunking, optional)
  - `pypdfform` (PDF filling)

### Frontend
- **Framework:** React 18+
- **Language:** TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **State Management:** React Query + Context API
- **Authentication:** Firebase JS SDK
- **HTTP Client:** Axios
- **Routing:** React Router

### Infrastructure
- **Cloud Provider:** Google Cloud Platform
- **Compute:** Cloud Run (serverless containers)
- **Database:** Cloud SQL PostgreSQL 15
- **Storage:** Google Cloud Storage
- **Messaging:** Pub/Sub
- **Authentication:** Firebase Auth
- **Secrets:** Secret Manager
- **IaC:** Terraform
- **CI/CD:** GitHub Actions
- **Monitoring:** Cloud Logging + Cloud Monitoring

### Development
- **Version Control:** Git + GitHub
- **Containerization:** Docker
- **Local Dev:** Python venv, Docker Compose (optional)
- **Code Quality:** Black (formatter), Ruff (linter), MyPy (type checking)
- **Testing:** Pytest (backend), Vitest (frontend)

---

## VIII. Compliance & Security (MVP-Level)

### A. GDPR Compliance (Basic)

**Requirements Implemented:**
1. **Data Minimization:** Only collect necessary user data (email, name, documents)
2. **Right to Access:** API endpoint to export user data: `GET /admin/export-user-data`
3. **Right to Erasure:** API endpoint to delete user data: `DELETE /admin/delete-user-data`
4. **Data Residency:** All data stored in EU region (europe-west1 or europe-west3)
5. **Encryption:**
   - At rest: Cloud SQL and GCS default encryption
   - In transit: TLS 1.3 for all API calls
6. **Audit Logs:** All data access logged in `audit_logs` table

**Phase 2 GDPR Features (Post-MVP):**
- Cookie consent banner
- Privacy policy generator
- GDPR consent management
- Data retention policies

### B. EU AI Act Compliance (MVP-Level)

**Classification:** High-Risk AI System (processes identity documents and financial data)

**Requirements Implemented:**
1. **Human-in-the-Loop:** Invoice validation UI allows human review/correction
2. **Logging & Traceability:** All AI processing logged with:
   - Input document
   - Model used
   - Confidence scores
   - Timestamp
   - User who validated
3. **Documentation:** Technical docs in `/docs` directory
4. **Transparency:** UI shows which AI model was used and confidence scores

**Phase 2 AI Act Features (Post-MVP):**
- Risk management documentation
- Bias testing for ID extraction
- Model cards for each AI service
- Conformity assessment

### C. Security Measures

**Implemented:**
1. **Authentication:** Firebase Auth with JWT tokens
2. **Authorization:** Role-based access control (admin, user, viewer)
3. **Multi-Tenancy:** Strict tenant_id filtering on all queries
4. **Input Validation:** Pydantic models validate all API inputs
5. **Rate Limiting:** Cloud Run concurrency limits
6. **Secrets Management:** API keys stored in Secret Manager (not in code)
7. **CORS:** Configured to allow only frontend domain
8. **SQL Injection Prevention:** SQLAlchemy ORM (parameterized queries)
9. **File Upload Security:**
   - File type validation (MIME type checking)
   - File size limits (10 MB default)
   - Virus scanning (Cloud Security Scanner, Phase 2)

**Phase 2 Security Features:**
- Penetration testing
- Security audit
- DDoS protection via Cloud Armor
- WAF rules
- Automated vulnerability scanning

---

## IX. Cost Optimization Strategies

### A. MVP Cost Controls

1. **Cloud Run:**
   - Set max instances per service (5 for workers, 10 for API)
   - Use minimum CPU/memory that works
   - Scale to zero for low-traffic workers

2. **Cloud SQL:**
   - Start with smallest instance (db-f1-micro)
   - Enable auto-increase for storage (only pay for what you use)
   - Schedule automated backups during off-peak hours

3. **AI API Usage:**
   - Default to cheapest models (Gemini Flash, Document AI OCR)
   - Only upgrade to premium models (Claude, Gemini Pro) when necessary
   - Cache repeated queries (e.g., same question asked twice)
   - Implement user rate limits (e.g., 50 documents/day during free beta)

4. **Storage:**
   - Use Standard class (not Nearline/Coldline) for active files
   - Implement lifecycle policy: delete temp files after 7 days
   - Compress documents before storage (if possible)

5. **Pub/Sub:**
   - Use standard tier (no need for guaranteed ordering)
   - Set message retention to 1 day (default is 7 days)

6. **Free Tiers:**
   - Firebase Auth: Free up to 50k monthly active users
   - Vercel frontend hosting: Free for hobby projects
   - Cloud Run: 2 million requests/month free

### B. Monitoring & Alerts

**Set up cost alerts:**
- Alert when monthly bill exceeds $100
- Alert when monthly bill exceeds $500
- Weekly cost report via email

**Monitor usage:**
- Track API calls per user (detect abuse)
- Track document processing volume
- Identify expensive operations (e.g., long summaries)

---

## X. Success Metrics & KPIs

### A. Technical Metrics

1. **Performance:**
   - API response time (p95): < 500ms
   - Document upload time: < 5 seconds for 10 MB file
   - Invoice processing time: < 30 seconds
   - OCR processing time: < 60 seconds for 10-page document
   - Summarization time: < 90 seconds for 50-page document
   - RAG query response time: < 5 seconds

2. **Reliability:**
   - API uptime: > 99.5%
   - Worker success rate: > 95%
   - Error rate: < 2%

3. **Accuracy:**
   - Invoice extraction accuracy: > 85% (before human validation)
   - OCR accuracy: > 95% on clean documents
   - RAG answer relevance: > 80% (user feedback)

### B. Business Metrics (Beta Phase)

1. **User Acquisition:**
   - Beta signups: 50+ users
   - Active users (processed ≥1 document): 20+ users
   - Weekly active users: 10+ users

2. **Usage:**
   - Documents processed: 500+ total
   - Average documents per user: 10+
   - Most used feature: (identify during beta)
   - Feature adoption rates

3. **Feedback:**
   - User satisfaction score: 4+/5
   - Net Promoter Score (NPS): Calculate after beta
   - Feature requests: Collect and prioritize

4. **Vertical Insights:**
   - Which vertical has highest usage? (legal, logistics, finance, other)
   - Which document types are most common?
   - Which features are most valuable per vertical?

**Post-Beta Decision:**
Based on metrics, identify the **single vertical** with highest traction to focus on for paid launch (Vertical SaaS strategy).

---

## XI. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Google Document AI accuracy lower than expected** | High | Medium | Implement hybrid approach: Use Gemini Vision for low-confidence extractions |
| **Solo developer bandwidth** | High | High | Strict MVP scope, use managed services, avoid custom infrastructure |
| **Cloud costs exceed budget** | Medium | Medium | Set hard spending limits, implement rate limiting, monitor usage daily |
| **Firebase Auth limitations** | Low | Low | Firebase Auth is mature and reliable; have backup plan to migrate to custom auth |
| **Multi-vertical approach dilutes focus** | Medium | Medium | Use beta phase to identify best vertical, then pivot to vertical SaaS |
| **Slow React learning curve** | Medium | Low | Use React templates/starters, focus on backend first, iterate on frontend |
| **EU compliance complexity** | High | Medium | Start with MVP-level compliance, hire consultant for Phase 2 full compliance |
| **Beta user acquisition challenges** | Medium | High | Leverage personal network, Romanian business communities, offer incentives |
| **AI model output quality issues** | High | Low | Implement human-in-the-loop validation, allow users to provide feedback |
| **Data migration complexity** | Low | Low | Use Alembic for versioned migrations, test thoroughly in dev environment |

---

## XII. Next Steps: From Specification to Implementation Plan

This technical specification provides a comprehensive foundation for building the Document AI SaaS platform. The next step is to convert this specification into a **detailed, task-by-task implementation plan** that another AI agent (or developer) can execute.

**The implementation plan should include:**
1. **Task Breakdown:** Each phase broken into specific, actionable tasks
2. **Time Estimates:** Realistic estimates for each task (in hours/days)
3. **Dependencies:** What must be completed before each task can start
4. **Code Templates:** Boilerplate code for common patterns (FastAPI routes, database models, etc.)
5. **Command References:** Exact gcloud, terraform, docker commands to run
6. **Configuration Files:** Complete examples of Dockerfiles, requirements.txt, terraform configs
7. **Testing Strategies:** What to test at each stage
8. **Deployment Steps:** Step-by-step deployment instructions
9. **Troubleshooting Guide:** Common issues and solutions
10. **Rollback Plans:** How to revert if something goes wrong

**Key Outputs for Implementation Plan:**
- [ ] Terraform configuration files (complete and ready to apply)
- [ ] Database schema SQL scripts (ready to execute)
- [ ] FastAPI project structure (boilerplate code)
- [ ] Docker configurations for all services
- [ ] GitHub Actions workflows (CI/CD pipelines)
- [ ] React project structure (boilerplate code)
- [ ] API integration examples (Python code for each GCP service)
- [ ] Environment configuration templates (.env files)
- [ ] Deployment runbooks (step-by-step guides)
- [ ] Monitoring & alerting setup guides

**Recommendation:**
Use a specialized planning AI agent (e.g., `/superpowers:write-plan` command) to convert this technical specification into a granular, executable implementation plan with **bite-sized tasks** optimized for solo developer execution.

---

## XIII. Conclusion

This technical specification adapts the original Azure-focused document AI blueprint to:

1. **Google Cloud Platform**: All Azure services replaced with GCP equivalents
2. **All-Python Architecture**: Simplified for solo developer efficiency
3. **Multi-Vertical Strategy**: Target multiple markets during beta to identify best fit
4. **Serverless-First**: Cloud Run, Pub/Sub, managed services to minimize ops overhead
5. **Cost-Optimized**: Projected $126-$539/month for MVP phase (within budget)
6. **Compliance-Ready**: MVP-level GDPR and EU AI Act implementation
7. **Rapid Launch Path**: 12-week implementation plan to beta launch

**Strategic Advantages:**
- **Faster Time to Market**: All-Python reduces context switching, Cloud Run eliminates infrastructure management
- **Lower Risk**: Free beta model validates product-market fit before monetization
- **Data-Driven Pivot**: Multi-vertical beta phase identifies highest-traction market for focused growth
- **Scalable Foundation**: Microservices architecture supports future growth to 10k+ users
- **EU-Compliant by Design**: Data residency, audit logging, human oversight built from day 1

**Success Criteria:**
- **Week 12**: 20+ active beta users processing real documents
- **Month 4**: Clear signal on which vertical has highest engagement
- **Month 5**: Pivot to vertical SaaS model for that market
- **Month 6**: Launch paid tiers with first paying customers

This platform is positioned to become **the leading AI document processing solution** for a specific high-value vertical in the Romanian and broader EU market.

---

**Document Status:** Ready for implementation planning
**Next Action:** Generate detailed task-level implementation plan with code templates
