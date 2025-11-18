#!/bin/bash
# Build all Docker images for deployment

set -e

PROJECT_ID=${PROJECT_ID:-"docai-mvp-prod"}
REGION=${REGION:-"europe-west1"}

echo "Building all Docker images for project: $PROJECT_ID"

# Build API Gateway
echo "Building API Gateway..."
docker build -t gcr.io/$PROJECT_ID/api-gateway:latest \
  -f backend/api_gateway/Dockerfile \
  backend/

# Build Invoice Worker
echo "Building Invoice Worker..."
docker build -t gcr.io/$PROJECT_ID/invoice-worker:latest \
  -f backend/workers/invoice_worker/Dockerfile \
  backend/

# Build OCR Worker
echo "Building OCR Worker..."
docker build -t gcr.io/$PROJECT_ID/ocr-worker:latest \
  -f backend/workers/ocr_worker/Dockerfile \
  backend/

# Build Summarizer Worker
echo "Building Summarizer Worker..."
docker build -t gcr.io/$PROJECT_ID/summarizer-worker:latest \
  -f backend/workers/summarizer_worker/Dockerfile \
  backend/

# Build RAG Ingest Worker
echo "Building RAG Ingest Worker..."
docker build -t gcr.io/$PROJECT_ID/rag-ingest-worker:latest \
  -f backend/workers/rag_ingest_worker/Dockerfile \
  backend/

# Build RAG Query Worker
echo "Building RAG Query Worker..."
docker build -t gcr.io/$PROJECT_ID/rag-query-worker:latest \
  -f backend/workers/rag_query_worker/Dockerfile \
  backend/

# Build Document Filling Worker
echo "Building Document Filling Worker..."
docker build -t gcr.io/$PROJECT_ID/docfill-worker:latest \
  -f backend/workers/docfill_worker/Dockerfile \
  backend/

echo "All images built successfully!"
echo "Run ./scripts/deploy_all.sh to deploy to Cloud Run"
