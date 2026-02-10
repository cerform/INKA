# INKA Architecture

## Overview

INKA is a monorepo containing three main services for tattoo salon administration:
1. **API** - FastAPI REST backend
2. **Bot** - Telegram bot for staff
3. **Admin** - React web panel

## System Architecture

```
┌─────────────┐         ┌─────────────┐
│   Telegram  │────────▶│     Bot     │
│   Client    │         │   Service   │
└─────────────┘         └──────┬──────┘
                               │
                               │ HTTP
                               ▼
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │────────▶│     API     │────────▶│  PostgreSQL │
│   (Admin)   │         │   Service   │         │  Database   │
└─────────────┘         └──────┬──────┘         └─────────────┘
                               │
                               │
                               ▼
                        ┌─────────────┐
                        │    Redis    │
                        │   (Cache)   │
                        └─────────────┘
```

## Module Boundaries

### Domain Layer (`libs/core/`)
Pure business logic, framework-agnostic:
- `domains/bookings/` - Booking management, conflict detection
- `domains/clients/` - Client profiles
- `domains/masters/` - Master availability
- `domains/auth/` - RBAC, break-glass sessions
- `domains/support/` - PII masking, diagnostics

### Application Layer (`apps/`)
Service-specific orchestration:
- `api/` - FastAPI routes, request/response handling
- `bot/` - Telegram handlers, conversation flows
- `admin/` - React components, state management

### Infrastructure Layer (`libs/`)
External integrations:
- `database/` - SQLAlchemy models, Alembic migrations
- `observability/` - Structured logging, correlation IDs

## Data Flow

### Booking Creation (Example)

```
User (Telegram) → Bot Handler → API Endpoint → Domain Logic → Database
                                      ↓
                                 Audit Log
                                      ↓
                                 Redis Cache
```

## Security

- **Authentication**: JWT tokens (API), Telegram user_id (Bot)
- **Authorization**: Role-based (admin, manager, master, qa, debugger)
- **PII Protection**: Role-based masking for phone numbers, notes
- **Break-Glass**: Temporary elevated access with audit trail

## Deployment

### Development
- Docker Compose with hot-reload
- Local PostgreSQL + Redis

### Production (Google Cloud)
- API: Cloud Run (europe-west1)
- Bot: Cloud Run (europe-west1)
- Database: Cloud SQL PostgreSQL
- Secrets: Secret Manager
- CI/CD: GitHub Actions

## Technology Stack

**Backend:**
- FastAPI 0.109
- SQLAlchemy 2.0
- Alembic (migrations)
- aiogram 3.3 (Telegram)

**Frontend:**
- Next.js 14
- React 18
- TypeScript

**Infrastructure:**
- PostgreSQL 15
- Redis 7
- Docker
- Terraform (IaC)

## Design Decisions

See [ADRs](adr/) for detailed architecture decision records.
