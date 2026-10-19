from collections.abc import Iterator

from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session


async def test_register_and_login_api_uses_uniform_response_envelope():
    from app.api.v1.auth import get_auth_session
    from app.main import create_app
    from app.models.user import User

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(engine)

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_auth_session] = override_session
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        registered = await client.post(
            "/api/v1/auth/register",
            json={"email": "buyer@example.com", "password": "Secret-123!", "display_name": "Buyer"},
        )
        logged_in = await client.post(
            "/api/v1/auth/login",
            json={"email": "buyer@example.com", "password": "Secret-123!"},
        )

    assert registered.status_code == 201
    assert registered.json()["code"] == "OK"
    assert logged_in.status_code == 200
    assert logged_in.json()["data"]["access_token"]


async def test_login_rejects_wrong_password_without_leaking_account_state():
    from app.api.v1.auth import get_auth_session
    from app.main import create_app
    from app.models.user import User
    from app.services.auth import AuthService

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(engine)
    with Session(engine) as session:
        AuthService(session).register("buyer@example.com", "Secret-123!", "Buyer")

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_auth_session] = override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "buyer@example.com", "password": "wrong-password"},
        )

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_INVALID_CREDENTIALS"
