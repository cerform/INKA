# Agent Routing & Assignment Matrix — INKA Admin

**Version:** 1.0  
**Last Updated:** 2026-02-22  
**Owner:** Engineering Manager  

---

## AGENT ASSIGNMENT OVERVIEW

When a defect is triaged, it is automatically routed to specialized agents based on **impact_area** and **severity**.

### Agent Types

| Role | Specialization | Typical Defects | Notification |
|------|---|---|---|
| **Backend Engineer** | API, business logic, data models | Code bugs, algorithm issues, database query problems | Slack + assigned task |
| **Bot Engineer** | Telegram bot, handlers, commands | Command timeouts, message formatting, state issues | Slack + assigned task |
| **QA Automation** | Test creation, regression testing, load testing | Test coverage, missing regression tests | Slack + assigned task |
| **DevOps/SRE** | Infrastructure, scaling, monitoring, deployment | Database resource exhaustion, memory leaks, rate limiting | PagerDuty page |
| **Security Engineer** | Access control, encryption, compliance | RBAC bypass, PII exposure, authentication issues | Security Slack + page |

---

## ROUTING MATRIX

### By Impact Area

```
Impact Area     → Primary Agent(s)          → Secondary              → Urgency
────────────────────────────────────────────────────────────────────────────
backend         → Backend Engineer          → QA, DevOps            → S1: 4h
                                                                     → S2: 24h

bot             → Bot Engineer              → QA, Backend           → S1: 2h
                                                                     → S2: 8h

database        → DevOps/SRE                → Backend Engineer      → S1: 1h
                                                                     → S2: 4h

security        → Security Engineer         → DevOps, Backend       → S1: 1h
                                                                     → S2: 2h

devops          → DevOps/SRE                → Backend, Security     → S1: 30min
                                                                     → S2: 1h
```

### By Severity

```
Severity    → Additional Assignments
────────────────────────────────────────────────
S1 + prod   → Always add QA Automation for verification
            → Always add secondary reviewer

S1 + sec    → Escalate to CISO/Security Lead
            → Notify compliance team

S2 + db     → Add database expert (if available)
            → Monitor for cascading issues
```

---

## AUTOMATIC ASSIGNMENT LOGIC

### Decision Tree

```python
def assign_agents(defect: Defect) -> List[AgentRole]:
    """
    Automatically determine agents based on impact_area + severity.
    Returns list of agent roles to assign.
    """
    agents = []
    
    # 1. PRIMARY: Impact area determines main agent
    if defect.impact_area == ImpactArea.BACKEND:
        agents.append(AgentRole.BACKEND_ENGINEER)
        agents.append(AgentRole.QA_AUTOMATION)
    
    elif defect.impact_area == ImpactArea.BOT:
        agents.append(AgentRole.BOT_ENGINEER)
        agents.append(AgentRole.QA_AUTOMATION)
    
    elif defect.impact_area == ImpactArea.DATABASE:
        agents.append(AgentRole.DEVOPS_SRE)
        agents.append(AgentRole.BACKEND_ENGINEER)
    
    elif defect.impact_area == ImpactArea.SECURITY:
        agents.append(AgentRole.SECURITY_ENGINEER)
        agents.append(AgentRole.DEVOPS_SRE)
        agents.append(AgentRole.BACKEND_ENGINEER)
    
    elif defect.impact_area == ImpactArea.DEVOPS:
        agents.append(AgentRole.DEVOPS_SRE)
        agents.append(AgentRole.BACKEND_ENGINEER)
    
    # 2. SEVERITY: S1 gets extra verification
    if defect.severity == DefectSeverity.S1:
        if AgentRole.QA_AUTOMATION not in agents:
            agents.append(AgentRole.QA_AUTOMATION)
    
    # 3. DEDUPLICATION
    return list(set(agents))
```

### Example Assignments

```
Defect: "Double booking allowed on 2026-02-20"
├─ severity: S1 (critical)
├─ impact_area: backend
├─ environment: prod
└─ Assigned Agents:
   ├─ Backend Engineer (primary for backend)
   ├─ QA Automation (verification for S1 + backend)
   └─ DevOps/SRE (standby if infra issue found)

Defect: "Telegram bot offline"
├─ severity: S1
├─ impact_area: bot
├─ environment: prod
└─ Assigned Agents:
   ├─ Bot Engineer (primary for bot)
   ├─ QA Automation (verification)
   └─ Backend Engineer (if API integration issue)

Defect: "Manager cannot see reports"
├─ severity: S2
├─ impact_area: backend
├─ environment: prod
└─ Assigned Agents:
   ├─ Backend Engineer (primary)
   └─ QA Automation (regression testing)

Defect: "Authentication bypass discovered"
├─ severity: S1
├─ impact_area: security
├─ environment: prod
└─ Assigned Agents:
   ├─ Security Engineer (primary)
   ├─ DevOps/SRE (incident response)
   └─ Backend Engineer (code fixes)
```

