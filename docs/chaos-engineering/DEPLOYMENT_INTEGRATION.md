# Chaos Engineering: Deployment Governor & Risk Predictor Integration

**Purpose:** Ensure chaos engineering system integrates seamlessly with deployment governance and risk prediction systems to provide holistic resilience visibility.

---

## 1. Deployment Governor Integration

### 1.1 Block Deployments During Active Chaos

**Problem:** Deploying while chaos is running makes it impossible to isolate causes of failures.

**Solution:** Deployment Governor checks for active chaos runs before allowing deployment.

**Implementation:**

```python
# In deployment_governor.py

from packages.chaos.models import ChaosRun, RunStatus
from sqlalchemy import select

async def check_active_chaos_runs(session) -> bool:
    """Check if any chaos experiments are currently running."""
    result = await session.execute(
        select(ChaosRun).where(ChaosRun.status == RunStatus.RUNNING)
    )
    active_runs = result.scalars().all()
    return len(active_runs) > 0

async def can_deploy(
    service: str,
    environment: str,
    session=None,
) -> tuple[bool, str]:
    """
    Determine if a deployment is allowed.
    Raises if active chaos runs detected.
    """
    if session is None:
        return True, "No DB session"
    
    if await check_active_chaos_runs(session):
        active_runs = await get_active_chaos_runs_summary(session)
        reason = f"Active chaos runs: {active_runs}"
        return False, reason
    
    return True, "OK"
```

**Usage in Deployment Governor:**

```python
@app.post("/deploy")
async def request_deployment(
    request: DeploymentRequest,
    session: AsyncSession = Depends(get_db_session),
):
    can_deploy, reason = await check_active_chaos_runs_gate(session)
    if not can_deploy:
        raise HTTPException(
            status_code=409,
            detail=f"Deployment blocked: {reason}"
        )
    
    # Proceed with deployment...
```

**Slack Notification (if deployment blocked):**

```
⚠️ DEPLOYMENT BLOCKED

Service: inka-api
Version: v2.3.4
Reason: Active chaos run detected

Active Runs:
- 550e8400 (api_latency_injection on stage)
- 661f9abc (db_connection_saturation on dev)

Please wait for chaos experiments to complete.
Expected: ~5 minutes

Monitor: /chaos_history
```

---

### 1.2 Link Deployment to Chaos Test Results

**Problem:** No traceability between deployment and its chaos testing results.

**Solution:** Add chaos test result link to deployment record.

**Database Schema Extension:**

```python
# In deployment_governor models

class Deployment(Base):
    __tablename__ = "deployments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service = Column(String(128), nullable=False)
    version = Column(String(64), nullable=False)
    environment = Column(String(32), nullable=False)
    deployed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # NEW: Link to chaos test runs
    chaos_test_runs = relationship(
        "ChaosRun",
        secondary="deployment_chaos_run_links",
        viewonly=True
    )
    chaos_test_status = Column(
        String(32),
        nullable=True,
        default=None,
        comment="'passed', 'failed', 'pending', or null if no tests run"
    )
    chaos_test_completed_at = Column(DateTime, nullable=True)

class DeploymentChaosRunLink(Base):
    """Join table: which chaos runs validated which deployments."""
    __tablename__ = "deployment_chaos_run_links"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.id"))
    run_id = Column(UUID(as_uuid=True), ForeignKey("chaos_runs.id"))
    link_created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Link reason
    reason = Column(
        String(256),
        nullable=False,
        comment="e.g., 'post-deploy stage validation' or 'canary validation'"
    )
```

**Workflow:**

