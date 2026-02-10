from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Enum as SQLEnum
import enum
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Booking(Base):
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False)
    master_id = Column(Integer, ForeignKey("master.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("service.id"), nullable=False)
    
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    notes = Column(String, nullable=True)
    deposit_amount = Column(Numeric(precision=10, scale=2), default=0)

    client = relationship("Client", back_populates="bookings")
    master = relationship("Master", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    attachments = relationship("Attachment", back_populates="booking")
