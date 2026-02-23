from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from packages.core.models import Material, StockEntry, Booking

class InventoryService:
    """
    Service for managing salon inventory, material stock, 
    and automatic deductions from bookings.
    """

    def adjust_stock(
        self, 
        db: Session, 
        tenant_id: int, 
        material_id: int, 
        delta: Decimal, 
        reason: str,
        booking_id: Optional[int] = None
    ) -> Material:
        """
        Manually or automatically adjusts stock level for a material.
        Negative delta = usage/deduction.
        Positive delta = restock/addition.
        """
        material = db.get(Material, material_id)
        if not material or material.tenant_id != tenant_id:
            raise ValueError("Material not found")

        # Create ledger entry
        entry = StockEntry(
            tenant_id=tenant_id,
            material_id=material_id,
            booking_id=booking_id,
            delta=delta,
            reason=reason
        )
        db.add(entry)

        # Update absolute stock quantity
        material.stock_quantity += delta
        
        db.flush() # Ensure it's updated in the session
        return material

    def get_low_stock_alerts(self, db: Session, tenant_id: int):
        """
        Returns materials where quantity is below threshold.
        """
        return db.execute(
            select(Material).where(
                Material.tenant_id == tenant_id,
                Material.stock_quantity <= Material.reorder_threshold
            )
        ).scalars().all()

inventory_service = InventoryService()
