from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InventoryAdjustRequest(BaseModel):
    delta: int = Field(description="入库为正数，出库为负数")
    reason: str = Field(min_length=1, max_length=64)


class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku_id: UUID
    quantity: int
    locked_quantity: int
    available_quantity: int
    low_stock_threshold: int
