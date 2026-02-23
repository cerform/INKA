# Chaos Engineering: Production Safety Checklist

**Purpose:** Ensure every production chaos experiment is executed safely with minimal risk of uncontrolled impact.

---

## Pre-Experiment Phase (Compliance & Planning)

### 1. Experiment Selection & Approval

- [ ] **Experiment approved by:**
  - [ ] Platform Lead
  - [ ] Compliance Officer
  - [ ] Incident Commander
- [ ] **Experiment type is production-allowed:**
  - ✅ api_latency_injection
  - ✅ db_connection_saturation
  - ✅ cloud_run_instance_kill
  - ✅ secret_rotation_simulation
  - ✅ network_timeout_api_db
  - ✅ high_concurrency_spike
  - ❌ random_500_injection
  - ❌ booking_conflict_surge
  - ❌ telegram_webhook_failure
- [ ] **Compliance token obtained** (for `--approve` flag)
- [ ] **Business case documented:**
  - Why run this experiment now?
  - Expected learnings
  - Acceptable impact window

### 2. Defect & Incident Status

- [ ] **No active S1 defects** blocking production
  ```bash
  curl -X GET http://api:8000/internal/defects?severity=S1&status=open
  # Result: count should be 0
  ```
- [ ] **No active major incidents** (P1/P2) in incident management system
- [ ] **Incident Commander assigned & on-call**
  - Slack: @incident_commander
  - Phone: (backup contact)

### 3. Timeline & Scheduling

- [ ] **Scheduled during low-traffic window**
  - Not during peak hours (typically 9–17 UTC)
  - Not during known partner integrations
  - Avoid: End of quarter, major releases
- [ ] **Scheduled OUTSIDE change freeze periods**
  - Check release calendar
  - Confirm no production deployments planned ±30 min
- [ ] **Scheduled in advance (≥7 days)**
  - Communicated to: #platform-resilience, #incident-management
  - Cross-team review period open
- [ ] **On-call team notified**
  - Slack message 48h before
  - Slack message 30m before
  - Status updates every 5 min during run

### 4. Blast Radius Analysis

- [ ] **Maximum affected resources documented:**
  - [ ] Max concurrent connections: ___
  - [ ] Max error rate allowed: ___
  - [ ] Max p95 latency allowed: ___
  - [ ] Services affected: ___
- [ ] **Customer-facing impact assessment:**
  - [ ] Will any customer see degradation? (YES/NO)
  - [ ] If YES, what's the max impact window? ___ minutes
  - [ ] Notification plan if incident declared: ___
- [ ] **Canary configuration verified:**
  - [ ] Traffic split to exactly 5% canary replicas
  - [ ] Rollback automatic if error rate > threshold
  - [ ] Canary replicas labeled for isolation

### 5. Rollback Verification

- [ ] **Rollback handler tested in staging**
  - [ ] Run same experiment on stage first
  - [ ] Verify rollback completes within 2 min
  - [ ] Verify services return to baseline
- [ ] **Rollback trigger verified:**
  - [ ] Error rate threshold correct
  - [ ] p95 latency threshold correct
  - [ ] Max duration hard-coded to ≤ 300 sec
- [ ] **Manual rollback plan documented:**
  - [ ] If automatic rollback fails: ___
  - [ ] Escalation contact: ___
  - [ ] Estimated recovery time: ___ minutes

---

## Pre-Experiment Phase (Monitoring Setup)

### 6. Monitoring & Alerting

- [ ] **CloudMonitoring dashboard open:**
  - [ ] Error rate graph visible & baseline marked
  - [ ] p95 latency graph visible & baseline marked
  - [ ] CPU/memory utilization visible
  - [ ] Refresh rate: 10 sec (not default 60 sec)
- [ ] **Alerting rules created (temporary):**
  - [ ] Alert if error rate > (threshold + 2x buffer)
  - [ ] Alert if p95 > (threshold + 500 ms buffer)
  - [ ] Notification: @incident_commander Slack
- [ ] **Log aggregation ready:**
  - [ ] CloudLogging filter prepared: `experiment_id="<run_id>"`
  - [ ] BigQuery dashboard (if applicable)
  - [ ] Custom alerts for chaos-specific patterns

### 7. Communication Readiness

- [ ] **Slack channels joined:**
  - [ ] #platform-resilience (core team)
  - [ ] #incident-management (incident room, if opened)
  - [ ] @incident_commander channel created (if needed)
