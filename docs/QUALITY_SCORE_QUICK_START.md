# Quick Start — Quality Score Agent

## 1. Understand the Score

**Quality Score** is a number from 0–100 that determines if a version is ready for deployment:

- ✅ **Score ≥ 90** → Production ready
- ⚠️ **80–89** → Staging only  
- 🚫 **< 80** → Deployment blocked

---

## 2. Check Your Release Score

### Using Telegram Bot

```
/release quality 1.3.0
/release quality latest
```

You'll get a formatted report with:
- Final score
- Dimension breakdown (coverage, defects, security, etc.)
- Penalties applied
- Recommendation

---

## 3. Run Quality Gate in CI

### GitHub Actions (Automatic)

When you push to `main` or `develop`:
1. Tests run with coverage collection
2. Security scan (Trivy) runs
3. Quality gate computes score
4. If score ≥ 80: staging deploy allowed
5. If score ≥ 90: production deploy allowed

### Local Testing

```bash
# Set up environment
export COVERAGE_PCT=85.0
export OPEN_S1_BUGS=0
export OPEN_S2_BUGS=0
export CRITICAL_VULNS=0
export HIGH_VULNS=0
export GITHUB_SHA=$(git rev-parse HEAD)
export VERSION=1.3.0

# Run quality gate
python scripts/quality_gate.py --target prod
```

**Output:**
```
============================================================
Quality Gate Report — 1.3.0
============================================================
Target       : PROD
Min Score    : 90
Final Score  : 83.5
Recommendation: STAGE_ONLY
Status       : 🚫 FAILED
```

---

## 4. Understand Penalties

Common reasons your score is too low:

### 1. Low Test Coverage

```
❌ Coverage 72% < 80%  → -20 points
```

**Fix:** Increase coverage with more tests
```bash
pytest --cov-report=html  # View coverage report
```

### 2. Open S1 Bug

```
❌ Any open S1 bug → Score = 0 (hard block)
```

**Fix:** Resolve all S1 (critical) bugs before release

### 3. Security Vulnerabilities

```
❌ Critical vuln(s): 1  → -25 points
❌ High vuln(s): 2      → -20 points (capped)
```

**Fix:** Patch vulnerabilities
```bash
trivy image scan myimage:latest --severity HIGH,CRITICAL
```

### 4. High Code Churn

```
❌ Code churn 35% > 30%  → -10 points
```

**Fix:** Reduce code changes in release
```bash
git diff --stat main..HEAD | tail -1
```

### 5. Open S2 Bugs

```
❌ Open S2 bug(s): 1  → -30 points each (cap -60)
```

**Fix:** Resolve major bugs

---

## 5. Improve Your Score

### Target Score: 90+

#### 1. High Test Coverage (20% weight)

```python
# Aiming for 95%+ coverage
pytest --cov=apps --cov=libs --cov-report=term-summary

# Must be > 80% (no penalty)
# 95% coverage = 19/20 points
```

#### 2. Clean Defect Status (20% weight)

```
# Must have:
#  - 0 open S1 bugs (mandatory)
#  - 0 open S2 bugs (for full score)
#  - Minimal S3 bugs

# Full score = 20/20 points
```

#### 3. Security Scan (15% weight)

```
# Zero critical vulnerabilities
# Zero high vulnerabilities
# Some medium vulns acceptable

# Full score = 15/15 points
```

#### 4. Migration Risk (10% weight)

```
# Database migrations: NONE or LOW
# High-risk migrations penalize heavily

# NONE = 10/10 points
# HIGH = 1/10 points
```

#### 5. Code Stability (10% weight)

```
# Keep code churn < 15% for full score
# Code churn = (added + deleted) / total_lines

# < 15% churn = 10/10 points
# > 30% churn = -10 points
```

#### 6. Performance (10% weight)

```
# p95 latency < 500ms (SLA)
# Error rate < 1%

# Good latency + low errors = 10/10 points
```

#### 7. Compliance (15% weight)

```
# Full compliance score from Compliance Agent
# Usually 15/15 points if no compliance issues
```

---

## 6. Workflow Example

### Pre-release Checklist

