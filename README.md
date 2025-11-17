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
docproc_ai/
├── backend/
│   ├── shared/           # Shared modules (database, models, auth, etc.)
│   ├── api_gateway/      # Main API Gateway service
│   └── workers/          # AI worker services
│       ├── ocr_worker/   # OCR processing worker
│       ├── invoice_worker/
│       ├── summarizer_worker/
│       └── ...
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

- Python 3.11+
- Node.js 18+
- Docker
- Google Cloud SDK
- GCP Project with required APIs enabled

### Backend Setup

```bash
# Create virtual environment
cd backend
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

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# Edit .env with your API base URL

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

## API Documentation

Once the API Gateway is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

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

For issues and questions, please contact the development team.
