# 🚀 INKA Google Cloud Run Deployment Guide

## Overview

This guide walks you through deploying the INKA Tattoo Salon Admin System to Google Cloud Run with a modern landing page and first-setup wizard.

## Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and configured
- Docker installed locally
- Access to Container Registry (gcr.io)
- Python 3.11+ (for local testing)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Run                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         INKA API Service (Cloud Run)                   │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Landing Page  │  API  │  Health Check          │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Cloud SQL (PostgreSQL)                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Cloud Memorystore (Redis)                     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Step 1: Prepare Environment

### 1.1 Set up Google Cloud Project

```bash
# Set your project ID
export PROJECT_ID="tattoo-480007"
export REGION="europe-west1"
export SERVICE_NAME="inka-api"

# Authenticate with Google Cloud
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  cloudkms.googleapis.com \
  cloudbuild.googleapis.com
```

### 1.2 Configure Service Account

```bash
# Create service account
gcloud iam service-accounts create inka-cloud-run \
  --display-name="INKA Cloud Run Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:inka-cloud-run@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:inka-cloud-run@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/redis.editor"
```

## Step 2: Set Up Cloud SQL (PostgreSQL)

```bash
# Create Cloud SQL instance
gcloud sql instances create inka-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --availability-type=REGIONAL \
  --backup-start-time=03:00

# Create database
gcloud sql databases create inka_prod \
  --instance=inka-db

# Create user
gcloud sql users create inka_user \
  --instance=inka-db \
  --password=<SECURE_PASSWORD>

# Get connection name
gcloud sql instances describe inka-db --format='value(connectionName)'
```

## Step 3: Set Up Cloud Memorystore (Redis)

```bash
# Create Redis instance
gcloud redis instances create inka-redis \
  --size=1 \
  --region=$REGION \
  --tier=basic \
  --redis-version=7.0

# Get connection details
gcloud redis instances describe inka-redis --region=$REGION
```

## Step 4: Prepare Environment Variables

Create a `.env.production` file with your production configuration:

```bash
# Database
DATABASE_URL=postgresql://inka_user:PASSWORD@CLOUD_SQL_IP:5432/inka_prod

# Redis
REDIS_URL=redis://REDIS_IP:6379/0

# API Configuration
API_SECRET_KEY=your_secure_secret_key_min_32_chars
PROJECT_NAME=INKA-Production
LOG_LEVEL=INFO
ENVIRONMENT=production

# Feature Flags
DEBUG=false
ENABLE_DOCS=true

# Telegram Bot (if using)
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321
```

## Step 5: Deploy Using Automated Script

### Option A: Using Deploy Script (Recommended)

```bash
# Make script executable
chmod +x scripts/deploy-gcp.sh

# Run deployment
./scripts/deploy-gcp.sh inka-api europe-west1

# With custom image
./scripts/deploy-gcp.sh inka-api europe-west1 custom-registry
```

**What the script does:**
1. ✅ Builds Docker image
2. ✅ Pushes to Google Container Registry
3. ✅ Deploys to Cloud Run
4. ✅ Verifies health check
5. ✅ Generates deployment report

### Option B: Using Cloud Build (CI/CD)

```bash
# Trigger build from Git
gcloud builds submit --config=cloudbuild-deployment.yaml

# Or schedule automatic builds
gcloud builds triggers create github \
  --repo-name=INKA \
  --repo-owner=cerform \
  --branch-pattern="^main$" \
  --build-config=cloudbuild-deployment.yaml \
  --name=inka-deploy-main
```

### Option C: Manual Docker Push

```bash
# Build locally
docker build -f apps/api/Dockerfile -t gcr.io/$PROJECT_ID/inka-api:latest .

# Push to GCR
docker push gcr.io/$PROJECT_ID/inka-api:latest

# Deploy to Cloud Run
gcloud run deploy inka-api \
  --image gcr.io/$PROJECT_ID/inka-api:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 50 \
  --service-account inka-cloud-run@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars "ENVIRONMENT=production"
```

## Step 6: Configure Domain & SSL

```bash
# Get Cloud Run service URL
gcloud run services describe inka-api \
  --platform managed \
  --region $REGION \
  --format='value(status.url)'

# Set up custom domain (if you have one)
gcloud run domain-mappings create \
  --domain=inka.yourdomain.com \
  --service=inka-api \
  --region=$REGION

# SSL is automatically provided by Google
```

## Step 7: Verify Deployment

### Health Check
```bash
SERVICE_URL=$(gcloud run services describe inka-api \
  --platform managed \
  --region $REGION \
  --format='value(status.url)')

# Test landing page
curl $SERVICE_URL

# Test health endpoint
curl $SERVICE_URL/health

# Test API documentation
curl $SERVICE_URL/docs
```

