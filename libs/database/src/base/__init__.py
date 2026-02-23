# Import all models here for Alembic target_metadata
from packages.db.base_class import Base
from packages.core.models.user import User
from packages.core.models.master import Master, Client
from packages.core.models.booking import Booking
from packages.core.models.audit import AuditLog
from packages.core.models.support import DebugSession, TestRun
from packages.core.domains.defects.models import Defect, DefectEvent
