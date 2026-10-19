from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_admin_order_status_creates_shipment_and_rejects_invalid_transition(tmp_path):
    from app.core.errors import AppError
    from app.db.base import Base, import_models
    from app.models.commerce import Order, Shipment
    from app.models.user import User
    from app.services.admin import AdminOperationsService

    import_models(); engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'ops.db'}"); Base.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(email="buyer@example.com", password_hash="hash", display_name="Buyer")
        session.add(user); session.flush()
        order = Order(order_number="FR-OPS-1", user_id=user.id, status="paid", total_amount=Decimal("99"), address_snapshot="北京")
        session.add(order); session.commit()
        service = AdminOperationsService(session)
        updated = service.update_order_status(order.id, "shipped", carrier="顺丰", tracking_number="SF123")
        shipment = session.query(Shipment).filter_by(order_id=order.id).one()
        assert updated.status == "shipped"
        assert shipment.tracking_number == "SF123"
        with pytest.raises(AppError) as error:
            service.update_order_status(order.id, "paid")

    assert error.value.code == "ORDER_INVALID_TRANSITION"


def test_admin_can_change_product_status(tmp_path):
    from app.db.base import Base, import_models
    from app.models.catalog import Product, ProductCategory
    from app.services.admin import AdminOperationsService

    import_models(); engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'product-status.db'}"); Base.metadata.create_all(engine)
    with Session(engine) as session:
        category = ProductCategory(name="上衣", slug="status-tops")
        session.add(category); session.flush()
        product = Product(category_id=category.id, name="测试商品", slug="status-product", description="x", status="draft")
        session.add(product); session.commit()
        updated = AdminOperationsService(session).set_product_status(product.id, "published")
    assert updated.status == "published"


def test_admin_product_listing_includes_editable_fields(tmp_path):
    from app.db.base import Base, import_models
    from app.models.catalog import Product, ProductCategory
    from app.services.admin import AdminOperationsService

    import_models(); engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'product-list.db'}"); Base.metadata.create_all(engine)
    with Session(engine) as session:
        category = ProductCategory(name="外套", slug="admin-list-jackets")
        session.add(category); session.flush()
        product = Product(category_id=category.id, name="测试夹克", slug="admin-jacket", description="防风面料", fabric_info="尼龙", care_instructions="冷水洗", status="draft")
        session.add(product); session.commit()
        row = AdminOperationsService(session).product_listing()[0]

    assert row["description"] == "防风面料"
    assert row["fabric_info"] == "尼龙"
    assert row["care_instructions"] == "冷水洗"
