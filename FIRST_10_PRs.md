# INKA First 10 PRs Implementation Roadmap

**Target:** Complete M0 (Deployable Skeleton) in 2 weeks  
**Status:** Ready for execution  
**Last Updated:** 2026-02-22

---

## PR-1: Fix Import Path Consistency

**Branch:** `fix/import-paths`  
**Objective:** Standardize all imports from `packages.core` → `libs.core`

### Changes Required

```python
# BEFORE (throughout codebase)
from packages.core.config import settings
from packages.db.base_class import Base
from packages.core.domains.bookings.models import Booking

# AFTER
from libs.core.src.config import settings
from libs.database.src.base import Base
from libs.core.src.domains.bookings.models import Booking
```

### Files to Update

1. `apps/api/src/app.py` - Fix imports for config, models, logging
2. `apps/api/src/app/main.py` - Update router imports
3. `apps/api/src/app/deps/` - Fix database, auth dependencies
4. `apps/bot/src/main.py` - Fix config imports
5. `libs/core/src/services/` - All service files
6. `libs/core/src/domains/*/` - All domain imports
7. `libs/database/alembic/env.py` - Fix Base import
8. All test files `apps/*/tests/` and `libs/*/tests/`

### Acceptance Criteria

- [ ] All imports use `libs.*` namespace
- [ ] All test imports updated
- [ ] `python -m pytest --collect-only` succeeds (no import errors)
- [ ] `ruff check .` passes with zero import errors
- [ ] Local development `docker compose up` starts all services
- [ ] CI pipeline green (all workflows pass)

### Implementation Notes

Use IDE search-replace with regex:
```
Find: from packages\.(.+)
Replace: from libs.core.src.$1
```

Test after each file group to catch dependency issues early.

---

## PR-2: Make External Service Configs Optional (Graceful Degradation)

**Branch:** `fix/optional-service-configs`  
**Objective:** Prevent crashes when BOT_TOKEN, OPENAI_API_KEY, etc. are missing

### Changes Required

**File:** `libs/core/src/config.py`

```python
from typing import Optional

class Settings(BaseSettings):
    # BEFORE: Would crash if env var not set
    # TELEGRAM_BOT_TOKEN: str = "change-me"
    
    # AFTER: Graceful handling
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    
    # Add validation methods
    def check_service_available(self, service_name: str) -> bool:
        """Check if external service is configured."""
        service_keys = {
            "telegram": "TELEGRAM_BOT_TOKEN",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_OAUTH_CLIENT_SECRET",
            "stripe": "STRIPE_SECRET_KEY",
        }
        key = service_keys.get(service_name)
        if not key:
            return False
        value = getattr(self, key, None)
        return value is not None and value != ""
```

**File:** `apps/api/src/app.py`

```python
from apps.bot.main import bot

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting INKA Admin...")
    
    # Only set webhook if BOT_TOKEN configured
    if settings.check_service_available("telegram"):
        try:
            await bot.set_webhook()
        except Exception as e:
            logger.warning(f"Could not set Telegram webhook: {e}")
    else:
        logger.warning("Telegram bot not configured (BOT_TOKEN missing)")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    if settings.TELEGRAM_BOT_TOKEN:
        await bot.session.close()
```

**File:** `apps/api/src/app/main.py` (if exists)

```python
# Add startup checks
@app.on_event("startup")
async def startup():
    # Log available services
    services = {
        "telegram": settings.check_service_available("telegram"),
        "openai": settings.check_service_available("openai"),
        "google": settings.check_service_available("google"),
        "stripe": settings.check_service_available("stripe"),
    }
    logger.info(f"Available services: {services}")
```

### Acceptance Criteria

- [ ] API starts without BOT_TOKEN env var (logs warning, continues)
- [ ] API starts without OPENAI_API_KEY (graceful degradation)
- [ ] All service integration endpoints return 503 (Service Unavailable) if service not configured
- [ ] Tests pass with missing configs
- [ ] Docker Compose starts with minimal .env (no BOT_TOKEN required)
- [ ] CI green

### Testing

```python
# Test: API starts without BOT_TOKEN
def test_api_starts_without_bot_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    from apps.api.src.app import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    
    # Check that bot endpoints return 503
    response = client.post("/api/v1/telegram/webhook")
    assert response.status_code == 503 or response.status_code == 405
```

---

## PR-3: Add Database Connection Pooling Config (pgBouncer)

**Branch:** `fix/db-connection-pooling`  
**Objective:** Configure pgBouncer for connection pooling; prepare for Cloud Run deployment

### Changes Required

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    # ... existing config ...
    ports:
      - "5432:5432"  # Direct access for local dev
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U inka -d inka_dev"]
      interval: 10s
      timeout: 5s
      retries: 5

  pgbouncer:
    image: pgbouncer:1.22-alpine
    container_name: inka-pgbouncer
    ports:
      - "6432:6432"  # pgBouncer port
    environment:
      DATABASES_HOST: postgres
      DATABASES_PORT: 5432
      DATABASES_USER: inka
      DATABASES_PASSWORD: inka
      DATABASES_DBNAME: inka_dev
      PGBOUNCER_POOL_MODE: transaction  # transaction pooling for web apps
      PGBOUNCER_MAX_CLIENT_CONN: 100
      PGBOUNCER_DEFAULT_POOL_SIZE: 10
      PGBOUNCER_MIN_POOL_SIZE: 5
      PGBOUNCER_RESERVE_POOL_SIZE: 2
      PGBOUNCER_RESERVE_POOL_TIMEOUT: 3
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "psql", "-h", "localhost", "-U", "pgbouncer", "-d", "pgbouncer", "-c", "SELECT 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    # ... existing config ...
    environment:
      # Use pgBouncer instead of direct Postgres
      DATABASE_URL: postgresql://inka:inka@pgbouncer:6432/inka_dev
    depends_on:
      pgbouncer:
        condition: service_healthy

  bot:
    # ... existing config ...
    environment:
      DATABASE_URL: postgresql://inka:inka@pgbouncer:6432/inka_dev
    depends_on:
      pgbouncer:
        condition: service_healthy
