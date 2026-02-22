# Self-Healing Agent — INKA Admin

**System:** INKA Admin  
**Role:** Self-Healing Agent  
**Status:** `ACTIVE`  
**Last Updated:** 2026-02-22  
**Authority Level:** `resilience_authority` + `admin`

---

## Overview

The Self-Healing Agent (SHA) is an autonomous operational responder embedded in the INKA Admin platform. It monitors runtime health signals, applies deterministic, pre-approved mitigation actions, and escalates anomalies that exceed safe autonomous remediation bounds. All decisions are explainable, logged, and subject to RBAC controls. The SHA **never** makes black-box inferences — every action traces to a documented rule.

---

## 1. Detection Matrix

| Signal | Source | Threshold | Severity | Polling Interval |
|---|---|---|---|---|
| **Error Rate Spike** | Cloud Run request metrics | `error_rate > 5%` over 5 min | CRITICAL | 60 s |
| **Latency Breach** | Cloud Run latency p95 | `p95 > 2000 ms` sustained 3 min | HIGH | 60 s |
| **DB Connection Pool Exhaustion** | Cloud SQL / SQLAlchemy pool | `pool_used / pool_max > 90%` | CRITICAL | 30 s |
| **Crash Loop Detection** | Cloud Run instance restarts | `restarts > 3` in 5 min window | CRITICAL | 60 s |
| **Memory Spike** | Cloud Run memory metrics | `memory_usage > 85%` sustained 2 min | HIGH | 60 s |
| **High Break-Glass Frequency** | AuditLog model | `> 3 break-glass sessions` in 1 hr | HIGH | 5 min |
| **Failed Booking Transactions** | API error logs + DB | `booking_fail_rate > 10%` in 10 min | HIGH | 2 min |
| **Failed Webhook Retries** | Telegram webhook delivery logs | `> 5 consecutive failures` | MEDIUM | 30 s |

### Signal Collection Architecture

```
Cloud Run Metrics ──┐
Cloud SQL Metrics ──┤──► Signal Aggregator ──► Threshold Evaluator ──► Decision Engine
App Structured Logs ──┤            (Redis time-series or GCP Monitoring)
AuditLog DB Table ──┘
```

### Signal States

Each monitored signal transitions through:

```
NOMINAL → DEGRADED → CRITICAL → MITIGATION_ACTIVE → RESOLVED / ESCALATED
```

---

## 2. Mitigation Rules

### Rule Catalog

| Rule ID | Trigger Condition | Action | Requires Confirmation | PII Check |
|---|---|---|---|---|
| `SHA-01` | Crash loop detected | Restart Cloud Run revision | Yes (prod) | No |
| `SHA-02` | DB pool exhaustion | Scale up min-instances by +2 | Yes (prod) | No |
| `SHA-03` | Error rate spike + deployment < 30 min | Rollback to last stable revision | Yes (prod) | No |
| `SHA-04` | Memory spike sustained > 2 min | Scale up instances + alert | Yes (prod) | No |
| `SHA-05` | Webhook failures > 5 consecutive | Retry with exponential backoff + alert | No (auto) | No |
| `SHA-06` | High break-glass frequency | Rate-limit non-admin API traffic | Yes (prod) | Yes |
| `SHA-07` | Booking fail rate > 10% | Switch booking endpoints to read-only mode | Yes (prod) | No |
| `SHA-08` | Error rate spike + deployment > 30 min | Disable non-critical features temporarily | Yes (prod) | No |
| `SHA-09` | Redis cache detected stale / corrupted | Flush Redis cache | No (auto) | No |

### Action Specifications

#### `SHA-01` — Restart Cloud Run Revision
```
Target:     Cloud Run service (api | bot | admin)
Method:     gcloud run services update-traffic --to-revisions=LATEST=100
Pre-check:  Verify deployment_age > 5 min (avoid restart during cold start)
Post-check: Monitor error_rate for 3 min post-restart
Rollback:   If error_rate remains > 5% after restart → trigger SHA-03
```

#### `SHA-02` — Scale Up Instances
```
Target:     Cloud Run min-instances
Method:     gcloud run services update --min-instances=<current+2>
Ceiling:    max-instances cap respected; never exceed deployment governor limits
Post-check: Re-evaluate pool utilization after 2 min
```

#### `SHA-03` — Rollback to Last Stable Revision
```
Target:     Cloud Run traffic split
Method:     gcloud run services update-traffic --to-revisions=<STABLE_REVISION>=100
Pre-check:  Confirm stable revision exists and passed health check
Audit:      Full rollback entry with reason, actor=SHA, revision IDs
```