### View Logs
```bash
# Stream logs
gcloud run logs read inka-api --region=$REGION --limit 50 --follow

# View specific revision
gcloud run revisions list --region=$REGION --service=inka-api
```

### Monitor Metrics
```bash
# View deployment metrics
gcloud run services describe inka-api \
  --region=$REGION \
  --format=json

# View in Cloud Console
echo "https://console.cloud.google.com/run/detail/$REGION/inka-api"
```

## Step 8: Traffic Management

```bash
# Route traffic gradually
gcloud run services update-traffic inka-api \
  --region=$REGION \
  --to-revisions=LATEST=50,PREVIOUS=50

# Route all traffic to new revision
gcloud run services update-traffic inka-api \
  --region=$REGION \
  --to-revisions=LATEST=100
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
gcloud run logs read inka-api --region=$REGION --limit 100

# Check container image
gcloud container images list --filter=inka-api

# Inspect image
gcloud container images describe gcr.io/$PROJECT_ID/inka-api:latest
```

### Database Connection Issues
```bash
# Check Cloud SQL instance
gcloud sql instances describe inka-db

# Check Cloud SQL proxy logs
gcloud logging read "resource.type=cloudsql_database" --limit 50

# Reset user password
gcloud sql users set-password inka_user \
  --instance=inka-db \
  --password=<NEW_PASSWORD>
```

### Memory/CPU Issues
```bash
# Increase resources
gcloud run services update inka-api \
  --memory=1Gi \
  --cpu=2 \
  --max-instances=100

# Check current settings
gcloud run services describe inka-api --region=$REGION --format=json | \
  jq '.spec.template.spec.containers[0].resources'
```

## Post-Deployment

### 1. Set Up Monitoring

```bash
# Create uptime check
gcloud monitoring checks create \
  --display-name="INKA API Health" \
  --monitored-resource="uptime_url" \
  --check-interval=60 \
  --timeout=10 \
  --http-check-path="/health"
```

### 2. Configure Alerts

```bash
# Create alert policy (via Console or Terraform)
# Alert on: High error rate, High latency, Quota exceeded
```

### 3. Enable Logging

```bash
# Cloud Logging is automatically enabled
# View structured logs
gcloud logging read --resource=cloud_run_revision
```

### 4. Set Up Auto-scaling

```bash
# Already configured with min-instances=1, max-instances=50
# Adjust as needed:
gcloud run services update inka-api \
  --min-instances=2 \
  --max-instances=100 \
  --region=$REGION
```

## Landing Page Features

Your deployment includes a modern landing page with:

- 🎨 **Responsive Design** - Works on all devices
- 📱 **Quick Start** - Copy-paste deployment commands
- 📚 **Documentation Links** - Easy access to guides
- 🔗 **API Reference** - Built-in Swagger UI
- ⚡ **Setup Wizard** - Track first-setup progress
- ❤️ **Health Monitor** - Real-time service status

### Access Points

```
Landing Page:     $SERVICE_URL/
API Docs:         $SERVICE_URL/docs
ReDoc:            $SERVICE_URL/redoc
Health Check:     $SERVICE_URL/health
Setup Status:     $SERVICE_URL/api/v1/setup
```

## Rollback Procedure

```bash
# List previous revisions
gcloud run revisions list --service=inka-api --region=$REGION

# Route traffic to previous revision
gcloud run services update-traffic inka-api \
  --region=$REGION \
  --to-revisions=<PREVIOUS_REVISION>=100
```

## Cost Optimization

- **Min instances**: Keep at 1 for production
- **Memory**: Start with 512Mi, increase if needed
- **CPU**: Start with 1, scale based on load
- **Max instances**: Set based on expected traffic

## Security Checklist

- [ ] Enable IAM service account
- [ ] Configure VPC for Cloud SQL
- [ ] Enable Cloud Armor for DDoS protection
- [ ] Set up Secret Manager for sensitive data
- [ ] Enable audit logging
- [ ] Configure rate limiting
- [ ] Set up WAF rules

## Next Steps

1. Monitor deployment for 24-48 hours
2. Run load tests to determine scaling needs
3. Configure backup policies for data
4. Set up disaster recovery plan
5. Document any custom configurations

## Support & Documentation

- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [INKA Architecture](./architecture/README.md)
- [API Documentation](https://api.inka.dev/docs)
- [GitHub Repository](https://github.com/cerform/INKA)

---

**Last Updated**: February 22, 2026
**Version**: 1.0.0
**Status**: Production Ready ✅
