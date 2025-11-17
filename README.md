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
