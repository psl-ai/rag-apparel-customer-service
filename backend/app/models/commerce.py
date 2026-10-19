from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedUuidModel


class Inventory(TimestampedUuidModel):
    __tablename__ = "inventories"
    __table_args__ = (UniqueConstraint("sku_id", name="uq_inventories_sku_id"), Index("ix_inventories_available", "available_quantity"))
    sku_id: Mapped[UUID] = mapped_column(ForeignKey("product_skus.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    locked_quantity: Mapped[int] = mapped_column(Integer, default=0)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5)


class InventoryTransaction(TimestampedUuidModel):
    __tablename__ = "inventory_transactions"
    inventory_id: Mapped[UUID] = mapped_column(ForeignKey("inventories.id", ondelete="CASCADE"), index=True)
    change_quantity: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(64), index=True)
    reference_id: Mapped[UUID | None] = mapped_column(nullable=True)


class Cart(TimestampedUuidModel):
    __tablename__ = "carts"
    __table_args__ = (UniqueConstraint("user_id", name="uq_carts_user_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)


class CartItem(TimestampedUuidModel):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "sku_id", name="uq_cart_items_variant"),)
    cart_id: Mapped[UUID] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True)
    sku_id: Mapped[UUID] = mapped_column(ForeignKey("product_skus.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)


class Order(TimestampedUuidModel):
    __tablename__ = "orders"
    order_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending_payment", index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    address_snapshot: Mapped[str] = mapped_column(Text)


class OrderItem(TimestampedUuidModel):
    __tablename__ = "order_items"
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    sku_id: Mapped[UUID] = mapped_column(ForeignKey("product_skus.id"), index=True)
    product_name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))


class Payment(TimestampedUuidModel):
    __tablename__ = "payments"
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(64), default="mock")
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    provider_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)


class Shipment(TimestampedUuidModel):
    __tablename__ = "shipments"
    __table_args__ = (UniqueConstraint("order_id", name="uq_shipments_order_id"),)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    carrier: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)


class Coupon(TimestampedUuidModel):
    __tablename__ = "coupons"
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    discount_type: Mapped[str] = mapped_column(String(32))
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class UserCoupon(TimestampedUuidModel):
    __tablename__ = "user_coupons"
    __table_args__ = (UniqueConstraint("user_id", "coupon_id", name="uq_user_coupons_user_coupon"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    coupon_id: Mapped[UUID] = mapped_column(ForeignKey("coupons.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="available", index=True)


class ProductFavorite(TimestampedUuidModel):
    __tablename__ = "product_favorites"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_product_favorites_user_product"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)


class ProductReview(TimestampedUuidModel):
    __tablename__ = "product_reviews"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), index=True)
    order_item_id: Mapped[UUID | None] = mapped_column(ForeignKey("order_items.id"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