---

## AGENT TASK DEFINITION

When defect is assigned, a task is generated for each agent:

### Task Structure

```python
{
    "defect_id": "550e8400-e29b-41d4-a716-446655440002",
    "defect_title": "Double booking allowed on 2026-02-20",
    "severity": "S1",
    "impact_area": "backend",
    
    "agent_role": "backend_engineer",
    "assigned_by": "manager_id",
    "assigned_at": "2026-02-22T14:30:00Z",
    
    "deadline_hours": 4,
    "deadline_absolute": "2026-02-22T18:30:00Z",
    
    "expected_output": [
        "Root cause analysis (for S1/S2)",
        "Code fix with PR",
        "Regression test added",
        "All CI checks green"
    ],
    
    "acceptance_criteria": [
        "Code compiles",
        "Unit tests pass",
        "Integration tests pass",
        "Coverage >= 80%",
        "Code review approved",
        "PR merged to main",
        "Deployed to staging"
    ],
    
    "priority": 1,  # 1 = highest
}
```

---

## EXPECTED OUTPUTS BY ROLE

### Backend Engineer

**For S1/S2 Defects:**

```
✓ INVESTIGATE (2 hours)
  • Root cause analysis
  • Stack trace examination
  • Database query analysis
  • Identify all affected code paths

✓ IMPLEMENT FIX (1-2 hours)
  • Code changes with detailed comments
  • Unit tests (>= 2 new tests)
  • Edge case handling
  • Backward compatibility check

✓ TESTING (1 hour)
  • Local testing (reproduce issue)
  • Run full test suite
  • Coverage report (target: >= 80%)
  • Load/stress testing if applicable

✓ CODE REVIEW (30 min)
  • Create pull request with:
    - Defect ID in PR title
    - Detailed description of fix
    - Before/after comparison
    - Regression test proof (fail → pass)
  • Address review comments

✓ DEPLOYMENT (30 min)
  • Deploy to staging
  • Run staging smoke tests
  • Deploy to production
  • Monitor error rates for 4 hours

✓ DOCUMENTATION (30 min)
  • Update defect status
  • Add fix_commit_sha
  • Document any config changes
  • Update runbook if needed
```

**For S3 Defects:**

```
✓ IMPLEMENT & DEPLOY (same as above, but relaxed timeline)
✓ NO RCA REQUIRED
✓ REGRESSION TEST APPRECIATED BUT NOT MANDATORY
```

### Bot Engineer

**For S1/S2 Telegram Bot Defects:**

```
✓ INVESTIGATE (1 hour)
  • Check bot logs in GCP Logging
  • Verify bot is running (Cloud Run)
  • Confirm handler registered
  • Test command manually

✓ IMPLEMENT FIX (1 hour)
  • Update handler code
  • Add/fix state management
  • Update message formatting
  • Add inline keyboard if needed

✓ UNIT TESTS (30 min)
  • Handler tests (aiogram test client)
  • State transition tests
  • Message format tests

✓ CODE REVIEW & MERGE (30 min)
  • Create PR, address review
  • Merge to main

✓ DEPLOYMENT (30 min)
  • Redeploy bot container
  • Verify /start, /help commands work
  • Test command in production

✓ DOCUMENTATION (20 min)
  • Update defect status
  • Document command changes
```

### QA Automation

**For All Defects (Primary Task: Regression Testing):**

```
✓ CREATE REGRESSION TEST (2 hours)
  • Write test in appropriate suite
  • Verify test FAILS without fix
  • Verify test PASSES with fix
  • Document in metadata
  • Add to CI pipeline

✓ COVERAGE ANALYSIS (30 min)
  • Run coverage report
  • Ensure >80% for affected code
  • Highlight uncovered edge cases

✓ LOAD TESTING (1 hour for S1)
  • Stress test if performance-related
  • Run k6/JMeter if applicable
  • Verify SLAs met

✓ ACCEPTANCE TESTING (1 hour)
  • Test fix against acceptance criteria
  • Verify no regressions in related features
  • Sign off on quality

✓ METRICS & REPORTING (30 min)
  • Update regression test metrics
  • Document results
  • Highlight any risks
```

### DevOps/SRE

**For Infrastructure & Database Defects:**