#### `SHA-05` — Webhook Retry with Backoff
```
Strategy:   Exponential backoff — 5s, 10s, 20s, 40s, 80s
Max:        5 retry attempts
After max:  Alert resilience_authority via Telegram + halt retries
```

#### `SHA-06` — Rate-Limit Traffic
```
Method:     Cloud Armor rate-limit rule activation
Threshold:  100 req/min per IP for non-admin routes
Duration:   15 min auto-expiry, renewable
PII Impact: Log that rate-limiting is active; do not log user identifiers
```

#### `SHA-07` — Read-Only Mode
```
Scope:      /api/v1/bookings POST, PUT, DELETE endpoints → return 503 with retry header
Exclusions: Admin override routes remain active
Duration:   10 min auto-expiry
Notification: Telegram alert to admin + resilience_authority
```

---

## 3. Decision Engine

The SHA decision engine is **fully deterministic**. No ML inference. No probabilistic routing. Every branch is an explicit conditional.

### Master Decision Tree

```
START: Signal batch evaluated every 30–60s
│
├─ [ERROR RATE > 5%]
│   ├─ deployment_age < 30 min
│   │   └─► SHA-03: ROLLBACK (pending prod confirmation)
│   └─ deployment_age >= 30 min
│       └─► SHA-08: DISABLE NON-CRITICAL FEATURES
│
├─ [DB_POOL > 90%]
│   └─► SHA-02: SCALE UP INSTANCES
│       └─ if pool still > 90% after 2 min
│           └─► ESCALATE → PagerDuty / Telegram alert
│
├─ [CRASH_LOOP = true] (restarts > 3 in 5 min)
│   └─► SHA-01: RESTART REVISION
│       └─ if crash loop continues after restart
│           └─► SHA-03: ROLLBACK
│
├─ [MEMORY > 85%]
│   └─► SHA-04: SCALE UP + ALERT
│
├─ [WEBHOOK_FAILURES > 5 consecutive]
│   └─► SHA-05: RETRY WITH BACKOFF
│       └─ if max retries reached
│           └─► ALERT + HALT
│
├─ [BREAK_GLASS_FREQ > 3/hr]
│   └─► SHA-06: RATE-LIMIT NON-ADMIN TRAFFIC
│       └─► COMPLIANCE_CHECK (PII involvement?): log PII flag
│
├─ [BOOKING_FAIL_RATE > 10%]
│   └─► SHA-07: READ-ONLY MODE + ALERT
│
├─ [LATENCY P95 > 2000ms]
│   └─ db_pool > 70%?
│   │   └─► SHA-02: SCALE UP
│   └─ db_pool <= 70%?
│       └─► ALERT only (external latency suspected)
│
└─ [ALL SIGNALS NOMINAL]
    └─► No action. Log heartbeat.
```

### Conflict Resolution

If multiple signals fire simultaneously:

| Priority | Rule | Rationale |
|---|---|---|
| 1 | SHA-03 (Rollback) | Highest blast radius prevention |
| 2 | SHA-02 (Scale) | Capacity before features disabled |
| 3 | SHA-07 (Read-Only) | Protect data integrity |
| 4 | SHA-01 (Restart) | Runtime recovery |
| 5 | SHA-08 (Feature disable) | Graceful degradation |
| 6 | SHA-06 (Rate-limit) | Traffic shaping |
| 7 | SHA-05 (Webhook retry) | Background, non-blocking |

---

## 4. Safety Constraints

These are **hard limits** — no rule, operator, or Telegram command overrides them.

| Constraint | Description |
|---|---|
| ❌ **No DB Schema Changes** | SHA never issues DDL statements. Schema changes require human approval via Alembic migration pipeline. |
| ❌ **No RBAC Bypass** | SHA acts as a system service account with scoped IAM permissions. It cannot grant, escalate, or remove permissions. |
| ❌ **No PII Exposure** | SHA logs never contain user PII (names, phone numbers, booking details). Redaction enforced at log-write layer. |
| ❌ **No Deployment Governor Override** | SHA cannot push a new revision. It can only route traffic to existing revisions. Deployment Governor holds the deployment lock. |
| ❌ **No Silent Actions in Prod** | Every prod action requires an audit log entry before execution. Action is aborted if audit write fails. |
| ✅ **Confirmation Gate (Prod)** | All prod mitigation actions (except SHA-05, SHA-09) require resilience_authority acknowledgment via Telegram within 60s, or action is skipped and escalation fires. |
| ✅ **Dry-Run Mode** | SHA can be set to `DRY_RUN` mode — all decisions are logged and alerted but no actions are executed. |
| ✅ **Self-Disable Circuit** | If SHA itself causes 2 consecutive failed mitigations, it sets its own status to `SUSPENDED` and alerts humans. |

