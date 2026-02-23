# CI/CD Control Center: Deployment Plan

## 1. Prerequisites
- GCP Project with billing enabled.
- Artifact Registry repository named `inka-repo`.
- Cloud SQL instance (Postgres).
- Secret Manager secret `DATABASE_URL` containing the postgres connection string.

## 2. Infrastructure Setup (Terraform)
1. Navigate to `infra/terraform`.
2. run `terraform init`.
3. run `terraform apply` with provided variables.

## 3. Initial Bootstrapping
Before the Control Center can orchestrate itself, we need to deploy it manually once or use a bootstrap Cloud Build trigger.

### Manual Bootstrap Script
```bash
# Set variables
PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west1"
REPO="inka-repo"

# Build API
gcloud builds submit apps/control-center/api \
  --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/cicd-api:latest

# Build UI
gcloud builds submit apps/control-center/ui \
  --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/cicd-ui:latest

# Deploy via Terraform or gcloud run deploy
```

## 4. Pipeline Configuration
Once deployed, register the pipelines in the Control Center DB:
1. `inka-api`
2. `inka-bot`
3. `inka-admin`

## 5. Security & RBAC Initial Setup
The first user to log in will be assigned the `SuperAdmin` role via the database.
Subsequent users must be invited or approved by an Admin.
