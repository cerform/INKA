# Definition of Done (DoD) — Defect Closure — INKA Admin

**Version:** 1.0  
**Last Updated:** 2026-02-22  
**Owner:** Engineering Manager  

---

## EXECUTIVE SUMMARY

**A defect may transition from RESOLVED → CLOSED only if ALL mandatory criteria are met.**

**Responsibility:**
- **Defect Author (Orchestrator):** Validates all criteria
- **QA:** Signs off on testing
- **Backend/Bot/DevOps:** Implements fix and confirms deployment
- **Manager:** Approves closure

**Non-Compliance:** Defect reverted to TESTING/FIXING with reason documented.

---

## MANDATORY CRITERIA (All Required)

### 1. Root Cause Documented (S1/S2 Only)

**Requirement:**
```
✅ defect.root_cause field populated
✅ Length >= 100 characters
✅ Contains 5 key elements:
   1. What failed
   2. Why it failed
   3. Why it was not detected earlier
   4. Corrective action taken
   5. Preventive action planned
```

**Example (GOOD):**
```
"Double booking occurred because the conflict detection query 
did not use FOR UPDATE pessimistic lock. In high-concurrency 
scenarios (> 10 req/sec), two requests both read 'no conflict' 
before either INSERT completed, resulting in duplicate bookings. 
Was not caught earlier due to unit tests covering only single-threaded 
scenarios. Fixed by adding FOR UPDATE lock to SELECT. Preventive: 
add load tests to CI pipeline to catch concurrency issues."
```

**Example (BAD):**
```
"Fixed the double booking issue."
```

**Verification:**
```python
def validate_rca(defect: Defect) -> bool:
    if defect.severity not in [S1, S2]:
        return True  # Not required for S3/S4
    
    if not defect.root_cause:
        return False  # Missing
    
    if len(defect.root_cause.strip()) < 100:
        return False  # Too short
    
    # Check DefectEvent timeline has rca_completed event
    rca_events = db.query(DefectEvent).filter(
        DefectEvent.defect_id == defect.id,
        DefectEvent.event_type == "rca_completed"
    ).all()
    
    return len(rca_events) > 0
```

### 2. Fix Merged to Main

**Requirement:**
```
✅ defect.fix_commit_sha populated (40-char git hash)
✅ Commit exists in main branch
✅ Commit message references defect ID
✅ All CI checks GREEN
✅ Code review approved (2+ for S1, 1+ for S2/S3)
```

**Commit Message Format:**
```
[DEF-12345] Fix double booking race condition

- Add FOR UPDATE lock to conflict detection query
- Add regression test: test_pessimistic_lock_prevents_double_booking
- Coverage: 18.2% → 21% (+2.8%)

Fixes: DEF-12345
Reviewed-by: @backend_engineer @qa_automation
```

**Verification:**
```python
def validate_fix_merged(defect: Defect) -> bool:
    if not defect.fix_commit_sha:
        return False  # Missing commit
    
    # Verify commit exists in main
    try:
        commit = subprocess.run(
            f"git log main --oneline | grep {defect.fix_commit_sha}",
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False  # Commit not in main
```

### 3. Regression Test Added

**Requirement:**
```
✅ defect.regression_test_added = true
✅ Test file exists: tests/[domain]/test_*_regression.py
✅ Test name descriptive: test_[scenario]_regression()
✅ Test location in metadata: regression_test_file, regression_test_name
✅ Test FAILS without fix (verified)
✅ Test PASSES with fix (verified)
✅ Test integrated into CI pipeline
✅ Coverage increased >= 2%
```

**Verification:**
```python
def validate_regression_test(defect: Defect) -> bool:
    if not defect.regression_test_added:
        return False  # Not marked as added
    
    # Check metadata
    metadata = defect.metadata_json or {}
    test_file = metadata.get("regression_test_file")
    test_name = metadata.get("regression_test_name")
    
    if not test_file or not test_name:
        return False  # Missing location info
    
    # Verify test file exists
    import os
    if not os.path.exists(f"/repo/{test_file}"):
        return False  # File doesn't exist
    
    # Check test name in file
    with open(f"/repo/{test_file}") as f:
        if f"def {test_name}" not in f.read():
            return False  # Test not found
    
    # Verify coverage increase
    coverage_increase = metadata.get("regression_test_coverage_increase", 0)
    return coverage_increase >= 2.0
```

**Acceptable Reasons for Missing Test (S3/S4 Only):**
```
❌ S1/S2 with no test → Defect BLOCKED
✅ S3 with no test → Acceptable (but not ideal)
✅ S4 with no test → Expected
```

