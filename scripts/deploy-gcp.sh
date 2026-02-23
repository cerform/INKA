#!/bin/bash

# INKA - Google Cloud Run Deployment Script
# Usage: ./deploy-gcp.sh [service-name] [region] [image-name]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="${1:-inka-api}"
REGION="${2:-europe-west1}"
PROJECT_ID="${3:-tattoo-480007}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${COMMIT_SHA}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       INKA - Google Cloud Run Deployment                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Service Name:   ${SERVICE_NAME}"
echo "  Region:         ${REGION}"
echo "  Project ID:     ${PROJECT_ID}"
echo "  Image:          ${IMAGE_NAME}"
echo "  Git Commit:     ${COMMIT_SHA}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Step 1: Build Docker image
echo -e "${YELLOW}📦 Step 1: Building Docker image...${NC}"
docker build \
    -f apps/api/Dockerfile \
    -t ${IMAGE_NAME} \
    -t ${IMAGE_TAG} \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
fi

# Step 2: Push to Google Container Registry
echo -e "${YELLOW}🚀 Step 2: Pushing image to GCR...${NC}"
docker push ${IMAGE_NAME}
docker push ${IMAGE_TAG}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Image pushed to GCR${NC}"
else
    echo -e "${RED}✗ Push to GCR failed${NC}"
    exit 1
fi

# Step 3: Deploy to Cloud Run
echo -e "${YELLOW}🌐 Step 3: Deploying to Cloud Run...${NC}"

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Using default settings.${NC}"
    echo -e "${YELLOW}Create .env file for production configuration.${NC}"
fi

gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 50 \
    --min-instances 1 \
    --no-traffic \
    --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Deployment to Cloud Run completed${NC}"
else
    echo -e "${RED}✗ Cloud Run deployment failed${NC}"
    exit 1
fi

# Step 4: Get service URL
echo -e "${YELLOW}🔗 Step 4: Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --format='value(status.url)')

if [ -z "$SERVICE_URL" ]; then
    SERVICE_URL="https://${SERVICE_NAME}-$(gcloud config get-value project | cut -d- -f2)--${REGION}.a.run.app"
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              ✅ Deployment Successful!                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Service URL:${NC}      ${SERVICE_URL}"
echo -e "${GREEN}API Docs:${NC}         ${SERVICE_URL}/docs"
echo -e "${GREEN}Health Check:${NC}     ${SERVICE_URL}/health"
echo ""

# Step 5: Verify deployment
echo -e "${YELLOW}📋 Step 5: Verifying deployment...${NC}"
sleep 5

if curl -s -f "${SERVICE_URL}/health" > /dev/null; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed (service may still be starting)${NC}"
fi

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. View logs:    gcloud run logs read ${SERVICE_NAME} --region=${REGION}"
echo "  2. Set traffic:  gcloud run services update-traffic ${SERVICE_NAME} --to-revisions=LATEST=100"
echo "  3. View metrics: gcloud run services describe ${SERVICE_NAME} --region=${REGION}"
echo ""
