# Chaos Engineering Documentation Index

**INKA Chaos & Resilience Testing System v1.0**  
**Complete | Production-Ready | February 2026**

---

## 📚 Documentation Structure

All chaos engineering documentation is organized in `/docs/chaos-engineering/`:

### 1. **[README.md](./README.md)** — Main Guide (18 KB)
   **Audience:** Everyone  
   **Time to Read:** 30 minutes
   
   Complete reference for:
   - Quick start (Telegram & API examples)
   - System architecture overview
   - 9 experiment catalog (hypotheses, blast radius, thresholds)
   - Safety controls (gates, compliance, abort conditions)
   - Telegram commands reference
   - REST API endpoints (with examples)
   - Metrics & dashboards
   - Defect integration
   - Production runbook basics
   - FAQ & troubleshooting

   **Start here if:** You're new to the chaos system

---

### 2. **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** — Executive Overview (20 KB)
   **Audience:** Engineering Leads, Managers  
   **Time to Read:** 15 minutes
   
   High-level summary:
   - Executive summary with key capabilities
   - System architecture diagram
   - Component overview with file sizes
   - 9 experiments quick table
   - Safety controls summary
   - Execution model lifecycle
   - Metrics overview (MTTR, auto-recovery, etc.)
   - Telegram commands quick reference
   - API quick reference
   - Integration points (Deployment Governor, Risk Predictor)
   - Production runbook highlights
   - Files & documentation index
   - Quick start guide (Telegram & CI/CD)
   - Common issues & solutions
   - Maintenance tasks
   - Success criteria

   **Start here if:** You need the big picture

---

### 3. **[PRODUCTION_SAFETY_CHECKLIST.md](./PRODUCTION_SAFETY_CHECKLIST.md)** — Pre-Flight Checklist (12 KB)
   **Audience:** Incident Commanders, On-Call SRE  
   **Time to Read:** 10 minutes (review) / 20 minutes (full execution)
   
   Structured checklist for production experiments:
   - **Phase 1: Compliance & Planning** (16 items)
     - Experiment approved
     - Defects checked
     - Timeline verified
     - Blast radius analyzed
     - Rollback verified
   
   - **Phase 2: Monitoring Setup** (8 items)
     - Dashboards open
     - Alerting rules created
     - Communication ready
   
   - **Phase 3: Execution** (7 items)
     - Pre-launch validation
     - Experiment launch
     - Real-time monitoring loop
     - Abort conditions
   
   - **Phase 4: Recovery** (6 items)
     - Recovery verification
     - Data integrity check
     - Metrics collection
     - Post-mortem communication
   
   - **Phase 5: Sign-Off** (3 items)
     - Incident Commander approval
     - Platform Lead approval
     - Compliance Officer notification
   
   - **Appendix:** Quick reference tables (abort thresholds, emergency contacts, dashboards)

   **Use this:** Before every production experiment

---

### 4. **[DEPLOYMENT_INTEGRATION.md](./DEPLOYMENT_INTEGRATION.md)** — Governor & Risk Integration (14 KB)
   **Audience:** Platform Architects, DevOps Engineers  
   **Time to Read:** 20 minutes
   
   Deep integration with related systems:
   - **Deployment Governor Integration**
     - Block deployments during active chaos
     - Link deployment to test results
     - Database schema for deployment-chaos linkage
     - CI/CD pipeline integration example
   
   - **Risk Predictor Integration**
     - Chaos resilience score formula (0-100)
     - Components (auto-recovery, MTTR, test success)
     - Risk adjustment calculation
     - Deployment decision flow diagram
     - Dashboard widgets
   
   - **Integration Workflow**
     - Pre-deployment checklist integration
     - Monitoring & alerting
     - Example scenario (deploy v2.3.4)
   
   - **Maintenance & Tuning**
     - Monthly reviews
     - Threshold adjustment guidance

   **Use this:** If implementing deployment gating or risk scoring

---

### 5. **[OPERATIONAL_RUNBOOK.md](./OPERATIONAL_RUNBOOK.md)** — Step-by-Step Procedures (16 KB)
   **Audience:** DevOps, SRE, On-Call Teams  
   **Time to Read:** 15 minutes (scanning) / 45 minutes (full)
   
   7 real-world scenarios with exact steps:
   
   1. **Scenario 1: Run Your First Test (Dev)**
      - 20 min procedure
      - Perfect for learning
   
   2. **Scenario 2: Manual Abort**
      - < 1 min procedure
      - When something goes wrong
   
   3. **Scenario 3: Production Chaos (High Stakes)**
      - 45 min procedure
      - Full pre-flight, execution, debrief
   
   4. **Scenario 4: Respond to Failure**
      - 30 min procedure
      - Root cause analysis & remediation
   
   5. **Scenario 5: Integrate into CI/CD**
      - 1 hour setup
      - Complete GitHub Actions workflow
   
   6. **Scenario 6: Troubleshoot Not Starting**
      - 10 min procedure
      - Diagnosis of safety gate blocks
   
   7. **Scenario 7: Schedule Regular Tests**
      - 15 min setup
      - Weekly chaos testing program
   
   - **Appendix:** Quick command reference (Telegram, API, gcloud)

   **Use this:** When you need step-by-step instructions