### SHA IAM Scope (Principle of Least Privilege)

```yaml
service_account: sha-agent@<PROJECT>.iam.gserviceaccount.com
roles:
  - roles/run.developer          # Update traffic, scale instances
  - roles/monitoring.viewer      # Read metrics
  - roles/logging.viewer         # Read logs
  - roles/redis.editor           # Flush cache (if Redis used)
  # NOT GRANTED:
  # - roles/cloudsql.admin       # No DB access
  # - roles/iam.admin            # No IAM management
```

---

## 5. Interaction with Risk & Compliance

### Compliance Check Protocol

Triggered when:
- `SHA-06` (rate-limiting) fires — potential impact on user access
- Any rollback (`SHA-03`) is executed — version regression risk
- Read-only mode (`SHA-07`) activated — service degradation

```
COMPLIANCE_CHECK:
  1. Query ComplianceFramework: is active_compliance_window? (maintenance, audit period)
  2. Is PII involved in the mitigation scope? → flag in audit log
  3. Is action within approved change window? → if not, add EMERGENCY flag
  4. Write compliance_check_result to AuditLog before action execution
  5. If compliance_score < threshold → ESCALATE instead of auto-mitigate
```

### Risk Predictor Integration

SHA reads the AI Risk Predictor output before executing rollback decisions:

```
IF risk_score > HIGH AND rollback_target_revision.risk_score > CURRENT.risk_score:
    → Do NOT rollback. Alert only.
    → Reason: rolling back to a higher-risk revision is counterproductive.
```

### Incident Classification

| SHA Action | Incident Severity | Required Notification |
|---|---|---|
| SHA-05 (webhook retry) | P4 — Low | Telegram log only |
| SHA-09 (cache flush) | P4 — Low | Telegram log only |
| SHA-01 (restart) | P3 — Medium | Telegram alert to admin |
| SHA-02 (scale up) | P3 — Medium | Telegram alert to admin |
| SHA-04 (memory scale) | P3 — Medium | Telegram alert to admin |
| SHA-08 (feature disable) | P2 — High | Telegram + email |
| SHA-06 (rate-limit) | P2 — High | Telegram + compliance |
| SHA-07 (read-only) | P2 — High | Telegram + compliance + email |
| SHA-03 (rollback) | P1 — Critical | Full escalation chain |

---

## 6. Audit Requirements

### Audit Log Schema

Every SHA action writes to the `AuditLog` table and to GCP Cloud Logging:

```python
class SHAAuditEntry(BaseModel):
    id:               UUID
    timestamp:        datetime          # UTC, microsecond precision
    signal_id:        str               # e.g. "error_rate_spike"
    signal_value:     float             # measured value at trigger time
    rule_id:          str               # e.g. "SHA-03"
    action_taken:     str               # human-readable description
    target_service:   str               # e.g. "api", "bot"
    target_revision:  str | None        # Cloud Run revision name
    environment:      Literal["dev", "stage", "prod"]
    triggered_by:     str               # "SHA_AGENT" or Telegram user_id
    confirmation_by:  str | None        # operator who confirmed (prod)
    confirmation_at:  datetime | None
    pii_involved:     bool
    compliance_check: dict              # result of compliance protocol
    outcome:          Literal["EXECUTED", "SKIPPED", "ESCALATED", "FAILED"]
    outcome_reason:   str
    dry_run:          bool
```

### Retention

| Log Type | Retention | Storage |
|---|---|---|
| SHA Audit Entries | 2 years | Cloud SQL AuditLog + GCS archive |
| Signal Snapshots | 90 days | GCP Monitoring / BigQuery |
| Action Confirmations | 2 years | AuditLog (linkable to entry) |

### Non-Repudiation Requirements

- All audit entries are **append-only** — no UPDATE or DELETE permitted on AuditLog rows
- Entries written with `created_at` timestamp from database clock (not application)
- Entries include full signal context (value, threshold, window) — no post-hoc modification possible

### Audit Query Endpoints

```
GET /api/v1/admin/sha/audit?from=<ISO>&to=<ISO>&rule=<SHA-XX>&env=<prod>
GET /api/v1/admin/sha/audit/<entry_id>
```

Access: `admin`, `resilience_authority`, `compliance_officer`

---

## Telegram Command Specification

### Commands

