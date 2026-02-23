# INKA Quick Reference Guide

**For:** Project managers, engineers, stakeholders  
**Updated:** 2026-02-22

---

## One-Page Summary

| Aspect | Status |
|--------|--------|
| **Current State** | Skeleton (models, CI/CD, auth framework) |
| **Next Milestone** | M0 (Week 2): Fix imports, scaffold calendar, enable CI/CD |
| **First PRs** | 10 PRs planned; ~7.5 days effort |
| **Go-Live Target** | Week 13 (12 weeks from now) |
| **Key Risks** | Calendar sync conflicts, double-booking, DST transitions, data leaks |
| **Timeline** | M0 (2w) → M1 (3w) → M2 (3w) → M3 (2w) → M4 (1w) → M5 (2w+) |

---

## Key Documents

### Planning & Strategy
- [PRODUCTION_DELIVERY_PLAN.md](./PRODUCTION_DELIVERY_PLAN.md) — Full roadmap (Milestones M0–M5, Architecture, Acceptance Criteria)
- [FIRST_10_PRs.md](./FIRST_10_PRs.md) — Detailed PR specs (next 2 weeks of work)
- [RISKS_AND_MITIGATIONS.md](./RISKS_AND_MITIGATIONS.md) — Risk register with mitigations

### Development Docs
- [docs/development/SETUP.md](./docs/development/SETUP.md) — Local dev setup
- [docs/operations/DEPLOYMENT.md](./docs/operations/DEPLOYMENT.md) — Deployment guide
- [CHANGELOG.md](./CHANGELOG.md) — Release notes
- [STRUCTURE.md](./STRUCTURE.md) — Directory layout

### Architecture
- [docs/architecture/README.md](./docs/architecture/README.md) — System design
- [docs/quality-score-agent.md](./docs/quality-score-agent.md) — Quality metrics & gating

---

## Quick Commands

### Local Development

```bash
# Start all services
make dev

# Run tests
make test

# Format code
make format

# Migrations
make migrate
make migrate-create MSG="description"

# View logs
docker compose logs -f api
```

### Git & PRs

```bash
# Start new feature
git checkout -b feature/my-feature

# After changes
git add .
git commit -m "feat: add feature"
git push origin feature/my-feature

# Create PR
# → GitHub → New Pull Request
# → GitHub Actions runs CI automatically
# → If green, request review
# → Reviewer approves → Merge
```

### Database

```bash
# Connect
psql postgresql://inka:inka@localhost:5432/inka_dev

# List tables
\dt

# Sample query
SELECT * FROM tenant LIMIT 10;

# Check migrations
alembic current
alembic upgrade head
```

### Docker

```bash
# Rebuild
docker compose down -v
docker compose up --build

# Shell into container
docker compose exec api bash

# Check logs
docker compose logs api --tail 50
```

---

## Project Roles & Responsibilities

| Role | Responsibility | Examples |
|------|-----------------|----------|
| **Backend Lead** | Core business logic, API, database | Calendar engine, booking CRUD, multi-tenant isolation |
| **Bot Lead** | Telegram bot, NLP, LLM integration | Handlers, state machines, LLM parsing |
| **Frontend Lead** | React UI, admin panel, real-time updates | Calendar view, forms, WebSocket |
| **DevOps** | Infrastructure, CI/CD, monitoring | Terraform, Cloud Run, Secret Manager, alerting |
| **QA / Defect Orchestrator** | Testing, quality gates, defect tracking | Test coverage, incident response, quality score |
| **Deployment Governor** | Release decisions, gating, rollback | Approval, monitoring, incidents |
| **Compliance Authority** | Security, audit, GDPR, PII | Data isolation, masking, retention policies |

---

## Milestone Checklist

### M0 (Week 1–2): Skeleton ✓

- [ ] PR-1: Import paths fixed
- [ ] PR-2: External service configs Optional
- [ ] PR-3: DB connection pooling configured
- [ ] PR-4: Calendar slot engine skeleton
- [ ] PR-5: DB indexes + migration
- [ ] PR-6: Tenant isolation middleware
- [ ] PR-7: User.role FK fixed
- [ ] PR-8: Terraform scaffold
- [ ] PR-9: CI enhanced (security, SBOM, coverage)
- [ ] PR-10: Documentation complete

**Acceptance:** All tests ≥50%, zero S1/S2, quality score ≥70

---

### M1 (Week 3–5): Calendar Engine MVP

**Deliverables:**
- Slot generation algorithm (DST-aware)
- Conflict detection service
- `/api/v1/calendar/slots` endpoint
- Working hours + time-off CRUD
- Redis caching (5-min TTL)
- 20+ integration tests

**Acceptance:** Slots generated correctly, no double-booking, test coverage ≥75%

---

### M2 (Week 6–8): Booking Flow & Notifications

**Deliverables:**
- Booking CRUD endpoints
- Booking state machine (PENDING → CONFIRMED → COMPLETED)
- Google Calendar sync (one-way: INKA → Google)
- SMS/Telegram reminders
- Background job queue
- Telegram bot handlers (`/book`, `/cancel`, `/reschedule`)

