# Chaos Engineering: Operational Runbook

**Purpose:** Step-by-step procedures for common chaos engineering scenarios.

---

## Scenario 1: Run Your First Chaos Test (Dev Environment)

**Goal:** Test the system with low risk; understand the flow

**Time:** 20 minutes

### Steps

**1. Preparation (5 min)**

```bash
# Ensure access to Telegram bot
# Should have "admin" or "resilience_authority" role

# Open monitoring dashboard
# https://console.cloud.google.com/monitoring/dashboards/custom/inka-chaos
```

**2. List Available Experiments (2 min)**

```
Send Telegram message:
/chaos_list dev

Response should show 9 experiments available for dev
```

**3. Choose an Experiment**

**Recommendation:** Start with `api_latency_injection`
- Simple to understand (adds 500ms delay)
- No database access required
- Easy to observe in metrics
- Auto-recovers quickly

**4. Start the Experiment (2 min)**

```
Send Telegram message:
/chaos_run api_latency_injection dev

Expected response:
✅ Experiment started!
Run ID: <8-char ID>
```

**5. Monitor in Real-Time (5 min)**

Watch the experiment:

```
# Every 30 seconds, run:
/chaos_history

# Check:
- Is experiment in "running" state?
- Error rate increasing? (expect 0-2% with latency injection)
- p95 latency increasing? (expect 500-600ms above baseline)
```

**Real-time monitoring via dashboard:**
```
Open: https://console.cloud.google.com/monitoring
Search for: inka-api error_rate and p95_latency metrics
```

**6. Experiment Completes (5 min wait)**

After ~5 minutes:

```
/chaos_history
# Should show status changed from "running" to "completed"
# Duration should show ~300 seconds
```

**7. Review Results**

```
/chaos_history
# Check MTTR: 42.5 sec (this is the recovery time)
# Check auto_recovery_rate: 87.5% (successful experiments without manual rollback)
```

**8. Troubleshoot if Needed**

If experiment was aborted early:

```
/chaos_history
# Check status: "rolled_back" means safety gate triggered
# Read abort_reason field for details
# Common: error_rate exceeded threshold
```

---

## Scenario 2: Manual Abort of Running Experiment

**Goal:** Stop an experiment that's causing unexpected impact

**Time:** < 1 minute

### Steps

**1. Identify the Run ID**

```
/chaos_history

# Find the "running" experiment and note the run ID (e.g., 550e8400)
```

**2. Send Stop Command**

```
/chaos_stop 550e8400

Expected response:
⛔ Experiment stopped + rollback triggered

Run ID: 550e8400
Message: [Rollback action description]
```

**3. Verify Recovery**

```
# Immediately check metrics
/chaos_history

# Wait 2 minutes then check again
# Expect: error_rate and p95_latency return to baseline
```

**4. Escalate if Needed**

If metrics don't recover within 3 minutes:

```
1. Slack: @incident_commander (page if necessary)
2. Manual recovery may be needed:
   gcloud run services update inka-api \
     --region europe-west1 \
     --image gcr.io/inka-prod/inka-api:latest
3. File S1 defect: "Chaos rollback failed for <experiment>"
```

---

## Scenario 3: Production Chaos (High Stakes)

**Goal:** Run validated chaos test on production with compliance

**Time:** 45 minutes (15 min prep + 15 min execution + 15 min debrief)

### Pre-Execution (15 min before)

**1. Communicate with Team**

```
Post to #platform-resilience:

🧪 CHAOS EXPERIMENT ALERT

Experiment: high_concurrency_spike
Time: 10:00 UTC (in 15 min)
Environment: PRODUCTION
Expected Duration: 5 min
Expected Impact: p95 latency +1500ms (temporary)

Monitoring: [dashboard link]
Stop Command: /chaos_stop <run_id>
Questions? Reply in thread
```

**2. Verify Pre-Requisites**

```
Checklist:
☐ No active S1/S2 defects: curl api:8000/internal/defects
☐ Incident Commander available (Slack: @ic_name)
☐ CloudMonitoring dashboard open & refreshing (10s interval)
☐ No ongoing deployments: gcloud run deployments list
☐ Database health ok: curl api:8000/health | jq .db_pool_status
☐ Compliance token obtained (from Compliance Officer)
```

**3. Load Monitoring Dashboards**

```
Open:
1. https://console.cloud.google.com/monitoring
   → Custom dashboard: inka-chaos
   → Graphs: error_rate, p95_latency, cpu, memory

2. https://console.cloud.google.com/logs/query
   → Filter: severity >= WARNING

3. Grafana: https://grafana.inka.internal/
   → Dashboard: Chaos Engineering
```

### Execution (15 min)

**4. Launch Experiment**

