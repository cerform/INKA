# Severity Classification Matrix — INKA Admin

**Version:** 1.0  
**Last Updated:** 2026-02-22  
**Owner:** Incident & Defect Orchestrator  

---

## SEVERITY LEVELS OVERVIEW

| Severity | Impact | Users Affected | SLA Response | SLA Resolution | Deployment Block | RCA Required |
|----------|--------|----------------|--------------|-----------------|-----------------|--------------|
| **S1** | 🔴 Critical | All | 15 min | 4 hours | ✅ YES | ✅ YES |
| **S2** | 🟠 High | Subset | 1 hour | 24 hours | ❌ NO | ✅ YES |
| **S3** | 🟡 Medium | Few | 2 days | Sprint | ❌ NO | ❌ NO |
| **S4** | ⚪ Low | None | Backlog | Whenever | ❌ NO | ❌ NO |

---

## S1: CRITICAL — IMMEDIATE ESCALATION

### Definition
Production outage affecting all users, data corruption, security breach, or unauthorized system access.

### Characteristics

**All of these apply:**
- ❌ System unavailable to most users (availability < 95%)
- ❌ Core business function blocked (bookings, payments, admin operations)
- ❌ Data loss or corruption detected
- ❌ Security vulnerability exploited
- ❌ PII leak or unauthorized access
- ❌ Break-glass privileges misused
- ❌ Cascading failures in dependent systems

**Examples (MUST Classify as S1):**

```
1. "Double booking allowed on 2026-02-20"
   - Master can book overlapping slots
   - Affects all bookings for that date
   - Business impact: Scheduling chaos, customer complaints, refunds
   → S1 BACKEND DEFECT

2. "Payment processing fails for all bookings"
   - Payment API returns 500 for all requests
   - Customers cannot complete purchases
   - Revenue impact: ~$5K/hour
   → S1 BACKEND + DEVOPS

3. "Telegram bot offline / not responding"
   - Bot not responding to /book, /status, /cancel commands
   - Admins cannot manage bookings
   - SLA: 99.9% uptime violated
   → S1 BOT DEFECT

4. "Database connection pool exhausted"
   - API returns 503 Service Unavailable
   - All database queries timeout
   - Cascading failure to downstream services
   → S1 DATABASE + DEVOPS

5. "Authentication bypass discovered"
   - Unauthenticated user can access admin endpoints
   - User role bypass (readOnly → admin)
   - Can delete/modify sensitive data
   → S1 SECURITY

6. "Unencrypted PII in error logs"
   - Customer email, phone in server logs
   - Logs visible in GCP Cloud Logging
   - Compliance violation: GDPR, Israeli privacy law
   → S1 SECURITY

7. "Break-glass user modified booking prices"
   - User exceeded scope of debug session
   - Changed 100 bookings to $0 price
   - Unauthorized financial impact
   → S1 SECURITY + AUDIT

8. "All admin panel operations timeout"
   - React frontend cannot load any data
   - Managers cannot view/manage bookings
   - No admin access for > 30 min
   → S1 BACKEND
```

### SLA & Escalation

**Response Time:** 15 minutes
- T+5 min: Auto-alert Telegram admin group
- T+10 min: If no acknowledgment → PagerDuty page to on-call
- T+15 min: If not started → Senior engineer + management page

**Resolution Target:** 4 hours
- T+2h: If still fixing → Activate war room (all hands)
- T+4h: If not resolved → Escalate to CTO + board notification

**Deployment Block:** YES
- No new deployments to production until S1 is RESOLVED or REJECTED
- CI/CD pipeline blocks: `gcloud run deploy` fails if `SELECT COUNT WHERE severity='S1' AND environment='prod' AND status IN ('open', 'triaged', 'assigned', 'fixing') > 0`

### Actions

1. **Immediate (0-15 min)**
   - Create/Acknowledge defect in system
   - Page on-call engineer
   - Start documenting in Slack #incidents
   - Assess initial impact: affected users, services, data

