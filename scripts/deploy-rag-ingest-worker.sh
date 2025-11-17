#!/bin/bash

set -e

PROJECT_ID="docai-mvp-prod"
REGION="europe-west1"
SERVICE_NAME="rag-ingest-worker"
IMAGE_NAME="europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/$SERVICE_NAME"

echo "Building Docker image..."
cd backend
docker build -t $IMAGE_NAME:latest -f workers/rag_ingest_worker/Dockerfile .

echo "Pushing to Artifact Registry..."
docker push $IMAGE_NAME:latest

echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --service-account ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,VERTEX_AI_LOCATION=us-central1,ENVIRONMENT=prod \
  --set-secrets DATABASE_URL=database-url:latest,DB_PASSWORD=database-password:latest \
  --min-instances 0 \
  --max-instances 5 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 1

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')

echo "Creating Pub/Sub push subscription..."
gcloud pubsub subscriptions create rag-ingestion-sub \
  --topic=rag-ingestion \
  --push-endpoint="$SERVICE_URL/process" \
  --push-auth-service-account=ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=600 \
  --message-retention-duration=7d

echo "Deployment complete!"
echo "Worker URL: $SERVICE_URL"
