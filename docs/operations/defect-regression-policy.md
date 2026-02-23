# Regression Prevention Policy — INKA Admin

**Version:** 1.0  
**Last Updated:** 2026-02-22  
**Owner:** QA + Engineering  

---

## POLICY STATEMENT

**Every bug fix must include an automated regression test. No exceptions.**

**Enforcement:**
- Defect cannot transition to CLOSED without `regression_test_added = true`
- CI pipeline enforces test execution (no skips)
- Code review checklist includes regression test verification
- Metrics dashboard tracks regression coverage % (target: 95%+)

---

## REGRESSION TEST REQUIREMENTS

### 1. Test Location & Naming

**Standard Location:**
```
tests/[domain]/test_[feature]_regression.py
```

**Examples:**
```
tests/bookings/test_conflict_detection_regression.py
tests/bot/test_inline_buttons_regression.py
tests/auth/test_rbac_bypass_regression.py
```

**Naming Convention:**
```python
def test_[defect_scenario]_[expected_behavior]_regression():
    """Regression: [Defect ID] - [Title]"""
```

**Examples:**
```python
def test_double_booking_prevention_pessimistic_lock_regression():
    """Regression: DEF-12345 - Double booking allowed on 2026-02-20"""

def test_manager_rbac_view_assigned_masters_regression():
    """Regression: DEF-12346 - Manager cannot see reports for assigned masters"""

def test_rate_limit_threshold_legitimate_traffic_regression():
    """Regression: DEF-12347 - API rate limiting too aggressive"""
```

### 2. Test Structure

**FAIL → FIX → PASS Verification**

Every regression test must:

```python
def test_[scenario]_regression():
    """
    Regression Test: [Defect ID]
    Title: [Defect Title]
    
    Scenario: What is being tested?
    Expected: What should happen with fix?
    Regression: What happens without fix?
    """
    
    # ARRANGE: Setup test data
    master_id = create_test_master()
    slot_start = datetime(2026, 2, 20, 10, 0)
    slot_end = datetime(2026, 2, 20, 11, 0)
    
    # ACT: Execute the scenario
    booking1 = booking_service.create_booking(
        master_id=master_id,
        client_id="client_1",
        start_time=slot_start,
        end_time=slot_end
    )
    
    # ASSERT WITH FIX: Second booking should fail
    with pytest.raises(ConflictError):
        booking2 = booking_service.create_booking(
            master_id=master_id,
            client_id="client_2",
            start_time=slot_start,
            end_time=slot_end
        )
    
    # VERIFY: Database integrity
    conflicting_bookings = db.query(Booking).filter(
        Booking.master_id == master_id,
        Booking.start_time == slot_start
    ).all()
    assert len(conflicting_bookings) == 1, "Double booking detected!"
```

### 3. Test Type Categories

Choose appropriate test type for your defect:

#### A. Unit Tests (fastest, most common)

For code logic issues (wrong algorithm, missing check, etc.)

```python
# Test a single function/method in isolation
def test_conflict_check_returns_false_for_free_slot_regression():
    service = BookingService()
    
    # Should return False (no conflict) for free slot
    assert service.has_conflict(
        master_id=1,
        start_time=datetime(2026, 2, 20, 10, 0),
        end_time=datetime(2026, 2, 20, 11, 0),
    ) == False
```

#### B. Integration Tests (slower, for flow bugs)

For end-to-end flow issues (race conditions, state management, etc.)

```python
# Test multiple components working together
@pytest.mark.asyncio
async def test_concurrent_bookings_pessimistic_lock_regression(db: Session):
    from concurrent.futures import ThreadPoolExecutor
    
    # Run concurrent booking attempts
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(create_booking, "client_1"),
            executor.submit(create_booking, "client_2"),
        ]
        results = [f.result() for f in futures]
    
    # Exactly one should succeed
    successes = [r for r in results if isinstance(r, Booking)]
    failures = [r for r in results if isinstance(r, Exception)]
    
    assert len(successes) == 1
    assert len(failures) == 1
```

