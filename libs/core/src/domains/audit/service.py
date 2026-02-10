from typing import Any
import uuid
from packages.core.domains.audit.models import AuditLog

class AuditService:
    def log(
        self, 
        db: Any, 
        actor_id: Any, 
        action: str, 
        entity_id: Any = None,
        request_id: Any = None,
        before_payload: Any = None,
        after_payload: Any = None
    ) -> AuditLog:
        """
        Logs an action to the audit trail.
        """
        log_entry = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_id=entity_id,
            request_id=request_id,
            before_payload=before_payload,
            after_payload=after_payload
        )
        db.add(log_entry)
        return log_entry

audit_service = AuditService()