2. **Investigation (15-60 min)**
   - Check recent deployments: git log, Cloud Run revisions
   - Review error logs: structured logs, exception traces
   - Check infrastructure: Cloud SQL, Redis, API health
   - Identify root cause hypothesis

3. **Mitigation (60-240 min)**
   - **Option A: Rollback** — Revert recent deployment
   - **Option B: Hotfix** — Deploy fix to main
   - **Option C: Workaround** — Disable problematic feature

4. **Post-Incident (24-48 hours)**
   - ✅ Complete RCA before closure
   - ✅ Add regression test to CI
   - ✅ Update runbook
   - ✅ Blameless postmortem
   - ✅ Schedule preventive actions

---

## S2: HIGH — FIX WITHIN SPRINT

### Definition
Feature malfunction, RBAC bypass, or partial service degradation affecting subset of users or non-critical flows.

### Characteristics

**One or more of these apply:**
- ⚠️ Subset of users affected (e.g., "Masters with > 1000 bookings", "Specific time zones", "Specific payment methods")
- ⚠️ Feature unavailable but alternatives exist (e.g., booking slow but can still create manually)
- ⚠️ Performance degradation > 1 second increase in P95 latency
- ⚠️ RBAC policy not enforced (wrong role sees restricted data)
- ⚠️ Data consistency issue (non-critical data stale or incorrect)
- ⚠️ Unauthorized access to non-PII data
- ⚠️ Intermittent failures (affects 5-50% of requests)
- ⚠️ API rate limiting too aggressive (legitimate traffic blocked)

**Examples (MUST Classify as S2):**

```
1. "Booking filtering slow for masters with 1000+ bookings"
   - Masters see dropdown/filter timeout after 30 seconds
   - Workaround: Use full admin panel
   - Performance issue, not unavailability
   → S2 BACKEND

2. "Manager cannot see reports for assigned masters"
   - Permission check returns "access denied"
   - Only affects manager role, not admins
   - Admins can still export reports
   → S2 BACKEND (RBAC bug)

3. "Telegram inline buttons timeout after 30 seconds"
   - User clicks button, no response
   - Can still /book via text commands
   - Affects UX but has workaround
   → S2 BOT

4. "Cache invalidation race condition"
   - Stale booking data shown sometimes
   - Refresh solves issue
   - Data eventually consistent
   → S2 BACKEND + DATABASE

5. "API rate limit threshold too aggressive"
   - Legitimate traffic from booking integrations blocked
   - Rate limit: 100 req/min, legitimate traffic: 150 req/min
   - Can temporarily whitelist IP
   → S2 DEVOPS

6. "Double booking not allowed but booking shows as pending"
   - User sees "Booking pending approval" instead of "Time slot taken"
   - Confusing but workflow still works (user gets rejection email)
   → S2 BACKEND + UX

7. "Email notifications 2-3 minutes late"
   - Transactional emails delayed
   - Customers not immediately notified
   - Non-critical but impacts UX
   → S2 BACKEND

8. "Some SVG icons missing in admin panel"
   - Visual glitch, functionality intact
   - Icons broken but buttons still work
   → S2 FRONTEND
```

### SLA & Escalation

**Response Time:** 1 hour
- T+30 min: Assigned engineer notified
- T+45 min: If no acknowledgment → Escalate in Slack #incidents
- T+1h: If not started → Assign backup engineer

**Resolution Target:** 24 hours (within sprint)
- Can be scheduled for next sprint if urgent fix unavailable
- Must be backlog priority, not ignored

**Deployment Block:** NO
- May continue deployments to production
- But S2 defect must be tracked and fixed
- If multiple S2 in same area, consider blocking

### Actions

1. **Triage (0-1 hour)**
   - Confirm issue reproduction
   - Document affected users/scenarios
   - Estimate fix complexity
   - Assign to appropriate engineer

2. **Development (1-24 hours)**
   - Code fix with test coverage
   - Pull request with regression test
   - Code review approval

3. **Testing & Deployment**
   - Deploy to staging
   - QA verification
   - Deploy to production
   - Monitor for 4 hours

