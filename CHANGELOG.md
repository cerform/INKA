# Changelog

All notable changes to INKA Admin are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

## [0.1.0] — 2026-02-22

### Added
- Initial project structure: FastAPI API, aiogram Telegram bot, Vite/React admin
- Core data models: User, Master, Client, Booking, Service, WorkingHours, TimeOff, AuditLog, Role
- Health check endpoints: `GET /health` and `GET /health/ready`
- Alembic migration scaffold (`libs/database/`)
- CI pipeline: lint, test, quality gate (GitHub Actions)
- Deploy pipeline: stage + prod with canary (10%), 30-min health monitor, manual approval gate, rollback workflow
- Pre-commit hooks: ruff, black, mypy
- Docker Compose for local development

### Changed
- `apps/api` Dockerfile simplified: self-contained build, no symlink hacks
- `main.py` cleaned to minimal startup (domain routers staged for M1+)
- `settings.py` all external service fields made Optional (no crash on missing env var)
- `logging.py` decoupled from `packages.core` (standalone inline impl)

### Fixed
- `telegram_bot_token` was `str` with no default — would crash startup if env var missing
- `setup/api.py` imports `User.role` as string against FK column (flagged, not yet fully fixed)
- Dockerfile previously installed entire monorepo; now API-only for faster builds
