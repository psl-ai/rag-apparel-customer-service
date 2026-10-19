from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def test_cart_add_and_checkout_decrements_inventory_and_creates_mock_payment():
    from app.models.catalog import Color, Product, ProductCategory, ProductSku, Size
    from app.models.commerce import Cart, CartItem, Inventory, InventoryTransaction, Order, OrderItem, Payment
    from app.models.user import User
    from app.services.orders import OrderService

    engine = create_engine(
        "sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    tables = (
        ProductCategory, Product, Color, Size, ProductSku, Inventory,
        InventoryTransaction, User, Cart, CartItem, Order, OrderItem, Payment,
    )
    for table in tables:
        table.__table__.create(engine)
    with Session(engine) as session:
        user = User(email="buyer@example.com", password_hash="hash", display_name="Buyer")
        category = ProductCategory(name="上衣", slug="tops")
        product = Product(category_id=uuid4(), name="风衣", slug="trench", description="x", status="published")
        color = Color(name="黑", hex_value="#000000")
        size = Size(name="M")
        session.add_all((user, category, product, color, size))
        session.commit()
        sku = ProductSku(product_id=product.id, color_id=color.id, size_id=size.id, code="TR-M", sale_price=Decimal("299.00"))
        session.add(sku)
        session.flush()
        inventory = Inventory(sku_id=sku.id, quantity=2, available_quantity=2, locked_quantity=0)
        session.add(inventory)
        session.commit()
        service = OrderService(session)
        service.add_to_cart(user.id, sku.id, 1)
        order = service.checkout(user.id, "北京市朝阳区测试路 1 号")

        assert order.status == "paid"
        assert order.total_amount == Decimal("299.00")
        assert session.get(Inventory, inventory.id).available_quantity == 1
        assert session.query(Payment).filter_by(order_id=order.id).one().provider == "mock"
