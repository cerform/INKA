# INKA Admin — DORA Metrics Authority

> **System:** INKA Admin DevOps | **Role:** Engineering Performance Dashboard Authority
> **Updated:** 2026-02-22 | **Owner:** Platform Engineering

---

## SECTION 1 — DORA METRIC DEFINITIONS & FORMULAS

### 1.1 Deployment Frequency (DF)

**Definition:** How often code is deployed to production.

| Tier | Threshold | Classification |
|------|-----------|----------------|
| Elite | Multiple times/day | 🟢 Elite |
| High | Once/day – once/week | 🔵 High |
| Medium | Once/week – once/month | 🟡 Medium |
| Low | Fewer than once/month | 🔴 Low |

**Formula:**
```
DF = (Total successful prod deployments) / (Measurement period in days)

DF_weekly  = deploys in last 7 days
DF_monthly = deploys in last 30 days
DF_trend   = (DF_current_period - DF_prev_period) / DF_prev_period × 100
```

**Data Source:** `release_registry`, `ci_cd_pipeline_logs (status=SUCCESS, env=production)`

---

### 1.2 Lead Time for Changes (LTC)

**Definition:** Time from code committed to running in production.

| Tier | Threshold |
|------|-----------|
| Elite | < 1 hour |
| High | 1 day – 1 week |
| Medium | 1 week – 1 month |
| Low | > 1 month |

**Formula:**
```
LTC_per_commit = T_deployed_at - T_committed_at
LTC_avg        = Σ(LTC_per_commit) / N_commits  (rolling 30 days)
LTC_p95        = 95th percentile of LTC_per_commit
LTC_p50        = Median LTC_per_commit
```

**Sub-components:**
```
LTC = T_code_review + T_ci_pipeline + T_staging_validation + T_prod_gate
```

**Data Source:** `github_commits.committed_at` → `release_registry.deployed_at`

---

### 1.3 Change Failure Rate (CFR)

**Definition:** Percentage of deployments causing a degradation requiring hotfix or rollback.

| Tier | Threshold |
|------|-----------|
| Elite | 0–5% |
| High | 5–10% |
| Medium | 10–15% |
| Low | > 15% |

**Formula:**
```
CFR = (Failed deployments + Rollback events + P1 incidents within 1h of deploy)
      ─────────────────────────────────────────────────────────────────────────
                      Total deployments in period
      × 100
```

**INKA-specific failure signals:**
- Rollback event logged in `rollback_events`
- P0/P1 incident opened within 60 min of deployment
- Health check failure post-deployment (Cloud Run startup failures)

**Data Source:** `rollback_events`, `incident_logs`, `ci_cd_pipeline_logs`

---

### 1.4 Mean Time To Recovery (MTTR)

**Definition:** Average time to restore service after an incident.

| Tier | Threshold |
|------|-----------|
| Elite | < 1 hour |
| High | < 1 day |
| Medium | 1 day – 1 week |
| Low | > 1 week |

**Formula:**
```
MTTR_per_incident = T_resolved_at - T_detected_at
MTTR_avg          = Σ(MTTR_per_incident) / N_incidents  (rolling 30 days)
```

**Detection sources:**
- Telegram alert fired
- Cloud Monitoring alert triggered
- Manual incident creation

**Data Source:** `incident_logs (detected_at, resolved_at, severity IN ['P0','P1','P2'])`

---

## SECTION 2 — DATA SOURCES & EXTRACTION LOGIC

### 2.1 Schema Map

| Source | Key Fields | Used For |
|--------|-----------|----------|
| `github_commits` | `sha`, `committed_at`, `author`, `branch`, `pr_merged_at` | LTC start, regression tracking |
| `ci_cd_pipeline_logs` | `run_id`, `start_time`, `end_time`, `status`, `env`, `service`, `triggered_by` | DF, build health, CFR signals |
| `release_registry` | `version`, `env`, `deployed_at`, `deployed_by`, `quality_score`, `risk_score` | DF, LTC end, version governance |
| `rollback_events` | `version`, `rolled_back_at`, `reason`, `triggered_by`, `environment` | CFR, rollback frequency |
| `incident_logs` | `id`, `severity`, `detected_at`, `resolved_at`, `linked_deployment`, `root_cause` | MTTR, CFR correlation |
| `defect_registry` | `id`, `severity`, `module`, `introduced_in`, `found_in_env`, `resolved_at` | Defect density, regression rate |
| `chaos_experiments` | `experiment_id`, `started_at`, `outcome`, `module`, `hypothesis_met` | Chaos success rate |
| `audit_log` | `actor`, `action`, `resource`, `env`, `timestamp`, `break_glass` | Break-glass freq, compliance |

