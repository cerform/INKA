from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from packages.core.crud.base import CRUDBase
from packages.core.models.role import Role, Permission
from packages.core.schemas.role import RoleCreate, RoleUpdate

class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    async def create_with_permissions(
        self, db: AsyncSession, *, obj_in: RoleCreate
    ) -> Role:
        db_obj = Role(
            name=obj_in.name,
            description=obj_in.description
        )
        if obj_in.permissions:
            result = await db.execute(
                select(Permission).where(Permission.id.in_(obj_in.permissions))
            )
            db_obj.permissions = result.scalars().all()
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

role = CRUDRole(Role)
