from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class Master(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="master_profile")
    bookings = relationship("Booking", back_populates="master")
    working_hours = relationship("WorkingHours", back_populates="master")
    time_off = relationship("TimeOff", back_populates="master")

class Client(Base):
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)

    bookings = relationship("Booking", back_populates="client")
