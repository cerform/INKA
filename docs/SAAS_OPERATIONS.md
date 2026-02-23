# SaaS Deployment & Operations Guide

## 1. Unified Architecture
This platform runs as three core services in Google Cloud Run:
- **`api`**: The shared backend handling all multi-tenant logic.
- **`customer`**: The shared customer portal (bookings, services).
- **`admin`**: The global Control Plane for platform operators.

## 2. Multi-Tenant Resolution
Resolution is handled via Domain/Host:
- **Admin**: `admin.yourapp.com`
- **Customer**: `tenant-slug.yourapp.com` or custom domains.

The backend resolves the `tenant_id` automatically using the `Host` header.

## 3. Secret Management
Secrets (e.g., individual salon's Telegram bot tokens) MUST be stored in Google Secret Manager.
The backend references them using a `secret_ref` field in the tenant configuration.

## 4. Operational Best Practices
- **Health Checks**:
    - `GET /healthz`: Basic liveness
    - `GET /readyz`: Database connectivity
- **DORA Metrics**: Integrated in the Control Plane to monitor velocity and stability.
- **Audit Logs**: Every administrative change is logged in the `audit_log` table with `tenant_id` context.

## 5. Deployment Commands
```bash
# Deploy Shared Backend
gcloud run deploy inka-api --source apps/api

# Deploy Global Control Plane
gcloud run deploy inka-admin --source apps/admin

# Deploy Shared Customer Portal
gcloud run deploy inka-customer --source apps/customer
```

## 6. Creating a New Tenant
1. Access the **Control Plane** at `admin.yourapp.com`.
2. Go to **Fleet View**.
3. Click **Create New Tenant**.
4. Provide name, slug (e.g. `midnight-ink`), and theme colors.
5. The salon is immediately live at `midnight-ink.yourapp.com`.