### 2.2 Extraction Queries (Pseudo-SQL)

```sql
-- Deployment Frequency (last 30 days)
SELECT
  DATE_TRUNC('day', deployed_at) AS day,
  COUNT(*) AS deployments,
  COUNT(*) / 30.0 AS daily_avg
FROM release_registry
WHERE env = 'production'
  AND deployed_at >= NOW() - INTERVAL '30 days'
GROUP BY 1
ORDER BY 1;

-- Lead Time for Changes
SELECT
  r.version,
  c.committed_at,
  r.deployed_at,
  EXTRACT(EPOCH FROM (r.deployed_at - c.committed_at))/3600 AS ltc_hours
FROM release_registry r
JOIN github_commits c ON c.sha = r.git_sha
WHERE r.env = 'production'
  AND r.deployed_at >= NOW() - INTERVAL '30 days';

-- Change Failure Rate
WITH total AS (
  SELECT COUNT(*) AS cnt FROM release_registry
  WHERE env = 'production' AND deployed_at >= NOW() - INTERVAL '30 days'
),
failures AS (
  SELECT COUNT(*) AS cnt FROM (
    SELECT version FROM rollback_events
    WHERE environment = 'production'
      AND rolled_back_at >= NOW() - INTERVAL '30 days'
    UNION
    SELECT linked_deployment FROM incident_logs
    WHERE severity IN ('P0','P1')
      AND detected_at >= NOW() - INTERVAL '30 days'
      AND detected_at - (SELECT deployed_at FROM release_registry
                          WHERE version = linked_deployment LIMIT 1) < INTERVAL '1 hour'
  ) f
)
SELECT ROUND(failures.cnt::numeric / NULLIF(total.cnt,0) * 100, 2) AS cfr_pct
FROM total, failures;

-- MTTR
SELECT
  AVG(EXTRACT(EPOCH FROM (resolved_at - detected_at))/3600) AS mttr_hours,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY
    EXTRACT(EPOCH FROM (resolved_at - detected_at))/3600) AS mttr_median,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY
    EXTRACT(EPOCH FROM (resolved_at - detected_at))/3600) AS mttr_p95
FROM incident_logs
WHERE severity IN ('P0','P1','P2')
  AND resolved_at IS NOT NULL
  AND detected_at >= NOW() - INTERVAL '30 days';
```

---

## SECTION 3 — ADDITIONAL METRICS

### 3.1 Quality Score Trend
```
QS_t = weighted_avg(test_coverage, defect_rate, security, migration_risk, performance, compliance)
QS_trend_30d = LR_slope(QS_t, t=last30days)   // positive = improving
```

### 3.2 Risk Score Trend
```
RS_t = AI_Risk_Predictor output [0..100] per deploy
RS_trend = Δ(RS_avg_last14d - RS_avg_prev14d)
```

### 3.3 Compliance Score Trend
```
CS_t = Σ(passed_controls) / Σ(total_controls) × 100
      per ISO-27001 / SOC2 / GDPR control domains
```

### 3.4 Chaos Experiment Success Rate
```
CESR = (Experiments where hypothesis_met=TRUE) / Total experiments × 100
```

### 3.5 Break-Glass Frequency
```
BGF = COUNT(audit_log WHERE break_glass=TRUE AND timestamp >= period) / period_days
Alert if BGF > 2/week
```

### 3.6 Regression Rate
```
RR = (Defects with root_cause='regression') / (Total defects in period) × 100
```

---

## SECTION 4 — DASHBOARD LAYOUT PLAN

### Executive View