4. **Closure**
   - Defect transitions to CLOSED
   - RCA documentation
   - Runbook updated if needed

---

## S3: MEDIUM — BACKLOG SCHEDULED

### Definition
UX issue, cosmetic bug, or minor performance concern with workaround available.

### Characteristics

**All apply:**
- ✓ No business function blocked
- ✓ Workaround available or behavior acceptable
- ✓ Non-critical path affected
- ✓ Cosmetic defect (typo, alignment, color, icons)
- ✓ Performance: 100-300ms latency increase
- ✓ Affects only specific user actions or scenarios
- ✓ Error messages unclear but users can proceed

**Examples (MUST Classify as S3):**

```
1. "Button label typo in admin panel"
   - "Savee" instead of "Save"
   - Functionality works perfectly
   - Cosmetic only
   → S3

2. "Booking confirmation email arrives 2 minutes late"
   - Email sent eventually (not lost)
   - Timing acceptable for non-urgent booking
   - Not transactional payment email
   → S3

3. "Telegram help menu missing recent features"
   - Help text outdated
   - Features still work via commands
   - Documentation gap
   → S3

4. "API response headers incomplete"
   - Missing some X-Custom-Headers
   - Response payload correct
   - Non-critical header
   → S3

5. "Master notes field max length too short"
   - Can't fit all notes
   - Can truncate or split across multiple bookings
   - Workaround exists
   → S3

6. "Date picker shows wrong month initially"
   - Click to correct month works
   - UX quirk, not broken
   → S3

7. "Loading spinner animation stutters"
   - UI lag, no functional issue
   - Users can still wait and proceed
   → S3

8. "Error message: 'Something went wrong'"
   - Unclear error, no error code
   - But transaction actually succeeded (idempotent)
   → S3
```

### SLA & Escalation

**Response Time:** 2 days (no urgency)
- Backlog ticket created
- Mentioned in team standup
- No page/escalation

**Resolution Target:** Next sprint or later
- Scheduled when team capacity available
- Can slip multiple sprints if higher priorities
- Not time-critical

**Deployment Block:** NO
- No deployments blocked
- Fix when time permits

### Actions

1. **Backlog Creation**
   - Create ticket with defect details
   - Add to backlog grooming
   - Set priority (P3)

2. **Scheduling**
   - Include in sprint if capacity
   - Or defer to future sprint
   - Document effort estimate

3. **Development & Testing**
   - Standard process (code review, tests)
   - No SLA pressure
   - Deploy with regular deployments

4. **Closure**
   - RCA not required
   - Regression test appreciated but optional
   - Defect closed with next regular deployment

---

## S4: LOW — COSMETIC / FUTURE

### Definition
Cosmetic defect, typo, documentation gap, or code quality issue with zero user impact.

### Characteristics

**All apply:**
- ✓ Zero user-facing impact
- ✓ Code quality / style issue
- ✓ Logging improvement
- ✓ Documentation typo or outdated example
- ✓ Build warning (not error)
- ✓ Unused code, dead imports
- ✓ Missing comments in utility functions
- ✓ Incomplete type hints

**Examples (MUST Classify as S4):**

```
1. "Unused import in utility module"
   - Import statement not used
   - Code still works
   - Linting issue
   → S4

2. "Log message grammatical error"
   - "Booking was created successful" → "was successfully created"
   - Functionality correct
   - Logging clarity
   → S4

3. "README example outdated"
   - Example command references old API version
   - New version still documented elsewhere
   - Documentation gap
   → S4

4. "Type hint incomplete"
   - Function returns `Any` instead of specific type
   - Code works, but type checking limited
   → S4

5. "Whitespace inconsistency"
   - Trailing spaces, inconsistent indentation
   - No functional issue
   - Style guide violation
   → S4

6. "Old TODO comment not cleaned up"
   - Comment references completed task
   - Can be removed
   → S4

7. "Database index missing on low-priority column"
   - Column not frequently queried
   - No performance impact
   - Technical debt
   → S4

8. "Test warning: deprecated assertion syntax"
   - Test passes, but uses old pytest syntax
   - Should modernize
   → S4
```

