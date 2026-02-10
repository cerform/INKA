from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("role.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permission.id"), primary_key=True),
)

class Role(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    users = relationship("User", back_populates="user_role")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
