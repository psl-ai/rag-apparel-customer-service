from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.commerce import Inventory, InventoryTransaction
from app.schemas.inventory import InventoryResponse


class InventoryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, sku_id: UUID) -> InventoryResponse:
        inventory = self.session.scalar(select(Inventory).where(Inventory.sku_id == sku_id))
        if inventory is None:
            raise AppError("INVENTORY_NOT_FOUND", "库存不存在", 404)
        return InventoryResponse.model_validate(inventory)

    def adjust(self, sku_id: UUID, delta: int, *, reason: str) -> InventoryResponse:
        inventory = self.session.scalar(select(Inventory).where(Inventory.sku_id == sku_id))
        if inventory is None:
            if delta < 0:
                raise AppError("INVENTORY_NOT_FOUND", "库存不存在", 404)
            inventory = Inventory(sku_id=sku_id, quantity=0, locked_quantity=0, available_quantity=0)
            self.session.add(inventory)
            self.session.flush()
        next_quantity = inventory.quantity + delta
        next_available = next_quantity - inventory.locked_quantity
        if next_quantity < 0 or next_available < 0:
            raise AppError("INVENTORY_INSUFFICIENT", "库存不足", 409)
        inventory.quantity = next_quantity
        inventory.available_quantity = next_available
        self.session.add(InventoryTransaction(inventory_id=inventory.id, change_quantity=delta, reason=reason))
        self.session.commit()
        self.session.refresh(inventory)
        return InventoryResponse.model_validate(inventory)
