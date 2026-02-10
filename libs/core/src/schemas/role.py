from typing import List, Optional
from .base import BaseSchema

class PermissionBase(BaseSchema):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int

class RoleBase(BaseSchema):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permissions: List[int] = []

class RoleUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[int]] = None

class Role(RoleBase):
    id: int
    permissions: List[Permission] = []
