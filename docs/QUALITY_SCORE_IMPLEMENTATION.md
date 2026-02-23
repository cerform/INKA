# Quality Score Agent — Complete Implementation Guide

## Overview

The Quality Score Agent is a deterministic system for evaluating release quality before deployment. It calculates a **Quality Score (0–100)** that determines whether a version is ready for:
- ✅ **Production deployment** (score ≥ 90)
- ⚠️ **Staging only** (80 ≤ score < 90)  
- 🚫 **Blocked** (score < 80)

---

## 1. Scoring Algorithm

### Formula

```
raw_score = Σ (dimension_weight × dimension_raw_score[0..100])
final_score = max(0, raw_score − Σ applied_penalties)
```

### Weighted Dimensions (100% total)

| Dimension | Weight | Measures | Formula |
|-----------|--------|----------|---------|
| **Test Coverage** | 20% | Code coverage % | Linear: `(pct-50)×2`, 0 at 50%, 100 at 100% |
| **Defect Status** | 20% | Open S1/S2 bugs | S1→0; S2 costs -25pts each; S3 costs -5pts |
| **Security Scan** | 15% | Critical/High/Med vulns | Crit -30, High -15, Med -5 per vuln, floored at 0 |
| **Migration Risk** | 10% | Database migration complexity | NONE=100, LOW=80, MEDIUM=50, HIGH=10 |
| **Code Stability** | 10% | Code churn vs previous release | 100 at ≤15% churn, decay to 0 at 60% |
| **Performance** | 10% | p95 latency + error rate | Avg of latency score + error rate score |
| **Compliance** | 15% | Compliance Agent score | Direct pass-through (0–100) |

### Dimension Scoring Examples

**Test Coverage:**
```
coverage_pct = 85  →  (85-50)*2 = 70 points (out of 100)
coverage_pct = 70  →  (70-50)*2 = 40 points
coverage_pct = 50  →  (50-50)*2 = 0 points
coverage_pct = 100 →  100 points
```

**Defect Status:**
```
0 S1, 0 S2, 0 S3  →  100 points
1 S1, 0 S2, 0 S3  →  0 points (any S1 = hard zero)
0 S1, 1 S2, 0 S3  →  75 points (100 - 25)
0 S1, 2 S2, 0 S3  →  50 points (100 - 50)
```

---

## 2. Penalty Matrix

Penalties are **subtracted from the raw weighted score**. Some penalties trigger **hard-zero rules**.

### Hard-Zero Rules (Immediate Score = 0)

| Trigger | Action |
|---------|--------|
| Any open **S1 bug** | Score immediately = 0, recommendation = BLOCK |
| **CI tests failed** | Score immediately = 0, recommendation = BLOCK |

### Cumulative Penalties (subtracted from raw score)

| Trigger | Penalty | Rule | Cap |
|---------|---------|------|-----|
| Open **S2** bug | -30 pts per bug | Cumulative | -60 total |
| **Coverage < 80%** | -20 pts | One-time | N/A |
| **Critical vuln** | -25 pts per vuln | Cumulative | -50 total |
| **High vuln** | -10 pts per vuln | Cumulative | -20 total |
| No regression test | -15 pts | One-time | N/A |
| **Code churn > 30%** | -10 pts | One-time | N/A |
| **CI lint failed** | -10 pts | One-time | N/A |

### Example: Penalty Calculation

```
Raw Score: 85.0
─────────────────────────
Penalty 1: 1 High vuln      -10.0
Penalty 2: Coverage 75%     -20.0
Penalty 3: Code churn 35%   -10.0
─────────────────────────
Total Penalties: -40.0
─────────────────────────
Final Score: 85.0 - 40.0 = 45.0  ✅ CALCULATED
```

---

## 3. Deployment Thresholds

| Score Range | Recommendation | Deployable To | Status |
|------------|---------------|---------------|--------|
| ≥ 90 | ✅ **PROD_READY** | Staging + Production | Deploy |
| 80–89 | ⚠️ **STAGE_ONLY** | Staging only | Needs approval |
| < 80 | 🚫 **BLOCK** | None | Blocked |

---

## 4. Version Quality Report

### Schema

