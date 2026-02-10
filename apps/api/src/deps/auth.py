from typing import List
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from packages.db.session import get_db
from packages.core.models.user import User
from packages.core.config import settings
from sqlalchemy import select

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    # In a real app, you'd get user from JWT or Telegram ID
    telegram_id: int = None 
) -> User:
    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def check_permissions(required_permissions: List[str]):
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        if current_user.is_superuser:
            return current_user
        
        # Load user role and permissions
        # This is a simplified check
        user_role = current_user.user_role
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No role assigned",
            )
        
        user_permission_names = [p.name for p in user_role.permissions]
        for perm in required_permissions:
            if perm not in user_permission_names:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permission: {perm}",
                )
        return current_user
    return permission_checker