### SLA & Escalation

**Response Time:** None (eventually)
- No backlog priority
- Fix when team has free time
- Mention in team 1-1s

**Resolution Target:** Indefinite
- Fix whenever convenient
- Can accumulate in backlog
- No deadline

**Deployment Block:** NO
- Never blocks anything
- Nice-to-have improvement

### Actions

1. **Optional Tracking**
   - Create GitHub issue (not defect)
   - Or mention in code review
   - Or ignore if truly trivial

2. **Development (Low Priority)**
   - Fix during spare time
   - Bundle with other changes
   - No dedicated effort

3. **Closure**
   - Merged with other changes
   - No special testing
   - No RCA or regression tests needed

---

## CLASSIFICATION DECISION TREE

```
START: New defect reported

┌─────────────────────────────────────────┐
│ 1. Is system completely unavailable?    │
│    (All users, all endpoints, > 30 min) │
└─────────────────────────────────────────┘
         YES ─→ S1 CRITICAL
         NO ↓

┌─────────────────────────────────────────┐
│ 2. Is there data loss or corruption?    │
│    OR Security breach/PII leak?          │
└─────────────────────────────────────────┘
         YES ─→ S1 CRITICAL
         NO ↓

┌─────────────────────────────────────────┐
│ 3. Is feature broken for all/most users?│
│    AND no workaround exists?             │
│    AND affects core business flow?       │
└─────────────────────────────────────────┘
         YES ─→ S1 CRITICAL
         NO ↓

┌─────────────────────────────────────────┐
│ 4. Is feature broken for subset of users│
│    OR has acceptable workaround?         │
│    OR RBAC policy violated?              │
│    OR performance degraded > 1 sec?      │
└─────────────────────────────────────────┘
         YES ─→ S2 HIGH
         NO ↓

┌─────────────────────────────────────────┐
│ 5. Is it cosmetic/UX issue?             │
│    OR missing non-critical feature?      │
│    OR documentation gap?                 │
│    OR non-blocking performance issue?    │
└─────────────────────────────────────────┘
         YES ─→ S3 MEDIUM
         NO ↓

┌─────────────────────────────────────────┐
│ 6. Else: typo, code style, unused code  │
└─────────────────────────────────────────┘
         ─→ S4 LOW
```

---

## SEVERITY OVERRIDE POLICY

In exceptional cases, severity may be overridden:

| Scenario | Base Classification | Override | Reason |
|----------|-------------------|----------|--------|
| S2 issue on weekend/holiday | S2 (24h target) | S1 (4h target) | Limited on-call coverage |
| S3 blocking all new deployments | S3 | S2 | Business impact escalates |
| S4 in critical financial flow | S4 | S2 | Context changes severity |
| S1 with easy fix (< 15 min) | S1 (4h target) | S2 (24h target) | Low actual impact |

**Override Requires:**
- Manager approval
- Documented reason in defect.metadata_json
- Updated SLA in defect record
- Audit log entry: "severity_overridden"

---

## ESCALATION PATHS

### S1 Escalation (4h → 2h → now)

```
T+0h:  S1 created → Auto-alert admin Telegram group
T+30m: No owner → Escalate in Slack #incidents
T+1h:  No progress → Page on-call engineer
T+2h:  Still fixing → Activate war room (all hands)
T+3h:  Still open → Escalate to CTO
T+4h:  Still open → Board notification (revenue impact)
```

### S2 Escalation (24h → 12h → 6h)

```
T+6h:   S2 created → Assign to engineer + Slack mention
T+12h:  No progress → Reassign + manager check-in
T+18h:  Still fixing → Escalate to engineering lead
T+24h:  Not started → REJECT defect (defer to next sprint)
```

### S3 Escalation (Backlog)

```
No time-based escalation
Mentioned in backlog grooming
Scheduled when capacity available
```

---

## SEVERITY JUSTIFICATION REQUIREMENTS

