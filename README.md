# Document AI SaaS - Intelligent Document Processing Platform

An AI-powered SaaS platform for document processing with invoice extraction, OCR, summarization, RAG chat, and document filling capabilities.

## 🚀 Features

- **Invoice Processing**: Automated data extraction from invoices with human-in-the-loop validation
- **Generic OCR**: Extract text from any document type
- **Document Summarization**: AI-powered summaries using Google Gemini
- **Chat with PDF**: RAG-based question answering over your documents
- **Document Filling**: Auto-fill PDF forms from Romanian ID cards
- **Multi-tenant**: Secure multi-tenant architecture with Firebase Auth
- **Scalable**: Built on Google Cloud Platform with Cloud Run and Pub/Sub

## 📋 Architecture

```
┌─────────────┐
│   React     │
│  Frontend   │
└──────┬──────┘
       │ REST API
       ▼
┌─────────────┐     ┌──────────────┐
│   FastAPI   │────▶│ Cloud SQL    │
│  API Gateway│     │ (PostgreSQL) │
└──────┬──────┘     └──────────────┘
       │ Pub/Sub
       ▼
┌─────────────────────────────────┐
│    AI Worker Services            │
│  • Invoice  • OCR  • Summarizer │
│  • RAG Ingest  • Doc Filling    │
└─────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│   Google Cloud Storage          │
│   Document AI • Vertex AI       │
└─────────────────────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL with pgvector extension
- **Queue**: Google Cloud Pub/Sub
- **Storage**: Google Cloud Storage
- **AI**: Document AI, Vertex AI (Gemini)
- **Auth**: Firebase Authentication
- **Cache**: Redis
- **Monitoring**: Cloud Logging, Cloud Monitoring, Sentry

### Frontend
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **State**: React Query
- **Routing**: React Router
- **Hosting**: Vercel / Firebase Hosting

### Infrastructure
- **Cloud**: Google Cloud Platform
- **Compute**: Cloud Run (serverless)
- **IaC**: Terraform
- **CI/CD**: GitHub Actions

## 📦 Prerequisites

- **Google Cloud Platform** account with billing enabled
- **Firebase** project
- **gcloud CLI** installed and authenticated
- **Docker** (for local development and deployment)
- **Terraform** 1.5+
- **Node.js** 18+
- **Python** 3.11+

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/document-ai-saas.git
cd document-ai-saas
```

### 2. Set Environment Variables

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="europe-west1"
export FIREBASE_PROJECT="your-firebase-project-id"
```

### 3. Enable GCP APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  documentai.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  redis.googleapis.com
```

### 4. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan -var="project_id=$PROJECT_ID"
terraform apply -var="project_id=$PROJECT_ID"
```

### 5. Run Database Migrations

```bash
cd ../backend
pip install -r requirements.txt
alembic upgrade head
```

### 6. Deploy Services

```bash
cd ..
./scripts/deploy-all.sh
```

### 7. Deploy Frontend

```bash
cd frontend
npm install
npm run build
vercel --prod
```

## 🔧 Configuration

### Backend Environment Variables

Create `.env` file in `backend/` directory:

```bash
# GCP
PROJECT_ID=your-project-id
REGION=europe-west1
VERTEX_AI_LOCATION=us-central1

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Firebase
FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccount.json
FIREBASE_PROJECT_ID=your-firebase-project

# Cloud Storage
GCS_BUCKET_UPLOADS=your-project-uploads
GCS_BUCKET_PROCESSED=your-project-processed
GCS_BUCKET_TEMP=your-project-temp

# Document AI
DOCUMENTAI_INVOICE_PROCESSOR_ID=your-processor-id
DOCUMENTAI_OCR_PROCESSOR_ID=your-processor-id
DOCUMENTAI_ID_PROCESSOR_ID=your-processor-id

# Redis
REDIS_HOST=10.0.0.3
REDIS_PORT=6379

