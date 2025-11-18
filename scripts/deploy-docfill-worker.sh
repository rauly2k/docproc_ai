#!/bin/bash

set -e

PROJECT_ID="docai-mvp-prod"
REGION="europe-west1"
SERVICE_NAME="docfill-worker"
IMAGE_NAME="europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/$SERVICE_NAME"

echo "Building Docker image..."
cd backend
docker build -t $IMAGE_NAME:latest -f workers/docfill_worker/Dockerfile ..

echo "Pushing to Artifact Registry..."
docker push $IMAGE_NAME:latest

echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --service-account ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,REGION=$REGION,ENVIRONMENT=prod \
  --set-secrets DATABASE_URL=database-url:latest,DB_PASSWORD=database-password:latest,DOCUMENTAI_ID_PROCESSOR_ID=documentai-id-processor-id:latest,GCS_BUCKET_PROCESSED=gcs-bucket-processed:latest \
  --min-instances 0 \
  --max-instances 5 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 1

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')

echo "Creating Pub/Sub push subscription..."
gcloud pubsub subscriptions create document-filling-sub \
  --topic=document-filling \
  --push-endpoint="$SERVICE_URL/process" \
  --push-auth-service-account=ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=600 \
  --message-retention-duration=7d \
  --max-retry-delay=600s \
  --min-retry-delay=10s

echo "Deployment complete!"
echo "Worker URL: $SERVICE_URL"
echo ""
echo "Next steps:"
echo "1. Create Document AI ID Processor in Cloud Console"
echo "2. Store processor ID in Secret Manager as 'documentai-id-processor-id'"
echo "3. Add PDF form templates to backend/shared/pdf_templates/"
echo "4. Test with: curl -X POST $SERVICE_URL/health"
