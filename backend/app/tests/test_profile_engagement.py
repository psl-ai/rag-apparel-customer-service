from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def _setup():
    from app.models.catalog import Color, Product, ProductCategory, ProductSku, Size
    from app.models.commerce import Inventory, InventoryTransaction, ProductFavorite, ProductReview, OrderItem
    from app.models.user import User, UserAddress, UserPreference

    engine = create_engine("sqlite+pysqlite:///:memory:")
    for table in (ProductCategory, Product, Color, Size, ProductSku, Inventory, InventoryTransaction, User, UserAddress, UserPreference, ProductFavorite, ProductReview, OrderItem):
        table.__table__.create(engine)
    session = Session(engine)
    user = User(email="one@example.com", password_hash="hash", display_name="One")
    other = User(email="two@example.com", password_hash="hash", display_name="Two")
    category = ProductCategory(name="上衣", slug=f"tops-{uuid4().hex[:8]}")
    session.add_all([user, other, category]); session.flush()
    product = Product(category_id=category.id, name="风衣", slug=f"coat-{uuid4().hex[:8]}", description="x", status="published")
    session.add(product); session.commit()
    return session, user, other, product


def test_profile_update_default_address_and_preferences():
    from app.services.profile import ProfileService

    session, user, _, _ = _setup(); service = ProfileService(session)
    service.update_user(user.id, {"display_name": "New Name"})
    first = service.create_address(user.id, {"recipient_name": "A", "phone": "13800000000", "province": "北京", "city": "北京", "district": "朝阳", "detail": "一号", "is_default": True})
    second = service.create_address(user.id, {"recipient_name": "B", "phone": "13800000001", "province": "北京", "city": "北京", "district": "海淀", "detail": "二号", "is_default": True})
    prefs = service.upsert_preferences(user.id, {"body_data": {"height": 175}, "style_preferences": ["通勤"]})
    assert session.get(type(user), user.id).display_name == "New Name"
    assert service.get_address(user.id, first.id).is_default is False
    assert service.get_address(user.id, second.id).is_default is True
    assert prefs["body_data"]["height"] == 175


def test_favorite_toggle_is_idempotent_and_review_requires_user():
    from app.services.engagement import EngagementService

    session, user, other, product = _setup(); service = EngagementService(session)
    assert service.toggle_favorite(user.id, product.id) is True
    assert service.list_favorites(user.id)[0].id == product.id
    assert service.toggle_favorite(user.id, product.id) is False
    assert service.list_favorites(user.id) == []
    review = service.create_review(user.id, product.id, 5, "很好")
    assert review.rating == 5
    with pytest.raises(Exception):
        service.create_review(other.id, uuid4(), 5, "越权")