```
1. Deployment to staging completes
   ↓
2. Deployment Governor creates Deployment record
   ↓
3. CI/CD post-deploy hook triggers:
   - /chaos_run api_latency_injection stage
   - /chaos_run db_connection_saturation stage
   ↓
4. CI/CD waits for chaos runs to complete (~10 min)
   ↓
5. Query /chaos/history?env=stage
   ↓
6. Check metrics:
   - auto_recovery_rate ≥ 85%? ✅
   - avg_mttr ≤ 60 sec? ✅
   ↓
7. If PASS: Update Deployment.chaos_test_status = "passed"
   If FAIL: Update Deployment.chaos_test_status = "failed"
          Block promotion to production
   ↓
8. Create DeploymentChaosRunLink records
```

**CI/CD Pipeline Integration (GitHub Actions):**

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
      
      - name: Run API Latency Test
        run: |
          curl -X POST ${{ secrets.CHAOS_API_BASE }}/chaos/run \
            -H "Authorization: Bearer ${{ secrets.CHAOS_API_TOKEN }}" \
            -d '{
              "experiment_name": "api_latency_injection",
              "environment": "stage",
              "requester": "ci-system"
            }' | jq -r '.run_id' > run_id.txt
      
      - name: Wait for experiment completion
        run: |
          RUN_ID=$(cat run_id.txt)
          for i in {1..40}; do
            STATUS=$(curl -X GET \
              ${{ secrets.CHAOS_API_BASE }}/chaos/history?limit=1 \
              -H "Authorization: Bearer ${{ secrets.CHAOS_API_TOKEN }}" \
              | jq -r '.[0].status')
            
            if [ "$STATUS" != "running" ]; then
              echo "Experiment completed with status: $STATUS"
              break
            fi
            
            echo "Waiting for experiment... ($i/40)"
            sleep 15
          done
      
      - name: Evaluate results
        run: |
          METRICS=$(curl -X GET \
            ${{ secrets.CHAOS_API_BASE }}/chaos/metrics?window_days=1 \
            -H "Authorization: Bearer ${{ secrets.CHAOS_API_TOKEN }}")
          
          MTTR=$(echo $METRICS | jq '.avg_mttr_sec')
          AUTO_RECOVERY=$(echo $METRICS | jq '.auto_recovery_rate_pct')
          
          echo "MTTR: ${MTTR} sec (target: < 60)"
          echo "Auto-Recovery: ${AUTO_RECOVERY}% (target: >= 85)"
          
          if (( $(echo "$MTTR > 60" | bc -l) )); then
            echo "❌ MTTR SLA violated"
            exit 1
          fi
          
          if (( $(echo "$AUTO_RECOVERY < 85" | bc -l) )); then
            echo "❌ Auto-recovery rate below SLA"
            exit 1
          fi
          
          echo "✅ All chaos tests passed!"
      
      - name: Notify results
        if: always()
        run: |
          # Post to Slack with results
          curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
            -d '{
              "text": "Post-deploy chaos testing completed",
              "status": "${{ job.status }}"
            }'
```

---

## 2. Risk Predictor Integration

### 2.1 Chaos Resilience Score

**Purpose:** Quantify system resilience based on chaos testing results. Lower resilience = higher product risk.

**Formula:**

```
chaos_resilience_score (0-100) = 
    auto_recovery_rate_pct * 0.4 +
    (100 - (mttr_sec / 60 * 100)) * 0.3 +
    (100 - failed_test_rate_pct * 10) * 0.3
```

**Components:**

| Component | Weight | Formula | Target |
|-----------|--------|---------|--------|
| Auto-Recovery Rate | 40% | `%` of completed without rollback | 85%+ |
| MTTR Score | 30% | `(1 - mttr/60) * 100` | < 60 sec |
| Resilience Test Success | 30% | `(1 - failed_tests) * 100` | ≤ 2 failures/month |

**Implementation:**

```python
# In risk_predictor.py

from packages.chaos.metrics import ChaosMetricsCollector

