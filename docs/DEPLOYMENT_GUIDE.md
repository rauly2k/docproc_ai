# Deployment Guide

## Prerequisites

- Google Cloud Platform account with billing enabled
- gcloud CLI installed and authenticated
- Terraform installed (v1.5+)
- Docker installed
- Firebase project created

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/docproc_ai.git
cd docproc_ai
```

### 2. Set Environment Variables

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="europe-west1"
export FIREBASE_PROJECT="your-firebase-project"
```

### 3. Enable GCP APIs

```bash
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable sql-component.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable storage-component.googleapis.com
gcloud services enable documentai.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 4. Initialize Terraform

```bash
cd terraform
terraform init
terraform plan -var="project_id=$PROJECT_ID"
terraform apply -var="project_id=$PROJECT_ID"
```

This creates:
- Cloud SQL database
- Cloud Storage buckets
- Pub/Sub topics and subscriptions
- Service accounts
- IAM roles

### 5. Database Setup

```bash
# Get database connection details
export DB_HOST=$(terraform output -raw db_host)
export DB_NAME=$(terraform output -raw db_name)

# Run migrations
cd ../backend
alembic upgrade head
```

### 6. Build and Deploy Services

```bash
# Build all Docker images
./scripts/build_all.sh

# Deploy all services
./scripts/deploy_all.sh
```

### 7. Deploy Frontend

```bash
cd frontend
npm install
npm run build

# Deploy to Vercel
vercel --prod
```

### 8. Verify Deployment

```bash
# Check all services are running
gcloud run services list --region=$REGION

# Test API health
curl https://api-gateway-xxx.run.app/health
```

## Updating

### Backend Updates

```bash
# Make changes to code
# Build and deploy specific service
./scripts/deploy_service.sh api-gateway

# Or deploy all
./scripts/deploy_all.sh
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
```

## Monitoring

- **Logs**: https://console.cloud.google.com/logs
- **Monitoring**: https://console.cloud.google.com/monitoring
- **Cloud Run**: https://console.cloud.google.com/run

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
```

### Database Connection Issues

```bash
# Test connection from Cloud Shell
gcloud sql connect documentai-db --user=postgres

# Check Cloud SQL Proxy
gcloud sql instances describe documentai-db
```

### Environment Variables

```bash
# List secrets
gcloud secrets list

# Check service environment
gcloud run services describe api-gateway --region=$REGION \
  --format="value(spec.template.spec.containers[0].env)"
```

## Cost Optimization

1. **Cloud Run**: Set max instances per service (5 for workers, 10 for API)
2. **Cloud SQL**: Start with smallest instance (db-f1-micro)
3. **Storage**: Implement lifecycle policy: delete temp files after 7 days
4. **AI APIs**: Default to cheapest models (Gemini Flash)

## Security Best Practices

1. **Secrets**: Never commit secrets to git, use Secret Manager
2. **IAM**: Follow principle of least privilege
3. **CORS**: Configure allowed origins properly
4. **HTTPS**: Enforce HTTPS for all endpoints
5. **Rate Limiting**: Implement rate limiting to prevent abuse
