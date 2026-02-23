# INKA Admin — Defect Management System (DMS) — Complete Reference

**Version:** 1.0  
**Date:** 2026-02-22  
**Status:** Production-Ready  

---

## 🎯 QUICK START

### For New Defects
1. Report via `/incident report` in Telegram or `/api/v1/defects` endpoint
2. Orchestrator triages: assigns severity (S1-S4) and impact area
3. Manager assigns agents based on routing matrix
4. Agents fix, test, and update defect status
5. Defect closes only when Definition of Done criteria met

### For Urgent (S1) Defects
```
T+0min:   Telegram admin group auto-alerted
T+5min:   If no ack → PagerDuty page
T+15min:  If not started → Senior engineer escalation
T+2h:     If still fixing → War room activation
T+4h:     If not resolved → CTO escalation
```

---

## 📚 DOCUMENTATION MAP

### Core Architecture
- **[defect-orchestration.md](defect-orchestration.md)** (100 KB)
  - System overview & end-to-end workflow
  - Database schema (defect_log, defect_event)
  - API endpoints (POST/GET/PATCH /api/v1/defects)
  - Audit integration
  - Telegram commands
  - Dashboard metrics
  - CI/CD enforcement rules
  - Risk analysis

### Policy Documents
- **[defect-severity-matrix.md](defect-severity-matrix.md)** (40 KB)
  - S1 Critical → S4 Low severity definitions
  - SLA targets per severity
  - Escalation paths
  - Decision tree for classification
  - Examples per impact area
  - Override process

- **[defect-regression-policy.md](defect-regression-policy.md)** (50 KB)
  - Regression test requirements
  - Test patterns & templates
  - CI/CD integration
  - Enforcement rules
  - Metrics tracking
  - Checklist

- **[defect-agent-routing.md](defect-agent-routing.md)** (45 KB)
  - Agent types & specializations
  - Routing matrix by impact area
  - Assignment logic & decision tree
  - Expected outputs per role
  - Acceptance criteria
  - Workload tracking
  - Escalation when stalled

- **[defect-definition-of-done.md](defect-definition-of-done.md)** (40 KB)
  - Mandatory DoD criteria (all must pass)
  - Conditional criteria (if applicable)
  - Pre-closure checklist
  - Validation matrix
  - Closure denial scenarios
  - Appeals process

---

## 🔑 KEY CONCEPTS

### Severity Classification

| Level | Impact | Examples | SLA Response | SLA Resolution | Deploy Block |
|-------|--------|----------|--------------|-----------------|--------|
| **S1** 🔴 | Critical outage, data loss, security breach | Double booking, auth bypass, DB down | 15 min | 4 hours | ✅ YES |
| **S2** 🟠 | Feature broken with workaround | Slow queries, RBAC edge case, timeout | 1 hour | 24 hours | ❌ NO |
| **S3** 🟡 | UX issue, minor problem | Typo, missing icon, 100ms slower | 2 days | Sprint | ❌ NO |
| **S4** ⚪ | Cosmetic, code quality | Unused import, doc typo | Backlog | Whenever | ❌ NO |

### Impact Areas

| Area | Owner | Example Defects |
|------|-------|-----------------|
| **backend** | Backend Engineer | API code bugs, algorithm issues, data models |
| **bot** | Bot Engineer | Telegram command issues, handler failures |
| **database** | DevOps/SRE | DB resource exhaustion, query timeouts, locks |
| **security** | Security Engineer | RBAC bypass, PII exposure, auth issues |
| **devops** | DevOps/SRE | Deployment, infrastructure, scaling issues |

### Status Workflow

```
OPEN → TRIAGED → ASSIGNED → FIXING → TESTING → RESOLVED → CLOSED
                                    ↓
                              [reject at any point]
```

**Valid Transitions:**
- OPEN → TRIAGED (after severity + impact assigned)
- TRIAGED → ASSIGNED (agents assigned)
- ASSIGNED → FIXING (work begins)
- FIXING → TESTING (code review approved)
- TESTING → RESOLVED (QA sign-off)
- RESOLVED → CLOSED (DoD criteria met)
- ANY → REJECTED (invalid, not pursuing)
- REJECTED → OPEN (reverse decision)

### Definition of Done (Before CLOSED)

**Mandatory for ALL:**
- ✅ Fix merged to main (commit hash recorded)
- ✅ CI pipeline green
- ✅ Audit trail complete

**Mandatory for S1/S2:**
- ✅ Root cause analyzed & documented (>= 100 chars)
- ✅ Regression test created & passing
- ✅ QA sign-off obtained