class ChaosResilienceScorer:
    """Compute resilience score from chaos testing results."""
    
    async def compute_score(
        self,
        session,
        window_days: int = 30,
    ) -> dict:
        """
        Compute chaos resilience score (0-100).
        
        Returns:
            {
                "score": 75.3,
                "components": {
                    "auto_recovery_rate": 87.5,
                    "mttr_score": 75.0,
                    "test_success_rate": 66.7
                },
                "trend": "improving",
                "recommendations": [...]
            }
        """
        collector = ChaosMetricsCollector()
        metrics = await collector.dashboard_summary(session, window_days)
        
        # Auto-recovery rate (0-100)
        auto_recovery = metrics["auto_recovery_rate_pct"]
        
        # MTTR score (100 = 0 sec, 0 = 60+ sec)
        mttr_sec = metrics["avg_mttr_sec"]
        mttr_score = max(0, 100 - (mttr_sec / 60 * 100))
        
        # Test success rate
        failed_tests = metrics["failed_resilience_tests"]
        total_runs = metrics["total_runs"]
        success_rate = max(0, 100 - (failed_tests / max(total_runs, 1) * 100))
        
        # Weighted score
        overall_score = (
            auto_recovery * 0.4 +
            mttr_score * 0.3 +
            success_rate * 0.3
        )
        
        return {
            "score": round(overall_score, 1),
            "components": {
                "auto_recovery_rate": round(auto_recovery, 1),
                "mttr_score": round(mttr_score, 1),
                "test_success_rate": round(success_rate, 1),
            },
            "metrics": {
                "avg_mttr_sec": round(mttr_sec, 1),
                "rollback_frequency": metrics["rollback_frequency"],
                "failed_tests": failed_tests,
            },
            "trend": await self._compute_trend(session, window_days),
            "recommendations": self._generate_recommendations(
                overall_score, metrics
            ),
        }
    
    async def _compute_trend(
        self,
        session,
        window_days: int,
    ) -> str:
        """Compare score to previous 30-day window."""
        current = await self.compute_score(session, window_days)["score"]
        previous = await self.compute_score(session, window_days * 2)["score"]
        
        if current > previous + 5:
            return "improving"
        elif current < previous - 5:
            return "degrading"
        else:
            return "stable"
    
    def _generate_recommendations(
        self,
        score: float,
        metrics: dict,
    ) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if metrics["auto_recovery_rate_pct"] < 85:
            recommendations.append(
                "⚠️ Auto-recovery rate below 85%. "
                "Review rollback handlers and fault detection logic."
            )
        
        if metrics["avg_mttr_sec"] > 60:
            recommendations.append(
                "⚠️ MTTR exceeds 60s target. "
                "Optimize recovery automation."
            )
        
        if metrics["failed_resilience_tests"] > 0:
            recommendations.append(
                f"❌ {metrics['failed_resilience_tests']} failed tests. "
                "File defects and schedule remediation."
            )
        
        if score < 50:
            recommendations.append(
                "🚨 CRITICAL: Resilience score < 50. "
                "Block production deployments until resolved."
            )
        
        if not recommendations:
            recommendations.append("✅ System resilience within acceptable range.")
        
        return recommendations
```

---

### 2.2 Risk Score Impact

**Risk Calculation:**

```python
# In risk_predictor.py

async def compute_product_risk_score(
    features: DeploymentFeatures,
    session: AsyncSession,
) -> RiskScore:
    """
    Compute deployment risk incorporating chaos resilience.
    
    Risk Factors:
    - Code changes (lines changed, complexity)
    - Test coverage (unit, integration, e2e)
    - Deployment frequency (canary / blue-green)
    - **Chaos resilience score** ← NEW
    - Active defects / incidents
    """
    
    base_risk = await compute_traditional_risk_score(features)
    
    # Chaos resilience adjustment
    chaos_scorer = ChaosResilienceScorer()
    resilience = await chaos_scorer.compute_score(session)
    chaos_risk_adjustment = (100 - resilience["score"]) / 100
    
    # If chaos score is low, increase product risk
    adjusted_risk = base_risk * (1 + chaos_risk_adjustment * 0.3)
    
    return RiskScore(
        base_score=base_risk,
        chaos_adjustment=chaos_risk_adjustment,
        final_score=adjusted_risk,
        resilience_details=resilience,
        recommendation=_risk_to_recommendation(adjusted_risk),
    )

