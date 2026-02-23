# 🏗️ Architecture Gap Analysis: Blueprint vs. Reality

> **Generated:** 2026-02-23  
> **Project:** INKA (Telegram Bot + FastAPI + Admin Panel)  
> **Target:** Production-grade on Google Cloud Run  

---

## Executive Summary

| Category | Blueprint Score | Current State | Gap |
|---|:-:|:-:|:-:|
| 1. Logical Architecture | ██████████░ | ████████░░░ | 🟡 Medium |
| 2. Repo Structure | ██████████░ | █████████░░ | 🟢 Low |
| 3. Environments & Promotion | ██████████░ | ██████░░░░░ | 🔴 High |
| 4. CI/CD Pipeline | ██████████░ | ████████░░░ | 🟡 Medium |
| 5. Containerization | ██████████░ | █████░░░░░░ | 🔴 High |
| 6. DB: Migrations, Access, Security | ██████████░ | ██████░░░░░ | 🟡 Medium |
| 7. Secrets & Config | ██████████░ | ██████░░░░░ | 🟡 Medium |
| 8. Observability | ██████████░ | ████░░░░░░░ | 🔴 High |
| 9. Release Strategy | ██████████░ | ████████░░░ | 🟡 Medium |
| 10. GCP Service Set | ██████████░ | █████░░░░░░ | 🔴 High |

**Overall Readiness: ~55%** — Strong foundation in repo structure and CI/CD workflows; critical gaps in observability, container security, IaC, and environment parity.

---

## 1. Logical Architecture (Levels)

### ✅ What's Implemented

| Layer | Status | Evidence |
|---|---|---|
| **Frontend SPA** | ✅ | `apps/admin/` — Vite + React, built to static, served via nginx |
| **Backend API** | ✅ | `apps/api/` — FastAPI, containerized for Cloud Run |
| **Telegram Bot** | ✅ | `apps/bot/` — aiogram 3.x, separate container |
| **PostgreSQL** | ✅ | Cloud SQL + local docker-compose |
| **Redis** | ✅ | In docker-compose.yml, dependency in pyproject.toml |
| **Object Storage** | ✅ | `google-cloud-storage` in deps, GCS_BUCKET_NAME configured |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **Edge/CDN** — No CDN in front of admin SPA | 🔴 High | Blueprint: DNS → CDN → WAF → TLS. Currently nginx serves directly from Cloud Run |
| **WAF/DDoS** — No WAF layer | 🟡 Medium | Cloud Armor or Cloudflare not configured |
| **Worker service** — No dedicated background worker | 🟡 Medium | No `apps/worker/` or queue consumer. All processing appears synchronous |
| **Message queue** — No Pub/Sub or Cloud Tasks | 🟡 Medium | Blueprint specifies queue for async tasks |
| **IdP/OAuth** — No external identity provider | 🟡 Medium | Auth is custom (python-jose, passlib). No OAuth/OIDC via Google, Auth0, etc. |

### 🎯 Action Items
```
[ ] Set up Cloud CDN + Cloud Load Balancer in front of admin SPA
[ ] Enable Cloud Armor (WAF) on the LB
[ ] Add apps/worker/ for background task processing
[ ] Integrate Pub/Sub or Cloud Tasks for async workflows
[ ] Evaluate OAuth/OIDC integration (Google Identity Platform)
```

---

## 2. Repository Structure

### ✅ What's Implemented — **Variant A: Monorepo** ✓

