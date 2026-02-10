import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class Master(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), unique=True)
    name = Column(String, nullable=False)
    active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="master_profile")
    bookings = relationship("Booking", back_populates="master")
