from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def test_inventory_adjustment_tracks_available_stock_and_rejects_oversell():
    from app.models.catalog import Color, Product, ProductCategory, ProductSku, Size
    from app.models.commerce import Inventory, InventoryTransaction
    from app.services.inventory import InventoryService

    engine = create_engine(
        "sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    for table in (ProductCategory, Product, Color, Size, ProductSku, Inventory, InventoryTransaction):
        table.__table__.create(engine)
    with Session(engine) as session:
        category = ProductCategory(name="上衣", slug="tops")
        product = Product(category_id=uuid4(), name="风衣", slug="trench", description="x")
        # Foreign key checks are disabled by SQLite; IDs still let the service exercise stock behavior.
        color = Color(name="黑", hex_value="#000000")
        size = Size(name="M")
        session.add_all((category, product, color, size))
        session.commit()
        sku = ProductSku(
            product_id=product.id, color_id=color.id, size_id=size.id, code="TR-M-BLK", sale_price=Decimal("299.00")
        )
        session.add(sku)
        session.commit()
        service = InventoryService(session)
        inventory = service.adjust(sku.id, 5, reason="restock")
        error = None
        try:
            service.adjust(sku.id, -6, reason="sale")
        except Exception as exc:  # noqa: BLE001
            error = exc

    assert inventory.available_quantity == 5
    assert error is not None
