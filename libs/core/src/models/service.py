from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class Service(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=60)
    price = Column(Numeric(precision=10, scale=2), nullable=False)

    bookings = relationship("Booking", back_populates="service")