| Command | Description | Access |
|---|---|---|
| `/selfheal status` | Show current SHA operational status, active signals, active mitigation | `admin`, `resilience_authority` |
| `/selfheal last-actions` | Show last 10 SHA actions with rule, outcome, timestamp | `admin`, `resilience_authority` |
| `/selfheal disable` | Set SHA to `SUSPENDED` state — no auto-mitigations until re-enabled | `admin`, `resilience_authority` |
| `/selfheal enable` | Re-activate SHA from `SUSPENDED` state | `admin`, `resilience_authority` |

### Command Response Format

#### `/selfheal status`
```
🤖 Self-Healing Agent — Status
────────────────────────────
Mode:       ACTIVE (DRY_RUN: OFF)
Environment: prod

Active Signals:
  ✅ error_rate       → 1.2% (OK)
  ⚠️  latency_p95     → 1850ms (DEGRADED)
  ✅ db_pool          → 62% (OK)
  ✅ webhook          → OK

Last Action: SHA-02 @ 2026-02-22T07:14:00Z → EXECUTED
Next evaluation: 32s
```

#### `/selfheal last-actions`
```
📋 SHA — Last 10 Actions
────────────────────────────
1. SHA-02 | Scale Up    | prod | EXECUTED | 07:14:00
2. SHA-05 | WH Retry    | prod | EXECUTED | 06:58:12
3. SHA-01 | Restart     | prod | SKIPPED (no confirm) | 06:45:00
...
```

#### `/selfheal disable`
```
⚠️ SHA will be SUSPENDED.
All auto-mitigations will halt.
Escalation alerts remain active.

Confirm: /selfheal disable confirm
[Audit log entry created: SHA_SUSPEND request by @user]
```

#### `/selfheal enable`
```
✅ SHA re-activated.
Mode: ACTIVE
[Audit log entry created: SHA_ACTIVATE by @user]
```

### Confirmation Flow (Prod Actions)

```
SHA detects trigger → sends Telegram alert:

  🚨 SHA — Action Required
  Rule: SHA-03 (Rollback)
  Env:  prod
  Signal: error_rate = 8.3% | deployment_age = 12m
  Target: api → revision-20260222-v42
  
  ⏱ Confirm within 60s or action will be SKIPPED.
  
  ✅ /selfheal confirm <action_id>
  ❌ /selfheal reject <action_id>
```

---

## Integration Points

| System | Interaction |
|---|---|
| **Deployment Governor** | SHA reads deployment lock; never writes. Rolls back only to revisions pre-approved by Governor. |
| **AI Risk Predictor** | SHA reads risk score before rollback to ensure target revision is lower risk. |
| **Quality Score System** | SHA checks quality score of rollback target (must be ≥ 80). |
| **Chaos Engineering Framework** | During chaos experiments, SHA is informed via experiment context. SHA actions are suppressed if signal is experiment-induced. |
| **Compliance & Audit Framework** | SHA runs compliance checks before high-severity actions; writes to shared AuditLog. |
| **Observability Stack** | SHA publishes its own metrics: `sha_actions_total`, `sha_signals_active`, `sha_escalations_total`. |

---

## SHA State Machine

```
         ┌──────────────────────────────────────┐
         │                                      │
    ┌────▼────┐     signal detected     ┌───────┴──────┐
    │ NOMINAL │────────────────────────►│ EVALUATING   │
    └────┬────┘                         └──────┬───────┘
         │                                     │
         │          no action needed           │ rule matched
         │◄────────────────────────────────────┤
         │                                     │
         │                          ┌──────────▼──────────┐
         │                          │ AWAITING_CONFIRMATION│ (prod only)
         │                          └──────────┬──────────┘
         │                                     │ confirmed / auto (non-prod)
         │                          ┌──────────▼──────────┐
         │      resolved            │  MITIGATING          │
         │◄─────────────────────────│                      │
         │                          └──────────┬──────────┘
         │                                     │ failed / exceeded limits
         │                          ┌──────────▼──────────┐
         │                          │     ESCALATED        │
         │                          └─────────────────────┘
         │
    ┌────▼────┐
    │SUSPENDED│ (/selfheal disable)
    └─────────┘
```

---

## Definition of Done

- [ ] All signals in Detection Matrix have implemented collectors
- [ ] All 9 mitigation rules have runbook-backed implementations
- [ ] Decision tree logic is unit-tested with 100% branch coverage
- [ ] Prod confirmation gate is tested end-to-end via Telegram flow
- [ ] Audit log schema migrated and append-only constraints verified
- [ ] SHA IAM service account provisioned with least-privilege roles
- [ ] `/selfheal` Telegram commands restricted to `admin` + `resilience_authority`
- [ ] SHA publishes `sha_actions_total` metric to GCP Monitoring
- [ ] SHA self-disable circuit breaker tested
- [ ] Chaos Engineering Framework informed of SHA suppression logic
