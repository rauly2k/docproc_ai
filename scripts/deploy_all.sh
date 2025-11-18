#!/bin/bash
# Deploy all services to Cloud Run

set -e

PROJECT_ID=${PROJECT_ID:-"docai-mvp-prod"}
REGION=${REGION:-"europe-west1"}

echo "Deploying all services to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Push images to Container Registry
echo "Pushing images to GCR..."
docker push gcr.io/$PROJECT_ID/api-gateway:latest
docker push gcr.io/$PROJECT_ID/invoice-worker:latest
docker push gcr.io/$PROJECT_ID/ocr-worker:latest
docker push gcr.io/$PROJECT_ID/summarizer-worker:latest
docker push gcr.io/$PROJECT_ID/rag-ingest-worker:latest
docker push gcr.io/$PROJECT_ID/rag-query-worker:latest
docker push gcr.io/$PROJECT_ID/docfill-worker:latest

# Deploy API Gateway
echo "Deploying API Gateway..."
gcloud run deploy api-gateway \
  --image gcr.io/$PROJECT_ID/api-gateway:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 10 \
  --cpu 2 \
  --memory 1Gi \
  --timeout 300

# Deploy Workers
for worker in invoice ocr summarizer rag-ingest rag-query docfill; do
  echo "Deploying $worker-worker..."
  gcloud run deploy $worker-worker \
    --image gcr.io/$PROJECT_ID/$worker-worker:latest \
    --region $REGION \
    --platform managed \
    --no-allow-unauthenticated \
    --min-instances 0 \
    --max-instances 5 \
    --cpu 2 \
    --memory 2Gi \
    --timeout 900
done

echo "All services deployed successfully!"
echo "API Gateway URL:"
gcloud run services describe api-gateway --region $REGION --format="value(status.url)"