```python
@dataclass
class QualityReport:
    version: str                           # e.g., "1.3.0"
    git_sha: str                           # Commit hash
    evaluated_at: str                      # UTC timestamp
    
    # Reflected inputs (for transparency)
    coverage_pct: float
    open_bugs: int                         # S1 count
    open_s2: int
    critical_vulns: int
    high_vulns: int
    migration_risk: str                    # "NONE" | "LOW" | "MEDIUM" | "HIGH"
    code_churn_pct: float
    p95_latency_ms: float
    compliance_score: float
    
    # Scoring breakdown
    dimension_scores: dict[str, float]     # {dimension: weighted_pts}
    penalties: list[dict[str, Any]]        # [{"reason": str, "pts": float}]
    raw_score: float                       # Before penalties
    final_score: float                     # After penalties (0–100)
    
    recommendation: str                    # "PROD_READY" | "STAGE_ONLY" | "BLOCK"
```

### Example Report

```
═══════════════════════════════════════════════════════════════
  INKA Quality Gate Report
═══════════════════════════════════════════════════════════════
  Version      : 1.3.0
  Git SHA      : a1b2c3d4e5f6g7h8
  Target       : PROD
  Gate         : 90 pts required
  Final Score  : 83.5 pts
  Recommendation: ⚠️ STAGE_ONLY
───────────────────────────────────────────────────────────────
  Dimension Scores:
    test_coverage        :  17.0 pts  (85.0% coverage)
    defect_status        :  20.0 pts  (0 S1, 0 S2)
    security_scan        :  12.0 pts  (0 crit, 1 high)
    migration_risk       :  10.0 pts  (NONE)
    code_stability       :  10.0 pts  (10% churn)
    performance          :   9.5 pts  (p95=250ms)
    compliance           :  15.0 pts  (100/100)
───────────────────────────────────────────────────────────────
  Raw Score    : 93.5
  Penalties:
    ⛔ High vuln(s): 1: -10.0
  Final Score  : 83.5
═══════════════════════════════════════════════════════════════
```

---

## 5. Telegram Commands

### `/release quality {version}`

Query quality score for a specific version.

**Input:**
```
/release quality 1.3.0
```

**Output:**
```
📊 Quality Report — v1.3.0
Git SHA: `a1b2c3d4e5`

Score: [████████░░] 83.5/100

─────────────────────────
Dimension Breakdown
  Test Coverage      :  85.0%  → 17.0pts
  Defect Status      : 0S1 / 0S2 open  → 20.0pts
  Security Scan      : 0 crit / 1 high → 12.0pts
  Migration Risk     : NONE → 10.0pts
  Code Stability     : churn 10% → 10.0pts
  Performance        : p95=250ms → 9.5pts
  Compliance         : 100 → 15.0pts
─────────────────────────
Applied Penalties
  ⛔ High vuln(s): 1: -10

Recommendation: ⚠️ STAGE_ONLY

🕐 Evaluated: 2026-02-22 06:55 UTC
```

### `/release quality latest`

Same as above but for the most recent version in the registry.

**Location in Code:**
```
apps/bot/src/bot/handlers/quality_handler.py
```

Router is registered in `apps/bot/src/main.py`:
```python
from apps.bot.handlers.quality_handler import router as quality_router
dp.include_router(quality_router)
```

---

## 6. CI Integration

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Git Push / PR                                       │
└────────────────────┬────────────────────────────────┘
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
    ┌──────┐   ┌──────────┐   ┌────────────┐
    │ Lint │   │  Tests   │   │  Security  │
    │ Job  │   │ + Cov    │   │  Scan      │
    └──────┘   └──────────┘   └────────────┘
       │             │             │
       └─────────────┼─────────────┘
                     ▼
          ┌────────────────────┐
          │ Quality Gate Job   │
          │ Compute Score      │
          └────────┬───────────┘
                   │
           ┌───────┴────────┐
        Score ≥ 80?      Score ≥ 90?
           │                │
        YES│              YES│
           ▼                ▼
      STAGE PASS       PROD PASS
           │                │
           ▼                ▼
      Deploy to         Deploy to
      Staging           Production
