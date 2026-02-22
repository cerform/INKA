# INKA Admin — KPI Definitions
**System:** INKA Admin Executive Reporting
**Version:** 1.0 | **Updated:** 2026-02-22

---

## Overview

All KPIs are collected automatically by the Executive Reporting Agent and published monthly. Each KPI has a defined data source, calculation method, target threshold, and traffic-light rule.

---

## KPI Registry

### 1. Uptime %

| Field | Value |
|-------|-------|
| **Definition** | Percentage of time each service was available and responding within its SLA latency threshold during the reporting period. |
| **Formula** | `(Total Minutes − Downtime Minutes) / Total Minutes × 100` |
| **Measured Per** | API Service, Telegram Bot, Admin Panel, Cloud SQL, Redis |
| **Aggregate** | Weighted average across all services |
| **Data Source** | Cloud Monitoring uptime checks + incident log |
| **Thresholds** | 🟢 GREEN ≥ 99.9% \| 🟡 YELLOW 99.5–99.9% \| 🔴 RED < 99.5% |
| **Target** | ≥ 99.9% per service |
| **Reporting Cadence** | Monthly (daily granularity available) |

---

### 2. Change Failure Rate (CFR)

| Field | Value |
|-------|-------|
| **Definition** | Percentage of deployments to production that caused a service degradation, incident, or required a rollback. |
| **Formula** | `Failed Deployments / Total Deployments × 100` |
| **DORA Classification** | Elite: < 5% \| High: 5–15% \| Medium: 15–30% \| Low: > 30% |
| **Data Source** | Deployment Governor event log + incident correlation |
| **Thresholds** | 🟢 GREEN < 10% \| 🟡 YELLOW 10–20% \| 🔴 RED > 20% |
| **Target** | < 10% |
| **Reporting Cadence** | Monthly |

---

### 3. Mean Time to Recovery (MTTR)

| Field | Value |
|-------|-------|
| **Definition** | Average time from incident detection to full service restoration across all P0/P1/P2 incidents in the period. |
| **Formula** | `Sum of (Resolution Time − Detection Time) / Total Incidents` |
| **Measured For** | P0, P1, P2 incidents only (P3 excluded from MTTR) |
| **Data Source** | Incident Management System + Self-Healing Agent event log |
| **Thresholds** | 🟢 GREEN < 30 min \| 🟡 YELLOW 30–60 min \| 🔴 RED > 60 min |
| **Target** | < 30 minutes |
| **Reporting Cadence** | Monthly |

---

### 4. Risk Score Trend

| Field | Value |
|-------|-------|
| **Definition** | Composite risk score (0–100) calculated by the AI Risk Predictor, reflecting deployment risk, security exposure, compliance gaps, and operational anomalies. Lower is better. |
| **Formula** | AI Risk Predictor weighted sum: Deployment History (25%) + Security Signals (25%) + Compliance Signal (20%) + Chaos Resilience (15%) + Operational Health (15%) |
| **Trend** | Tracked monthly; 3-month rolling trend plotted |
| **Data Source** | AI Risk Predictor model output |
| **Thresholds** | 🟢 GREEN < 40 \| 🟡 YELLOW 40–65 \| 🔴 RED > 65 |
| **Target** | < 40 |
| **Reporting Cadence** | Monthly (weekly updates available) |

---

### 5. Compliance Score

| Field | Value |
|-------|-------|
| **Definition** | Weighted compliance score (0–100) reflecting adherence to ISO 27001, SOC2, GDPR, and internal policies as assessed by the Compliance & Audit Framework. |
| **Formula** | `Weighted sum of framework coverage scores × policy weights` |
| **Weights** | ISO 27001: 30% \| SOC2: 30% \| GDPR: 25% \| Internal: 15% |
| **Data Source** | Compliance Audit Agent automated scans + manual review results |
| **Thresholds** | 🟢 GREEN ≥ 85 \| 🟡 YELLOW 70–84 \| 🔴 RED < 70 |
| **Target** | ≥ 85 |
| **Reporting Cadence** | Monthly |
| **Gate Rule** | Releases with compliance score < 80 are blocked from production |

---

### 6. Chaos Test Resilience %

