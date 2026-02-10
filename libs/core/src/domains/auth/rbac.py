from typing import Set, Dict

ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "admin": {"*"},
    "manager": {"clients:*", "bookings:*", "masters:*"},
    "master": {"bookings:read", "bookings:update_status"},
    "qa": {"diag:read", "testdata:*"},
    "debugger": {"diag:read", "audit:read"},
    "read_only": {"view"},
}

def has_permission(role: str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, set())
    return "*" in perms or permission in perms
