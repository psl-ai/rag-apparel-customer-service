from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


def test_register_persists_hashed_user_and_login_returns_tokens():
    from app.models.user import User
    from app.services.auth import AuthService

    engine = create_engine("sqlite+pysqlite:///:memory:")
    User.__table__.create(engine)

    with Session(engine) as session:
        service = AuthService(session)
        registered = service.register("customer@example.com", "Secret-123!", "Customer")
        logged_in = service.login("customer@example.com", "Secret-123!")
        stored = session.scalar(select(User).where(User.email == "customer@example.com"))

    assert registered.email == "customer@example.com"
    assert logged_in.access_token
    assert logged_in.refresh_token
    assert stored is not None
    assert stored.password_hash != "Secret-123!"
