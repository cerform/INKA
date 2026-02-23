from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class Master(Base):
    __tablename__ = "master"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    tenant = relationship("Tenant", back_populates="masters")
    user = relationship("User", back_populates="master_profile")
    bookings = relationship("Booking", back_populates="master")
    working_hours = relationship("WorkingHours", back_populates="master")
    time_off = relationship("TimeOff", back_populates="master")
    __table_args__ = {"extend_existing": True}

class Client(Base):
    __tablename__ = "client"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)

    tenant = relationship("Tenant", back_populates="clients")
    bookings = relationship("Booking", back_populates="client")
    __table_args__ = {"extend_existing": True}