#### C. Load/Stress Tests (for performance issues)

For concurrency and performance bugs

```python
# Test under high load
@pytest.mark.slow
def test_slow_booking_filter_performance_regression(db: Session):
    master = create_test_master()
    
    # Create 5000 bookings for this master
    for i in range(5000):
        create_booking(master_id=master.id)
    
    # Filter should complete in < 1 second
    import time
    start = time.time()
    results = booking_service.filter_bookings(master_id=master.id)
    elapsed = time.time() - start
    
    assert elapsed < 1.0, f"Query took {elapsed:.2f}s, should be < 1s"
    assert len(results) == 5000
```

#### D. Security Tests (for RBAC/auth bugs)

For access control and security issues

```python
# Test permissions are enforced
@pytest.mark.asyncio
async def test_manager_cannot_access_global_reports_regression(db: Session):
    manager_user = create_test_user(role="manager")
    
    # Manager should NOT be able to access global reports (admin only)
    with pytest.raises(PermissionError):
        await report_service.get_global_analytics(user=manager_user)
    
    # But manager should access team reports
    results = await report_service.get_team_analytics(user=manager_user)
    assert results is not None
```

#### E. API/Integration Tests (for endpoint bugs)

For HTTP endpoint and API contract issues

```python
@pytest.mark.asyncio
async def test_api_rate_limit_whitelist_regression(client: TestClient):
    """Test that whitelisted IPs bypass rate limit"""
    
    # Simulate 200 requests (exceeds limit of 100/min)
    for i in range(200):
        response = client.get(
            "/api/v1/bookings",
            headers={"X-Forwarded-For": "192.168.1.1"}  # Whitelisted IP
        )
        # Should NOT be rate limited
        assert response.status_code != 429
```

### 4. Proof of Regression (Required)

Before merging PR, verify test actually catches the bug:

**Step 1: Check that test FAILS without fix**
```bash
# Temporarily revert fix
git stash

# Run regression test
pytest tests/bookings/test_conflict_detection_regression.py -v
# Expected: FAIL ❌

# Restore fix
git stash pop
```

**Step 2: Check that test PASSES with fix**
```bash
# Test now passes
pytest tests/bookings/test_conflict_detection_regression.py -v
# Expected: PASS ✅
```

**Step 3: Document in commit message**
```
Commit message:
---
Add regression test for DEF-12345

Test file: tests/bookings/test_conflict_detection_regression.py
Test name: test_double_booking_prevention_pessimistic_lock_regression

Verification:
- Test FAILS without fix (confirmed via git stash)
- Test PASSES with fix (confirms fix is effective)
- Coverage: +2.3% (18% → 20.3%)

This test prevents regression if FOR UPDATE lock is removed or 
if concurrent booking logic is refactored without proper locking.
```

### 5. Code Coverage Requirements

**Minimum Coverage:**
- New test must exercise the fixed code path (100% of fix)
- Related code coverage should increase by >= 2%
- Target: 80%+ for affected module

**Verify Coverage:**
```bash
pytest --cov=apps.api.app.domains.bookings \
       --cov-report=html \
       --cov-report=term-missing \
       tests/bookings/test_conflict_detection_regression.py

# Coverage should show:
# - 100% of conflict detection lines executed by test
# - Overall module coverage >= 80%
```

### 6. Test Metadata

Add to defect record when test is created:

```json
{
  "regression_test_file": "tests/bookings/test_conflict_detection_regression.py",
  "regression_test_name": "test_double_booking_prevention_pessimistic_lock_regression",
  "regression_test_type": "integration",
  "regression_test_coverage_increase": "2.3%",
  "regression_test_verified": true,
  "regression_test_verified_at": "2026-02-22T16:30:00Z",
  "regression_test_verification_method": "fail_without_fix_pass_with_fix"
}
```

---

## CI/CD INTEGRATION

