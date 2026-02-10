from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from packages.core.models.audit import AuditLog

class AuditService:
    @staticmethod
    async def log(
        db: AsyncSession,
        *,
        user_id: Optional[int] = None,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        db_obj = AuditLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

audit = AuditService()
