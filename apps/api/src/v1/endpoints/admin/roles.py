from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.deps.auth import check_permissions
from packages.db.session import get_db
from packages.core.crud import crud_role
from packages.core.schemas import role as role_schema

router = APIRouter()

@router.post("/", response_model=role_schema.Role, dependencies=[Depends(check_permissions(["staff.manage"]))])
async def create_role(
    *,
    db: AsyncSession = Depends(get_db),
    role_in: role_schema.RoleCreate
) -> Any:
    """
    Create a new role with permissions.
    """
    return await crud_role.role.create_with_permissions(db, obj_in=role_in)

@router.get("/", response_model=List[role_schema.Role], dependencies=[Depends(check_permissions(["staff.manage"]))])
async def read_roles(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve roles.
    """
    return await crud_role.role.get_multi(db, skip=skip, limit=limit)