### 1. Automatic Test Execution

Every PR must pass regression tests:

```yaml
# .github/workflows/test.yml
name: Test & Regression

on: [push, pull_request]

jobs:
  regression-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run All Regression Tests
        run: |
          pytest tests/ -k "regression" -v --tb=short
      
      - name: Fail if Regression Tests Skipped
        run: |
          # Ensure no regressions are skipped
          pytest tests/ -k "regression" --collect-only | grep "skip" && exit 1 || true
      
      - name: Coverage Report
        run: |
          pytest tests/ --cov=apps --cov=libs --cov-report=term-missing
```

### 2. Defect-Specific Test Verification

For PRs fixing defects:

```python
# .github/workflows/defect-fix.yml
- name: Verify Regression Test for Defect
  run: |
    # Extract defect ID from branch: feature/DEF-12345-fix
    DEFECT_ID=$(git rev-parse --abbrev-ref HEAD | grep -oE 'DEF-[0-9a-f-]+' || echo "")
    
    if [ -z "$DEFECT_ID" ]; then
      # Try commit message
      DEFECT_ID=$(git log -1 --pretty=%B | grep -oE 'DEF-[0-9a-f-]+' || echo "")
    fi
    
    if [ -n "$DEFECT_ID" ]; then
      echo "🔍 Checking regression test for $DEFECT_ID"
      
      # Search for test mentioning this defect
      if grep -r "Regression.*$DEFECT_ID\|$DEFECT_ID.*Regression" tests/ --include="*.py"; then
        echo "✓ Regression test found"
      else
        echo "✗ No regression test found for $DEFECT_ID"
        echo "Please add test with comment: # Regression: $DEFECT_ID"
        exit 1
      fi
    fi
```

### 3. Coverage Enforcement

```yaml
- name: Enforce Coverage
  run: |
    # Min coverage: 80% for affected modules
    pytest --cov=apps --cov=libs --cov-fail-under=80 tests/
    
    # Ensure new code has > 80% coverage
    # (Can use coverage-compare tool)
```

---

## REGRESSION TEST PATTERNS

### Pattern 1: Before/After State

```python
def test_booking_deletion_updates_master_availability_regression():
    """DEF-12348: Deleted booking doesn't free up master slot"""
    
    master = create_test_master()
    booking = create_booking(master_id=master.id, start_time=T1, end_time=T2)
    
    # BEFORE: Slot is taken
    assert has_conflict(master_id, T1, T2) == True
    
    # DELETE booking
    delete_booking(booking.id)
    
    # AFTER: Slot should be free
    assert has_conflict(master_id, T1, T2) == False  # FIX verified
    
    # Verify new booking can use slot
    new_booking = create_booking(master_id=master.id, start_time=T1, end_time=T2)
    assert new_booking is not None
```

### Pattern 2: Concurrent State

```python
@pytest.mark.asyncio
async def test_concurrent_double_booking_locked_regression():
    """DEF-12345: Double booking race condition"""
    
    async def attempt_booking(client_id: str):
        try:
            return await booking_service.create_booking(..., client_id=client_id)
        except ConflictError:
            return ConflictError()
    
    # Execute concurrent attempts
    results = await asyncio.gather(
        attempt_booking("client_1"),
        attempt_booking("client_2"),
    )
    
    # Exactly one succeeds, one fails (pessimistic lock working)
    successes = [r for r in results if isinstance(r, Booking)]
    failures = [r for r in results if isinstance(r, ConflictError)]
    
    assert len(successes) == 1
    assert len(failures) == 1
```

### Pattern 3: Permission Enforcement

```python
def test_readonly_user_cannot_modify_booking_regression():
    """DEF-12349: ReadOnly user can delete bookings"""
    
    readonly_user = create_test_user(role="read_only")
    booking = create_booking()
    
    # ReadOnly should not be able to delete
    with pytest.raises(PermissionError):
        booking_service.delete_booking(booking.id, actor=readonly_user)
    
    # But admin can
    admin_user = create_test_user(role="admin")
    result = booking_service.delete_booking(booking.id, actor=admin_user)
    assert result.deleted == True
```

