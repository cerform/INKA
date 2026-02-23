from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class Material(Base):
    """
    Base record for materials/supplies (e.g., ink, needles, massage oil).
    """
    __tablename__ = "material"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False) # e.g., "ml", "pcs", "bottle"
    stock_quantity = Column(Numeric(precision=10, scale=2), default=0, nullable=False)
    reorder_threshold = Column(Numeric(precision=10, scale=2), default=10, nullable=False)

    tenant = relationship("Tenant", back_populates="materials")
    entries = relationship("StockEntry", back_populates="material")

class StockEntry(Base):
    """
    Ledger of stock movements (deductions vs additions).
    """
    __tablename__ = "stock_entry"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("booking.id"), nullable=True)
    delta = Column(Numeric(precision=10, scale=2), nullable=False) # Negative for usage, Positive for restock
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)

    material = relationship("Material", back_populates="entries")
    booking = relationship("Booking") # Link to booking if deduction happened automatically

class PurchaseOrder(Base):
    """
    Tracking for stock fulfillment.
    """
    __tablename__ = "purchase_order"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    quantity = Column(Numeric(precision=10, scale=2), nullable=False)
    status = Column(String, default="ordered", nullable=False) # ordered, delivered, cancelled
    ordered_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    material = relationship("Material")