### 4. CI Pipeline Green

**Requirement:**
```
✅ All unit tests PASS
✅ All integration tests PASS
✅ Linters PASS (ruff)
✅ Type checks PASS (mypy)
✅ Code coverage >= 80% (for affected module)
✅ No new security warnings (bandit)
✅ No deprecation warnings
✅ Build artifacts generated successfully
```

**Verification - Automated in CI:**
```yaml
# .github/workflows/ci.yml
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Unit Tests
        run: pytest tests/ -v --tb=short
      
      - name: Linting
        run: ruff check . --select E,F,I,N,UP,S,B,A,C4,DTZ,T20,PT,RET,SIM,ARG,PTH,ERA,PL,RUF
      
      - name: Type Checking
        run: mypy . --strict
      
      - name: Coverage
        run: |
          pytest --cov=apps --cov=libs --cov-report=term-missing --cov-fail-under=80
      
      - name: Security
        run: bandit -r apps libs --fail-under=7
      
      - name: Build Check
        run: python -m build
```

**If Any Check Fails:**
```
❌ Defect cannot close
→ Fix must be updated
→ Re-run CI
→ Merge only when GREEN
```

### 5. QA Sign-Off

**Requirement:**
```
✅ QA has tested fix in staging environment
✅ All acceptance criteria verified
✅ No regressions detected in related features
✅ Test scenarios match product requirements
✅ Defect scenario cannot be reproduced with fix
✅ QA sign-off documented in DefectEvent
```

**QA Sign-Off Event:**
```python
DefectEvent(
    defect_id="...",
    event_type="qa_sign_off",
    actor_id="qa_engineer_id",
    payload={
        "test_scenarios_run": [
            "Create booking for master with 1000+ existing bookings",
            "Concurrent booking attempts (100+ concurrent)",
            "Booking cancellation and re-booking",
        ],
        "result": "PASS",
        "defect_reproduced_with_fix": False,
        "regressions_detected": False,
        "coverage_increase": "2.8%",
        "approval": True,
        "signed_by": "qa_engineer_id"
    }
)
```

**Verification:**
```python
def validate_qa_sign_off(defect: Defect) -> bool:
    qa_events = db.query(DefectEvent).filter(
        DefectEvent.defect_id == defect.id,
        DefectEvent.event_type == "qa_sign_off"
    ).all()
    
    if not qa_events:
        return False  # No QA sign-off found
    
    latest_qa_event = qa_events[-1]
    return latest_qa_event.payload.get("approval") == True
```

### 6. Audit Trail Complete

**Requirement:**
```
✅ DefectEvent timeline shows complete flow:
   • defect_created
   • [status transitions: open → triaged → assigned → fixing → testing → resolved]
   • agents_assigned
   • fix_merged
   • regression_test_added
   • rca_completed (for S1/S2)
   • qa_sign_off
   • monitoring_stable (for prod S1/S2)

✅ All state transitions audited in audit_log table
✅ No missing events
✅ Timeline is coherent (no backwards time travel)
```

**Verification:**
```python
def validate_audit_trail(defect: Defect) -> bool:
    events = db.query(DefectEvent).filter(
        DefectEvent.defect_id == defect.id
    ).order_by(DefectEvent.created_at).all()
    
    required_event_types = [
        "defect_created",
        "agents_assigned",
        "fix_merged",
        "regression_test_added",
        "qa_sign_off",
    ]
    
    if defect.severity in [S1, S2]:
        required_event_types.append("rca_completed")
    
    if defect.environment == "prod" and defect.severity in [S1, S2]:
        required_event_types.append("monitoring_stable")
    
    found_types = [e.event_type for e in events]
    return all(rt in found_types for rt in required_event_types)
```

---

## CONDITIONAL CRITERIA (If Applicable)

### 7. Production Monitoring Stable (S1/S2 + Prod Only)

**Requirement:**
```
✅ Defect must be in RESOLVED status for >= 24 hours
✅ Error rates stable (< baseline + 5%)
✅ Latency stable (< baseline + 100ms)
✅ No escalations or re-opens during period
✅ Monitoring dashboard green

Examples:
  • S1 Backend → 24h stable monitoring
  • S1 Bot → 24h stable, bot responding normally
  • S1 Database → 24h stable, queries < 100ms
```

**Automated Monitoring:**

