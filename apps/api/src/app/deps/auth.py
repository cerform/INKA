from typing import Generator, Annotated
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from packages.db.session import SessionLocal
from packages.core.domains.auth.models import User
from packages.core.domains.auth.rbac import has_permission

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    x_telegram_id: Annotated[int | None, Header()] = None
) -> User:
    if not x_telegram_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Telegram-ID header required"
        )
    
    user = db.query(User).filter(User.telegram_id == x_telegram_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

from packages.core.domains.auth.break_glass import break_glass_service

class PermissionChecker:
    def __init__(self, permission: str):
        self.permission = permission

    def __call__(self, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> User:
        has_bg = False
        if user.role == "debugger":
            has_bg = break_glass_service.is_session_active(db, user.id)
        
        # If user has break-glass, they get admin-like permissions for their session
        if has_bg:
            return user

        if not has_permission(user.role, self.permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {self.permission}"
            )
        return user
