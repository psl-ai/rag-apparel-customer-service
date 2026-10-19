from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def _setup():
    from app.models.catalog import Color, Product, ProductCategory, ProductSku, Size
    from app.models.commerce import Coupon, Inventory, InventoryTransaction, Order, OrderItem, Payment, Cart, CartItem, Shipment
    from app.models.user import User, UserAddress

    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in (ProductCategory, Product, Color, Size, ProductSku, Inventory, InventoryTransaction, User, UserAddress, Cart, CartItem, Order, OrderItem, Payment, Shipment, Coupon):
        table.__table__.create(engine)
    session = Session(engine)
    user = User(email="buyer@example.com", password_hash="hash", display_name="Buyer")
    category = ProductCategory(name="上衣", slug=f"tops-{uuid4().hex[:6]}")
    color = Color(name=f"黑-{uuid4().hex[:6]}", hex_value="#000000")
    size = Size(name=f"M-{uuid4().hex[:6]}")
    session.add_all([user, category, color, size]); session.flush()
    product = Product(category_id=category.id, name="风衣", slug=f"trench-{uuid4().hex[:6]}", description="x", status="published")
    session.add(product); session.flush()
    sku = ProductSku(product_id=product.id, color_id=color.id, size_id=size.id, code=f"TR-{uuid4().hex[:6]}", sale_price=Decimal("299.00"))
    session.add(sku); session.flush(); inventory = Inventory(sku_id=sku.id, quantity=5, available_quantity=5, locked_quantity=0); session.add(inventory)
    coupon = Coupon(code="WELCOME10", discount_type="percentage", discount_value=Decimal("10"), active=True)
    session.add(coupon); session.commit()
    return session, user, sku, inventory, coupon


def test_cart_update_remove_and_coupon_checkout_then_cancel_restores_stock():
    from app.services.orders import OrderService

    session, user, sku, inventory, coupon = _setup()
    service = OrderService(session)
    service.add_to_cart(user.id, sku.id, 1)
    item = service.get_cart_items(user.id)[0]
    service.update_cart_item(user.id, item.id, 2)
    assert service.get_cart(user.id).items[0].quantity == 2
    order = service.checkout(user.id, "北京市朝阳区测试路 1 号", coupon_code=coupon.code)
    assert order.total_amount == Decimal("538.20")
    assert session.get(inventory.__class__, inventory.id).available_quantity == 3
    service.cancel_order(user.id, order.id)
    assert session.get(inventory.__class__, inventory.id).available_quantity == 5
    assert service.get_order(user.id, order.id).status == "canceled"


def test_order_refund_and_address_ownership():
    from app.core.errors import AppError
    from app.services.orders import OrderService
    from app.services.profile import ProfileService

    session, user, sku, _, _ = _setup()
    other = type(user)(email="other@example.com", password_hash="hash", display_name="Other"); session.add(other); session.commit()
    profile = ProfileService(session)
    address = profile.create_address(user.id, {"recipient_name": "Buyer", "phone": "13800000000", "province": "北京", "city": "北京", "district": "朝阳", "detail": "1号"})
    try:
        profile.get_address(other.id, address.id)
        raise AssertionError("ownership check missing")
    except AppError as exc:
        assert exc.code == "ADDRESS_NOT_FOUND"
    service = OrderService(session); service.add_to_cart(user.id, sku.id, 1); order = service.checkout(user.id, "地址")
    assert service.refund_order(user.id, order.id).status == "refund_requested"