```

**File:** `libs/core/src/config.py`

```python
from sqlalchemy.pool import NullPool, QueuePool

# For development (pgBouncer handles pooling)
if settings.ENVIRONMENT == "development":
    # Use NullPool (no client-side pooling, pgBouncer handles it)
    SQLALCHEMY_ENGINE_KWARGS = {
        "poolclass": NullPool,
    }
else:
    # For production (Cloud Run), use QueuePool with modest limits
    SQLALCHEMY_ENGINE_KWARGS = {
        "poolclass": QueuePool,
        "pool_size": 5,  # Connections per worker
        "max_overflow": 10,
        "pool_pre_ping": True,  # Verify connections before use
        "pool_recycle": 3600,  # Recycle connections every hour
    }
```

**File:** `infra/terraform/modules/cloud_run/main.tf` (create)

```hcl
resource "google_cloud_run_service" "api" {
  # ... standard config ...
  
  template {
    spec {
      containers {
        env {
          name  = "DATABASE_URL"
          value = "postgresql://${var.db_user}:${var.db_password}@${var.cloudsql_instance_connection}/${var.db_name}"
        }
        # Cloud SQL Proxy will handle connection pooling
        env {
          name  = "CLOUD_SQL_INSTANCE"
          value = var.cloudsql_instance_connection
        }
      }
    }
  }
}
```

### Acceptance Criteria

- [ ] pgBouncer container starts in docker-compose
- [ ] API connects via pgBouncer (port 6432)
- [ ] Connection pool stats visible (via pgbouncer admin console)
- [ ] Load test: 100 concurrent requests, no connection exhaustion
- [ ] `docker compose logs pgbouncer` shows connection events
- [ ] CI green

### Testing

```bash
# Check pgBouncer status
psql -h localhost -p 6432 -U inka -d pgbouncer -c "SHOW POOLS"

# Expected output:
#  database  | user | cl_active | cl_waiting | sv_active | sv_idle | sv_used | sv_tested | sv_login | maxwait
# -----------+------+-----------+------------+-----------+---------+---------+-----------+----------+---------
#  inka_dev  | inka |        10 |          0 |        10 |       0 |      10 |         0 |        0 |       0
```

---

## PR-4: Scaffold Calendar Slot Engine Skeleton

**Branch:** `feature/calendar-slot-engine-skeleton`  
**Objective:** Create service structure and placeholder functions for slot generation

### Changes Required

**File:** `libs/core/src/services/calendar_slot_service.py` (create)

```python
"""
Calendar Slot Management Service

Responsible for:
  - Generating available slots for a master on a given date
  - Checking slot availability
  - Handling timezone conversions
  - Managing conflicts and exceptions
"""

from datetime import date, datetime, time, timedelta
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import pytz
from sqlalchemy.orm import Session

from libs.core.src.models.schedule import WorkingHours, TimeOff
from libs.core.src.models.booking import Booking

@dataclass
class TimeSlot:
    start_time: datetime
    end_time: datetime
    is_available: bool = True
    reason: Optional[str] = None  # "booked", "time_off", "working_hours"

class SlotInterval(Enum):
    FIFTEEN_MINUTES = 15
    THIRTY_MINUTES = 30
    ONE_HOUR = 60

