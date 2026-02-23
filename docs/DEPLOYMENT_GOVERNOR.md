# Deployment Governor — Quality Score Integration

> **Contract between Quality Score Agent and Deployment Governor**

The Quality Score system serves as a **deployment gate** that prevents low-quality versions from reaching production.

---

## 1. Integration Overview

### Actors

| Actor | Role | Responsibilities |
|-------|------|------------------|
| **Quality Score Agent** | Evaluator | Compute score, generate report, recommend action |
| **CI Pipeline** | Orchestrator | Run tests, security scans, trigger quality gate |
| **Deployment Governor** | Gatekeeper | Check score, decide deployment eligibility |
| **Release Manager** | Approver | Authorize staging/prod deploys |

### Flow

```
┌──────────────────────┐
│ Code Push / PR       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ CI Pipeline (GitHub Actions / Cloud Build)   │
│ ────────────────────────────────────────────  │
│ 1. Lint                                      │
│ 2. Unit + Integration Tests                  │
│ 3. Security Scan (Trivy)                     │
│ 4. Collect Metrics                           │
│ 5. Quality Gate (compute score)              │
└──────────┬───────────────────────────────────┘
           │
    ┌──────┴────────┐
    │               │
   YES            NO
    │               │
    ▼               ▼
┌─────────────┐  ┌──────────┐
│ Score Pass? │  │FAIL/BLOCK│
│ >= 80?      │  │ Notify   │
└────┬────────┘  └──────────┘
     │
  ┌──┴──┐
  │     │
 YES   NO
  │     │
  ▼     ▼
┌──────────────────┐
│ Check Threshold  │
├──────────────────┤
│ >= 90? PROD OK   │
│ >= 80? STAGING OK│
└────┬─────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Deployment Governor              │
│ ────────────────────────────────  │
│ 1. Read quality_report.json      │
│ 2. Check recommendation          │
│ 3. Verify target (stage/prod)    │
│ 4. Approve/Deny deployment       │
└──────────┬───────────────────────┘
           │
     ┌─────┴──────┐
     │            │
  APPROVED      DENIED
     │            │
     ▼            ▼
  DEPLOY       FAIL PIPELINE
```

---

## 2. Contract Specification

### 2.1 Input Contract (CI to Quality Score Agent)

The CI pipeline must provide these **environment variables** before invoking quality gate:

```python
QualityInput(
    version: str                          # e.g., "1.3.0" or git SHA
    git_sha: str                          # Commit hash
    coverage_pct: float                   # From pytest-cov XML
    open_s1_bugs: int                     # From defect tracker
    open_s2_bugs: int                     # From defect tracker
    open_s3_bugs: int = 0
    regression_tests_missing: bool = False
    critical_vulns: int = 0               # From Trivy/Snyk
    high_vulns: int = 0
    medium_vulns: int = 0
    migration_risk_level: int = 0         # 0=NONE, 1=LOW, 2=MEDIUM, 3=HIGH
    code_churn_pct: float = 0.0           # From git diff --stat
    p95_latency_ms: float = 0.0           # From performance benchmarks
    p99_latency_ms: float = 0.0
    error_rate_pct: float = 0.0           # % of 5xx errors
    compliance_score: float = 100.0       # From Compliance Agent
    ci_lint_passed: bool = True           # Lint exit code
    ci_tests_passed: bool = True          # Test exit code
)
```

### 2.2 Output Contract (Quality Score Agent to Deployment Governor)

The Quality Score Agent produces `quality_report.json`:

```json
{
  "version": "1.3.0",
  "git_sha": "abc123...",
  "evaluated_at": "2026-02-22 06:55 UTC",
  
  "coverage_pct": 92.0,
  "open_bugs": 0,
  "open_s2": 0,
  "critical_vulns": 0,
  "high_vulns": 1,
  "migration_risk": "NONE",
  "code_churn_pct": 10.0,
  "p95_latency_ms": 250.0,
  "compliance_score": 100.0,
  
  "dimension_scores": {
    "test_coverage": 17.0,
    "defect_status": 20.0,
    "security_scan": 12.0,
    "migration_risk": 10.0,
    "code_stability": 10.0,
    "performance": 9.5,
    "compliance": 15.0
  },
  
  "penalties": [
    {"reason": "High vuln(s): 1", "pts": 10.0}
  ],
  
  "raw_score": 93.5,
  "final_score": 83.5,
  "recommendation": "STAGE_ONLY"
}
```

