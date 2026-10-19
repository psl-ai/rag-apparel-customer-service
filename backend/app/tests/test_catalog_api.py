from collections.abc import Iterator

from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


async def test_public_product_list_returns_only_published_matches():
    from app.api.v1.catalog import get_catalog_session
    from app.main import create_app
    from app.models.catalog import Product, ProductCategory
    from app.services.catalog import CatalogService

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    ProductCategory.__table__.create(engine)
    Product.__table__.create(engine)
    with Session(engine) as session:
        category = ProductCategory(name="上衣", slug="tops")
        session.add(category)
        session.commit()
        service = CatalogService(session)
        service.create_product(category_id=category.id, name="风衣", slug="trench", description="通勤", status="published")
        service.create_product(category_id=category.id, name="草稿", slug="draft", description="通勤", status="draft")

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_catalog_session] = override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/products?search=风衣")

    assert response.status_code == 200
    assert [item["name"] for item in response.json()["data"]["items"]] == ["风衣"]