```bash
# 1. Run tests with coverage
pytest libs/ apps/ \
  --cov=apps --cov=libs \
  --cov-report=xml:coverage.xml \
  --cov-report=term-summary

# 2. Run security scan
trivy image scan --format json --output trivy-report.json myimage:latest

# 3. Check defect count (from your tracker)
#    - Must be 0 S1 bugs
#    - Ideally 0 S2 bugs

# 4. Check code churn
git diff --stat main..HEAD

# 5. Run quality gate
export COVERAGE_PCT=92.0  # From pytest
export GITHUB_SHA=$(git rev-parse HEAD)
export VERSION=1.3.0

python scripts/quality_gate.py --target prod

# 6. Check output
# If score >= 90: ✅ PROD_READY
# If score >= 80: ⚠️ STAGE_ONLY (approve for staging)
# If score < 80:  🚫 BLOCK (fix issues)
```

---

## 7. Key Decision Points

### "Can I deploy to production?"

✅ **YES** if:
- Quality score ≥ 90
- All tests pass
- Zero S1 bugs open
- No critical vulnerabilities
- Coverage > 80%

⚠️ **MAYBE** (staging only) if:
- Quality score 80–89
- Can fix issues in staging
- All S1 bugs closed

❌ **NO** (blocked) if:
- Quality score < 80
- Open S1 bugs exist
- CI tests failed
- Major security issues

---

## 8. Commands Reference

### Telegram Bot

```
/release quality 1.3.0     # Score for specific version
/release quality latest     # Score for latest version
```

### Quality Gate Script

```bash
# Full example
python scripts/quality_gate.py \
  --target prod \
  --version 1.3.0 \
  --coverage coverage.xml \
  --junit test-results.xml \
  --trivy-json trivy-report.json \
  --output quality_report.json

# Minimal (all defaults)
python scripts/quality_gate.py --target stage
```

### Check Registry

```bash
cat quality_registry.json | jq '.releases[-1]'
```

---

## 9. Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Score always 0 | Open S1 bug or CI failed | Close S1 bugs, fix test failures |
| Low coverage score | < 80% coverage | Add more tests |
| Security penalties | Vulnerabilities found | Patch deps, fix code issues |
| Churn penalties | > 30% lines changed | Break into smaller changes |
| Telegram command fails | Registry file missing | Run quality gate to create registry |
| Score stuck at 80 | S2 bugs or other issues | Check penalty breakdown in report |

---

## 10. Next Steps

1. **First Release:** Run locally, see if score ≥ 80
2. **CI Integration:** Enable GitHub Actions workflow
3. **Defect Tracker:** Connect to your Jira/Linear instance
4. **Compliance Agent:** Integrate compliance scoring
5. **Performance Monitoring:** Add benchmark collection

---

## Example Score Report

```
═══════════════════════════════════════════════════════
INKA Quality Gate Report
═══════════════════════════════════════════════════════
Version      : 1.3.0
Git SHA      : a1b2c3d4e5f6
Target       : PROD
Gate         : 90 pts required
Final Score  : 87.5 pts ← Below 90, staging only
Recommendation: ⚠️  STAGE_ONLY
───────────────────────────────────────────────────────
Dimension Scores:
  test_coverage        :  18.4 pts  (92% coverage)
  defect_status        :  20.0 pts  (0 S1, 0 S2)
  security_scan        :  13.5 pts  (0 crit, 1 high)
  migration_risk       :  10.0 pts  (NONE)
  code_stability       :  10.0 pts  (12% churn)
  performance          :   9.5 pts  (p95=300ms)
  compliance           :  15.0 pts  (100/100)
───────────────────────────────────────────────────────
Raw Score    : 96.4
Penalties:
  ⛔ High vuln(s): 1: -10.0
  ⛔ CI lint failed: -10.0
Final Score  : 87.5 ← After penalties
═══════════════════════════════════════════════════════

✅ Can deploy to: Staging
❌ Cannot deploy to: Production (need 90+)

Next Steps:
1. Fix the 1 high vulnerability
2. Fix CI lint errors
3. Target: Re-run for score > 90
```