| Field | Value |
|-------|-------|
| **Definition** | Percentage of planned chaos experiments where the system maintained its availability and recovery SLA targets (no SLA breach, self-healed or recovered within tolerance). |
| **Formula** | `Passed Experiments / Total Experiments Run × 100` |
| **Data Source** | Chaos Engineering Framework experiment log |
| **Experiment Types** | Service kill, network partition, database failover, Redis OOM, CPU spike, concurrency flood |
| **Thresholds** | 🟢 GREEN ≥ 85% \| 🟡 YELLOW 70–84% \| 🔴 RED < 70% |
| **Target** | ≥ 85% |
| **Reporting Cadence** | Monthly (minimum 4 experiments/month required for valid score) |

---

### 7. Self-Healing Success %

| Field | Value |
|-------|-------|
| **Definition** | Percentage of Self-Healing Agent activations that successfully resolved the anomaly without human escalation. |
| **Formula** | `Auto-Resolved Events / Total Agent Activations × 100` |
| **Data Source** | Self-Healing Agent audit log |
| **Thresholds** | 🟢 GREEN ≥ 80% \| 🟡 YELLOW 60–79% \| 🔴 RED < 60% |
| **Target** | ≥ 80% |
| **Reporting Cadence** | Monthly |
| **Note** | Only counts activations where root cause was within agent's defined mitigation scope |

---

### 8. Critical Defects Count

| Field | Value |
|-------|-------|
| **Definition** | Total number of open P0/P1 defects (critical bugs, security vulnerabilities rated Critical/High) at the end of the reporting period. |
| **Formula** | Count of open issues with severity = Critical or High at period end |
| **Data Source** | Issue tracker + Security scanner + Quality Score system |
| **Thresholds** | 🟢 GREEN = 0 \| 🟡 YELLOW 1–2 \| 🔴 RED ≥ 3 |
| **Target** | 0 critical defects |
| **Reporting Cadence** | Monthly (real-time dashboard available) |
| **Gate Rule** | Any Critical defect automatically blocks production deployment |

---

## KPI Summary Table

| # | KPI | Formula Summary | Target | GREEN | YELLOW | RED |
|---|-----|----------------|--------|-------|--------|-----|
| 1 | Uptime % | Available minutes / total | ≥ 99.9% | ≥ 99.9% | 99.5–99.9% | < 99.5% |
| 2 | Change Failure Rate | Failed deploys / total deploys | < 10% | < 10% | 10–20% | > 20% |
| 3 | MTTR | Avg incident resolution time | < 30 min | < 30 min | 30–60 min | > 60 min |
| 4 | Risk Score | AI composite score (0–100) | < 40 | < 40 | 40–65 | > 65 |
| 5 | Compliance Score | Weighted framework score (0–100) | ≥ 85 | ≥ 85 | 70–84 | < 70 |
| 6 | Chaos Resilience % | Passed chaos tests / total | ≥ 85% | ≥ 85% | 70–84% | < 70% |
| 7 | Self-Healing % | Auto-resolved / total activations | ≥ 80% | ≥ 80% | 60–79% | < 60% |
| 8 | Critical Defects | Count of open Critical/High issues | 0 | 0 | 1–2 | ≥ 3 |

---

## Data Collection & Automation

```
┌─────────────────────────────────────────────────┐
│            KPI Data Pipeline                    │
├─────────────────────────────────────────────────┤
│  Cloud Monitoring  ──► Uptime, Latency          │
│  Deployment Log    ──► CFR, Deployment Freq     │
│  Incident System   ──► MTTR, Incident Count     │
│  AI Risk Predictor ──► Risk Score               │
│  Compliance Agent  ──► Compliance Score         │
│  Chaos Framework   ──► Resilience %             │
│  Self-Healing Log  ──► Self-Healing %           │
│  Issue Tracker     ──► Critical Defects         │
└──────────┬──────────────────────────────────────┘
           │
           ▼
  Executive Reporting Agent
           │
           ├── Monthly Report (Markdown)
           ├── Telegram: /report monthly
           └── KPI Dashboard (Admin Panel)
```

---

*Maintained by: Platform Engineering | Review cycle: Quarterly*
