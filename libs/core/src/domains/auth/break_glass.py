from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID
from packages.core.domains.support.models import DebugSession, DebugSessionStatus

class BreakGlassService:
    def create_session(
        self, 
        db: Any, 
        user_id: UUID, 
        reason: str, 
        duration_minutes: int = 60
    ) -> DebugSession:
        """
        Creates a new break-glass session for a user.
        """
        # Deactivate any existing active sessions
        db.query(DebugSession).filter(
            DebugSession.user_id == user_id,
            DebugSession.status == DebugSessionStatus.ACTIVE
        ).update({"status": DebugSessionStatus.TERMINATED})

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        
        session = DebugSession(
            user_id=user_id,
            reason=reason,
            expires_at=expires_at,
            status=DebugSessionStatus.ACTIVE,
            is_break_glass=True
        )
        db.add(session)
        return session

    def is_session_active(self, db: Any, user_id: UUID) -> bool:
        """
        Checks if a user has an active, non-expired break-glass session.
        """
        session = db.query(DebugSession).filter(
            DebugSession.user_id == user_id,
            DebugSession.status == DebugSessionStatus.ACTIVE,
            DebugSession.expires_at > datetime.now(timezone.utc)
        ).first()
        
        return session is not None

break_glass_service = BreakGlassService()
