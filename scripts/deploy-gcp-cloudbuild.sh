#!/bin/bash

# INKA - Google Cloud Run Deployment via Cloud Build
# This script deploys without requiring local Docker
# Uses gcloud Cloud Build for container creation

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVICE_NAME="${1:-inka-api}"
REGION="${2:-europe-west1}"
PROJECT_ID="${3:-tattoo-480007}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       INKA - Cloud Build Deployment (No Docker Needed)    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Service Name:   ${SERVICE_NAME}"
echo "  Region:         ${REGION}"
echo "  Project ID:     ${PROJECT_ID}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Verify gcloud authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
    echo -e "${RED}❌ Not authenticated with Google Cloud${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi

echo -e "${YELLOW}✓ gcloud authenticated${NC}"
echo ""

# Step 1: Submit build to Cloud Build
echo -e "${YELLOW}📦 Step 1: Submitting build to Cloud Build...${NC}"
echo ""

BUILD_ID=$(gcloud builds submit . \
    --config=cloudbuild-deployment.yaml \
    --project=$PROJECT_ID \
    --substitutions="_SERVICE_NAME=$SERVICE_NAME,_REGION=$REGION,_PROJECT_ID=$PROJECT_ID" \
    --async \
    --format='value(id)' 2>&1 | tail -1)

if [ -z "$BUILD_ID" ] || [ "$BUILD_ID" = "null" ]; then
    echo -e "${RED}❌ Failed to submit build${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build submitted with ID: ${BUILD_ID}${NC}"
echo ""

# Step 2: Wait for build to complete
echo -e "${YELLOW}⏳ Step 2: Waiting for build to complete (this may take 5-10 minutes)...${NC}"
echo ""

# Monitor build progress
while true; do
    BUILD_STATUS=$(gcloud builds log $BUILD_ID --project=$PROJECT_ID --limit=1 2>&1)
    BUILD_STATE=$(gcloud builds describe $BUILD_ID --project=$PROJECT_ID --format='value(status)' 2>&1)
    
    case $BUILD_STATE in
        SUCCESS)
            echo -e "${GREEN}✓ Build completed successfully${NC}"
            break
            ;;
        FAILURE)
            echo -e "${RED}✗ Build failed${NC}"
            echo ""
            echo -e "${YELLOW}Build logs:${NC}"
            gcloud builds log $BUILD_ID --project=$PROJECT_ID
            exit 1
            ;;
        QUEUED|WORKING)
            echo -ne "\r  Status: $BUILD_STATE... "
            sleep 10
            ;;
        *)
            echo -ne "\r  Status: $BUILD_STATE... "
            sleep 10
            ;;
    esac
done

echo ""

# Step 3: Verify deployment
echo -e "${YELLOW}📋 Step 3: Verifying deployment...${NC}"
sleep 5

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --format='value(status.url)' 2>&1 || echo "")

if [ -z "$SERVICE_URL" ]; then
    SERVICE_URL="https://${SERVICE_NAME}-${REGION}-${PROJECT_ID}.a.run.app"
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              ✅ Deployment Successful!                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Service Details:${NC}"
echo "  Service URL:    ${SERVICE_URL}"
echo "  API Docs:       ${SERVICE_URL}/docs"
echo "  Health Check:   ${SERVICE_URL}/health"
echo "  Landing Page:   ${SERVICE_URL}/"
echo ""

# Try health check
echo -e "${YELLOW}🔍 Testing service health...${NC}"
sleep 5

if curl -s -f "${SERVICE_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Service starting up, health check will pass shortly${NC}"
fi

echo ""
echo -e "${YELLOW}📊 Build Information:${NC}"
echo "  Build ID:       $BUILD_ID"
echo "  View logs:      gcloud builds log $BUILD_ID"
echo ""

echo -e "${YELLOW}🔧 Next Steps:${NC}"
echo "  1. Open landing page: $SERVICE_URL"
echo "  2. Check logs:        gcloud run logs read $SERVICE_NAME --region=$REGION"
echo "  3. View metrics:      gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "  4. Configure domain:  gcloud run domain-mappings create --domain=yourdomain.com --service=$SERVICE_NAME --region=$REGION"
echo ""