**For Production S1/S2:**
- ✅ Monitoring stable for 24 hours
- ✅ No errors/escalations during monitoring

**Conditional:**
- ✅ Runbook updated (if incident response documented)
- ✅ Related defects also resolved (if any)

---

## 🚀 WORKFLOW EXAMPLES

### Example 1: S1 Production Backend Bug

```
[2026-02-22 14:30] DETECT
└─ Monitoring alert: Error rate spike to 45%
   → Auto-created defect: "Double booking allowed"
   → Severity: S1 (critical, production outage)
   → Impact: backend
   → Status: OPEN

[14:35] TRIAGE
├─ Manager reviews: Confirmed, all users affected
├─ Status: TRIAGED
└─ Agents assigned: Backend Engineer, QA, DevOps

[14:35] ASSIGN AGENTS
├─ Backend Engineer gets task: Fix booking logic
├─ QA gets task: Create regression test
├─ DevOps gets task: Monitor infrastructure
└─ Status: ASSIGNED

[14:45] FIX IN PROGRESS
└─ Backend Engineer:
    • Identifies: Missing pessimistic lock
    • Code fix: Add FOR UPDATE to conflict check
    • Unit tests: 2 new tests, all pass
    • Commit: a1b2c3d4
    • Status: FIXING

[15:15] CODE REVIEW
├─ 2 reviewers approve PR
├─ All CI checks green
├─ Merged to main
└─ Status: TESTING (ready for QA)

[15:30] QA TESTING
├─ QA creates regression test:
│  └─ test_pessimistic_lock_prevents_double_booking
│     • FAILS without fix ✓
│     • PASSES with fix ✓
│     • Coverage: 18.2% → 21% (+2.8%)
├─ Acceptance testing: PASS
├─ QA sign-off: Approved
└─ Status: RESOLVED

[15:45] ROOT CAUSE ANALYSIS
├─ Backend Engineer documents RCA:
│  • What: Missing pessimistic lock in SELECT
│  • Why: Not needed in single-threaded code
│  • Why-not-detected: Tests only cover single-threaded
│  • Fix: Add FOR UPDATE lock
│  • Preventive: Add load test to CI
├─ Manager reviews RCA
└─ Approved

[16:00] MONITORING & DEPLOYMENT
├─ Deploy to production
├─ Monitor error rates: Returning to normal
├─ Set 24h monitoring requirement
├─ Auto-check at 16:00 tomorrow

[Next Day 16:00] CLOSURE VALIDATION
├─ Error rates: 0.3% (baseline 0.2%, OK)
├─ No escalations during 24h
├─ DoD validation: ALL PASS ✓
├─ Manager approves closure
├─ Status: CLOSED ✓
└─ Metrics recorded: MTTR = 1.5h, SLA met ✓
```

### Example 2: S3 Frontend Typo

```
[2026-02-20] DETECT
└─ QA finds: Button says "Savee" instead of "Save"

[Create defect]
├─ Title: "Typo: 'Savee' in admin panel"
├─ Severity: S3 (cosmetic)
├─ Impact: frontend (or backend if response text)
└─ Status: OPEN

[Manager triages]
├─ Status: TRIAGED
├─ Assigned: Frontend Engineer (low priority)
└─ Added to backlog

[Next sprint]
├─ Frontend Engineer fixes typo
├─ PR created: "Fix typo in booking form"
├─ CI green
├─ Merged to main
├─ Status: TESTING

[QA verification]
├─ Button now reads "Save" ✓
├─ No regressions
├─ Status: RESOLVED

[Closure]
├─ DoD validation:
│  • No RCA needed (S3) ✓
│  • Fix merged ✓
│  • CI green ✓
│  • QA sign-off ✓
│  • (Regression test optional for S3)
├─ Status: CLOSED ✓
└─ Metrics: Time = 2 weeks (scheduled in backlog)
```

---

## 📊 METRICS & DASHBOARDS

### Primary Metrics

```
CRITICAL METRICS (Tracked Daily):
├─ Open S1 defects (prod) → Should be 0
├─ S1 SLA compliance → Target: 100%
├─ S2 SLA compliance → Target: 95%
├─ MTTR (Mean Time To Resolution)
│  ├─ S1: Target < 4h, Actual = 2.1h ✓
│  └─ S2: Target < 24h, Actual = 18.5h ✓
├─ Regression test coverage → Target: 95%+, Actual: 92%
└─ RCA completion rate (S1/S2) → Target: 100%

PROCESS METRICS (Weekly):
├─ Defects created vs closed
├─ Average defects in backlog
├─ Agent workload distribution
├─ Deployment blockers (S1 prod)
└─ Escalations

QUALITY METRICS (Monthly):
├─ Defect creation trend (increasing/stable/decreasing)
├─ Reopened defects (regressions detected)
├─ First-time fix rate
└─ Lessons learned implemented
```

