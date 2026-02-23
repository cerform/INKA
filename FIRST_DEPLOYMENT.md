# 🚀 INKA - First Deployment Guide

## What's New

Your INKA project now includes:

✅ **Modern Landing Page** - Beautiful, responsive first-impression page  
✅ **First Setup Wizard** - Interactive setup progress tracking  
✅ **Google Cloud Run Ready** - Production-grade deployment configuration  
✅ **One-Click Deploy** - Automated deployment script  
✅ **Monitoring & Logging** - Built-in health checks and metrics  

## Quick Start (5 minutes)

### 1. Prerequisites

```bash
# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Login to Google Cloud
gcloud auth login
gcloud config set project tattoo-480007

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com
```

### 2. Deploy in One Command

```bash
cd /Users/simanbekov/projects/inka

# Quick deploy (with all prompts)
bash scripts/quick-deploy.sh

# Or manual deploy with custom options
bash scripts/deploy-gcp.sh inka-api europe-west1
```

**That's it!** Your API will be live in ~2-3 minutes.

### 3. Access Your Service

Once deployed, you'll get a URL like:
```
https://inka-api-xxxxx-eu.a.run.app
```

Visit:
- 🏠 Landing Page: `https://inka-api-xxxxx-eu.a.run.app/`
- 📖 API Docs: `https://inka-api-xxxxx-eu.a.run.app/docs`
- ❤️ Health: `https://inka-api-xxxxx-eu.a.run.app/health`

## What Happens During Deployment

```
1. 📦 Build Docker Image
   - Compiles your code
   - Sets up dependencies
   - Creates container

2. 🚀 Push to Google Container Registry
   - Uploads to gcr.io
   - Tags with git commit SHA

3. 🌐 Deploy to Cloud Run
   - Creates new revision
   - Sets up networking
   - Configures auto-scaling

4. ✅ Verify & Test
   - Runs health checks
   - Confirms service is live
   - Shows you the URL
```

## Landing Page Features

### What You'll See

The landing page displays:

- **Project Information**
  - Service name and status
  - Version number
  - Environment details

- **Quick Links**
  - API Documentation
  - Health Check endpoint
  - GitHub repository
  - Setup status

- **Setup Wizard** (Track first-time setup)
  - Database configuration
  - Telegram bot setup
  - Admin panel installation
  - Test execution

### Interactive Setup

Track your setup progress via API:

```bash
SERVICE_URL="https://inka-api-xxxxx-eu.a.run.app"

# Get setup status
curl $SERVICE_URL/api/v1/setup

# Mark step as complete
curl -X POST $SERVICE_URL/api/v1/setup/complete/1
```

## Configuration for Production

### 1. Set Environment Variables

Create `.env.production`:

```bash
# Database (Cloud SQL)
DATABASE_URL=postgresql://user:pass@cloud-sql-ip:5432/inka_prod

# Cache (Memorystore)
REDIS_URL=redis://redis-ip:6379/0

# Security
API_SECRET_KEY=your-secure-key-32-chars-minimum
DEBUG=false

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### 2. Update Deployment Script

Edit `scripts/deploy-gcp.sh`:

```bash
# Line ~15 - Set your project ID
PROJECT_ID="your-gcp-project-id"

# Line ~19 - Set your region
REGION="europe-west1"  # or another region
```

### 3. Configure Auto-scaling

```bash
# Adjust min/max instances based on expected load
gcloud run services update inka-api \
  --min-instances=2 \
  --max-instances=100 \
  --region=europe-west1
```

## Monitoring & Logs

### View Logs

```bash
# Stream logs (follow mode)
gcloud run logs read inka-api --follow

# View specific number of logs
gcloud run logs read inka-api --limit=50

# Filter by severity
gcloud run logs read inka-api --limit=50 | grep ERROR
```

### View Metrics

```bash
# Check current deployment
gcloud run services describe inka-api

# View all revisions
gcloud run revisions list --service=inka-api

# Check resource usage
gcloud monitoring dashboards list
```

### Set Up Alerts

```bash
# Alert on high error rate
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="5XX errors" \
  --condition-threshold-value=10
```

## Updating Your Service

### Deploy New Version

```bash
# Make code changes
# Then:
bash scripts/deploy-gcp.sh inka-api europe-west1

# Your new version will be live in 2-3 minutes!
```

### Roll Back to Previous Version

```bash
# See all revisions
gcloud run revisions list --service=inka-api --region=europe-west1

# Route traffic to previous revision
gcloud run services update-traffic inka-api \
  --to-revisions=PREVIOUS=100 \
  --region=europe-west1
```

## Troubleshooting

### Service won't start?

```bash
# Check logs for errors
gcloud run logs read inka-api --limit=100

# Common issues:
# 1. Database connection - Check DATABASE_URL
# 2. Missing environment variables - Check .env
# 3. Port mismatch - Should be 8080
# 4. Timeout - Increase timeout in deployment script
```

### Getting "permission denied" errors?

```bash
# Check your service account has correct permissions
gcloud projects get-iam-policy tattoo-480007

# Grant necessary roles
gcloud projects add-iam-policy-binding tattoo-480007 \
  --member=serviceAccount:inka-cloud-run@tattoo-480007.iam.gserviceaccount.com \
  --role=roles/cloudsql.client
```

### High latency or errors?

```bash
# Increase resources
gcloud run services update inka-api \
  --memory=1Gi \
  --cpu=2 \
  --max-instances=100
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy
        run: |
          bash scripts/deploy-gcp.sh inka-api europe-west1
        env:
          GOOGLE_CREDENTIALS: ${{ secrets.GCP_SA_KEY }}
```

### Cloud Build Integration

```bash
# Automatically deploy on git push
gcloud builds triggers create github \
  --repo-name=INKA \
  --repo-owner=cerform \
  --branch-pattern="^main$" \
  --build-config=cloudbuild-deployment.yaml
```

## Cost Estimation

**Monthly cost estimate:**

- Cloud Run: ~$10-30 (depending on traffic)
- Cloud SQL: ~$10-20/month
- Cloud Storage: ~$1-5/month
- Memorystore Redis: ~$20-40/month

**Total: $40-95/month** for small-to-medium traffic

To reduce costs:
- Use Cloud SQL `db-f1-micro` tier
- Set `min-instances=0` (cold starts OK for low traffic)
- Use Memorystore instead of self-managed Redis

## Next Steps

1. ✅ Deploy your first version
2. 📊 Monitor logs and metrics
3. 🔐 Set up security (IAM, SSL certificates)
4. 📈 Configure auto-scaling policies
5. 🎯 Set up uptime monitoring and alerts
6. 📚 Document your setup in deployment guide

## Documentation

Full deployment documentation:
- [Google Cloud Run Deployment Guide](./docs/GOOGLE_CLOUD_RUN_DEPLOYMENT.md)
- [Architecture Overview](./docs/architecture/)
- [Development Setup](./docs/development/)

## Support

Need help? Check:
1. [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
2. [INKA GitHub Issues](https://github.com/cerform/INKA/issues)
3. Deployment logs: `gcloud run logs read inka-api`

---

**Ready to deploy?**

```bash
cd /Users/simanbekov/projects/inka
bash scripts/quick-deploy.sh
```

Your landing page will be live in seconds! 🎉
