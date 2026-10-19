from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CartItemRequest(BaseModel):
    sku_id: UUID
    quantity: int = Field(ge=1, le=99)


class CartItemResponse(BaseModel):
    id: UUID
    sku_id: UUID
    quantity: int


class CartResponse(BaseModel):
    id: UUID
    user_id: UUID
    items: list[CartItemResponse]


class CheckoutRequest(BaseModel):
    address_snapshot: str = Field(min_length=5, max_length=500)
    coupon_code: str | None = Field(default=None, max_length=64)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    user_id: UUID
    status: str
    total_amount: Decimal
    address_snapshot: str | None = None
