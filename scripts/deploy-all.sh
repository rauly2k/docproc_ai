#!/bin/bash
#
# Deploy all services to Google Cloud Run
# Usage: ./scripts/deploy-all.sh

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-your-project-id}"
REGION="${REGION:-europe-west1}"
REPOSITORY="docai-images"

echo "================================================"
echo "Deploying Document AI SaaS to Google Cloud Run"
echo "================================================"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "================================================"

# Colors for output
GREEN='\033[0.32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to build and push Docker image
build_and_push() {
    local service_name=$1
    local dockerfile_path=$2

    echo -e "${BLUE}Building $service_name...${NC}"

    local image_name="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${service_name}:latest"

    docker build -t "$image_name" -f "$dockerfile_path" backend/
    docker push "$image_name"

    echo -e "${GREEN}✓ Built and pushed $service_name${NC}"
}

# Function to deploy to Cloud Run
deploy_service() {
    local service_name=$1
    local image_name="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${service_name}:latest"
    local min_instances=${2:-0}
    local max_instances=${3:-10}
    local memory=${4:-1Gi}
    local cpu=${5:-1}
    local timeout=${6:-300}

    echo -e "${BLUE}Deploying $service_name to Cloud Run...${NC}"

    gcloud run deploy "$service_name" \
        --image "$image_name" \
        --platform managed \
        --region "$REGION" \
        --service-account "${service_name}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --no-allow-unauthenticated \
        --min-instances "$min_instances" \
        --max-instances "$max_instances" \
        --memory "$memory" \
        --cpu "$cpu" \
        --timeout "$timeout" \
        --set-secrets DATABASE_URL=database-url:latest \
        --set-env-vars PROJECT_ID="$PROJECT_ID",REGION="$REGION" \
        --quiet

    echo -e "${GREEN}✓ Deployed $service_name${NC}"
}

# 1. API Gateway
echo ""
echo "=== API Gateway ==="
build_and_push "api-gateway" "backend/Dockerfile"
deploy_service "api-gateway" 2 20 2Gi 2 300

# 2. Invoice Worker
echo ""
echo "=== Invoice Worker ==="
build_and_push "invoice-worker" "backend/Dockerfile"
deploy_service "invoice-worker" 0 5 2Gi 2 900

# 3. OCR Worker
echo ""
echo "=== OCR Worker ==="
build_and_push "ocr-worker" "backend/Dockerfile"
deploy_service "ocr-worker" 0 5 2Gi 2 600

# 4. Summarizer Worker
echo ""
echo "=== Summarizer Worker ==="
build_and_push "summarizer-worker" "backend/Dockerfile"
deploy_service "summarizer-worker" 0 5 1Gi 1 300

# 5. RAG Ingest Worker
echo ""
echo "=== RAG Ingest Worker ==="
build_and_push "rag-ingest-worker" "backend/Dockerfile"
deploy_service "rag-ingest-worker" 0 3 2Gi 2 900

# 6. Document Filling Worker
echo ""
echo "=== Document Filling Worker ==="
build_and_push "docfill-worker" "backend/Dockerfile"
deploy_service "docfill-worker" 0 3 2Gi 1 300

echo ""
echo "================================================"
echo -e "${GREEN}✓ All services deployed successfully!${NC}"
echo "================================================"
echo ""
echo "API Gateway URL:"
gcloud run services describe api-gateway --region="$REGION" --format="value(status.url)"
echo ""
echo "To view logs:"
echo "  gcloud run services logs read api-gateway --region=$REGION"
echo ""
echo "To view all services:"
echo "  gcloud run services list --region=$REGION"