### 2.3 Exit Code Contract

The quality gate script exits with:

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| `0` | Quality gate **PASSED** | Proceed with deployment (if score sufficient) |
| `1` | Quality gate **FAILED** | Block deployment |
| `2` | Configuration error | Check inputs and retry |

**Note:** Exit code 0 doesn't guarantee deployment — Deployment Governor checks threshold:
- Exit 0 + score < 80: Block (invalid config)
- Exit 0 + 80 ≤ score < 90: Staging only
- Exit 0 + score ≥ 90: Production OK

### 2.4 Recommendation Contract

The `recommendation` field guides Deployment Governor:

| Recommendation | Meaning | Allowed Targets |
|---|---|---|
| `PROD_READY` | Score ≥ 90 | Staging + Production |
| `STAGE_ONLY` | 80 ≤ Score < 90 | Staging only |
| `BLOCK` | Score < 80 | None (deployment blocked) |

---

## 3. Deployment Governor Implementation

### 3.1 Pseudo-Code

```python
async def should_deploy(
    target: str,  # "stage" or "prod"
    report_path: str,  # "quality_report.json"
) -> bool:
    """Determine if deployment should proceed."""
    
    # Load report
    with open(report_path) as f:
        report = json.load(f)
    
    # Check hard rules
    if report["recommendation"] == "BLOCK":
        logger.info("Deployment BLOCKED by quality gate")
        return False
    
    if target == "prod":
        if report["final_score"] < 90:
            logger.info(f"Production blocked: score {report['final_score']} < 90")
            return False
    
    elif target == "stage":
        if report["final_score"] < 80:
            logger.info(f"Staging blocked: score {report['final_score']} < 80")
            return False
    
    # All checks passed
    logger.info(f"✅ {target.upper()} deployment APPROVED")
    return True
```

### 3.2 Example: GitHub Actions Implementation

```yaml
- name: Check Quality Gate
  id: quality_check
  run: |
    python scripts/quality_gate.py --target ${{ env.DEPLOYMENT_TARGET }}
    EXIT_CODE=$?
    
    # Parse report
    SCORE=$(jq '.final_score' quality_report.json)
    RECOMMENDATION=$(jq -r '.recommendation' quality_report.json)
    
    if [[ $EXIT_CODE -ne 0 ]]; then
      echo "❌ Quality gate failed"
      exit 1
    fi
    
    if [[ "${{ env.DEPLOYMENT_TARGET }}" == "prod" && $SCORE -lt 90 ]]; then
      echo "❌ Cannot deploy to PROD: score $SCORE < 90"
      exit 1
    fi
    
    echo "✅ Quality gate passed: $RECOMMENDATION"
    exit 0
```

### 3.3 Example: Cloud Build Implementation

```yaml
# quality-gate step
- name: 'gcr.io/cloud-builders/docker'
  id: quality-gate
  script: |
    #!/bin/bash
    set -e
    
    python scripts/quality_gate.py \
      --target ${_DEPLOYMENT_TARGET} \
      --version ${SHORT_SHA}
    
    # Extract score
    SCORE=$(jq '.final_score' quality_report.json)
    RECOMMENDATION=$(jq -r '.recommendation' quality_report.json)
    
    echo "Quality Score: $SCORE"
    echo "Recommendation: $RECOMMENDATION"
    
    # Block if needed
    if [[ "${_DEPLOYMENT_TARGET}" == "prod" && $(echo "$SCORE < 90" | bc) -eq 1 ]]; then
      echo "❌ Production deployment blocked: score < 90"
      exit 1
    fi

# deploy step (only runs if quality-gate succeeds)
- name: 'gcr.io/cloud-builders/gke-deploy'
  id: deploy
  args: [...]
  waitFor: ['quality-gate']  # Depends on quality gate
```

---

## 4. Operational Procedures

### 4.1 Normal Path: Score ≥ 90 (PROD_READY)

```
1. Code merged to main
2. CI pipeline runs (tests, scans, quality gate)
3. Quality score: 91.5
4. Recommendation: PROD_READY
5. Deployment Governor: ✅ APPROVED
6. Deploy to production automatically
7. Monitor in Datadog/GCP
```

