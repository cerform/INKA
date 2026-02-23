# INKA Chaos & Resilience Engineering Runbook

**Version**: 1.0 | **Owner**: Resilience Authority | **Last Updated**: 2026-02-22

> This runbook governs all chaos engineering activities for the INKA Admin system (Cloud Run + Postgres + Telegram Bot).

---

## 1. Chaos Experiment Catalog

All 9 experiments are defined in `libs/chaos/catalog.py`. They are immutable — changes require code review.

| # | Name | Type | Max Duration | Allowed Envs | Compliance Required |
|---|------|------|-------------|-------------|-------------------|
| 1 | `api_latency_injection` | API middleware | 5 min | dev, stage, prod | No |
| 2 | `db_connection_saturation` | DB pool | 3 min | dev, stage, prod | **Yes** |
| 3 | `telegram_webhook_failure` | Bot webhook | 2 min | dev, stage | No |
| 4 | `booking_conflict_surge` | Load | 3 min | dev, stage | No |
| 5 | `random_500_injection` | Middleware | 5 min | **dev, stage only** | No |
| 6 | `cloud_run_instance_kill` | Infra | 2 min | dev, stage, prod | **Yes** |
| 7 | `secret_rotation_simulation` | Secrets | 5 min | dev, stage, prod | **Yes** |
| 8 | `network_timeout_api_db` | Network | 3 min | dev, stage, prod | **Yes** |
| 9 | `high_concurrency_spike` | Load (k6) | 5 min | dev, stage, prod | **Yes** |

### Experiment Detail

#### 1. API Latency Injection
- **Hypothesis**: System handles +500 ms API latency; clients retry correctly; p95 < 2000 ms.
- **Blast Radius**: All inbound HTTP requests to inka-api.
- **Abort If**: p95 > 2000 ms OR error rate > 10%.
- **Rollback**: Remove latency middleware; delay resets to 0 ms.

#### 2. DB Connection Saturation
- **Hypothesis**: API returns 503 clearly when pool exhausted; auto-recovers after load subsides.
- **Blast Radius**: All DB-dependent API endpoints.
- **Abort If**: Error rate > 10% OR API errors > 50% for 30 s.
- **Rollback**: Dispose + recreate SQLAlchemy connection pool.

#### 3. Telegram Webhook Failure
- **Hypothesis**: Bot commands queue during webhook unavailability; drain without data loss on restore.
- **Blast Radius**: All Telegram bot webhook ingestion.
- **Abort If**: S1 defect triggered OR bot unavailable > 2 min.
- **Rollback**: Restore webhook URL to production endpoint via `setWebhook` API.

#### 4. Booking Conflict Surge
- **Hypothesis**: Conflict detection correct under concurrent surge; returns 409 without data corruption.
- **Blast Radius**: Booking API and `bookings` DB table.
- **Abort If**: Error rate > 20% OR data integrity check fails.
- **Rollback**: Stop load generator; run integrity check query.

#### 5. Random 500 Injection *(dev/stage only)*
- **Hypothesis**: Clients handle random 500s gracefully with retry; user-friendly error messages shown.
- **Blast Radius**: ≈5% of all HTTP responses.
- **Abort If**: Error rate > 15% sustained for 60 s.
- **Rollback**: Disable middleware flag; pass-through resumes.

#### 6. Cloud Run Instance Kill
- **Hypothesis**: Cloud Run auto-scales; replacement instance healthy within 30 s; < 5% error rate during recovery.
- **Blast Radius**: One running instance of `inka-api`.
- **Abort If**: Error rate > 5% for > 30 s OR no recovery after 90 s.
- **Rollback**: Cloud Run auto-scales — verify via `gcloud run services describe`.

#### 7. Secret Rotation Simulation
- **Hypothesis**: Services reload new secrets within rotation window without auth failures > 2%.
- **Blast Radius**: Secret Manager secret versions; config reload path.
- **Abort If**: Auth failure rate > 2% OR secret unavailable > 60 s.
- **Rollback**: Disable new secret version; force Cloud Run restart.

#### 8. Network Timeout (API ↔ DB)
- **Hypothesis**: API returns 503 with timeout context; no requests hang indefinitely.
- **Blast Radius**: DB connection layer — all API requests that query DB.
- **Abort If**: Error rate > 15% OR any request hangs > 30 s.
- **Rollback**: Restore default DB connection timeout.

#### 9. High Concurrency Spike
- **Hypothesis**: System sustains 500 RPS for 5 min with p95 < 3000 ms, error rate < 5%.
- **Blast Radius**: All three services (inka-api, inka-bot, inka-admin).
- **Abort If**: p95 > 3000 ms OR error rate > 5% OR S1 defect.
- **Rollback**: Stop k6 process; verify services cooling down.

---

## 2. Execution Safety Model

```
[Telegram Command / GitHub Actions Trigger]
        │
        ▼
┌─────────────────────────────────────────┐
│         SafetyController                │
│  ① Env gate (allowlist check)           │
│  ② Max duration ≤ 300 s enforcement     │
│  ③ Compliance approval (prod)           │
│  ④ Active S1/S2 defect check            │
└─────────────────────────────────────────┘
        │ Pass
        ▼
┌─────────────────────────────────────────┐
│         ChaosRunner                     │
│  • Creates ChaosRun record (audit trail)│
│  • starts experiment adapter            │
│  • polls metrics every 15 s             │
│  • evaluates abort conditions           │
└─────────────────────────────────────────┘
        │ Abort triggered
        ▼
┌─────────────────────────────────────────┐
│         RollbackManager                 │
│  • idempotent per-experiment handler    │
│  • marks run as ROLLED_BACK             │
│  • logs rollback result                 │
└─────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│         ChaosMetricsCollector           │
│  • stores snapshots → chaos_metrics     │
│  • computes MTTR, auto-recovery rate    │
└─────────────────────────────────────────┘
```

