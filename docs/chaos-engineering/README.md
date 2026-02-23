# INKA Chaos Engineering & Resilience Testing

**Version 1.0** | Last Updated: February 2026

This document describes the complete Chaos Engineering system for INKA Admin, enabling controlled resilience testing across all environments (dev, stage, prod) with safety guardrails and automated recovery.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Chaos Experiment Catalog](#chaos-experiment-catalog)
4. [Safety Controls](#safety-controls)
5. [Telegram Bot Commands](#telegram-bot-commands)
6. [API Reference](#api-reference)
7. [Metrics & Dashboards](#metrics--dashboards)
8. [Defect Integration](#defect-integration)
9. [Production Runbook](#production-runbook)
10. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## Quick Start

### For Telegram Users (Admins & Resilience Authority)

```bash
/chaos_list              # Show all available experiments
/chaos_run <exp> [env]   # Start an experiment (default: dev)
/chaos_stop <run_id>     # Abort a running experiment
/chaos_history           # View last 10 runs + metrics
```

**Example:**
```
/chaos_run api_latency_injection stage
/chaos_stop abc12345
```

### For API Users

```bash
# List experiments
curl -X GET http://localhost:8000/chaos/experiments?env=stage

# Start experiment
curl -X POST http://localhost:8000/chaos/run \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_name": "api_latency_injection",
    "environment": "stage",
    "requester": "ci-system"
  }'

# Stop experiment
curl -X POST http://localhost:8000/chaos/stop/{run_id} \
  -H "Content-Type: application/json" \
  -d '{"reason": "manual stop"}'

# View metrics
curl -X GET http://localhost:8000/chaos/metrics?window_days=30
```

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────┐
│                   INKA Chaos System                  │
├──────────────────────┬────────────────────────────────┤
│                      │                                │
│  Telegram Bot        │     FastAPI Backend            │
│  /chaos_*            │     /chaos/* endpoints         │
│  handlers            │                                │
│       │              │           ▼                    │
│       └──────────────┼─────► ChaosRunner              │
│                      │       (orchestrator)           │
│                      │           │                    │
│                      │     ┌─────┼─────┐              │
│                      │     │     │     │              │
│                      │    ▼    ▼    ▼                 │
│                      │  Safety Rollback Metrics      │
│                      │  Control Manager  Collector   │
│                      │     │                          │
│                      │     └──► PostgreSQL            │
│                      │          (ChaosRun,           │
│                      │           ChaosMetric)        │
└──────────────────────┴────────────────────────────────┘
```

### Library Structure

```
libs/chaos/
├── models.py          # SQLAlchemy ORM (ChaosExperiment, ChaosRun, ChaosMetric)
├── catalog.py         # Immutable experiment definitions
├── safety.py          # Pre-flight & runtime safety gates
├── runner.py          # Experiment lifecycle orchestrator
├── rollback.py        # Per-experiment rollback handlers
├── metrics.py         # Collection & aggregation (MTTR, auto-recovery, etc.)
└── __init__.py        # Public API exports
```

### Runtime Flow

```
1. User runs /chaos_run api_latency_injection stage

2. Bot → API POST /chaos/run
   {
     "experiment_name": "api_latency_injection",
     "environment": "stage",
     "requester": "telegram:@admin"
   }

3. ChaosRunner.run() executes:
   a) Fetch experiment from catalog
   b) SafetyController.check_pre_conditions()
      - Verify env allowed
      - Verify max_duration not exceeded
      - Verify compliance approval (if prod)
      - Check for active S1/S2 defects
   c) Create ChaosRun record in DB
   d) Launch background task: _execute_loop()

4. _execute_loop() runs:
   a) Call _start_experiment() (enables chaos injection)
   b) Poll metrics every 15 seconds
   c) For each poll:
      - Record metric snapshot
      - SafetyController.check_abort_conditions()
        → error_rate >= threshold? ABORT
        → p95_latency >= threshold? ABORT
        → elapsed_time >= max_duration_sec? ABORT
        → S1 defect active? ABORT
   d) If abort triggered:
      - RollbackManager.rollback()
      - Mark run as ROLLED_BACK or FAILED
   e) If completes normally:
      - _stop_experiment()
      - Mark run as COMPLETED

5. Metrics published to:
   - PostgreSQL (ChaosMetric rows)
   - Structured logs (JSON with experiment_id)
   - Telegram via /chaos_history
```

---

## Chaos Experiment Catalog

### 1. API Latency Injection

**Name:** `api_latency_injection`  
**Type:** api_latency  
**Duration:** 300 sec (5 min)  
**Environments:** dev, stage, prod  
**Compliance Required:** ❌ No

**Hypothesis:**
> The system handles +500 ms API latency gracefully — clients retry correctly and p95 stays below 2000 ms.

**Blast Radius:** All inbound HTTP requests to the API service

**Abort Conditions:**
- Error rate ≥ 10%
- p95 latency ≥ 2000 ms

**Rollback:** Disables latency middleware; delay restored to 0 ms

**Implementation:**
- FastAPI middleware injects 500 ms delay into request processing
- Applies uniformly across all endpoints

---

### 2. DB Connection Saturation

**Name:** `db_connection_saturation`  
**Type:** db_saturation  
**Duration:** 180 sec (3 min)  
**Environments:** dev, stage, prod  
**Compliance Required:** ✅ Yes

**Hypothesis:**
> The API returns 503 with a clear error message when DB pool is exhausted, and recovers automatically once load subsides.

**Blast Radius:** All API endpoints that use database connections

**Abort Conditions:**
- Error rate ≥ 10%
- p95 latency ≥ 5000 ms
- API error responses > 50% for 30 sec

**Rollback:** Resets SQLAlchemy connection pool to default size

**Implementation:**
- Opens max concurrent connections to exhaust pool
- New requests fail immediately with 503 Service Unavailable

---

### 3. Telegram Webhook Failure

**Name:** `telegram_webhook_failure`  
**Type:** webhook_failure  
**Duration:** 120 sec (2 min)  
**Environments:** dev, stage (NOT prod)  
**Compliance Required:** ❌ No

**Hypothesis:**
> Bot commands queue correctly during webhook unavailability and drain without data loss when restored.

**Blast Radius:** All Telegram bot webhook ingestion

**Abort Conditions:**
- S1 defect triggered
- Bot unavailable > 2 min

**Rollback:** Restores Telegram webhook URL to production endpoint

**Implementation:**
- Temporarily routes webhook to black-hole endpoint
- Messages queued by Telegram (up to TTL)

---

### 4. Booking Conflict Surge

**Name:** `booking_conflict_surge`  
**Type:** booking_surge  
**Duration:** 180 sec (3 min)  
**Environments:** dev, stage  
**Compliance Required:** ❌ No

**Hypothesis:**
> Booking conflict detection remains correct and returns 409 without data corruption under concurrent surge traffic.

**Blast Radius:** Booking API endpoints and DB booking table

**Abort Conditions:**
- Error rate ≥ 20%
- p95 latency ≥ 3000 ms
- Data integrity check fails

**Rollback:** Stops load generator; verifies booking table integrity

**Implementation:**
- Fires 50 concurrent booking requests with conflicting time slots
- Validates all conflicts detected correctly

---

### 5. Random 500 Error Injection

**Name:** `random_500_injection`  
**Type:** random_500  
**Duration:** 300 sec (5 min)  
**Environments:** dev, stage (NEVER prod)  
**Compliance Required:** ❌ No

**Hypothesis:**
> Clients and the bot handle random 500 errors gracefully with retry logic and display user-friendly error messages.

**Blast Radius:** 5% of all HTTP responses from API

**Abort Conditions:**
- Error rate ≥ 15% sustained for 60 sec

**Rollback:** Disables random 500 middleware flag

**Implementation:**
- Middleware randomly returns HTTP 500 for ~5% of requests
- **Dev/Stage only** — never prod

---

### 6. Cloud Run Instance Kill

**Name:** `cloud_run_instance_kill`  
**Type:** instance_kill  
**Duration:** 120 sec (2 min)  
**Environments:** dev, stage, prod  
**Compliance Required:** ✅ Yes

**Hypothesis:**
> Cloud Run auto-scales and restores a replacement instance within 30 s, with < 5% error rate during the recovery window.

**Blast Radius:** One Cloud Run instance of inka-api service

**Abort Conditions:**
- Error rate ≥ 5% for > 30 sec
- No recovery after 90 sec

**Rollback:** Verifies new instance is healthy via `gcloud run services describe`

**Implementation:**
- Sends SIGKILL to one running Cloud Run instance via gcloud CLI
- Cloud Run automatically replaces it

---

### 7. Secret Rotation Simulation

**Name:** `secret_rotation_simulation`  
**Type:** secret_rotation  
**Duration:** 300 sec (5 min)  
**Environments:** dev, stage, prod  
**Compliance Required:** ✅ Yes

**Hypothesis:**
> Services reload new secrets within their rotation window without causing auth failures exceeding SLA threshold.

**Blast Radius:** Secret Manager secret versions; config reload path

**Abort Conditions:**
- Auth failure rate ≥ 2%
- Secret unavailable > 60 sec

**Rollback:** Reverts to previous secret version; triggers config reload

**Implementation:**
- Adds new secret version in Secret Manager
- Forces app to reload config
- Validates old version still works (graceful)

---

### 8. Network Timeout (API ↔ DB)

**Name:** `network_timeout_api_db`  
**Type:** network_timeout  
**Duration:** 180 sec (3 min)  
**Environments:** dev, stage, prod  
**Compliance Required:** ✅ Yes

**Hypothesis:**
> The API returns 503 with timeout context when the DB connection times out, without hanging requests indefinitely.

**Blast Radius:** DB connection layer — all API requests that query DB

**Abort Conditions:**
- Error rate ≥ 15%
- p95 latency ≥ 5000 ms
- Any request hangs > 30 sec

**Rollback:** Restores default DB connection timeout values

**Implementation:**
- Applies 2 sec connection timeout to DB pool
- Simulates network partition

---

### 9. High Concurrency Spike (Load Test)

**Name:** `high_concurrency_spike`  
**Type:** concurrency_spike  
**Duration:** 300 sec (5 min)  
**Environments:** dev, stage, prod  
**Compliance Required:** ✅ Yes

**Hypothesis:**
> The system sustains 500 RPS for 5 minutes with p95 < 3000 ms and error rate < 5%, demonstrating horizontal scalability.

**Blast Radius:** All three services — inka-api, inka-bot, inka-admin

**Abort Conditions:**
- p95 > 3000 ms
- Error rate > 5%
- S1 defect triggered

**Rollback:** Stops k6 load test process; verifies services recovered

**Implementation:**
- k6 load test ramping to 500 Virtual Users
- Hits key API endpoints (bookings, clients, masters)

---

## Safety Controls

### 1. Environment Gating

| Experiment | Dev | Stage | Prod |
|-----------|-----|-------|------|
| api_latency_injection | ✅ | ✅ | ✅ |
| db_connection_saturation | ✅ | ✅ | ✅ |
| telegram_webhook_failure | ✅ | ✅ | ❌ |
| booking_conflict_surge | ✅ | ✅ | ❌ |
| random_500_injection | ✅ | ✅ | ❌ |
| cloud_run_instance_kill | ✅ | ✅ | ✅ |
| secret_rotation_simulation | ✅ | ✅ | ✅ |
| network_timeout_api_db | ✅ | ✅ | ✅ |
| high_concurrency_spike | ✅ | ✅ | ✅ |

### 2. Compliance Approval

**Production experiments requiring approval:**
- db_connection_saturation
- cloud_run_instance_kill
- secret_rotation_simulation
- network_timeout_api_db
- high_concurrency_spike

**Approval Flow:**
1. User runs: `/chaos_run <exp> prod --approve`
2. Telegram/API validates `compliance_approved=True`
3. SafetyController raises `ComplianceGateError` if missing
4. Audit log records approval status

### 3. Runtime Abort Conditions

Each experiment defines automatic abort triggers:

**Error Rate Threshold**
```python
if error_rate_pct >= experiment.abort_error_rate_pct:
    → ABORT and ROLLBACK
```

**p95 Latency Threshold**
```python
if p95_latency_ms >= experiment.abort_p95_latency_ms:
    → ABORT and ROLLBACK
```

**Max Duration Enforcement**
```python
if elapsed_sec >= experiment.max_duration_sec:
    → NORMAL COMPLETION (even if metrics look good)
```

**Active S1/S2 Defect Detection**
```python
if check_for_active_defects():
    → IMMEDIATE ABORT (highest priority)
```

### 4. Defect System Integration

The chaos system integrates with INKA's defect tracking:

**Pre-flight Check:**
```python
SafetyController._check_no_active_defects()
# Calls defect API: GET /internal/defects?severity=S1,S2
# If count > 0 → raise ActiveDefectError
```

**Runtime Monitoring:**
```python
# During _execute_loop(), sample defects every POLL_INTERVAL_SEC
if s1_defect_active:
    → Trigger immediate abort + rollback
```

**Post-Experiment:**
```python
# If new S1 defect created during experiment
# Correlate to chaos run ID in defect record
# Mark as "triggered_by_chaos"
```

### 5. Canary Mode (Production)

For production, chaos is limited to **max 5% traffic**:

```python
SafetyController.PROD_MAX_TRAFFIC_PCT = 5
```

Implementation:
- Route-based traffic splitting (Istio, Cloud Load Balancer)
- Canary label on affected instances
- Automatic rollback if error rate exceeds threshold

---

## Telegram Bot Commands

### /chaos_list [env]

**Permissions:** admin, resilience_authority

**Usage:**
```
/chaos_list              # Show all experiments
/chaos_list stage        # Show stage-allowed experiments
/chaos_list prod         # Show prod-allowed experiments
```

**Response Format:**
```
🧪 Chaos Experiment Catalog [stage]

1. api_latency_injection
   Injects 500 ms artificial delay via FastAPI middleware.
   💥 Blast: All inbound HTTP requests to the API service
   ⏱ Max: 5m | ✅ no approval needed
   🌍 Envs: `dev, stage, prod`

2. db_connection_saturation
   ...
```

---

### /chaos_run \<experiment\> [env] [--approve]

**Permissions:** admin, resilience_authority

**Usage:**
```
/chaos_run api_latency_injection          # Start on dev (default)
/chaos_run api_latency_injection stage    # Start on stage
/chaos_run cloud_run_instance_kill prod --approve   # Start on prod
```

**Response Examples:**

✅ **Success (202 Accepted):**
```
🔥 Chaos experiment started!

Experiment: api_latency_injection
Environment: stage
Run ID: abc12345
Requester: telegram:@admin

Monitor with: /chaos_history
Stop with: /chaos_stop abc12345
```

⚠️ **Missing Approval (Prod):**
```
⚠️ Production chaos requires explicit approval!

Re-run with --approve flag:
/chaos_run cloud_run_instance_kill prod --approve

This confirms you have compliance team sign-off.
```

🔐 **Safety Gate Blocked:**
```
🔐 Safety gate blocked the experiment:
Active S1 defects detected — chaos blocked.
```

---

### /chaos_stop \<run_id\>

**Permissions:** admin, resilience_authority

**Usage:**
```
/chaos_stop abc12345    # Abort experiment
```

**Response:**
```
⛔ Experiment stopped + rollback triggered

Run ID: abc12345
Message: API latency middleware disabled — delay restored to 0 ms.
Stopped by: telegram:@admin
```

---

### /chaos_history [env]

**Permissions:** admin, resilience_authority

**Usage:**
```
/chaos_history          # Show all recent runs
/chaos_history stage    # Show stage runs only
```

**Response Format:**
```
📜 Chaos Run History (last 10)

✅ `abc12345` — api_latency_injection
   Env: stage | Duration: 45s
   By: telegram:@admin

🔁 `def67890` — db_connection_saturation
   Env: dev | Duration: 120s
   By: telegram:@bot
   ⚠️ DB pool reset after abort.

📊 30-Day Metrics
   MTTR: 45s | Auto-recovery: 87.5%
   Rollbacks: 3 | Failed tests: 1
```

---

## API Reference

### Base URL
```
http://localhost:8000/chaos
```

### Authentication

All chaos endpoints require admin/resilience_authority role. Implement via:
- Bearer token (JWT)
- Session cookie
- Custom header middleware

See [API Auth Design](../development/auth.md) for details.

---

### GET /experiments

**Description:** List all experiments in the catalog

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| env | string | Filter by environment: `dev`, `stage`, `prod` |

**Response (200 OK):**
```json
[
  {
    "name": "api_latency_injection",
    "experiment_type": "api_latency",
    "hypothesis": "The system handles +500 ms API latency...",
    "blast_radius": "All inbound HTTP requests to the API service",
    "max_duration_sec": 300,
    "abort_error_rate_pct": 10.0,
    "abort_p95_latency_ms": 2000,
    "rollback_trigger": "p95 latency > 2000 ms OR error rate > 10%",
    "allowed_envs": ["dev", "stage", "prod"],
    "requires_compliance": false,
    "description": "Injects 500 ms artificial delay via FastAPI middleware."
  },
  ...
]
```

**Example:**
```bash
curl -X GET "http://localhost:8000/chaos/experiments?env=stage" \
  -H "Authorization: Bearer <token>"
```

---

### POST /run

**Description:** Start a chaos experiment

**Request Body:**
```json
{
  "experiment_name": "api_latency_injection",
  "environment": "stage",
  "compliance_approved": false,
  "requester": "ci-system"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| experiment_name | string | ✅ | Name from catalog |
| environment | string | ✅ | `dev`, `stage`, or `prod` |
| compliance_approved | boolean | ❌ | Required for prod + requires_compliance=true |
| requester | string | ❌ | Identity tag (default: "api") |

**Response (202 Accepted):**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "experiment_name": "api_latency_injection",
  "environment": "stage",
  "status": "running",
  "requester": "ci-system",
  "compliance_approved": false,
  "started_at": null,
  "ended_at": null,
  "abort_reason": null,
  "duration_sec": null,
  "message": "Experiment 'api_latency_injection' started. run_id=550e8400"
}
```

**Error Responses:**

404 Not Found:
```json
{"detail": "Unknown experiment: 'invalid_name'. Available: [...]"}
```

403 Forbidden (Environment Gate):
```json
{"detail": "Experiment 'random_500_injection' is not allowed in environment 'prod'."}
```

403 Forbidden (Compliance):
```json
{"detail": "Experiment 'cloud_run_instance_kill' requires compliance approval..."}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/chaos/run" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_name": "api_latency_injection",
    "environment": "stage",
    "requester": "ci-system"
  }'
```

---

### POST /stop/{run_id}

**Description:** Abort a running experiment + trigger rollback

**URL Parameters:**
| Name | Type | Description |
|------|------|-------------|
| run_id | UUID | Run ID from `/run` response |

**Request Body:**
```json
{
  "reason": "manual stop"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reason | string | ❌ | Reason for stopping (default: "manual stop") |

**Response (200 OK):**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "aborted",
  "abort_reason": "manual stop",
  "message": "Experiment 550e8400 stopped: manual stop"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/chaos/stop/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"reason": "manual stop"}'
```

---

### GET /history

**Description:** Paginated chaos run history

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| limit | int | Results per page (default: 10, max: 100) |
| offset | int | Pagination offset (default: 0) |
| env | string | Filter by environment |

**Response (200 OK):**
```json
[
  {
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "experiment_name": "api_latency_injection",
    "environment": "stage",
    "status": "completed",
    "requester": "ci-system",
    "created_at": "2026-02-22T10:30:00Z",
    "started_at": "2026-02-22T10:30:05Z",
    "ended_at": "2026-02-22T10:35:05Z",
    "duration_sec": 300.0,
    "abort_reason": null
  },
  ...
]
```

**Example:**
```bash
curl -X GET "http://localhost:8000/chaos/history?limit=20&env=stage" \
  -H "Authorization: Bearer <token>"
```

---

### GET /metrics

**Description:** Dashboard metrics aggregation

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| window_days | int | Lookback window (default: 30, max: 365) |

**Response (200 OK):**
```json
{
  "window_days": 30,
  "avg_mttr_sec": 42.5,
  "auto_recovery_rate_pct": 87.5,
  "rollback_frequency": 3,
  "failed_resilience_tests": 1,
  "total_runs": 8
}
```

| Field | Description |
|-------|-------------|
| avg_mttr_sec | Mean Time To Recovery in seconds |
| auto_recovery_rate_pct | % of experiments that completed without manual rollback |
| rollback_frequency | Number of manual rollbacks triggered |
| failed_resilience_tests | Experiments aborted due to threshold breach |

**Example:**
```bash
curl -X GET "http://localhost:8000/chaos/metrics?window_days=30" \
  -H "Authorization: Bearer <token>"
```

---

## Metrics & Dashboards

### Key Metrics

**1. MTTR (Mean Time To Recovery)**
- **Definition:** Time from experiment start to system recovered to healthy state
- **Calculation:** `(ended_at - started_at) for each run`
- **Target SLA:** < 60 seconds
- **Tracked in:** `ChaosMetric.mttr_sec`

**2. Auto-Recovery Rate**
- **Definition:** % of experiments that completed without manual rollback
- **Calculation:** `completed_count / (completed + rolled_back + aborted) * 100`
- **Target SLA:** ≥ 85%
- **Use Case:** Measure system's self-healing capability

**3. Rollback Frequency**
- **Definition:** Number of manual rollbacks triggered in window
- **Calculation:** `count(status=ROLLED_BACK)`
- **Target SLA:** ≤ 5 per month
- **Indicates:** Safety gates are working; experiments exposing real weaknesses

**4. Failed Resilience Tests**
- **Definition:** Experiments aborted due to threshold breach
- **Calculation:** `count(status in [ABORTED, FAILED])`
- **Target SLA:** ≤ 2 per month
- **Action:** File defects for exposed issues

---

### Dashboard Views

#### 1. Experiment Status (Real-Time)

```
RUNNING EXPERIMENTS (last 24h)
┌──────────────────────────────────────────────────────┐
│ 550e8400  api_latency_injection  stage               │
│ Started: 10:30 | Elapsed: 2m 15s | p95: 1850ms       │
│ Error: 2.1% ✅ | Status: RUNNING 🔄                  │
├──────────────────────────────────────────────────────┤
│ (no other running experiments)                        │
└──────────────────────────────────────────────────────┘
```

#### 2. Historical Timeline

```
LAST 10 RUNS (by creation date)
┌───────┬────────────────────────────┬──────┬──────────┐
│ ID    │ Experiment                 │ Env  │ Status   │
├───────┼────────────────────────────┼──────┼──────────┤
│ 550e8 │ api_latency_injection      │ stg  │ ✅ DONE  │
│ 661f9 │ db_connection_saturation   │ dev  │ 🔁 RBCK  │
│ 7723a │ high_concurrency_spike     │ stg  │ ⛔ ABRT  │
│ ...   │ ...                        │ ...  │ ...      │
└───────┴────────────────────────────┴──────┴──────────┘
```

#### 3. Metrics Scorecard

```
CHAOS ENGINEERING METRICS (30-DAY WINDOW)
┌─────────────────────────────────────────┐
│ MTTR                     42.5 sec  ✅    │
│ Target: < 60 sec                        │
│                                         │
│ Auto-Recovery Rate       87.5%     ✅    │
│ Target: ≥ 85%                          │
│                                         │
│ Rollback Frequency       3 / month  ✅   │
│ Target: ≤ 5 / month                    │
│                                         │
│ Failed Resilience Tests  1 / month  ⚠️   │
│ Target: ≤ 2 / month                    │
│ → File S2 defects for exposed issues    │
└─────────────────────────────────────────┘
```

#### 4. Environment Breakdown

```
RUNS BY ENVIRONMENT (30 days)
┌────────┬───────┬─────────────┬──────────┐
│ Env    │ Total │ Completed   │ Rollback │
├────────┼───────┼─────────────┼──────────┤
│ dev    │   15  │  13 (86%)   │ 2        │
│ stage  │   12  │  10 (83%)   │ 2        │
│ prod   │    3  │   3 (100%)  │ 0        │
└────────┴───────┴─────────────┴──────────┘
```

---

### Dashboard Tools

**1. Prometheus Metrics Export**

The chaos runner emits metrics via structured JSON logs:
```json
{
  "timestamp": "2026-02-22T10:35:05Z",
  "level": "INFO",
  "logger": "packages.chaos.runner",
  "event": "chaos_metric_recorded",
  "experiment_id": "550e8400-e29b-41d4-a716-446655440000",
  "experiment": "api_latency_injection",
  "error_rate_pct": 2.1,
  "p95_latency_ms": 1850,
  "active_connections": 42
}
```

**Ingestion:** CloudLogging → BigQuery → Looker Dashboard

**2. Grafana Dashboard**

Import the Grafana JSON dashboard:
```bash
curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Authorization: Bearer <grafana_api_token>" \
  -d @docs/chaos-engineering/grafana-dashboard.json
```

**3. Custom Alerts**

Set up alerts for:
- Experiment failed to start (check SafetyController logs)
- Rollback triggered (indicates issue exposed)
- MTTR trending up (system becoming less resilient)

---

## Defect Integration

### Pre-Experiment Defect Check

```python
SafetyController._check_no_active_defects()
```

**Flow:**
1. Before experiment starts, query defect API
2. Filter for severity=S1 or S2
3. If any found → raise `ActiveDefectError` → chaos blocked

**Endpoint:**
```
GET /internal/defects?severity=S1,S2&status=open
```

**Response:**
```json
{
  "count": 1,
  "defects": [
    {
      "id": "S1-2026-001",
      "title": "Database connection pool exhausted under load",
      "severity": "S1",
      "created_at": "2026-02-20T14:30:00Z"
    }
  ]
}
```

---

### Runtime Defect Detection

During `_execute_loop()`, check for new S1/S2 defects every poll interval:

```python
async def _execute_loop(...):
    while elapsed < experiment.max_duration_sec:
        metrics = await _sample_metrics(...)
        
        # Check for S1 defects created during experiment
        active_defects = await check_active_defects()
        if any(d.severity == "S1" for d in active_defects):
            → AbortConditionError("S1 defect triggered")
```

---

### Post-Experiment Defect Correlation

After experiment completes (or fails), correlate any new S1/S2 defects:

```python
async def _persist_run_end(run_id, status):
    # Check for defects created during [started_at, ended_at]
    defects = await query_defects(
        created_after=run.started_at,
        created_before=run.ended_at
    )
    
    for defect in defects:
        # Link to chaos run
        defect.triggered_by_run_id = run_id
        defect.triggered_by_experiment = run.experiment_name
        await session.flush()
```

**Benefit:** Audit trail shows which chaos experiments exposed which defects.

---

## Production Runbook

### Pre-Experiment Checklist

- [ ] **Experiment Approved**: Compliance team has approved prod chaos plan
- [ ] **No Active S1/S2 Defects**: Run `/chaos_list prod` to confirm no blockers
- [ ] **Incident Commander On-Call**: Someone can intervene if needed
- [ ] **Monitoring Active**: CloudMonitoring dashboards loaded and watched
- [ ] **Rollback Plan Verified**: Understand rollback strategy for this experiment
- [ ] **Communication**: Notify #platform-resilience Slack channel 30 min before start
- [ ] **Canary Approval**: Traffic routing to only 5% for prod runs

### Execution Steps

**Example: Run `high_concurrency_spike` on prod**

1. **Send Telegram Command:**
   ```
   /chaos_run high_concurrency_spike prod --approve
   ```

2. **Monitor Real-Time:**
   - Open CloudMonitoring dashboard
   - Watch error_rate, p95_latency in the graph panel
   - Run `/chaos_history` to check status

3. **Expected Behavior:**
   - p95 latency rises to ~2800 ms (within 3000 ms abort threshold)
   - Error rate stays < 5% (within abort threshold)
   - After 5 minutes, experiment completes normally

4. **If Abort Triggered:**
   - Rollback starts automatically (k6 load stopped)
   - Wait 2–3 minutes for services to cool down
   - Check metrics return to baseline
   - File S2 defect if performance didn't meet SLA

5. **Debrief:**
   - Document MTTR in runbook
   - Review logs for unexpected issues
   - Share findings in #platform-resilience

### Emergency Stop Procedure

**If experiment causes uncontrolled impact:**

1. **Immediate Stop:**
   ```
   /chaos_stop <run_id>
   ```

2. **Verify Rollback:**
   ```
   /chaos_history
   # Check status shows "rolled_back" or "completed"
   ```

3. **Check System Health:**
   - Error rate returned to baseline < 1%?
   - p95 latency returned to baseline < 500 ms?
   - All services responding?

4. **If Not Recovered:**
   ```
   # Manually restart services
   gcloud run services update inka-api --region europe-west1 \
     --image gcr.io/inka-prod/inka-api:latest
   ```

5. **File S1 Defect:**
   ```
   Title: "Chaos rollback failed for <experiment>"
   Description: Attach logs, recovery steps, impact window
   ```

---

## FAQ & Troubleshooting

### Q: How do I get access to chaos commands?

**A:** Contact your admin to add the `resilience_authority` role:
```bash
UPDATE users SET role = 'resilience_authority' WHERE telegram_id = 123456789;
```

---

### Q: Can I run experiments on production?

**A:** Yes, but:
1. Only pre-approved experiments (`requires_compliance=true`)
2. Must pass `--approve` flag
3. Requires no active S1/S2 defects
4. Limited to 5% traffic canary mode
5. Max duration 5 minutes

---

### Q: What happens if an experiment causes a real incident?

**A:**
1. Abort is triggered automatically (error/latency threshold breached)
2. Rollback handler executes (removes chaos injection)
3. System typically recovers in 30–90 seconds (MTTR)
4. File S2 defect for the resilience gap exposed

---

### Q: Why was my experiment blocked?

**Common reasons:**
- **EnvironmentGateError**: Experiment not allowed in that env
  - e.g., `random_500_injection` only for dev/stage
- **ComplianceGateError**: Prod experiments need `--approve`
- **ActiveDefectError**: Active S1/S2 defect blocks prod chaos

**Troubleshoot:**
```
/chaos_list stage          # Check if experiment allowed in stage
/chaos_run <exp> stage     # Try a non-prod env first
```

---

### Q: How do I monitor a running experiment?

**Options:**
1. **Telegram:** `/chaos_history` (updates every poll interval)
2. **CloudMonitoring:** Open dashboard, watch error_rate & p95_latency graphs
3. **Logs:** Grep for `experiment_id` in CloudLogging

**Example:**
```bash
gcloud logging read \
  "jsonPayload.experiment_id='550e8400-e29b-41d4-a716-446655440000'" \
  --limit 50 --format json | jq .
```

---

### Q: What's the difference between "completed" and "rolled_back"?

| Status | Meaning | Action |
|--------|---------|--------|
| **completed** | Ran full duration without exceeding thresholds | Normal end |
| **rolled_back** | Aborted due to threshold breach; rollback executed | Investigate |
| **failed** | Rollback itself failed; manual intervention needed | Urgent |

---

### Q: Can I customize abort thresholds?

**A:** Thresholds are immutable in the catalog (frozen dataclass). To change:
1. Edit [catalog.py](../../libs/chaos/catalog.py)
2. Adjust `abort_error_rate_pct` / `abort_p95_latency_ms`
3. Redeploy API service

Example:
```python
"api_latency_injection": ExperimentDefinition(
    ...
    abort_error_rate_pct=15.0,  # was 10.0 — more lenient
    ...
)
```

---

### Q: How are metrics persisted?

**A:** All metrics stored in PostgreSQL:
- `chaos_runs` — experiment lifecycle (1 row per run)
- `chaos_metrics` — point-in-time snapshots (polling every 15 sec)

**Query examples:**
```sql
-- MTTR for api_latency_injection
SELECT AVG(r.ended_at - r.started_at) AS mttr_sec
FROM chaos_runs r
WHERE r.experiment_name = 'api_latency_injection'
  AND r.status IN ('completed', 'rolled_back')
  AND r.created_at > NOW() - INTERVAL '30 days';

-- Auto-recovery rate
SELECT 
  100.0 * COUNT(CASE WHEN status = 'completed' THEN 1 END) 
  / COUNT(*) AS recovery_pct
FROM chaos_runs
WHERE created_at > NOW() - INTERVAL '30 days';
```

---

### Q: Can chaos experiments run concurrently?

**A:** Yes, but **not recommended for prod**:
- Multiple experiments → multiplicative blast radius
- Harder to isolate which experiment caused an issue

**Suggestion:**
- Dev/stage: Run experiments in parallel (test interaction effects)
- Prod: Run one experiment at a time, 1 per week max

---

## Integration Checklist

### Deployment Governor Integration

- [ ] Add chaos run_id to deployment context
- [ ] Block deployments during active chaos runs
- [ ] Link deployment to chaos test results

**Code:**
```python
async def can_deploy(service):
    active_runs = await get_active_chaos_runs()
    if active_runs:
        raise DeploymentBlockedError(
            f"Active chaos runs: {active_runs}"
        )
```

---

### Risk Predictor Integration

- [ ] Score changes based on chaos test results
- [ ] Lower risk score for well-tested resilience properties
- [ ] Increase risk score for exposed weaknesses

**Code:**
```python
chaos_score = await compute_chaos_resilience_score(
    auto_recovery_rate=87.5,
    mttr_sec=42.5,
    failed_tests=1
)
# Low chaos_score → High product_risk_score
```

---

### CI/CD Pipeline Integration

- [ ] Automatically run chaos tests on staging after deployment
- [ ] Fail CI pipeline if MTTR > SLA or auto_recovery_rate < 85%
- [ ] Archive metrics to artifacts

**Example Workflow:**
```yaml
post-deploy-stage:
  - name: Run Chaos Tests
    run: |
      /chaos_run api_latency_injection stage
      /chaos_run db_connection_saturation stage
      sleep 600  # wait for runs to complete
      
      # Check metrics
      MTTR=$(curl /chaos/metrics | jq .avg_mttr_sec)
      if [ $MTTR -gt 60 ]; then
        echo "MTTR SLA failed: $MTTR > 60s"
        exit 1
      fi
```

---

## References

- [INKA Architecture](../architecture/README.md)
- [Defect System](../operations/defects.md)
- [Deployment Governor](../operations/deployment-governor.md)
- [Risk Predictor](../operations/risk-predictor.md)
- [Cloud Run Runbook](../operations/cloud-run.md)

---

**Questions?** Reach out to #platform-resilience on Slack or file an issue on the chaos backlog.

**Last Updated:** February 2026  
**Maintainer:** Platform Engineering Team
