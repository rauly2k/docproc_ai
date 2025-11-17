# Document AI - Phase 6: Document Filling Implementation

This repository contains the implementation of Phase 6 (Document Filling) for the Document AI SaaS platform.

## Features Implemented

### Backend Services

1. **Document Filling Worker** (`backend/workers/docfill_worker/`)
   - Extracts data from ID cards using Google Document AI
   - Fills PDF forms automatically with extracted data
   - Supports Romanian ID cards, EU ID cards, and passports
   - Deployed as a Cloud Run service

2. **API Gateway** (`backend/api_gateway/`)
   - REST API endpoints for document filling operations
   - Authentication with Firebase
   - Multi-tenant support
   - Deployed as a Cloud Run service

3. **Shared Modules** (`backend/shared/`)
   - Database models (SQLAlchemy)
   - Pydantic schemas for validation
   - Firebase authentication utilities
   - Google Cloud Storage utilities
   - Pub/Sub publishing utilities
   - Configuration management

### Frontend Application

1. **Document Filling UI** (`frontend/`)
   - React + TypeScript + Vite
   - Tailwind CSS for styling
   - Document filling form component
   - Template selection
   - Download filled PDFs
   - React Query for state management

## Project Structure

```
docproc_ai/
├── backend/
│   ├── shared/                    # Shared modules
│   │   ├── config.py             # Configuration
│   │   ├── database.py           # Database setup
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── schemas.py            # Pydantic schemas
│   │   ├── auth.py               # Firebase auth
│   │   ├── gcs.py                # Cloud Storage
│   │   ├── pubsub.py             # Pub/Sub
│   │   └── pdf_templates/        # PDF form templates
│   ├── api_gateway/              # API Gateway service
│   │   ├── main.py
│   │   ├── routes/
│   │   │   └── filling.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── workers/
│   │   └── docfill_worker/       # Document filling worker
│   │       ├── main.py
│   │       ├── processor.py
│   │       ├── Dockerfile
│   │       └── requirements.txt
│   └── requirements.txt          # Base requirements
├── frontend/                      # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   └── Filling/
│   │   ├── pages/
│   │   ├── services/
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── scripts/                       # Deployment scripts
│   ├── deploy-api-gateway.sh
│   └── deploy-docfill-worker.sh
└── docs/                          # Documentation
    └── plans/
        └── phase-6-document-filling.md
```

## Prerequisites

### Development Environment

- Python 3.11+
- Node.js 18+
- Docker Desktop
- Google Cloud SDK (`gcloud` CLI)
- Firebase CLI

### Google Cloud Platform

1. **GCP Project** with enabled APIs:
   - Cloud Run
   - Cloud SQL (PostgreSQL)
   - Pub/Sub
   - Cloud Storage
   - Document AI
   - Secret Manager
   - Artifact Registry

2. **Document AI Processor**:
   - Create an Identity Document Processor in EU region
   - Note the processor ID

3. **GCS Buckets**:
   - `docai-uploads-{env}` - Raw uploads
   - `docai-processed-{env}` - Processed/filled PDFs

4. **Pub/Sub Topics**:
   - `document-filling` - Document filling jobs

5. **Cloud SQL Database**:
   - PostgreSQL 15
   - Database: `docai`
   - Tables created from `backend/shared/models.py`

### Environment Variables

Backend services need these environment variables (store in Secret Manager):

```bash
# GCP Configuration
PROJECT_ID=docai-mvp-prod
REGION=europe-west1
ENVIRONMENT=prod

# Database
DATABASE_URL=postgresql://user:pass@host:5432/docai
DB_PASSWORD=your_password

# GCS Buckets
GCS_BUCKET_UPLOADS=docai-uploads-prod
GCS_BUCKET_PROCESSED=docai-processed-prod

# Document AI
DOCUMENTAI_ID_PROCESSOR_ID=your_processor_id
```

Frontend needs (create `frontend/.env`):

```bash
VITE_API_BASE_URL=https://api-gateway-url.run.app
VITE_FIREBASE_API_KEY=your_key
VITE_FIREBASE_AUTH_DOMAIN=your_domain
VITE_FIREBASE_PROJECT_ID=your_project
```

## Local Development

### Backend