### S1 Defects MUST include:
- [ ] Quantified user impact (number of affected users)
- [ ] Revenue/business impact if applicable
- [ ] Availability metric (actual uptime %)
- [ ] Evidence of cascading failures (if applicable)

### S2 Defects MUST include:
- [ ] Subset of users affected (specific scenario)
- [ ] Workaround available (if applicable)
- [ ] Impact on non-critical flows
- [ ] Estimated resolution effort

### S3 Defects MUST include:
- [ ] User-facing impact description
- [ ] Workaround or acceptable behavior
- [ ] Estimated effort to fix

### S4 Defects (minimal requirements):
- [ ] Brief description
- [ ] Category (typo/style/doc)

---

## EXAMPLES BY IMPACT AREA

### Backend Defects

| Scenario | Severity | Reason |
|----------|----------|--------|
| API returns 500 for all bookings | S1 | All users blocked |
| Booking filtering timeout (> 30s) | S2 | Subset affected, workaround exists |
| Typo in error message | S4 | Cosmetic |
| Response time increased by 500ms | S2 | Performance degradation |
| One endpoint broken (other endpoints work) | S2 | Subset of flows affected |

### Bot Defects

| Scenario | Severity | Reason |
|----------|----------|--------|
| Bot completely offline | S1 | All admin commands blocked |
| One command timeout (others work) | S2 | Subset of commands affected |
| Button text typo | S4 | Cosmetic |
| Help menu outdated | S3 | Documentation gap |
| Response time 2s (normally 100ms) | S2 | Performance issue |

### Database Defects

| Scenario | Severity | Reason |
|----------|----------|--------|
| Connection pool exhausted | S1 | All database queries blocked |
| Query timeout on secondary replica | S2 | Read-heavy operations affected, writes OK |
| Missing index on non-critical column | S4 | Technical debt, no visible impact |
| Data inconsistency (eventually corrects) | S2 | Non-immediate data issue |
| Backup missing 1 day | S1 | Data loss risk |

### Security Defects

| Scenario | Severity | Reason |
|----------|----------|--------|
| Authentication bypass | S1 | Unauthorized access |
| Role bypass (readOnly → admin) | S1 | RBAC violation |
| RBAC policy unenforced (edge case) | S2 | Specific scenario issue |
| PII in error logs | S1 | Compliance violation |
| Unused secret in codebase | S3 | Technical debt, not exposed |

---

## REVIEW & CHALLENGE PROCESS

If you disagree with assigned severity:

1. **Document disagreement** in defect.metadata_json
   ```json
   {
     "severity_challenge": {
       "reason": "I believe this is S1, not S2, because...",
       "challenger": "user_id",
       "timestamp": "2026-02-22T14:30:00Z"
     }
   }
   ```

2. **Notify manager** for review

3. **Manager decision:**
   - Confirm original severity
   - Upgrade/downgrade with reason
   - Document in audit trail

4. **Resolution:**
   - Update defect.severity
   - Create DefectEvent with type="severity_reviewed"
   - Update SLA accordingly

---

## FREQUENTLY ASKED QUESTIONS

**Q: Is this S1 or S2?**
> If > 50% of users affected AND core business flow blocked AND no workaround → S1  
> If < 50% affected OR workaround exists OR non-core flow → S2

**Q: Does this defect deserve escalation?**
> S1 = always escalate immediately  
> S2 = escalate if not progressing by 12h  
> S3 = backlog, no escalation  
> S4 = ignore unless high priority

**Q: Can I change severity after defect created?**
> Yes, with manager approval. Document in audit trail. Update SLA targets.

**Q: What if the impact is unclear?**
> Default to higher severity (safer).  
> S3 → S2 if business impact unclear  
> S2 → S1 if system availability at risk

---

## FINAL DECISION AUTHORITY

| Severity | Authority |
|----------|-----------|
| S1 ↔ S2 | Manager or Senior Engineer |
| S2 ↔ S3 | Team Lead |
| S3 ↔ S4 | Any Engineer |

All severity changes must be audited.
