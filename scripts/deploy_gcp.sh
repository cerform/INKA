#!/bin/bash
set -e

# Configuration
REGION="europe-west1"
DB_INSTANCE_NAME="inka-db-prod"
DB_NAME="inka_prod"
DB_USER="inka"
REDIS_INSTANCE_NAME="inka-redis-prod"

echo "🚀 Starting Inka Deployment to Google Cloud (Region: $REGION)"

# 1. Project Setup
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    read -p "Enter your Google Cloud Project ID: " PROJECT_ID
else
    PROJECT_ID=$GOOGLE_CLOUD_PROJECT
fi

echo "Using Project ID: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# 2. Enable APIs
echo "🔌 Enabling necessary APIs..."
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    compute.googleapis.com \
    servicenetworking.googleapis.com

# 3. Network Configuration (Private Service Access for SQL/Redis)
echo "🌐 Configuring Network..."
# Check if network exists, if not use default
NETWORK="default"
# Create an IP range for private services if not exists
gcloud compute addresses create google-managed-services-$NETWORK \
    --global \
    --purpose=VPC_PEERING \
    --prefix-length=16 \
    --description="Peering for Google Cloud services" \
    --network=$NETWORK || echo "IP range likely exists, continuing..."

gcloud services vpc-peerings connect \
    --service=servicenetworking.googleapis.com \
    --ranges=google-managed-services-$NETWORK \
    --network=$NETWORK \
    --project=$PROJECT_ID || echo "Peering likely exists, continuing..."

# 4. Cloud SQL Setup
echo "🗄️ Checking Cloud SQL Instance..."
if ! gcloud sql instances describe $DB_INSTANCE_NAME > /dev/null 2>&1; then
    echo "Creating Cloud SQL instance (this takes a few minutes)..."
    # Generate a random root password
    ROOT_PASSWORD=$(openssl rand -base64 12)
    echo "Generated Root Password: $ROOT_PASSWORD"
    
    gcloud sql instances create $DB_INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --cpu=1 \
        --memory=3840MiB \
        --region=$REGION \
        --root-password=$ROOT_PASSWORD \
        --network=$NETWORK
else
    echo "Cloud SQL instance $DB_INSTANCE_NAME already exists."
fi

echo "Creating Database and User..."
gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE_NAME || echo "Database exists"
# Prompt for DB password
read -s -p "Enter password for DB user '$DB_USER': " DB_PASSWORD
echo ""
gcloud sql users create $DB_USER --instance=$DB_INSTANCE_NAME --password=$DB_PASSWORD || echo "User exists (or password update failed if exists)"

# Construct DB URL
# Note: For Cloud Run we usually use the connection name, but for Alembic we need a URL.
# We will use the Private IP.
DB_PRIVATE_IP=$(gcloud sql instances describe $DB_INSTANCE_NAME --format="value(ipAddresses[0].ipAddress)")
# Use asyncpg driver for production if needed, or psycopg2. The dockerfile uses psycopg2-binary, so postgresql:// is fine.
DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_PRIVATE_IP:5432/$DB_NAME"

# 5. Redis Setup
echo "⚡ Checking Redis Instance..."
if ! gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION > /dev/null 2>&1; then
    echo "Creating Redis instance..."
    gcloud redis instances create $REDIS_INSTANCE_NAME \
        --size=1 \
        --region=$REGION \
        --redis-version=redis_7_0 \
        --network=$NETWORK
else
    echo "Redis instance $REDIS_INSTANCE_NAME already exists."
fi

REDIS_HOST=$(gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION --format="value(host)")
REDIS_PORT=$(gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION --format="value(port)")
REDIS_URL="redis://$REDIS_HOST:$REDIS_PORT/0"

# 6. Secrets Management
echo "🔒 configuring Secrets..."

create_secret() {
    local name=$1
    local value=$2
    if ! gcloud secrets describe $name > /dev/null 2>&1; then
        echo -n "$value" | gcloud secrets create $name --data-file=-
    else
        echo "Secret $name exists. Updating..."
        echo -n "$value" | gcloud secrets versions add $name --data-file=-
    fi
}

