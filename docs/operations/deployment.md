# Deployment Guide

## Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed locally
- GitHub repository connected to Google Cloud Build

## Environment Setup

### 1. Create Cloud SQL Instance

```bash
gcloud sql instances create inka-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=europe-west1

gcloud sql databases create inka_prod \
  --instance=inka-db

gcloud sql users create inka \
  --instance=inka-db \
  --password=SECURE_PASSWORD_HERE
```

### 2. Create Secrets

```bash
# Bot token
echo -n "YOUR_BOT_TOKEN" | gcloud secrets create bot-token --data-file=-

# API secret key
openssl rand -base64 32 | gcloud secrets create api-secret-key --data-file=-

# Database URL
echo -n "postgresql://inka:PASSWORD@/inka_prod?host=/cloudsql/PROJECT:europe-west1:inka-db" | \
  gcloud secrets create database-url --data-file=-
```

### 3. Enable APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com
```

## Deployment

### API Service

```bash
cd apps/api

gcloud run deploy inka-api \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets DATABASE_URL=database-url:latest,API_SECRET_KEY=api-secret-key:latest \
  --add-cloudsql-instances PROJECT:europe-west1:inka-db \
  --min-instances 1 \
  --max-instances 10 \
  --memory 512Mi
```

### Bot Service

```bash
cd apps/bot

gcloud run deploy inka-bot \
  --source . \
  --region europe-west1 \
  --platform managed \
  --no-allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets DATABASE_URL=database-url:latest,BOT_TOKEN=bot-token:latest \
  --add-cloudsql-instances PROJECT:europe-west1:inka-db \
  --min-instances 1 \
  --max-instances 5 \
  --memory 256Mi
```

### Admin Panel

```bash
cd apps/admin

# Build and push to Container Registry
docker build -t gcr.io/PROJECT/inka-admin .
docker push gcr.io/PROJECT/inka-admin

gcloud run deploy inka-admin \
  --image gcr.io/PROJECT/inka-admin \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars NEXT_PUBLIC_API_URL=https://inka-api-HASH.run.app \
  --min-instances 0 \
  --max-instances 3 \
  --memory 512Mi
```

## Database Migrations

Run migrations after first deployment:

```bash
# Connect to Cloud SQL Proxy
cloud_sql_proxy -instances=PROJECT:europe-west1:inka-db=tcp:5432

# In another terminal
export DATABASE_URL="postgresql://inka:PASSWORD@localhost:5432/inka_prod"
alembic -c libs/database/alembic.ini upgrade head
```

## CI/CD with GitHub Actions

### Setup

1. Create service account:
```bash
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

gcloud projects add-iam-policy-binding PROJECT \
  --member="serviceAccount:github-actions@PROJECT.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding PROJECT \
  --member="serviceAccount:github-actions@PROJECT.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

2. Create key and add to GitHub secrets:
```bash
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@PROJECT.iam.gserviceaccount.com
```

Add `key.json` content to GitHub secret `GCP_SA_KEY`

### Deploy Workflow

See `.github/workflows/deploy-api.yml` and `.github/workflows/deploy-bot.yml`

## Monitoring

### Logs

```bash
# API logs
gcloud run services logs read inka-api --region europe-west1

# Bot logs
gcloud run services logs read inka-bot --region europe-west1
```

### Metrics

View in Cloud Console:
- https://console.cloud.google.com/run?project=PROJECT

## Rollback

```bash
# List revisions
gcloud run revisions list --service inka-api --region europe-west1

# Rollback to specific revision
gcloud run services update-traffic inka-api \
  --to-revisions REVISION=100 \
  --region europe-west1
```

## Troubleshooting

### Service won't start
- Check logs: `gcloud run services logs read SERVICE`
- Verify secrets are accessible
- Check Cloud SQL connection

### Database connection issues
- Verify Cloud SQL instance is running
- Check connection string format
- Ensure service account has Cloud SQL Client role

### Bot not receiving updates
- Verify webhook URL is set correctly
- Check Telegram webhook status: `curl https://api.telegram.org/botTOKEN/getWebhookInfo`
- Set webhook: `curl -X POST https://api.telegram.org/botTOKEN/setWebhook -d "url=https://inka-bot-HASH.run.app/webhook"`