### Dashboard Access

```
Cloud Monitoring Dashboard: https://console.cloud.google.com/monitoring/dashboards/custom/inka-defects
Team Dashboard (Slack): #defects-metrics
Admin Panel: /admin/defects/dashboard
```

---

## 🔔 ALERTS & ESCALATIONS

### Auto-Created Alerts

```
Trigger                          → Action
─────────────────────────────────────────────────────────
S1 + prod created               → Telegram admin group
S1 not acked in 5 min            → PagerDuty page
S1 not started in 1h             → Senior engineer page
S1 not resolved in 4h            → CTO escalation
S2 not started in 12h            → Manager notification
S1 SLA breached                  → Board notification
Open S1 blocks deployment        → CI pipeline blocks push
Regression test missing          → PR blocked
```

### Manual Escalation

In Telegram: `/incident escalate {id}`
- Requires: debugger or admin role
- Notifies: Management group
- Use for: S1/S2 not progressing

---

## 👥 TEAM RESPONSIBILITIES

### Incident Orchestrator (Manager)
- ✅ Triage defects (assign severity + impact area)
- ✅ Assign agents
- ✅ Monitor SLAs
- ✅ Approve closures
- ✅ Escalate if needed

### Backend Engineer
- ✅ Fix backend code bugs
- ✅ Write unit/integration tests
- ✅ Provide RCA for S1/S2
- ✅ Update affected services

### Bot Engineer
- ✅ Fix Telegram bot issues
- ✅ Update handlers & commands
- ✅ Handle state management bugs
- ✅ Test in production environment

### DevOps/SRE
- ✅ Fix infrastructure issues
- ✅ Scale resources if needed
- ✅ Update monitoring/alerts
- ✅ Manage disaster recovery

### QA Automation
- ✅ Create regression tests
- ✅ Acceptance testing
- ✅ Load testing (if needed)
- ✅ Sign off on quality

### Security Engineer
- ✅ Assess security vulnerabilities
- ✅ Fix RBAC/auth issues
- ✅ Verify compliance
- ✅ Audit access logs

---

## 🛠️ TOOLS & COMMANDS

### Create Defect (API)

```bash
curl -X POST https://inka-admin.app/api/v1/defects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Double booking allowed",
    "description": "Master can book overlapping slots",
    "environment": "prod",
    "severity": "S1",
    "impact_area": "backend",
    "detected_by": "qa"
  }'
```

### Create Defect (Telegram)

```
/incident report
→ Follow wizard (title, description, environment, severity)
→ Confirm submission
```

### View Defect Status

```bash
# API
curl https://inka-admin.app/api/v1/defects/550e8400-e29b-41d4-a716-446655440002

# Telegram
/incident status 550e8400-e29b-41d4-a716-446655440002
```

### Update Defect Status

```bash
curl -X PATCH https://inka-admin.app/api/v1/defects/550e8400-e29b-41d4-a716-446655440002 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "triaged",
    "assigned_agents": ["backend_engineer", "qa_automation"]
  }'
```

### View Timeline

```bash
# API
curl https://inka-admin.app/api/v1/defects/550e8400-e29b-41d4-a716-446655440002/timeline

# Telegram
/incident timeline 550e8400-e29b-41d4-a716-446655440002
```

### Check S1 Defects (CI/CD)

```bash
# Run before deployment
python scripts/check_open_s1_defects.py

# Output:
# ✓ No open S1 production defects. Deployment OK.
# OR
# ❌ Found 2 open S1 production defect(s):
#    - Double booking issue (ID: ...)
#    - Payment processing fails (ID: ...)
```

---

## 📋 CHECKLISTS

### For Bug Reporter
- [ ] Describe issue clearly
- [ ] Provide reproduction steps
- [ ] Note environment (prod/stage/dev)
- [ ] Include error messages/stack trace if available
- [ ] Estimated user impact

### For Triage Manager
- [ ] Verify severity (S1-S4)
- [ ] Confirm impact area (backend/bot/db/security/devops)
- [ ] Assign appropriate agents
- [ ] Set SLA deadline
- [ ] Add to tracking