```
Send Telegram:
/chaos_run high_concurrency_spike prod --approve

Response:
🔥 Chaos experiment started!
Experiment: high_concurrency_spike
Environment: PRODUCTION
Run ID: 550e8400
Requester: telegram:@your_handle

Post to Slack: "Experiment launched: 550e8400"
```

**5. Monitor Every Minute**

```
Checklist (repeat every 60 seconds):

☐ Error rate < 5% threshold? ✅
☐ p95 latency < 3000 ms threshold? ✅
☐ No new S1 defects appearing? ✅
☐ CloudRun instances healthy? ✅
☐ Database connections not maxed? ✅
☐ Requests completing (not hanging)? ✅

If ANY issue detected:
  /chaos_stop 550e8400
  → Investigate root cause
  → File S2 defect
```

**6. Experiment Completes**

After ~5 minutes:

```
/chaos_history

Status should show: "completed"
(Not: "rolled_back" or "failed")
```

### Post-Execution (15 min)

**7. Verify Recovery**

```
✅ Metrics returned to baseline within 3 minutes?
✅ No residual latency/errors?
✅ All services responding?
✅ Database consistent?

If all yes → continue to debrief
If no → escalate to incident commander
```

**8. Record Results**

```
/chaos_history

Record:
- MTTR: _____ sec (from metrics display)
- Auto-recovery: YES/NO
- Peak error rate: _____ %
- Peak p95: _____ ms
- Any surprising behaviors: _____
```

**9. Debrief in Slack**

```
Post summary to #platform-resilience:

✅ CHAOS EXPERIMENT COMPLETE

Experiment: high_concurrency_spike
Duration: 5m 0s
Status: COMPLETED ✅

Metrics:
- MTTR: 42 sec ✅
- Error Rate Peak: 4.2% ✅
- p95 Latency Peak: 2850 ms ✅
- Auto-Recovery: YES ✅

Hypothesis: [Confirmed / Disproven]

Key Learnings:
- ___

Next Actions:
- [File S2 if needed]
- [Update thresholds if needed]
```

**10. Archive Results**

```
Link to metrics:
https://bigquery.cloud.google.com/table/...

Attach to deployment ticket for this week
```

---

## Scenario 4: Respond to Chaos Experiment Failure

**Goal:** Understand why an experiment failed and remediate

**Time:** 30 minutes (diagnosis + remediation)

### Situation

Experiment was aborted early with:
```
Status: rolled_back
Abort Reason: "Error rate 12.1% >= threshold 10%"
```

### Steps

**1. Understand What Happened**

```
The experiment was auto-aborted because:
- Experiment: [name]
- Abort Trigger: Error rate ≥ 10%
- Actual Peak: 12.1%
- This means: The system's error handling is not as resilient as assumed
```

**2. Query Detailed Metrics**

```bash
# Get all metric snapshots from this run
gcloud logging read \
  'jsonPayload.experiment_id="550e8400"' \
  --format=json | jq '.[] | .jsonPayload | {timestamp, error_rate_pct, p95_latency_ms}'

# Get exact error messages
gcloud logging read \
  'jsonPayload.experiment_id="550e8400" AND severity >= ERROR' \
  --format json | jq '.[] | .jsonPayload'
```

**3. Root Cause Analysis**

