# SaaS Control Plane & Multi-Tenant Orchestrator Implementation Plan

## 1. Core Architecture
- **Single Backend**: FastAPI (already in `apps/api`).
- **Single Customer Frontend**: Next.js or Vite (to be created as `apps/customer`).
- **Single Admin Frontend**: Vite + React (repurposing `apps/admin` as Global Control Plane).

## 2. Multi-Tenancy Strategy
- **Isolation**: Shared Database, Shared Schema, enforced by `tenant_id`.
- **Resolution**:
    - Backend: `Host` header -> Tenant Lookup.
    - Frontend: `location.hostname` -> API.
- **Tenant States**: `CREATED`, `ACTIVE`, `SUSPENDED`, `DELETED`.

## 3. Implementation Steps

### Phase 1: Backend Foundations
1. [ ] **Tenant Resolution Middleware**:
    - Implement middleware to extract domain/host.
    - Lookup tenant in DB (cached).
    - Inject `tenant_id` into state/context.
2. [ ] **Global Admin API**:
    - `/admin/tenants`: CRUD for tenants.
    - `/admin/health`: System-wide metrics.
    - `/admin/audit`: Global audit logs.
3. [ ] **Secret Management**:
    - Integrate `SecretManager` for bot tokens (scoped by tenant).

### Phase 2: Global Admin Frontend (Control Plane)
1. [ ] **Fleet Management**:
    - Table view of all salons.
    - Creation wizard (Name, Slug, Type, Theme).
2. [ ] **Tenant Control**:
    - Activate/Suspend buttons.
    - View tenant-specific logs/metrics.
3. [ ] **Impersonation**:
    - Secure "Login as Tenant" functionality.

### Phase 3: Shared Customer Frontend
1. [ ] **Dynamic Branding Engine**:
    - Fetch theme settings from `/v1/tenant/config`.
    - Apply CSS variables dynamically.
2. [ ] **Booking Flow**:
    - Multi-tenant booking system.

### Phase 4: DevOps & Observability
1. [ ] **Structured Logging**:
    - Add `tenant_id` and `correlation_id` to all logs.
2. [ ] **DORA Metrics**:
    - Implement metrics for Deployment Frequency, Lead Time, MTTR, CFR.
3. [ ] **CI/CD Integration**:
    - Unified deployment to Cloud Run.

## 4. Database Schema Updates
- Ensure `tenant` table has:
    - `slug` (unique)
    - `domain` (optional custom domain)
    - `theme_config` (JSON)
    - `status` (Enum)
    - `subscription_plan` (String)

## 5. Security Model
- **Platform Admin**: Can access everything across all tenants.
- **Tenant Owner**: Can access only their own tenant data.
- **Master/Staff**: Limited access within their tenant.
- **Customer**: Read-only services, can create bookings.
