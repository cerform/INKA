from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from packages.db.base_class import Base

class ServiceMaterial(Base):
    """
    Association table defining which materials are used for a specific service.
    E.g. "Tattoo Session" uses "5ml of Black Ink".
    """
    __tablename__ = "service_material"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("service.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("material.id"), nullable=False)
    quantity_required = Column(Numeric(precision=10, scale=2), nullable=False)

    service = relationship("Service", back_populates="service_materials")
    material = relationship("Material")
