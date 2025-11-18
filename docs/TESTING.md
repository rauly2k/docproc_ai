# Testing Guide - DocProc AI Platform

Complete step-by-step guide to test all components of the DocProc AI platform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Backend Testing](#backend-testing)
4. [Frontend Testing](#frontend-testing)
5. [Infrastructure Testing](#infrastructure-testing)
6. [Integration Testing](#integration-testing)
7. [Manual End-to-End Testing](#manual-end-to-end-testing)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

```bash
# Check versions
python --version    # 3.11+
node --version      # 18+
docker --version    # 20+
gcloud --version    # Latest
terraform --version # 1.5+
```

### Install Missing Tools

**Python 3.11:**
```bash
# macOS
brew install python@3.11

# Ubuntu
sudo apt update
sudo apt install python3.11 python3.11-venv

# Windows
# Download from python.org
```

**Node.js 18:**
```bash
# macOS
brew install node@18

# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows
# Download from nodejs.org
```

**Docker:**
```bash
# macOS
brew install --cask docker

# Ubuntu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Windows
# Download Docker Desktop
```

**Google Cloud SDK:**
```bash
# macOS
brew install google-cloud-sdk

# Ubuntu
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt-get update && sudo apt-get install google-cloud-sdk

# Windows
# Download from cloud.google.com/sdk
```

**Terraform:**
```bash
# macOS
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Ubuntu
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/rauly2k/docproc_ai.git
cd docproc_ai
```

### 2. Set Up PostgreSQL with pgvector

**Option A: Using Docker (Recommended)**

```bash
# Start PostgreSQL 15 with pgvector
docker run -d \
  --name docproc-postgres \
  -e POSTGRES_DB=docproc_ai_dev \
  -e POSTGRES_USER=docproc_user \
  -e POSTGRES_PASSWORD=dev_password_12345 \
  -p 5432:5432 \
  pgvector/pgvector:pg15

# Verify it's running
docker ps | grep docproc-postgres
```

**Option B: Local PostgreSQL**

```bash
# Install PostgreSQL 15
brew install postgresql@15  # macOS
sudo apt install postgresql-15 postgresql-contrib  # Ubuntu

# Start PostgreSQL
brew services start postgresql@15  # macOS
sudo systemctl start postgresql  # Ubuntu

# Create database
psql postgres
CREATE DATABASE docproc_ai_dev;
CREATE USER docproc_user WITH PASSWORD 'dev_password_12345';
GRANT ALL PRIVILEGES ON DATABASE docproc_ai_dev TO docproc_user;
\q

# Install pgvector extension
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install  # May need sudo

# Enable extension
psql -d docproc_ai_dev
CREATE EXTENSION vector;
\q
```

### 3. Configure Environment Variables

**Backend:**

```bash
cd backend

# Create .env file
cat > .env << 'EOF'
# Application
ENVIRONMENT=dev
DEBUG=true

# GCP Configuration
PROJECT_ID=docai-mvp-prod
REGION=europe-west1

# Database
DATABASE_URL=postgresql://docproc_user:dev_password_12345@localhost:5432/docproc_ai_dev
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Firebase (get from Firebase Console)
FIREBASE_CREDENTIALS_PATH=./firebase-adminsdk.json
FIREBASE_PROJECT_ID=your-firebase-project-id

# Cloud Storage (will create local buckets for testing)
GCS_BUCKET_UPLOADS=docai-uploads-dev
GCS_BUCKET_PROCESSED=docai-processed-dev

# Vertex AI
VERTEX_AI_LOCATION=us-central1

# Pub/Sub Topics
PUBSUB_TOPIC_INVOICE=docai-invoice-processing-dev
PUBSUB_TOPIC_OCR=docai-ocr-processing-dev
PUBSUB_TOPIC_SUMMARIZATION=docai-summarization-dev
PUBSUB_TOPIC_RAG_INGESTION=docai-rag-ingestion-dev
PUBSUB_TOPIC_DOCUMENT_FILLING=docai-document-filling-dev
EOF

# Download Firebase credentials
# 1. Go to Firebase Console > Project Settings > Service Accounts
# 2. Click "Generate New Private Key"
# 3. Save as backend/firebase-adminsdk.json
```

**Frontend:**

```bash
cd ../frontend

# Create .env file
cat > .env << 'EOF'
VITE_API_BASE_URL=http://localhost:8000/v1

# Firebase Configuration (get from Firebase Console > Project Settings > Web App)
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
EOF
```

### 4. Set Up GCP Authentication (for local testing)

```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project docai-mvp-prod

# Set application default credentials
gcloud auth application-default login
```

---

## Backend Testing

### 1. Install Dependencies

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r shared/requirements.txt
pip install -r api_gateway/requirements.txt
pip install -r requirements-dev.txt
```

### 2. Run Database Migrations

```bash
cd migrations

# Create initial migration (if not exists)
alembic revision --autogenerate -m "Initial schema"

# Run migrations
alembic upgrade head

# Verify tables created
psql -d docproc_ai_dev -c "\dt"
# Should see: tenants, users, documents, document_chunks, etc.
```

### 3. Run Code Quality Checks

```bash
cd ..  # Back to backend/

# Format check with Black
black --check .

# Auto-format (if needed)
black .

# Lint with Ruff
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type check with MyPy
mypy shared/ api_gateway/ workers/ --ignore-missing-imports
```

### 4. Run Unit Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_models.py -v

# Run specific test function
pytest tests/test_models.py::test_user_creation -v

# View HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### 5. Test API Gateway Locally

**Terminal 1 - Start API Gateway:**

```bash
cd backend/api_gateway
source ../venv/bin/activate

# Run with auto-reload
uvicorn main:app --reload --port 8000 --log-level debug

# Should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# 🚀 Starting API Gateway...
```

**Terminal 2 - Test Endpoints:**

```bash
# Health check
curl http://localhost:8000/health

# Expected: {"status":"healthy","version":"1.0.0"}

# View API docs
open http://localhost:8000/docs  # Interactive Swagger UI

# Test authentication (needs Firebase token)
# First, get Firebase token from frontend login or:
curl -X POST http://localhost:8000/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User",
    "tenant_name": "Test Company"
  }'

# Upload document (with auth token)
curl -X POST http://localhost:8000/v1/documents/upload \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -F "file=@/path/to/test.pdf" \
  -F "document_type=invoice"

# List documents
curl http://localhost:8000/v1/documents \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

### 6. Test Workers Locally

**Test Invoice Worker:**

```bash
cd backend/workers/invoice_worker
source ../../venv/bin/activate

# Run worker
uvicorn main:app --reload --port 8001

# Test in another terminal
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant-id",
    "document_id": "test-doc-id",
    "gcs_path": "gs://bucket/test.pdf"
  }'
```

**Test OCR Worker:**

```bash
cd backend/workers/ocr_worker
uvicorn main:app --reload --port 8002
```

**Test Summarizer Worker:**

```bash
cd backend/workers/summarizer_worker
uvicorn main:app --reload --port 8003
```

**Test RAG Ingest Worker:**

```bash
cd backend/workers/rag_ingest_worker
uvicorn main:app --reload --port 8004
```

**Test Document Filling Worker:**

```bash
cd backend/workers/docfill_worker
uvicorn main:app --reload --port 8005
```

---

## Frontend Testing

### 1. Install Dependencies

```bash
cd frontend

# Install dependencies
npm install

# Verify installation
npm list --depth=0
```

### 2. Run Linting

```bash
# ESLint
npm run lint

# Fix auto-fixable issues
npm run lint:fix

# Format with Prettier
npm run format

# Type check
npm run type-check
```

### 3. Run Unit Tests

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# View coverage report
open coverage/index.html
```

### 4. Start Development Server

```bash
# Start frontend dev server
npm run dev

# Should see:
# VITE v4.x.x  ready in xxx ms
# ➜  Local:   http://localhost:5173/
# ➜  Network: use --host to expose
```

### 5. Test Frontend Manually

Open browser to http://localhost:5173

**Test Authentication Flow:**

1. **Signup:**
   - Navigate to http://localhost:5173/signup
   - Enter email, password, full name, organization name
   - Click "Create Account"
   - Should create Firebase user and backend tenant/user
   - Should redirect to dashboard

2. **Login:**
   - Navigate to http://localhost:5173/login
   - Enter email and password
   - Click "Sign In"
   - Should authenticate with Firebase
   - Should redirect to dashboard

3. **Protected Routes:**
   - Try accessing http://localhost:5173/ without login
   - Should redirect to /login
   - After login, should access dashboard

**Test Dashboard:**
- Should see user email in header
- Should see statistics (all zeros initially)
- Should see feature cards (Invoices, Summaries, Chat, Filling)
- Click each feature card to test navigation

**Browser Console Check:**
```javascript
// Open browser console (F12)
// Should see no errors
// Should see Firebase auth state
// Should see API calls to backend
```

---

## Infrastructure Testing

### 1. Validate Terraform Configuration

```bash
cd terraform

# Initialize Terraform
terraform init

# Validate syntax
terraform validate

# Expected: Success! The configuration is valid.

# Format check
terraform fmt -check -recursive

# Auto-format (if needed)
terraform fmt -recursive
```

### 2. Terraform Plan (Dry Run)

```bash
# Create terraform.tfvars
cat > terraform.tfvars << 'EOF'
project_id = "docai-mvp-prod"
region     = "europe-west1"
environment = "dev"
database_tier = "db-f1-micro"
EOF

# Run plan
terraform plan -out=tfplan

# Review the plan
# Should show all resources to be created:
# - google_service_account.cloud_run
# - google_storage_bucket.uploads
# - google_sql_database_instance.main
# - google_pubsub_topic.topics (5 topics)
# - google_cloud_run_v2_service.* (6 services)
# - etc.
```

### 3. Cost Estimation

```bash
# Install Infracost
brew install infracost  # macOS
curl -fsSL https://raw.githubusercontent.com/infracost/infracost/master/scripts/install.sh | sh  # Linux

# Register for free API key
infracost auth login

# Estimate costs
infracost breakdown --path .

# Expected output with monthly cost estimates
```

### 4. Terraform Apply (Test Environment)

**⚠️ WARNING: This will create real GCP resources and incur costs**

```bash
# Apply to test environment
terraform apply tfplan

# Confirm: yes

# Wait for completion (10-20 minutes)
# Cloud SQL creation is slowest

# View outputs
terraform output

# Should see:
# - api_gateway_url
# - uploads_bucket
# - database_connection_name
# - etc.
```

### 5. Verify Infrastructure

```bash
# Check Cloud Run services
gcloud run services list --region=europe-west1

# Check Cloud SQL
gcloud sql instances list

# Check Cloud Storage
gsutil ls

# Check Pub/Sub topics
gcloud pubsub topics list

# Check IAM service account
gcloud iam service-accounts list
```

### 6. Cleanup Test Infrastructure

```bash
# Destroy all resources
terraform destroy

# Confirm: yes

# Verify cleanup
gcloud run services list --region=europe-west1
gcloud sql instances list
```

---

## Integration Testing

### 1. Full Stack Local Test

**Setup:**

```bash
# Terminal 1: Backend API Gateway
cd backend/api_gateway
source ../venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: PostgreSQL (if not using Docker)
# Should already be running
```

**Test Full Workflow:**

1. **User Registration:**
   - Open http://localhost:5173/signup
   - Create account
   - Verify in database:
     ```bash
     psql -d docproc_ai_dev -c "SELECT * FROM users;"
     psql -d docproc_ai_dev -c "SELECT * FROM tenants;"
     ```

2. **Document Upload:**
   - Login to dashboard
   - Open browser console (F12) → Network tab
   - Use Swagger UI: http://localhost:8000/docs
   - Test `/v1/documents/upload` endpoint
   - Upload a test PDF
   - Verify in database:
     ```bash
     psql -d docproc_ai_dev -c "SELECT * FROM documents;"
     ```

3. **Invoice Processing:**
   - Use uploaded document ID
   - Call `/v1/invoices/{document_id}/process`
   - Check logs for Pub/Sub message published
   - Verify invoice worker receives message (if running)

4. **RAG Chat:**
   - Index a document: `/v1/chat/{document_id}/index`
   - Query document: `/v1/chat/query`
   - Verify chunks in database:
     ```bash
     psql -d docproc_ai_dev -c "SELECT id, chunk_index, token_count FROM document_chunks LIMIT 5;"
     ```

### 2. API Integration Tests

Create test script:

```bash
# Create integration test script
cat > test_api_integration.sh << 'EOF'
#!/bin/bash

API_URL="http://localhost:8000/v1"

echo "Testing API Integration..."

# Health check
echo "1. Health Check"
curl -s $API_URL/../health | jq .

# Signup
echo "2. Create User"
SIGNUP_RESPONSE=$(curl -s -X POST $API_URL/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "integration-test@example.com",
    "password": "TestPass123!",
    "full_name": "Integration Test",
    "tenant_name": "Test Org"
  }')
echo $SIGNUP_RESPONSE | jq .

# Extract user_id (you'll need to implement token retrieval)
# For now, use Firebase admin SDK to create custom token

echo "Integration tests completed!"
EOF

chmod +x test_api_integration.sh
./test_api_integration.sh
```

---

## Manual End-to-End Testing

### Test Scenarios

#### Scenario 1: Invoice Processing Workflow

1. **Login** → http://localhost:5173/login
2. **Navigate to Invoices** → Click "Invoice Processing" card
3. **Upload Invoice PDF** → Use sample invoice from `docs/sample_data/`
4. **Trigger Processing** → Click "Process Invoice"
5. **Wait for Results** → Should show extracted data
6. **Validate Data** → Edit fields if needed
7. **Approve** → Mark as validated
8. **Verify in Database:**
   ```sql
   SELECT * FROM invoice_data WHERE document_id = 'YOUR_DOC_ID';
   ```

#### Scenario 2: Document Summarization

1. **Upload Document** → Upload a multi-page PDF
2. **Navigate to Summaries**
3. **Generate Summary** → Select document, choose model (Flash/Pro)
4. **View Results** → Should show summary with key points
5. **Verify in Database:**
   ```sql
   SELECT * FROM document_summaries WHERE document_id = 'YOUR_DOC_ID';
   ```

#### Scenario 3: Chat with PDF (RAG)

1. **Upload Document** → Upload a PDF
2. **Index Document** → Trigger RAG indexing
3. **Navigate to Chat**
4. **Ask Questions:**
   - "What is this document about?"
   - "Summarize the main points"
   - "What are the key dates mentioned?"
5. **Verify Answers** → Should include source citations
6. **Check Chunks:**
   ```sql
   SELECT chunk_index, substring(content, 1, 100)
   FROM document_chunks
   WHERE document_id = 'YOUR_DOC_ID'
   ORDER BY chunk_index;
   ```

#### Scenario 4: Document Filling

1. **Upload ID Document** → Romanian ID card or passport
2. **Navigate to Document Filling**
3. **Select Template** → Choose form template
4. **Process** → Extract ID data and fill form
5. **Download** → Get filled PDF
6. **Verify** → Open PDF, check fields populated

### Performance Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils  # Ubuntu
brew install ab  # macOS

# Test API Gateway performance
ab -n 1000 -c 10 http://localhost:8000/health

# Test document upload (with auth)
# Create a test file
dd if=/dev/zero of=test.pdf bs=1M count=1

# Benchmark
ab -n 100 -c 5 -p test.pdf -T application/pdf \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/v1/documents/upload
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Error: could not connect to server
# Solution: Check PostgreSQL is running
docker ps | grep postgres  # If using Docker
pg_isready -h localhost -p 5432  # If local

# Restart if needed
docker start docproc-postgres
brew services restart postgresql@15
```

#### 2. Firebase Authentication Error

```bash
# Error: Firebase credentials not found
# Solution: Verify firebase-adminsdk.json exists
ls -la backend/firebase-adminsdk.json

# Download from Firebase Console:
# Project Settings > Service Accounts > Generate New Private Key
```

#### 3. GCP API Not Enabled

```bash
# Error: API [documentai.googleapis.com] not enabled
# Solution: Enable required APIs
gcloud services enable documentai.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable vision.googleapis.com
```

#### 4. Port Already in Use

```bash
# Error: Address already in use
# Solution: Kill process on port
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000  # Windows - note PID
taskkill /PID <PID> /F  # Windows
```

#### 5. Module Not Found

```bash
# Error: ModuleNotFoundError: No module named 'fastapi'
# Solution: Activate virtual environment and reinstall
source venv/bin/activate
pip install -r shared/requirements.txt
```

#### 6. Frontend Build Failed

```bash
# Error: Module not found
# Solution: Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

#### 7. Terraform State Locked

```bash
# Error: Error acquiring the state lock
# Solution: Force unlock (use carefully)
terraform force-unlock <LOCK_ID>
```

### Debugging Tips

**Backend Debugging:**

```bash
# Enable debug logging
export DEBUG=true

# Run with Python debugger
python -m pdb backend/api_gateway/main.py

# Or use ipdb (better)
pip install ipdb
# Add: import ipdb; ipdb.set_trace() in code
```

**Frontend Debugging:**

```javascript
// Browser console
// Check Firebase auth state
firebase.auth().currentUser

// Check API calls
// Network tab → Filter by XHR

// React DevTools
// Install Chrome extension
```

**Database Debugging:**

```bash
# Connect to database
psql -d docproc_ai_dev

# Common queries
\dt  -- List tables
\d tablename  -- Describe table
SELECT * FROM users LIMIT 5;
SELECT * FROM documents ORDER BY created_at DESC LIMIT 10;

# Check pgvector
SELECT id, embedding <-> '[0,0,0,...]'::vector AS distance
FROM document_chunks
ORDER BY distance LIMIT 5;
```

---

## Test Coverage Goals

### Backend
- **Unit Tests:** 60%+ coverage
- **Integration Tests:** Key workflows covered
- **API Tests:** All endpoints tested

### Frontend
- **Unit Tests:** 50%+ coverage
- **Component Tests:** All pages/components
- **E2E Tests:** Critical user flows

### Infrastructure
- **Terraform:** Valid and applies cleanly
- **No drift:** `terraform plan` shows no changes

---

## Continuous Testing

### Pre-commit Checks

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
EOF

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

### CI/CD Testing

Tests run automatically on:
- Every push to main/develop
- Every pull request
- See `.github/workflows/` for details

---

## Next Steps

1. ✅ Complete local backend testing
2. ✅ Complete local frontend testing
3. ✅ Validate Terraform configuration
4. ⏳ Deploy to test environment
5. ⏳ Run integration tests
6. ⏳ Deploy to production

---

**Need Help?**
- Check logs: `tail -f backend/logs/app.log`
- Review API docs: http://localhost:8000/docs
- Check GitHub Issues: https://github.com/rauly2k/docproc_ai/issues
