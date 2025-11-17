#!/bin/bash

set -e

PROJECT_ID="docai-mvp-prod"
REGION="europe-west1"
SERVICE_NAME="api-gateway"
IMAGE_NAME="europe-west1-docker.pkg.dev/$PROJECT_ID/docai-images/$SERVICE_NAME"

echo "Building Docker image..."
cd backend
docker build -t $IMAGE_NAME:latest -f api_gateway/Dockerfile .

echo "Pushing to Artifact Registry..."
docker push $IMAGE_NAME:latest

echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --service-account api-gateway@$PROJECT_ID.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,REGION=$REGION,ENVIRONMENT=prod \
  --set-secrets DATABASE_URL=database-url:latest,DB_PASSWORD=database-password:latest \
  --min-instances 1 \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 80

echo "Deployment complete!"
echo "Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'