```
✓ INVESTIGATE (1 hour)
  • Check Cloud Run metrics
  • Review Cloud SQL status
  • Check Cloud Monitoring dashboards
  • Analyze error logs

✓ IMPLEMENT MITIGATION (1-2 hours)
  • Scale resources if needed
  • Update configuration
  • Restart services if needed
  • Update monitoring alerts

✓ MONITORING (4-24 hours)
  • Watch metrics for stability
  • Set up alerting thresholds
  • Document SLA impact

✓ RUNBOOK UPDATE (30 min)
  • Document incident response steps
  • Add troubleshooting section
  • Create playbook if needed

✓ PREVENTION (ongoing)
  • Plan long-term fix
  • Coordinate with backend/database teams
  • Schedule for next sprint
```

### Security Engineer

**For Security/RBAC Defects:**

```
✓ VULNERABILITY ASSESSMENT (2 hours)
  • Confirm vulnerability
  • Assess impact (what data exposed?)
  • Document proof of concept
  • Estimate blast radius

✓ CONTAINMENT (1 hour, if needed)
  • Disable vulnerable endpoint
  • Reset compromised credentials
  • Revoke suspicious tokens
  • Audit access logs

✓ FIX & REMEDIATION (2-4 hours)
  • Code fix (RBAC enforcement, input validation, etc.)
  • Cryptography review if applicable
  • Security test creation

✓ INCIDENT REVIEW (2 hours)
  • How was vulnerability introduced?
  • Why wasn't it caught in code review?
  • Update security checklist

✓ COMPLIANCE VERIFICATION (1 hour)
  • Verify fix meets compliance requirements
  • Document for audit trail
  • Notify compliance team if PII affected
```

---

## ACCEPTANCE CRITERIA BY ROLE

### Backend Engineer Acceptance

```
PR/Commit Ready for Merge:
 ✅ All unit tests pass
 ✅ All integration tests pass
 ✅ Code coverage >= 80%
 ✅ Linters pass (ruff, mypy)
 ✅ No new security warnings
 ✅ Code review approved (2 reviewers for S1)
 ✅ Regression test created and passing
 ✅ Commit message references defect ID
 ✅ No merge conflicts

Ready for Staging Deployment:
 ✅ Merged to main
 ✅ CI green on main
 ✅ Staging smoke tests pass

Ready for Production Deployment:
 ✅ Staging validation complete
 ✅ Monitoring configured
 ✅ Runbook updated (if needed)
 ✅ RCA complete (for S1/S2)
```

### Bot Engineer Acceptance

```
PR Ready for Merge:
 ✅ Handler tests pass
 ✅ State machine tests pass
 ✅ Manual testing in staging
 ✅ Code review approved
 ✅ No bot crashes observed

Bot Ready for Production:
 ✅ Redeployed to Cloud Run
 ✅ Verified responding to /start, /help
 ✅ Verified command under test works
 ✅ No bot errors in logs (5 min check)
```

### QA Automation Acceptance

```
Regression Test Complete:
 ✅ Test file created
 ✅ Test name descriptive
 ✅ Test FAILS without fix (verified)
 ✅ Test PASSES with fix (verified)
 ✅ Test runs in CI pipeline
 ✅ Coverage >= 80%
 ✅ No flaky tests

Acceptance Testing:
 ✅ Defect scenario reproduced (before fix)
 ✅ Defect cannot reproduce (after fix)
 ✅ No related features broken
 ✅ Sign-off given
```

### DevOps/SRE Acceptance

```
Infrastructure Fix:
 ✅ Issue reproduced
 ✅ Resources scaled / config updated
 ✅ Metrics show improvement
 ✅ Alerts configured
 ✅ SLA met for 24h+ (prod S1/S2)

Runbook:
 ✅ Troubleshooting steps documented
 ✅ Alert interpretation guide added
 ✅ Escalation path clear
```

### Security Engineer Acceptance

```
Vulnerability Fixed:
 ✅ PoC no longer works
 ✅ RBAC enforcement verified
 ✅ Audit logs show fix active
 ✅ Security test added
 ✅ Compliance review complete (if PII affected)
```

---

## WORKLOAD DISTRIBUTION

### Agent Workload Tracking

```
Backend Engineer:
  • S1 defects: Max 1 at a time
  • S2 defects: Max 3 at a time
  • S3 defects: Max 5 at a time

Bot Engineer:
  • S1 defects: Max 1 at a time
  • S2 defects: Max 2 at a time

DevOps/SRE:
  • S1 defects: Max 1 at a time (on-call)
  • S2 defects: Max 2 at a time

QA Automation:
  • Defects in testing phase: All (not limited)
  • Focus on highest severity first
```

### Load Balancing

If agent is at max workload:

1. **Assign to backup agent** (secondary from matrix)
2. **Increase deadline** (if approved by manager)
3. **Escalate to team lead** (if blocking critical path)
4. **Hire temporary support** (if persistent overload)

---

## ESCALATION WHEN ASSIGNMENT STALLS

