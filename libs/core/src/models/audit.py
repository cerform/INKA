from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from packages.core.models.audit import AuditLog

class AuditLog(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=True) # e.g., "booking", "user"
    target_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