### Environment Rules

| Rule | Dev | Stage | Prod |
|------|-----|-------|------|
| Auto-run from CI | ✅ | ✅ | ❌ Manual only |
| Compliance required | ❌ | ❌ | ✅ |
| Manual GH approval gate | ❌ | ❌ | ✅ |
| `random_500_injection` allowed | ✅ | ✅ | ❌ Blocked |
| Max traffic impact | 100% | 100% | **5% canary** |

---

## 3. Rollback Triggers Reference

| Condition | Action | Urgency |
|-----------|--------|---------|
| Error rate > threshold | Auto-abort + rollback | Immediate |
| p95 latency > threshold | Auto-abort + rollback | Immediate |
| S1 defect triggered | Hard stop, no retry | Immediate |
| Max duration elapsed | Graceful stop | Scheduled |
| `chaos_stop` API call | Manual abort + rollback | Immediate |
| GitHub Actions timeout | Forced stop via API | Scheduled |

---

## 4. Integration Map

### Defect System
`SafetyController._check_no_active_defects()` — calls internal defect API before any prod experiment.
- Integration endpoint: `GET /internal/defects/active?severity=S1,S2`
- Blocks experiment if `count > 0`.

### Risk Predictor (from previous agent)
- Chaos experiments with `requires_compliance=True` should integrate with the Risk Predictor score gate.
- Block if Risk Predictor score < 60 for the target environment.

### Deployment Governor
- Post-deploy `api_latency_injection` smoke run (60 s in dev) is a deploy gate in `deploy.yml`.
- Deploy fails if smoke run aborts.

---

## 5. Metrics & Dashboards

### Key Metrics (tracked in `chaos_metrics` + Cloud Monitoring)

| Metric | Target | Alert At |
|--------|--------|----------|
| MTTR (mean) | < 120 s | > 300 s |
| Auto-recovery rate | > 80% | < 60% |
| Rollback frequency | < 5/month | > 10/month |
| Failed resilience tests | < 20% | > 40% |
| Prod experiments/month | ≥ 2 | 0 (stale) |

### Dashboard Panels (Grafana / Cloud Monitoring)

1. **Chaos Experiment Timeline** — Gantt of runs by env with status color coding
2. **MTTR Trend** — 90-day rolling average
3. **Auto-Recovery Rate** — % by experiment type
4. **Error Rate During Chaos** — overlaid with experiment windows
5. **Rollback Frequency** — per week, by experiment type

### Prometheus-style Metrics (future)
```
chaos_runs_total{experiment, env, status}
chaos_run_duration_seconds{experiment, env}
chaos_error_rate_pct{experiment, env}
chaos_mttr_seconds{experiment}
```

---

## 6. Production Safety Checklist

Before every production chaos experiment:

- [ ] Active S1/S2 defects = 0 (check defect system)
- [ ] Compliance team sign-off obtained (email/Jira ticket)
- [ ] Risk Predictor score ≥ 60 for prod
- [ ] Deployment Governor: no deploy in progress
- [ ] On-call engineer is online and monitoring
- [ ] Runbook URL shared in incident Slack channel
- [ ] Rollback procedure verified (dry-run in stage)
- [ ] Monitoring dashboards open (Cloud Monitoring + Grafana)
- [ ] Maximum blast radius confirmed (canary ≤ 5% traffic)
- [ ] Post-experiment review scheduled (within 48 h)

---

## 7. Telegram Commands Reference

| Command | Description | Required Role |
|---------|-------------|---------------|
| `/chaos_list [env]` | List all experiments | admin, resilience_authority |
| `/chaos_run <name> [env] [--approve]` | Start experiment | admin, resilience_authority |
| `/chaos_stop <run_id>` | Abort + rollback | admin, resilience_authority |
| `/chaos_history [env]` | Last 10 runs + metrics | admin, resilience_authority |

> [!IMPORTANT]
> For production runs: always include `--approve` flag. This confirms compliance sign-off. Without it, the bot returns a confirmation prompt.

---

## 8. File Structure

```
libs/
  chaos/
    __init__.py          # Package exports
    models.py            # SQLAlchemy ORM (ChaosExperiment, ChaosRun, ChaosMetric)
    catalog.py           # Immutable experiment definitions (9 experiments)
    runner.py            # ChaosRunner — lifecycle orchestrator
    safety.py            # SafetyController — all guard logic
    rollback.py          # RollbackManager — per-experiment rollback handlers
    metrics.py           # ChaosMetricsCollector — MTTR, recovery rate, etc.

apps/
  api/src/app/domains/chaos/
    models.py            # Pydantic request/response schemas
    api.py               # FastAPI router (5 endpoints)
  bot/src/handlers/
    chaos_handler.py     # Telegram commands (aiogram Router)

alembic/versions/
  add_chaos_tables.py    # DB migration: 3 tables + enums

.github/workflows/
  chaos.yml              # GitHub Actions chaos workflow
```
