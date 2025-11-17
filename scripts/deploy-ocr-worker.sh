#!/bin/bash
set -e

PROJECT_ID="docai-mvp-prod"
REGION="europe-west1"
SERVICE_NAME="ocr-worker"
IMAGE_NAME="europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/$SERVICE_NAME"

cd backend
docker build -t $IMAGE_NAME:latest -f workers/ocr_worker/Dockerfile .
docker push $IMAGE_NAME:latest

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --service-account ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,REGION=$REGION,ENVIRONMENT=prod \
  --set-secrets DATABASE_URL=database-url:latest,DB_PASSWORD=database-password:latest,DOCUMENTAI_OCR_PROCESSOR_ID=documentai-ocr-processor-id:latest \
  --min-instances 0 \
  --max-instances 5 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 1

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')

gcloud pubsub subscriptions create ocr-processing-sub \
  --topic=ocr-processing \
  --push-endpoint="$SERVICE_URL/process" \
  --push-auth-service-account=ai-workers@$PROJECT_ID.iam.gserviceaccount.com \
  --ack-deadline=600 \
  --message-retention-duration=7d

echo "Deployment complete!"