```
inka/
  apps/
    api/          ✅
    bot/          ✅
    admin/        ✅
  libs/
    core/         ✅ (business logic / DDD)
    database/     ✅ (alembic, migrations)
    observability/✅ (logging_config)
    chaos/        ✅ (chaos engineering)
    quality/      ✅ (quality gate scripts)
    orchestrator/ ✅ (AI/LLM orchestration)
  docs/           ✅
  scripts/        ✅
  .github/workflows/ ✅
```

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **infra/** directory with Terraform | 🔴 High | `STRUCTURE.md` plans `infra/terraform/` but **0 `.tf` files** exist |
| **No `libs/shared/` for cross-language types** | 🟢 Low | Python libs exist; no shared TS/Python type generation |
| **Root README** is minimal | 🟢 Low | Exists but could be more comprehensive |

### 🎯 Action Items
```
[ ] Create infra/terraform/ with GCP module structure (dev/staging/prod)
[ ] Create infra/terraform/modules/ for reusable GCP components
[ ] Consider shared type generation between Python Pydantic ↔ TypeScript
```

---

## 3. Environments & Promotion

### ✅ What's Implemented

| Environment | Status | Evidence |
|---|---|---|
| **dev** | ⚠️ Partial | docker-compose.yml for local dev; no Cloud Run dev environment |
| **staging** | ✅ | `deploy-stage.yml` deploys to `*-stage` services |
| **prod** | ✅ | `deploy-prod.yml` with canary + full promotion |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **No actual Cloud Run `dev` environment** | 🔴 High | Local docker-compose ≠ cloud dev env. Blueprint: 3 cloud environments |
| **"Build once, promote" not fully enforced** | 🔴 High | `deploy-stage.yml` **builds images during stage deploy** — should build once in CI, then promote the same SHA |
| **Image tagging inconsistency** | 🟡 Medium | Stage builds `v0.1.0-stage` tag; prod references `v0.1.0-stage` image — correct promotion intent, but the build step is in the wrong place |
| **No ephemeral preview environments** | 🟢 Low | Blueprint mentions "E2E на ephemeral env" per PR |

### 🎯 Action Items
```
[ ] Create Cloud Run dev services (inka-api-dev, inka-bot-dev, inka-admin-dev)
[ ] Move image build to CI (build once on merge to main) → promote to stage → promote to prod
[ ] Remove build step from deploy-stage.yml; reference CI-built image SHA
[ ] (Optional) Set up ephemeral environments for PR previews
```

---

## 4. CI/CD Pipeline

### ✅ What's Implemented

| CI Step (per PR) | Status | Evidence |
|---|---|---|
| Lint/Format | ✅ | `ci-gate.yml` → ruff, black, mypy |
| Unit Tests | ✅ | `ci-gate.yml` → pytest + coverage gate (80%) |
| SAST (Trivy scan) | ✅ | `ci-gate.yml` → trivy-action on built images |
| Build container image | ✅ | `ci-gate.yml` → docker build per service |
| SBOM generation | ✅ | `ci-gate.yml` → trivy CycloneDX SBOM |
| Version bump check | ✅ | `scripts/version_check.py` |
| Changelog check | ✅ | `ci-gate.yml` → verifies CHANGELOG.md updated |
| Migration safety check | ✅ | `ci-gate.yml` → upgrade/downgrade cycle test |
| Quality gate scoring | ✅ | `scripts/quality_gate.py` |

| CD Step | Status | Evidence |
|---|---|---|
| Stage deploy on tag | ✅ | `deploy-stage.yml` on SemVer tag |
| Prod deploy with approval | ✅ | `deploy-prod.yml` → GitHub Environment approval |
| Canary (10% → 100%) | ✅ | `deploy-prod.yml` → traffic splitting |
| Rollback | ✅ | `rollback.yml` with DB downgrade option |
| Telegram notifications | ✅ | Deployment/rollback alerts via Telegram |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **No `semgrep` SAST** | 🟢 Low | Trivy covers vulnerability scanning; semgrep would add code-level SAST |
| **No E2E tests** | 🟡 Medium | No integration/E2E test step (Playwright/Cypress) |
| **Admin (frontend) not linted in CI** | 🟡 Medium | CI only covers Python lint; no ESLint/TypeScript checks for `apps/admin/` |
| **Duplicate CI workflows** | 🟢 Low | Both `ci.yml` and `ci-gate.yml` exist with overlapping roles |
| **Migrations run after deploy, not before** | 🟡 Medium | In `deploy-prod.yml`, migrations run in step "Run DB migrations on Prod" **after** traffic shift to 100% — should run before |

### 🎯 Action Items
```
[ ] Add frontend lint/typecheck to CI (ESLint + tsc --noEmit for apps/admin/)
[ ] Move migration step BEFORE traffic promotion in deploy-prod.yml
[ ] Remove or consolidate ci.yml (redundant with ci-gate.yml)
[ ] Add semgrep for code-level security analysis
[ ] Add E2E test step (Playwright) — at least smoke tests
```

---

## 5. Containerization

### ✅ What's Implemented

| Feature | API | Bot | Admin |
|---|---|---|---|
| Dockerfile exists | ✅ | ✅ | ✅ |
| Multi-stage build | ❌ | ❌ | ✅ (builder→nginx) |
| Non-root user | ⚠️ `apps/api/src/Dockerfile` has it, but main `apps/api/Dockerfile` does NOT | ❌ | ❌ (nginx runs as root) |
| Health endpoints | ✅ `/health/` in HEALTHCHECK | ❌ | N/A |
| Slim base image | ✅ python:3.12-slim | ✅ python:3.12-slim | ✅ node:20-slim / nginx:alpine |
| Context-aware COPY | ⚠️ | ⚠️ | ✅ |

### ❌ Critical Gaps

| Gap | Priority | Details |
|---|---|---|
| **API Dockerfile not multi-stage** | 🔴 High | `apps/api/Dockerfile` uses single-stage build. Build tools and dev dependencies remain in prod image |
| **Bot Dockerfile not multi-stage** | 🔴 High | Same issue. Bloated image with build artifacts |
| **No non-root user** in main Dockerfiles | 🔴 High | `apps/api/Dockerfile` and `apps/bot/Dockerfile` run as root. Only the **unused** `apps/api/src/Dockerfile` has `appuser` |
| **Bot has no health endpoint** | 🟡 Medium | No healthz/readyz for bot container. Cloud Run needs it |
| **Admin runs nginx as root** | 🟡 Medium | Should run as non-root (nginx unprivileged image) |
| **`/healthz` and `/readyz` naming** | 🟢 Low | Blueprint specifies k8s-style `/healthz` + `/readyz`. Current API only has `/health/` |
| **Duplicate API Dockerfile** | 🟡 Medium | Both `apps/api/Dockerfile` and `apps/api/src/Dockerfile` exist — which is canonical? |

### 🎯 Action Items
```
[ ] Rewrite apps/api/Dockerfile as multi-stage (builder → runtime)
[ ] Rewrite apps/bot/Dockerfile as multi-stage
[ ] Add non-root user to ALL Dockerfiles
[ ] Add /healthz and /readyz endpoints to API
[ ] Add health check endpoint to Bot
[ ] Use nginx:alpine-unprivileged for admin
[ ] Remove duplicate apps/api/src/Dockerfile
```

---

## 6. DB: Migrations, Access, Security

### ✅ What's Implemented

| Feature | Status | Evidence |
|---|---|---|
| Alembic migrations | ✅ | `libs/database/alembic/` + `alembic.ini` |
| Migration in CD pipeline | ✅ | Both `deploy-stage.yml` and `deploy-prod.yml` run `alembic upgrade head` |
| Migration safety checks | ✅ | `ci-gate.yml` → upgrade/downgrade cycle in CI |
| Cloud SQL | ✅ | Configured for GCP deployment |
| Separate env DB credentials | ✅ | Secrets per environment (`STAGE_DATABASE_URL`, `PROD_DATABASE_URL`) |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **Migrations not idempotent-verified** | 🟡 Medium | CI tests upgrade/downgrade but no explicit idempotency check |
| **No VPC Connector** | 🔴 High | Blueprint: "Only through private network/VPC connector". No IaC to enforce this |
| **No separate DB user per environment** | 🟡 Medium | All envs use same user `inka` format in docker-compose |
| **Secret Manager for DB DSN** | ⚠️ Partial | Secrets are in GitHub Secrets but no GCP Secret Manager integration in Terraform (no Terraform exists) |
| **No automated backup verification** | 🟡 Medium | Blueprint: "регулярный restore test". No CI job or cron to verify backup restores |
| **Migration timing in prod** | 🟡 Medium | Runs **after** full traffic promotion — should run before or as init container |
| **Backward-compatible migration checks** | 🟢 Low | No automated check that migrations are backward-compatible |

### 🎯 Action Items
```
[ ] Create VPC Connector in Terraform for Cloud Run → Cloud SQL
[ ] Define separate DB users: inka_dev, inka_stage, inka_prod
[ ] Move migration step BEFORE traffic promotion in deploy-prod.yml
[ ] Add scheduled backup restore test (monthly Cloud Build job)
[ ] Add backward-compatibility linter for migration files
```

---

## 7. Secrets & Config

### ✅ What's Implemented

| Feature | Status | Evidence |
|---|---|---|
| `.env.example` | ✅ | Template with all required vars |
| `.env` in `.gitignore` | ✅ | Not committed to repo |
| GitHub Secrets for CI/CD | ✅ | Used in all workflow files |
| GCP Secret Manager as mount | ✅ | `deploy-stage.yml` uses `secrets:` directive |
| `GOOGLE_APPLICATION_CREDENTIALS` | ✅ | In `.env.example` |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **No GCP Secret Manager IaC** | 🔴 High | Secrets referenced in workflows but no Terraform to create/manage them |
| **No secret rotation policy** | 🟡 Medium | Blueprint: secrets should rotate. No mechanism defined |
| **No break-glass procedure** | 🟡 Medium | Documented in audit report but not implemented as code |
| **`.env` file exists in repo root** | 🔴 High | `inka/.env` (758 bytes) — verify it's in `.gitignore` and never committed |
| **Config vs. Secret boundary unclear** | 🟢 Low | All config is env vars. No config files managed via IaC |

### 🎯 Action Items
```
[ ] Verify .env is in .gitignore (double check git history for accidental commits)
[ ] Create Terraform for GCP Secret Manager entries
[ ] Define secret rotation schedule (BOT_TOKEN, DB passwords, API keys)
[ ] Implement break-glass access procedure with audit trail
[ ] Separate config (non-secret) from secrets in deployment manifests
```

---

## 8. Observability (must-have) — ⚠️ BIGGEST GAP

### ✅ What's Implemented

| Feature | Status | Evidence |
|---|---|---|
| Structured JSON logs | ✅ | `libs/observability/src/logging_config.py` — `python-json-logger` |
| Request ID / Actor ID in logs | ✅ | `CustomJsonFormatter` adds `request_id`, `actor_id`, `role` |
| Latency tracking in logs | ✅ | `latency_ms` field in log formatter |
| Cloud Logging (implicit) | ✅ | Cloud Run auto-captures stdout |

### ❌ What's Missing

| Gap | Priority | Details |
|---|---|---|
| **No OpenTelemetry** | 🔴 Critical | Zero `opentelemetry` in deps, no tracing SDK. Blueprint: "Tracing через OpenTelemetry" |
| **No Sentry** | 🔴 High | Zero `sentry-sdk` in deps. Blueprint: "Ошибки (Sentry)" |
| **No distributed tracing** | 🔴 High | No `trace_id` or correlation ID propagation front→back |
| **No metrics collection** | 🔴 High | No Prometheus metrics, no Cloud Monitoring agent. No RPS/latency/DB pool metrics |
| **No alerting on SLO** | 🔴 High | No Cloud Monitoring alert policies defined |
| **No `structlog`** | 🟡 Medium | Using `python-json-logger` which is less feature-rich than structlog for context binding |
| **ContextFilter not wired** | 🟡 Medium | `ContextFilter` class exists but doesn't appear to be applied via middleware |
| **No Cloud Monitoring dashboards** | 🟡 Medium | No Terraform or scripts to create dashboards |
| **PagerDuty/Slack integration missing** | 🟡 Medium | Only Telegram notifications exist |

### 🎯 Action Items (Prioritized)
```
HIGH PRIORITY:
[ ] Add opentelemetry-sdk, opentelemetry-instrumentation-fastapi to pyproject.toml
[ ] Configure OTLP exporter → Cloud Trace
[ ] Add sentry-sdk to deps + init in main.py
[ ] Generate trace_id in frontend, propagate via header to API
[ ] Wire ContextFilter as FastAPI middleware for request_id propagation

MEDIUM PRIORITY:
[ ] Add prometheus-client or Cloud Monitoring custom metrics
[ ] Create Cloud Monitoring dashboards (latency, error rate, DB pool)
[ ] Define SLO-based alert policies (e.g., error rate > 1%, p95 > 2s)
[ ] Migrate from python-json-logger to structlog
[ ] Add Cloud Monitoring uptime checks for all services
```

---

## 9. Release Strategy

### ✅ What's Implemented

| Feature | Status | Evidence |
|---|---|---|
| SemVer versioning | ✅ | `v0.1.0` in pyproject.toml, version check in CI |
| Tag-based deployments | ✅ | `deploy-stage.yml` triggers on `v*.*.*` tags |
| Canary deploys | ✅ | `deploy-prod.yml` → 10% canary → health check → 100% |
| Rollback mechanism | ✅ | `rollback.yml` with traffic revert + DB downgrade |
| Health monitoring during canary | ✅ | `monitor_canary.py` with 30-min window |
| Release registry | ✅ | `register_release.py` + `release_registry` tracking |
| CHANGELOG enforcement | ✅ | CI checks CHANGELOG.md updated per PR |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **No feature flags** | 🟡 Medium | Blueprint: "Feature flags для рискованных фич". No LaunchDarkly, Unleash, or homegrown |
| **No auto-rollback** | 🟡 Medium | Blueprint: "Автоматический rollback при росте 5xx/latency". Canary health check exists but doesn't auto-rollback on failure — only fails the pipeline |
| **24h stability check script missing** | 🟡 Medium | `deploy-prod.yml` references `scripts/check_stage_stability.py` but file doesn't exist |
| **Monitor canary script missing** | 🟡 Medium | `deploy-prod.yml` references `scripts/monitor_canary.py` but file doesn't exist |
| **Rollback helper scripts missing** | 🟡 Medium | `rollback.yml` references `scripts/get_rollback_revision.py` and `scripts/log_rollback_incident.py` — not present |

### 🎯 Action Items
```
[ ] Implement scripts/check_stage_stability.py
[ ] Implement scripts/monitor_canary.py with auto-rollback on threshold breach
[ ] Implement scripts/get_rollback_revision.py
[ ] Implement scripts/log_rollback_incident.py
[ ] Implement scripts/update_release_status.py
[ ] Evaluate feature flag system (start with simple DB-backed flags)
[ ] Add auto-rollback step in deploy-prod.yml on canary failure
```

---

## 10. GCP Production Service Set

### Blueprint vs. Reality

| Service | Blueprint | Current State |
|---|---|---|
| **Cloud Run** (API, Bot, Admin) | ✅ Required | ✅ Deployed (3 services) |
| **Cloud SQL PostgreSQL** | ✅ Required | ✅ Configured |
| **Secret Manager** | ✅ Required | ⚠️ Referenced in workflow yaml but no IaC |
| **Artifact Registry** | ✅ Required | ✅ Used for container images |
| **Cloud Storage + CDN** | ✅ Required | ⚠️ GCS configured, **no CDN** |
| **Cloud Load Balancer + SSL** | ✅ Required | ❌ Not configured — Cloud Run default URLs |
| **Cloud Logging/Monitoring** | ✅ Required | ⚠️ Implicit (Cloud Run stdout), no custom setup |
| **Alerting** | ✅ Required | ❌ No alert policies defined |
| **Pub/Sub / Cloud Tasks** | Optional | ❌ Not implemented |
| **Redis (Memorystore)** | Optional | ❌ In docker-compose only; no Cloud Memorystore |
| **VPC Connector** | Implicit | ❌ Not configured |
| **Cloud Armor (WAF)** | Implicit | ❌ Not configured |

### 🎯 Action Items (IaC Priority)
```
CRITICAL:
[ ] Create infra/terraform/modules/cloud_run/
[ ] Create infra/terraform/modules/cloud_sql/
[ ] Create infra/terraform/modules/secret_manager/
[ ] Create infra/terraform/modules/artifact_registry/

HIGH:
[ ] Create infra/terraform/modules/load_balancer/ (Cloud LB + managed SSL)
[ ] Create infra/terraform/modules/cdn/ (Cloud CDN for admin SPA)
[ ] Create infra/terraform/modules/monitoring/ (dashboards + alerts)
[ ] Create infra/terraform/modules/networking/ (VPC + connector)

MEDIUM:
[ ] Create infra/terraform/modules/memorystore/ (Redis)
[ ] Create infra/terraform/modules/pubsub/ (message queue)
[ ] Create infra/terraform/modules/cloud_armor/ (WAF)
[ ] Create infra/terraform/environments/{dev,staging,prod}/main.tf
```

---

## 🔥 Top 10 Priority Actions

| # | Action | Impact | Effort | Section |
|---|---|---|---|---|
| 1 | **Add OpenTelemetry tracing + Sentry** | 🔴 Critical | 3-5 days | §8 Observability |
| 2 | **Create Terraform IaC foundation** | 🔴 Critical | 5-7 days | §10 GCP |
| 3 | **Fix Dockerfiles** (multi-stage, non-root, healthz) | 🔴 High | 1-2 days | §5 Containers |
| 4 | **Enforce "build once, promote"** | 🔴 High | 1 day | §3 Environments |
| 5 | **Fix migration timing** (before traffic, not after) | 🔴 High | 0.5 days | §4 CI/CD, §6 DB |
| 6 | **Implement missing CD scripts** (5 scripts) | 🟡 Medium | 2-3 days | §9 Release |
| 7 | **Cloud CDN + Load Balancer + SSL** | 🟡 Medium | 2-3 days | §1 Architecture, §10 |
| 8 | **VPC Connector for Cloud SQL** | 🟡 Medium | 0.5 days | §6 DB, §10 GCP |
| 9 | **Frontend CI** (ESLint + TypeScript) | 🟡 Medium | 0.5 days | §4 CI/CD |
| 10 | **Feature flags system** | 🟢 Low | 2-3 days | §9 Release |

---

## Scripts Referenced but Missing

These scripts are referenced in GitHub Actions workflows but **do not exist** in the `scripts/` directory:

| Script | Referenced In | Purpose |
|---|---|---|
| `scripts/check_stage_stability.py` | `deploy-prod.yml` | 24h stage stability verification |
| `scripts/monitor_canary.py` | `deploy-prod.yml` | Canary health monitoring (30 min) |
| `scripts/get_rollback_revision.py` | `rollback.yml` | Find previous stable revision |
| `scripts/log_rollback_incident.py` | `rollback.yml` | Record rollback incident |
| `scripts/update_release_status.py` | `deploy-prod.yml` | Update release registry status |
| `scripts/check_migrations.py` | `ci-gate.yml` | Migration safety analysis |

> ⚠️ **These missing scripts will cause workflow failures.** They must be implemented before the pipelines are production-ready.

---

## Current vs. Target Architecture Diagram

```
CURRENT STATE:
                                                    
  Browser ──→ Cloud Run (admin) ──→ Cloud Run (API) ──→ Cloud SQL
                                         ↓
                                    Cloud Run (bot)
                              (public internet to DB ⚠️)

TARGET STATE (Blueprint):

  Browser ──→ Cloud CDN ──→ Cloud LB (SSL/WAF) ──→ Cloud Run (admin)
                                    │
                                    ├──→ Cloud Run (API) ──[VPC]──→ Cloud SQL
                                    │         ↓                        ↓
                                    │    Cloud Run (worker)      Memorystore
                                    │         ↓                   (Redis)
                                    │     Pub/Sub / Tasks
                                    │
                                    └──→ Cloud Run (bot.ssr)
                                    
  Observability: OpenTelemetry → Cloud Trace/Monitoring + Sentry
  IaC: Terraform per environment (dev/staging/prod)
  Secrets: GCP Secret Manager (IaC-managed)
```

---

*Document generated by architecture audit. Review quarterly.*
