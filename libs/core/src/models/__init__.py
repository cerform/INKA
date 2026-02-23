# Models should be imported directly or from individual files
# Don't import domains models here to avoid duplicate table registrations

from packages.core.models.tenant import Tenant
from packages.core.models.user import User
from packages.core.models.master import Master, Client
from packages.core.models.booking import Booking
from packages.core.models.service import Service
from packages.core.models.schedule import WorkingHours, TimeOff
from packages.core.models.audit import AuditLog
from packages.core.models.role import Role, Permission
from packages.core.models.salon import SalonWorkingHours, SalonClosedDay
from packages.core.models.inventory import Material, StockEntry, PurchaseOrder
from packages.core.models.service_material import ServiceMaterial

__all__ = [
    "Tenant",
    "User",
    "Master",
    "Client",
    "Booking",
    "Service",
    "WorkingHours",
    "TimeOff",
    "AuditLog",
    "Role",
    "Permission",
    "SalonWorkingHours",
    "SalonClosedDay",
    "Material",
    "StockEntry",
    "PurchaseOrder",
    "ServiceMaterial",
]