### 4.2 Conditional Path: 80 ≤ Score < 90 (STAGE_ONLY)

```
1. Code merged to develop
2. CI pipeline runs
3. Quality score: 84.2
4. Recommendation: STAGE_ONLY
5. Deployment Governor: Deploy to staging only
6. Release Manager: Reviews in staging (1-2 days)
7. If stable, backport to main for retry
8. Retry quality gate on main (should improve score)
9. If score ≥ 90 after fixes: Deploy to prod
```

### 4.3 Blocked Path: Score < 80 (BLOCK)

```
1. Code merged to develop
2. CI pipeline runs
3. Quality score: 65.3
4. Recommendation: BLOCK
5. Deployment Governor: ❌ DEPLOYMENT BLOCKED
6. Notify team on Slack
7. Release Manager: Reviews failures
   - Low coverage? Add tests
   - Open S2 bugs? Fix them
   - Vulnerabilities? Patch deps
8. Push fix to develop
9. Rerun CI/quality gate
10. If score ≥ 80: Retry
```

---

## 5. Monitoring & Observability

### 5.1 Metrics to Track

```
# Quality gate metrics
quality_gate_execution_time_seconds    # How long does scoring take?
quality_gate_pass_rate                 # % of releases that pass
quality_gate_score_by_dimension        # Score trends
quality_gate_penalties_applied         # Most common issues
deployment_blocked_count               # How often we block bad releases
deployment_staging_only_count          # How often we gate to staging

# Example Prometheus
quality_score_total{version="1.3.0",recommendation="PROD_READY"} 91.5
```

### 5.2 Logging

Every quality gate execution should log:

```python
logger.info(
    "quality_gate_executed",
    extra={
        "version": "1.3.0",
        "git_sha": "abc123...",
        "score": 91.5,
        "recommendation": "PROD_READY",
        "target": "prod",
        "duration_ms": 1234,
        "penalties_count": 0,
        "decision": "APPROVED",
    },
)
```

### 5.3 Alerts

Set up alerts for:

1. **Too many blocks** (quality gates failing)
   - Alert: > 3 blocks in 24 hours
   - Action: Review team's code quality processes

2. **Low average scores**
   - Alert: Average score < 85 over week
   - Action: Invest in test coverage, reduce code churn

3. **Slow quality gate**
   - Alert: Scoring takes > 30 seconds
   - Action: Optimize data source queries

---

## 6. Integration Checklist

- [ ] CI pipeline collects all required metrics
- [ ] Quality gate script configured in CI
- [ ] `quality_report.json` produced and persisted
- [ ] Deployment Governor checks report before deploy
- [ ] Exit codes properly handled
- [ ] Slack/Teams notifications on gate failures
- [ ] Quality registry (quality_registry.json) maintained
- [ ] Telegram bot `/release quality` command works
- [ ] Monitoring dashboards show score trends
- [ ] Runbook documented for debugging

---

## 7. Troubleshooting Guide

### Deployment blocked, but score looks good?

**Check:**
1. Is score actually < 80? (might be rounding display issue)
2. Is there an open S1 bug? (hard zero)
3. Did CI tests pass? (hard zero if not)
4. Are all required metrics provided?

**Fix:**
```bash
cat quality_report.json | jq '.final_score, .recommendation, .penalties'
```

### Quality gate slow in CI?

**Check:**
1. Are defect API calls slow?
2. Are artifact downloads slow?
3. Large coverage.xml file?

**Fix:**
- Cache quality registry locally
- Use async API calls
- Parallelize metric collection

### Recommendation wrong for deployment target?

**Check:**
1. Is `_DEPLOYMENT_TARGET` set correctly in CI?
2. Is Deployment Governor checking threshold?

**Fix:**
```bash
# CI should pass --target to quality_gate.py
python scripts/quality_gate.py --target prod  # Not "stage"
```

---

## 8. References

- [Quality Score Agent Implementation](QUALITY_SCORE_IMPLEMENTATION.md)
- [Quality Score Quick Start](QUALITY_SCORE_QUICK_START.md)
- [CI Integration Configs](../cloudbuild-quality-gate.yaml)