1. **Install dependencies**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   export PROJECT_ID=docai-mvp-prod
   export DATABASE_URL=postgresql://docai:password@localhost:5432/docai
   export DOCUMENTAI_ID_PROCESSOR_ID=your_processor_id
   ```

3. **Run API Gateway**:
   ```bash
   cd api_gateway
   python main.py
   # Runs on http://localhost:8000
   # API docs at http://localhost:8000/docs
   ```

4. **Run Document Filling Worker**:
   ```bash
   cd workers/docfill_worker
   python main.py
   # Runs on http://localhost:8005
   ```

### Frontend

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Create `.env` file**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run development server**:
   ```bash
   npm run dev
   # Runs on http://localhost:3000
   ```

## Deployment

### Deploy Document Filling Worker

```bash
./scripts/deploy-docfill-worker.sh
```

This will:
- Build Docker image
- Push to Artifact Registry
- Deploy to Cloud Run
- Create Pub/Sub subscription

### Deploy API Gateway

```bash
./scripts/deploy-api-gateway.sh
```

This will:
- Build Docker image
- Push to Artifact Registry
- Deploy to Cloud Run
- Return API Gateway URL

### Deploy Frontend

```bash
cd frontend
npm run build
# Deploy to Vercel, Netlify, or Firebase Hosting
```

## Usage

### 1. Upload ID Document

First, upload an ID card or passport image through the document upload interface.

### 2. Fill PDF Form

1. Navigate to `/filling` page
2. Select your uploaded ID document
3. Choose a PDF form template
4. Click "Extract Data & Fill Form"
5. Wait for processing (30-60 seconds)
6. Download the filled PDF

### 3. API Usage

**List templates**:
```bash
curl https://api-gateway-url/v1/filling/templates \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Extract and fill**:
```bash
curl -X POST https://api-gateway-url/v1/filling/extract-and-fill \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id_document_id": "uuid",
    "template_name": "romanian_standard_form"
  }'
```

**Download filled PDF**:
```bash
curl https://api-gateway-url/v1/filling/{document_id}/download \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Adding New PDF Templates

1. Create a fillable PDF form with named fields
2. Save to `backend/shared/pdf_templates/{template_name}.pdf`
3. Update field mapping in `backend/workers/docfill_worker/processor.py`:
   ```python
   def _map_data_to_form_fields(self, data, template_name):
       if template_name == "my_custom_form":
           return {
               "field_name": data.get("extracted_field", ""),
               # Map more fields...
           }
   ```
4. Add template info to API in `backend/api_gateway/routes/filling.py`:
   ```python
   FillingTemplateInfo(
       name="my_custom_form",
       display_name="My Custom Form",
       description="Description here",
       fields=["field1", "field2"]
   )
   ```

## Testing

### Test Document AI ID Processor

```bash
cd backend/workers/docfill_worker
python -c "
from processor import DocumentFillingProcessor
p = DocumentFillingProcessor()
data = p.extract_id_data('gs://your-bucket/test-id.jpg')
print(data)
"
```

### Test PDF Filling

```bash
python -c "
from processor import DocumentFillingProcessor
p = DocumentFillingProcessor()
test_data = {
    'family_name': 'Popescu',
    'given_names': 'Ion',
    'cnp': '1234567890123',
    # ... more fields
}
p.fill_pdf_form('romanian_standard_form', test_data, 'gs://bucket/output.pdf')
"
```

## Monitoring

### Cloud Run Logs

```bash
# API Gateway logs
gcloud run logs read api-gateway --region europe-west1

# Worker logs
gcloud run logs read docfill-worker --region europe-west1
```

### Pub/Sub Monitoring

```bash
# Check subscription
gcloud pubsub subscriptions describe document-filling-sub

# Check dead letter messages
gcloud pubsub topics list-subscriptions document-filling
```

## Troubleshooting

### Worker not processing messages

1. Check Pub/Sub subscription exists:
   ```bash
   gcloud pubsub subscriptions list
   ```

2. Check worker is running:
   ```bash
   gcloud run services describe docfill-worker --region europe-west1
   ```

3. Check worker logs for errors

### Document AI errors

1. Verify processor ID is correct
2. Check processor is in EU region
3. Verify service account has `documentai.admin` role

### PDF filling errors

1. Verify template exists in `pdf_templates/` directory
2. Check form field names match mapping
3. Ensure PDF is actually fillable

## Next Steps

Phase 6 is now complete! Next implementation phases:

- **Phase 1-5**: Implement core platform, invoice processing, OCR, summarization, and RAG
- **Phase 7**: Polish, monitoring, and beta launch

## Support

For issues or questions:
- Check the technical specification: `docs/technical_specification.md`
- Review the plan: `docs/plans/phase-6-document-filling.md`

## License

Proprietary - Document AI SaaS Platform
