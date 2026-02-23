#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west1"
REPO="inka-repo"
API_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/api:latest"
BOT_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/bot:latest"
ADMIN_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/admin:latest"

echo "🚀 Starting Inka Production Deployment..."

# 1. Build and Push Images using Cloud Build
echo "📦 Building images with Cloud Build..."
gcloud builds submit . --config=cloudbuild.yaml --substitutions=_IMAGE=$API_IMAGE,_DOCKERFILE=apps/api/Dockerfile
gcloud builds submit . --config=cloudbuild.yaml --substitutions=_IMAGE=$BOT_IMAGE,_DOCKERFILE=apps/bot/Dockerfile
gcloud builds submit . --config=cloudbuild.yaml --substitutions=_IMAGE=$ADMIN_IMAGE,_DOCKERFILE=apps/admin/Dockerfile



# 2. Deploy API
echo "🌐 Deploying API..."
gcloud run deploy inka-api \
  --image=$API_IMAGE \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --update-env-vars="ENVIRONMENT=prod"

API_URL=$(gcloud run services describe inka-api --region=$REGION --format='value(status.url)')

# 3. Deploy Bot
echo "🤖 Deploying Bot..."
gcloud run deploy inka-bot \
  --image=$BOT_IMAGE \
  --region=$REGION \
  --platform=managed \
  --no-allow-unauthenticated \
  --update-env-vars="API_URL=$API_URL"

# 4. Deploy Admin
echo "🖥️ Deploying Admin..."
gcloud run deploy inka-admin \
  --image=$ADMIN_IMAGE \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --update-env-vars="VITE_API_URL=$API_URL"

ADMIN_URL=$(gcloud run services describe inka-admin --region=$REGION --format='value(status.url)')

# 5. Run Migrations
echo "🐘 Running DB Migrations..."
# Note: In a real environment, this might be run via a job or a temporary container
# Here we assume the terminal has DB access for demonstration
(cd libs/database && alembic upgrade head)


echo "✅ Deployment Complete!"
echo "------------------------------------------------"
echo "API URL:   $API_URL"
echo "Admin URL: $ADMIN_URL (Start Setup here!)"
echo "------------------------------------------------"