```

### CI Contract with Deployment Governor

#### Inputs (Environment Variables)

| Variable | Source | Required | Default |
|----------|--------|----------|---------|
| `GITHUB_SHA` / `COMMIT_SHA` | Injected by GitHub Actions / Cloud Build | ✅ | N/A |
| `VERSION` | Release tag or SHA | ✅ | `GITHUB_SHA` |
| `COVERAGE_PCT` | `coverage.xml` or pytest-cov JSON | ✅ | 0.0 |
| `OPEN_S1_BUGS` | Defect tracker API or JSON | ✅ | 0 |
| `OPEN_S2_BUGS` | Defect tracker API or JSON | ✅ | 0 |
| `CRITICAL_VULNS` | Trivy/Snyk JSON output | ✅ | 0 |
| `HIGH_VULNS` | Trivy/Snyk JSON output | ✅ | 0 |
| `MEDIUM_VULNS` | Trivy/Snyk JSON output | ⚠️ | 0 |
| `MIGRATION_RISK_LEVEL` | Release metadata (0–3) | ⚠️ | 0 |
| `CODE_CHURN_PCT` | `git diff --stat` | ⚠️ | 0.0 |
| `P95_LATENCY_MS` | Performance benchmark | ⚠️ | 0.0 |
| `ERROR_RATE_PCT` | Performance benchmark | ⚠️ | 0.0 |
| `COMPLIANCE_SCORE` | Compliance Agent | ⚠️ | 100.0 |
| `CI_TESTS_PASSED` | JUnit XML or test exit code | ✅ | true |
| `CI_LINT_PASSED` | Linter exit code | ⚠️ | true |
| `REGRESSION_TESTS_MISS` | Manual flag or analysis | ⚠️ | false |

#### Outputs (Report File)

**Exit Codes:**
- `0` : Quality gate **PASSED**, deployment allowed
- `1` : Quality gate **FAILED**, deployment blocked
- `2` : Configuration error (invalid input)

**Report File** (`quality_report.json`):
```json
{
  "version": "1.3.0",
  "git_sha": "abc123...",
  "evaluated_at": "2026-02-22 06:55 UTC",
  "coverage_pct": 85.0,
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

---

## 7. Running Quality Gate

### Locally (Development)

```bash
# Run all checks
pytest libs/ apps/ --cov=apps --cov=libs --cov-report=xml:coverage.xml

# Run security scan
trivy image scan --format json --output trivy-report.json myimage:latest

# Execute quality gate
export COVERAGE_PCT=85.0
export OPEN_S1_BUGS=0
export OPEN_S2_BUGS=0
export GITHUB_SHA=$(git rev-parse HEAD)
export VERSION=1.3.0

python scripts/quality_gate.py \
  --target stage \
  --version $VERSION \
  --output-json quality_report.json
```

### In GitHub Actions

The `.github/workflows/quality-gate.yml` workflow runs:
1. Tests + coverage
2. Security scan (Trivy)
3. Defect collection
4. Quality gate (script above)
5. Optional: Deploy if gate passed

### In Cloud Build

The `cloudbuild-quality-gate.yaml` runs the same steps in Google Cloud Build pipeline.

---

## 8. Quality Registry

The quality score system maintains a **release registry** (`quality_registry.json`) that caches all computed scores:

```json
{
  "releases": [
    {
      "version": "1.2.0",
      "git_sha": "abc123...",
      "coverage_pct": 82.0,
      "open_s1_bugs": 0,
      "open_s2_bugs": 0,
      "critical_vulns": 0,
      "high_vulns": 0,
      "medium_vulns": 2,
      "migration_risk_level": 0,
      "code_churn_pct": 8.0,
      "p95_latency_ms": 350.0,
      "error_rate_pct": 0.05,
      "compliance_score": 95.0,
      "ci_tests_passed": true,
      "ci_lint_passed": true
    },
    {
      "version": "1.3.0",
      "git_sha": "def456...",
      ...
    }
  ]
}
```

**Location:** `quality_registry.json` (root directory, can be overridden with `QUALITY_REGISTRY_PATH` env var)

---

## 9. Implementation Checklist

- ✅ Scoring algorithm (weighted dimensions + penalties)
- ✅ Quality Engine (`libs/quality/src/quality_score.py`)
- ✅ Data source (`libs/quality/src/data_source.py`)
- ✅ CI integration script (`scripts/quality_gate.py`)
- ✅ Telegram handler (`apps/bot/src/bot/handlers/quality_handler.py`)
- ✅ GitHub Actions workflow (`.github/workflows/quality-gate.yml`)
- ✅ Cloud Build configuration (`cloudbuild-quality-gate.yaml`)
- ✅ Test suite (`libs/quality/tests/test_quality_score.py`)
- ⚠️ TODO: Defect tracker API integration (Jira/Linear/etc)
- ⚠️ TODO: Compliance Agent endpoint integration
- ⚠️ TODO: Performance benchmark collection

---

## 10. Integration Points

### 1. Defect Tracker (Jira/Linear)

Replace stub in `libs/quality/src/data_source.py`:
```python
async def _fetch_from_defect_api(self, version: str) -> Optional[dict]:
    # Call your Jira API to get open S1/S2 counts
    # Return dict with open_s1_bugs, open_s2_bugs, etc.
```

### 2. Compliance Agent

Replace stub in quality engine:
```python
compliance_score = await self._fetch_from_compliance_agent(version)
```

### 3. Performance Benchmarks

Collect k6/Locust results and pass:
```python
p95_latency_ms = 250.0
error_rate_pct = 0.1
```

### 4. Git Churn Analysis

Compute code churn:
```bash
git diff --stat previous_release..current_release | tail -1
# Output: 45 files changed, 1234 insertions(+), 567 deletions(-)
# Calculate: (1234 + 567) / (total_lines) * 100 = churn_pct
```

---

## 11. Testing

Run unit tests:
```bash
pytest libs/quality/tests/ -v
```

Test cases cover:
- Hard-zero rules (S1 bugs, CI failure)
- Penalty matrix (S2, coverage, vulns, churn)
- Threshold classification (PROD_READY, STAGE_ONLY, BLOCK)
- Report field integrity

---

## 12. Troubleshooting

### Quality score always 0
- ✅ Check for open S1 bugs (`--open-s1-bugs` must be 0)
- ✅ Verify CI tests passed (`--ci-tests-passed` must be true)

### Score lower than expected
- ✅ Review penalties in report output
- ✅ Check coverage < 80% threshold
- ✅ Look for security vulnerabilities

### Telegram command not working
- ✅ Verify `quality_router` is registered in `apps/bot/src/main.py`
- ✅ Check bot token is valid
- ✅ Verify `quality_registry.json` exists

### CI integration failing
- ✅ Ensure all required env vars are set (see table above)
- ✅ Check `quality_registry.json` path
- ✅ Verify Python dependencies installed

---

## 13. Examples

### Example 1: Perfect Release

```
Version: 1.4.0
Coverage: 95%
Defects: 0 S1, 0 S2
Vulns: 0 critical, 0 high
Churn: 5%

Dimension Scores:
  test_coverage:    19.0 (95% × 20%)
  defect_status:    20.0 (0 S1/S2 × 20%)
  security_scan:    15.0 (0 vulns × 15%)
  migration_risk:   10.0 (NONE × 10%)
  code_stability:   10.0 (5% churn × 10%)
  performance:      10.0 (SLA met × 10%)
  compliance:       15.0 (100% × 15%)
  ──────────────────────
  Raw Score:        99.0

Penalties: None

Final Score: 99.0
Recommendation: ✅ PROD_READY
```

### Example 2: Problematic Release

```
Version: 1.5.0
Coverage: 72%
Defects: 0 S1, 1 S2
Vulns: 1 critical, 2 high
Churn: 35%

Dimension Scores:
  test_coverage:    4.4 (72% → (72-50)×2 = 44 × 20%)
  defect_status:    15.0 (1 S2 → 75/100 × 20%)
  security_scan:    2.0 (1 crit + 2 high → 40/100 × 15%)
  migration_risk:   10.0 (NONE × 10%)
  code_stability:   3.0 (35% churn → 30/100 × 10%)
  performance:      8.0 (p95=450ms → 80/100 × 10%)
  compliance:       13.5 (90% × 15%)
  ──────────────────────
  Raw Score:        55.9

Penalties:
  - Coverage < 80%:           -20.0
  - Critical vuln(s): 1:      -25.0
  - High vuln(s): 2:          -20.0 (capped)
  - Code churn 35% > 30%:     -10.0
  ──────────────────────
  Total Penalties:            -75.0

Final Score: max(0, 55.9 - 75.0) = 0
Recommendation: 🚫 BLOCK
```

---

## 14. Further Reading

- [INKA Architecture](../architecture/)
- [Development Setup](../development/setup.md)
- [Deployment Guide](../operations/deployment.md)
- [Compliance Agent](../compliance-agent.md)
