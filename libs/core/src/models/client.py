from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class Client(Base):
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bookings = relationship("Booking", back_populates="client")