- [ ] **Status message template prepared:**
  ```
  🧪 CHAOS EXPERIMENT START
  Experiment: <name>
  Environment: PRODUCTION
  Expected Duration: <max_duration_sec> sec
  Requester: <telegram_handle>
  Monitoring: <dashboard_link>
  Abort Triggers:
    - Error rate ≥ <X>%
    - p95 latency ≥ <Y> ms
    - S1 defect detected
  Expected Outcome: <hypothesis>
  ```
- [ ] **Escalation path clear:**
  - [ ] Level 1: Incident Commander
  - [ ] Level 2: Platform Lead
  - [ ] Level 3: VP Engineering

---

## Execution Phase

### 8. Pre-Launch Validation (5 min before)

- [ ] **Incident Commander confirms readiness** ✅
- [ ] **All monitoring dashboards open & updating**
- [ ] **Baseline metrics recorded:**
  - [ ] Error rate: ___ %
  - [ ] p95 latency: ___ ms
  - [ ] CPU per replica: ___ %
  - [ ] Active connections: ___
- [ ] **No deployments in progress:**
  ```bash
  gcloud run deployments list --filter="status:DEPLOYING"
  # Should return: (No deployments in DEPLOYING state)
  ```
- [ ] **Database connection pool healthy:**
  ```bash
  curl http://api:8000/health | jq .db_pool_status
  # Expected: {"available": XX, "total": XX, "used": YY}
  ```
- [ ] **Slack thread created for real-time updates**

### 9. Launch Experiment

**Send Telegram command:**
```
/chaos_run <experiment> prod --approve
```

**Expected response (202 Accepted):**
```
🔥 Chaos experiment started!
Experiment: <name>
Environment: PRODUCTION
Run ID: 550e8400-e29b-41d4-a716-446655440000
```

**Post to Slack:**
```
🧪 EXPERIMENT LAUNCHED
Run ID: 550e8400
Status: RUNNING
Time: [timestamp]
Monitoring: [dashboard link]
```

---

### 10. Real-Time Monitoring Loop (Every 1 min)

**During the experiment, continuously check:**

✅ **Metrics Within Tolerances:**
- [ ] Error rate < (abort threshold + buffer)
- [ ] p95 latency < (abort threshold + buffer)
- [ ] No cascading latency increases

✅ **System Health:**
- [ ] Database connections not exhausted
- [ ] Cloud Run instances healthy
- [ ] Memory/CPU not maxed out

✅ **No New S1 Defects:**
- [ ] Defect system queried for new S1s
- [ ] If found → Immediate abort

✅ **Application Behavior:**
- [ ] Requests completing (not hanging)
- [ ] No timeout errors (unless expected for the experiment)
- [ ] No data corruption (check DB integrity if applicable)

**If ANY issue detected → `/chaos_stop <run_id>`**

---

### 11. Abort Conditions (Automatic or Manual)

**Automatic abort triggered by SafetyController when:**
- ❌ Error rate ≥ X%
- ❌ p95 latency ≥ Y ms
- ❌ Elapsed time ≥ max_duration_sec
- ❌ S1 defect detected

**Manual abort if:**
- ❌ Unexpected impact on customers (support requests spiking)
- ❌ Monitoring metrics not reliably updating (blind spot)
- ❌ Unknown behavior observed (not matching hypothesis)
- ❌ Incident Commander requests stop

**Abort command:**
```
/chaos_stop 550e8400
```

**Expected response:**
```
⛔ Experiment stopped + rollback triggered
Run ID: 550e8400
Message: <rollback_action>
```

---

## Post-Experiment Phase

### 12. Recovery Verification (5 min after completion)

- [ ] **Experiment status:**
  ```bash
  /chaos_history
  # Check last run shows: completed OR rolled_back
  ```
- [ ] **Metrics returned to baseline:**
  - [ ] Error rate ≤ baseline + 0.5% (within 2 min)
  - [ ] p95 latency ≤ baseline + 100 ms (within 2 min)
  - [ ] CPU/memory normalized
- [ ] **No residual effects:**
  - [ ] No hanging requests
  - [ ] DB connection pool healthy
  - [ ] All services responding to health checks
- [ ] **Rollback handler executed successfully:**
  - [ ] Check logs for rollback message
  - [ ] Verify injection removed (e.g., latency middleware disabled)
  - [ ] If failed: **ESCALATE to Platform Lead**

### 13. Data Integrity Check

