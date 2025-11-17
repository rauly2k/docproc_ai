# Document AI SaaS Platform - Phase 2 Implementation

This repository contains the implementation of Phase 2 (Invoice Processing) of the Document AI SaaS platform.

## Project Structure

```
docproc_ai/
├── backend/
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
# Edit .env with your configuration

# Run development server
npm run dev
```

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
./scripts/deploy-api-gateway.sh
```

This script will:
1. Build Docker image for API gateway
2. Push to Google Artifact Registry
3. Deploy to Cloud Run

## Environment Variables

### Backend

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