### For Fixing Engineer
- [ ] Reproduce issue locally
- [ ] Understand root cause
- [ ] Implement fix
- [ ] Write regression test
- [ ] Pass all CI checks
- [ ] Create pull request
- [ ] Respond to review comments
- [ ] Merge to main

### For QA
- [ ] Test fix in staging
- [ ] Verify no regressions
- [ ] Confirm regression test passes
- [ ] Sign off on quality
- [ ] Document results

### For Closure
- [ ] RCA complete (S1/S2)
- [ ] Fix merged to main
- [ ] Regression test added
- [ ] CI green
- [ ] QA sign-off
- [ ] Monitoring stable (prod S1/S2)
- [ ] Runbook updated (if needed)
- [ ] All DoD criteria met
- [ ] Manager approval
- [ ] Defect closed

---

## 🎓 TRAINING & EDUCATION

### New Team Member Onboarding
1. Read: [defect-orchestration.md](defect-orchestration.md) (~20 min)
2. Read: [defect-severity-matrix.md](defect-severity-matrix.md) (~15 min)
3. Read: Role-specific document:
   - Backend: [defect-agent-routing.md](defect-agent-routing.md) (Backend Engineer section)
   - QA: [defect-regression-policy.md](defect-regression-policy.md) (whole doc)
   - Manager: [defect-definition-of-done.md](defect-definition-of-done.md) (Closure Approval section)
4. Watch: [Demo video] (link TBD)
5. Create: Test defect (practice with S4)
6. Review: With team lead

### References for Common Scenarios
- "How do I classify severity?" → [defect-severity-matrix.md](defect-severity-matrix.md) § Decision Tree
- "What should the RCA include?" → [defect-orchestration.md](defect-orchestration.md) § Root Cause Analysis
- "When can we close a defect?" → [defect-definition-of-done.md](defect-definition-of-done.md)
- "Who should fix this?" → [defect-agent-routing.md](defect-agent-routing.md) § Routing Matrix
- "Why do we need a regression test?" → [defect-regression-policy.md](defect-regression-policy.md) § Policy Statement

---

## ❓ FAQS

**Q: Can I close a defect without a regression test?**
> No. S1/S2 require regression tests. S3 appreciated but not blocking. S4 optional.

**Q: What if the fix is just a documentation update?**
> Still S4, not required for closure. But if code is fixed, must add regression test.

**Q: How long do I wait after deploying before closing?**
> S1/S2 + prod: 24 hours of stable monitoring. Others: Immediately after QA sign-off.

**Q: Who approves the RCA?**
> Manager or engineering lead reviews for completeness and accuracy.

**Q: What if an S1 defect is discovered during deploy?**
> Rollback immediately, create defect, declare SEV-1, investigate root cause.

**Q: Can I mark a defect "CLOSED" with a workaround?**
> No. CLOSED means fixed. REJECTED means "we're not fixing this" (with reason). Use REJECTED for "customers should use workaround X" scenarios.

**Q: Do we need RCA for every S2 defect?**
> Yes. S2 is high severity. Must understand why it happened to prevent recurrence.

---

## 📞 CONTACT & ESCALATION

```
For Questions:
- DMS Owner: [Manager Email]
- Slack: #defects-help
- Runbook: /docs/operations/defect-*

For S1 Defects:
- Telegram: @backend_on_call, @devops_on_call
- PagerDuty: [Link]
- War Room: [Zoom Link]

For Process Changes:
- Submit to: Engineering Lead
- Discuss in: Weekly retro
- Approve by: CTO
```

---

## 📅 SCHEDULE

```
Daily (9 AM):     Defect standup (5 min)
Weekly (Monday):  S1/S2 review + metrics
Weekly (Friday):  Process improvements retro
Monthly:          RCA deep-dive (learnings)
Quarterly:        DMS policy review & updates
```

---

## 🔒 COMPLIANCE & AUDIT

All defects are audited:
- Who created it
- All state changes (with timestamps)
- RCA documentation
- Fixes deployed (commit hashes)
- Tests added (file paths)
- Final closure (approval)

**Data Retention:** 3 years (regulatory requirement)  
**Audit Log:** Available to compliance team on request  
**GDPR:** Defects involving PII marked and handled per privacy policy  

---

**Version History:**
- v1.0 — 2026-02-22 — Initial system design (Production-Ready)

**Next Review:** 2026-05-22 (quarterly)

---

**Remember:** A well-managed defect system means fewer repeat incidents, faster learning, and safer systems. Follow the process.