```python
def validate_production_stability(defect: Defect) -> bool:
    if not (defect.environment == "prod" and defect.severity in [S1, S2]):
        return True  # Not applicable
    
    if not defect.resolved_at:
        return False  # Must be RESOLVED first
    
    hours_since_resolved = (datetime.now(tz) - defect.resolved_at).total_seconds() / 3600
    if hours_since_resolved < 24:
        return False  # Not 24h yet
    
    # Check monitoring metrics for this time period
    metrics = query_cloud_monitoring(
        start_time=defect.resolved_at,
        end_time=defect.resolved_at + timedelta(hours=24),
        filters={"defect_id": str(defect.id)}
    )
    
    # Verify no spikes
    error_rate_increase = (metrics.error_rate_max - metrics.baseline) / metrics.baseline
    if error_rate_increase > 0.05:  # > 5%
        return False
    
    # Verify no re-opens
    reopens = db.query(DefectEvent).filter(
        DefectEvent.defect_id == defect.id,
        DefectEvent.event_type.contains("reopened"),
        DefectEvent.created_at > defect.resolved_at
    ).count()
    
    return reopens == 0
```

### 8. Runbook Updated (If Applicable)

**Requirement:**
```
IF incident response was documented:
   ✅ Runbook section created or updated
   ✅ Troubleshooting steps documented
   ✅ Alert interpretation guide added
   ✅ Escalation path clear
   ✅ Team has reviewed runbook

IF new operational procedure discovered:
   ✅ Runbook includes new procedure
   ✅ Examples provided
   ✅ Owner assigned for maintenance

IF disaster recovery affected:
   ✅ Recovery procedure updated
   ✅ Recovery time objective (RTO) documented
   ✅ Tested with team
```

**Example Runbook Addition:**

```markdown
## Incident: Double Booking Race Condition

### Detection
- Alert: Booking table has (master_id, date, start_time) duplicates
- Check: SELECT COUNT(*) FROM booking GROUP BY master_id, date, 
        start_time HAVING COUNT(*) > 1

### Root Cause
- Missing pessimistic lock in conflict detection
- Concurrent requests both read "no conflict" before INSERT
- Race condition in async FastAPI with multiple workers

### Immediate Actions
1. Check error rate in Cloud Monitoring
2. If error rate > 10%, begin investigation
3. Query DB: count of duplicate bookings
4. If duplicates detected, run data cleanup script

### Remediation
1. Deploy commit a1b2c3d4 (adds FOR UPDATE lock)
2. Run regression test: test_pessimistic_lock_prevents_double_booking
3. Monitor error rate for 24h
4. Close defect only after 24h stable

### Prevention
- Load test all time-slot operations before merge
- Use pessimistic locks for all critical concurrent operations
- Review async concurrency in code review
```

### 9. Related Incidents Resolved

**Requirement:**
```
IF defect.related_incidents is not empty:
   ✅ All related defects also RESOLVED/CLOSED
   OR explicitly marked as independent
   
IF defect is child of larger incident:
   ✅ Parent incident also RESOLVED
   OR child can close independently
```

**Verification:**
```python
def validate_related_incidents(defect: Defect) -> bool:
    related_ids = defect.related_incidents or []
    if not related_ids:
        return True  # No related incidents
    
    for related_id in related_ids:
        related_defect = db.query(Defect).filter(
            Defect.id == UUID(related_id)
        ).first()
        
        if not related_defect:
            return False  # Related defect doesn't exist
        
        if related_defect.status not in [RESOLVED, CLOSED]:
            return False  # Related defect not resolved
    
    return True
```

### 10. Break-Glass Session Audit (If Applicable)

**Requirement:**
```
IF break-glass session was involved in detecting/triaging defect:
   ✅ Session logs reviewed for scope compliance
   ✅ Any unauthorized actions documented
   ✅ Session appropriately closed
   ✅ RCA includes why break-glass was needed
   ✅ Preventive action: improve monitoring to avoid need
```

**Verification:**
```python
def validate_break_glass_audit(defect: Defect) -> bool:
    metadata = defect.metadata_json or {}
    if "break_glass_session_id" not in metadata:
        return True  # Not applicable
    
    session_id = metadata["break_glass_session_id"]
    session = db.query(DebugSession).filter(
        DebugSession.id == session_id
    ).first()
    
    if not session:
        return False  # Session not found
    
    # Check for audit review
    audit_events = db.query(AuditLog).filter(
        AuditLog.entity_id == session_id,
        AuditLog.action.contains("reviewed")
    ).all()
    
    return len(audit_events) > 0
```

---

## DEFINITION OF DONE VALIDATION MATRIX

### S1 Defects - ALL Criteria Required

