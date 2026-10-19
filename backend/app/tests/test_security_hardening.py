from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_login_uses_database_role_association_not_email(tmp_path):
    from app.db.base import Base, import_models
    from app.models.user import Role, User, user_roles
    from app.services.auth import AuthService

    import_models(); engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'rbac.db'}"); Base.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(email="not-admin@example.com", password_hash="", display_name="Operator")
        from app.core.security import hash_password
        user.password_hash = hash_password("Secret-123!")
        role = Role(name="operator")
        session.add_all([user, role]); session.flush()
        session.execute(user_roles.insert().values(user_id=user.id, role_id=role.id)); session.commit()
        token = AuthService(session).login("not-admin@example.com", "Secret-123!")

    from app.core.security import decode_token
    assert decode_token(token.access_token)["role"] == "operator"


def test_idempotent_checkout_replays_original_order(tmp_path):
    from app.db.base import Base, import_models
    from app.models.catalog import Color, Product, ProductCategory, ProductSku, Size
    from app.models.commerce import CartItem, Inventory
    from app.models.user import User
    from app.services.orders import OrderService

    import_models(); engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'idempotency.db'}"); Base.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(email="buyer@example.com", password_hash="hash", display_name="Buyer")
        category = ProductCategory(name="幂等分类", slug="idempotency-category")
        color = Color(name="幂等黑", hex_value="#000000"); size = Size(name="幂等M", sort_order=1)
        session.add_all([user, category, color, size]); session.flush()
        product = Product(category_id=category.id, name="幂等商品", slug="idempotency-product", description="测试", status="published")
        session.add(product); session.flush()
        sku = ProductSku(product_id=product.id, color_id=color.id, size_id=size.id, code="IDEMP-001", sale_price=Decimal("99.00"))
        session.add(sku); session.flush(); session.add(Inventory(sku_id=sku.id, quantity=3, available_quantity=3, locked_quantity=0)); session.commit()
        service = OrderService(session); service.add_to_cart(user.id, sku.id, 1)
        first = service.checkout(user.id, "北京市朝阳区", idempotency_key="checkout-1")
        replay = service.checkout(user.id, "北京市朝阳区", idempotency_key="checkout-1")

    assert replay.id == first.id


def test_idempotent_checkout_rejects_same_key_with_different_request(tmp_path):
    from app.core.errors import AppError
    from app.db.base import Base, import_models
    from app.models.catalog import Color, Product, ProductCategory, ProductSku, Size
    from app.models.commerce import Inventory
    from app.models.user import User
    from app.services.orders import OrderService

    import_models(); engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'idempotency-conflict.db'}"); Base.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(email="buyer2@example.com", password_hash="hash", display_name="Buyer")
        category = ProductCategory(name="冲突分类", slug="idempotency-conflict-category")
        color = Color(name="冲突黑", hex_value="#111111"); size = Size(name="冲突M", sort_order=1)
        session.add_all([user, category, color, size]); session.flush()
        product = Product(category_id=category.id, name="冲突商品", slug="idempotency-conflict-product", description="测试", status="published")
        session.add(product); session.flush(); sku = ProductSku(product_id=product.id, color_id=color.id, size_id=size.id, code="IDEMP-002", sale_price=Decimal("99.00")); session.add(sku); session.flush(); session.add(Inventory(sku_id=sku.id, quantity=3, available_quantity=3, locked_quantity=0)); session.commit()
        service = OrderService(session); service.add_to_cart(user.id, sku.id, 1); service.checkout(user.id, "北京市朝阳区", idempotency_key="checkout-2")
        service.add_to_cart(user.id, sku.id, 1)
        with pytest.raises(AppError) as error:
            service.checkout(user.id, "上海市浦东新区", idempotency_key="checkout-2")

    assert error.value.code == "IDEMPOTENCY_CONFLICT"