| Widget | Content | Window |
|--------|---------|--------|
| Deployment Velocity | DF trend sparkline + current tier badge | 30/90d |
| Stability Index | Composite: (1-CFR) × MTTR_score × 100 | 30d |
| Incident Heatmap | Calendar heatmap of P0-P2 incidents by day | 90d |
| DORA Tier Summary | 4-quadrant scorecard with tier badges | Current |
| Quality Score Trend | Line chart QS over 90 days | 90d |
| Risk Score Trend | Line chart RS per deployment | 30/90d |
| Compliance Score | Gauge (0-100) with domain breakdown | Current |

### Engineering View

| Widget | Content |
|--------|---------|
| Module Defect Density | Bar chart: defects per KLOC by module (api/bot/admin) |
| High-Risk Areas | Ranked table: module × risk score × change frequency |
| Migration Risk Frequency | Timeline of migration events + rollback risk score |
| Lead Time Breakdown | Stacked bar: review + CI + staging + prod gate |
| Regression Rate Trend | Line chart over 90 days |
| Chaos Success Rate | Donut chart per experiment type |
| Break-Glass Log | Table: actor, timestamp, reason, duration |

---

## SECTION 5 — ALERT THRESHOLDS & DEFINITIONS

### 5.1 Core DORA Alerts

| Alert | Condition | Severity | Channel |
|-------|-----------|----------|---------|
| CFR_HIGH | CFR > 10% (7-day rolling) | P1 | Telegram + PagerDuty |
| CFR_CRITICAL | CFR > 20% (7-day rolling) | P0 | Telegram + PagerDuty + Email |
| MTTR_BREACH | MTTR_avg > 4h (30-day) | P1 | Telegram |
| MTTR_CRITICAL | MTTR_avg > 8h (30-day) | P0 | Telegram + PagerDuty |
| DF_DROP | DF drops >50% vs prev 7d | P2 | Telegram |
| LTC_DEGRADED | LTC_p95 > 24h (7-day) | P2 | Telegram |

### 5.2 Quality & Risk Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| QS_BLOCK | Quality Score < 80 for stage / < 90 for prod | P0 (block) |
| RS_HIGH | Risk Score > 80 | P1 |
| COMPLIANCE_BREACH | Compliance Score < 85 | P1 |
| CHAOS_FAIL_STREAK | 3 consecutive chaos failures | P2 |
| BREAKGLASS_SPIKE | BGF > 2/week | P1 |
| REGRESSION_SPIKE | Regression rate > 20% | P1 |

### 5.3 Alert Message Template (Telegram)
```
🚨 [SEVERITY] DORA ALERT — {alert_name}

Metric:  {metric_name}
Current: {current_value}
Threshold: {threshold_value}
Period:  {measurement_period}
Trend:   {trend_direction} {trend_delta}

Affected: {service_or_module}
Last Deploy: {last_deploy_version} @ {last_deploy_time}
Run: /dora status to investigate
```

---

## Executive Summary Template

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INKA ADMIN — ENGINEERING PERFORMANCE REPORT
Period: {start_date} → {end_date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DORA SCORECARD
──────────────
Deployment Frequency    {df_value}/day     [{df_tier}]
Lead Time for Changes   {ltc_p50}h median  [{ltc_tier}]
Change Failure Rate     {cfr_pct}%         [{cfr_tier}]
Mean Time To Recovery   {mttr_avg}h        [{mttr_tier}]

OVERALL DORA BAND:      [{overall_tier}]

KEY SIGNALS
───────────
Stability Index:        {stability_index}/100
Quality Score (avg):    {qs_avg}/100
Risk Score (avg):       {rs_avg}/100
Compliance Score:       {cs}/100
Chaos Success:          {cesr}%
Regressions:            {rr}%
Break-glass events:     {bgf_count}

INCIDENTS
─────────
P0: {p0_count}  P1: {p1_count}  P2: {p2_count}
Avg MTTR P0: {mttr_p0}h
Avg MTTR P1: {mttr_p1}h

TOP RISK MODULES
────────────────
{module_1}: Risk={r1}, Defect Density={dd1}/KLOC
{module_2}: Risk={r2}, Defect Density={dd2}/KLOC

RECOMMENDATIONS
───────────────
{auto-generated based on tier breaches and trend signals}

Generated by INKA DORA Engine @ {timestamp}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