**Acceptance:** End-to-end booking works, notifications >99% delivery, test coverage ≥80%

---

### M3 (Week 9–10): Admin UI Calendar

**Deliverables:**
- React calendar component (month/week/day views)
- Real-time updates (WebSocket/SSE)
- Quick create/edit booking modals
- Master availability sidebar
- Mobile-responsive design
- E2E tests for critical flows

**Acceptance:** UI fully functional, mobile-responsive, test coverage ≥80%, quality score ≥85

---

### M4 (Week 11): Onboarding Wizard & Multi-Tenant

**Deliverables:**
- Onboarding wizard (4-step form)
- Tenant creation + initialization
- RBAC enforcement (Admin, Manager, Master, QA, Debugger)
- Break-glass session logic
- Google Workspace domain config
- Onboarding checklist UI

**Acceptance:** New tenant can self-onboard, multi-tenant isolation verified

---

### M5 (Week 12+): Inventory, Analytics, Hardening

**Deliverables:**
- Inventory BOM + stock depletion
- Purchase order tracking
- Reorder alerts (Slack/email)
- Analytics dashboard (revenue, bookings by master, inventory turnover)
- Observability (structured logging, tracing, metrics)
- PII masking (role-based)
- GDPR delete endpoint
- Load testing + hardening
- Runbooks for common incidents

**Acceptance:** All features shipped, observability live, security audit passed, quality score ≥90

---

## Decision Framework

### Should We Build or Buy?

| Component | Build | Buy | Recommendation |
|-----------|-------|-----|-----------------|
| **Calendar UI** | 2 weeks | FullCalendar license | **Buy** (FullCalendar, already in deps) |
| **Slot Engine** | 1 week | None available | **Build** |
| **Payment Processing** | 2 weeks | Stripe / Wise | **Buy** (Stripe, M5) |
| **LLM Integration** | 3 days | OpenAI / Anthropic API | **Buy** (OpenAI, optional M2) |
| **SMS Notifications** | 1 day | Twilio / Vonage | **Buy** (Twilio fallback) |
| **Google Calendar Sync** | 3 days | None (must use API) | **Build** |
| **Monitoring/Logging** | 2 days | DataDog / New Relic | **Buy** (optional, Cloud Monitoring free) |

---

## Dependency Map

```
M0 (imports fixed, config, indexing, middleware)
  ↓
M1 (calendar engine, slot generation)
  ↓
M2 (booking CRUD, sync, notifications) ← Depends on M1
  ├─ Bot handlers ← Depends on booking API
  ├─ Google Calendar sync ← Depends on booking API
  └─ Notifications ← Depends on job queue
  ↓
M3 (admin UI calendar) ← Depends on M2 API
  ↓
M4 (onboarding wizard) ← Depends on M0, M1, M2, M3
  ↓
M5 (inventory, analytics, hardening) ← Depends on M4, M1–M3
```

---

## Effort Estimation

| Phase | Backend | Frontend | DevOps | QA | Total |
|-------|---------|----------|--------|-----|-------|
| **M0** (2w) | 3d | 0d | 2d | 1d | 6d |
| **M1** (3w) | 8d | 0d | 1d | 2d | 11d |
| **M2** (3w) | 7d | 2d | 1d | 2d | 12d |
| **M3** (2w) | 3d | 8d | 0d | 2d | 13d |
| **M4** (1w) | 4d | 2d | 1d | 1d | 8d |
| **M5** (2w) | 4d | 2d | 2d | 2d | 10d |
| **Total** | **29d** | **14d** | **7d** | **10d** | **60d** |

**Assumptions:**
- Team size: 2 backend + 1 frontend + 1 DevOps
- 5-day weeks, 8-hour days = 20 working days/month
- Parallel work reduces calendar time (60 person-days ÷ 4 people ≈ 15 weeks)

---

## Quality Gates

### Per-Merge Quality Gate (Every PR)

| Gate | Threshold | Action |
|------|-----------|--------|
| **Lint** | Zero errors | Block merge if failed |
| **Tests** | Pass (no failures) | Block merge if failed |
| **Coverage** | ≥50% (MVP), ≥80% (production) | Warn, allow merge with comment |
| **Security** | Zero critical vulns | Block merge if critical found |
| **Type Checking** | Zero mypy errors (warnings OK) | Warn, allow merge |

### Per-Release Quality Gate (Deploy to Prod)

| Gate | Threshold | Action |
|------|-----------|--------|
| **Quality Score** | ≥90 | Block deploy if <90 |
| **S1 Defects** | Zero | Block deploy if any open |
| **S2 Defects** | ≤0 (prod) or ≤2 (stage) | Block deploy if exceeded |
| **Test Coverage** | ≥85% | Block deploy if <85% |
| **Security Scan** | Zero critical, ≤3 high | Block deploy if exceeded |
| **Manual Approval** | 2 reviewers (prod), 1 (stage) | Require before deploy |

---