def _risk_to_recommendation(risk_score: float) -> str:
    if risk_score < 30:
        return "✅ LOW RISK: Proceed with standard deployment"
    elif risk_score < 50:
        return "⚠️ MEDIUM RISK: Recommend canary deployment"
    elif risk_score < 70:
        return "🔴 HIGH RISK: Enforce 5% canary + extended monitoring"
    else:
        return "🛑 CRITICAL: Block deployment until risk mitigated"
```

**Deployment Decision Flow:**

```
+─────────────────────────────────────┐
│ Deployment Request to Production    │
└─────────────────────────────────────┘
         │
         ↓
+─────────────────────────────────────┐
│ Compute Product Risk Score          │
│ (code changes, test coverage, etc)  │
└─────────────────────────────────────┘
         │
         ↓
+─────────────────────────────────────┐
│ Query Chaos Resilience Score        │
│ (last 30 days of chaos testing)     │
└─────────────────────────────────────┘
         │
         ↓
+─────────────────────────────────────┐
│ Adjust Risk Based on Resilience     │
│ Low resilience = higher risk        │
└─────────────────────────────────────┘
         │
         ↓
+─────────────────────────────────────┐
│ Decision:                           │
│  0-30: ✅ Proceed                   │
│ 30-50: ⚠️ Canary (50%)              │
│ 50-70: 🔴 Canary (5%)               │
│ 70+:   🛑 Block                     │
└─────────────────────────────────────┘
```

---

### 2.3 Dashboard Visibility

**Chaos Resilience Widget (in Risk Dashboard):**

```
┌────────────────────────────────────────────────┐
│ 🧪 CHAOS ENGINEERING RESILIENCE (30 days)      │
├────────────────────────────────────────────────┤
│ Overall Score:  75.3 / 100  📈 improving       │
│                                                │
│ Components:                                    │
│  • Auto-Recovery Rate:   87.5%  ✅ (target 85) │
│  • MTTR:                 45 sec ✅ (target 60) │
│  • Test Success Rate:    66.7%  ⚠️ (target 90) │
│                                                │
│ Metrics (30-day window):                       │
│  • Total Chaos Runs:     8                     │
│  • Completed:            7                     │
│  • Rolled Back:          1                     │
│  • Failed:               0                     │
│  • Failed Resilience:    1  [defect: S2-123]   │
│                                                │
│ Trend: ↗ Improving (was 72.1 last month)       │
│                                                │
│ Recommendations:                               │
│  1. ⚠️ Test success rate below target          │
│  2. ✅ MTTR within acceptable range            │
│  3. 📋 Schedule chaos test for secret_rotation │
│                                                │
│ Last Run: api_latency_injection on stage       │
│ Status: ✅ PASSED (MTTR: 42s, Recovery: 100%)  │
└────────────────────────────────────────────────┘
```

---

## 3. Integration Workflow

### 3.1 Pre-Deployment Checklist

```python
# In deployment_governor.py

async def pre_deployment_checklist(
    service: str,
    version: str,
    target_env: str,
    session: AsyncSession,
) -> DeploymentApproval:
    """
    Complete deployment pre-flight checklist.
    Returns: approved=True/False with detailed reasons.
    """
    
    checks = {
        "no_active_chaos": await check_no_active_chaos_runs(session),
        "chaos_resilience_ok": await check_chaos_resilience_score(session, min_score=60),
        "no_s1_defects": await check_no_active_s1_defects(session),
        "test_coverage": await check_test_coverage(service, version, min_coverage=80),
        "blue_green_ready": await check_blue_green_setup(service, target_env),
    }
    
    all_passed = all(checks.values())
    
    return DeploymentApproval(
        approved=all_passed,
        checks=checks,
        timestamp=datetime.utcnow(),
        approved_by=None,  # Requires manual approval if any check fails
    )
