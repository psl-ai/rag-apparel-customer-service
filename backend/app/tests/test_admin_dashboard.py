from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_dashboard_returns_real_counts_and_revenue(tmp_path):
    from app.db.base import Base, import_models
    from app.models.catalog import Product, ProductCategory
    from app.models.commerce import Order
    from app.models.conversation import Conversation, CustomerFeedback
    from app.models.user import User
    from app.services.admin import AdminAnalyticsService

    import_models(); engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'dashboard.db'}"); Base.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(email="dash@example.com", password_hash="hash", display_name="Dash")
        category = ProductCategory(name="上衣", slug=f"dash-{uuid4().hex[:8]}")
        session.add_all([user, category]); session.flush()
        session.add(Order(order_number="FR-DASH-1", user_id=user.id, status="paid", total_amount=Decimal("199.00"), address_snapshot="北京"))
        session.add(Conversation(user_id=user.id, status="open")); session.flush()
        conversation = session.query(Conversation).one()
        session.add(CustomerFeedback(conversation_id=conversation.id, rating=5, comment="好")); session.commit()
        data = AdminAnalyticsService(session).dashboard()

    assert data["users"] == 1
    assert data["orders"] == 1
    assert data["sales_amount"] == Decimal("199.00")
    assert data["consultations"] == 1
    assert data["satisfaction"] == 5.0