---

## 🎯 Navigation by Role

### I'm a **Product Engineer**

1. Read: [README.md - Quick Start](./README.md#quick-start)
2. Try: Scenario 1 in [OPERATIONAL_RUNBOOK.md](./OPERATIONAL_RUNBOOK.md)
3. Run: `/chaos_run api_latency_injection dev`
4. Reference: [README.md - Telegram Commands](./README.md#telegram-bot-commands)

---

### I'm an **SRE / On-Call**

1. Review: [PRODUCTION_SAFETY_CHECKLIST.md](./PRODUCTION_SAFETY_CHECKLIST.md)
2. Bookmark: [OPERATIONAL_RUNBOOK.md - Scenario 2 (Abort)](./OPERATIONAL_RUNBOOK.md#scenario-2-manual-abort-of-running-experiment)
3. Understand: [README.md - Safety Controls](./README.md#safety-controls)
4. Know by heart: Emergency contacts in Safety Checklist appendix

---

### I'm a **Platform/DevOps Engineer**

1. Understand: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)
2. Integrate: [DEPLOYMENT_INTEGRATION.md](./DEPLOYMENT_INTEGRATION.md)
3. Deploy: Follow [OPERATIONAL_RUNBOOK.md - Scenario 5 (CI/CD)](./OPERATIONAL_RUNBOOK.md#scenario-5-integrate-chaos-into-cicd-pipeline)
4. Maintain: Monthly tasks in [IMPLEMENTATION_SUMMARY.md § 12](./IMPLEMENTATION_SUMMARY.md#12-maintenance--support)

---

### I'm an **Engineering Lead**

1. Review: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) (15 min)
2. Skim: [DEPLOYMENT_INTEGRATION.md](./DEPLOYMENT_INTEGRATION.md) (10 min)
3. Set: Success criteria from [IMPLEMENTATION_SUMMARY.md § 13](./IMPLEMENTATION_SUMMARY.md#13-success-criteria)
4. Plan: Monthly reviews from [IMPLEMENTATION_SUMMARY.md § 12](./IMPLEMENTATION_SUMMARY.md#12-maintenance--support)

---

### I'm the **Incident Commander**

1. Know: [PRODUCTION_SAFETY_CHECKLIST.md](./PRODUCTION_SAFETY_CHECKLIST.md) completely
2. Understand: [README.md - Abort Conditions](./README.md#31-runtime-abort-conditions)
3. Emergency procedure: [OPERATIONAL_RUNBOOK.md - Scenario 2](./OPERATIONAL_RUNBOOK.md#scenario-2-manual-abort-of-running-experiment)
4. Recovery: Manual restart steps in Scenario 2

---

### I'm **Compliance/Risk**

1. Review: [IMPLEMENTATION_SUMMARY.md § 7](./IMPLEMENTATION_SUMMARY.md#7-integration-points)
2. Understand: Compliance gates in [README.md § 2.2](./README.md#22-compliance-approval)
3. Checklist: [PRODUCTION_SAFETY_CHECKLIST.md](./PRODUCTION_SAFETY_CHECKLIST.md) - specifically approval sections
4. Integration: [DEPLOYMENT_INTEGRATION.md - Risk Predictor](./DEPLOYMENT_INTEGRATION.md#2-risk-predictor-integration)

---

## 📊 Quick Reference Tables

### Experiment Overview

| Exp | Duration | Envs | Approval | MTTR Target |
|-----|----------|------|----------|-------------|
| API Latency | 5m | dev, stage, prod | ❌ | < 60s |
| DB Saturation | 3m | dev, stage, prod | ✅ | < 60s |
| Webhook Failure | 2m | dev, stage | ❌ | < 60s |
| Booking Surge | 3m | dev, stage | ❌ | < 60s |
| Random 500 | 5m | dev, stage | ❌ | < 60s |
| Instance Kill | 2m | dev, stage, prod | ✅ | < 60s |
| Secret Rotation | 5m | dev, stage, prod | ✅ | < 60s |
| Network Timeout | 3m | dev, stage, prod | ✅ | < 60s |
| Concurrency Spike | 5m | dev, stage, prod | ✅ | < 60s |

*Full details: [README.md § 3](./README.md#3-chaos-experiment-catalog)*

---

### Key Metrics (30-Day Window)

| Metric | Target | Status | Action if Below |
|--------|--------|--------|-----------------|
| MTTR | < 60s | ✅ | Optimize recovery automation |
| Auto-Recovery | ≥ 85% | ✅ | Review fault detection |
| Rollback Frequency | ≤ 5/month | ✅ | Normal operation |
| Failed Tests | ≤ 2/month | ⚠️ | File defects |

*Full details: [README.md § 4.1](./README.md#41-key-metrics)*

---

### Telegram Commands

```
/chaos_list [env]              List experiments
/chaos_run <exp> [env] [--app] Start experiment
/chaos_stop <run_id>           Abort experiment
/chaos_history [env]           View history & metrics
```

*Full details: [README.md § 5](./README.md#5-telegram-bot-commands)*

---

### REST API Endpoints

```
GET  /chaos/experiments         List catalog
POST /chaos/run                 Start experiment
POST /chaos/stop/{run_id}       Stop experiment
GET  /chaos/history             View history
GET  /chaos/metrics             Get metrics
```

*Full details: [README.md § 6](./README.md#6-rest-api)*

---

## 🚀 Getting Started (3 Phases)

### Phase 1: Understand (Day 1)
- [ ] Read [README.md § 1-2](./README.md#quick-start) (Quick Start)
- [ ] Review [IMPLEMENTATION_SUMMARY.md § 2](./IMPLEMENTATION_SUMMARY.md#system-architecture) (Architecture)
- [ ] Understand your role above

### Phase 2: Try (Day 2-3)
- [ ] Follow [OPERATIONAL_RUNBOOK.md - Scenario 1](./OPERATIONAL_RUNBOOK.md#scenario-1-run-your-first-chaos-test-dev-environment)
- [ ] Run: `/chaos_run api_latency_injection dev`
- [ ] Monitor and document results

### Phase 3: Prepare (Day 4-7)
- [ ] If on-call: Review [PRODUCTION_SAFETY_CHECKLIST.md](./PRODUCTION_SAFETY_CHECKLIST.md) completely
- [ ] If DevOps: Plan [DEPLOYMENT_INTEGRATION.md](./DEPLOYMENT_INTEGRATION.md) integration
- [ ] Bookmark [OPERATIONAL_RUNBOOK.md](./OPERATIONAL_RUNBOOK.md) for reference
- [ ] Bookmark emergency contact list

---

## 🆘 Troubleshooting Guide

**"Experiment blocked (403)"**  
→ [README.md § 10](./README.md#faq--troubleshooting)

**"Need to stop running experiment"**  
→ [OPERATIONAL_RUNBOOK.md - Scenario 2](./OPERATIONAL_RUNBOOK.md#scenario-2-manual-abort-of-running-experiment)

**"Experiment failed, how to respond?"**  
→ [OPERATIONAL_RUNBOOK.md - Scenario 4](./OPERATIONAL_RUNBOOK.md#scenario-4-respond-to-chaos-experiment-failure)

**"Rolling out to production, what to check?"**  
→ [PRODUCTION_SAFETY_CHECKLIST.md](./PRODUCTION_SAFETY_CHECKLIST.md)

**"Need to integrate with CI/CD"**  
→ [OPERATIONAL_RUNBOOK.md - Scenario 5](./OPERATIONAL_RUNBOOK.md#scenario-5-integrate-chaos-into-cicd-pipeline)

**"Chaos not affecting anything, are thresholds wrong?"**  
→ [DEPLOYMENT_INTEGRATION.md § 5.2](./DEPLOYMENT_INTEGRATION.md#52-threshold-tuning)

---

## 📈 Metrics Dashboards

**Grafana:** https://grafana.inka.internal/d/chaos-engineering  
**CloudMonitoring:** https://console.cloud.google.com/monitoring/dashboards/custom/inka-chaos  
**CloudLogging:** https://console.cloud.google.com/logs/query  
**BigQuery:** `inka_prod.chaos_runs` table

*Setup guides: [README.md § 4.3](./README.md#dashboard-tools)*

---

## 🔗 Related Systems

- **[Defect System](../operations/defects.md)** — S1/S2 defect blocking
- **[Deployment Governor](../operations/deployment-governor.md)** — Deployment gating
- **[Risk Predictor](../operations/risk-predictor.md)** — Risk scoring
- **[Cloud Run Runbook](../operations/cloud-run.md)** — Container management
- **[INKA Architecture](../architecture/README.md)** — System design

---

## 📞 Support & Questions

**Slack:** #platform-resilience  
**On-Call:** @incident_commander  
**Escalation:** Platform Lead / VP Engineering

---

## 📝 Document Versions

| File | Version | Size | Last Updated |
|------|---------|------|--------------|
| README.md | 1.0 | 18 KB | Feb 22, 2026 |
| IMPLEMENTATION_SUMMARY.md | 1.0 | 20 KB | Feb 22, 2026 |
| PRODUCTION_SAFETY_CHECKLIST.md | 1.0 | 12 KB | Feb 22, 2026 |
| DEPLOYMENT_INTEGRATION.md | 1.0 | 14 KB | Feb 22, 2026 |
| OPERATIONAL_RUNBOOK.md | 1.0 | 16 KB | Feb 22, 2026 |

**Total Documentation:** 80 KB  
**Maintenance Review Date:** May 2026  
**Maintained By:** Platform Engineering Team

---

**Ready to get started?** Pick your role above and follow the links!
