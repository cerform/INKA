from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from packages.core.models.audit import DebugSession, DebugSessionStatus

class BreakGlassService:
    def create_session(
        self, 
        db: Any, 
        tenant_id: int,
        user_id: int, 
        reason: str, 
        duration_minutes: int = 60
    ) -> DebugSession:
        """
        Creates a new break-glass session for a user.
        """
        # Deactivate any existing active sessions
        db.query(DebugSession).filter(
            DebugSession.tenant_id == tenant_id,
            DebugSession.user_id == user_id,
            DebugSession.status == DebugSessionStatus.ACTIVE
        ).update({"status": DebugSessionStatus.TERMINATED})

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        
        session = DebugSession(
            tenant_id=tenant_id,
            user_id=user_id,
            reason=reason,
            expires_at=expires_at,
            status=DebugSessionStatus.ACTIVE,
            is_break_glass=True
        )
        db.add(session)
        return session

    def is_session_active(self, db: Any, tenant_id: int, user_id: int) -> bool:
        """
        Checks if a user has an active, non-expired break-glass session.
        """
        session = db.query(DebugSession).filter(
            DebugSession.tenant_id == tenant_id,
            DebugSession.user_id == user_id,
            DebugSession.status == DebugSessionStatus.ACTIVE,
            DebugSession.expires_at > datetime.now(timezone.utc)
        ).first()
        
        return session is not None

break_glass_service = BreakGlassService()
