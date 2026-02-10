from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    language_code = Column(String, default="en")
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("role.id"), nullable=True)
    
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user_role = relationship("Role", back_populates="users")
    master_profile = relationship("Master", back_populates="user", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="user")
