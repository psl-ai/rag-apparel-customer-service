from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedUuidModel


class ProductCategory(TimestampedUuidModel):
    __tablename__ = "product_categories"
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("product_categories.id"), nullable=True)


class Product(TimestampedUuidModel):
    __tablename__ = "products"
    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category_id: Mapped[UUID] = mapped_column(ForeignKey("product_categories.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    description: Mapped[str] = mapped_column(Text)
    fabric_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    care_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProductImage(TimestampedUuidModel):
    __tablename__ = "product_images"
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    object_key: Mapped[str] = mapped_column(String(512))
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[int] = mapped_column(default=0)


class ProductTag(TimestampedUuidModel):
    __tablename__ = "product_tags"
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    value: Mapped[str] = mapped_column(String(80), index=True)


class Color(TimestampedUuidModel):
    __tablename__ = "colors"
    name: Mapped[str] = mapped_column(String(64), unique=True)
    hex_value: Mapped[str] = mapped_column(String(7))


class Size(TimestampedUuidModel):
    __tablename__ = "sizes"
    name: Mapped[str] = mapped_column(String(32), unique=True)
    sort_order: Mapped[int] = mapped_column(default=0)


class SizeChart(TimestampedUuidModel):
    __tablename__ = "size_charts"
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    size_id: Mapped[UUID] = mapped_column(ForeignKey("sizes.id"), index=True)
    measurements: Mapped[str] = mapped_column(Text)


class ProductSku(TimestampedUuidModel):
    __tablename__ = "product_skus"
    __table_args__ = (
        UniqueConstraint("product_id", "color_id", "size_id", name="uq_product_skus_variant"),
        Index("ix_product_skus_code", "code", unique=True),
    )
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    color_id: Mapped[UUID] = mapped_column(ForeignKey("colors.id"), index=True)
    size_id: Mapped[UUID] = mapped_column(ForeignKey("sizes.id"), index=True)
    code: Mapped[str] = mapped_column(String(80))
    barcode: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    image_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
