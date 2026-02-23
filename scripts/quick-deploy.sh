#!/bin/bash

# INKA Quick Deploy to Google Cloud Run
# One-command deployment with auto-configuration

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║         INKA Quick Deploy - Google Cloud Run             ║
║                   One-Click Deployment                    ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check requirements
echo -e "${YELLOW}🔍 Checking requirements...${NC}"

for cmd in gcloud docker git; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}✗ $cmd not installed${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All requirements met${NC}"

# Configuration
PROJECT_ID="${GCP_PROJECT:-tattoo-480007}"
REGION="${GCP_REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-inka-api}"

echo -e "\n${YELLOW}Configuration:${NC}"
echo "  Project: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"

# Get current git info
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo -e "  Branch: $BRANCH"
echo -e "  Commit: $COMMIT"

# Confirm
echo -e "\n${YELLOW}Ready to deploy? (y/n)${NC}"
read -r confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Deployment cancelled"
    exit 0
fi

# Run deployment
echo -e "\n${YELLOW}Starting deployment...${NC}\n"
./scripts/deploy-gcp.sh $SERVICE_NAME $REGION $PROJECT_ID

echo -e "\n${GREEN}✅ Deployment complete!${NC}"
echo -e "${YELLOW}View your service at:${NC}"
gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)'
