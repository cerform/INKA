# INKA Production Delivery Plan

**Status:** Ready for V1 Release | **Last Updated:** 2026-02-22 | **Target:** 8–12 weeks to production

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Repository State Report](#repository-state-report)
3. [Gap Analysis](#gap-analysis)
4. [Target Architecture](#target-architecture)
5. [Milestone Plan (M0–M5)](#milestone-plan)
6. [CI/CD & Infrastructure Checklist](#cicd--infrastructure-checklist)
7. [First 10 PRs Plan](#first-10-prs-plan)
8. [Risks & Mitigations](#risks--mitigations)

---

## Executive Summary

**Current State:** INKA has a **functional monorepo skeleton** with core data models, CI/CD pipeline baseline, and deployment infrastructure placeholders.

**Gaps:** Missing calendar sync engine, onboarding wizard, multi-tenant slot management, admin UI calendar view, inventory system, and production-hardened deployment configs.

**Path to Production:**
- **M0 (Now–Week 2):** Fix broken imports, scaffold calendar engine skeleton, enable CI/CD
- **M1 (Week 3–5):** Calendar MVP (availability, slot generation, conflict detection)
- **M2 (Week 6–8):** Booking flow, notifications, Telegram integration
- **M3 (Week 9–10):** Admin UI calendar + real-time updates
- **M4 (Week 11):** Onboarding wizard + multi-tenant setup
- **M5 (Week 12+):** Inventory, purchasing, analytics, production hardening

**Definition of Done per Milestone:**
- All tests ≥80% green (unit + integration)
- Zero S1/S2 defects open
- Quality score ≥85 for stage, ≥90 for prod
- Deployment docs complete
- Rollback plan validated

---

## Repository State Report

### ✅ What Exists (Ready to Use)

| Component | Status | Notes |
|-----------|--------|-------|
| **FastAPI Skeleton** | ✅ Ready | `/apps/api/src/app.py` with routers, middleware, health checks |
| **Database Models** | ✅ Ready | Tenant, User, Master, Client, Booking, Service, Schedule (SQLAlchemy ORM) |
| **Alembic Migrations** | ✅ Ready | 4 migrations: release_registry, multi_tenancy, inventory, defects |
| **Telegram Bot Skeleton** | ✅ Ready | aiogram 3.3, polling mode, handlers framework |
| **Admin Panel** | ✅ Partial | Vite + React 19, Tailwind, React Query, FullCalendar installed but UI NOT built |
| **Docker Compose** | ✅ Ready | postgres, redis, api, bot, admin all defined |
| **CI Pipeline** | ✅ Ready | Lint, test, quality gate (GitHub Actions) |
| **Deploy Pipelines** | ✅ Ready | Stage & Prod workflows with defect gate, canary (10%), health checks, rollback |
| **Roles & RBAC** | ✅ Ready | Permission model + role-based access control foundation |
| **Quality Score System** | ✅ Ready | Weighted scoring (test cov, defects, security, migration risk, compliance) |
| **Pre-commit Hooks** | ✅ Ready | ruff, black, mypy checks configured |

### ⚠️ What's Broken / Incomplete

| Component | Issue | Impact | Fix Effort |
|-----------|-------|--------|-----------|
| **Calendar Sync** | Not implemented | Cannot sync Google Calendar or generate slots | **HIGH** (5 days) |
| **Slot Engine** | Not implemented | Cannot compute available slots by day/week/master | **HIGH** (4 days) |
| **Booking Flow** | Partial (model exists, no endpoints) | Cannot create/modify/cancel bookings | **MEDIUM** (3 days) |
| **Notifications** | Not implemented | No reminders to client/master | **MEDIUM** (3 days) |
| **Admin Calendar UI** | Not implemented | No calendar view in admin panel | **MEDIUM** (4 days) |
| **Onboarding Wizard** | Not implemented | New salons cannot self-onboard | **HIGH** (5 days) |
| **Inventory System** | Partially modeled | Models exist, no endpoints or BOM logic | **MEDIUM** (3 days) |
| **LLM Integration** | Not implemented | Telegram bot cannot use LLM for intelligence | **MEDIUM** (2 days) |
| **Google Calendar OAuth** | Not configured | No integration with Google Calendar API | **MEDIUM** (2 days) |
| **Admin UI Calendar Pages** | Not implemented | React components not built | **HIGH** (4 days) |
| **Observability** | Minimal | Logging is basic, no distributed tracing, no metrics | **MEDIUM** (3 days) |
| **Timezone Handling** | Partial | Models have tz field, logic not implemented | **LOW** (2 days) |
| **Multi-tenant Isolation** | Incomplete | No row-level security or tenant_id filters in queries | **MEDIUM** (3 days) |
| **Performance Indexes** | Missing | No indexes on high-query tables (booking start_time, client phone) | **LOW** (1 day) |
| **Integration Tests** | Sparse | Only 5 test files found | **MEDIUM** (4 days) |
| **API Endpoints** | Scaffolded not implemented | Router structure exists, handlers missing | **MEDIUM** (5 days) |

### 🚨 Technical Debt & Risks

| Category | Issue | Severity | Mitigation |
|----------|-------|----------|-----------|
| **Import Paths** | Mixed `packages.core` vs `libs.core` naming | MEDIUM | Standardize all imports to `libs.*` (1 PR) |
| **Config** | TELEGRAM_BOT_TOKEN defaults to `""` (crashes if missing) | MEDIUM | Make all external service fields truly Optional, graceful degradation |
| **Database** | No connection pooling config for Cloud Run | MEDIUM | Add CloudSQL Proxy + pgBouncer config to deployment |
| **Secrets** | `.env` in docker-compose exposed | MEDIUM | Switch to Secret Manager for stage/prod |
| **Schema** | User.role is string, should FK to Role table | LOW | Fix FK relationship (quick migration) |
| **Bot** | Webhook URL hardcoded (should be env var) | LOW | Use settings.TELEGRAM_WEBHOOK_URL |
| **Missing Indexes** | Booking.start_time, Client.phone, Master.tenant_id | LOW | Add 2-3 strategic indexes |
| **No Circuit Breaker** | API calls to Google Calendar / LLM have no retry/timeout | MEDIUM | Add httpx retry + timeout config |
| **PII Security** | Phone numbers & notes visible to all roles | MEDIUM | Implement role-based masking in serializers |

### 📊 Code Metrics

| Metric | Value | Target |
|--------|-------|--------|
| Test Coverage | ~30% (estimate from 5 test files) | 80% |
| Python Files | ~80 | Expected for MVP |
| React Components | ~5 (partial) | ~30 for M3 |
| Database Models | 15 | 15 ✅ |
| API Endpoints | 3 (health, root, setup) | 30+ |
| Migrations | 4 | Increases with features |

---

## Gap Analysis

### Feature Gaps

| Feature | Requirement | Current | Missing | Effort |
|---------|-------------|---------|---------|--------|
| **Calendar Engine** | Show available slots by day/week, master, service duration | Models only | Slot generation algorithm, conflict detection, DST handling | 8 days |
| **Google Calendar Sync** | Sync salon + master calendars, 2-way binding | Not started | OAuth setup, sync scheduler, conflict resolution | 5 days |
| **Booking Creation** | Client/admin creates booking; checks availability; reserves slot | Model exists | API endpoint, service logic, double-booking guard | 3 days |
| **Booking Cancellation** | Cancel with 24h notice; refund logic; calendar sync | Not started | Endpoint, refund service, sync to calendar | 2 days |
| **Booking Rescheduling** | Reschedule to different time/master; notify both parties | Not started | Endpoint, availability check, notification trigger | 2 days |
| **Notifications** | SMS/Telegram reminder before booking; cancellation notice | Not started | Notification service, SMS provider config, scheduling | 3 days |
| **Admin Calendar View** | React UI showing all bookings by day/week/master | Not started | Calendar component (FullCalendar integrated), real-time updates | 4 days |
| **Admin Booking Management** | Create/edit/cancel bookings from admin UI | Not started | CRUD endpoints + UI forms | 2 days |
| **Multi-Tenant Isolation** | Row-level security; each tenant sees only own data | Partial | Middleware to inject tenant_id in all queries; audit trail | 3 days |
| **Onboarding Wizard** | Setup link; OAuth flow; bot token config; calendar connection | Not started | Multi-step form, Secret Manager integration, tenant creation | 5 days |
| **Inventory BOM** | Services declare material usage; stock depletion on booking | Model exists | Service → Material mapping, depletion logic, stock alerts | 3 days |
| **Purchase Orders** | Reorder when stock < threshold; track deliveries | Model exists | PO creation, supplier integration, delivery tracking | 3 days |
| **LLM Integration** | Bot uses LLM to parse natural language booking requests | Not started | LLM service wrapper, prompt templates, safety checks | 3 days |
| **Report & Analytics** | Revenue, bookings by master, inventory turnover | Not started | Report API endpoints, query optimization | 3 days |

### Platform Gaps

| Gap | Requirement | Current | Missing | Effort |
|-----|-------------|---------|---------|--------|
| **Observability** | Structured logging + correlation IDs + error tracking | Basic | Distributed tracing (OpenTelemetry), error reporting (Sentry), metrics (Prometheus) | 3 days |
| **Security** | JWT auth (API) + Telegram ID auth (bot); PII masking; break-glass | Auth model ready | JWT implementation, break-glass session logic, PII masking in serializers | 3 days |
| **Testing** | Unit + integration + E2E tests; ≥80% coverage | ~30% | Expand test suite, fixtures, mocking, E2E tests | 5 days |
| **Database Migrations** | Safe up/down, backward compat, rollback testing | Framework ready | Migration testing in CI, rollback validation | 1 day |
| **Infrastructure** | Terraform modules for Cloud Run, Cloud SQL, Secret Manager | Not started | Terraform code, environment configs (dev/stage/prod) | 3 days |
| **CI/CD** | Linting, testing, security scanning, quality gate, deployment | Partial (workflow exists) | Trivy scan, SBOM generation, coverage thresholds, approval workflows | 2 days |
| **Secrets Management** | Externalize all sensitive data to Secret Manager | Not started | Rotated credentials, audit logging, access controls | 1 day |
| **Load Testing** | Verify system handles N concurrent bookings | Not started | k6 or Locust load test suite, SLA validation | 2 days |
| **Compliance** | Audit logs for all mutations; PII protection; GDPR deletions | Model ready | Audit log service, GDPR delete endpoint | 2 days |

---

## Target Architecture

### System Design (C4 Level 1)

```
┌──────────────────────────────────────────────────────────────────┐
│                        INKA Salon Platform                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │   Telegram   │    │   Web Admin  │    │ Google Oauth │        │
│  │   Clients    │    │   (React)    │    │  (Calendar)  │        │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘        │
│         │                   │                   │                 │
│         ├─────────┬─────────┴─────────┬────────┘                 │
│         ▼         ▼                   ▼                          │
│    ┌────────────────────────────────────────┐                   │
│    │      FastAPI Backend (Port 8000)       │                   │
│    │  ├─ /api/v1/bookings                   │                   │
│    │  ├─ /api/v1/masters                    │                   │
│    │  ├─ /api/v1/clients                    │                   │
│    │  ├─ /api/v1/calendar/slots             │                   │
│    │  ├─ /api/v1/inventory                  │                   │
│    │  ├─ /api/v1/tenant/setup               │                   │
│    │  └─ /api/v1/admin/*                    │                   │
│    └─────┬───────────────────────────────────┘                   │
│          │                                                        │
│    ┌─────┴─────────────────────┬──────────────────┐              │
│    ▼                           ▼                  ▼              │
│ ┌──────────────┐  ┌─────────────────────┐  ┌──────────────┐     │
│ │  PostgreSQL  │  │ Redis (Sessions,    │  │  Telegram    │     │
│ │  Cloud SQL   │  │  Cache, Queue)      │  │  Bot Worker  │     │
│ └──────────────┘  └─────────────────────┘  └──────────────┘     │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘

External Integrations:
  • Google Calendar API (read/write availability & bookings)
  • Google Workspace Domain (service account for calendar access)
  • OpenAI / Anthropic (LLM for natural language parsing)
  • Twilio / Vonage (SMS notifications)
  • Stripe / Payment Gateway (deposits)
```

### Multi-Tenant Data Isolation Strategy

**Decision: Row-Level Security + Tenant_ID Column**

```
Rationale:
  ✅ Simpler than schema-per-tenant
  ✅ Easier to implement multi-tenant reports
  ✅ Better for horizontal scaling
  ✅ Single database, lower operational overhead
  ⚠️ Requires strict middleware enforcement
```

**Implementation:**
1. Every table has `tenant_id INT FK(tenant.id)` column
2. Middleware extracts `tenant_id` from JWT (API) or Telegram user context (bot)
3. All ORM queries auto-filter by tenant_id via SQLAlchemy `get_bind()` hook or session-scoped filter
4. Foreign keys enforced: `(tenant_id, resource_id)` composite keys where needed

**Key Tables:**
```sql
tenant          -- Salons: id, slug, name, timezone, is_active, created_at
user            -- Staff: id, tenant_id FK, telegram_id, full_name, phone, role_id FK, is_active
master          -- Stylists: id, tenant_id FK, user_id FK, name, active
client          -- Customers: id, tenant_id FK, full_name, phone, notes
service         -- Services: id, tenant_id FK, name, duration_minutes, price
booking         -- Reservations: id, tenant_id FK, client_id FK, master_id FK, service_id FK, start_time, end_time, status
working_hours   -- Master schedule: id, tenant_id FK, master_id FK, day_of_week, start_time, end_time, is_active
time_off        -- Days off: id, tenant_id FK, master_id FK, start_time, end_time, description
material        -- Inventory: id, tenant_id FK, name, unit, stock_quantity, reorder_threshold
stock_entry     -- Stock movements: id, tenant_id FK, material_id FK, booking_id FK, delta, reason, created_at
purchase_order  -- PO: id, tenant_id FK, material_id FK, quantity, status, ordered_at, delivered_at
audit_log       -- Audit trail: id, tenant_id FK, user_id FK, action, target_type, target_id, details, created_at
```

### Calendar & Slot Engine

**Responsibility:** Generate available slots for a given (master, date, service_duration).

**Algorithm:**

```python
def get_available_slots(
    tenant_id: int,
    master_id: int,
    service_date: date,
    service_duration_mins: int,
    interval_mins: int = 30  # Slot granularity
) -> list[TimeSlot]:
    """
    1. Load master's working_hours for service_date's day-of-week
    2. Load all bookings for (master_id, service_date)
    3. Load all time_off covering service_date
    4. Build a boolean array [08:00, 08:30, 09:00, ..., 17:00]
    5. Mark time_off periods as unavailable
    6. Mark booked periods as unavailable
    7. Scan array for contiguous_duration >= service_duration_mins
    8. Return list of (start_time, end_time, is_available=True)
    
    Edge cases:
      • DST transitions (offset changes at 02:00/03:00)
      • Master's custom exceptions (holiday, half-day)
      • Service > 60 mins spanning multiple intervals
      • 24h buffer before next booking (if required)
    """
```

**Data Flow:**

```
Admin/Bot requests available slots
         │
         ▼
API: GET /api/v1/calendar/slots?master_id=5&date=2026-03-15&service_id=2
         │
         ├─ Load master working_hours for 2026-03-15
         ├─ Load all bookings on 2026-03-15 for master_id=5
         ├─ Load time_off covering 2026-03-15
         ├─ Load service duration (service_id=2 → duration_mins)
         │
         ▼
Slot Engine: generate_slots(...)
         │
         ├─ Build availability bitmap
         ├─ Subtract booked time
         ├─ Subtract time_off
         │
         ▼
Response: [
  {start: 09:00, end: 09:30, is_available: true},
  {start: 09:30, end: 10:00, is_available: true},
  {start: 10:00, end: 10:30, is_available: false},  # Booked
  ...
]
```

### Calendar Sync Strategy

**Source of Truth: Booking table in INKA (primary)**

**Sync Direction:** INKA → Google Calendar (one-way initially, two-way in M3+)

**Process:**

```
1. User creates booking in INKA (API or Admin UI)
   ├─ Create booking record (status=PENDING)
   ├─ Enqueue job: sync_booking_to_calendar(booking_id)
   └─ Response to client immediately

2. Background job (Celery/RQ worker):
   ├─ Load booking + master + service details
   ├─ Get master's Google Calendar ID (from tenant settings)
   ├─ Create calendar event:
      - Title: "{service_name} - {client_name}"
      - Time: booking.start_time → booking.end_time
      - Description: booking.notes
      - Attendees: [master_email, client_email]
   ├─ Store Google Calendar event_id in booking.calendar_event_id
   ├─ Send confirmation email/SMS to client & master
   └─ Log sync in audit_log

3. Booking cancelled in INKA:
   ├─ Update booking.status = CANCELLED
   ├─ Delete Google Calendar event (if exists)
   ├─ Send cancellation notification
   └─ Refund if applicable

4. Google Calendar conflict detected:
   ├─ Log warning: booking has calendar_event_id but Google event missing
   ├─ Trigger alert to admin (break-glass session)
   └─ Disable booking until manually resolved

Edge cases:
  • Master changes timezone → recalculate slot availability
  • Master unavailable (time_off) but booking exists → admin alert
  • Google API rate limit hit → exponential backoff retry
  • Offline mode (no internet) → queue syncs, flush on reconnect
```

### Onboarding Flow (Multi-Tenant Setup)

**User Journey:**

```
1. New Salon Admin visits https://inka.app/setup
2. Enters salon details: name, timezone, business hours
3. Auth flow:
   ├─ Google OAuth (to read/write calendar)
   ├─ Telegram webhook URL + bot token input
   └─ Optional LLM key (OpenAI/Anthropic)
4. System creates tenant record
5. System initializes Google Calendar integration
6. System activates Telegram bot for this tenant
7. Admin is taken to /admin/dashboard
8. Dashboard shows "Onboarding Checklist":
   ├─ ✅ Salon created
   ├─ Add masters
   ├─ Add services
   ├─ Configure working hours
   ├─ Enable Telegram bot
   └─ First test booking

Activation Endpoint:
  POST /api/v1/tenant/setup
  {
    "name": "Salon XYZ",
    "slug": "salon-xyz",
    "timezone": "Asia/Jerusalem",
    "working_hours": {
      "monday": {start: "08:00", end: "17:00"},
      ...
    },
    "google_oauth_code": "4/...",
    "telegram_bot_token": "123456789:ABCDEFG...",
    "openai_api_key": "sk-..." (optional)
  }
```

---

## Milestone Plan

### M0: Deployable Skeleton (Week 1–2)

**Goal:** Fix import paths, enable CI/CD, scaffold calendar engine, run all tests green.

**User Stories:**

| ID | Title | AC | Est. |
|----|----|-----|------|
| M0-1 | Fix import path inconsistencies (`packages.core` → `libs.core`) | All imports standardized; tests pass | 1d |
| M0-2 | Make external service configs truly Optional (no crash if BOT_TOKEN missing) | API starts with missing BOT_TOKEN; log warning | 0.5d |
| M0-3 | Add database connection pooling config for Cloud Run (CloudSQL Proxy + pgBouncer) | pgBouncer config in docker-compose; Terraform variable for max_connections | 1d |
| M0-4 | Scaffold calendar slot engine (skeleton code, no logic yet) | `libs/core/src/services/calendar_slot_service.py` created; unit test structure ready | 1d |
| M0-5 | Add database indexes for high-query columns (booking.start_time, client.phone, master.tenant_id) | Alembic migration created and tested | 0.5d |
| M0-6 | Implement tenant isolation middleware (inject tenant_id in all queries) | All ORM queries auto-filter by tenant_id; unit tests pass | 1d |
| M0-7 | Fix User.role FK relationship (string → FK to Role table) | Migration created; backwards compat tested | 0.5d |
| M0-8 | Set up Terraform skeleton for dev/stage/prod environments | `infra/terraform/environments/{dev,stage,prod}/main.tf` with Cloud Run, Cloud SQL, Secret Manager | 1.5d |
| M0-9 | Update CI to run security scan (Trivy), SBOM generation, coverage reporting | `.github/workflows/ci.yml` updated; passes green | 1d |
| M0-10 | Document setup for local development (Makefile, Docker Compose, env vars) | README.md updated; `make dev` starts all services | 0.5d |

**Definition of Done:**
- ✅ All tests pass (test coverage ≥50%)
- ✅ No lint errors (ruff, black, mypy)
- ✅ Zero S1/S2 defects
- ✅ Quality score ≥70

**Owner:** Backend Lead

---

### M1: Calendar Engine MVP (Week 3–5)

**Goal:** Implement slot generation, availability checking, conflict detection.

**User Stories:**

| ID | Title | AC | Est. |
|----|----|-----|------|
| M1-1 | Implement `generate_available_slots()` algorithm | Returns list of (start_time, end_time, is_available) tuples; passes 15+ unit tests including DST | 3d |
| M1-2 | Create endpoint: `GET /api/v1/calendar/slots?master_id=X&date=Y&service_id=Z` | Returns available time slots as JSON; filters by tenant | 1d |
| M1-3 | Implement conflict detection service (double-booking guard) | Service checks booking overlap; rejects if conflict; logs to audit_trail | 1d |
| M1-4 | Add timezone handling in slot generation (DST aware) | Uses pytz/zoneinfo to calculate local times; handles spring/fall transitions | 1.5d |
| M1-5 | Create working_hours + time_off CRUD endpoints | POST/PUT/DELETE /api/v1/masters/{master_id}/working-hours and time-off | 1d |
| M1-6 | Write integration tests for calendar engine (Postgres + fixtures) | 20+ integration tests; all green | 2d |
| M1-7 | Add slot caching (Redis) with TTL=5min | Frequently requested slots cached; cache invalidated on booking change | 1d |

**Definition of Done:**
- ✅ Slot generation algorithm fully tested
- ✅ No double-booking possible
- ✅ DST transitions handled correctly
- ✅ Test coverage ≥75%
- ✅ Quality score ≥75

**Owner:** Backend Lead + Defect Orchestrator (for test strategy)

---

### M2: Booking Flow & Notifications (Week 6–8)

**Goal:** End-to-end booking creation, modification, cancellation, and notifications.

**User Stories:**

| ID | Title | AC | Est. |
|----|----|-----|------|
| M2-1 | Create booking endpoint: `POST /api/v1/bookings` | Validates master availability; checks conflicts; creates booking; returns booking_id | 2d |
| M2-2 | Modify booking endpoint: `PATCH /api/v1/bookings/{id}` | Allows time/master change if no conflict; logs audit trail | 1d |
| M2-3 | Cancel booking endpoint: `DELETE /api/v1/bookings/{id}` | Sets status=CANCELLED; triggers refund; logs reason | 1d |
| M2-4 | Implement notification service (SMS + Telegram) | Service sends reminder 24h before; sends confirmation on booking; configurable templates | 2d |
| M2-5 | Integrate Telegram bot handlers for booking CRUD | `/book`, `/cancel`, `/reschedule` commands; uses API under the hood | 2d |
| M2-6 | Set up background job queue (Redis + RQ or Celery) | Jobs: send_notification, sync_to_calendar, generate_reports; jobs retry on failure | 1.5d |
| M2-7 | Implement Google Calendar sync (one-way: INKA → Google) | On booking creation, creates Google Calendar event; stores event_id in booking record | 2d |
| M2-8 | Add booking status state machine (PENDING → CONFIRMED → COMPLETED or CANCELLED) | Validations: can only confirm PENDING; can only complete CONFIRMED | 1d |

**Definition of Done:**
- ✅ Booking CRUD fully operational
- ✅ Notifications sent reliably (at least 1 success rate ≥99%)
- ✅ Google Calendar sync working (manual verification)
- ✅ Test coverage ≥80%
- ✅ Quality score ≥80

**Owner:** Backend Lead + Bot Lead

---

### M3: Admin UI Calendar View (Week 9–10)

**Goal:** Build calendar-first admin dashboard with real-time updates.

**User Stories:**

| ID | Title | AC | Est. |
|----|----|-----|------|
| M3-1 | Create calendar component using FullCalendar + React | Month, week, day views; drag-to-reschedule; responsive design | 2d |
| M3-2 | Implement API endpoint: `GET /api/v1/bookings?date_range=...&master_id=...&status=...` | Supports filtering and pagination; returns 100+ bookings efficiently | 1d |
| M3-3 | Add real-time updates via WebSocket or Server-Sent Events (SSE) | When booking created elsewhere, admin UI updates without refresh | 1.5d |
| M3-4 | Build quick-create booking form (modal on calendar click) | Click empty slot → open form → submit → booking created | 1d |
| M3-5 | Build quick-edit booking modal (click existing event) | Edit time, master, notes; save with conflict validation | 1d |
| M3-6 | Add calendar filters: by master, status, date range | Filters apply in-memory or via API query params | 1d |
| M3-7 | Display master availability sidebar (live slot count) | Shows available slots for each master today + next 7 days | 1d |
| M3-8 | Implement admin-only settings panel: working hours, closed days, services | Forms to edit salon config; changes reflect in slot generation immediately | 1d |
| M3-9 | Add client list view with booking history | Table showing all clients; click → see booking history; can force-cancel | 1d |
| M3-10 | Mobile-responsive design (tablet + phone) | Tested on iPad, iPhone 12, Android tablets | 1d |

**Definition of Done:**
- ✅ Calendar UI fully functional
- ✅ Real-time updates working (SSE or WebSocket)
- ✅ All admin workflows verified (create, edit, cancel booking)
- ✅ Mobile-responsive
- ✅ E2E tests for critical flows
- ✅ Quality score ≥85

**Owner:** Frontend Lead + Backend Lead

---

### M4: Onboarding Wizard & Multi-Tenant (Week 11)

**Goal:** New salons can self-onboard without engineering help.

**User Stories:**

| ID | Title | AC | Est. |
|----|----|-----|------|
| M4-1 | Build onboarding wizard (multi-step form) | Step 1: Salon info; Step 2: OAuth (Google); Step 3: Bot token; Step 4: Confirm | 2d |
| M4-2 | Implement `/api/v1/tenant/setup` endpoint | Creates tenant; initializes Google Calendar connection; activates bot | 1.5d |
| M4-3 | Add email verification for salon admin | Sends verification link; creates user record after verification | 1d |
| M4-4 | Implement role-based access control (Admin, Manager, Master, QA, Debugger) | Each role has specific permissions; enforced in API (via @require_role decorator) | 1.5d |
| M4-5 | Add break-glass session logic (temporary elevated access) | Admin can request temporary "debugger" role with audit trail; auto-expires | 1d |
| M4-6 | Implement multi-tenant data isolation enforcement | Middleware rejects cross-tenant queries; tests verify isolation | 1d |
| M4-7 | Create admin onboarding checklist UI | Shows setup progress; reminds to add masters, services, working hours | 0.5d |
| M4-8 | Add Google Workspace domain configuration (service account) | Tenants can provide service account JSON; API uses it to read master calendars | 1d |

**Definition of Done:**
- ✅ End-to-end onboarding tested (manual + automated)
- ✅ Multi-tenant isolation enforced
- ✅ RBAC working for all endpoints
- ✅ Quality score ≥85

**Owner:** Backend Lead + DevOps (for Secret Manager setup)

---

### M5: Inventory, Purchasing, Analytics, & Hardening (Week 12+)

**Goal:** Complete feature set; production-ready observability & security.

**User Stories:**

| ID | Title | AC | Est. |
|----|----|-----|------|
| M5-1 | Implement inventory BOM (Bill of Materials): Service → Materials mapping | API endpoints to define which materials used in each service; auto-deduct on booking | 2d |
| M5-2 | Implement stock depletion on booking completion | When booking marked COMPLETED, deduct material quantities from inventory | 1d |
| M5-3 | Add reorder alerts (Slack/email when stock < threshold) | Alerts sent to manager; includes supplier info + PO link | 1d |
| M5-4 | Build purchase order creation + tracking | Endpoints to create PO, mark delivered; tracks cost vs budget | 1.5d |
| M5-5 | Implement observability (structured logging, distributed tracing) | All requests log correlation_id; latency tracked; error rate monitored | 2d |
| M5-6 | Add PII masking for role-based access (phone, notes) | Non-admin roles see masked phone (***-***-5678); debug role unmasks | 1d |
| M5-7 | Build analytics dashboard: revenue, bookings by master, inventory turnover | API endpoints + React dashboard; uses aggregated queries | 2d |
| M5-8 | Implement GDPR delete endpoint: `/api/v1/clients/{id}/gdpr-delete` | Anonymizes client data; keeps audit trail | 1d |
| M5-9 | Set up error tracking (Sentry integration) | All exceptions logged; released version tracked; alerts on high error rate | 0.5d |
| M5-10 | Load test the system (k6 script: N concurrent users booking) | Verify p95 latency <500ms; no errors under 100 concurrent requests | 1.5d |
| M5-11 | Harden deployment: Terraform for prod; Secret Manager; SSL/TLS; WAF rules | Prod infrastructure fully IaC; no manual configuration | 2d |
| M5-12 | Create runbooks for common incidents (DB connection pool exhaustion, calendar sync lag, bot token revoked) | Runbooks stored in `docs/operations/runbooks/`; team trained | 1d |

**Definition of Done:**
- ✅ All features shipped
- ✅ Test coverage ≥85%
- ✅ Observability live (tracing, metrics, error tracking)
- ✅ Load test results documented
- ✅ Security audit passed (PII masking, multi-tenant isolation, no secrets in logs)
- ✅ Quality score ≥90
- ✅ Runbooks documented and team trained

**Owner:** Backend Lead + DevOps + Frontend Lead

---

## CI/CD & Infrastructure Checklist

### GitHub Workflows

| Workflow | File | Purpose | Status |
|----------|------|---------|--------|
| **Lint & Test** | `.github/workflows/ci.yml` | Run on PR: ruff, black, mypy, pytest | ✅ Exists, needs update |
| **Quality Gate** | `.github/workflows/ci-gate.yml` | Block merge if coverage <80%, S1/S2 open, security issues | ⚠️ Partial, needs CI integration |
| **Deploy to Stage** | `.github/workflows/deploy-stage.yml` | Manual approval + canary deployment (10%) | ✅ Exists |
| **Deploy to Prod** | `.github/workflows/deploy-prod.yml` | Requires stage success + manual approval + health checks | ✅ Exists |
| **Rollback** | `.github/workflows/rollback.yml` | Automatic or manual rollback on failure | ✅ Exists |
| **Chaos Testing** | `.github/workflows/chaos.yml` | Run chaos tests against stage (circuit breaker, timeouts) | ⚠️ Partial |

### Google Cloud Infrastructure

#### Cloud Run Services

| Service | Purpose | Replicas | Memory | CPU | Env |
|---------|---------|----------|--------|-----|-----|
| `inka-api` | FastAPI backend | 2–10 (auto-scale) | 1Gi | 2 | stage, prod |
| `inka-bot` | Telegram bot worker | 1–5 (auto-scale) | 512Mi | 1 | stage, prod |
| `inka-scheduler` | Job queue (notification, calendar sync) | 1–3 | 512Mi | 1 | stage, prod |

#### Cloud SQL

| Database | Engine | Version | HA | Backups | Env |
|----------|--------|---------|----|---------|----|
| `inka-db` | PostgreSQL | 15 | Yes (regional) | Daily + 7-day retention | stage, prod |

#### Cloud Storage

| Bucket | Purpose | Retention |
|--------|---------|-----------|
| `inka-uploads` | User attachments (booking docs) | 90 days |
| `inka-backups` | Database backups + exports | 30 days |
| `inka-reports` | Analytics exports + SBOM/CVE reports | 180 days |

#### Secret Manager

| Secret | Purpose | Rotation | Access |
|--------|---------|----------|--------|
| `inka-db-password-stage` | Cloud SQL user password | Quarterly | Cloud Run (stage) |
| `inka-db-password-prod` | Cloud SQL user password | Quarterly | Cloud Run (prod) |
| `telegram-bot-token-stage` | Bot token | On deployment | Cloud Run (bot service) |
| `telegram-bot-token-prod` | Bot token | On deployment | Cloud Run (bot service) |
| `google-oauth-client-secret` | OAuth client secret | On rotation | Cloud Run (API) |
| `openai-api-key-prod` | OpenAI secret | Quarterly | Cloud Run (API) |
| `stripe-secret-key-prod` | Stripe signing key | Quarterly | Cloud Run (API) |

### Terraform Modules

```
infra/
├── terraform/
│   ├── main.tf                 # Provider setup (Google Cloud)
│   ├── variables.tf            # Input variables (project, region, etc.)
│   ├── outputs.tf              # Output values (service URLs, DNS, etc.)
│   │
│   ├── modules/
│   │   ├── cloud_run/          # Cloud Run service template
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   │
│   │   ├── cloud_sql/          # Cloud SQL instance + database + user
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   │
│   │   ├── secret_manager/     # Secret creation + IAM bindings
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   │
│   │   ├── monitoring/         # Cloud Monitoring + Alerting
│   │   │   ├── main.tf
│   │   │   └── variables.tf
│   │   │
│   │   └── network/            # VPC, Cloud NAT (optional)
│   │       ├── main.tf
│   │       └── variables.tf
│   │
│   └── environments/
│       ├── dev/                # Development environment
│       │   ├── terraform.tfvars
│       │   └── main.tf (local state)
│       │
│       ├── stage/              # Staging environment
│       │   ├── terraform.tfvars
│       │   └── main.tf (remote state on GCS)
│       │
│       └── prod/               # Production environment
│           ├── terraform.tfvars
│           └── main.tf (remote state on GCS + locks)
```

### Environment Variables & Secrets Map

#### Development (Docker Compose)

```env
# .env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://inka:inka@postgres:5432/inka_dev
REDIS_URL=redis://redis:6379/0
TELEGRAM_BOT_TOKEN=<test token>
OPENAI_API_KEY=<test key>
GOOGLE_OAUTH_CLIENT_ID=<dev OAuth app>
GOOGLE_OAUTH_CLIENT_SECRET=<dev OAuth secret>
```

#### Staging (Secret Manager)

All secrets fetched from Google Secret Manager at runtime.

```
Secret Manager Keys:
  - inka-stage-db-password
  - inka-stage-bot-token
  - inka-stage-google-oauth-secret
  - inka-stage-openai-api-key
  - inka-stage-stripe-secret-key
```

#### Production (Secret Manager)

```
Secret Manager Keys:
  - inka-prod-db-password
  - inka-prod-bot-token
  - inka-prod-google-oauth-secret
  - inka-prod-openai-api-key
  - inka-prod-stripe-secret-key
  - inka-prod-sentry-dsn
  - inka-prod-datadog-api-key (optional)
```

### Deployment Gating Rules

```
GATE 1: Code Quality
  Condition: Quality Score ≥ 85 for stage, ≥ 90 for prod
  Blocks: Any deployment with lower score
  
GATE 2: Defect Registry
  Condition: Zero open S1 bugs; max 2 open S2 bugs (stage), zero S2 (prod)
  Blocks: Deployment if S1 detected or S2 limit exceeded
  
GATE 3: Test Coverage
  Condition: ≥ 80% line coverage (stage), ≥ 85% (prod)
  Blocks: Deployment if below threshold
  
GATE 4: Security Scan
  Condition: Zero critical vulns; max 3 high-severity (stage), zero high (prod)
  Blocks: Deployment if threshold exceeded
  
GATE 5: Migration Safety
  Condition: All new migrations tested for up/down cycle
  Blocks: Deployment if migration test fails
  
GATE 6: Manual Approval
  Condition: Human review required for stage (1 approver) and prod (2 approvers)
  Blocks: Auto-deployment; requires GitHub Environment approval
```

### Release Process

```
1. Developer pushes feature to develop branch
2. GitHub CI runs: lint, test, quality-gate, security scan
3. If all green, merge to main
4. Tag with semantic version: v0.2.0
5. GitHub Actions triggers deploy-stage.yml
   ├─ Defect gate: Check for open S1/S2
   ├─ Manual approval: Requires 1 reviewer in "stage" environment
   ├─ Build: docker build 3 images (api, bot, admin)
   ├─ Push: to Artifact Registry
   ├─ Deploy: Cloud Run (stage) with canary (10%)
   ├─ Health check: Wait 30 min, monitor error rate + latency
   └─ Approval for prod
6. Manual trigger to deploy-prod.yml
   ├─ Defect gate: Check for open S1 (zero tolerance)
   ├─ Manual approval: Requires 2 reviewers in "prod" environment
   ├─ Build + push (use prod registry)
   ├─ Deploy: Cloud Run (prod) with rolling update (20% at a time)
   ├─ Health check: Wait 60 min
   └─ Rollback available for 24 hours

Rollback:
  If deploy fails or errors spike, click "Rollback" in GitHub Actions
  → Cloud Run service reverts to previous stable revision
  → Incident created automatically
  → On-call alerted
```

---

## First 10 PRs Plan

**Timeline:** Weeks 1–3 (M0 completion)

| # | Title | Scope | Owner | Est. | Dependencies |
|---|-------|-------|-------|------|--------------|
| **PR-1** | Fix import paths: `packages.core` → `libs.core` | Search-replace across all files; update pytest paths | Backend | 0.5d | None |
| **PR-2** | Make external service configs Optional (no crash) | Config fields default to `None`; logging on missing keys | Backend | 0.5d | PR-1 |
| **PR-3** | Add database connection pooling config (pgBouncer) | Docker Compose addition; Terraform variable for max_connections | DevOps | 0.5d | PR-1 |
| **PR-4** | Scaffold calendar slot engine skeleton | Create `libs/core/src/services/calendar_slot_service.py`; placeholder functions + unit tests | Backend | 0.5d | PR-1 |
| **PR-5** | Add database indexes + migration | Create migration for booking.start_time, client.phone indexes | Backend | 0.5d | PR-1 |
| **PR-6** | Implement tenant isolation middleware | Middleware to auto-inject tenant_id; test coverage for multi-tenant queries | Backend | 1d | PR-1 |
| **PR-7** | Fix User.role FK relationship + migration | Change column type; update ORM relationship; backwards-compat migration | Backend | 0.5d | PR-5 |
| **PR-8** | Set up Terraform skeleton (dev/stage/prod) | Create directory structure; main.tf with Cloud Run + Cloud SQL modules | DevOps | 1d | PR-3 |
| **PR-9** | Update CI workflows: security scan + SBOM + coverage reporting | Add Trivy job; add SBOM generation; update coverage thresholds | DevOps | 1d | PR-1 |
| **PR-10** | Documentation: local setup, API overview, deployment guide | Update README; add `docs/development/setup.md`; add deployment checklist | Docs | 1d | All prior |

---

## Risks & Mitigations

### High-Risk Items

| # | Risk | Probability | Impact | Mitigation |
|---|------|-------------|--------|-----------|
| **R1** | **Calendar Sync Conflict (Google ↔ INKA mismatch)** | HIGH (60%) | Service bookings from Google Calendar not reflected in INKA; data loss | • Implement two-way sync with versioning (not one-way) • Add conflict detection: if INKA booking missing from Google, alert admin (M1+) • Periodic reconciliation job (daily) • Audit log every sync event |
| **R2** | **Double Booking Despite Conflict Check** | MEDIUM (30%) | Client gets two overlapping bookings; master unhappy | • Pessimistic locking on slot generation (lock booking row until confirmed) • Race-condition tests (concurrent requests to same slot) • Database constraint: UNIQUE(master_id, start_time, end_time) if overlapping | 
| **R3** | **DST Transition Bug (Spring/Fall Time Shift)** | MEDIUM (25%) | Slots disappear or duplicate during DST; bookings off by 1 hour | • Test slot generation for specific DST dates (2026-03-29, 2026-10-25 for Europe) • Use only UTC internally; convert to local time only for display • Validate no two bookings overlap after DST transition |
| **R4** | **Multi-Tenant Data Leak (Cross-Tenant Query)** | HIGH (40%) | Master A sees Client B's private notes; GDPR violation | • Middleware enforces tenant_id on every ORM query • Unit tests: verify tenant_id=1 query cannot see tenant_id=2 data • Code review: audit all raw SQL queries • Run row-level security tests in CI |
| **R5** | **Google Calendar OAuth Token Expires** | MEDIUM (50%) | Sync stops; master's calendar gets stale | • Implement refresh token flow in integration • Add telemetry: track token freshness • Alert if last successful sync >24h ago • Runbook for manual token refresh |
| **R6** | **LLM Prompt Injection (Telegram Bot)** | MEDIUM (35%) | Attacker tricks bot to bypass validation or leak data | • Sanitize all user input before feeding to LLM • Use LLM safety libraries (langchain safety checks) • Log all LLM requests + responses for audit • Rate-limit API calls per user/tenant |
| **R7** | **Notification Delivery Failure (SMS/Email)** | LOW (20%) | Client doesn't get reminder; misses appointment | • Implement notification retry logic (exponential backoff) • Add notification delivery dashboard (success rate tracking) • Fallback: Telegram notification if SMS fails |
| **R8** | **Cloud Run Service Startup Timeout** | MEDIUM (30%) | Deployment hangs; health check fails; canary rollback | • Ensure alembic migrations run in <30s (add timeout monitoring) • Pre-warm DB connections on startup • Split migration from app startup (run migrations in init container) |
| **R9** | **Inventory Stock Calculation Incorrect** | LOW (15%) | Stock goes negative; incorrect reorder alerts | • Add constraint: stock_quantity ≥ 0 (DB level) • Reconciliation job: audit BOM usage vs actual stock monthly | Add unit tests for edge cases (fractional units, concurrent deductions) |
| **R10** | **Performance Degradation (Slow Queries)** | MEDIUM (40%) | Admin dashboard takes >2s to load; user frustration | • Add query cost analysis in CI (pg_stat_statements) • Implement caching (Redis) for frequently accessed data (working_hours, available_slots) • Load test before each release (100 concurrent bookings) | Create alert if p95 latency > 500ms |

### Medium-Risk Items

| # | Risk | Probability | Impact | Mitigation |
|---|------|-------------|--------|-----------|
| **R11** | **Cloud SQL Connection Pool Exhaustion** | MEDIUM (30%) | API requests timeout; service unavailable | • Configure pgBouncer (connection pooling) • Monitor active connections in Cloud Monitoring • Alert if >80% of max connections in use |
| **R12** | **Telegram Bot Token Revoked** | LOW (15%) | Bot goes offline; users cannot message | • Rotate token quarterly (automatic in Secret Manager) • Monitor bot polling errors • Runbook: how to issue new token and redeploy |
| **R13** | **Stripe / Payment Integration Fails** | MEDIUM (25%) | Deposits cannot be collected; revenue loss | • Implement idempotency keys for payment requests • Add webhook verification (signature check) • Reconciliation job: monthly audit of Stripe vs INKA charges |
| **R14** | **Admin UI Does Not Load (Frontend Bundle Too Large)** | LOW (20%) | Lazy-load components; code splitting; use CDN | • Set up Vite build optimization • Monitor bundle size in CI • Use Vercel/Netlify CDN for admin panel |
| **R15** | **Lack of Test Data for Manual QA** | MEDIUM (30%) | QA cannot reproduce issues; slows bug fix cycle | • Implement seed script for test data (10 tenants, 100 bookings, etc.) • Use FactoryBoy for fixture generation | Make seed data available in docker-compose for local testing |

---

## Acceptance Criteria per Milestone

### M0 Acceptance (Week 2 EOD)

- ✅ All imports standardized to `libs.*`
- ✅ Config fields default gracefully (no startup crashes)
- ✅ CI runs security scan + SBOM generation
- ✅ Terraform skeleton created with dev/stage/prod directories
- ✅ Zero S1/S2 defects
- ✅ Test coverage ≥50%
- ✅ Quality score ≥70
- ✅ Local setup works with `make dev` (all services start)
- ✅ Database migrations up/down tested

### M1 Acceptance (Week 5 EOD)

- ✅ Slot generation algorithm fully functional
- ✅ No double-booking possible (detected + rejected)
- ✅ DST transitions tested (manual verification on specific dates)
- ✅ Timezone handling working (pytz/zoneinfo integrated)
- ✅ Caching working (5-min TTL)
- ✅ Zero S1/S2 defects
- ✅ Test coverage ≥75%
- ✅ Quality score ≥75
- ✅ API endpoint responds <500ms (p95) under load

### M2 Acceptance (Week 8 EOD)

- ✅ Booking creation, modification, cancellation fully working
- ✅ Notifications sent reliably (>99% success rate)
- ✅ Google Calendar sync operational (manual verification)
- ✅ Telegram bot handlers functional (`/book`, `/cancel`, `/reschedule`)
- ✅ State machine enforced (PENDING → CONFIRMED → COMPLETED or CANCELLED)
- ✅ Background job queue working (Redis + RQ)
- ✅ Zero S1/S2 defects
- ✅ Test coverage ≥80%
- ✅ Quality score ≥80
- ✅ Load test: 50 concurrent bookings, <500ms p95 latency

### M3 Acceptance (Week 10 EOD)

- ✅ Calendar UI renders correctly (month, week, day views)
- ✅ Real-time updates working (WebSocket or SSE)
- ✅ Mobile-responsive (iPad + iPhone + Android tablets)
- ✅ Drag-to-reschedule functional
- ✅ Quick-create & quick-edit forms working
- ✅ Filters apply correctly (master, status, date range)
- ✅ E2E tests for critical flows (create, edit, cancel booking)
- ✅ Zero S1/S2 defects
- ✅ Test coverage ≥80%
- ✅ Quality score ≥85
- ✅ Load test: 100 concurrent users, <500ms p95 latency

### M4 Acceptance (Week 11 EOD)

- ✅ Onboarding wizard fully functional (4 steps)
- ✅ Tenant creation working (database record created)
- ✅ RBAC enforced (Admin, Manager, Master, QA, Debugger roles)
- ✅ Multi-tenant data isolation verified (unit + integration tests)
- ✅ Break-glass sessions working with audit trail
- ✅ Google Workspace domain config accepted
- ✅ Zero S1/S2 defects
- ✅ Test coverage ≥85%
- ✅ Quality score ≥85
- ✅ Manual E2E: New tenant onboards → creates booking → sees calendar

### M5 Acceptance (Week 12+ EOD)

- ✅ Inventory BOM fully integrated
- ✅ Stock depletion on booking completion
- ✅ Reorder alerts sent (Slack + email)
- ✅ Purchase orders created + tracked
- ✅ Observability live (tracing, metrics, error tracking)
- ✅ PII masking enforced (role-based)
- ✅ GDPR delete endpoint working
- ✅ Analytics dashboard operational
- ✅ Load test results: p95 latency <500ms (100–200 concurrent), error rate <0.1%
- ✅ Security audit passed (no secrets in logs, no PII leaks, multi-tenant isolation verified)
- ✅ Runbooks documented + team trained
- ✅ Zero S1/S2 defects
- ✅ Test coverage ≥85%
- ✅ Quality score ≥90
- ✅ Terraform deployment to prod tested (dry-run)

---

## Key Decisions & Trade-Offs

### Decision 1: Single Monorepo vs Microservices

**Chosen:** Monorepo (FastAPI + bot + admin)

**Rationale:**
- Simpler deployment (all services versioned together)
- Shared domain logic (no code duplication)
- Easier to test end-to-end
- Lower operational overhead for MVP

**Trade-off:** As we scale to 10K+ concurrent bookings, may need to separate bot + scheduler as microservices.

---

### Decision 2: Row-Level Security vs Schema-per-Tenant

**Chosen:** Row-Level Security (RLS) with tenant_id column

**Rationale:**
- PostgreSQL RLS policies can be added later without data migration
- Easier to implement cross-tenant reports (revenue by region)
- Simpler onboarding (no schema creation needed)
- Lower database overhead

**Trade-off:** Requires strict middleware enforcement; one bug could leak data.

---

### Decision 3: One-Way vs Two-Way Calendar Sync

**Chosen:** One-way initially (INKA → Google); two-way in M3+

**Rationale:**
- Simpler to implement (don't need to merge Google events into INKA)
- Source of truth is INKA (simpler conflict resolution)
- Allows offline mode (sync when reconnected)

**Trade-off:** If master edits calendar in Google, changes won't reflect in INKA (until two-way implemented).

---

### Decision 4: Notification Channel (SMS vs Telegram vs Email)

**Chosen:** Telegram primary, SMS as fallback, email for critical (password reset)

**Rationale:**
- Telegram free (no SMS cost)
- Real-time (vs email)
- In-app interaction possible (book via bot)

**Trade-off:** Requires bot deployment; some salons may prefer SMS-only.

---

### Decision 5: LLM Provider (OpenAI vs Anthropic vs Local)

**Chosen:** OpenAI (optional); can be swapped to Anthropic or local LLaMA

**Rationale:**
- GPT-4 best-in-class for NLP
- Easy integration (API)
- Optional (system works without LLM)

**Trade-off:** Cost ($0.01–0.05 per request); alternatives cheaper but lower quality.

---

## Deployment & Go-Live Checklist

### Pre-Prod (Week 12)

- [ ] Security audit completed (penetration testing, code review)
- [ ] Load testing results: p95 latency <500ms, error rate <0.1%
- [ ] Database backups tested (restore to stage)
- [ ] Disaster recovery plan documented
- [ ] Runbooks for 10+ common incidents created
- [ ] Team trained on runbooks (dry-run incident)
- [ ] Monitoring + alerting configured (Cloud Monitoring)
- [ ] On-call rotation established
- [ ] SLA/SLO documented (99.9% uptime, <100ms latency)

### Prod Deployment (Week 13)

**Canary Deployment (Day 1–2):**
- Deploy to 10% of traffic
- Monitor error rate, latency, database load
- If all green, gradually increase to 100%

**Full Deployment (Day 3):**
- All traffic on new version
- Monitor for 24 hours
- Rollback available if needed

**Post-Deployment:**
- [ ] Analytics dashboard live
- [ ] Revenue tracking enabled
- [ ] Support team trained on admin UI
- [ ] Customer onboarding begins (invite first 10 beta customers)

---

## Success Metrics

### Business KPIs

| Metric | Target | Timing |
|--------|--------|--------|
| **System Uptime** | 99.9% | Month 1+ |
| **Booking Success Rate** | >99% | Month 1+ |
| **Notification Delivery** | >98% | Month 1+ |
| **Onboarding Time** | <30 min (end-to-end) | Week 13+ |
| **Customer Support Tickets** | <5 per 100 bookings | Month 1+ |

### Technical KPIs

| Metric | Target | Timing |
|--------|--------|--------|
| **API Latency (p95)** | <500ms | Month 1+ |
| **Test Coverage** | ≥85% | Month 3+ |
| **Security Score** | Zero S1, ≤2 S2 | Continuous |
| **Database Query Efficiency** | <100ms slow query | Month 1+ |
| **Error Rate** | <0.1% | Month 1+ |

---

## Questions for Stakeholder Review

1. **Timeline:** Is 12 weeks realistic? Can we parallelize work?
2. **Resources:** Do we have 2 backend engineers + 1 frontend + 1 DevOps by Week 3?
3. **Customers:** Do we test with real salons during M2–M3, or wait until M4?
4. **LLM:** Should we include in M2, or defer to M5?
5. **Localization:** Multi-language support in M0 or M4+?
6. **Mobile App:** Native iOS/Android, or web-only for MVP?
7. **Payment Integration:** Stripe deposits in M2 or M5?
8. **Analytics:** Basic (total bookings) or advanced (revenue per master, churn, LTV)?

---

## Appendix: Command Reference

```bash
# Local Development
make dev                      # Start all services (docker-compose)
make migrate                  # Run Alembic migrations
make test                     # Run pytest
make lint                     # Run ruff + black + mypy
make format                   # Format code

# Deployment
gcloud run deploy inka-api --region europe-west1 --image-url=...
gcloud sql instances patch inka-db --backup-start-time=02:00
terraform apply -var-file=infra/terraform/environments/prod/terraform.tfvars

# Database
psql postgresql://inka:inka@localhost:5432/inka_dev
\dt                          # List tables
SELECT * FROM booking WHERE tenant_id=1;

# Docker
docker compose logs -f api   # Tail API logs
docker compose exec api bash # Shell into container
docker compose down -v       # Tear down + remove volumes
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-22  
**Author:** INKA Production Planning Team  
**Status:** Ready for Implementation
