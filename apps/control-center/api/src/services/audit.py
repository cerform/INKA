"""Audit logging service."""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session
from ..models import AuditLog


def log_action(
    db: Session,
    actor: str,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> AuditLog:
    """Write an audit log entry and flush it to the DB session."""
    entry = AuditLog(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details_json=details or {},
    )
    db.add(entry)
    db.flush()
    return entry