- [ ] **For booking-related experiments:**
  ```sql
  -- Check for conflicting bookings
  SELECT COUNT(*) FROM bookings 
  WHERE time_slot_start < (SELECT MAX(time_slot_end) 
                           FROM bookings b2 WHERE b2.id != bookings.id);
  # Expected: 0
  ```

- [ ] **For secret rotation experiments:**
  - [ ] Check auth token validity
  - [ ] Verify no requests stuck in "auth pending" state
  - [ ] Check user session continuity

- [ ] **General:**
  - [ ] No orphaned records in DB
  - [ ] Replication lag < 1 sec
  - [ ] No unintended locks

### 14. Metrics & Learning Collection

- [ ] **Query final metrics:**
  ```bash
  curl http://localhost:8000/chaos/metrics?window_days=1 | jq .
  ```
  - [ ] MTTR: ___ sec
  - [ ] Auto-recovery rate: ___ %
  - [ ] Rollback frequency: ___ (should be 0 or 1)

- [ ] **Record learnings:**
  - [ ] Experiment ran as expected? (YES/NO)
  - [ ] Hypothesis confirmed? (YES/NO)
  - [ ] Any surprising behaviors? List:
    ```
    - ___
    - ___
    ```
  - [ ] Defects exposed? (Link to defect IDs)

- [ ] **Update runbook:**
  - [ ] Add actual MTTR to runbook
  - [ ] Document any manual steps needed
  - [ ] Update abort thresholds if needed

### 15. Post-Mortem & Communication

- [ ] **Create Slack summary message:**
  ```
  ✅ CHAOS EXPERIMENT COMPLETE
  
  Experiment: <name>
  Duration: <actual_duration_sec>
  Status: COMPLETED
  Requester: <telegram_handle>
  
  Results:
  - MTTR: <mttr_sec> sec ✅
  - Error Rate Peak: <peak_error_rate>% ✅
  - p95 Latency Peak: <peak_latency_ms> ms ✅
  - Auto-Recovery: YES ✅
  
  Hypothesis: [Confirmed / Disproven / Partially Confirmed]
  Key Learnings:
  - ___
  - ___
  
  Next Actions:
  - [ ] File defect if needed (link: ___)
  - [ ] Update alerting thresholds (link: ___)
  - [ ] Archive results (link: ___)
  ```

- [ ] **Notify stakeholders:**
  - [ ] Post summary to #platform-resilience
  - [ ] Email to Compliance Officer
  - [ ] Update Chaos Engineering dashboard

- [ ] **Schedule debrief (if defects found):**
  - [ ] Invite: Platform Lead, Engineering Lead, Product
  - [ ] Discuss: Root cause, remediation, timeline

---

## Quality Assurance Sign-Off

### 16. Final Approval

- [ ] **Incident Commander sign-off:**
  - Name: ___
  - Timestamp: ___
  - Notes: ___

- [ ] **Platform Lead approval:**
  - Name: ___
  - Timestamp: ___
  - Notes: ___

- [ ] **Compliance Officer notified:**
  - Name: ___
  - Timestamp: ___
  - Status: ✅ Approved / ⚠️ Issues Found

---

## Appendix: Quick Reference

### Abort Thresholds by Experiment

| Experiment | Error Rate | p95 Latency | Duration |
|-----------|-----------|-----------|----------|
| api_latency_injection | 10% | 2000 ms | 300 sec |
| db_connection_saturation | 10% | 5000 ms | 180 sec |
| cloud_run_instance_kill | 5% | 3000 ms | 120 sec |
| secret_rotation_simulation | 2% (auth) | none | 300 sec |
| network_timeout_api_db | 15% | 5000 ms | 180 sec |
| high_concurrency_spike | 5% | 3000 ms | 300 sec |

### Emergency Contacts

| Role | Name | Slack | Phone |
|------|------|-------|-------|
| Incident Commander | ___ | @___ | ___ |
| Platform Lead | ___ | @___ | ___ |
| VP Engineering | ___ | @___ | ___ |
| On-Call SRE | ___ | @___ | ___ |

### Dashboard Links

- **CloudMonitoring:** https://console.cloud.google.com/monitoring/dashboards/custom/inka-chaos
- **CloudLogging:** https://console.cloud.google.com/logs/query
- **BigQuery:** `inka_prod.chaos_runs` table
- **Grafana:** https://grafana.inka.internal/d/chaos-engineering

---

**Reviewed & Approved By:**
- Platform Lead: _________________ Date: _____
- Compliance Officer: _________________ Date: _____
- VP Engineering: _________________ Date: _____

**Next Review Date:** _______________