| Criterion | Required | Optional | Notes |
|-----------|----------|----------|-------|
| Root Cause | ✅ YES | - | Mandatory |
| Fix Merged | ✅ YES | - | Mandatory |
| Regression Test | ✅ YES | - | Mandatory |
| CI Green | ✅ YES | - | Mandatory |
| QA Sign-off | ✅ YES | - | Mandatory |
| Audit Trail | ✅ YES | - | Mandatory |
| Prod Monitoring 24h | ✅ YES (prod only) | - | Mandatory for prod |
| Runbook Updated | ⚠️ CONDITIONAL | - | If response documented |
| Related Defects | ✅ YES | - | Mandatory |
| Break-Glass Audit | ⚠️ CONDITIONAL | - | If session involved |

### S2 Defects - MOST Criteria Required

| Criterion | Required | Optional | Notes |
|-----------|----------|----------|-------|
| Root Cause | ✅ YES | - | Mandatory |
| Fix Merged | ✅ YES | - | Mandatory |
| Regression Test | ✅ YES | - | Mandatory |
| CI Green | ✅ YES | - | Mandatory |
| QA Sign-off | ✅ YES | - | Mandatory |
| Audit Trail | ✅ YES | - | Mandatory |
| Prod Monitoring 24h | ✅ YES (prod only) | - | For prod, 24h stable |
| Runbook Updated | ⚠️ CONDITIONAL | - | If response documented |
| Related Defects | ✅ YES | - | Mandatory |

### S3 Defects - Core Criteria Required

| Criterion | Required | Optional | Notes |
|-----------|----------|----------|-------|
| Root Cause | ❌ NO | ✅ | Not required for S3 |
| Fix Merged | ✅ YES | - | Mandatory |
| Regression Test | ❌ OPTIONAL | ✅ | Appreciated but not blocking |
| CI Green | ✅ YES | - | Mandatory |
| QA Sign-off | ✅ YES | - | Mandatory |
| Audit Trail | ✅ YES | - | Minimal audit required |
| Prod Monitoring | ❌ NO | - | Not required |
| Runbook Updated | ❌ NO | ✅ | Optional |
| Related Defects | ✅ YES | - | If any |

### S4 Defects - Minimal Criteria

| Criterion | Required | Optional | Notes |
|-----------|----------|----------|-------|
| Root Cause | ❌ NO | - | Not required |
| Fix Merged | ✅ YES | - | Mandatory |
| Regression Test | ❌ NO | ✅ | Not required |
| CI Green | ✅ YES | - | Mandatory |
| QA Sign-off | ❌ OPTIONAL | ✅ | May self-verify |
| Audit Trail | ✅ YES | - | Minimal |
| Prod Monitoring | ❌ NO | - | Not required |
| Runbook Updated | ❌ NO | - | Not required |
| Related Defects | ✅ YES | - | If any |

---

## PRE-CLOSURE CHECKLIST

Use this before attempting to transition defect to CLOSED:

```
□ MANDATORY CRITERIA
  □ Root Cause (S1/S2)
    □ defect.root_cause populated
    □ Length >= 100 characters
    □ Contains what/why/why-not
    □ RCA event in timeline

  □ Fix Merged
    □ defect.fix_commit_sha populated
    □ Commit in main branch
    □ Commit message references defect
    □ All CI checks GREEN

  □ Regression Test
    □ defect.regression_test_added = true
    □ Test file exists
    □ Test FAILS without fix (verified)
    □ Test PASSES with fix (verified)
    □ In CI pipeline
    □ Coverage >= 80% for module
    □ Metadata has test location

  □ CI Green
    □ All unit tests PASS
    □ All integration tests PASS
    □ Linting PASS
    □ Type checking PASS
    □ Coverage >= 80%
    □ No security warnings

  □ QA Sign-Off
    □ QA tested in staging
    □ Acceptance criteria verified
    □ No regressions detected
    □ QA event in timeline
    □ Approval = true

  □ Audit Trail
    □ Complete timeline in DefectEvents
    □ All transitions logged
    □ Coherent chronology

□ CONDITIONAL CRITERIA (If Applicable)
  □ Production Monitoring (S1/S2 + prod)
    □ 24h since RESOLVED
    □ Error rates stable
    □ Latency stable
    □ Monitoring event in timeline

  □ Runbook (If incident response)
    □ Runbook section updated
    □ Troubleshooting added
    □ Team reviewed

  □ Related Incidents
    □ All related defects RESOLVED/CLOSED
    □ OR marked independent

  □ Break-Glass Audit (If applicable)
    □ Session logs reviewed
    □ Scope compliance verified
    □ Audit event in timeline

□ FINAL VALIDATION
  □ Defect orchestrator reviews all criteria
  □ Manager approves closure
  □ Defect status transitions to CLOSED
  □ Closure event created in timeline
  □ Metrics updated
```

