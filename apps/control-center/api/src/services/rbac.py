"""RBAC service — role-based access control dependency for FastAPI routes."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import RBACUser, UserRole


def get_current_user_email(x_user_email: Optional[str] = Header(default=None)) -> str:
    """
    Extract authenticated user email from request header.
    
    In production this should be validated against a JWT or an identity proxy header
    (e.g. Google Cloud IAP sets X-Goog-Authenticated-User-Email).
    For development, we accept X-User-Email directly.
    """
    if not x_user_email:
        # Fallback: anonymous viewer in dev mode
        return "anonymous@local"
    return x_user_email


def require_role(*allowed_roles: UserRole):
    """
    FastAPI dependency factory that enforces a minimum role.
    
    Usage:
        @router.post("/deploy")
        async def deploy(user=Depends(require_role(UserRole.DEPLOYER, UserRole.ADMIN))):
            ...
    """
    def _check(
        email: str = Depends(get_current_user_email),
        db: Session = Depends(get_db),
    ) -> RBACUser:
        user = db.query(RBACUser).filter(
            RBACUser.email == email,
            RBACUser.is_active == True,
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User '{email}' not found in RBAC registry",
            )

        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not allowed. Required: {[r.value for r in allowed_roles]}",
            )
        return user

    return _check
