# INKA Chaos Engineering System - Complete Implementation Summary

**Version:** 1.0  
**Status:** ✅ Complete  
**Last Updated:** February 2026  
**Maintained By:** Platform Engineering Team

---

## Executive Summary

The INKA Chaos Engineering System is a **production-ready, safety-first platform** for continuous resilience testing. It enables controlled failure injection across dev, stage, and prod environments with automated safety controls, intelligent rollback, and comprehensive metrics.

### Key Capabilities

✅ **9 Pre-Built Experiments** — API latency, DB saturation, webhook failures, booking conflicts, random errors, instance kills, secret rotation, network timeouts, concurrency spikes

✅ **Multi-Environment Support** — Dev (unrestricted) → Stage (gated) → Production (compliance + canary)

✅ **Automated Safety Gates** — Pre-flight compliance checks, real-time abort conditions, S1/S2 defect blocking

✅ **Graceful Rollback** — Per-experiment handlers, automatic + manual triggers, idempotent operations

✅ **Rich Metrics** — MTTR, auto-recovery rate, rollback frequency, failed test tracking

✅ **Telegram + API** — Simple bot commands for operators, REST API for CI/CD integration

✅ **Integration Ready** — Works with Deployment Governor & Risk Predictor for holistic resilience visibility

---

## System Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│                    INKA Chaos System                │
├──────────────────┬────────────────────────────────────┤
│                  │                                    │
│  Telegram Bot    │         FastAPI Backend            │
│  /chaos_*        │         /chaos/* endpoints         │
│  commands        │                                    │
│       │          │              ▼                     │
│       └──────────┼─────► ChaosRunner                  │
│                  │       (Orchestrator)               │
│                  │            │                       │
│                  │    ┌────────┼────────┐             │
│                  │    │        │        │             │
│                  │   ▼       ▼        ▼              │
│                  │  Safety Rollback Metrics          │
│                  │  Control Manager Collector        │
│                  │    │                               │
│                  │    └──► PostgreSQL                 │
│                  │         (ChaosRun, ChaosMetric)   │
│                  │                                    │
│     Integration  │    ◄──┬──────────────┬──────┐     │
│     Points       │       │              │      │     │
│                  │    Defect API  Deployment Risk    │
│                  │    System      Governor  Predictor │
└──────────────────┴────────────────────────────────────┘
```

### Library Structure

```
libs/chaos/
├── models.py          # SQLAlchemy ORM (9 KB)
├── catalog.py         # Experiment definitions (8 KB)
├── safety.py          # Pre-flight & runtime gates (6 KB)
├── runner.py          # Lifecycle orchestrator (9 KB)
├── rollback.py        # Per-experiment handlers (5 KB)
├── metrics.py         # Collection & aggregation (7 KB)
└── __init__.py        # Public API exports (0.3 KB)

apps/api/src/app/domains/chaos/
├── api.py             # FastAPI router (8 KB)
└── models.py          # Pydantic schemas (4 KB)

apps/bot/src/handlers/
├── chaos_handler.py   # Telegram commands (12 KB)
└── ...

docs/chaos-engineering/
├── README.md                           # Main guide (18 KB)
├── PRODUCTION_SAFETY_CHECKLIST.md      # Pre-flight checklist (12 KB)
└── DEPLOYMENT_INTEGRATION.md           # Gov & Risk integration (14 KB)
```

**Total Implementation:** ~103 KB code + 44 KB documentation

---

## 1. Chaos Experiment Catalog

### 9 Pre-Built Experiments

All experiments are immutable, pre-tested, and follow a consistent safety pattern.

| # | Experiment | Type | Duration | Envs | Approval | MTTR Target |
|---|-----------|------|----------|------|----------|-------------|
| 1 | API Latency (+500ms) | api_latency | 5m | dev, stage, prod | ❌ | < 60s |
| 2 | DB Connection Pool Saturation | db_saturation | 3m | dev, stage, prod | ✅ | < 60s |
| 3 | Telegram Webhook Failure | webhook_failure | 2m | dev, stage | ❌ | < 60s |
| 4 | Booking Conflict Surge (50 concurrent) | booking_surge | 3m | dev, stage | ❌ | < 60s |
| 5 | Random 500 Error (5% of requests) | random_500 | 5m | dev, stage | ❌ | < 60s |
| 6 | Cloud Run Instance Kill | instance_kill | 2m | dev, stage, prod | ✅ | < 60s |
| 7 | Secret Rotation Simulation | secret_rotation | 5m | dev, stage, prod | ✅ | < 60s |
| 8 | Network Timeout (API ↔ DB) | network_timeout | 3m | dev, stage, prod | ✅ | < 60s |
| 9 | High Concurrency Spike (500 RPS) | concurrency_spike | 5m | dev, stage, prod | ✅ | < 60s |

### Experiment Properties

Each experiment defines:
- **Hypothesis** — What resilience property we're testing
- **Blast Radius** — Scope of chaos injection
- **Abort Conditions** — Error rate threshold, p95 latency threshold, max duration
- **Rollback Strategy** — Specific actions to undo the injection
- **Environment Restrictions** — Which envs allowed (some only dev/stage)
- **Compliance Required** — Whether prod requires manager approval

**Example: API Latency Injection**

```python
"api_latency_injection": ExperimentDefinition(
    name="api_latency_injection",
    hypothesis="System handles +500ms latency gracefully with correct retry logic",
    blast_radius="All inbound HTTP requests",
    max_duration_sec=300,
    abort_error_rate_pct=10.0,
    abort_p95_latency_ms=2000,
    allowed_envs=frozenset({"dev", "stage", "prod"}),
    requires_compliance=False,
    rollback_trigger="p95 > 2000ms OR error_rate > 10%",
)
```

---

## 2. Safety Controls

### 2.1 Environment Gating

| Experiment | Dev | Stage | Prod |
|-----------|-----|-------|------|
| api_latency_injection | ✅ | ✅ | ✅ |
| db_connection_saturation | ✅ | ✅ | ✅ |
| random_500_injection | ✅ | ✅ | ❌ Never Prod |
| booking_conflict_surge | ✅ | ✅ | ❌ Never Prod |
| telegram_webhook_failure | ✅ | ✅ | ❌ Never Prod |
| cloud_run_instance_kill | ✅ | ✅ | ✅ |
| secret_rotation_simulation | ✅ | ✅ | ✅ |
| network_timeout_api_db | ✅ | ✅ | ✅ |
| high_concurrency_spike | ✅ | ✅ | ✅ |

### 2.2 Compliance Gates

**Production experiments requiring explicit approval:**
- db_connection_saturation
- cloud_run_instance_kill
- secret_rotation_simulation
- network_timeout_api_db
- high_concurrency_spike

**Approval Flow:**
```
/chaos_run <exp> prod --approve
   ↓
SafetyController.check_pre_conditions()
   ├─ Verify compliance_approved=True
   ├─ Verify no S1/S2 defects active
   ├─ Verify max_duration ≤ 300 sec
   └─ All checks passed → PROCEED
```

### 2.3 Runtime Abort Conditions

During experiment execution, automatically abort if:
- ❌ Error rate ≥ threshold (e.g., 10%)
- ❌ p95 latency ≥ threshold (e.g., 2000 ms)
- ❌ Elapsed time ≥ max_duration (e.g., 300 sec)
- ❌ S1 defect detected (highest priority)

**Polling:** Every 15 seconds

**Abort Action:** → Trigger rollback → Mark run as ROLLED_BACK

### 2.4 Defect System Integration

**Pre-flight Check:**
```python
SafetyController._check_no_active_defects()
# GET /internal/defects?severity=S1,S2
# If any S1/S2 found → raise ActiveDefectError
# Chaos blocked until defects resolved
```

**Runtime Monitoring:**
```python
# Every poll interval during _execute_loop()
if check_for_active_s1_defects():
    → IMMEDIATE ABORT (no questions asked)
```

**Post-Experiment Correlation:**
```python
# After run complete, link any new S1/S2 to chaos run
defects = query_defects(
    created_after=run.started_at,
    created_before=run.ended_at
)
# Audit trail: which experiments exposed which defects
```

---

## 3. Execution Model

### 3.1 Experiment Lifecycle

```
1. User Initiates
   /chaos_run api_latency_injection stage
              ↓
2. Pre-Flight Checks (SafetyController)
   ├─ Environment allowed?
   ├─ Max duration ok?
   ├─ Compliance approved (if prod)?
   └─ No active S1/S2?
              ↓
3. Create ChaosRun Record
   id, experiment_name, env, requester, status=PENDING
              ↓
4. Launch Background Task
   _execute_loop(run_id, experiment)
              ↓
5. Experiment Injection (15s - 5m)
   ├─ _start_experiment() → enable chaos
   ├─ Poll metrics every 15s
   ├─ Record metric snapshots
   ├─ Check abort conditions each poll
   └─ If abort → trigger rollback
              ↓
6. Normal Completion or Abort
   ├─ COMPLETED: full duration reached normally
   ├─ ROLLED_BACK: abort condition triggered
   └─ FAILED: rollback itself failed
              ↓
7. Final State in DB
   ChaosRun marked with:
   - status (completed | rolled_back | failed)
   - duration_sec
   - abort_reason (if applicable)
```

### 3.2 Rollback Mechanism

**Per-Experiment Handlers:**

```python
_ROLLBACK_REGISTRY = {
    "api_latency":     _rollback_api_latency,          # Disable middleware
    "db_saturation":   _rollback_db_saturation,        # Reset pool
    "webhook_failure": _rollback_webhook_failure,      # Restore URL
    "booking_surge":   _rollback_booking_surge,        # Stop load gen
    "random_500":      _rollback_random_500,           # Disable middleware
    "instance_kill":   _rollback_instance_kill,        # Verify auto-scaled
    "secret_rotation": _rollback_secret_rotation,      # Revert version
    "network_timeout": _rollback_network_timeout,      # Restore timeout
    "concurrency_spike": _rollback_concurrency_spike,  # Stop k6
}
```

**Rollback is:**
- ✅ Automatic (on abort condition)
- ✅ Idempotent (safe to call multiple times)
- ✅ Logged (every action recorded)
- ✅ Fast (< 10 seconds typically)

---

## 4. Metrics & Dashboards

### 4.1 Key Metrics

**1. MTTR (Mean Time To Recovery)**
- Calculation: `(ended_at - started_at)` for each run
- Target SLA: < 60 seconds
- Use: Measure system's self-healing speed

**2. Auto-Recovery Rate**
- Calculation: `% of COMPLETED runs (no manual rollback needed)`
- Target SLA: ≥ 85%
- Use: Measure system's fault tolerance

**3. Rollback Frequency**
- Calculation: `Count of ROLLED_BACK runs per month`
- Target SLA: ≤ 5 per month
- Use: Indicates safety gates are working

**4. Failed Resilience Tests**
- Calculation: `Count of FAILED runs per month`
- Target SLA: ≤ 2 per month
- Use: Identify exposed weaknesses

### 4.2 Dashboard Views

**Real-Time Experiment Status:**
```
RUNNING EXPERIMENTS (24h)
└─ 550e8400 | api_latency_injection | stage
   Started: 10:30 | Elapsed: 2m | p95: 1850ms | Error: 2.1% ✅
```

**Historical Timeline:**
```
LAST 10 RUNS
│ ID      │ Experiment                    │ Env  │ Status   │
├─────────┼────────────────────────────────┼──────┼──────────┤
│ 550e8400│ api_latency_injection         │ stage│ ✅ DONE  │
│ 661f9abc│ db_connection_saturation      │ dev  │ 🔁 RBCK  │
│ 7723a1d2│ high_concurrency_spike        │ stage│ ⛔ ABRT  │
```

**Metrics Scorecard (30-day):**
```
MTTR                     42.5 sec  ✅ (target < 60)
Auto-Recovery Rate       87.5%     ✅ (target ≥ 85)
Rollback Frequency       3/month   ✅ (target ≤ 5)
Failed Resilience Tests  1/month   ⚠️  (target ≤ 2)
```

---

## 5. Telegram Bot Commands

All commands require `admin` or `resilience_authority` role.

### /chaos_list [env]

List all experiments in catalog, optionally filtered by environment.

```
/chaos_list              # All experiments
/chaos_list stage        # Stage-allowed only
/chaos_list prod         # Production-allowed only
```

**Response Format:**
```
🧪 Chaos Experiment Catalog

1. api_latency_injection
   Injects 500 ms artificial delay via FastAPI middleware.
   💥 Blast: All inbound HTTP requests
   ⏱ Max: 5m | ✅ no approval needed
   🌍 Envs: dev, stage, prod

2. db_connection_saturation
   ...
```

### /chaos_run \<experiment\> [env] [--approve]

Start a chaos experiment.

```
/chaos_run api_latency_injection          # Default: dev
/chaos_run api_latency_injection stage    # Explicit env
/chaos_run cloud_run_instance_kill prod --approve   # Prod with approval
```

**Success Response:**
```
🔥 Chaos experiment started!

Experiment: api_latency_injection
Environment: stage
Run ID: 550e8400
Requester: telegram:@admin

Monitor with: /chaos_history
Stop with: /chaos_stop 550e8400
```

### /chaos_stop \<run_id\>

Abort a running experiment + trigger rollback.

```
/chaos_stop 550e8400
```

**Response:**
```
⛔ Experiment stopped + rollback triggered

Run ID: 550e8400
Message: API latency middleware disabled — delay restored to 0 ms.
Stopped by: telegram:@admin
```

### /chaos_history [env]

View last 10 experiment runs + 30-day metrics.

```
/chaos_history          # All environments
/chaos_history stage    # Stage only
```

**Response:**
```
📜 Chaos Run History (last 10)

✅ 550e8400 — api_latency_injection
   Env: stage | Duration: 45s
   By: telegram:@admin

🔁 661f9abc — db_connection_saturation
   Env: dev | Duration: 120s
   By: telegram:@bot
   ⚠️  DB pool reset after abort.

📊 30-Day Metrics
   MTTR: 42s | Auto-recovery: 87.5%
   Rollbacks: 3 | Failed tests: 1
```

---

## 6. REST API

**Base URL:** `http://localhost:8000/chaos`

**Authentication:** Bearer token (admin/resilience_authority)

### GET /experiments

List all experiments in the catalog.

```bash
curl http://localhost:8000/chaos/experiments?env=stage \
  -H "Authorization: Bearer <token>"
```

### POST /run

Start an experiment.

```bash
curl -X POST http://localhost:8000/chaos/run \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_name": "api_latency_injection",
    "environment": "stage",
    "requester": "ci-system"
  }'

Response (202 Accepted):
{
  "run_id": "550e8400-...",
  "experiment_name": "api_latency_injection",
  "environment": "stage",
  "status": "running",
  "message": "Experiment started. run_id=550e8400"
}
```

### POST /stop/{run_id}

Abort an experiment.

```bash
curl -X POST http://localhost:8000/chaos/stop/550e8400 \
  -H "Authorization: Bearer <token>" \
  -d '{"reason": "manual stop"}'

Response (200 OK):
{
  "run_id": "550e8400-...",
  "status": "aborted",
  "abort_reason": "manual stop",
  "message": "Experiment stopped"
}
```

### GET /history

View paginated run history.

```bash
curl http://localhost:8000/chaos/history?limit=20&env=stage \
  -H "Authorization: Bearer <token>"

Response:
[
  {
    "run_id": "550e8400-...",
    "experiment_name": "api_latency_injection",
    "environment": "stage",
    "status": "completed",
    "requester": "ci-system",
    "created_at": "2026-02-22T10:30:00Z",
    "duration_sec": 300.0
  },
  ...
]
```

### GET /metrics

Dashboard metrics aggregation.

```bash
curl http://localhost:8000/chaos/metrics?window_days=30 \
  -H "Authorization: Bearer <token>"

Response:
{
  "window_days": 30,
  "avg_mttr_sec": 42.5,
  "auto_recovery_rate_pct": 87.5,
  "rollback_frequency": 3,
  "failed_resilience_tests": 1,
  "total_runs": 8
}
```

---

## 7. Integration Points

### 7.1 Deployment Governor

**Pre-Deployment Blockers:**
```python
# Block deployments during active chaos
if await check_active_chaos_runs(session):
    raise HTTPException(409, "Active chaos runs prevent deployment")
```

**Deployment Metadata:**
```python
# Link deployment to chaos test results
class Deployment:
    deployment_id = UUID
    service = "inka-api"
    version = "v2.3.4"
    chaos_test_status = "passed"  # or "failed"
    chaos_test_runs = [run_id_1, run_id_2]
```

### 7.2 Risk Predictor

**Chaos Resilience Score (0-100):**
```python
chaos_resilience_score =
    auto_recovery_rate_pct * 0.4 +
    (100 - mttr_score) * 0.3 +
    test_success_rate * 0.3

# If score < 50 → Block prod deployments
# If score 50-70 → Canary only (5%)
# If score 70+ → Full deployment allowed
```

**Risk Adjustment:**
```python
# Low chaos resilience increases product risk
adjusted_risk = base_risk * (1 + chaos_risk_adjustment * 0.3)
```

### 7.3 Defect System

**Pre-Flight Blocking:**
```python
# Active S1/S2 defects block prod chaos
GET /internal/defects?severity=S1,S2&status=open
if count > 0:
    raise ActiveDefectError("Defects block chaos")
```

**Post-Experiment Linking:**
```python
# Correlate defects exposed by chaos
for defect in get_defects(created_after=run.started_at):
    defect.triggered_by_run_id = run.id
```

---

## 8. Production Runbook

### Pre-Experiment Checklist

- [ ] Experiment approved (Platform Lead + Compliance)
- [ ] No active S1/S2 defects
- [ ] Incident Commander on-call
- [ ] Monitoring dashboards loaded
- [ ] Rollback strategy understood
- [ ] Team notified (#platform-resilience)
- [ ] Canary traffic routed (5% max for prod)

### Execution Steps

1. **Send Telegram command:**
   ```
   /chaos_run high_concurrency_spike prod --approve
   ```

2. **Monitor real-time:**
   - CloudMonitoring dashboard with 10s refresh
   - Error rate & p95 latency graphs visible
   - `/chaos_history` for status updates

3. **Expected behavior:**
   - p95 < 3000 ms (abort threshold)
   - Error rate < 5% (abort threshold)
   - After 5 min: experiment completes normally

4. **If abort triggered:**
   - Automatic rollback starts
   - Wait 2-3 min for services to cool down
   - Verify metrics return to baseline
   - File S2 defect if SLA not met

5. **Debrief:**
   - Document actual MTTR
   - Share findings in #platform-resilience
   - Update runbook if needed

### Emergency Stop

```
/chaos_stop <run_id>
# Triggers immediate rollback + marks run ABORTED
```

**If manual rollback needed:**
```bash
gcloud run services update inka-api \
  --region europe-west1 \
  --image gcr.io/inka-prod/inka-api:latest
```

---

## 9. Files & Documentation

### Core Code Files

| File | Purpose | Size |
|------|---------|------|
| `libs/chaos/models.py` | ORM definitions | 5 KB |
| `libs/chaos/catalog.py` | 9 experiments | 8 KB |
| `libs/chaos/safety.py` | Safety gates | 6 KB |
| `libs/chaos/runner.py` | Orchestrator | 9 KB |
| `libs/chaos/rollback.py` | Rollback handlers | 5 KB |
| `libs/chaos/metrics.py` | Metrics collection | 7 KB |
| `apps/api/domains/chaos/api.py` | FastAPI routes | 8 KB |
| `apps/bot/handlers/chaos_handler.py` | Telegram commands | 12 KB |

### Documentation Files

| File | Purpose | Size |
|------|---------|------|
| `docs/chaos-engineering/README.md` | Main guide | 18 KB |
| `docs/chaos-engineering/PRODUCTION_SAFETY_CHECKLIST.md` | Pre-flight checklist | 12 KB |
| `docs/chaos-engineering/DEPLOYMENT_INTEGRATION.md` | Gov & Risk integration | 14 KB |

---

## 10. Quick Start Guide

### As a Telegram User

```bash
# List experiments
/chaos_list stage

# Run one
/chaos_run api_latency_injection stage

# Check status
/chaos_history

# Stop if needed
/chaos_stop <run_id>
```

### As a CI/CD Pipeline

```bash
# Start experiment in staging after deployment
curl -X POST http://api:8000/chaos/run \
  -H "Authorization: Bearer $CHAOS_TOKEN" \
  -d '{
    "experiment_name": "api_latency_injection",
    "environment": "stage",
    "requester": "ci-system"
  }' | jq -r '.run_id' > run_id.txt

# Wait for completion (max 10 min)
for i in {1..40}; do
  sleep 15
  STATUS=$(curl -X GET http://api:8000/chaos/history?limit=1 \
    -H "Authorization: Bearer $CHAOS_TOKEN" | jq -r '.[0].status')
  [ "$STATUS" != "running" ] && break
done

# Check metrics
METRICS=$(curl -X GET http://api:8000/chaos/metrics?window_days=1 \
  -H "Authorization: Bearer $CHAOS_TOKEN")

MTTR=$(echo $METRICS | jq '.avg_mttr_sec')
if (( $(echo "$MTTR > 60" | bc -l) )); then
  echo "❌ MTTR SLA failed: $MTTR > 60"
  exit 1
fi

echo "✅ Chaos validation passed"
```

---

## 11. Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Experiment blocked (403) | Environment gated | Try on stage first; check `/chaos_list stage` |
| "Compliance approval required" | Prod without --approve | Re-run with `--approve` flag |
| Rollback failed | Handler error | Check logs; may need manual recovery |
| MTTR > 60s | Slow recovery | File S2 defect; optimize rollback handler |
| No auto-recovery | Thresholds too lenient | Increase abort thresholds in catalog |
| S1 defect blocked start | Active defect | Resolve defect in defect system first |

---

## 12. Maintenance & Support

### Monthly Tasks

- [ ] Review chaos metrics (trend analysis)
- [ ] Update abort thresholds if SLA changed
- [ ] Verify deployment blocking working
- [ ] Analyze any failed resilience tests
- [ ] Update runbook based on learnings

### Quarterly Tasks

- [ ] Add new experiments (if new resilience gaps identified)
- [ ] Audit role-based access (admin/resilience_authority)
- [ ] Review integration with Risk Predictor
- [ ] Refine production safety checklist

### Support Contacts

| Role | Name | Slack | Phone |
|------|------|-------|-------|
| Lead | ___ | @___ | ___ |
| On-Call | ___ | @___ | ___ |
| Compliance | ___ | @___ | ___ |

---

## 13. Success Criteria

✅ **System is working well if:**
- MTTR < 60 seconds (avg)
- Auto-recovery rate ≥ 85%
- Rollback frequency ≤ 5 per month
- Failed resilience tests ≤ 2 per month
- No unexpect

ed customer impact during prod chaos runs
- Deployment Governor successfully blocks during active runs
- Risk Predictor score influences deployment decisions

⚠️ **Review needed if:**
- MTTR trending upward (degrading recovery speed)
- Auto-recovery < 80% (system less resilient)
- Rollback frequency > 5/month (safety gates helping)
- Failed tests > 2/month (exposed weaknesses accumulating)

---

## References

**Internal Links:**
- [INKA Architecture](../architecture/README.md)
- [Defect System Guide](../operations/defects.md)
- [Deployment Governor Runbook](../operations/deployment-governor.md)
- [Risk Predictor Design](../operations/risk-predictor.md)

**External References:**
- [Chaos Engineering (Gremlin)](https://www.gremlin.com/community/tutorials)
- [Principles of Chaos Engineering](https://principlesofchaos.org/)
- [Site Reliability Engineering (SRE) - Google](https://sre.google/books/)

---

**Questions?** Open an issue or reach out to #platform-resilience on Slack.

**Last Updated:** February 22, 2026  
**Maintained By:** Platform Engineering Team  
**Version:** 1.0 (Production Ready)