```

---

### 3.2 Monitoring & Alerting

**Alert Conditions:**

| Alert | Condition | Action |
|-------|-----------|--------|
| Low Resilience | chaos_resilience_score < 50 | Notify SRE team, block prod deployments |
| High Rollback Rate | rollback_frequency > 5/month | Page incident commander, review rollback handlers |
| MTTR Degradation | mttr_trend = "degrading" | Investigate recovery automation |
| Test Failure | failed_resilience_tests > 0 | File S2 defect, add to backlog |

**Slack Integration:**

```yaml
# alerts/chaos-resilience.yaml

- name: "Low Resilience Score"
  condition: "chaos_resilience_score < 50"
  channel: "#platform-resilience"
  message: |
    🚨 CRITICAL: Chaos resilience score is {{ score }}/100
    
    This indicates system resilience has degraded.
    Implications: Production deployments will be blocked.
    
    Review:
    - Auto-recovery rate: {{ auto_recovery }}%
    - MTTR: {{ mttr_sec }}s
    - Failed tests: {{ failed_tests }}
    
    Action: Review failed resilience tests and file defects.
    Dashboard: https://grafana.internal/d/chaos-engineering
```

---

## 4. Example Integration Scenario

**Scenario:** Deploy v2.3.4 of inka-api to production

**Timeline:**

```
10:00 - Deployment request submitted
        Deployment Governor checks:
        ✅ No active chaos runs
        ✅ Chaos resilience score: 78/100 (good)
        ✅ No S1 defects
        ✅ Test coverage: 92%
        → Deployment APPROVED

10:05 - Deployment starts (blue-green)
        10% of traffic routed to v2.3.4

10:15 - Post-deploy chaos test: api_latency_injection
        Runs on staging with same code version
        - Expected latency: +500ms
        - Result: ✅ p95: 1850ms (< 2000ms threshold)
        - MTTR: 42 seconds
        - Auto-recovery: YES

10:30 - Risk Predictor evaluates:
        Base risk: 35 (from code changes)
        Chaos resilience adjustment: +2 (resilience score is high)
        Final risk: 37 → Canary approval (50%)

10:35 - 50% of traffic now on v2.3.4
        Monitoring shows:
        - Error rate: 0.8% (baseline 0.7%)
        - p95 latency: 480ms (baseline 450ms)
        - No anomalies

11:00 - Green fully healthy, 100% traffic shifted
        Deployment complete
        
        Post-deployment summary:
        ✅ Risk: LOW (37/100)
        ✅ Chaos resilience: Validated
        ✅ MTTR: < 60s (SLA met)
        ✅ Auto-recovery: 100%
```

---

## 5. Maintenance & Tuning

### 5.1 Regular Reviews

**Monthly Review Checklist:**

- [ ] Review chaos resilience trend (improving/stable/degrading?)
- [ ] Analyze any failed resilience tests
- [ ] Update abort thresholds if SLA changed
- [ ] Verify deployment blocking is working correctly
- [ ] Check Risk Predictor recommendations adoption rate

### 5.2 Threshold Tuning

**If chaos tests fail too often (> 2/month):**
- Lower abort thresholds (experiment more lenient)
- System likely not as resilient as assumed

**If all chaos tests pass easily:**
- Increase abort thresholds (experiment more aggressive)
- Better test coverage of system limits

**Example adjustment:**
```python
# In catalog.py

"high_concurrency_spike": ExperimentDefinition(
    ...
    abort_error_rate_pct=5.0,      # was 3%, more lenient
    abort_p95_latency_ms=3500,     # was 3000ms, more lenient
    ...
)
```

---

## References

- [Chaos Engineering Guide](./README.md)
- [Deployment Governor Runbook](../operations/deployment-governor.md)
- [Risk Predictor Design](../operations/risk-predictor.md)
- [Defect System](../operations/defects.md)