create_secret "inka-database-url" "$DATABASE_URL"
create_secret "inka-redis-url" "$REDIS_URL"

read -p "Enter Telegram Bot Token: " BOT_TOKEN
create_secret "inka-bot-token" "$BOT_TOKEN"

# 7. Build and Deploy API
echo "🔨 Building and Deploying API..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/inka-api . -f apps/api/Dockerfile
gcloud run deploy inka-api \
    --image gcr.io/$PROJECT_ID/inka-api \
    --region $REGION \
    --allow-unauthenticated \
    --set-secrets="DATABASE_URL=inka-database-url:latest,REDIS_URL=inka-redis-url:latest" \
    --set-env-vars="ENVIRONMENT=production" \
    --vpc-connector-args=connector-name=serverless-connector 

# Wait... Cloud Run needs a VPC connector to talk to Private IP SQL/Redis.
# Let's create a VPC connector if it doesn't exist.
echo "Creating Serverless VPC Access Connector..."
if ! gcloud compute networks vpc-access connectors describe inka-connector --region=$REGION > /dev/null 2>&1; then
    gcloud compute networks vpc-access connectors create inka-connector \
        --network $NETWORK \
        --region $REGION \
        --range 10.8.0.0/28
else
    echo "Connector inka-connector exists."
fi

# Re-deploy API with connector
echo "🚀 Deploying API service..."
gcloud run deploy inka-api \
    --image gcr.io/$PROJECT_ID/inka-api \
    --region $REGION \
    --allow-unauthenticated \
    --vpc-connector inka-connector \
    --set-secrets="DATABASE_URL=inka-database-url:latest,REDIS_URL=inka-redis-url:latest" \
    --set-env-vars="ENVIRONMENT=production"

API_URL=$(gcloud run services describe inka-api --region $REGION --format="value(status.url)")
echo "✅ API Deployed at: $API_URL"

# 8. Build and Deploy Admin
echo "🔨 Building and Deploying Admin..."
# Admin needs API_URL at build time or runtime?
# Dockerfile uses NEXT_PUBLIC_API_URL. It's built into the image at build time for static sites usually,
# or used at runtime if using SSR. The dockerfile is nginx (static).
# So we need to pass build-arg.
gcloud builds submit --tag gcr.io/$PROJECT_ID/inka-admin apps/admin \
    --substitutions=_API_URL=$API_URL

# Admin Dockerfile needs to be slightly adjusted to accept ARG if we use Cloud Build substitutions easily,
# OR we just pass it as --build-arg to the docker build command that Cloud Build runs.
# Default cloud build configuration might be tricky with args.
# Let's create a cloudbuild.yaml specifically for admin or just use command line args.
gcloud builds submit apps/admin \
    --tag gcr.io/$PROJECT_ID/inka-admin \
    --build-arg VITE_API_URL=$API_URL

gcloud run deploy inka-admin \
    --image gcr.io/$PROJECT_ID/inka-admin \
    --region $REGION \
    --allow-unauthenticated

ADMIN_URL=$(gcloud run services describe inka-admin --region $REGION --format="value(status.url)")
echo "✅ Admin Deployed at: $ADMIN_URL"

# 9. Build and Deploy Bot
echo "🔨 Building and Deploying Bot..."
# Bot needs webhook URL setup. Usually bot is a polling or webhook.
# If webhook, it needs an endpoint. The code likely handles webhook via API or standalone?
# The dockerfile runs "apps.bot.src.main".
gcloud builds submit --tag gcr.io/$PROJECT_ID/inka-bot . -f apps/bot/Dockerfile

gcloud run deploy inka-bot \
    --image gcr.io/$PROJECT_ID/inka-bot \
    --region $REGION \
    --no-allow-unauthenticated \
    --vpc-connector inka-connector \
    --set-secrets="DATABASE_URL=inka-database-url:latest,REDIS_URL=inka-redis-url:latest,BOT_TOKEN=inka-bot-token:latest" \
    --set-env-vars="ENVIRONMENT=production"

echo "✅ Bot Deployed."

echo "🎉 Deployment Complete!"
echo "API: $API_URL"
echo "Admin: $ADMIN_URL"
echo "Don't forget to set up your Bot Webhook if needed!"
