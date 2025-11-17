# Deployment Guide

## Prerequisites

- Google Cloud Platform account with billing enabled
- gcloud CLI installed and authenticated
- Terraform installed (v1.5+)
- Docker installed
- Firebase project created
- Node.js 18+ and Python 3.11+

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/document-ai-saas.git
cd document-ai-saas
```

### 2. Set Environment Variables

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="europe-west1"
export FIREBASE_PROJECT="your-firebase-project"
```

### 3. Enable GCP APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable sql-component.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable documentai.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable redis.googleapis.com
```

### 4. Initialize Terraform

```bash
cd terraform
terraform init
terraform plan -var="project_id=$PROJECT_ID"
terraform apply -var="project_id=$PROJECT_ID"
```

This creates:
- Cloud SQL PostgreSQL database with pgvector
- Cloud Storage buckets (uploads, processed, temp)
- Pub/Sub topics and subscriptions
- Redis instance for caching
- Service accounts and IAM roles

### 5. Database Setup

```bash
# Get database connection details
DB_HOST=$(terraform output -raw db_host)
DB_NAME=$(terraform output -raw db_name)

# Run migrations
cd ../backend
pip install -r requirements.txt
alembic upgrade head
```

### 6. Build and Deploy Services

```bash
# Build all Docker images
cd ..
./scripts/build-all.sh

# Deploy all services
./scripts/deploy-all.sh
```

This deploys:
- API Gateway
- Invoice Worker
- OCR Worker
- Summarizer Worker
- RAG Ingest Worker
- RAG Query Worker
- Document Filling Worker

### 7. Deploy Frontend

```bash
cd frontend
npm install
npm run build

# Deploy to Vercel
vercel --prod

# Or deploy to Firebase Hosting
firebase deploy --only hosting
```

### 8. Verify Deployment

```bash
# Check all services are running
gcloud run services list --region=$REGION

# Test API health
curl https://your-api-gateway-url/health

# Check database connectivity
psql -h $DB_HOST -U postgres -d documentai
```

## Configuration

### Environment Variables

Create `.env` file in backend directory:

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

# Pub/Sub
PUBSUB_TOPIC_INVOICE=invoice-processing
PUBSUB_TOPIC_OCR=ocr-processing
PUBSUB_TOPIC_SUMMARY=summarization-processing
PUBSUB_TOPIC_RAG_INGEST=rag-ingestion
PUBSUB_TOPIC_DOCFILL=document-filling

# Document AI
DOCUMENTAI_INVOICE_PROCESSOR_ID=abc123
DOCUMENTAI_OCR_PROCESSOR_ID=def456
DOCUMENTAI_ID_PROCESSOR_ID=ghi789

# Redis
REDIS_HOST=10.0.0.3
REDIS_PORT=6379

# Sentry (optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# Frontend URL
FRONTEND_URL=https://your-app.vercel.app
```

### Secrets Management

Store sensitive data in Secret Manager:

```bash
# Database password
echo -n "your-db-password" | gcloud secrets create database-password --data-file=-

# Firebase service account
gcloud secrets create firebase-credentials --data-file=serviceAccount.json

# Grant access to service accounts
gcloud secrets add-iam-policy-binding database-password \
  --member="serviceAccount:api-gateway@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Updating

### Backend Updates

```bash
# Make changes to code
# Build and deploy specific service
./scripts/deploy-service.sh api-gateway

# Or deploy all
./scripts/deploy-all.sh
```

### Frontend Updates

```bash
cd frontend
npm run build
vercel --prod
```

### Database Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Monitoring

### Logs

```bash
# View API Gateway logs
gcloud run services logs read api-gateway --region=$REGION --limit=100

# Stream logs in real-time
gcloud run services logs tail api-gateway --region=$REGION

# Filter error logs
gcloud logging read "severity=ERROR AND resource.type=cloud_run_revision" --limit=50
```

### Monitoring Dashboard

Access Cloud Monitoring dashboard:
```
https://console.cloud.google.com/monitoring/dashboards
```

Key metrics to monitor:
- Request rate (requests/minute)
- Response latency (p50, p95, p99)
- Error rate (%)
- Pub/Sub queue depth
- Database connections
- Worker processing time

### Alerts

View and configure alerts:
```
https://console.cloud.google.com/monitoring/alerting
```

Pre-configured alerts:
- High error rate (>5% errors)
- API downtime
- High latency (>2 seconds p95)
- Database connection issues
- High queue depth (>100 messages)

## Rollback

### Rollback Cloud Run Service

```bash
# List revisions
gcloud run revisions list --service=api-gateway --region=$REGION