---

## CLOSURE DENIAL SCENARIOS

If DoD validation fails, defect is **NOT CLOSED**. Instead:

### Scenario 1: Missing RCA (S1/S2)

```
Status: RESOLVED → reverts to TESTING

Reason: "Root cause missing or < 100 chars"

Action Required:
- Engineer provides detailed RCA
- Manager reviews
- Retry closure validation
```

### Scenario 2: Regression Test Not Added

```
Status: RESOLVED → reverts to TESTING

Reason: "Regression test file not found or test doesn't exist"

Action Required:
- Create regression test
- Verify test FAILS without fix
- Verify test PASSES with fix
- Merge test to main
- Retry closure validation
```

### Scenario 3: CI Not Green

```
Status: RESOLVED → remains in TESTING

Reason: "3 unit tests failing, coverage 73% < 80%"

Action Required:
- Fix failing tests
- Add more test coverage
- Re-run CI until all green
- Retry closure validation
```

### Scenario 4: Monitoring Not Stable (Prod S1/S2)

```
Status: RESOLVED → blocked from CLOSED

Reason: "Only 18h of stable monitoring, need 24h. Error rate: 2.1% vs baseline 0.5%"

Action Required:
- Wait 6 more hours
- Monitor error rates
- Investigate spike (if any)
- Confirm stable after 24h
- Retry closure validation
```

### Scenario 5: Related Incident Still Open

```
Status: RESOLVED → reverts to TESTING

Reason: "Related defect DEF-12346 still in FIXING status"

Action Required:
- Wait for related defect to also reach RESOLVED
- OR mark as independent (with justification)
- Retry closure validation
```

---

## CLOSURE APPROVAL WORKFLOW

```
Engineer: "Defect ready for closure"
  ↓
Orchestrator: Validates all DoD criteria
  ├─ All criteria met?
  │  ├─ YES → Approve closure
  │  └─ NO → Specify which criteria failed
  ↓
Manager: Spot-checks critical criteria
  ├─ RCA quality (S1/S2)
  ├─ Test coverage
  ├─ Monitoring (prod)
  └─ Approves or requests changes
  ↓
Defect: Status → CLOSED
  ├─ DefectEvent("defect_closed") created
  ├─ Audit log entry: "defect.closed"
  └─ Metrics updated
```

---

## METRICS AFTER CLOSURE

Once defect is CLOSED, calculate:

```python
metrics = {
    "severity": defect.severity,
    "time_to_resolution": (defect.resolved_at - defect.detected_at).total_seconds() / 3600,
    "sla_met": defect.resolved_at <= defect.sla_deadline,
    "rca_completed": defect.root_cause is not None,
    "regression_test_added": defect.regression_test_added,
    "agents_assigned": defect.assigned_agents,
    "changes_required": count_of_dod_violations,  # 0 = clean closure
    "time_to_closure": (datetime.now() - defect.created_at).total_seconds() / 3600,
}

# Update dashboard metrics
dashboard.mttr[defect.severity] += metrics["time_to_resolution"]
dashboard.sla_compliance[defect.severity] += 1 if metrics["sla_met"] else 0
dashboard.regression_coverage += 1 if metrics["regression_test_added"] else 0
```

---

## APPEALS PROCESS

If you believe defect meets DoD despite validation failure:

1. **Document exception reason** (in defect.metadata_json)
   ```json
   {
     "dod_exception_reason": "Regression test requires 2h infrastructure setup. Time-boxed exception for S3 defect. Test will be added in next sprint.",
     "dod_exception_approved_by": "manager_id",
     "dod_exception_date": "2026-02-22T15:00:00Z"
   }
   ```

2. **Manager reviews** and approves (or denies) exception

3. **Document in timeline**
   ```python
   DefectEvent(
       event_type="dod_exception_granted",
       payload={"reason": "...", "approved_by": "..."}
   )
   ```

4. **Proceed with closure** (if approved)

**Exception limits:**
- S1 defects: NO exceptions
- S2 defects: Max 1 criterion exception (with manager approval)
- S3 defects: Max 2 criterion exceptions (no RCA, no test)
- S4 defects: All criteria except merge can be waived

---

## FINAL WORDS

> **A defect is not truly "fixed" until it cannot happen again.**
> 
> The Definition of Done ensures:
> - Root causes are understood
> - Fixes are comprehensive
> - Regressions are prevented
> - Lessons are learned
> - Team knowledge is codified
> 
> Cutting corners on DoD leads to repeated incidents and wasted effort.
> 
> **Do it right the first time.**