```
T+0h:   Defect assigned to agent
        ├─ Agent acknowledged
        └─ Task created in task tracking

T+2h:   Check-in
        ├─ Is agent making progress?
        ├─ If S1: No progress → Check for blockers
        └─ If S2: No progress → Continue monitoring

T+4h (S1) / T+12h (S2):  Escalation 1
        ├─ Agent not started?
        ├─ → Assign to backup agent
        ├─ → Manager notifies agent why
        └─ → Increase visibility in standup

T+6h (S1) / T+18h (S2):  Escalation 2
        ├─ Still stalled?
        ├─ → Team lead takes ownership
        ├─ → Hold 1:1 with agent
        └─ → Identify blockers (knowledge gap? Resource issue?)

T+8h (S1) / T+24h (S2):  Escalation 3
        ├─ Not resolved?
        ├─ → Engineering manager review
        ├─ → Consider all-hands support
        └─ → If still stalled → CTO involvement
```

---

## SPECIAL CASES

### Case 1: Unknown Impact Area

If impact_area cannot be determined:

```
→ Assign: "Investigation Agent" (senior backend engineer)
→ Task: "Determine impact area and route to appropriate team"
→ Deadline: 2 hours

After investigation:
→ Re-assign to primary agent based on finding
→ Update defect.impact_area
```

### Case 2: Cross-Functional Defect

If defect spans multiple impact areas:

```
Example: Payment processing fails (backend issue) because Cloud SQL 
is out of disk space (infrastructure issue)

→ Primary assignment: DevOps/SRE (critical path)
→ Secondary assignment: Backend Engineer (payment logic review)
→ Task: Coordinate together

Priority: Fix infrastructure first, then verify backend
```

### Case 3: Agent on Leave

If assigned agent is unavailable:

```
→ Check backup assignment (secondary role)
→ If backup unavailable: Escalate to team lead
→ Re-assign to next available agent in role
→ Update stakeholders
```

### Case 4: Skill Mismatch

If agent lacks expertise:

```
Example: Database performance tuning (DevOps assigned) but team has 
dedicated DBA

→ Consult DBA (secondary reviewer)
→ If defect really needs DBA: Re-assign
→ Use as learning opportunity for primary agent
```

---

## HANDOFF PROTOCOL

When transitioning defect between agents:

### From Triage to Assignment

```
Triage Manager → Assigned Agent

Documents to prepare:
✓ Defect record with full context
✓ Reproduction steps
✓ Links to monitoring/logs
✓ Previous attempts (if any)
✓ Known blockers
✓ Escalation contact

Communication:
✓ Slack message to agent
✓ Link to defect ticket
✓ Expected deadline
✓ Any critical info
```

### From Investigation to Implementation

```
Investigation Agent → Implementation Agent

If investigation reveals new information:
✓ Update defect.description
✓ Update defect.impact_area (if changed)
✓ Document findings in metadata_json
✓ Re-assign if impact area changed
✓ Notify new agent of findings
```

### From Implementation to QA Testing

```
Backend/Bot/DevOps Agent → QA Agent

When code is ready for testing:
✓ PR merged to main
✓ Deployed to staging
✓ Notify QA to begin acceptance testing
✓ Provide test scenarios
✓ Flag any critical test paths
```

### From QA to Closure

```
QA Agent → Defect Orchestrator

When testing complete:
✓ QA sign-off documented
✓ Regression test added
✓ Coverage metrics recorded
✓ Defect transitions to RESOLVED
✓ Monitor for 24h before CLOSED
```

---

## METRICS TO TRACK

```python
class AgentMetrics:
    # Assignment metrics
    assignments_per_agent: dict           # How many defects assigned
    avg_assignments_per_severity: dict    # S1, S2, S3, S4 distribution
    
    # Performance metrics
    mttr_per_agent: dict                  # Mean time to resolution
    mtta_per_agent: dict                  # Mean time to acknowledgment
    avg_time_in_each_status: dict         # How long in assigned/fixing/testing
    
    # Quality metrics
    first_time_fix_rate: dict             # % of defects fixed on first attempt
    regression_reopen_count: dict         # Defects reopened after closure
    
    # Workload metrics
    concurrent_assignments: dict          # Max concurrent defects per agent
    assignments_at_deadline: dict         # % meeting deadline
    
    # Skill metrics
    expertise_coverage: dict              # Which agents have which skills
```

---

## DEFINITION OF AGENT DONE

Agent can declare task COMPLETE only if:

```
✅ Defect assigned action(s) completed
✅ All acceptance criteria met
✅ Code/infrastructure changes deployed
✅ Defect status updated appropriately
✅ Documentation updated
✅ Handoff to next agent (if applicable)
✅ Task marked complete in tracking system
```

This ensures clear accountability and status visibility across the entire incident response lifecycle.
