import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class Booking(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("client.id"), nullable=False)
    master_id = Column(UUID(as_uuid=True), ForeignKey("master.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False, default="planned")
    created_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "status IN ('planned', 'confirmed', 'done', 'canceled', 'no_show')",
            name="booking_status_check"
        ),
        Index("idx_booking_time", "master_id", "start_time", "end_time"),
    )

    # Relationships
    client = relationship("Client", back_populates="bookings")
    master = relationship("Master", back_populates="bookings")
    creator = relationship("User", back_populates="created_bookings")