# Sentry (optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# Frontend URL
FRONTEND_URL=https://your-app.vercel.app
```

### Frontend Environment Variables

Create `.env.local` file in `frontend/` directory:

```bash
VITE_API_URL=https://your-api-gateway-url
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
```

## 🧪 Local Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run API Gateway
uvicorn api_gateway.main:app --reload --port 8080
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📚 Documentation

- **User Guide**: [docs/guides/user-guide.md](docs/guides/user-guide.md)
- **Deployment Guide**: [docs/guides/deployment-guide.md](docs/guides/deployment-guide.md)
- **Admin Guide**: [docs/guides/admin-guide.md](docs/guides/admin-guide.md)
- **API Documentation**: Available at `/docs` endpoint (Swagger UI)
- **Phase Plans**: [docs/plans/](docs/plans/)

## 🔒 Security

- All data encrypted in transit (TLS 1.3) and at rest
- Firebase Authentication with JWT tokens
- Multi-tenant isolation at database level
- Rate limiting and CORS protection
- Security headers (CSP, HSTS, etc.)
- Regular security audits
- GDPR compliant

## 📊 Monitoring

### Dashboards

- **Cloud Monitoring**: https://console.cloud.google.com/monitoring
- **Logs**: https://console.cloud.google.com/logs

### Key Metrics

- Request rate (requests/minute)
- Error rate (% of failed requests)
- Response latency (p50, p95, p99)
- Queue depth (Pub/Sub messages)
- Database connections
- Worker processing time

### Alerts

Pre-configured alerts for:
- High error rate (>5%)
- API downtime
- High latency (>2s p95)
- Database connection issues
- High queue depth (>100 messages)

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=. --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm run test
```

### Load Testing

```bash
# Install artillery
npm install -g artillery

# Run load test
artillery quick --count 50 --num 100 https://your-api-url/health
```

## 🚢 Deployment

### Backend

```bash
# Deploy all services
./scripts/deploy-all.sh

# Deploy specific service
gcloud run deploy api-gateway \
  --image gcr.io/$PROJECT_ID/api-gateway:latest \
  --region=$REGION
```

### Frontend

```bash
cd frontend
npm run build

# Deploy to Vercel
vercel --prod

# Or deploy to Firebase Hosting
firebase deploy --only hosting
```

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 💰 Cost Estimation

Estimated monthly costs for production (moderate usage):

| Service | Usage | Cost |
|---------|-------|------|
| Cloud Run (API) | 2M requests | $40 |
| Cloud Run (Workers) | 10K jobs | $15 |
| Cloud SQL | db-n1-standard-2 | $95 |
| Cloud Storage | 100GB | $2 |
| Pub/Sub | 2M messages | $8 |
| Document AI | 10K pages | $150 |
| Vertex AI | 500K tokens | $20 |
| Redis | 1GB | $30 |
| **Total** | | **~$360/month** |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Email**: support@documentai.com
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/document-ai-saas/issues)

## 🗺️ Roadmap

### Phase 0-7 ✅ (Complete)
- [x] Core platform infrastructure
- [x] Invoice processing
- [x] Generic OCR
- [x] Document summarization
- [x] Chat with PDF (RAG)
- [x] Document filling
- [x] Polish and beta launch

### Future Features
- [ ] Multi-language support (Romanian, Spanish, French)
- [ ] Batch processing
- [ ] API webhooks
- [ ] Custom model training
- [ ] Mobile app (iOS/Android)
- [ ] Zapier/Make integrations

## 🎯 Beta Program

We're currently in beta! Join our beta program to:
- Get free access during beta period
- 50% discount on first 3 months after launch
- Priority support
- Influence product roadmap

Contact: beta@documentai.com

## 📈 Performance

- API Response Time: <200ms (p95)
- Document Processing: 10-30 seconds
- OCR Accuracy: >95% (clear documents)
- Invoice Extraction: >90% accuracy
- Uptime: 99.9% SLA

## 🙏 Acknowledgments

Built with:
- Google Cloud Platform
- Firebase
- FastAPI
- React
- Tailwind CSS
- And many other amazing open-source projects

---

**Made with ❤️ by the Document AI Team**
