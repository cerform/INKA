# Import all models here for Alembic target_metadata
from packages.db.base_class import Base
from packages.core.domains.auth.models import User
from packages.core.domains.clients.models import Client
from packages.core.domains.masters.models import Master
from packages.core.domains.bookings.models import Booking
from packages.core.domains.audit.models import AuditLog
from packages.core.domains.support.models import DebugSession, TestRun
