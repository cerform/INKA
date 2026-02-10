from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class Attachment(Base):
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("booking.id"), nullable=True)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=True) # MIME type
    created_at = Column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="attachments")