### Pattern 4: Data Integrity

```python
def test_delete_master_orphaned_bookings_regression():
    """DEF-12350: Deleting master leaves orphaned bookings"""
    
    master = create_test_master()
    booking = create_booking(master_id=master.id)
    
    # Delete master
    master_service.delete_master(master.id)
    
    # Booking should be cascade-deleted or marked deleted
    deleted_booking = db.query(Booking).filter(Booking.id == booking.id).first()
    assert deleted_booking is None or deleted_booking.deleted == True
```

---

## REGRESSION TEST METRICS

Track and monitor:

```python
class RegressionMetrics:
    total_tests: int                  # Total regression tests
    tests_executed: int               # Tests run in last CI
    tests_passed: int                 # Tests passing
    tests_failed: int                 # Tests failing (regression detected!)
    tests_skipped: int                # Tests skipped (not allowed)
    
    coverage_increase: float          # % coverage increase from tests
    avg_test_duration: float          # Seconds per test
    
    defects_with_regression_tests: int  # Closed defects with tests
    regression_test_coverage: float     # % of closed defects with tests (target: 95%)
    
    regression_detected_count: int      # Tests that caught regressions
```

---

## REGRESSION PREVENTION RULES

### 1. No Skipping Tests

```python
# ❌ WRONG - Test gets skipped
@pytest.mark.skip
def test_critical_regression():
    pass

# ✅ CORRECT - Test always runs
def test_critical_regression():
    pass

# ✅ OK - Conditional skip with clear reason
@pytest.mark.skipif(not db_available, reason="Database not available")
def test_critical_regression(db: Session):
    pass
```

### 2. No Generic Tests

```python
# ❌ WRONG - Too generic, doesn't test specific fix
def test_booking_works():
    booking = create_booking()
    assert booking is not None

# ✅ CORRECT - Tests specific defect scenario
def test_double_booking_pessimistic_lock_regression():
    """DEF-12345: Prevents race condition when two users book same slot"""
    booking1 = create_booking(master_id=M, start_time=T1, end_time=T2)
    with pytest.raises(ConflictError):
        booking2 = create_booking(master_id=M, start_time=T1, end_time=T2)
```

### 3. Tests Must Be Deterministic

```python
# ❌ WRONG - Uses non-deterministic time
def test_booking_timeout_regression():
    start = time.time()
    result = slow_operation()
    elapsed = time.time() - start
    assert elapsed < 0.1  # Flaky! System load varies

# ✅ CORRECT - Uses mock/deterministic approach
@patch('time.sleep')
def test_booking_timeout_regression(mock_sleep):
    result = slow_operation()
    assert result.status == "completed"
```

### 4. Tests Must Be Independent

```python
# ❌ WRONG - Depends on previous test
class TestRegressions:
    def test_1_create_booking(self):
        self.booking = create_booking()
    
    def test_2_delete_booking(self):
        delete_booking(self.booking.id)  # Relies on test_1

# ✅ CORRECT - Each test is independent
class TestRegressions:
    def test_create_and_delete_booking(self):
        booking = create_booking()
        delete_booking(booking.id)
        # Clean up own state
```

---

## REGRESSION TEST CHECKLIST

Before marking defect "regression_test_added = true":

- [ ] Test file created in `tests/[domain]/test_*_regression.py`
- [ ] Test name includes defect ID in docstring
- [ ] Test structure: ARRANGE → ACT → ASSERT
- [ ] Test FAILS without fix (verified with `git stash`)
- [ ] Test PASSES with fix (verified after merge)
- [ ] Test is deterministic (always passes/fails consistently)
- [ ] Test is independent (can run alone)
- [ ] Test exercises 100% of fix code
- [ ] Code coverage increased by >= 2%
- [ ] Test added to CI pipeline
- [ ] No `@pytest.mark.skip` decorators
- [ ] Test has clear comment: `# Regression: DEF-XXXXX`
- [ ] Metadata added to defect record
- [ ] Code review approved
- [ ] PR/commit message references defect
- [ ] CI green (all tests pass)