class CalendarSlotService:
    """Service for managing booking availability and slot generation."""
    
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
    
    def get_available_slots(
        self,
        master_id: int,
        service_date: date,
        service_duration_mins: int,
        interval: SlotInterval = SlotInterval.THIRTY_MINUTES,
    ) -> list[TimeSlot]:
        """
        Generate available time slots for a master on a given date.
        
        Args:
            master_id: Master/stylist ID
            service_date: Date to check availability (date object)
            service_duration_mins: Required duration of service in minutes
            interval: Slot granularity (15, 30, 60 min)
        
        Returns:
            List of TimeSlot objects with availability status
        
        Raises:
            ValueError: If service_date is in past or service_duration invalid
        """
        # TODO: Implement
        # 1. Load master's working hours for service_date's day-of-week
        # 2. Load all bookings for (master_id, service_date)
        # 3. Load all time_off covering service_date
        # 4. Build availability bitmap
        # 5. Return list of TimeSlot objects
        pass
    
    def is_slot_available(
        self,
        master_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a specific time slot is available (no conflicts).
        
        Returns:
            (is_available, conflict_reason or None)
        """
        # TODO: Implement
        # Check:
        #   1. Within working hours
        #   2. No existing bookings overlap
        #   3. No time_off covering the period
        pass
    
    def get_master_timezone(self, master_id: int) -> str:
        """Get master's timezone from tenant settings."""
        # TODO: Implement (load from master or tenant settings)
        pass
    
    def convert_to_local_time(self, utc_time: datetime, timezone_str: str) -> datetime:
        """Convert UTC time to local timezone."""
        # TODO: Implement
        pass
    
    def get_conflicting_bookings(
        self,
        master_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> list[Booking]:
        """Get all bookings that conflict with the given time range."""
        # TODO: Implement
        pass
```

**File:** `libs/core/src/services/__init__.py` (create if not exists)

```python
from .calendar_slot_service import CalendarSlotService, TimeSlot, SlotInterval

__all__ = ["CalendarSlotService", "TimeSlot", "SlotInterval"]
```

**File:** `libs/core/tests/services/__init__.py` (create)

```python
# Test fixtures and helpers for services
```

**File:** `libs/core/tests/services/test_calendar_slot_service.py` (create)

```python
"""Unit tests for CalendarSlotService."""

import pytest
from datetime import date, datetime, time, timedelta
from sqlalchemy.orm import Session
import pytz

from libs.core.src.services.calendar_slot_service import (
    CalendarSlotService,
    TimeSlot,
    SlotInterval,
)
from libs.core.src.models.schedule import WorkingHours, TimeOff
from libs.core.src.models.booking import Booking, BookingStatus
from libs.core.src.models.master import Master
from libs.core.src.models.tenant import Tenant

@pytest.fixture
def tenant(db: Session) -> Tenant:
    """Create test tenant."""
    tenant = Tenant(name="Test Salon", slug="test-salon", timezone="Asia/Jerusalem")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant

@pytest.fixture
def master(db: Session, tenant: Tenant) -> Master:
    """Create test master."""
    master = Master(tenant_id=tenant.id, name="John Stylist", active=True)
    db.add(master)
    db.commit()
    db.refresh(master)
    return master

def test_get_available_slots_basic(db: Session, master: Master):
    """Test basic slot generation."""
    service = CalendarSlotService(db, master.tenant_id)
    
    # Master works 09:00-17:00 on Monday
    # Request slots for next Monday
    test_date = date(2026, 2, 23)  # Monday
    slots = service.get_available_slots(master.id, test_date, 30)
    
    assert len(slots) > 0
    assert all(isinstance(s, TimeSlot) for s in slots)
    # Should have slots from 09:00 to 17:00 (at 30-min intervals = 16 slots)
    assert len(slots) == 16

def test_get_available_slots_no_working_hours(db: Session, master: Master):
    """Test slot generation when master has no working hours set."""
    service = CalendarSlotService(db, master.tenant_id)
    test_date = date(2026, 2, 24)  # Tuesday
    slots = service.get_available_slots(master.id, test_date, 30)
    
    # Should return empty or all unavailable
    assert all(not s.is_available for s in slots) or len(slots) == 0

def test_is_slot_available_with_conflict(db: Session, master: Master):
    """Test conflict detection."""
    service = CalendarSlotService(db, master.tenant_id)
    
    # Create existing booking 10:00-11:00
    booking = Booking(
        tenant_id=master.tenant_id,
        master_id=master.id,
        client_id=1,  # Assume client exists
        service_id=1,  # Assume service exists
        start_time=datetime(2026, 2, 23, 10, 0, tzinfo=pytz.UTC),
        end_time=datetime(2026, 2, 23, 11, 0, tzinfo=pytz.UTC),
        status=BookingStatus.CONFIRMED,
    )
    db.add(booking)
    db.commit()
    
    # Check availability for overlapping slot 10:30-11:30
    is_available, reason = service.is_slot_available(
        master.id,
        datetime(2026, 2, 23, 10, 30, tzinfo=pytz.UTC),
        datetime(2026, 2, 23, 11, 30, tzinfo=pytz.UTC),
    )
    
    assert not is_available
    assert reason == "booked"

def test_timezone_conversion(db: Session, master: Master):
    """Test UTC to local timezone conversion."""
    service = CalendarSlotService(db, master.tenant_id)
    
    utc_time = datetime(2026, 2, 23, 12, 0, tzinfo=pytz.UTC)  # 12:00 UTC
    local = service.convert_to_local_time(utc_time, "Asia/Jerusalem")
    
    # Asia/Jerusalem is UTC+2 (winter)
    assert local.hour == 14  # 12:00 UTC + 2 = 14:00
```

### Acceptance Criteria

- [ ] Service class created with skeleton methods
- [ ] Unit test file created with 5+ test cases (all marked TODO)
- [ ] No import errors
- [ ] Documentation (docstrings) complete
- [ ] CI green (linting, type checking)

### Notes

- Tests are marked TODO; they will be filled in during M1
- Focus on clean API design and documentation
- Prepare for TDD-driven implementation in M1

---

## PR-5: Add Database Indexes + Create Migration

**Branch:** `fix/add-db-indexes`  
**Objective:** Improve query performance by adding indexes on frequently accessed columns

### Changes Required

**File:** `libs/database/alembic/versions/0014_add_performance_indexes.py` (create)

```python
"""Add performance indexes for high-query columns

Revision ID: 0014_add_performance_indexes
Revises: 0013_add_defect_tables
Create Date: 2026-02-22
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014_add_performance_indexes"
down_revision = "0013_add_defect_tables"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Index on booking.start_time for range queries (slot generation)
    op.create_index(
        "idx_booking_start_time",
        "booking",
        ["start_time"],
        postgresql_where=sa.text("status != 'cancelled'"),  # Don't index cancelled
    )
    
    # Index on (master_id, start_time) for master-specific queries
    op.create_index(
        "idx_booking_master_start_time",
        "booking",
        ["master_id", "start_time"],
    )
    
    # Index on client.phone for client lookup
    op.create_index(
        "idx_client_phone",
        "client",
        ["phone"],
        postgresql_opclass={"phone": "varchar_pattern_ops"},  # For LIKE queries
    )
    
    # Index on (tenant_id, master_id) for tenant-scoped queries
    op.create_index(
        "idx_master_tenant_id",
        "master",
        ["tenant_id", "id"],
    )
    
    # Index on (tenant_id, client_id) for tenant-scoped queries
    op.create_index(
        "idx_client_tenant_id",
        "client",
        ["tenant_id", "id"],
    )
    
    # Index on working_hours for schedule queries
    op.create_index(
        "idx_working_hours_master_day",
        "working_hours",
        ["master_id", "day_of_week"],
    )
    
    # Index on time_off for availability queries
    op.create_index(
        "idx_time_off_master_date_range",
        "time_off",
        ["master_id", "start_time", "end_time"],
    )

def downgrade() -> None:
    op.drop_index("idx_time_off_master_date_range", table_name="time_off")
    op.drop_index("idx_working_hours_master_day", table_name="working_hours")
    op.drop_index("idx_client_tenant_id", table_name="client")
    op.drop_index("idx_master_tenant_id", table_name="master")
    op.drop_index("idx_client_phone", table_name="client")
    op.drop_index("idx_booking_master_start_time", table_name="booking")
    op.drop_index("idx_booking_start_time", table_name="booking")
```

### Acceptance Criteria

- [ ] Migration creates 7 indexes
- [ ] `alembic upgrade head` succeeds
- [ ] `alembic downgrade -1` succeeds (rollback works)
- [ ] Query EXPLAIN plans show index usage
- [ ] No impact on existing data
- [ ] CI passes (migration tested)

### Testing

```bash
# Run migration
alembic upgrade head

# Check indexes created
psql inka_dev -c "\di booking*"
# Expected output:
#           Name            | Type  | Table   | Size    | Description
# -------------------------+-------+---------+---------+-------------
#  idx_booking_start_time   | index | booking | 16 KB   |
#  idx_booking_master_start_time | index | booking | 16 KB   |
```

---

## PR-6: Implement Tenant Isolation Middleware

**Branch:** `feature/tenant-isolation-middleware`  
**Objective:** Auto-inject tenant_id filter in all ORM queries

### Changes Required

**File:** `libs/core/src/utils/tenant_context.py` (create)

```python
"""Tenant context management (thread-local storage)."""

from contextvars import ContextVar
from typing import Optional

_tenant_id_var: ContextVar[Optional[int]] = ContextVar("tenant_id", default=None)

def set_tenant_id(tenant_id: Optional[int]) -> None:
    """Set the current tenant context."""
    _tenant_id_var.set(tenant_id)

def get_tenant_id() -> Optional[int]:
    """Get the current tenant context."""
    return _tenant_id_var.get()

def clear_tenant_id() -> None:
    """Clear the current tenant context."""
    _tenant_id_var.set(None)
```

**File:** `apps/api/src/app/middleware/tenant_middleware.py` (create)

```python
"""Middleware to extract and validate tenant from request."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from typing import Optional

from libs.core.src.config import settings
from libs.core.src.utils.tenant_context import set_tenant_id, clear_tenant_id

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant_id from JWT token.
    
    Expected JWT payload:
    {
        "sub": "user_id",
        "tenant_id": 123
    }
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extract Authorization header
        auth_header = request.headers.get("authorization", "")
        tenant_id: Optional[int] = None
        
        if auth_header.startswith("Bearer "):
            try:
                token = auth_header[7:]
                # Decode JWT (no verification for now, use in production)
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=["HS256"],
                )
                tenant_id = payload.get("tenant_id")
            except jwt.InvalidTokenError:
                pass  # Let route handle unauthorized
        
        # Set tenant context
        set_tenant_id(tenant_id)
        
        try:
            response = await call_next(request)
        finally:
            # Clear context
            clear_tenant_id()
        
        return response
```

**File:** `apps/api/src/app.py` (update)

```python
from apps.api.src.app.middleware.tenant_middleware import TenantMiddleware

app = FastAPI(...)
app.add_middleware(TenantMiddleware)  # Must be FIRST middleware
app.add_middleware(LoggingMiddleware)
```

**File:** `libs/core/src/models/base.py` (create, if not exists)

```python
"""Base model with automatic tenant_id filtering."""

from sqlalchemy import and_
from sqlalchemy.orm import Session, declared_attr
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_method

from libs.core.src.utils.tenant_context import get_tenant_id

Base = declarative_base()

class TenantMixin:
    """Mixin to add tenant_id to models and filter queries automatically."""
    
    @hybrid_method
    def filter_by_tenant(self, session: Session):
        """Filter query to current tenant context."""
        tenant_id = get_tenant_id()
        if tenant_id is None:
            raise ValueError("Tenant context not set")
        return session.query(self.__class__).filter(self.__class__.tenant_id == tenant_id)
```

**File:** `libs/core/src/models/booking.py` (update)

```python
from libs.core.src.models.base import TenantMixin

class Booking(Base, TenantMixin):
    # ... existing columns ...
    pass
```

### Acceptance Criteria

- [ ] Middleware extracts tenant_id from JWT
- [ ] Context variable set for request duration
- [ ] Context cleared after request completes
- [ ] Unit tests verify tenant isolation (query for tenant 1 cannot access tenant 2)
- [ ] Integration test: two users from different tenants cannot see each other's data
- [ ] CI green

### Testing

```python
def test_tenant_isolation(db: Session):
    """Verify tenant isolation in queries."""
    from libs.core.src.utils.tenant_context import set_tenant_id, get_tenant_id
    
    # Create two tenants and two clients
    tenant1 = Tenant(name="Salon 1", slug="salon-1")
    tenant2 = Tenant(name="Salon 2", slug="salon-2")
    db.add_all([tenant1, tenant2])
    db.commit()
    
    client1 = Client(tenant_id=tenant1.id, full_name="Alice", phone="111")
    client2 = Client(tenant_id=tenant2.id, full_name="Bob", phone="222")
    db.add_all([client1, client2])
    db.commit()
    
    # Set context to tenant 1
    set_tenant_id(tenant1.id)
    
    # Query clients
    clients = db.query(Client).all()
    
    # Should only see tenant 1's client
    assert len(clients) == 1  # Only Alice
    assert clients[0].full_name == "Alice"
```

---

## PR-7: Fix User.role Foreign Key Relationship

**Branch:** `fix/user-role-fk`  
**Objective:** Change User.role from string to proper FK to Role table

### Changes Required

**File:** `libs/database/alembic/versions/0015_fix_user_role_fk.py` (create)

```python
"""Fix User.role to be foreign key instead of string

Revision ID: 0015_fix_user_role_fk
Revises: 0014_add_performance_indexes
Create Date: 2026-02-22
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0015_fix_user_role_fk"
down_revision = "0014_add_performance_indexes"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create temporary column for role_id
    op.add_column(
        "user",
        sa.Column("role_id_temp", sa.Integer(), sa.ForeignKey("role.id"), nullable=True),
    )
    
    # 2. Migrate data: map role names to IDs
    # Assuming roles exist: admin=1, manager=2, master=3, qa=4, debugger=5
    op.execute("""
        UPDATE "user" u
        SET role_id_temp = (
            SELECT id FROM role WHERE role.name = u.role LIMIT 1
        )
        WHERE u.role IS NOT NULL
    """)
    
    # 3. Drop old role column and rename new one
    op.drop_column("user", "role")
    op.rename_table("user", "user_old")
    op.rename_table("user_new", "user")  # If needed, otherwise just rename column

def downgrade() -> None:
    # Reverse the FK to string
    op.add_column("user", sa.Column("role", sa.String(), nullable=False, server_default='read_only'))
    op.execute("""
        UPDATE "user" u
        SET role = r.name
        FROM role r
        WHERE u.role_id = r.id
    """)
    op.drop_column("user", "role_id")
```

**File:** `libs/core/src/models/user.py` (update)

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    # BEFORE:
    # role = Column(String, nullable=False, server_default='read_only')
    
    # AFTER:
    role_id = Column(Integer, ForeignKey("role.id"), nullable=False)
    
    is_active = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=sa.text('now()'))
    
    # Relationship
    role = relationship("Role", back_populates="users")
    tenant = relationship("Tenant", back_populates="users")
```

### Acceptance Criteria

- [ ] Migration created and tests up/down cycle
- [ ] User.role_id column properly references Role table
- [ ] ORM relationship working (`user.role.name`)
- [ ] All existing users migrated to correct role_id
- [ ] No data loss
- [ ] CI green

---

## PR-8: Set Up Terraform Skeleton (Dev/Stage/Prod)

**Branch:** `infra/terraform-skeleton`  
**Objective:** Create base Terraform modules for Cloud Run, Cloud SQL, Secret Manager

### Directory Structure

```
infra/
└── terraform/
    ├── main.tf              # Provider setup
    ├── variables.tf         # Input variables
    ├── outputs.tf           # Output values
    ├── terraform.tfvars     # Development defaults
    │
    ├── modules/
    │   ├── cloud_run/
    │   │   ├── main.tf
    │   │   ├── variables.tf
    │   │   └── outputs.tf
    │   │
    │   ├── cloud_sql/
    │   │   ├── main.tf
    │   │   ├── variables.tf
    │   │   └── outputs.tf
    │   │
    │   ├── secret_manager/
    │   │   ├── main.tf
    │   │   ├── variables.tf
    │   │   └── outputs.tf
    │   │
    │   └── monitoring/
    │       ├── main.tf
    │       └── variables.tf
    │
    └── environments/
        ├── dev/
        │   ├── terraform.tfvars
        │   └── main.tf (placeholder)
        │
        ├── stage/
        │   ├── terraform.tfvars
        │   └── main.tf (placeholder)
        │
        └── prod/
            ├── terraform.tfvars
            └── main.tf (placeholder)
```

### Key Files

**File:** `infra/terraform/main.tf`

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "google-beta" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

module "cloud_sql" {
  source = "./modules/cloud_sql"
  
  project_id      = var.gcp_project_id
  region          = var.gcp_region
  environment     = var.environment
  instance_name   = "inka-${var.environment}-db"
  database_name   = "inka"
  database_user   = "inka"
  database_version = "POSTGRES_15"
  tier            = var.db_machine_type
}

module "cloud_run_api" {
  source = "./modules/cloud_run"
  
  project_id          = var.gcp_project_id
  region              = var.gcp_region
  environment         = var.environment
  service_name        = "inka-api"
  image               = var.api_image
  memory              = "1Gi"
  cpu                 = "2"
  min_instances       = var.api_min_instances
  max_instances       = var.api_max_instances
  
  environment_variables = {
    DATABASE_URL = module.cloud_sql.database_url
    ENVIRONMENT  = var.environment
  }
}

module "secret_manager" {
  source = "./modules/secret_manager"
  
  project_id   = var.gcp_project_id
  environment  = var.environment
  secrets = {
    "db-password"        = var.db_password
    "bot-token"          = var.bot_token
    "google-oauth-secret" = var.google_oauth_secret
  }
}
```

**File:** `infra/terraform/variables.tf`

```hcl
variable "gcp_project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "gcp_region" {
  type        = string
  default     = "europe-west1"
  description = "GCP Region"
}

variable "environment" {
  type        = string
  description = "Environment (dev, stage, prod)"
  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "environment must be dev, stage, or prod"
  }
}

variable "db_machine_type" {
  type        = string
  default     = "db-f1-micro"
  description = "Cloud SQL machine type"
}

variable "api_min_instances" {
  type        = number
  default     = 1
  description = "Minimum Cloud Run instances"
}

variable "api_max_instances" {
  type        = number
  default     = 10
  description = "Maximum Cloud Run instances"
}

variable "api_image" {
  type        = string
  description = "Docker image for API service"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Cloud SQL user password"
}

variable "bot_token" {
  type        = string
  sensitive   = true
  description = "Telegram bot token"
}

variable "google_oauth_secret" {
  type        = string
  sensitive   = true
  description = "Google OAuth client secret"
}
```

**File:** `infra/terraform/environments/dev/terraform.tfvars`

```hcl
gcp_project_id = "inka-dev"
gcp_region     = "europe-west1"
environment    = "dev"

db_machine_type    = "db-f1-micro"
api_min_instances  = 1
api_max_instances  = 2
api_image          = "europe-west1-docker.pkg.dev/inka-dev/inka-repo/api:latest"

# These are placeholders; use -var flag or Terraform Cloud for actual secrets
db_password          = "changeme"
bot_token            = "changeme"
google_oauth_secret  = "changeme"
```

### Acceptance Criteria

- [ ] Directory structure matches above
- [ ] `terraform init` succeeds
- [ ] `terraform validate` succeeds (no syntax errors)
- [ ] Variables and outputs documented
- [ ] `.gitignore` excludes `.terraform/` and `.tfstate` files
- [ ] README includes how to apply
- [ ] CI skips terraform for now (placeholder)

---

## PR-9: Update CI Workflows (Security Scan + SBOM + Coverage)

**Branch:** `ci/enhance-ci-pipeline`  
**Objective:** Add security scanning, SBOM generation, and coverage thresholds

### Changes Required

**File:** `.github/workflows/ci.yml` (update, add jobs)

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '18'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]
          
      - name: Run ruff
        run: ruff check apps/ libs/
        
      - name: Run black
        run: black --check apps/ libs/
        
      - name: Run mypy
        run: mypy apps/ libs/
        continue-on-error: true

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy (container scanning)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
      
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Run Bandit (Python security)
        run: |
          pip install bandit
          bandit -r apps/ libs/ -f json -o bandit-results.json || true
      
      - name: Upload Bandit results
        uses: actions/upload-artifact@v3
        with:
          name: bandit-report
          path: bandit-results.json

  sbom:
    name: Generate SBOM
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate SBOM using syft
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
          syft . -o spdx-json > sbom.spdx.json
      
      - name: Upload SBOM
        uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: sbom.spdx.json

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: inka
          POSTGRES_PASSWORD: inka
          POSTGRES_DB: inka_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
          
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 3s
          --health-retries 5
        ports:
          - 6379:6379
          
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]
          
      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql://inka:inka@localhost:5432/inka_test
          REDIS_URL: redis://localhost:6379/0
        run: pytest --cov=apps --cov=libs --cov-report=xml --cov-report=html
        
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          fail_ci_if_error: false
      
      - name: Check coverage threshold
        run: |
          COVERAGE=$(python -c "
          import xml.etree.ElementTree as ET
          tree = ET.parse('coverage.xml')
          rate = float(tree.getroot().attrib.get('line-rate', 0)) * 100
          print(f'{rate:.2f}')
          ")
          echo "Coverage: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < 50" | bc -l) )); then
            echo "Coverage ${COVERAGE}% is below 50% threshold"
            exit 1
          fi
      
      - name: Upload coverage report
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: htmlcov/

  quality-gate:
    name: Quality Gate
    runs-on: ubuntu-latest
    needs: [lint, security-scan, test]
    if: always()
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Check all checks passed
        run: |
          LINT_RESULT=${{ needs.lint.result }}
          SECURITY_RESULT=${{ needs.security-scan.result }}
          TEST_RESULT=${{ needs.test.result }}
          
          if [ "$LINT_RESULT" = "failure" ]; then
            echo "❌ Lint check failed"
            exit 1
          fi
          
          if [ "$TEST_RESULT" = "failure" ]; then
            echo "❌ Tests failed"
            exit 1
          fi
          
          echo "✅ All checks passed"
```

### Acceptance Criteria

- [ ] CI runs Trivy security scan
- [ ] CI generates SBOM (syft output)
- [ ] Coverage report uploaded to Codecov
- [ ] Workflow fails if coverage <50%
- [ ] All security scan results visible in GitHub Security tab
- [ ] PR status checks all show green
- [ ] Artifacts (SBOM, coverage report) downloadable from Actions

---

## PR-10: Documentation (Local Setup, API Overview, Deployment)

**Branch:** `docs/production-setup-guide`  
**Objective:** Create comprehensive documentation for development and deployment

### Files to Create

**File:** `docs/development/SETUP.md`

```markdown
# INKA Development Setup Guide

## Prerequisites

- **Python 3.11+** (check: `python --version`)
- **Node.js 18+** (check: `node --version`)
- **Docker & Docker Compose** (check: `docker --version` and `docker compose --version`)
- **Git** (check: `git --version`)

## Quick Start (Recommended)

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/inka.git
cd inka
cp .env.example .env
```

### 2. Start All Services

```bash
make dev
```

This starts:
- PostgreSQL + pgBouncer (localhost:5432, 6432)
- Redis (localhost:6379)
- FastAPI (localhost:8000)
- Telegram bot (polling mode)
- React admin panel (localhost:3000)

All services are ready when you see:
```
✅ postgres: healthy
✅ pgbouncer: healthy
✅ redis: healthy
✅ api: Application startup complete
✅ admin: ready
```

### 3. Verify Setup

```bash
# API should respond
curl http://localhost:8000/health

# Admin panel should load
open http://localhost:3000

# Database should be initialized
make migrate

# Run tests
make test
```

## Manual Setup (Without Docker)

### 1. PostgreSQL

```bash
# Using Homebrew (macOS)
brew install postgresql@15
brew services start postgresql@15

# Using apt (Linux)
sudo apt install postgresql-15

# Create database and user
psql -U postgres -c "CREATE USER inka WITH PASSWORD 'inka';"
psql -U postgres -c "CREATE DATABASE inka_dev OWNER inka;"
```

### 2. Redis

```bash
# Using Homebrew (macOS)
brew install redis
brew services start redis

# Using apt (Linux)
sudo apt install redis-server
```

### 3. Python Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[dev]
pre-commit install
```

### 4. Run Migrations

```bash
make migrate
```

### 5. Start API

```bash
uvicorn apps.api.src.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Start Bot (in separate terminal)

```bash
python -m apps.bot.src.main
```

### 7. Start Admin (in separate terminal)

```bash
cd apps/admin
npm install
npm run dev
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=postgresql://inka:inka@localhost:5432/inka_dev
REDIS_URL=redis://localhost:6379/0

# API
SECRET_KEY=your-secret-key-here
DEBUG=True
LOG_LEVEL=DEBUG

# Telegram (optional, leave empty for local dev)
TELEGRAM_BOT_TOKEN=

# LLM (optional)
OPENAI_API_KEY=

# Google OAuth (optional)
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
```

## Common Tasks

### Run Tests

```bash
make test                   # All tests + coverage
pytest apps/api/tests/      # Specific directory
pytest -k "test_booking"    # Specific test pattern
pytest -v                   # Verbose output
```

### Format Code

```bash
make format                 # Autoformat code
make lint                   # Check code quality
```

### Create Database Migration

```bash
make migrate-create MSG="add new column"
# Edit `libs/database/alembic/versions/0XXX_*.py`
make migrate                # Apply migration
```

### View Logs

```bash
docker compose logs -f api    # API logs
docker compose logs -f bot    # Bot logs
docker compose logs -f admin  # Admin logs
```

## Troubleshooting

### API won't start

```bash
# Check port 8000 is free
lsof -i :8000

# Check database connection
psql postgresql://inka:inka@localhost:5432/inka_dev

# Check migrations applied
alembic -c libs/database/alembic.ini current
```

### Tests failing with database error

```bash
# Ensure test database exists
createdb inka_test

# Run migrations for test DB
DATABASE_URL=postgresql://postgres@localhost/inka_test alembic upgrade head
```

### React admin panel won't compile

```bash
cd apps/admin
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## IDE Setup

### VS Code (Recommended)

Install extensions:
- **Python** (Microsoft)
- **Pylance** (Microsoft)
- **Black Formatter** (Microsoft)
- **Thunder Client** (for API testing)
- **ES7+ React/Redux/React-Native snippets** (dsznajder)

Settings:
```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  }
}
```

### PyCharm

- Set Python interpreter to venv
- Mark `libs/` and `apps/` as "Sources Root"
- Configure black in Settings → Tools → Black

## Next Steps

- Read [API Documentation](../operations/api.md)
- Check out [Architecture Overview](./ARCHITECTURE.md)
- Start with [First Booking PR](../../PRODUCTION_DELIVERY_PLAN.md)
```

**File:** `docs/operations/DEPLOYMENT.md`

```markdown
# Deployment Guide

## Prerequisites

- **gcloud CLI** installed and authenticated
- **Terraform** ≥1.0
- Access to Google Cloud Project

## Environments

| Env | Region | DB Size | API Instances | Purpose |
|-----|--------|---------|---------------|---------|
| **dev** | europe-west1 | f1-micro | 1–2 | Local testing |
| **stage** | europe-west1 | f1-micro | 2–5 | Pre-prod testing |
| **prod** | europe-west1 | db-n1-standard-2 | 5–50 | Customer-facing |

## Deploy to Stage

### 1. Prepare Release

```bash
# Create semantic version tag
git tag -a v0.1.0 -m "Release v0.1.0: Calendar MVP"
git push origin v0.1.0
```

### 2. GitHub Actions Will Trigger

- Run CI (lint, test, security scan)
- Quality gate check
- Ask for manual approval
- Build and push Docker images
- Deploy to Cloud Run (stage) with canary
- Monitor health for 30 minutes

### 3. Manual Approval

Go to GitHub Actions → Deploy to Stage → Click "Approve"

## Deploy to Prod

### 1. Staging Must Be Green

Ensure stage deployment succeeded:
```bash
gcloud run services describe inka-api --region europe-west1 --platform managed
```

### 2. Trigger Prod Deployment

In GitHub Actions, click "Deploy to Prod" workflow

### 3. Two Reviewers Required

Two team members must approve before prod deployment starts

### 4. Canary Deployment

- 20% of traffic to new version
- Monitor for 1 hour
- If healthy, gradually increase to 100%

## Rollback

### Automatic (On Health Check Failure)

If deployment fails health checks, Cloud Run automatically rolls back to previous revision.

### Manual (Emergency)

```bash
# List revisions
gcloud run revisions list --service inka-api --region europe-west1

# Set traffic to previous revision
gcloud run services update-traffic inka-api --region europe-west1 \
  --to-revisions REVISION=100
```

## Secrets Management

All secrets stored in Google Secret Manager:

```bash
# View available secrets
gcloud secrets list

# Create new secret
echo "secret-value" | gcloud secrets create bot-token-prod --data-file=-

# Update secret
echo "new-secret-value" | gcloud secrets versions add bot-token-prod --data-file=-

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding bot-token-prod \
  --member=serviceAccount:inka-api@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

## Monitoring

### Cloud Monitoring Dashboard

```bash
gcloud monitoring dashboards create --config-from-file=infra/monitoring/dashboard.yaml
```

### Logs

```bash
gcloud run services logs read inka-api --region europe-west1 --limit 50

# Follow live logs
gcloud run services logs read inka-api --region europe-west1 --follow
```

### Error Reporting

```bash
# View recent errors
gcloud error-reporting list --filter="service_name:inka-api"
```

## Database Backups

### Automated Backups

Cloud SQL automatically backs up daily. Backups retained for 7 days.

### Manual Backup

```bash
gcloud sql backups create --instance=inka-db-prod \
  --description="Pre-release backup v0.2.0"
```

### Restore

```bash
# List backups
gcloud sql backups list --instance=inka-db-prod

# Restore (restores to new instance, then can switch)
gcloud sql backups restore BACKUP_ID --backup-instance=inka-db-prod
```

## Database Migrations in Prod

Migrations run automatically in the `api` Cloud Run service startup sequence:

```dockerfile
# In Dockerfile
RUN alembic -c libs/database/alembic.ini upgrade head
```

To prevent auto-migrations (safer):
1. Run migration in staging first
2. Verify no issues
3. Manually trigger production migration:

```bash
gcloud cloud-sql-proxy INSTANCE_CONNECTION_NAME &
alembic -c libs/database/alembic.ini upgrade head
```

## Incident Response

### API Down / 5xx Errors

```bash
# Check recent logs
gcloud run services logs read inka-api --limit 100 | grep ERROR

# Check metrics
gcloud monitoring time-series list --filter='resource.service_name="inka-api"'

# Restart service
gcloud run services describe inka-api --region europe-west1  # Check current revision
gcloud run deploy inka-api --region europe-west1 --image=SAME_IMAGE  # Re-deploy

# If all else fails, rollback
gcloud run services update-traffic inka-api --region europe-west1 \
  --to-revisions PREVIOUS_REVISION=100
```

### Database Slow Queries

```bash
# Connect to Cloud SQL
gcloud cloud-sql-proxy INSTANCE_CONNECTION_NAME &

# Check slow query log
psql -h 127.0.0.1 -U inka -d inka_prod -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Kill long-running query
psql -h 127.0.0.1 -U inka -d inka_prod -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE query LIKE '%LONG_QUERY%';"
```

## Runbooks

See [docs/operations/runbooks/](./runbooks/) for step-by-step incident response.
```

### Acceptance Criteria

- [ ] `docs/development/SETUP.md` complete with quick start, manual setup, troubleshooting
- [ ] `docs/operations/DEPLOYMENT.md` complete with deploy instructions, rollback, monitoring
- [ ] `docs/development/API.md` created (endpoint list, example requests)
- [ ] `README.md` updated to link to docs
- [ ] All code examples tested and working
- [ ] Deployed team confirms docs are clear and accurate

---

## Summary Table

| # | Title | Owner | Est. | Dependencies |
|---|-------|-------|------|--------------|
| PR-1 | Fix import paths | Backend | 0.5d | None |
| PR-2 | Optional service configs | Backend | 0.5d | PR-1 |
| PR-3 | DB connection pooling (pgBouncer) | DevOps | 0.5d | PR-1 |
| PR-4 | Calendar slot engine skeleton | Backend | 0.5d | PR-1 |
| PR-5 | Add DB indexes + migration | Backend | 0.5d | PR-1 |
| PR-6 | Tenant isolation middleware | Backend | 1d | PR-1, PR-5 |
| PR-7 | Fix User.role FK | Backend | 0.5d | PR-5 |
| PR-8 | Terraform skeleton | DevOps | 1d | PR-3 |
| PR-9 | Enhance CI (security, SBOM, coverage) | DevOps | 1d | PR-1 |
| PR-10 | Documentation | Docs | 1d | All prior |

**Total Estimated Effort:** 7.5 days (M0 completion: Week 2)

---

**Document Version:** 1.0  
**Status:** Ready for Implementation  
**Last Updated:** 2026-02-22