Ask:
- **What was the chaos injection?** (e.g., +500ms latency)
- **Why did it cause errors?** (e.g., timeout in downstream service)
- **Is this expected?** (e.g., service doesn't have retry logic)
- **Is this a real issue?** (would happen in production if network degraded)

**4. File a Defect**

If the failure reveals a real issue:

```
Create S2 defect:

Title: "[Resilience] <service> fails under <condition>"
Example: "[Resilience] API service fails under 500ms latency"

Description:
Chaos experiment: api_latency_injection
Trigger: Error rate reached 12.1% at +500ms latency
Expected: System should handle with < 10% error rate
Actual: 12.1% error rate observed

Impact: [Critical/High/Medium] during production network degradation
Recommendation: Implement circuit breaker / timeout handling
```

**5. Remediation**

```
Option A: Fix the underlying issue (e.g., add retry logic)
  → Re-run experiment → should now pass

Option B: Accept the risk (e.g., rare scenario)
  → Increase abort threshold
  → Document in runbook
  → Ticket for future optimization

Option C: Adjust experiment (if too aggressive)
  → Reduce latency injection (e.g., +300ms instead of +500ms)
  → Re-run for validation
```

**6. Document Learnings**

```
Update: docs/chaos-engineering/IMPLEMENTATION_SUMMARY.md

Add section:
"Known Issues from Chaos Testing"
- Issue: <description>
- Exposed by: <experiment>
- Status: [Fixed / Accepted Risk / In Progress]
- Tracking: [Defect ID]
```

---

## Scenario 5: Integrate Chaos into CI/CD Pipeline

**Goal:** Automatically run chaos tests on every staging deployment

**Time:** 1 hour (setup)

### Implementation

**1. Create GitHub Actions Workflow**

```yaml
# .github/workflows/post-deploy-chaos-testing.yml

name: Post-Deploy Chaos Testing

on:
  workflow_run:
    workflows: ["Deploy to Staging"]
    types: [completed]

jobs:
  chaos-validation:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    steps:
      - name: Wait for deployment stabilization
        run: sleep 60
      
      - name: Run Chaos Experiments
        run: |
          # Array of experiments to run on staging
          EXPERIMENTS=(
            "api_latency_injection"
            "db_connection_saturation"
          )
          
          for EXP in "${EXPERIMENTS[@]}"; do
            echo "Starting: $EXP"
            
            RUN_ID=$(curl -X POST ${{ secrets.CHAOS_API_BASE }}/chaos/run \
              -H "Authorization: Bearer ${{ secrets.CHAOS_API_TOKEN }}" \
              -H "Content-Type: application/json" \
              -d "{
                \"experiment_name\": \"$EXP\",
                \"environment\": \"stage\",
                \"requester\": \"ci-system\"
              }" | jq -r '.run_id')
            
            echo "Run ID: $RUN_ID"
            
            # Wait for completion (poll every 15s, max 10 min)
            for i in {1..40}; do
              STATUS=$(curl -s -X GET \
                "${{ secrets.CHAOS_API_BASE }}/chaos/history?limit=1" \
                -H "Authorization: Bearer ${{ secrets.CHAOS_API_TOKEN }}" \
                | jq -r '.[0].status')
              
              if [ "$STATUS" != "running" ]; then
                echo "Experiment completed: $STATUS"
                break
              fi
              
              echo "Waiting... ($i/40)"
              sleep 15
            done
          done
      
      - name: Validate Metrics
        run: |
          METRICS=$(curl -s -X GET \
            "${{ secrets.CHAOS_API_BASE }}/chaos/metrics?window_days=1" \
            -H "Authorization: Bearer ${{ secrets.CHAOS_API_TOKEN }}")
          
          MTTR=$(echo $METRICS | jq '.avg_mttr_sec')
          AUTO_RECOVERY=$(echo $METRICS | jq '.auto_recovery_rate_pct')
          
          echo "MTTR: $MTTR sec (target: < 60)"
          echo "Auto-Recovery: $AUTO_RECOVERY% (target: >= 85)"
          
          # Check SLA
          MTTR_OK=$(echo "$MTTR < 60" | bc -l)
          RECOVERY_OK=$(echo "$AUTO_RECOVERY >= 85" | bc -l)
          
          if [ $MTTR_OK -eq 0 ]; then
            echo "❌ MTTR SLA failed"
            exit 1
          fi
          
          if [ $RECOVERY_OK -eq 0 ]; then
            echo "❌ Auto-recovery SLA failed"
            exit 1
          fi
          
          echo "✅ All chaos validation passed"
      
      - name: Report Results
        if: always()
        run: |
          # Post summary comment to pull request
          # (implementation depends on your PR system)
          curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
            -H "Content-Type: application/json" \
            -d "{
              \"text\": \"Post-deploy chaos testing: ${{ job.status }}\",
              \"blocks\": [{
                \"type\": \"section\",
                \"text\": {
                  \"type\": \"mrkdwn\",
                  \"text\": \"*Chaos Validation*\n${{ job.status }}\n<${{ secrets.CHAOS_DASHBOARD }}|View Dashboard>\"
                }
              }]
            }"
```

**2. Set GitHub Secrets**

```bash
# In GitHub repo settings → Secrets → New secret

CHAOS_API_BASE = "http://api:8000"
CHAOS_API_TOKEN = "<bearer_token>"
CHAOS_DASHBOARD = "https://grafana.internal/d/chaos"
SLACK_WEBHOOK = "https://hooks.slack.com/services/..."
```

**3. Test the Workflow**

```bash
# Trigger by creating a deployment to staging
# Workflow should automatically run
# Check logs in: Actions tab → Post-Deploy Chaos Testing

# If it fails, debug by checking:
# 1. API token is valid
# 2. Chaos service is accessible
# 3. Network connectivity between CI and internal API
```

**4. Block on Failure**

In GitHub branch protection rules:

```
✅ Require "Post-Deploy Chaos Testing" workflow to pass
   (Prevents merging PRs if chaos tests fail)
```

---

## Scenario 6: Troubleshoot Experiment Not Starting

**Goal:** Diagnose why an experiment was blocked by safety gates

**Time:** 10 minutes

### Symptoms

```
⚠️ Safety gate blocked the experiment:
Experiment 'cloud_run_instance_kill' is not allowed in environment 'prod'...
```

or

```
🔐 Safety gate blocked the experiment:
Active S1/S2 defects detected — chaos blocked.
```

### Diagnosis Steps

**1. Check Environment**

```
/chaos_list prod

# Look for the experiment
# If not listed → blocked by environment gate
# Read "Envs: dev, stage" (not prod)
```

**2. Check for Active Defects**

```bash
curl http://api:8000/internal/defects?severity=S1,S2&status=open \
  -H "Authorization: Bearer <token>"

# If count > 0:
# Active defects are blocking prod chaos
# Resolve them first, then retry
```

**3. Check Compliance Approval**

```
If error says "requires compliance approval":
  /chaos_run <experiment> prod --approve
  # Retry with --approve flag
```

**4. Check Max Duration**

```
This should never fail (hardcoded limit is 300s)
But if it does: experiment definition is invalid
Contact platform team
```

### Resolution

| Error | Solution |
|-------|----------|
| "Not allowed in environment" | Use staging instead, or request approval for prod |
| "Active S1/S2 defects" | Resolve defects in defect system, then retry |
| "Requires compliance approval" | Add `--approve` flag, confirm you have sign-off |
| "Max duration exceeded" | Contact platform team (config error) |

---

## Scenario 7: Schedule Regular Chaos Tests

**Goal:** Establish routine resilience testing (e.g., weekly)

**Time:** 15 minutes setup + 5 min per week for monitoring

### Weekly Chaos Test Plan

**Option A: Automated via Calendar Reminder**

```
# Create recurring event in team calendar
Title: "Weekly Chaos Test"
Time: Every Monday 10:00 UTC
Duration: 30 min
Description: Run scheduled resilience tests

Note: Adjust time to match low-traffic window
```

**Option B: Automated via Scheduled Job**

```bash
# Create Cloud Scheduler job that triggers chaos every Monday

gcloud scheduler jobs create http weekly-chaos-test \
  --location europe-west1 \
  --schedule "0 10 * * MON"  # Every Monday at 10:00 UTC \
  --http-method POST \
  --uri http://api:8000/chaos/run \
  --headers "Authorization=Bearer ${CHAOS_TOKEN}" \
  --message-body '{
    "experiment_name": "api_latency_injection",
    "environment": "stage",
    "requester": "ci-scheduler"
  }'
```

**Option C: Manual Discipline**

```
Each Monday:
1. Team lead sends message to #platform-resilience
2. Reminder: "Time for weekly chaos test"
3. Someone executes: /chaos_run api_latency_injection stage
4. Team monitors and documents results
```

### Recommended Weekly Schedule

```
Monday:   api_latency_injection (stage)
Wednesday: db_connection_saturation (stage)
Friday:   booking_conflict_surge (dev)

Rotate through other experiments monthly
Document all results in shared spreadsheet
```

### Tracking Results

```
# Spreadsheet columns:
| Date | Experiment | Env | Status | MTTR | Notes |
|------|------------|-----|--------|------|-------|
| 2/24 | api_lat... | stg | ✅     | 42s  |       |
| 2/26 | db_satur.. | stg | ✅     | 58s  | Pool responsive |
| 2/28 | booking... | dev | ⚠️     | 65s  | File S2: conflict detection slow |
```

---

## Appendix: Quick Commands

### Common Telegram Commands

```bash
# List experiments
/chaos_list
/chaos_list stage
/chaos_list prod

# Run experiments
/chaos_run api_latency_injection dev
/chaos_run db_connection_saturation stage
/chaos_run cloud_run_instance_kill prod --approve

# Stop running experiment
/chaos_stop 550e8400

# View history & metrics
/chaos_history
/chaos_history dev
/chaos_history stage
```

### Common API Calls

```bash
# List experiments
curl http://api:8000/chaos/experiments \
  -H "Authorization: Bearer $TOKEN"

# Start experiment
curl -X POST http://api:8000/chaos/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"experiment_name":"api_latency_injection","environment":"stage"}'

# Stop experiment
curl -X POST http://api:8000/chaos/stop/550e8400 \
  -H "Authorization: Bearer $TOKEN"

# View history
curl http://api:8000/chaos/history?limit=10 \
  -H "Authorization: Bearer $TOKEN"

# Get metrics
curl http://api:8000/chaos/metrics?window_days=30 \
  -H "Authorization: Bearer $TOKEN"
```

### Common gcloud Commands

```bash
# Check for active defects
curl http://api:8000/internal/defects?severity=S1,S2 \
  -H "Authorization: Bearer $TOKEN"

# Check system health
curl http://api:8000/health | jq .

# View logs for experiment
gcloud logging read 'jsonPayload.experiment_id="550e8400"' \
  --limit 50 --format json | jq .

# Manually restart service (emergency)
gcloud run services update inka-api \
  --region europe-west1 \
  --image gcr.io/inka-prod/inka-api:latest
```

---

**Need help?** Slack: #platform-resilience