## Communication Plan

### Weekly Sync (Monday 10:00 UTC)

**Duration:** 30 min  
**Attendees:** Team leads (Backend, Frontend, DevOps, QA), PM  
**Agenda:**
1. Progress on current milestone (5 min)
2. Blockers & dependencies (5 min)
3. Risks & mitigation status (5 min)
4. Upcoming week priorities (5 min)
5. Any incidents or escalations (5 min)

**Output:** Slack summary + calendar update

### Daily Standup (Async via Slack)

**Time:** 9:00 UTC (post in #dev-updates)  
**Format:**
```
@backend-lead: Done: PR-3 merged. Doing: PR-4 calendar skeleton. Blocker: None.
@frontend-lead: Done: Setup vite. Doing: Project structure. Blocker: Waiting for API docs.
@devops-lead: Done: Terraform scaffold. Doing: Cloud SQL setup. Blocker: GCP quotas.
```

### Incident Response (Slack + Call)

If P1/P2 incident:
1. Create incident channel: `#incident-YYYY-MM-DD-HH`
2. Call on Slack (3-way: Backend + DevOps + PM)
3. Root cause analysis within 24 hours
4. Post-mortem in `docs/operations/incidents/`

---

## Common Questions

### Q: When can we open to customers?

**A:** Week 13 (M5 complete). Beta launch to 10 salons in week 11 (during M4).

### Q: Do we need all features for production?

**A:** MVP = M0 + M1 + M2 + M3 (calendar-first booking system).  
Nice-to-have = M4 (onboarding wizard) + M5 (inventory).  
For first 10 customers, we can onboard manually; wizard in M4.

### Q: What if we find critical bugs in M3/M4?

**A:** Hotfix branches off main; deploy immediately (no gating).  
Document in CHANGELOG; add regression test.

### Q: Can we parallelize M1 & M2?

**A:** Partially. Frontend can start M2 API stubs while Backend does M1 slot engine.  
Sync endpoints need M1 complete, so some serialization.

### Q: What's the SLA for first production month?

**A:** 99.5% uptime (4.3 hours downtime/month allowed).  
API latency p95 < 500ms.  
Booking success rate > 99%.

### Q: Who approves production deployments?

**A:** Deployment Governor (2 approvals required).  
Quality Score Agent checks gating rules automatically.

### Q: How do we rollback if production breaks?

**A:** Cloud Run automatic rollback if health checks fail.  
Manual rollback: GitHub Actions "Rollback" button → reverts to previous revision.  
Database rollback: Alembic downgrade (if migration caused issue).

---

## Useful Links

- **GitHub Repo:** https://github.com/yourusername/inka
- **GCP Project:** https://console.cloud.google.com/projects/YOUR_PROJECT_ID
- **Architecture Diagram:** [docs/architecture/README.md](./docs/architecture/README.md)
- **API Documentation:** [docs/development/API.md](./docs/development/API.md)
- **Deployment Guide:** [docs/operations/DEPLOYMENT.md](./docs/operations/DEPLOYMENT.md)
- **Incident Runbooks:** [docs/operations/runbooks/](./docs/operations/runbooks/)

---

## Contacts

| Role | Name | Slack | Email |
|------|------|-------|-------|
| **Project Manager** | TBD | @pm | pm@company.com |
| **Backend Lead** | TBD | @backend-lead | backend@company.com |
| **Frontend Lead** | TBD | @frontend-lead | frontend@company.com |
| **DevOps Lead** | TBD | @devops-lead | devops@company.com |
| **QA Lead** | TBD | @qa-lead | qa@company.com |
| **Security Officer** | TBD | @security | security@company.com |

---

## Quick Troubleshooting

### Docker won't start

```bash
docker compose down -v
docker system prune
docker compose up --build
```

### Tests failing

```bash
make clean
pip install -e .[dev]
pytest --verbose
```

### Database issues

```bash
psql postgresql://inka:inka@localhost:5432/inka_dev
\dt  # List tables
SELECT * FROM tenant;
```

### Git merge conflicts

```bash
git status  # See conflicts
# Edit files to resolve
git add .
git commit -m "Resolve merge conflicts"
git push
```

### Port already in use

```bash
lsof -i :8000  # See process using port 8000
kill -9 <PID>
```

---

## Appendix: File Locations

| What | Where |
|------|-------|
| API code | `apps/api/src/app/` |
| Bot code | `apps/bot/src/` |
| Admin UI | `apps/admin/src/` |
| Core domain logic | `libs/core/src/domains/` |
| Database models | `libs/core/src/models/` |
| Migrations | `libs/database/alembic/versions/` |
| Tests | `apps/*/tests/`, `libs/*/tests/` |
| Docs | `docs/` |
| CI/CD workflows | `.github/workflows/` |
| Terraform config | `infra/terraform/` |
| Docker Compose | `docker-compose.yml` |
| Config | `libs/core/src/config.py`, `.env` |

---

**Version:** 1.0  
**Last Updated:** 2026-02-22  
**Status:** Ready for Team Use
