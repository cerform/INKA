#!/bin/bash
set -e

# INKA Deployment Script for Google Cloud Run
# Usage: ./deploy.sh [dev|staging|prod]

ENVIRONMENT=${1:-dev}
PROJECT_ID="your-gcp-project-id"  # TODO: Replace with your project ID
REGION="europe-west1"

echo "🚀 Deploying INKA to Google Cloud Run ($ENVIRONMENT)"

# Colors for output
RED='\033[0,31m'
GREEN='\033[0,32m'
YELLOW='\033[1,33m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Set project
echo -e "${YELLOW}📋 Setting GCP project to: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    sqladmin.googleapis.com \
    storage.googleapis.com

# Create Cloud SQL instance (if not exists)
echo -e "${YELLOW}🗄️  Setting up Cloud SQL PostgreSQL...${NC}"
if ! gcloud sql instances describe inka-db-$ENVIRONMENT 2>/dev/null; then
    echo "Creating new Cloud SQL instance..."
    gcloud sql instances create inka-db-$ENVIRONMENT \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --root-password=$(openssl rand -base64 32)
    
    # Create database
    gcloud sql databases create inka_$ENVIRONMENT \
        --instance=inka-db-$ENVIRONMENT
    
    # Create user
    DB_PASSWORD=$(openssl rand -base64 32)
    gcloud sql users create inka \
        --instance=inka-db-$ENVIRONMENT \
        --password=$DB_PASSWORD
    
    echo -e "${GREEN}✅ Cloud SQL instance created${NC}"
    echo -e "${YELLOW}Database password: $DB_PASSWORD${NC}"
    echo -e "${YELLOW}Save this password! You'll need it for setup wizard.${NC}"
else
    echo "Cloud SQL instance already exists"
fi

# Create secrets (if not exist)
echo -e "${YELLOW}🔐 Setting up Secret Manager...${NC}"

# Bot Token (you'll set this via setup wizard)
if ! gcloud secrets describe bot-token-$ENVIRONMENT 2>/dev/null; then
    echo -n "placeholder" | gcloud secrets create bot-token-$ENVIRONMENT --data-file=-
fi

# API Secret Key
if ! gcloud secrets describe api-secret-key-$ENVIRONMENT 2>/dev/null; then
    openssl rand -base64 32 | gcloud secrets create api-secret-key-$ENVIRONMENT --data-file=-
fi

# Database URL
if ! gcloud secrets describe database-url-$ENVIRONMENT 2>/dev/null; then
    DB_CONNECTION_NAME=$(gcloud sql instances describe inka-db-$ENVIRONMENT --format="value(connectionName)")
    echo -n "postgresql://inka:CHANGE_ME@/inka_$ENVIRONMENT?host=/cloudsql/$DB_CONNECTION_NAME" | \
        gcloud secrets create database-url-$ENVIRONMENT --data-file=-
    echo -e "${YELLOW}⚠️  Update database-url-$ENVIRONMENT secret with correct password${NC}"
fi

# Deploy API
echo -e "${YELLOW}🚀 Deploying API service...${NC}"
gcloud run deploy inka-api-$ENVIRONMENT \
    --source ./apps/api \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars ENVIRONMENT=$ENVIRONMENT \
    --set-secrets DATABASE_URL=database-url-$ENVIRONMENT:latest,API_SECRET_KEY=api-secret-key-$ENVIRONMENT:latest \
    --add-cloudsql-instances $(gcloud sql instances describe inka-db-$ENVIRONMENT --format="value(connectionName)") \
    --min-instances 1 \
    --max-instances 10 \
    --memory 512Mi \
    --timeout 300

API_URL=$(gcloud run services describe inka-api-$ENVIRONMENT --region $REGION --format="value(status.url)")
echo -e "${GREEN}✅ API deployed: $API_URL${NC}"

# Deploy Bot
echo -e "${YELLOW}🤖 Deploying Bot service...${NC}"
gcloud run deploy inka-bot-$ENVIRONMENT \
    --source ./apps/bot \
    --region $REGION \
    --platform managed \
    --no-allow-unauthenticated \
    --set-env-vars ENVIRONMENT=$ENVIRONMENT,API_URL=$API_URL \
    --set-secrets DATABASE_URL=database-url-$ENVIRONMENT:latest,BOT_TOKEN=bot-token-$ENVIRONMENT:latest \
    --add-cloudsql-instances $(gcloud sql instances describe inka-db-$ENVIRONMENT --format="value(connectionName)") \
    --min-instances 1 \
    --max-instances 5 \
    --memory 256Mi \
    --timeout 300

BOT_URL=$(gcloud run services describe inka-bot-$ENVIRONMENT --region $REGION --format="value(status.url)")
echo -e "${GREEN}✅ Bot deployed: $BOT_URL${NC}"

# Deploy Admin Panel
echo -e "${YELLOW}💻 Deploying Admin Panel...${NC}"
cd apps/admin
npm run build
cd ../..

gcloud run deploy inka-admin-$ENVIRONMENT \
    --source ./apps/admin \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars NEXT_PUBLIC_API_URL=$API_URL \
    --min-instances 0 \
    --max-instances 3 \
    --memory 512Mi

ADMIN_URL=$(gcloud run services describe inka-admin-$ENVIRONMENT --region $REGION --format="value(status.url)")
echo -e "${GREEN}✅ Admin Panel deployed: $ADMIN_URL${NC}"

# Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo ""
echo "1. Open Setup Wizard:"
echo -e "   ${GREEN}$ADMIN_URL/setup${NC}"
echo ""
echo "2. Enter configuration:"
echo "   - Bot Token (from @BotFather)"
echo "   - Database credentials"
echo "   - Admin account details"
echo ""
echo "3. Set Telegram webhook:"
echo -e "   ${GREEN}curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \\${NC}"
echo -e "   ${GREEN}  -d \"url=$BOT_URL/webhook\"${NC}"
echo ""
echo -e "${YELLOW}📊 Service URLs:${NC}"
echo -e "   API:   ${GREEN}$API_URL${NC}"
echo -e "   Bot:   ${GREEN}$BOT_URL${NC}"
echo -e "   Admin: ${GREEN}$ADMIN_URL${NC}"
echo ""
echo -e "${YELLOW}🔍 View logs:${NC}"
echo "   gcloud run services logs read inka-api-$ENVIRONMENT --region $REGION"
echo "   gcloud run services logs read inka-bot-$ENVIRONMENT --region $REGION"
echo ""
