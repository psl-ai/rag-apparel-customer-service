from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def test_catalog_service_creates_and_filters_published_products():
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
        service.create_product(
            category_id=category.id,
            name="轻盈风衣",
            slug="light-trench",
            description="适合春秋通勤",
            status="published",
        )
        service.create_product(
            category_id=category.id,
            name="草稿夹克",
            slug="draft-jacket",
            description="尚未发布",
            status="draft",
        )
        products = service.list_products(search="风衣")

    assert len(products) == 1
    assert products[0].name == "轻盈风衣"