---

## ENFORCEMENT & CONSEQUENCES

**What happens if regression test is missing:**

| Scenario | Action | Timeline |
|----------|--------|----------|
| Defect closed without test | Defect reverted to TESTING | Immediate |
| Test fails in CI | PR blocked until fixed | Per merge attempt |
| Test missing on main branch | Defect marked TESTING for re-fix | Next CI run |
| Coverage < 80% | PR blocked until coverage increases | Per CI run |
| Test skipped in CI | Build fails | Per build |

**SLA for Regression Tests:**

| Severity | Test Required By | Verification |
|----------|-----------------|--------------|
| S1/S2 | Before closure | Must be in PR before merge |
| S3 | Before closure | Appreciated but not blocking |
| S4 | Optional | Not required |

---

## EXAMPLES FROM PRODUCTION

### Example 1: Double Booking Regression

**Defect:** S1 Double booking allowed when two users book same slot simultaneously  
**Root Cause:** Missing pessimistic lock (FOR UPDATE)  
**Fix:** Add `SELECT FOR UPDATE` in conflict detection

**Regression Test:**
```python
# tests/bookings/test_conflict_detection_regression.py

def test_double_booking_pessimistic_lock_prevents_race_regression():
    """
    Regression: DEF-20260220-001
    Double booking allowed on 2026-02-20
    
    Fix: Add FOR UPDATE lock in conflict detection query
    """
    master = create_test_master()
    slot_start = datetime(2026, 2, 20, 10, 0)
    slot_end = datetime(2026, 2, 20, 11, 0)
    
    def concurrent_booking(client_id):
        try:
            return booking_service.create_booking(
                master_id=master.id,
                client_id=client_id,
                start_time=slot_start,
                end_time=slot_end
            )
        except ConflictError:
            return ConflictError("Conflict detected")
    
    # Concurrent requests
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(concurrent_booking, ["c1", "c2"]))
    
    # Exactly one succeeds
    bookings = [r for r in results if isinstance(r, Booking)]
    conflicts = [r for r in results if isinstance(r, ConflictError)]
    
    assert len(bookings) == 1, "Should have exactly 1 successful booking"
    assert len(conflicts) == 1, "Should have exactly 1 conflict"
    
    # No double bookings in database
    double_bookings = db.query(Booking).filter(
        Booking.master_id == master.id,
        Booking.start_time == slot_start
    ).all()
    assert len(double_bookings) == 1, "Double booking detected!"
```

**Verification:**
- Test run without fix: FAIL ✗ (double booking allowed)
- Test run with fix: PASS ✓ (pessimistic lock prevents double booking)
- Coverage increase: 2.8% (18.2% → 21%)
- CI status: GREEN

---

## FAQS

**Q: Can I mark regression_test_added=true if I just run existing tests?**
> No. You must CREATE a NEW test specifically for this defect. Existing tests didn't catch the bug, so they don't prevent regression.

**Q: What if the fix is just a documentation update (S4)?**
> S4 defects don't require regression tests. But if you fix code, always add a test.

**Q: How long should regression tests be kept?**
> Forever. Regression tests are part of permanent codebase. Remove only if codebase is refactored and test becomes redundant.

**Q: Can I use mocks instead of real database?**
> Use real database for integration tests (preferred). Mocks OK for unit tests if you're testing isolated logic.

**Q: What if the defect is in a library we didn't write?**
> Still add regression test in OUR codebase to ensure we detect if the issue reoccurs after library updates.

---

**Final Rule:** Every closed defect = one permanently added regression test in the codebase. This compounds over time and makes your system increasingly resilient.