# Rollback to previous revision
gcloud run services update-traffic api-gateway \
  --to-revisions=api-gateway-00002-xyz=100 \
  --region=$REGION
```

### Rollback Database

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>
```

## Troubleshooting

### Service Not Starting

```bash
# Check logs
gcloud run services logs read api-gateway --region=$REGION --limit=100

# Check service status
gcloud run services describe api-gateway --region=$REGION

# Test locally with Docker
docker build -t api-gateway -f backend/api_gateway/Dockerfile .
docker run -p 8080:8080 --env-file .env api-gateway
```

### Database Connection Issues

```bash
# Test connection from Cloud Shell
gcloud sql connect documentai-db --user=postgres

# Check Cloud SQL Proxy
gcloud sql instances describe documentai-db

# Verify network configuration
gcloud compute networks describe default
```

### High Latency

```bash
# Check Cloud Run instance count
gcloud run services describe api-gateway --region=$REGION \
  --format="value(spec.template.spec.containerConcurrency)"

# Increase min instances
gcloud run services update api-gateway \
  --region=$REGION \
  --min-instances=2

# Check database query performance
# Connect to database and run:
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
```

### Out of Memory

```bash
# Increase memory allocation
gcloud run services update api-gateway \
  --region=$REGION \
  --memory=2Gi

# Check current resource usage
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/memory/utilizations"'
```

## Security

### SSL/TLS

Cloud Run automatically provides HTTPS. For custom domains:

```bash
gcloud beta run domain-mappings create \
  --service=api-gateway \
  --domain=api.yourdomain.com \
  --region=$REGION
```

### Firewall Rules

```bash
# Restrict database access to Cloud Run services only
gcloud sql instances patch documentai-db \
  --authorized-networks=0.0.0.0/0 \
  --no-assign-ip

# Use VPC connector
gcloud compute networks vpc-access connectors create documentai-connector \
  --region=$REGION \
  --network=default \
  --range=10.8.0.0/28
```

### Rotate Secrets

```bash
# Update database password
gcloud sql users set-password postgres \
  --instance=documentai-db \
  --password=<NEW_PASSWORD>

# Update Secret Manager
echo -n "<NEW_PASSWORD>" | gcloud secrets versions add database-password --data-file=-

# Restart services to pick up new secret
gcloud run services update api-gateway --region=$REGION
```

## Backup and Recovery

### Database Backup

```bash
# Manual backup
gcloud sql backups create --instance=documentai-db

# List backups
gcloud sql backups list --instance=documentai-db

# Restore from backup
gcloud sql backups restore <BACKUP_ID> \
  --backup-instance=documentai-db
```

### Document Backup

```bash
# Sync GCS buckets to local
gsutil -m rsync -r gs://your-bucket-documents ./backup/

# Restore from local
gsutil -m rsync -r ./backup/ gs://your-bucket-documents
```

## Cost Optimization

### Reduce Cloud Run Costs

```bash
# Set min instances to 0 for workers
gcloud run services update invoice-worker \
  --region=$REGION \
  --min-instances=0

# Use smaller instance types
gcloud run services update api-gateway \
  --region=$REGION \
  --memory=1Gi \
  --cpu=1
```

### Database Optimization

```bash
# Use smaller instance for dev/staging
gcloud sql instances patch documentai-db-dev \
  --tier=db-f1-micro

# Enable automatic storage increase
gcloud sql instances patch documentai-db \
  --database-flags=max_connections=100
```

### Storage Lifecycle

```bash
# Auto-delete old documents after 90 days
gsutil lifecycle set lifecycle.json gs://your-bucket-documents
```

lifecycle.json:
```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
```

## Support

For deployment issues:
- Check deployment guide: /docs/guides/deployment-guide.md
- Review logs: Cloud Console > Logging
- Contact: devops@documentai.com
