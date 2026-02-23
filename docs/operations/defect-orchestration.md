# INKA Admin — Defect & Incident Orchestration System

**Version:** 1.0  
**Last Updated:** 2026-02-22  
**Author:** Incident & Defect Orchestrator  
**Status:** Production-Ready  

---

## TABLE OF CONTENTS

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Severity Classification](#severity-classification)
6. [Root Cause Analysis](#root-cause-analysis)
7. [Agent Routing](#agent-routing)
8. [Regression Prevention](#regression-prevention)
9. [Telegram Incident Commands](#telegram-incident-commands)
10. [Dashboard & Metrics](#dashboard--metrics)
11. [CI/CD Enforcement](#cicd-enforcement)
12. [Definition of Done](#definition-of-done)
13. [Risk Analysis](#risk-analysis)
14. [Runbooks](#runbooks)

---

## SYSTEM OVERVIEW

### Mission
The Defect & Incident Orchestration System (DIOS) coordinates the full lifecycle of defect management:

1. **Intake** — Collect bugs, incidents, errors from all sources (monitoring, users, QA, break-glass)
2. **Normalization** — Convert into structured defect records with context
3. **Classification** — Assign severity, impact area, and routing
4. **Assignment** — Route to specialized agents based on impact area
5. **Analysis** — Mandatory RCA for S1/S2 defects
6. **Fix & Test** — Coordinate fixes and QA validation
7. **Regression** — Enforce test creation before closure
8. **Closure** — Only when all DoD criteria met
9. **Audit** — Full audit trail for all state changes

### Key Principles

- **No defect left behind** — All issues tracked, no ad-hoc fixes
- **Traceability** — Every defect linked to request_id, audit logs, commits
- **SLA-driven** — Severity determines response deadline
- **Automation-first** — Monitoring feeds defects automatically
- **RCA mandatory** — No S1/S2 closed without documented root cause
- **Regression prevention** — Every fix gets a test
- **Production safety** — S1 defects block deployments

---

## ARCHITECTURE

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        INCIDENT SOURCES                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │  Monitoring  │  │   QA Tests   │  │  Break-Glass │  │ User Report  ││
│  │   Alerts     │  │   Failures   │  │   Sessions   │  │   (Telegram) ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
                     ┌────────────────────────────┐
                     │ Incident Auto-Logger       │
                     │ (Normalize → Defect Record)│
                     └────────────────────────────┘
                                  ↓
            ┌─────────────────────────────────────────────────┐
            │         DEFECT INTAKE & CLASSIFICATION           │
            │  - Severity Assignment (S1-S4)                  │
            │  - Impact Area Detection (bot/backend/db/sec)   │
            │  - Audit Log Creation                            │
            └─────────────────────────────────────────────────┘
                                  ↓
              ┌──────────────────────────────────────────┐
              │      AGENT ROUTING & ASSIGNMENT           │
              │  (Based on Impact Area & Severity)       │
              │  - Backend Engineer → backend defects    │
              │  - Bot Engineer → telegram bot defects   │
              │  - Security Engineer → security defects  │
              │  - DevOps → infra defects                │
              └──────────────────────────────────────────┘
                                  ↓
            ┌─────────────────────────────────────────────────┐
            │         FIX & TEST PHASE                         │
            │  - Agent implements fix                          │
            │  - Regression test added (mandatory)             │
            │  - CI pipeline validates                         │
            │  - QA automation run                             │
            └─────────────────────────────────────────────────┘
                                  ↓
              ┌──────────────────────────────────────────┐
              │    ROOT CAUSE ANALYSIS (S1/S2 only)       │
              │  - Timeline reconstruction                │
              │  - What/Why/Why-not analysis              │
              │  - Preventive actions                     │
              └──────────────────────────────────────────┘
                                  ↓
                ┌────────────────────────────────┐
                │ CLOSURE VALIDATION              │
                │ - RCA complete (S1/S2)          │
                │ - Regression test added         │
                │ - CI green                      │
                │ - Monitoring stable 24h (prod)  │
                │ - Runbook updated if needed     │
                └────────────────────────────────┘
                                  ↓
                      ┌──────────────────┐
                      │  DEFECT CLOSED   │
                      │  & AUDIT LOGGED  │
                      └──────────────────┘
```

### System Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Defect Log Table** | Primary defect storage | PostgreSQL, JSONB |
| **Defect Event Table** | Audit trail (every state change) | PostgreSQL, JSONB |
| **API Endpoints** | CRUD + timeline + filtering | FastAPI |
| **Telegram Bot** | Incident intake & status | aiogram 3.3+ |
| **Audit Service** | Integration with global audit log | Existing audit_service |
| **Agent Routing Logic** | Assignment based on impact area | Service layer logic |
| **RCA Service** | Mandatory for S1/S2 | Custom service |
| **CI/CD Hooks** | Enforce regression tests | GitHub Actions |
| **Monitoring** | Auto-create S1 defects on outages | GCP Cloud Monitoring |
| **Dashboard** | Metrics & SLA tracking | Cloud Monitoring / custom |

---

## DATABASE SCHEMA

### Defect Log Table (existing, verified)

```sql
CREATE TABLE defect_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core fields
    title VARCHAR NOT NULL,
    description TEXT,
    environment VARCHAR NOT NULL,  -- dev, stage, prod
    severity VARCHAR NOT NULL,      -- S1, S2, S3, S4
    impact_area VARCHAR NOT NULL,   -- bot, backend, db, security, devops
    detected_by VARCHAR NOT NULL,   -- user, qa, monitoring
    
    -- Traceability
    request_id UUID UNIQUE INDEX,    -- Links to HTTP request
    correlation_id UUID INDEX,       -- Links related incidents
    actor_id UUID NOT NULL FOREIGN KEY (user.id),  -- Who reported it
    
    -- State management
    status VARCHAR NOT NULL DEFAULT 'open' INDEX,  -- open, triaged, assigned, fixing, testing, resolved, closed, rejected
    root_cause TEXT,                 -- RCA requirement for S1/S2
    fix_commit_sha VARCHAR(40),      -- Git commit hash of fix
    regression_test_added BOOLEAN DEFAULT false,
    
    -- Flexible fields
    assigned_agents JSONB DEFAULT '[]'::jsonb,      -- ["backend_engineer", "qa_automation"]
    related_incidents JSONB DEFAULT '[]'::jsonb,    -- ["defect_id_1", "defect_id_2"]
    metadata_json JSONB DEFAULT '{}'::jsonb,        -- Custom context (stack trace, error code, etc.)
    
    -- Timestamps (critical for SLA tracking)
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for query optimization
    INDEX idx_severity_status (severity, status),
    INDEX idx_environment (environment),
    INDEX idx_impact_area (impact_area),
    INDEX idx_created_at (created_at),
    INDEX idx_actor_id (actor_id)
);
```

### Defect Event Table (audit trail)

```sql
CREATE TABLE defect_event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    defect_id UUID NOT NULL FOREIGN KEY (defect_log.id) ON DELETE CASCADE INDEX,
    
    -- Event classification
    event_type VARCHAR NOT NULL,  -- status_changed, agent_assigned, rca_completed, test_added, fix_merged, etc.
    actor_id UUID FOREIGN KEY (user.id),  -- Who triggered the event (NULL for system events)
    
    -- Event payload (flexible storage for all event data)
    payload JSONB,  -- e.g., {"old_status": "open", "new_status": "triaged", "reason": "..."}
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_defect_id (defect_id),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
);
```

### Audit Log Integration

Every defect state change must be logged in the global `audit_log` table:

```sql
INSERT INTO audit_log (
    actor_id, 
    action, 
    entity_id, 
    request_id, 
    before_payload, 
    after_payload, 
    created_at
) VALUES (
    '...', 
    'defect.status_changed', 
    '...defect_id...', 
    '...request_id...', 
    '{"status": "open"}', 
    '{"status": "triaged"}', 
    NOW()
);
```

---

## API ENDPOINTS

### Base URL
```
POST   /api/v1/defects
GET    /api/v1/defects
PATCH  /api/v1/defects/{id}
GET    /api/v1/defects/{id}
GET    /api/v1/defects/{id}/timeline
DELETE /api/v1/defects/{id}  (soft delete with audit)
```

### 1. POST /api/v1/defects

**Create Defect (Any authenticated user)**

```json
Request:
{
  "title": "Double booking allowed on 2026-02-20",
  "description": "Master 'Dmitry' able to book overlapping slots. Affects all bookings on this date.",
  "environment": "prod",
  "severity": "S1",
  "impact_area": "backend",
  "detected_by": "qa",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
  "metadata_json": {
    "affected_master_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "booking_ids": ["...", "..."],
    "error_message": "Conflict detection failed",
    "stack_trace": "..."
  }
}

Response (201 Created):
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "title": "Double booking allowed on 2026-02-20",
  "description": "...",
  "environment": "prod",
  "severity": "S1",
  "impact_area": "backend",
  "detected_by": "qa",
  "status": "open",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "actor_id": "...",
  "detected_at": "2026-02-22T14:30:00Z",
  "created_at": "2026-02-22T14:30:00Z",
  "assigned_agents": [],
  "related_incidents": [],
  "root_cause": null,
  "regression_test_added": false
}
```

**Validations:**
- Only authenticated users can create defects
- `severity` must be valid enum (S1, S2, S3, S4)
- `impact_area` must be valid enum
- `environment` must be one of: dev, stage, prod
- `title` max 200 chars, required
- `description` optional but recommended for S1/S2

**Triggers:**
- Auto-create DefectEvent with type="defect_created"
- Log to global audit_log with action="defect.created"
- If S1 + prod: Send alert to Telegram admin group
- If S1 + prod: Block new deployments until acknowledged

---

### 2. GET /api/v1/defects

**List Defects (Requires 'defects:read' permission)**

```json
Request Query Params:
  ?severity=S1,S2           (filter by severity)
  &status=open,triaged      (filter by status)
  &impact_area=backend      (filter by impact area)
  &environment=prod         (filter by environment)
  &assigned_to=user_id      (filter by assigned agent)
  &created_after=2026-02-01 (ISO 8601 datetime)
  &created_before=2026-02-28
  &limit=50
  &offset=0
  &sort=-created_at         (- for desc, + for asc)
  &q=search_term            (full-text search on title + description)

Response (200 OK):
{
  "items": [
    {
      "id": "...",
      "title": "...",
      "severity": "S1",
      "status": "open",
      "impact_area": "backend",
      "environment": "prod",
      "detected_at": "2026-02-22T14:30:00Z",
      "acknowledged_at": null,
      "assigned_agents": [],
      "actor_id": "..."
    },
    ...
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

**Permissions:**
- `defects:read` — Any authenticated user
- Filters respect user's role (qa/debugger/admin see all; managers see their team's)

**Optimizations:**
- Indexes on severity, status, environment, impact_area, created_at
- Pagination enforced (max 500 per request)
- Full-text search uses PostgreSQL `tsvector`

---

### 3. PATCH /api/v1/defects/{id}

**Update Defect (Requires specific permission based on field)**

```json
Request:
{
  "status": "triaged",
  "severity": "S1",
  "assigned_agents": ["backend_engineer", "qa_automation"],
  "root_cause": "Booking conflict check logic had race condition in multi-threaded context. Fixed by adding pessimistic lock.",
  "fix_commit_sha": "a1b2c3d4e5f6g7h8i9j0",
  "regression_test_added": true
}

Response (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "status": "triaged",
  "severity": "S1",
  "assigned_agents": ["backend_engineer", "qa_automation"],
  "root_cause": "...",
  "fix_commit_sha": "...",
  "regression_test_added": true,
  "updated_at": "2026-02-22T15:45:00Z"
}
```

**Business Rules (enforced by service layer):**

| Transition | From | To | Allowed | Requires | Blocks Deployment |
|------------|------|----|---------|---------|----|
| Triage | OPEN | TRIAGED | Y | severity + impact_area filled | N |
| Assign | TRIAGED | ASSIGNED | Y | assigned_agents not empty | N |
| Begin Fix | ASSIGNED | FIXING | Y | - | N |
| Test Fix | FIXING | TESTING | Y | fix_commit_sha + regression_test_added | N |
| Resolve | TESTING | RESOLVED | Y | - (no more changes after) | N |
| Close | RESOLVED | CLOSED | Y | **RCA if S1/S2** | Y if S1 |
| Reject | ANY | REJECTED | Y | rejection_reason | N |

**Validation Logic:**

```python
# 1. Validate status transition
if new_status not in VALID_TRANSITIONS[old_status]:
    raise HTTPException(400, f"Invalid transition from {old_status} to {new_status}")

# 2. Enforce RCA for S1/S2 being closed
if new_status == CLOSED and defect.severity in [S1, S2]:
    root_cause = update_data.get('root_cause') or defect.root_cause
    if not root_cause or root_cause.strip() == '':
        raise HTTPException(400, "S1/S2 defects require root_cause before closure")

# 3. Enforce regression test for closure
if new_status == CLOSED and not defect.regression_test_added:
    raise HTTPException(400, "Defect cannot be closed without regression test added")

# 4. Block deployment if S1 and prod
if defect.severity == S1 and defect.environment == 'prod' and new_status == OPEN:
    raise HTTPException(503, "S1 production defect blocks deployments")

# 5. Create DefectEvent + Audit Log
crud.create_timeline_event(
    db,
    defect_id=defect.id,
    event_type=f"status_{old_status}_to_{new_status}",
    actor_id=actor.id,
    payload={
        "old_status": old_status,
        "new_status": new_status,
        "reason": update_data.get("reason"),
        "assigned_agents": update_data.get("assigned_agents")
    }
)

audit_service.log(
    db=db,
    actor_id=actor.id,
    action=f"defect.{new_status}",
    entity_id=defect.id,
    before_payload=old_data,
    after_payload=updated_data
)
```

**Permissions:**
- `defects:triage` — Move to TRIAGED
- `defects:assign` — Move to ASSIGNED, set assigned_agents
- `defects:fix` — Move to FIXING
- `defects:test` — Move to TESTING
- `defects:close` — Move to CLOSED/RESOLVED
- `defects:reject` — Move to REJECTED
- `audit:read` — View audit trail of all changes

---

### 4. GET /api/v1/defects/{id}

**Get Single Defect (Requires 'defects:read')**

```json
Response (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "title": "Double booking allowed on 2026-02-20",
  "description": "...",
  "environment": "prod",
  "severity": "S1",
  "impact_area": "backend",
  "detected_by": "qa",
  "status": "triaged",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
  "actor_id": "...",
  "assigned_agents": ["backend_engineer"],
  "related_incidents": ["550e8400-e29b-41d4-a716-446655440003"],
  "root_cause": null,
  "fix_commit_sha": null,
  "regression_test_added": false,
  "metadata_json": {
    "affected_master_id": "...",
    "booking_ids": ["...", "..."],
    "error_message": "..."
  },
  "detected_at": "2026-02-22T14:30:00Z",
  "acknowledged_at": "2026-02-22T14:35:00Z",
  "resolved_at": null,
  "created_at": "2026-02-22T14:30:00Z",
  "updated_at": "2026-02-22T15:45:00Z"
}
```

---

### 5. GET /api/v1/defects/{id}/timeline

**Get Audit Timeline (Requires 'audit:read')**

Shows complete history of all state changes and events.

```json
Response (200 OK):
{
  "defect_id": "550e8400-e29b-41d4-a716-446655440002",
  "events": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440004",
      "event_type": "defect_created",
      "actor_id": "550e8400-e29b-41d4-a716-446655440005",
      "actor_name": "qa_user@inka",
      "payload": {
        "severity": "S1",
        "impact_area": "backend"
      },
      "created_at": "2026-02-22T14:30:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440006",
      "event_type": "status_open_to_triaged",
      "actor_id": "550e8400-e29b-41d4-a716-446655440007",
      "actor_name": "manager@inka",
      "payload": {
        "old_status": "open",
        "new_status": "triaged",
        "reason": "Confirmed in prod environment"
      },
      "created_at": "2026-02-22T14:35:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440008",
      "event_type": "agent_assigned",
      "actor_id": "550e8400-e29b-41d4-a716-446655440007",
      "actor_name": "manager@inka",
      "payload": {
        "assigned_agents": ["backend_engineer", "qa_automation"],
        "reason": "Conflict detection logic"
      },
      "created_at": "2026-02-22T15:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440009",
      "event_type": "fix_merged",
      "actor_id": "550e8400-e29b-41d4-a716-446655440010",
      "actor_name": "backend_engineer@inka",
      "payload": {
        "commit_sha": "a1b2c3d4e5f6g7h8i9j0",
        "pr_url": "https://github.com/inka-admin/inka/pull/123"
      },
      "created_at": "2026-02-22T16:20:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440011",
      "event_type": "regression_test_added",
      "actor_id": "550e8400-e29b-41d4-a716-446655440010",
      "actor_name": "backend_engineer@inka",
      "payload": {
        "test_file": "tests/bookings/test_conflict_detection.py",
        "test_name": "test_pessimistic_lock_prevents_double_booking",
        "coverage_increase": "2.3%"
      },
      "created_at": "2026-02-22T16:30:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440012",
      "event_type": "rca_completed",
      "actor_id": "550e8400-e29b-41d4-a716-446655440007",
      "actor_name": "manager@inka",
      "payload": {
        "root_cause": "Booking conflict check logic had race condition in multi-threaded context when multiple requests tried to book same slot simultaneously. Was using SELECT without FOR UPDATE lock.",
        "why_not_detected": "Unit tests only cover single-threaded scenario. Load tests not run on this endpoint.",
        "preventive_actions": ["Always use pessimistic locks for critical checks", "Add load tests to CI pipeline for booking endpoints"]
      },
      "created_at": "2026-02-22T17:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440013",
      "event_type": "status_testing_to_resolved",
      "actor_id": "550e8400-e29b-41d4-a716-446655440014",
      "actor_name": "qa_automation@inka",
      "payload": {
        "old_status": "testing",
        "new_status": "resolved",
        "qa_result": "PASS"
      },
      "created_at": "2026-02-22T17:15:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440015",
      "event_type": "status_resolved_to_closed",
      "actor_id": "550e8400-e29b-41d4-a716-446655440007",
      "actor_name": "manager@inka",
      "payload": {
        "old_status": "resolved",
        "new_status": "closed"
      },
      "created_at": "2026-02-22T17:30:00Z"
    }
  ]
}
```

**Reconstructs entire incident lifecycle using DefectEvent + Audit Log.**

---

## SEVERITY CLASSIFICATION

### S1: Critical (Immediate Escalation)

**Definition:** Production outage, data loss, security breach, or break-glass misuse.

**Characteristics:**
- Users unable to complete core transactions
- Data corruption detected
- Security vulnerability exploited in prod
- PII leak
- System-wide availability < 95%
- Break-glass session misused (unauthorized actions)

**Examples:**
- Double booking allowed (S1 backend defect)
- Payment processing fails for all bookings (S1 backend + devops)
- Telegram bot offline / unresponsive (S1 bot)
- Database connection pool exhausted (S1 db + devops)
- Authentication bypass discovered (S1 security)
- Unencrypted PII in logs (S1 security)

**SLA & Actions:**
- **Response time:** 15 minutes
- **Resolution target:** 4 hours
- **Acknowledgment required:** Yes (manager/admin)
- **Block deployments:** YES — No new deploys until RESOLVED or REJECTED
- **Alert channels:** 
  - Telegram admin group (immediate)
  - PagerDuty (if configured)
  - GCP Cloud Monitoring (incident)
- **Post-incident:** RCA mandatory within 24h, runbook update required
- **Metrics:** Tracked for MTTR + incident frequency

**Escalation Path:**
1. Auto-alert Telegram admin group
2. If not acknowledged in 5 min → PagerDuty page
3. If not resolved in 2h → Senior engineer + management escalation

---

### S2: High (Fix Within Sprint)

**Definition:** Feature malfunction, RBAC bypass, or partial service degradation.

**Characteristics:**
- Subset of users affected
- Feature unavailable but alternatives exist
- Performance degradation (> 1s latency increase)
- RBAC policy not enforced correctly
- Data consistency issues (non-critical)
- Unauthorized access to non-PII data

**Examples:**
- Booking filtering slow for masters with 1000+ bookings (S2 backend)
- Manager cannot see reports for assigned masters (S2 backend)
- Telegram inline buttons timeout after 30 sec (S2 bot)
- Cache invalidation race condition (S2 backend + db)
- API rate limiting threshold too aggressive (S2 devops)

**SLA & Actions:**
- **Response time:** 1 hour
- **Resolution target:** Sprint length (e.g., 1 week)
- **Acknowledgment required:** Yes (manager/senior engineer)
- **Block deployments:** NO — May continue deploys, but S2 defect tracked
- **Alert channels:** 
  - Slack #incidents
  - Assigned engineer notification
- **Post-incident:** RCA required, runbook updated if needed
- **Metrics:** Tracked for backlog priority + burn-down

**Escalation Path:**
1. Alert assigned engineer
2. If not acknowledged in 30 min → Slack escalation
3. If not started in 2h → Assign backup engineer

---

### S3: Medium (Backlog Scheduled)

**Definition:** UX issue, cosmetic bug, or minor performance concern.

**Characteristics:**
- Non-blocking user experience issue
- Cosmetic defect (typo, alignment, color)
- Performance concern (100-300ms increase)
- Missing optional feature
- Misleading error message
- Documentation gap

**Examples:**
- Button label typo in admin panel (S3)
- Booking confirmation email arrives 2 minutes late (S3)
- Telegram help menu missing recent features (S3)
- API response headers incomplete (S3)
- Failed booking notification not sent (non-critical flow) (S3)

**SLA & Actions:**
- **Response time:** 2 days
- **Resolution target:** Next sprint or backlog
- **Acknowledgment required:** No
- **Block deployments:** NO
- **Alert channels:** 
  - Backlog ticket created
  - Team standup mention
- **Post-incident:** Fix verification + regression test, no RCA needed
- **Metrics:** Tracked for backlog health

---

### S4: Low (Cosmetic / Future)

**Definition:** Cosmetic issue, typo, or documentation gap with zero user impact.

**Characteristics:**
- No user impact
- Code quality / style issue
- Logging improvement
- Comment/documentation typo
- Build warning (not error)

**Examples:**
- Unused import in utility module (S4)
- Log message grammatical error (S4)
- README example outdated (S4)
- Type hint incomplete (S4)

**SLA & Actions:**
- **Response time:** None (backlog when time permits)
- **Resolution target:** Eventually
- **Acknowledgment required:** No
- **Block deployments:** NO
- **Alert channels:** None (backlog only)
- **Post-incident:** None (no RCA, test optional)
- **Metrics:** Optional (low priority)

---

### Severity Decision Matrix

| Criteria | S1 | S2 | S3 | S4 |
|----------|----|----|----|----|
| **Users affected** | All | Subset | Few | None |
| **Data loss** | Yes | Possible | No | No |
| **Security breach** | Yes | RBAC bypass | No | No |
| **Availability** | < 95% | < 99% | 99%+ | 99%+ |
| **Workaround exists** | No | Yes | Yes | Yes |
| **Production system** | Critical → S1 | High risk → S2 | Low risk → S3 | None → S4 |

---

## ROOT CAUSE ANALYSIS

### RCA Requirements (S1 & S2 Mandatory)

Every S1 and S2 defect **must** include a completed RCA before closure. RCA must be documented in the `root_cause` field and DefectEvent timeline.

### RCA Template & Structure

**Section 1: Timeline Reconstruction**

Using `request_id`, `correlation_id`, and audit logs, rebuild the sequence of events:

```
[2026-02-20 14:30:00 UTC] User A (master_id: 123) attempts booking slot 10:00-11:00 for client X
  → API request received (request_id: req-aaa-111)
  → Booking service calls conflict_check()
  → Query: SELECT * FROM booking WHERE master_id=123 AND date='2026-02-20' (No lock)
  → Result: No conflicting booking found
  
[2026-02-20 14:30:00.001 UTC] User B (master_id: 123) SIMULTANEOUSLY attempts same slot
  → API request received (request_id: req-bbb-222)
  → Booking service calls conflict_check()
  → Query: SELECT * FROM booking WHERE master_id=123 AND date='2026-02-20' (No lock)
  → Result: No conflicting booking found (User A's booking not yet COMMITTED)
  
[2026-02-20 14:30:00.100 UTC] User A's transaction COMMITS
  → Booking for slot 10:00-11:00 created
  
[2026-02-20 14:30:00.150 UTC] User B's transaction COMMITS
  → Booking for SAME slot 10:00-11:00 created (RACE CONDITION)
  → Double booking now exists

[2026-02-20 14:31:00 UTC] Monitoring alert: Double booking detected
```

**Section 2: What Failed**

Describe the immediate failure:

```
The conflict detection logic in BookingService.create_booking() uses a non-blocking SELECT query:

    SELECT * FROM booking 
    WHERE master_id = :master_id 
    AND date = :date
    AND status = 'confirmed'

When two requests execute simultaneously:
  1. Both reach SELECT at virtually same time
  2. Neither sees the other's uncommitted transaction
  3. Both return "no conflict" and proceed to INSERT
  4. Database accepts both INSERTs (no UNIQUE constraint exists on time slots)
  5. Race condition: double booking created
```

**Section 3: Why It Failed**

Root cause analysis — dig deeper:

```
Root Cause: Missing pessimistic locking in multi-threaded context.

Technical Root Cause:
- SELECT query does NOT use FOR UPDATE (row-level lock)
- Booking service runs in async context (FastAPI + multiple workers)
- No transactional isolation level set to SERIALIZABLE
- Database connection pool has concurrent connections

Contributing Factors:
1. Async architecture allows simultaneous processing of same master's bookings
2. PostgreSQL default isolation level (READ COMMITTED) allows dirty reads from uncommitted transactions
3. No application-level mutex or distributed lock (e.g., Redis)
4. Conflict detection happens BEFORE INSERT, with gap between check and write
5. No unique constraint on (master_id, date, start_time, end_time)
```

**Section 4: Why It Was Not Detected Earlier**

Preventive controls that failed:

```
1. Unit Tests: Only cover single-threaded scenario
   - Test creates single booking, asserts no conflict
   - Never test concurrent requests to same slot
   - Mock time is sequential, not parallel

2. Integration Tests: Run on single DB connection
   - No multi-threaded test harness
   - No load test for high-concurrency booking endpoints

3. Code Review: Missed locking issue
   - Reviewers unfamiliar with async race conditions
   - No checklist for database concurrency issues

4. Load Testing: Not run on booking endpoints
   - Concurrency testing skipped in CI pipeline
   - Only performance testing done

5. Database Constraints: Missing UNIQUE constraint
   - No constraint to prevent duplicate slot bookings
   - Relied solely on application logic
```

**Section 5: Corrective Action (Immediate)**

Fix deployed and tested:

```
1. Add FOR UPDATE lock to conflict check:

   SELECT * FROM booking 
   WHERE master_id = :master_id 
   AND date = :date
   AND status = 'confirmed'
   FOR UPDATE SKIP LOCKED

2. Wrap in explicit transaction with SERIALIZABLE isolation:

   BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
   -- Check for conflict
   -- If none, INSERT booking
   COMMIT;

3. Add UNIQUE constraint as safety net:

   ALTER TABLE booking ADD CONSTRAINT uniq_master_timeslot 
   UNIQUE (master_id, date, start_time);

4. Restart booking service (deploy commit: a1b2c3d4e5f6g7h8i9j0)

5. QA Validation: Load test with 100 concurrent requests to same slot
   Result: All but first request rejected (conflict detected)
```

**Section 6: Preventive Action (Long-term)**

Prevent recurrence:

```
1. Code Quality:
   - Add linting rule: forbid SELECT without FOR UPDATE on critical tables
   - Add code review checklist item: "Check for concurrency issues"
   - Education: Team training on database locking + async patterns

2. Testing:
   - Add concurrent booking tests to CI pipeline
   - Load test framework: k6 or JMeter for concurrency testing
   - Target: Simulate 50+ concurrent requests per endpoint
   - Every release must pass concurrency tests

3. Database:
   - Add UNIQUE constraints on time-based resources (bookings, schedule)
   - Document isolation level requirements per service
   - Add foreign key constraints to prevent orphaned bookings

4. Monitoring:
   - Alert on double bookings (SELECT COUNT WHERE master_id=X AND date=Y AND status='confirmed' > 1)
   - Alert on transaction rollbacks (deadlock/serialization failures)
   - Metric: "concurrent_conflicts" tracked per hour

5. Runbook Update:
   - Add "Database Locking Best Practices" section
   - Example: "Always use FOR UPDATE for critical checks in async context"
```

### RCA Payload Structure (for DefectEvent)

```json
{
  "event_type": "rca_completed",
  "payload": {
    "root_cause": "Missing pessimistic lock (FOR UPDATE) in conflict detection logic...",
    "why_not_detected": "Unit tests only cover single-threaded scenario. No load tests on booking endpoints.",
    "timeline": [
      {"timestamp": "2026-02-20T14:30:00Z", "event": "User A attempts booking"},
      {"timestamp": "2026-02-20T14:30:00.001Z", "event": "User B simultaneously attempts same slot"},
      {"timestamp": "2026-02-20T14:30:00.100Z", "event": "User A's transaction commits"},
      {"timestamp": "2026-02-20T14:30:00.150Z", "event": "User B's transaction commits (race condition)"}
    ],
    "corrective_actions": [
      "Deploy fix with FOR UPDATE lock (commit: a1b2c3d4)",
      "Add UNIQUE constraint on (master_id, date, start_time)",
      "Load test with 100 concurrent requests"
    ],
    "preventive_actions": [
      "Add concurrency testing to CI pipeline",
      "Team training on database locking patterns",
      "Add code review checklist for async concurrency",
      "Monitor for double bookings in production"
    ],
    "rca_completed_by": "manager@inka",
    "rca_completed_at": "2026-02-22T17:00:00Z"
  }
}
```

### Enforcement

**No S1/S2 defect may transition to CLOSED without:**
1. Non-empty `root_cause` field (>= 100 characters)
2. DefectEvent with type="rca_completed" in timeline
3. Corrective + preventive actions documented

Code enforcement in service layer:

```python
def validate_s1_s2_closure(db: Session, defect: Defect):
    if defect.severity not in [DefectSeverity.S1, DefectSeverity.S2]:
        return  # S3/S4 don't need RCA
    
    # Check root_cause field
    if not defect.root_cause or len(defect.root_cause.strip()) < 100:
        raise HTTPException(
            status_code=400,
            detail=f"S{defect.severity.value} defects require detailed root cause (>= 100 chars)"
        )
    
    # Check DefectEvent timeline
    rca_events = db.query(DefectEvent).filter(
        DefectEvent.defect_id == defect.id,
        DefectEvent.event_type == "rca_completed"
    ).all()
    
    if not rca_events:
        raise HTTPException(
            status_code=400,
            detail="RCA event not found in timeline. Complete RCA before closure."
        )
    
    rca_event = rca_events[-1]  # Latest RCA
    if not rca_event.payload or \
       not rca_event.payload.get("corrective_actions") or \
       not rca_event.payload.get("preventive_actions"):
        raise HTTPException(
            status_code=400,
            detail="RCA missing corrective or preventive actions"
        )
```

---

## AGENT ROUTING

### Agent Assignment Matrix

Based on `impact_area` and `severity`, defects are routed to specialized agents:

| Impact Area | Primary Agent | Secondary | Severity Filter | Urgency |
|-------------|---------------|-----------|-----------------|---------|
| **backend** | Backend Engineer | QA Automation, DevOps | S1/S2 within 1h, S3 next sprint | Critical fixes ASAP |
| **bot** | Telegram Bot Engineer | QA Automation | S1 within 30min, S2 within 2h | High responsiveness |
| **db** | DevOps / Database Engineer | Backend Engineer | S1 within 15min | Critical data |
| **security** | Security Engineer | DevOps, Backend | S1 within 1h | Immediate escalation |
| **devops** | DevOps / SRE | Backend, Security | S1 within 30min | Infrastructure critical |

### Assignment Logic (Service Layer)

```python
from typing import List
from enum import Enum

class AgentType(str, Enum):
    BACKEND_ENGINEER = "backend_engineer"
    BOT_ENGINEER = "bot_engineer"
    QA_AUTOMATION = "qa_automation"
    DEVOPS_SRE = "devops_sre"
    SECURITY_ENGINEER = "security_engineer"

def assign_agents(defect: Defect) -> List[AgentType]:
    """
    Automatically determine assigned agents based on impact_area + severity.
    Returns list of agent roles to notify.
    """
    agents = []
    
    # Primary assignment based on impact area
    if defect.impact_area == ImpactArea.BACKEND:
        agents.append(AgentType.BACKEND_ENGINEER)
        agents.append(AgentType.QA_AUTOMATION)  # For regression tests
    
    elif defect.impact_area == ImpactArea.BOT:
        agents.append(AgentType.BOT_ENGINEER)
        agents.append(AgentType.QA_AUTOMATION)
    
    elif defect.impact_area == ImpactArea.DB:
        agents.append(AgentType.DEVOPS_SRE)
        agents.append(AgentType.BACKEND_ENGINEER)  # May need schema changes
    
    elif defect.impact_area == ImpactArea.SECURITY:
        agents.append(AgentType.SECURITY_ENGINEER)
        agents.append(AgentType.DEVOPS_SRE)  # For incident response
        agents.append(AgentType.BACKEND_ENGINEER)  # If app code affected
    
    elif defect.impact_area == ImpactArea.DEVOPS:
        agents.append(AgentType.DEVOPS_SRE)
        agents.append(AgentType.BACKEND_ENGINEER)  # If service affected
    
    # Secondary assignment based on severity
    if defect.severity == DefectSeverity.S1:
        # Always include QA for critical verification
        if AgentType.QA_AUTOMATION not in agents:
            agents.append(AgentType.QA_AUTOMATION)
    
    return list(set(agents))  # Remove duplicates

def create_agent_task(defect: Defect, agent: AgentType) -> dict:
    """
    Create a task for assigned agent with expected output + deadline.
    """
    deadline_hours = {
        (DefectSeverity.S1, AgentType.BACKEND_ENGINEER): 4,
        (DefectSeverity.S1, AgentType.BOT_ENGINEER): 2,
        (DefectSeverity.S1, AgentType.DEVOPS_SRE): 1,
        (DefectSeverity.S1, AgentType.SECURITY_ENGINEER): 1,
        (DefectSeverity.S2, AgentType.BACKEND_ENGINEER): 24,
        (DefectSeverity.S2, AgentType.BOT_ENGINEER): 8,
        (DefectSeverity.S2, AgentType.DEVOPS_SRE): 4,
        (DefectSeverity.S3, AgentType.BACKEND_ENGINEER): 168,  # 1 week
        (DefectSeverity.S4, AgentType.BACKEND_ENGINEER): None,  # Backlog
    }
    
    deadline_key = (defect.severity, agent)
    hours = deadline_hours.get(deadline_key, 168)
    
    return {
        "agent": agent.value,
        "defect_id": str(defect.id),
        "title": defect.title,
        "severity": defect.severity.value,
        "impact_area": defect.impact_area.value,
        "deadline_hours": hours,
        "expected_output": get_expected_output(agent, defect),
        "acceptance_criteria": get_acceptance_criteria(agent, defect),
        "assigned_at": datetime.now(timezone.utc),
    }

def get_expected_output(agent: AgentType, defect: Defect) -> str:
    """
    Define what each agent should deliver.
    """
    templates = {
        AgentType.BACKEND_ENGINEER: (
            "1. Root cause analysis\n"
            "2. Code fix with test coverage > 80%\n"
            "3. Pull request with regression test\n"
            "4. Deployment confirmation"
        ),
        AgentType.BOT_ENGINEER: (
            "1. Issue reproduction steps\n"
            "2. Code fix in telegram bot handlers\n"
            "3. Unit test for fix\n"
            "4. Deployment to bot"
        ),
        AgentType.DEVOPS_SRE: (
            "1. Infrastructure assessment\n"
            "2. Resource scaling / config fix\n"
            "3. Monitoring alert configuration\n"
            "4. Runbook update"
        ),
        AgentType.QA_AUTOMATION: (
            "1. Test reproduction\n"
            "2. Regression test creation\n"
            "3. Load/stress test if applicable\n"
            "4. QA sign-off"
        ),
        AgentType.SECURITY_ENGINEER: (
            "1. Vulnerability assessment\n"
            "2. Proof of concept (PoC)\n"
            "3. Fix or mitigation\n"
            "4. Security verification"
        ),
    }
    return templates.get(agent, "")

def get_acceptance_criteria(agent: AgentType, defect: Defect) -> List[str]:
    """
    Define what 'done' means for each agent.
    """
    criteria = {
        AgentType.BACKEND_ENGINEER: [
            "Code compiles without errors",
            "Unit tests pass (new + existing)",
            "Regression test added",
            "Code review approved",
            "CI pipeline green",
            "Fix deployed to staging",
        ],
        AgentType.BOT_ENGINEER: [
            "Bot command / handler updated",
            "Unit tests added",
            "Telegram handlers tested manually",
            "Code review approved",
            "Deployed to bot",
        ],
        AgentType.DEVOPS_SRE: [
            "Infrastructure scaling applied",
            "Config changes deployed",
            "Monitoring metrics confirmed",
            "Runbook documented",
            "SLA threshold met",
        ],
        AgentType.QA_AUTOMATION: [
            "Test case created",
            "Test passes with fix, fails without it",
            "Test integrated into CI",
            "Coverage > 80% for related code",
        ],
    }
    return criteria.get(agent, [])
```

### Assignment Workflow

```python
def assign_defect(db: Session, defect_id: UUID, actor_id: UUID):
    """
    Auto-assign agents when defect transitions to TRIAGED or ASSIGNED.
    """
    defect = crud.get_defect(db, defect_id)
    agents = assign_agents(defect)
    
    # Update defect
    defect.assigned_agents = [a.value for a in agents]
    defect.status = DefectStatus.ASSIGNED
    
    # Create DefectEvent
    crud.create_timeline_event(
        db,
        defect_id=defect.id,
        event_type="agents_assigned",
        actor_id=actor_id,
        payload={
            "assigned_agents": defect.assigned_agents,
            "tasks": [create_agent_task(defect, agent).model_dump() for agent in agents]
        }
    )
    
    # Send Telegram notifications to agents
    for agent in agents:
        send_telegram_notification(
            to_role=agent.value,
            message=f"New defect assigned: {defect.title}\nSeverity: {defect.severity.value}\nDeadline: {create_agent_task(defect, agent)['deadline_hours']}h"
        )
    
    # Log to audit trail
    audit_service.log(
        db=db,
        actor_id=actor_id,
        action="defect.agents_assigned",
        entity_id=defect.id,
        after_payload={"assigned_agents": defect.assigned_agents}
    )
    
    db.commit()
    return defect
```

---

## REGRESSION PREVENTION

### Regression Prevention Policy

Every defect fix **must include** an automated regression test before closure.

**Enforcement Rule:**
```
IF defect.status -> CLOSED AND defect.regression_test_added != true
THEN REJECT transition with error: "Regression test required before closure"
```

### Regression Test Requirements

For each fix, define:

1. **Test Location** (required field in DefectEvent)
   - File path: `tests/bookings/test_conflict_detection.py`
   - Package: `inka/apps/api/tests/bookings/`

2. **Test Name** (required field in DefectEvent)
   - Descriptive: `test_pessimistic_lock_prevents_double_booking`
   - Format: `test_<defect_scenario>_<fix_validation>`

3. **Test Type**
   - Unit test (for code logic)
   - Integration test (for end-to-end flows)
   - Load test (for concurrency issues)
   - Security test (for RBAC/auth issues)

4. **Assertion**
   - Test must FAIL without the fix
   - Test must PASS with the fix
   - Proof: Run test on fix commit only

5. **Code Coverage**
   - New test must increase coverage > 2%
   - Target: 80%+ for affected module

### Regression Test Template

```python
# tests/bookings/test_conflict_detection.py

import pytest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from packages.core.domains.bookings.service import BookingService
from packages.core.domains.bookings.models import Booking

class TestConflictDetection:
    """
    Regression test for: S1 Double booking allowed on 2026-02-20
    Fix: Add FOR UPDATE lock in conflict detection (commit: a1b2c3d4)
    """
    
    @pytest.fixture
    def booking_service(self, db: Session):
        return BookingService()
    
    @pytest.fixture
    def master_and_slot(self, db: Session):
        # Create test master and time slot
        master_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        slot_date = datetime.now().date() + timedelta(days=1)
        slot_start = datetime.combine(slot_date, datetime.min.time()).replace(hour=10)
        slot_end = slot_start + timedelta(hours=1)
        return master_id, slot_start, slot_end
    
    def test_pessimistic_lock_prevents_double_booking(
        self,
        db: Session,
        booking_service: BookingService,
        master_and_slot: tuple
    ):
        """
        **Regression Test:** Concurrent requests to book same slot should fail
        
        **Scenario:** Two users simultaneously attempt to book 10:00-11:00 for same master
        **Expected Behavior:** First booking succeeds, second fails with conflict error
        **Regression:** Without FOR UPDATE lock, both succeed (double booking)
        """
        master_id, slot_start, slot_end = master_and_slot
        
        def attempt_booking(client_id: str):
            try:
                return booking_service.create_booking(
                    db=db,
                    master_id=master_id,
                    client_id=client_id,
                    start_time=slot_start,
                    end_time=slot_end
                )
            except Exception as e:
                return f"CONFLICT: {str(e)}"
        
        # Execute concurrent booking attempts
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(attempt_booking, ["client_1", "client_2"]))
        
        # Verify: Exactly 1 success, 1 failure
        successes = [r for r in results if not isinstance(r, str)]
        failures = [r for r in results if isinstance(r, str) and "CONFLICT" in r]
        
        assert len(successes) == 1, f"Expected 1 booking success, got {len(successes)}"
        assert len(failures) == 1, f"Expected 1 booking conflict, got {len(failures)}"
        
        # Verify: No double bookings in database
        double_bookings = db.query(Booking).filter(
            Booking.master_id == master_id,
            Booking.start_time == slot_start
        ).all()
        assert len(double_bookings) == 1, f"Double booking detected: {len(double_bookings)} bookings exist"
    
    def test_pessimistic_lock_detects_conflict_without_fix(
        self,
        db: Session,
        booking_service: BookingService,
        master_and_slot: tuple
    ):
        """
        **Regression Proof:** This test FAILS without FOR UPDATE fix.
        Run this test on old code (without fix) to demonstrate race condition.
        """
        master_id, slot_start, slot_end = master_and_slot
        
        # Create first booking
        booking1 = booking_service.create_booking(
            db=db,
            master_id=master_id,
            client_id="client_a",
            start_time=slot_start,
            end_time=slot_end
        )
        assert booking1 is not None
        
        # WITHOUT FIX: Attempt second booking on SAME slot (should fail)
        # WITH FIX: Would raise ConflictError
        with pytest.raises(ConflictError):
            booking_service.create_booking(
                db=db,
                master_id=master_id,
                client_id="client_b",
                start_time=slot_start,
                end_time=slot_end
            )
```

### CI Integration

In GitHub Actions pipeline, enforce:

```yaml
# .github/workflows/test.yml
name: Test & Regression

on: [push, pull_request]

jobs:
  regression-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Regression Tests
        run: |
          pytest tests/ -k "test_.*regression" -v --tb=short
      
      - name: Fail if No Regression Test
        run: |
          # Check if PR added regression test for referenced defect
          if grep -r "Regression Test:" tests/ | grep -q "@"; then
            echo "✓ Regression test found for defect"
          else
            echo "✗ No regression test found. Defect must include test."
            exit 1
          fi
      
      - name: Coverage Check
        run: |
          pytest --cov=apps --cov=libs --cov-report=term-missing
          # Ensure new code has >80% coverage
          coverage report --fail-under=80
```

### Enforcement in Defect API

```python
def validate_closure_regression_test(db: Session, defect: Defect):
    """
    Enforce: Defect cannot be CLOSED without regression test added.
    """
    if not defect.regression_test_added:
        raise HTTPException(
            status_code=400,
            detail="Regression test must be added before closure. "
                   "Update 'regression_test_added' field and provide test location."
        )
    
    # Verify test actually exists in codebase
    test_file = defect.metadata_json.get("regression_test_file")
    test_name = defect.metadata_json.get("regression_test_name")
    
    if not test_file or not test_name:
        raise HTTPException(
            status_code=400,
            detail="Regression test location missing. Provide 'regression_test_file' and 'regression_test_name' in metadata."
        )
```

---

## TELEGRAM INCIDENT COMMANDS

### New Commands

Add these commands to Telegram bot for incident management:

```python
# apps/bot/src/bot/handlers/incidents.py

from aiogram import Router, types, F
from aiogram.filters import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from packages.core.domains.defects.service import create_defect_with_audit
from packages.core.domains.auth.models import User

router = Router()

class IncidentReportStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_environment = State()
    waiting_for_severity = State()
    confirmation = State()

# ============================================================================
# /incident report — Start incident creation wizard
# ============================================================================

@router.message(F.text == "/incident report")
async def incident_report(message: types.Message, state: FSMContext, user: User):
    """
    Start guided incident report creation.
    Restricted to: qa, debugger, admin, manager
    """
    # Permission check
    if user.role not in ["qa", "debugger", "admin", "manager"]:
        await message.reply(
            "❌ You don't have permission to report incidents.\n"
            "Required roles: qa, debugger, admin, manager"
        )
        return
    
    await message.reply(
        "📋 **Incident Report Wizard**\n\n"
        "I'll help you document an incident. Follow the steps below.\n\n"
        "**Step 1:** What's the incident title? (max 200 chars)\n"
        "Example: 'Double booking allowed on 2026-02-20'"
    )
    await state.set_state(IncidentReportStates.waiting_for_title)

@router.message(IncidentReportStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    """Store title and ask for description."""
    if len(message.text) > 200:
        await message.reply("⚠️ Title too long (max 200 chars). Try again:")
        return
    
    await state.update_data(title=message.text)
    await message.reply(
        "**Step 2:** Describe the issue (what happened)?\n"
        "Example: 'Master can book overlapping time slots for same service.'"
    )
    await state.set_state(IncidentReportStates.waiting_for_description)

@router.message(IncidentReportStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    """Store description and ask for environment."""
    await state.update_data(description=message.text)
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🔴 prod", callback_data="env_prod"),
            types.InlineKeyboardButton(text="🟠 stage", callback_data="env_stage"),
        ],
        [
            types.InlineKeyboardButton(text="🟡 dev", callback_data="env_dev"),
        ]
    ])
    
    await message.reply(
        "**Step 3:** Which environment?\n",
        reply_markup=keyboard
    )
    await state.set_state(IncidentReportStates.waiting_for_environment)

@router.callback_query(F.data.startswith("env_"))
async def select_environment(query: types.CallbackQuery, state: FSMContext):
    """Store environment selection and ask for severity."""
    env = query.data.split("_")[1]  # prod, stage, dev
    await state.update_data(environment=env)
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🔴 S1 (Critical)", callback_data="sev_S1"),
            types.InlineKeyboardButton(text="🟠 S2 (High)", callback_data="sev_S2"),
        ],
        [
            types.InlineKeyboardButton(text="🟡 S3 (Medium)", callback_data="sev_S3"),
            types.InlineKeyboardButton(text="⚪ S4 (Low)", callback_data="sev_S4"),
        ]
    ])
    
    env_label = {"prod": "🔴 prod", "stage": "🟠 stage", "dev": "🟡 dev"}.get(env, env)
    
    await query.message.edit_text(
        f"**Step 4:** What's the severity?\n\n"
        f"Selected environment: {env_label}\n\n"
        f"📌 **Severity Guide:**\n"
        f"🔴 **S1 (Critical)** — Production outage, users blocked\n"
        f"🟠 **S2 (High)** — Feature broken, workaround exists\n"
        f"🟡 **S3 (Medium)** — UX issue, non-blocking\n"
        f"⚪ **S4 (Low)** — Cosmetic, typo, etc.\n",
        reply_markup=keyboard
    )
    await state.set_state(IncidentReportStates.waiting_for_severity)

@router.callback_query(F.data.startswith("sev_"))
async def select_severity(query: types.CallbackQuery, state: FSMContext):
    """Store severity and show confirmation."""
    severity = query.data.split("_")[1]  # S1, S2, S3, S4
    await state.update_data(severity=severity)
    
    data = await state.get_data()
    
    severity_icon = {"S1": "🔴", "S2": "🟠", "S3": "🟡", "S4": "⚪"}.get(severity, "")
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Submit", callback_data="confirm_yes"),
            types.InlineKeyboardButton(text="❌ Cancel", callback_data="confirm_no"),
        ]
    ])
    
    await query.message.edit_text(
        f"**Review Incident Report**\n\n"
        f"**Title:** {data['title']}\n"
        f"**Description:** {data['description']}\n"
        f"**Environment:** {data['environment'].upper()}\n"
        f"**Severity:** {severity_icon} {severity}\n\n"
        f"Looks good?",
        reply_markup=keyboard
    )
    await state.set_state(IncidentReportStates.confirmation)

@router.callback_query(F.data == "confirm_yes")
async def submit_incident(query: types.CallbackQuery, state: FSMContext, db: Session, user: User):
    """Submit incident to database."""
    data = await state.get_data()
    
    try:
        # Create defect record
        from packages.core.domains.defects.schemas import DefectCreate
        
        defect_payload = DefectCreate(
            title=data['title'],
            description=data['description'],
            environment=data['environment'],
            severity=data['severity'],
            impact_area="unknown",  # Will be triaged by manager
            detected_by="user",
            request_id=None
        )
        
        defect = create_defect_with_audit(
            db=db,
            actor_id=user.id,
            payload=defect_payload
        )
        
        # Generate view link
        defect_link = f"https://inka-admin.app/defects/{defect.id}"
        
        await query.message.edit_text(
            f"✅ **Incident Reported Successfully!**\n\n"
            f"Defect ID: `{defect.id}`\n"
            f"Title: {data['title']}\n"
            f"Severity: {data['severity']}\n\n"
            f"👉 [View Incident]({defect_link})\n\n"
            f"Admins will triage shortly.",
            parse_mode="Markdown"
        )
        
        # Alert admin group
        admin_group_id = -1001234567890  # Configure in .env
        await query.bot.send_message(
            chat_id=admin_group_id,
            text=f"🚨 **New Incident Reported** ({data['severity']})\n\n"
                 f"Title: {data['title']}\n"
                 f"Environment: {data['environment']}\n"
                 f"Reported by: {user.full_name}\n"
                 f"ID: {defect.id}"
        )
        
    except Exception as e:
        await query.message.edit_text(
            f"❌ Error creating incident: {str(e)}\n"
            f"Please contact admin."
        )
    
    await state.clear()

@router.callback_query(F.data == "confirm_no")
async def cancel_incident(query: types.CallbackQuery, state: FSMContext):
    """Cancel incident creation."""
    await query.message.edit_text("❌ Incident report cancelled.")
    await state.clear()

# ============================================================================
# /incident status {id} — Get incident details
# ============================================================================

@router.message(commands=["incident"])
async def incident_command(message: types.Message, command: CommandObject, user: User, db: Session):
    """
    Handle: /incident status {id}, /incident list open, /incident escalate {id}, /incident timeline {id}
    """
    if not command.args:
        await message.reply(
            "📋 **Incident Commands**\n\n"
            "`/incident report` — Report new incident\n"
            "`/incident status {id}` — Check incident status\n"
            "`/incident list open` — Show open incidents\n"
            "`/incident escalate {id}` — Escalate to management (S2+ only)\n"
            "`/incident timeline {id}` — View full incident history\n"
        )
        return
    
    args = command.args.split()
    subcommand = args[0]
    
    if subcommand == "status" and len(args) > 1:
        await incident_status(message, args[1], user, db)
    elif subcommand == "list" and len(args) > 1:
        await incident_list(message, args[1], user, db)
    elif subcommand == "escalate" and len(args) > 1:
        await incident_escalate(message, args[1], user, db)
    elif subcommand == "timeline" and len(args) > 1:
        await incident_timeline(message, args[1], user, db)
    else:
        await message.reply("❓ Unknown command. Use `/incident` for help.")

async def incident_status(message: types.Message, defect_id: str, user: User, db: Session):
    """Show incident status."""
    from packages.core.domains.defects.models import Defect
    from uuid import UUID
    
    try:
        defect = db.query(Defect).filter(Defect.id == UUID(defect_id)).first()
        if not defect:
            await message.reply(f"❌ Incident {defect_id} not found.")
            return
        
        severity_icon = {"S1": "🔴", "S2": "🟠", "S3": "🟡", "S4": "⚪"}.get(defect.severity.value, "")
        status_icon = {
            "open": "🔵",
            "triaged": "🟣",
            "assigned": "🟠",
            "fixing": "🟡",
            "testing": "🟢",
            "resolved": "✅",
            "closed": "🔒",
        }.get(defect.status.value, "")
        
        await message.reply(
            f"{status_icon} **Incident Status**\n\n"
            f"**ID:** `{defect.id}`\n"
            f"**Title:** {defect.title}\n"
            f"**Severity:** {severity_icon} {defect.severity.value}\n"
            f"**Status:** {status_icon} {defect.status.value}\n"
            f"**Environment:** {defect.environment}\n"
            f"**Impact Area:** {defect.impact_area.value}\n"
            f"**Assigned to:** {', '.join(defect.assigned_agents) or 'unassigned'}\n\n"
            f"**Created:** {defect.created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"**Updated:** {defect.updated_at.strftime('%Y-%m-%d %H:%M UTC')}\n",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

async def incident_list(message: types.Message, filter_status: str, user: User, db: Session):
    """List incidents filtered by status (open, triaged, assigned, fixing)."""
    from packages.core.domains.defects.models import Defect, DefectStatus
    
    try:
        defects = db.query(Defect)\
            .filter(Defect.status == filter_status)\
            .order_by(Defect.severity, Defect.created_at.desc())\
            .limit(10)\
            .all()
        
        if not defects:
            await message.reply(f"ℹ️ No {filter_status} incidents.")
            return
        
        text = f"📋 **{filter_status.upper()} Incidents** ({len(defects)})\n\n"
        for d in defects:
            sev_icon = {"S1": "🔴", "S2": "🟠", "S3": "🟡", "S4": "⚪"}.get(d.severity.value, "")
            text += f"{sev_icon} {d.title[:50]}\n"
            text += f"   ID: `{str(d.id)[:8]}...`\n"
        
        await message.reply(text, parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

async def incident_escalate(message: types.Message, defect_id: str, user: User, db: Session):
    """Escalate incident to management (S2+ only)."""
    from packages.core.domains.defects.models import Defect, DefectSeverity
    from uuid import UUID
    
    # Permission check
    if user.role not in ["debugger", "admin"]:
        await message.reply("❌ Only debugger/admin can escalate incidents.")
        return
    
    try:
        defect = db.query(Defect).filter(Defect.id == UUID(defect_id)).first()
        if not defect:
            await message.reply(f"❌ Incident not found.")
            return
        
        # Only allow S1/S2 escalation
        if defect.severity not in [DefectSeverity.S1, DefectSeverity.S2]:
            await message.reply(
                f"⚠️ Only S1/S2 incidents can be escalated.\n"
                f"Current severity: {defect.severity.value}"
            )
            return
        
        # Send message to management group
        management_group_id = -1001234567891  # Configure in .env
        
        sev_icon = {"S1": "🔴", "S2": "🟠"}.get(defect.severity.value, "")
        await message.bot.send_message(
            chat_id=management_group_id,
            text=f"🚨 **ESCALATED** {sev_icon} {defect.severity.value}\n\n"
                 f"Title: {defect.title}\n"
                 f"Environment: {defect.environment}\n"
                 f"Status: {defect.status.value}\n"
                 f"Escalated by: {user.full_name}\n"
                 f"ID: {defect.id}"
        )
        
        await message.reply(f"✅ Incident escalated to management.")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

async def incident_timeline(message: types.Message, defect_id: str, user: User, db: Session):
    """Show incident timeline (audit trail)."""
    from packages.core.domains.defects.models import Defect, DefectEvent
    from uuid import UUID
    
    try:
        defect = db.query(Defect).filter(Defect.id == UUID(defect_id)).first()
        if not defect:
            await message.reply(f"❌ Incident not found.")
            return
        
        events = db.query(DefectEvent)\
            .filter(DefectEvent.defect_id == defect.id)\
            .order_by(DefectEvent.created_at)\
            .limit(10)\
            .all()
        
        if not events:
            await message.reply("ℹ️ No timeline events yet.")
            return
        
        text = f"📜 **Incident Timeline** ({len(events)} events)\n\n"
        for event in events:
            actor_name = event.actor.full_name if event.actor else "SYSTEM"
            text += f"• **{event.event_type}**\n"
            text += f"  By: {actor_name}\n"
            text += f"  At: {event.created_at.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        
        await message.reply(text, parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
```

### Permission Model

```python
# Telegram incident command permissions

INCIDENT_COMMAND_PERMISSIONS = {
    "/incident report": ["qa", "debugger", "admin", "manager"],
    "/incident status": ["qa", "debugger", "admin", "manager", "readOnly"],
    "/incident list": ["qa", "debugger", "admin", "manager"],
    "/incident escalate": ["debugger", "admin"],
    "/incident timeline": ["qa", "debugger", "admin"],
}

def check_incident_command_permission(user: User, command: str) -> bool:
    allowed_roles = INCIDENT_COMMAND_PERMISSIONS.get(command, [])
    return user.role in allowed_roles
```

---

## DASHBOARD & METRICS

### Key Metrics to Track

```python
class DefectMetrics:
    """Metrics collected and exported to Cloud Monitoring."""
    
    # 1. Volume Metrics
    defects_total: int              # Total defects created
    defects_open: int               # Currently open defects
    defects_by_severity: dict       # {S1: 2, S2: 5, S3: 12, S4: 8}
    defects_by_impact_area: dict    # {backend: 8, bot: 3, db: 2, security: 1, devops: 4}
    defects_by_environment: dict    # {prod: 5, stage: 3, dev: 10}
    defects_by_status: dict         # {open: 5, triaged: 3, fixing: 2, testing: 1, closed: 10}
    
    # 2. SLA Metrics
    sla_compliance_s1: float        # % of S1 resolved within 4h
    sla_compliance_s2: float        # % of S2 resolved within 24h
    sla_compliance_s3: float        # % of S3 resolved within sprint
    sla_breaches: List[str]         # List of defect IDs with breached SLA
    
    # 3. Efficiency Metrics
    mttr_s1: float                  # Mean Time To Resolution (hours) for S1
    mttr_s2: float                  # MTTR for S2
    mttr_s3: float                  # MTTR for S3
    mtta: float                     # Mean Time To Acknowledgment
    mttf: float                     # Mean Time To Fix
    
    # 4. Quality Metrics
    regression_test_coverage: float # % of closed defects with regression tests
    rca_completion_rate: float      # % of S1/S2 with completed RCA
    defects_reopened: int           # Count of defects moved from resolved/closed back to open
    
    # 5. Incident Metrics
    break_glass_incidents: int      # Count of break-glass sessions that created defects
    production_incidents: int       # Count of prod defects
    security_incidents: int         # Count of security-related defects
    
    # 6. Trend Metrics
    defects_created_today: int
    defects_created_this_week: int
    defects_created_this_month: int
    defect_creation_trend: str      # "increasing", "stable", "decreasing"
    
    # 7. Team Metrics
    defects_per_agent: dict         # {backend_engineer: 8, qa: 5, bot_engineer: 3}
    avg_defects_per_agent: float
    agent_workload: dict            # {backend_engineer: {assigned: 3, in_progress: 2, resolved: 10}}
```

### Dashboard Layout (Cloud Monitoring)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  INKA Admin — Defect Management Dashboard                               │
│  Last Updated: 2026-02-22 17:30 UTC                                     │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┬──────────────────────────────┐
│ CRITICAL ALERTS             │ STATUS OVERVIEW              │
├─────────────────────────────┼──────────────────────────────┤
│                             │                              │
│ 🔴 S1 OPEN: 2              │ Total Defects: 42            │
│   - Double booking issue    │ Open: 5                      │
│   - Payment processing      │ Triaged: 3                   │
│                             │ Fixing: 2                    │
│ ⚠️ SLA BREACHES: 1          │ Testing: 1                   │
│   - S2 breach (26h/24h)     │ Closed: 31                   │
│                             │                              │
└─────────────────────────────┴──────────────────────────────┘

┌─────────────────────────────┬──────────────────────────────┐
│ SEVERITY BREAKDOWN          │ IMPACT AREA                  │
├─────────────────────────────┼──────────────────────────────┤
│                             │                              │
│ S1: 🔴 2 (5%)              │ Backend:  8 (19%)            │
│ S2: 🟠 5 (12%)             │ Bot:      3 (7%)             │
│ S3: 🟡 12 (29%)            │ Database: 2 (5%)             │
│ S4: ⚪ 23 (55%)            │ Security: 1 (2%)             │
│                             │ DevOps:   4 (10%)            │
│                             │ Unknown:  24 (57%)          │
│                             │                              │
└─────────────────────────────┴──────────────────────────────┘

┌─────────────────────────────┬──────────────────────────────┐
│ ENVIRONMENT DISTRIBUTION    │ PERFORMANCE METRICS          │
├─────────────────────────────┼──────────────────────────────┤
│                             │                              │
│ Production: 5 (12%)         │ MTTR S1: 3.2h (target: 4h)  │
│ Staging:    3 (7%)          │ MTTR S2: 18.5h (target: 24h)│
│ Dev:        34 (81%)        │ MTTA:    45min               │
│                             │ RCA Completion: 92%          │
│                             │ Regression Tests: 88%        │
│                             │                              │
└─────────────────────────────┴──────────────────────────────┘

┌─────────────────────────────┬──────────────────────────────┐
│ TREND (30 DAYS)             │ TEAM WORKLOAD                │
├─────────────────────────────┼──────────────────────────────┤
│                             │                              │
│ Defects Created: 156        │ Backend Engineer: 5 active   │
│ Trend: ⬆️ +8% (vs prior mo) │ Bot Engineer:     1 active   │
│ Velocity: 5.2/day           │ DevOps:           2 active   │
│ Closure Rate: 4.1/day       │ QA Automation:    1 active   │
│ Backlog Aging: 12 days avg  │                              │
│                             │                              │
└─────────────────────────────┴──────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ RECENT ACTIVITY (Last 10 Events)                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 17:30 — S1 Double Booking → TRIAGED (Manager)              │
│ 17:15 — S2 Slow Reports → Agents Assigned (Backend + QA)   │
│ 17:00 — S1 RCA Completed (Manager)                         │
│ 16:45 — Regression test added (Backend Engineer)            │
│ 16:30 — S3 Typo fix merged (Backend Engineer)               │
│ ...                                                          │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ ALERTS & ACTIONS                                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ ⚠️ S1 Double Booking open > 1h — Escalate to CTO?           │
│ ⚠️ S2 Payment Processing open > 2h — Assign backup dev      │
│ ℹ️ Regression test coverage < 90% — Team action item        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### API Endpoint for Metrics

```python
@router.get("/api/v1/defects/metrics/summary")
def get_metrics_summary(
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=90)
) -> MetricsSummary:
    """
    Get aggregated defect metrics for dashboard.
    Cacheable for 5 minutes.
    """
    from datetime import datetime, timedelta, timezone
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Query metrics
    all_defects = db.query(Defect).filter(Defect.created_at >= cutoff_date).all()
    
    s1_defects = [d for d in all_defects if d.severity == DefectSeverity.S1]
    s2_defects = [d for d in all_defects if d.severity == DefectSeverity.S2]
    
    # Calculate SLA compliance
    def check_sla(defects, hours):
        if not defects:
            return 100.0
        compliant = [d for d in defects if d.resolved_at and 
                    (d.resolved_at - d.detected_at).total_seconds() <= hours * 3600]
        return (len(compliant) / len(defects)) * 100
    
    sla_s1 = check_sla(s1_defects, 4)
    sla_s2 = check_sla(s2_defects, 24)
    
    return MetricsSummary(
        total_defects=len(all_defects),
        by_severity={
            "S1": len([d for d in all_defects if d.severity == DefectSeverity.S1]),
            "S2": len([d for d in all_defects if d.severity == DefectSeverity.S2]),
            "S3": len([d for d in all_defects if d.severity == DefectSeverity.S3]),
            "S4": len([d for d in all_defects if d.severity == DefectSeverity.S4]),
        },
        by_impact_area={...},
        by_status={...},
        sla_compliance={"S1": sla_s1, "S2": sla_s2},
        mttr={...},
        regression_coverage=...,
        rca_completion=...
    )
```

---

## CI/CD ENFORCEMENT

### CI/CD Rules & Policies

```yaml
# .github/workflows/defect-enforcement.yml
name: Defect Enforcement

on: [push, pull_request]

jobs:
  defect-regression-test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Extract Defect ID from Branch/Commit
        id: defect
        run: |
          # Parse defect ID from branch name: feature/DEF-123-fix-issue
          DEFECT_ID=$(git rev-parse --abbrev-ref HEAD | grep -oE 'DEF-[0-9a-f-]+' || echo "")
          if [ -z "$DEFECT_ID" ]; then
            # Try commit message
            DEFECT_ID=$(git log -1 --pretty=%B | grep -oE 'DEF-[0-9a-f-]+' || echo "")
          fi
          echo "defect_id=$DEFECT_ID" >> $GITHUB_OUTPUT
      
      - name: Validate Regression Test Exists
        if: steps.defect.outputs.defect_id != ''
        run: |
          echo "Checking for regression test for ${{ steps.defect.outputs.defect_id }}"
          
          # Search for regression test mentioning this defect
          if grep -r "Regression.*${{ steps.defect.outputs.defect_id }}" tests/ --include="*.py"; then
            echo "✓ Regression test found"
          else
            echo "✗ No regression test found for ${{ steps.defect.outputs.defect_id }}"
            echo "Please add a test with comment: # Regression Test: ${{ steps.defect.outputs.defect_id }}"
            exit 1
          fi
      
      - name: Run Regression Tests
        run: |
          pytest tests/ -k "regression" -v --tb=short
      
      - name: Test Coverage
        run: |
          pytest --cov=apps --cov=libs --cov-report=term-missing --cov-fail-under=80
      
      - name: Lint & Type Check
        run: |
          ruff check .
          mypy apps libs --strict

  block-s1-deployment:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Check for Open S1 Production Defects
        run: |
          # Query database for open S1 prod defects
          python scripts/check_open_s1_defects.py
          # Script exits with code 1 if S1 defects exist
      
      - name: Block Deployment if S1 Open
        if: failure()
        run: |
          echo "❌ Deployment blocked: Open S1 production defect(s) exist"
          exit 1
```

### Check Script

```python
# scripts/check_open_s1_defects.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from packages.core.domains.defects.models import Defect, DefectSeverity
from packages.db.session import get_db

def check_open_s1_defects():
    """
    Exit with code 1 if S1 production defects exist in OPEN/TRIAGED/ASSIGNED status.
    This blocks CI/CD deployments.
    """
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("⚠️ DATABASE_URL not set. Skipping S1 check.")
        return 0
    
    engine = create_engine(database_url)
    
    with Session(engine) as db:
        s1_open = db.query(Defect).filter(
            Defect.severity == DefectSeverity.S1,
            Defect.environment == "prod",
            Defect.status.in_(["open", "triaged", "assigned", "fixing"])
        ).all()
        
        if not s1_open:
            print("✓ No open S1 production defects. Deployment OK.")
            return 0
        
        print(f"❌ Found {len(s1_open)} open S1 production defect(s):")
        for defect in s1_open:
            print(f"   - {defect.title} (ID: {defect.id})")
            print(f"     Status: {defect.status.value}")
            print(f"     Created: {defect.detected_at}")
        
        return 1

if __name__ == "__main__":
    exit_code = check_open_s1_defects()
    exit(exit_code)
```

### Deployment Workflow (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  pre-deploy-checks:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      
      - name: Check S1 Defects Block
        run: python scripts/check_open_s1_defects.py
      
      - name: Verify CI Green
        run: |
          # Ensure all tests, lints, coverage passed
          pytest --tb=short --strict-markers
          ruff check .
          mypy .
  
  deploy:
    needs: pre-deploy-checks
    runs-on: ubuntu-latest
    
    steps:
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy inka-api \
            --source . \
            --region europe-west1 \
            --allow-unauthenticated
      
      - name: Smoke Tests
        run: |
          # Run basic smoke tests on deployed API
          python scripts/smoke_tests.py
      
      - name: Monitor for Regressions (30 min)
        run: |
          # Monitor error rates, latency for 30 minutes
          python scripts/monitor_deployment.py --duration 30
```

---

## DEFINITION OF DONE

A defect may transition from **RESOLVED** to **CLOSED** only if **ALL** of the following criteria are met:

### Mandatory (ALL Required)

- [ ] **Root Cause Documented** (S1/S2 only)
  - [ ] `root_cause` field has >= 100 characters
  - [ ] Describes "what failed", "why", "why not detected"
  - [ ] DefectEvent "rca_completed" exists in timeline
  
- [ ] **Fix Merged**
  - [ ] `fix_commit_sha` field populated with valid commit hash
  - [ ] Commit exists in main branch
  - [ ] Pull request reviewed and approved
  
- [ ] **Regression Test Added**
  - [ ] `regression_test_added = true`
  - [ ] Test file location in `metadata_json.regression_test_file`
  - [ ] Test name in `metadata_json.regression_test_name`
  - [ ] Test FAILS without fix, PASSES with fix (verified)
  - [ ] Test integrated into CI pipeline
  
- [ ] **CI Green**
  - [ ] All unit tests pass
  - [ ] All integration tests pass
  - [ ] Linters pass (ruff)
  - [ ] Type checks pass (mypy)
  - [ ] Code coverage >= 80%
  - [ ] No new security warnings (bandit)
  
- [ ] **QA Sign-off**
  - [ ] QA has verified fix in staging environment
  - [ ] Test scenarios match product requirements
  - [ ] No regressions detected in related features
  
- [ ] **Audit Trail Complete**
  - [ ] DefectEvent timeline shows complete flow
  - [ ] All state transitions audited
  - [ ] Assigned agents have signed off
  
- [ ] **For Production Defects (S1/S2)**
  - [ ] Monitoring stable for 24 hours
  - [ ] No escalations during monitoring period
  - [ ] Error rates < baseline

### Conditional (If Applicable)

- [ ] **Runbook Updated**
  - [ ] If incident response documented → runbook section updated
  - [ ] If new operational procedure → runbook created
  - [ ] If disaster recovery affected → recovery procedure updated
  
- [ ] **Deployment Cutoff**
  - [ ] If S1 + prod: No more deployments until CLOSED
  - [ ] If S2 + prod: May deploy, but defect tracked
  
- [ ] **Related Incidents Resolved**
  - [ ] If `related_incidents` list not empty:
  - [ ] All related defects also resolved/closed
  - [ ] Or explicitly marked as independent
  
- [ ] **Break-glass Investigation** (if applicable)
  - [ ] If break-glass session involved: RCA includes misuse analysis
  - [ ] Access logs reviewed
  - [ ] Policy violation (if any) documented

### Validation Before Closure

```python
def validate_defect_dod(db: Session, defect: Defect) -> List[str]:
    """
    Check all DoD criteria. Return list of failed checks.
    Empty list = all criteria met = safe to close.
    """
    failures = []
    
    # 1. Root Cause (S1/S2 only)
    if defect.severity in [DefectSeverity.S1, DefectSeverity.S2]:
        if not defect.root_cause or len(defect.root_cause) < 100:
            failures.append("Root cause missing or too short (< 100 chars)")
        
        rca_events = db.query(DefectEvent).filter(
            DefectEvent.defect_id == defect.id,
            DefectEvent.event_type == "rca_completed"
        ).all()
        if not rca_events:
            failures.append("RCA event not found in timeline")
    
    # 2. Fix Merged
    if not defect.fix_commit_sha:
        failures.append("Fix commit SHA not recorded")
    else:
        # Verify commit exists in Git
        try:
            commit = verify_commit_in_main(defect.fix_commit_sha)
            if not commit:
                failures.append("Commit not found in main branch")
        except Exception as e:
            failures.append(f"Commit verification failed: {e}")
    
    # 3. Regression Test
    if not defect.regression_test_added:
        failures.append("Regression test not added")
    else:
        test_file = defect.metadata_json.get("regression_test_file")
        test_name = defect.metadata_json.get("regression_test_name")
        if not test_file or not test_name:
            failures.append("Regression test location missing")
    
    # 4. Monitoring (S1/S2 + prod only)
    if defect.severity in [DefectSeverity.S1, DefectSeverity.S2] and defect.environment == "prod":
        if not defect.resolved_at:
            failures.append("Defect must be RESOLVED before CLOSED")
        
        hours_resolved = (datetime.now(timezone.utc) - defect.resolved_at).total_seconds() / 3600
        if hours_resolved < 24:
            failures.append(f"Must be stable for 24h. Currently: {hours_resolved:.1f}h")
    
    return failures

def can_close_defect(db: Session, defect: Defect) -> bool:
    """Check if defect can be closed (DoD met)."""
    failures = validate_defect_dod(db, defect)
    return len(failures) == 0

# Usage in API
@router.patch("/api/v1/defects/{id}")
def update_defect(defect_id: UUID, payload: DefectUpdate, db: Session = Depends(get_db)):
    defect = crud.get_defect(db, defect_id)
    
    if payload.status == DefectStatus.CLOSED:
        failures = validate_defect_dod(db, defect)
        if failures:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Cannot close defect. DoD criteria not met:",
                    "failures": failures
                }
            )
    
    # Proceed with update
    ...
```

---

## RISK ANALYSIS

### Key Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| **S1 Defect Misclassified** | False urgency, wasted resources or missed critical issue | Medium | Severity matrix + manager review + automated alerts |
| **Defect Duplication** | Wasted effort, conflicting fixes | Medium | Correlation ID field + search on creation + dedupe service |
| **RCA Never Completed** | Repeat incidents | High | Enforce in API validation + deadline + escalation |
| **Regression Test Skipped** | Same bug reoccurs | Medium | CI enforcement + DoD block + metrics dashboard |
| **Break-glass Misused** | Unauthorized changes, audit trail gap | Low | Break-glass policy + full audit logging + 24h review |
| **S1 Deployment Allowed** | Cascading failures | Low | CI check + deployment pipeline block |
| **Data Loss in Defect Log** | Historical record lost | Low | PostgreSQL backups + audit log retention |
| **Defect SLA Missed** | Poor incident response | Medium | Monitoring alerts + escalation rules + metrics |
| **Telegram Bot Offline** | Incident intake blocked | Low | Bot health monitoring + fallback API endpoint |
| **Agent Burnout** | Quality degradation | Medium | Load balancing + priority queue + on-call rotation |

---

## RUNBOOKS

### Runbook: S1 Production Outage

```markdown
## INCIDENT: Production Outage (S1)

### Detection
- Monitoring alert: Error rate > 10% OR latency > 1s OR availability < 95%
- Auto-created defect with ID [DEFECT_ID]
- Telegram admin group notified

### Immediate Actions (0-15 min)
1. Acknowledge defect in Telegram: `/incident status [DEFECT_ID]`
2. Page on-call engineer: `@backend_engineer @devops_sre`
3. Declare SEV-1 in #incidents Slack channel
4. Assess impact: affected users, services, data
5. Begin triage: move defect to TRIAGED status

### Investigation Phase (15-60 min)
1. Check recent deployments: `gcloud run services list` + git log
2. Review error logs: Cloud Logging, structured logs
3. Check infrastructure: Cloud Run, Cloud SQL, Redis
4. Assess data: any corruption or anomalies?
5. Document timeline in defect.metadata_json

### Mitigation (60-240 min)
1. **Option A: Rollback**
   - Rollback to last known good revision
   - Monitor error rates for 30 min
   - If stable, close incident with "reverted" root cause

2. **Option B: Hotfix**
   - Begin coding fix immediately
   - Merge to main with DEFECT_ID in commit message
   - Deploy to staging for 10-min smoke test
   - Deploy to production
   - Monitor for 24h

3. **Option C: Workaround**
   - Disable problematic feature
   - Document workaround
   - Schedule fix for next release
   - Update defect with workaround details

### Post-Incident (24h)
1. Complete RCA: timeline + root cause + why missed
2. Add regression test to CI
3. Update runbook based on lessons learned
4. Hold blameless postmortem with team
5. Schedule preventive actions
6. Close defect only after 24h stable monitoring

### Escalation
- 30 min: No owner assigned → escalate to CTO
- 2h: Still fixing → activate war room
- 4h: Still open → all-hands investigation
```

### Runbook: Break-glass Audit Review

```markdown
## INCIDENT: Break-Glass Session Suspicious Activity

### Detection
- Break-glass session created for reason: "Debug booking issue"
- User actions recorded: Modified 5 bookings, Changed user role
- Potential misuse: Unauthorized scope change

### Review Workflow
1. Query audit log: SELECT * FROM audit_log WHERE actor_id = [USER_ID] AND created_at > [SESSION_START]
2. Get break-glass details: SELECT * FROM debug_session WHERE id = [SESSION_ID]
3. Review actions in context:
   - Were actions consistent with stated reason?
   - Were sensitive tables accessed?
   - Were PII accessed?

### Decision
- **Authorized:** Actions consistent with debugging reason → No action
- **Unauthorized:** Actions exceed scope → Create S1 security defect
- **Ambiguous:** Escalate to security team + manager

### Security Defect Workflow
1. Create S1 security defect: "Unauthorized break-glass activity by [USER]"
2. Assign to security + devops teams
3. Immediate investigation:
   - What data was accessed/modified?
   - Who was affected?
   - Was PII exposed?
4. RCA includes:
   - Why break-glass policy not enforced
   - Why audit logs not reviewed in real-time
   - Why role not revoked after session
5. Preventive:
   - Auto-revoke break-glass privileges
   - Real-time audit alerts
   - Update break-glass policy
```

---

## Conclusion

This Defect & Incident Orchestration System provides:

✅ **Structured defect management** — Intake, triage, fix, test, close  
✅ **Severity-driven SLAs** — S1 critical, S2 high, S3 medium, S4 low  
✅ **Mandatory RCA** — Every S1/S2 must document root cause  
✅ **Regression prevention** — Every fix requires automated test  
✅ **Telegram integration** — Incident reporting & status tracking  
✅ **Audit trail** — Complete lifecycle audit logging  
✅ **Agent routing** — Automatic assignment based on impact area  
✅ **CI/CD enforcement** — S1 blocks deployments, tests required  
✅ **Metrics & dashboard** — SLA tracking, MTTR, trend analysis  
✅ **Production safety** — Formal DoD, monitoring, escalation rules  

**No defect is left behind. Every incident is tracked, fixed, tested, and learned from.**
