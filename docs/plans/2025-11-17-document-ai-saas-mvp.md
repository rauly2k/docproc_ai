# Document AI SaaS MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a production-ready B2B document processing SaaS platform on Google Cloud Platform with 5 core AI features (Invoice Processing, OCR, Summarization, Chat with PDF, Document Filling).

**Architecture:** All-Python event-driven microservices using FastAPI for API Gateway and 6 worker services, deployed on Cloud Run. Async processing via Google Pub/Sub, PostgreSQL with pgvector for RAG, React frontend with Firebase Auth.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Google Cloud Platform (Cloud Run, Cloud SQL, Pub/Sub, Document AI, Vertex AI), React, TypeScript, Terraform, Docker.

**Timeline:** 12 weeks (solo developer)

**Budget:** $500-2000/month during MVP phase

---

## Table of Contents

- [Phase 0: Infrastructure Setup (Week 1)](#phase-0-infrastructure-setup-week-1)
- [Phase 1: Core Platform (Weeks 2-3)](#phase-1-core-platform-weeks-2-3)
- [Phase 2: Invoice Processing (Weeks 4-5)](#phase-2-invoice-processing-weeks-4-5)
- [Phase 3: Generic OCR (Week 6)](#phase-3-generic-ocr-week-6)
- [Phase 4: Text Summarization (Week 7)](#phase-4-text-summarization-week-7)
- [Phase 5: Chat with PDF (RAG) (Weeks 8-9)](#phase-5-chat-with-pdf-rag-weeks-8-9)
- [Phase 6: Document Filling (Week 10)](#phase-6-document-filling-week-10)
- [Phase 7: Polish & Beta Launch (Weeks 11-12)](#phase-7-polish--beta-launch-weeks-11-12)

---

## Phase 0: Infrastructure Setup (Week 1)

**Goal:** Set up GCP project, development environment, Terraform infrastructure, and CI/CD pipelines.

### Task 0.1: Create Project Structure (2 hours)

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `terraform/.gitkeep`
- Create: `backend/.gitkeep`
- Create: `frontend/.gitkeep`
- Create: `docs/.gitkeep`
- Create: `tests/.gitkeep`

**Step 1: Initialize Git repository**

```bash
cd D:\docprocessing_ai
git init
```

Expected: `Initialized empty Git repository`

**Step 2: Create .gitignore**

Create file: `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env
.env.local
*.env

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Terraform
terraform/.terraform/
terraform/*.tfstate
terraform/*.tfstate.backup
terraform/.terraform.lock.hcl

# Node.js
node_modules/
npm-debug.log
yarn-error.log

# Build outputs
*.log
.DS_Store

# Secrets
*.pem
*.key
service-account-*.json
firebase-credentials.json

# Temporary files
tmp/
temp/
*.tmp
```

**Step 3: Create README.md**

Create file: `README.md`

```markdown
# Document AI SaaS Platform

AI-powered document processing platform for B2B customers.

## Features

- Invoice Processing with human-in-the-loop validation
- Generic OCR (Document AI + Gemini Vision)
- Document Summarization (Vertex AI)
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
├── frontend/          # React TypeScript app
├── terraform/         # Infrastructure as Code
├── docs/             # Documentation and plans
└── tests/            # Integration tests
```

## Setup Instructions

See [docs/setup.md](docs/setup.md) for detailed setup instructions.

## Development

See [docs/development.md](docs/development.md) for development workflow.

## Deployment

See [docs/deployment.md](docs/deployment.md) for deployment instructions.
```

**Step 4: Create directory structure**

```bash
mkdir -p backend/shared backend/api_gateway backend/workers backend/migrations backend/scripts
mkdir -p frontend/src frontend/public
mkdir -p terraform/modules terraform/environments
mkdir -p docs/plans
mkdir -p tests/backend tests/frontend
```

**Step 5: Commit**

```bash
git add .
git commit -m "chore: initialize project structure"
```

Expected: Files committed successfully

---

### Task 0.2: GCP Project Setup (1 hour)

**Files:**
- Create: `docs/gcp-setup.md`

**Step 1: Create GCP project**

```bash
# Set project ID (replace with your preferred ID)
export PROJECT_ID="docai-mvp-prod"
export REGION="europe-west1"
export ZONE="europe-west1-b"

# Create project
gcloud projects create $PROJECT_ID --name="Document AI SaaS MVP"

# Set as default project
gcloud config set project $PROJECT_ID
```

Expected: `Create in progress for [https://cloudresourcemanager.googleapis.com/v1/projects/docai-mvp-prod]`

**Step 2: Enable billing**

```bash
# List billing accounts
gcloud billing accounts list

# Link billing account (replace BILLING_ACCOUNT_ID)
gcloud billing projects link $PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

Expected: Billing account linked

**Step 3: Enable required APIs**

```bash
# Enable all required Google Cloud APIs
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  pubsub.googleapis.com \
  storage.googleapis.com \
  documentai.googleapis.com \
  aiplatform.googleapis.com \
  vision.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  compute.googleapis.com
```

Expected: `Operation "operations/..." finished successfully`

**Step 4: Set up gcloud defaults**

```bash
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE
```

**Step 5: Document setup**

Create file: `docs/gcp-setup.md`

```markdown
# GCP Setup

## Project Details

- **Project ID:** docai-mvp-prod
- **Region:** europe-west1 (Belgium)
- **Zone:** europe-west1-b

## Enabled APIs

- Cloud Run
- Cloud SQL Admin
- Pub/Sub
- Cloud Storage
- Document AI
- Vertex AI
- Vision AI
- Secret Manager
- Artifact Registry
- Cloud Build

## Environment Variables

```bash
export PROJECT_ID="docai-mvp-prod"
export REGION="europe-west1"
export ZONE="europe-west1-b"
```

## Verification

```bash
gcloud config list
gcloud services list --enabled
```
```

**Step 6: Commit**

```bash
git add docs/gcp-setup.md
git commit -m "docs: add GCP project setup documentation"
```

---

### Task 0.3: Terraform Setup (3 hours)

**Files:**
- Create: `terraform/main.tf`
- Create: `terraform/variables.tf`
- Create: `terraform/outputs.tf`
- Create: `terraform/terraform.tfvars`
- Create: `terraform/backend.tf`
- Create: `terraform/modules/cloud_run/main.tf`
- Create: `terraform/modules/cloud_sql/main.tf`
- Create: `terraform/modules/pubsub/main.tf`
- Create: `terraform/modules/storage/main.tf`

**Step 1: Create Terraform backend configuration**

Create file: `terraform/backend.tf`

```hcl
# Backend configuration for Terraform state
# State will be stored in Google Cloud Storage

terraform {
  backend "gcs" {
    bucket = "docai-mvp-terraform-state"
    prefix = "terraform/state"
  }
}
```

**Step 2: Create GCS bucket for Terraform state**

```bash
# Create bucket for Terraform state
gsutil mb -p $PROJECT_ID -l $REGION gs://docai-mvp-terraform-state

# Enable versioning
gsutil versioning set on gs://docai-mvp-terraform-state
```

Expected: Bucket created successfully

**Step 3: Create main Terraform configuration**

Create file: `terraform/main.tf`

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs (redundant with gcloud but ensures consistency)
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "documentai.googleapis.com",
    "aiplatform.googleapis.com",
    "vision.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "docai-images"
  description   = "Docker images for Document AI services"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}

# Cloud Storage buckets
module "storage" {
  source = "./modules/storage"

  project_id = var.project_id
  region     = var.region
  env        = var.environment
}

# Cloud SQL PostgreSQL
module "cloud_sql" {
  source = "./modules/cloud_sql"

  project_id    = var.project_id
  region        = var.region
  database_tier = var.database_tier
  env           = var.environment
}

# Pub/Sub topics and subscriptions
module "pubsub" {
  source = "./modules/pubsub"

  project_id = var.project_id
}

# Service accounts for Cloud Run services
resource "google_service_account" "api_gateway" {
  account_id   = "api-gateway"
  display_name = "API Gateway Service Account"
}

resource "google_service_account" "workers" {
  account_id   = "ai-workers"
  display_name = "AI Workers Service Account"
}

# IAM bindings
resource "google_project_iam_member" "api_gateway_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.api_gateway.email}"
}

resource "google_project_iam_member" "api_gateway_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.api_gateway.email}"
}

resource "google_project_iam_member" "workers_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.workers.email}"
}

resource "google_project_iam_member" "workers_documentai" {
  project = var.project_id
  role    = "roles/documentai.apiUser"
  member  = "serviceAccount:${google_service_account.workers.email}"
}

resource "google_project_iam_member" "workers_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.workers.email}"
}

resource "google_project_iam_member" "workers_vision" {
  project = var.project_id
  role    = "roles/cloudvision.user"
  member  = "serviceAccount:${google_service_account.workers.email}"
}

resource "google_project_iam_member" "workers_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.workers.email}"
}
```

**Step 4: Create variables file**

Create file: `terraform/variables.tf`

```hcl
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "database_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}
```

**Step 5: Create outputs file**

Create file: `terraform/outputs.tf`

```hcl
output "artifact_registry_url" {
  description = "Artifact Registry URL"
  value       = google_artifact_registry_repository.docker_repo.name
}

output "api_gateway_service_account" {
  description = "API Gateway service account email"
  value       = google_service_account.api_gateway.email
}

output "workers_service_account" {
  description = "Workers service account email"
  value       = google_service_account.workers.email
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = module.cloud_sql.connection_name
}

output "storage_buckets" {
  description = "GCS bucket names"
  value       = module.storage.bucket_names
}
```

**Step 6: Create tfvars file**

Create file: `terraform/terraform.tfvars`

```hcl
project_id    = "docai-mvp-prod"
region        = "europe-west1"
environment   = "prod"
database_tier = "db-f1-micro"
```

**Step 7: Create storage module**

Create file: `terraform/modules/storage/main.tf`

```hcl
variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "env" {
  type = string
}

resource "google_storage_bucket" "uploads" {
  name          = "${var.project_id}-uploads-${var.env}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "processed" {
  name          = "${var.project_id}-processed-${var.env}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "temp" {
  name          = "${var.project_id}-temp-${var.env}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }
}

output "bucket_names" {
  value = {
    uploads   = google_storage_bucket.uploads.name
    processed = google_storage_bucket.processed.name
    temp      = google_storage_bucket.temp.name
  }
}
```

**Step 8: Create Cloud SQL module**

Create file: `terraform/modules/cloud_sql/main.tf`

```hcl
variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "database_tier" {
  type = string
}

variable "env" {
  type = string
}

resource "random_id" "db_suffix" {
  byte_length = 4
}

resource "google_sql_database_instance" "postgres" {
  name             = "docai-postgres-${var.env}-${random_id.db_suffix.hex}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = var.database_tier

    ip_configuration {
      ipv4_enabled = false
      require_ssl  = true

      # Allow Cloud Run services to connect via private IP
      private_network = null
    }

    backup_configuration {
      enabled            = true
      start_time         = "03:00"
      point_in_time_recovery_enabled = false
      backup_retention_settings {
        retained_backups = 7
      }
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  deletion_protection = true
}

resource "google_sql_database" "main" {
  name     = "docai"
  instance = google_sql_database_instance.postgres.name
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "google_sql_user" "main" {
  name     = "docai"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# Store database password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "database-password"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

output "connection_name" {
  value = google_sql_database_instance.postgres.connection_name
}

output "database_name" {
  value = google_sql_database.main.name
}

output "database_user" {
  value = google_sql_user.main.name
}
```

**Step 9: Create Pub/Sub module**

Create file: `terraform/modules/pubsub/main.tf`

```hcl
variable "project_id" {
  type = string
}

# Topics
resource "google_pubsub_topic" "invoice_processing" {
  name = "invoice-processing"
}

resource "google_pubsub_topic" "ocr_processing" {
  name = "ocr-processing"
}

resource "google_pubsub_topic" "summarization_processing" {
  name = "summarization-processing"
}

resource "google_pubsub_topic" "rag_ingestion" {
  name = "rag-ingestion"
}

resource "google_pubsub_topic" "document_filling" {
  name = "document-filling"
}

resource "google_pubsub_topic" "processing_failures" {
  name = "processing-failures"
}

# Dead letter topic
resource "google_pubsub_topic" "dead_letter" {
  name = "dead-letter-topic"
}

# Subscriptions (will be created by Cloud Run services with push endpoints)
# Placeholder for future push subscriptions

output "topic_names" {
  value = {
    invoice_processing       = google_pubsub_topic.invoice_processing.name
    ocr_processing          = google_pubsub_topic.ocr_processing.name
    summarization_processing = google_pubsub_topic.summarization_processing.name
    rag_ingestion           = google_pubsub_topic.rag_ingestion.name
    document_filling        = google_pubsub_topic.document_filling.name
    processing_failures     = google_pubsub_topic.processing_failures.name
    dead_letter             = google_pubsub_topic.dead_letter.name
  }
}
```

**Step 10: Initialize Terraform**

```bash
cd terraform
terraform init
```

Expected: `Terraform has been successfully initialized!`

**Step 11: Validate Terraform configuration**

```bash
terraform validate
```

Expected: `Success! The configuration is valid.`

**Step 12: Plan infrastructure**

```bash
terraform plan -out=tfplan
```

Expected: Plan shows resources to be created

**Step 13: Apply infrastructure**

```bash
terraform apply tfplan
```

Expected: Resources created successfully

**Step 14: Commit**

```bash
cd ..
git add terraform/
git commit -m "feat: add Terraform infrastructure configuration"
```

---

### Task 0.4: Firebase Setup (1 hour)

**Files:**
- Create: `docs/firebase-setup.md`

**Step 1: Create Firebase project**

1. Go to https://console.firebase.google.com/
2. Click "Add project"
3. Select existing GCP project: `docai-mvp-prod`
4. Enable Google Analytics (optional)
5. Click "Continue"

Expected: Firebase project created

**Step 2: Enable Firebase Authentication**

1. In Firebase Console, go to "Build" > "Authentication"
2. Click "Get started"
3. Enable "Email/Password" sign-in method
4. Click "Save"

Expected: Email/Password authentication enabled

**Step 3: Create web app in Firebase**

1. In Firebase Console, click project settings (gear icon)
2. Click "Add app" > Web
3. App nickname: "Document AI Web App"
4. Click "Register app"
5. Copy Firebase configuration object

Expected: Web app registered, config available

**Step 4: Document Firebase configuration**

Create file: `docs/firebase-setup.md`

```markdown
# Firebase Setup

## Project

- **Firebase Project:** docai-mvp-prod
- **Authentication:** Email/Password enabled

## Web App Configuration

Add this to frontend environment variables:

```javascript
// Firebase configuration (public - safe to commit)
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "docai-mvp-prod.firebaseapp.com",
  projectId: "docai-mvp-prod",
  storageBucket: "docai-mvp-prod.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};
```

## Service Account for Backend

1. Go to Project Settings > Service Accounts
2. Click "Generate new private key"
3. Save as `firebase-credentials.json` (DO NOT COMMIT)
4. Upload to Secret Manager:

```bash
gcloud secrets create firebase-credentials \
  --data-file=firebase-credentials.json \
  --replication-policy=automatic
```

## Verification

Test authentication in Firebase Console under "Authentication" > "Users"
```

**Step 5: Generate and store Firebase service account**

1. In Firebase Console: Project Settings > Service Accounts
2. Click "Generate new private key"
3. Save to `firebase-credentials.json` (local only)
4. Upload to Secret Manager:

```bash
gcloud secrets create firebase-credentials \
  --data-file=firebase-credentials.json \
  --replication-policy=automatic
```

Expected: Secret created in Secret Manager

**Step 6: Delete local credentials file**

```bash
rm firebase-credentials.json
```

**Step 7: Commit documentation**

```bash
git add docs/firebase-setup.md
git commit -m "docs: add Firebase setup documentation"
```

---

### Task 0.5: Local Development Environment (2 hours)

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.python-version`
- Create: `.env.example`
- Create: `docs/development.md`

**Step 1: Create Python version file**

Create file: `backend/.python-version`

```
3.11.7
```

**Step 2: Create shared requirements**

Create file: `backend/requirements.txt`

```txt
# Core FastAPI
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
pgvector==0.2.3

# Google Cloud
google-cloud-storage==2.10.0
google-cloud-pubsub==2.18.4
google-cloud-documentai==2.24.0
google-cloud-aiplatform==1.38.0
google-cloud-vision==3.4.5
google-cloud-secret-manager==2.16.4

# Firebase
firebase-admin==6.3.0

# AI/ML
langchain==0.0.340
langchain-google-vertexai==0.0.6

# PDF processing
pypdfform==1.4.30
PyPDF2==3.0.1

# Utilities
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
httpx==0.25.2

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
ruff==0.1.6
mypy==1.7.1
```

**Step 3: Create environment template**

Create file: `.env.example`

```bash
# GCP Configuration
PROJECT_ID=docai-mvp-prod
REGION=europe-west1
ENVIRONMENT=dev

# Database (for local development)
DATABASE_URL=postgresql://docai:password@localhost:5432/docai
CLOUD_SQL_CONNECTION_NAME=docai-mvp-prod:europe-west1:docai-postgres-prod-xxxxx

# Storage
GCS_BUCKET_UPLOADS=docai-mvp-prod-uploads-prod
GCS_BUCKET_PROCESSED=docai-mvp-prod-processed-prod
GCS_BUCKET_TEMP=docai-mvp-prod-temp-prod

# Pub/Sub Topics
PUBSUB_TOPIC_INVOICE=invoice-processing
PUBSUB_TOPIC_OCR=ocr-processing
PUBSUB_TOPIC_SUMMARY=summarization-processing
PUBSUB_TOPIC_RAG_INGEST=rag-ingestion
PUBSUB_TOPIC_DOCFILL=document-filling

# Vertex AI
VERTEX_AI_LOCATION=us-central1

# Firebase (backend service account handled via Secret Manager)
FIREBASE_PROJECT_ID=docai-mvp-prod

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Security
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
```

**Step 4: Create development documentation**

Create file: `docs/development.md`

```markdown
# Development Guide

## Prerequisites

- Python 3.11+
- Docker Desktop
- gcloud CLI
- Node.js 18+ (for frontend)
- Git

## Backend Setup

### 1. Create virtual environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
# Copy template
cp ../.env.example .env

# Edit .env with your values
```

### 4. Authenticate with GCP

```bash
gcloud auth application-default login
gcloud config set project docai-mvp-prod
```

### 5. Run database migrations (after Phase 1)

```bash
cd migrations
alembic upgrade head
```

### 6. Run API Gateway locally

```bash
cd api_gateway
uvicorn main:app --reload --port 8000
```

Access: http://localhost:8000/docs

## Frontend Setup

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Configure environment

Create `.env.local`:

```bash
VITE_API_URL=http://localhost:8000/v1
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=docai-mvp-prod.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=docai-mvp-prod
```

### 3. Run development server

```bash
npm run dev
```

Access: http://localhost:5173

## Testing

### Backend tests

```bash
cd backend
pytest tests/ -v
```

### Frontend tests

```bash
cd frontend
npm run test
```

## Code Quality

### Format code

```bash
cd backend
black .
ruff check . --fix
```

### Type checking

```bash
mypy backend/
```

## Docker Development

### Build images locally

```bash
# API Gateway
docker build -t docai-api-gateway:local backend/api_gateway/

# Workers
docker build -t docai-invoice-worker:local backend/workers/invoice_worker/
```

### Run with Docker Compose (optional)

```bash
docker-compose up
```
```

**Step 5: Set up Python virtual environment**

```bash
cd backend
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Expected: Virtual environment created and dependencies installed

**Step 6: Verify installation**

```bash
python -c "import fastapi; print(fastapi.__version__)"
```

Expected: `0.104.1`

**Step 7: Commit**

```bash
cd ..
git add backend/requirements.txt backend/.python-version .env.example docs/development.md
git commit -m "feat: add backend dependencies and development environment"
```

---

### Task 0.6: CI/CD Pipeline (2 hours)

**Files:**
- Create: `.github/workflows/backend-ci.yml`
- Create: `.github/workflows/deploy.yml`

**Step 1: Create backend CI workflow**

Create file: `.github/workflows/backend-ci.yml`

```yaml
name: Backend CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'backend/**'
  pull_request:
    branches: [main, develop]
    paths:
      - 'backend/**'

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements.txt') }}

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --cov=. --cov-report=xml

      - name: Code quality - Black
        run: |
          cd backend
          pip install black
          black --check .

      - name: Code quality - Ruff
        run: |
          cd backend
          pip install ruff
          ruff check .

      - name: Type checking - MyPy
        run: |
          cd backend
          pip install mypy
          mypy --install-types --non-interactive . || true

  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1

      - name: Configure Docker for Artifact Registry
        run: |
          gcloud auth configure-docker europe-west1-docker.pkg.dev

      - name: Build and push API Gateway image
        run: |
          cd backend/api_gateway
          docker build -t europe-west1-docker.pkg.dev/docai-mvp-prod/docai-images/api-gateway:${{ github.sha }} .
          docker push europe-west1-docker.pkg.dev/docai-mvp-prod/docai-images/api-gateway:${{ github.sha }}
```

**Step 2: Create deployment workflow**

Create file: `.github/workflows/deploy.yml`

```yaml
name: Deploy to Cloud Run

on:
  workflow_dispatch:
    inputs:
      service:
        description: 'Service to deploy'
        required: true
        type: choice
        options:
          - api-gateway
          - invoice-worker
          - ocr-worker
          - summarizer-worker
          - rag-ingest-worker
          - rag-query-worker
          - docfill-worker
      environment:
        description: 'Environment'
        required: true
        type: choice
        options:
          - prod
          - staging

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ${{ inputs.service }} \
            --image europe-west1-docker.pkg.dev/docai-mvp-prod/docai-images/${{ inputs.service }}:${{ github.sha }} \
            --region europe-west1 \
            --platform managed \
            --allow-unauthenticated
```

**Step 3: Set up GitHub secrets**

1. Create GCP service account for GitHub Actions:

```bash
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Service Account"

gcloud projects add-iam-policy-binding docai-mvp-prod \
  --member="serviceAccount:github-actions@docai-mvp-prod.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding docai-mvp-prod \
  --member="serviceAccount:github-actions@docai-mvp-prod.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@docai-mvp-prod.iam.gserviceaccount.com
```

2. Add to GitHub repository secrets:
   - Go to repository Settings > Secrets and variables > Actions
   - Add new secret: `GCP_SA_KEY` = contents of `github-actions-key.json`

**Step 4: Delete local service account key**

```bash
rm github-actions-key.json
```

**Step 5: Commit**

```bash
git add .github/
git commit -m "ci: add GitHub Actions workflows for CI/CD"
```

---

### Task 0.7: Database Schema & Migrations (2 hours)

**Files:**
- Create: `backend/shared/database.py`
- Create: `backend/shared/models.py`
- Create: `backend/migrations/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/versions/001_initial_schema.py`

**Step 1: Create database connection module**

Create file: `backend/shared/database.py`

```python
"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
from google.cloud.sql.connector import Connector

# Base class for models
Base = declarative_base()


def get_database_url() -> str:
    """Get database URL based on environment."""
    # Local development
    if os.getenv("ENVIRONMENT") == "dev":
        return os.getenv("DATABASE_URL", "postgresql://docai:password@localhost:5432/docai")

    # Production: use Cloud SQL connector
    connector = Connector()

    def getconn():
        conn = connector.connect(
            os.getenv("CLOUD_SQL_CONNECTION_NAME"),
            "pg8000",
            user=os.getenv("DB_USER", "docai"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME", "docai"),
        )
        return conn

    # Create engine with Cloud SQL connector
    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        poolclass=NullPool,
    )
    return engine


def create_database_engine():
    """Create SQLAlchemy engine."""
    if os.getenv("ENVIRONMENT") == "dev":
        database_url = get_database_url()
        return create_engine(database_url, echo=True)
    else:
        return get_database_url()


# Create engine
engine = create_database_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 2: Create database models**

Create file: `backend/shared/models.py`

```python
"""SQLAlchemy database models."""

from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, DateTime, Date,
    Text, DECIMAL, ForeignKey, Index, TIMESTAMP, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

from .database import Base


class Tenant(Base):
    """Multi-tenant organization."""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """User account."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(255), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    documents = relationship("Document", back_populates="user")

    # Indexes
    __table_args__ = (
        Index("idx_user_tenant_email", "tenant_id", "email", unique=True),
    )


class Document(Base):
    """Uploaded document."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Metadata
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500))
    mime_type = Column(String(100))
    file_size_bytes = Column(BigInteger)
    document_type = Column(String(50))

    # Storage
    gcs_path = Column(Text, nullable=False)
    gcs_processed_path = Column(Text)

    # Processing status
    status = Column(String(50), default="uploaded")
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    error_message = Column(Text)

    # AI processing flags
    ocr_completed = Column(Boolean, default=False)
    invoice_parsed = Column(Boolean, default=False)
    summarized = Column(Boolean, default=False)
    rag_indexed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    user = relationship("User", back_populates="documents")
    invoice_data = relationship("InvoiceData", back_populates="document", uselist=False)
    ocr_result = relationship("OCRResult", back_populates="document", uselist=False)
    summary = relationship("DocumentSummary", back_populates="document", uselist=False)
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_tenant_documents", "tenant_id", "created_at"),
        Index("idx_user_documents", "user_id", "created_at"),
        Index("idx_document_status", "status"),
    )


class InvoiceData(Base):
    """Extracted invoice data."""
    __tablename__ = "invoice_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Vendor information
    vendor_name = Column(String(500))
    vendor_address = Column(Text)
    vendor_tax_id = Column(String(100))

    # Invoice details
    invoice_number = Column(String(100))
    invoice_date = Column(Date)
    due_date = Column(Date)

    # Amounts
    subtotal = Column(DECIMAL(15, 2))
    tax_amount = Column(DECIMAL(15, 2))
    total_amount = Column(DECIMAL(15, 2))
    currency = Column(String(3), default="EUR")

    # Line items
    line_items = Column(JSONB, default=[])

    # Raw extraction
    raw_extraction = Column(JSONB)

    # Human validation
    is_validated = Column(Boolean, default=False)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    validated_at = Column(DateTime)
    validation_notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="invoice_data")

    # Indexes
    __table_args__ = (
        Index("idx_tenant_invoices", "tenant_id", "invoice_date"),
        Index("idx_invoice_validation", "is_validated"),
    )


class OCRResult(Base):
    """OCR text extraction result."""
    __tablename__ = "ocr_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    extracted_text = Column(Text, nullable=False)
    confidence_score = Column(DECIMAL(5, 4))
    page_count = Column(Integer)
    ocr_method = Column(String(50))

    layout_data = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="ocr_result")


class DocumentSummary(Base):
    """Document summary."""
    __tablename__ = "document_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    summary = Column(Text, nullable=False)
    model_used = Column(String(100))
    word_count = Column(Integer)
    key_points = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="summary")


class DocumentChunk(Base):
    """Document chunks for RAG."""
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer)

    # Vector embedding (768 dimensions for textembedding-gecko)
    embedding = Column(Vector(768))

    metadata = Column(JSONB, default={})

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    # Indexes
    __table_args__ = (
        Index("idx_tenant_chunks", "tenant_id"),
        Index("idx_document_chunks", "document_id", "chunk_index"),
    )


class AuditLog(Base):
    """Audit log for compliance."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))

    action = Column(String(100), nullable=False)
    details = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_audit_tenant", "tenant_id", "created_at"),
        Index("idx_audit_user", "user_id", "created_at"),
    )
```

**Step 3: Initialize Alembic**

```bash
cd backend/migrations
pip install alembic
alembic init .
```

**Step 4: Configure Alembic**

Edit `backend/migrations/alembic.ini`:

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = postgresql://docai:password@localhost:5432/docai

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**Step 5: Configure Alembic environment**

Create file: `backend/migrations/env.py`

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared.database import Base
from shared.models import *  # Import all models

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 6: Create initial migration**

```bash
cd backend/migrations
alembic revision -m "initial schema"
```

**Step 7: Edit generated migration file**

Edit the generated file in `backend/migrations/versions/xxx_initial_schema.py`:

```python
"""initial schema

Revision ID: xxx
Revises:
Create Date: 2025-11-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers
revision = 'xxx'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('subdomain', sa.String(100), unique=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('settings', postgresql.JSONB, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('firebase_uid', sa.String(255), unique=True, nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('role', sa.String(50), server_default='user'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime()),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
    )
    op.create_index('idx_user_tenant_email', 'users', ['tenant_id', 'email'], unique=True)

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500)),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('file_size_bytes', sa.BigInteger()),
        sa.Column('document_type', sa.String(50)),
        sa.Column('gcs_path', sa.Text(), nullable=False),
        sa.Column('gcs_processed_path', sa.Text()),
        sa.Column('status', sa.String(50), server_default='uploaded'),
        sa.Column('processing_started_at', sa.DateTime()),
        sa.Column('processing_completed_at', sa.DateTime()),
        sa.Column('error_message', sa.Text()),
        sa.Column('ocr_completed', sa.Boolean(), server_default='false'),
        sa.Column('invoice_parsed', sa.Boolean(), server_default='false'),
        sa.Column('summarized', sa.Boolean(), server_default='false'),
        sa.Column('rag_indexed', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_tenant_documents', 'documents', ['tenant_id', 'created_at'])
    op.create_index('idx_user_documents', 'documents', ['user_id', 'created_at'])
    op.create_index('idx_document_status', 'documents', ['status'])

    # Create invoice_data table
    op.create_table(
        'invoice_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vendor_name', sa.String(500)),
        sa.Column('vendor_address', sa.Text()),
        sa.Column('vendor_tax_id', sa.String(100)),
        sa.Column('invoice_number', sa.String(100)),
        sa.Column('invoice_date', sa.Date()),
        sa.Column('due_date', sa.Date()),
        sa.Column('subtotal', sa.DECIMAL(15, 2)),
        sa.Column('tax_amount', sa.DECIMAL(15, 2)),
        sa.Column('total_amount', sa.DECIMAL(15, 2)),
        sa.Column('currency', sa.String(3), server_default='EUR'),
        sa.Column('line_items', postgresql.JSONB, server_default='[]'),
        sa.Column('raw_extraction', postgresql.JSONB),
        sa.Column('is_validated', sa.Boolean(), server_default='false'),
        sa.Column('validated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('validated_at', sa.DateTime()),
        sa.Column('validation_notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_tenant_invoices', 'invoice_data', ['tenant_id', 'invoice_date'])
    op.create_index('idx_invoice_validation', 'invoice_data', ['is_validated'])

    # Create ocr_results table
    op.create_table(
        'ocr_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.DECIMAL(5, 4)),
        sa.Column('page_count', sa.Integer()),
        sa.Column('ocr_method', sa.String(50)),
        sa.Column('layout_data', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create document_summaries table
    op.create_table(
        'document_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('model_used', sa.String(100)),
        sa.Column('word_count', sa.Integer()),
        sa.Column('key_points', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create document_chunks table with vector column
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer()),
        sa.Column('embedding', Vector(768)),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_tenant_chunks', 'document_chunks', ['tenant_id'])
    op.create_index('idx_document_chunks', 'document_chunks', ['document_id', 'chunk_index'])

    # Create HNSW index for vector similarity search
    op.execute('CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops)')

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id')),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('details', postgresql.JSONB),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('user_agent', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_audit_tenant', 'audit_logs', ['tenant_id', 'created_at'])
    op.create_index('idx_audit_user', 'audit_logs', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('document_chunks')
    op.drop_table('document_summaries')
    op.drop_table('ocr_results')
    op.drop_table('invoice_data')
    op.drop_table('documents')
    op.drop_table('users')
    op.drop_table('tenants')
    op.execute('DROP EXTENSION IF EXISTS vector')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
```

**Step 8: Commit**

```bash
cd ../..
git add backend/shared/ backend/migrations/
git commit -m "feat: add database models and Alembic migrations"
```

---

## Phase 0 Complete ✓

**Summary:** Infrastructure setup complete
- GCP project configured
- Terraform infrastructure deployed
- Firebase authentication enabled
- Development environment ready
- CI/CD pipelines configured
- Database schema designed

**Next:** Phase 1 - Core Platform (Weeks 2-3)

---

## Phase 1: Core Platform (Weeks 2-3)

**Goal:** Build API Gateway with authentication, file upload, and basic document management.

### Task 1.1: API Gateway Project Setup (2 hours)

**Files:**
- Create: `backend/api_gateway/Dockerfile`
- Create: `backend/api_gateway/main.py`
- Create: `backend/api_gateway/config.py`
- Create: `backend/api_gateway/dependencies.py`
- Create: `backend/shared/config.py`
- Create: `backend/shared/auth.py`

**Step 1: Create shared configuration**

Create file: `backend/shared/config.py`

```python
"""Shared configuration management."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # GCP
    project_id: str = "docai-mvp-prod"
    region: str = "europe-west1"
    environment: str = "dev"

    # Database
    database_url: str = "postgresql://docai:password@localhost:5432/docai"
    cloud_sql_connection_name: str = ""
    db_user: str = "docai"
    db_password: str = ""
    db_name: str = "docai"

    # Storage
    gcs_bucket_uploads: str = "docai-mvp-prod-uploads-prod"
    gcs_bucket_processed: str = "docai-mvp-prod-processed-prod"
    gcs_bucket_temp: str = "docai-mvp-prod-temp-prod"

    # Pub/Sub
    pubsub_topic_invoice: str = "invoice-processing"
    pubsub_topic_ocr: str = "ocr-processing"
    pubsub_topic_summary: str = "summarization-processing"
    pubsub_topic_rag_ingest: str = "rag-ingestion"
    pubsub_topic_docfill: str = "document-filling"

    # Vertex AI
    vertex_ai_location: str = "us-central1"

    # Firebase
    firebase_project_id: str = "docai-mvp-prod"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # Security
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

**Step 2: Create Firebase auth utility**

Create file: `backend/shared/auth.py`

```python
"""Firebase authentication utilities."""

from firebase_admin import auth, credentials, initialize_app
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import secretmanager
import json
import os

from .config import get_settings

settings = get_settings()

# Initialize Firebase Admin SDK
def init_firebase():
    """Initialize Firebase Admin SDK."""
    try:
        if settings.environment == "dev":
            # Local development: use service account file
            cred = credentials.ApplicationDefault()
        else:
            # Production: get credentials from Secret Manager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{settings.project_id}/secrets/firebase-credentials/versions/latest"
            response = client.access_secret_version(request={"name": name})
            cred_json = json.loads(response.payload.data.decode("UTF-8"))
            cred = credentials.Certificate(cred_json)

        initialize_app(cred)
    except Exception as e:
        print(f"Firebase initialization error: {e}")
        # Already initialized
        pass


# Security scheme
security = HTTPBearer()


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """Verify Firebase ID token and return user info."""
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Authentication token has expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


def get_tenant_id_from_token(token_data: dict) -> str:
    """Extract tenant_id from Firebase token custom claims."""
    tenant_id = token_data.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail="No tenant association found. Please contact support."
        )
    return tenant_id


def get_user_role_from_token(token_data: dict) -> str:
    """Extract user role from Firebase token custom claims."""
    return token_data.get("role", "user")
```

**Step 3: Create API Gateway main application**

Create file: `backend/api_gateway/main.py`

```python
"""FastAPI API Gateway for Document AI SaaS."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from backend.shared.auth import init_firebase
from backend.shared.config import get_settings
from .routes import auth, documents

settings = get_settings()

# Initialize Firebase
init_firebase()

# Create FastAPI app
app = FastAPI(
    title="Document AI API",
    description="AI-powered document processing platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api-gateway"}


# Include routers
app.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/v1/documents", tags=["Documents"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
```

**Step 4: Create Dockerfile for API Gateway**

Create file: `backend/api_gateway/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code
COPY ../shared /app/backend/shared

# Copy API Gateway code
COPY . /app/backend/api_gateway

WORKDIR /app/backend/api_gateway

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 5: Create .dockerignore**

Create file: `backend/.dockerignore`

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv/
*.env
.git
.gitignore
*.md
tests/
.pytest_cache/
```

**Step 6: Commit**

```bash
git add backend/api_gateway/ backend/shared/config.py backend/shared/auth.py
git commit -m "feat: add API Gateway skeleton with Firebase auth"
```

---

### Task 1.2: Authentication Endpoints (3 hours)

**Files:**
- Create: `backend/api_gateway/routes/auth.py`
- Create: `backend/shared/schemas.py`

**Step 1: Create Pydantic schemas**

Create file: `backend/shared/schemas.py`

```python
"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    tenant_name: str = Field(..., min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: UUID
    tenant_id: UUID
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Document schemas
class DocumentUpload(BaseModel):
    document_type: str = Field(..., pattern="^(invoice|contract|id|generic)$")


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    document_type: str
    status: str
    gcs_path: str
    created_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

**Step 2: Create authentication routes**

Create file: `backend/api_gateway/routes/auth.py`

```python
"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from firebase_admin import auth
import uuid

from backend.shared.database import get_db
from backend.shared.models import User, Tenant
from backend.shared.schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from backend.shared.auth import verify_firebase_token

router = APIRouter()


@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create new user account with tenant.

    1. Create Firebase user
    2. Create tenant in database
    3. Create user in database linked to tenant
    4. Set custom claims on Firebase user (tenant_id, role)
    5. Return token and user info
    """
    try:
        # Create Firebase user
        firebase_user = auth.create_user(
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.full_name,
        )

        # Create tenant
        tenant = Tenant(
            name=user_data.tenant_name,
            subdomain=user_data.tenant_name.lower().replace(" ", "-"),
        )
        db.add(tenant)
        db.flush()  # Get tenant.id

        # Create user
        user = User(
            firebase_uid=firebase_user.uid,
            tenant_id=tenant.id,
            email=user_data.email,
            full_name=user_data.full_name,
            role="admin",  # First user is admin
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Set custom claims
        auth.set_custom_user_claims(firebase_user.uid, {
            "tenant_id": str(tenant.id),
            "role": "admin",
        })

        # Generate custom token
        custom_token = auth.create_custom_token(firebase_user.uid)

        return TokenResponse(
            access_token=custom_token.decode("utf-8"),
            user=UserResponse.from_orm(user),
        )

    except auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Email already registered")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user (client-side Firebase Auth handles actual authentication).
    This endpoint is mainly for documentation.

    In practice, the frontend will:
    1. Call Firebase signInWithEmailAndPassword()
    2. Get ID token from Firebase
    3. Send ID token to backend in Authorization header
    """
    # This is a placeholder - actual authentication happens client-side
    # The frontend will get the ID token from Firebase SDK
    raise HTTPException(
        status_code=501,
        detail="Login is handled client-side by Firebase SDK. Use the ID token in Authorization header."
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    user = db.query(User).filter(User.firebase_uid == token_data["uid"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.from_orm(user)


@router.post("/refresh")
async def refresh_token(token_data: dict = Depends(verify_firebase_token)):
    """Refresh authentication token."""
    # Generate new custom token
    new_token = auth.create_custom_token(token_data["uid"])

    return {
        "access_token": new_token.decode("utf-8"),
        "token_type": "bearer",
    }
```

**Step 3: Test authentication locally**

Create file: `tests/backend/test_auth.py`

```python
"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.api_gateway.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_signup_success():
    """Test user signup."""
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "tenant_name": "Test Company"
        }
    )

    # Should return token and user info
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"


def test_signup_duplicate_email():
    """Test signup with existing email."""
    # First signup
    client.post(
        "/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "SecurePass123!",
            "full_name": "User One",
            "tenant_name": "Company One"
        }
    )

    # Second signup with same email
    response = client.post(
        "/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "DifferentPass456!",
            "full_name": "User Two",
            "tenant_name": "Company Two"
        }
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/backend/test_auth.py -v
```

Expected: Tests pass (or setup issues to fix)

**Step 5: Commit**

```bash
git add backend/api_gateway/routes/auth.py backend/shared/schemas.py tests/backend/test_auth.py
git commit -m "feat: add authentication endpoints (signup, login, me)"
```

---

*Due to length constraints, I'll continue this plan in a structured format. The plan continues with:*

- **Task 1.3:** Document upload endpoint with GCS integration
- **Task 1.4:** Document list/retrieve endpoints
- **Task 1.5:** Pub/Sub publisher setup
- **Task 1.6:** React frontend setup with Firebase Auth
- **Task 1.7:** Deploy API Gateway to Cloud Run

**Then Phase 2-7 following similar detailed patterns with:**
- Exact file paths
- Complete code
- Step-by-step commands
- Testing procedures
- Commit messages

**Would you like me to:**
1. Continue with full detailed tasks for all phases in separate files?
2. Compress remaining phases into task summaries?
3. Focus on specific phases you want detailed first?

---

## Execution Handoff

**Plan saved to:** `docs/plans/2025-11-17-document-ai-saas-mvp.md`

**Two execution options:**

**1. Subagent-Driven Development (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration with quality gates

**2. Parallel Session (separate)** - Open new session in this directory, use `superpowers:executing-plans` skill, batch execution with review checkpoints

**Which approach would you prefer?**
