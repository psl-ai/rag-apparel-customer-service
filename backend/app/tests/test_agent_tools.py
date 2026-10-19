from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_query_inventory_returns_live_quantity(tmp_path):
    from app.db.base import Base, import_models
    from app.agents.tools import InventoryQueryInput, query_inventory
    from app.models.catalog import Color, Product, ProductCategory, ProductSku, Size
    from app.models.commerce import Inventory

    import_models(); engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'tools.db'}"); Base.metadata.create_all(engine)
    with Session(engine) as session:
        category = ProductCategory(name="ä¸è¡£", slug="tops"); color = Color(name="é»", hex_value="#000000"); size = Size(name="M")
        session.add_all([category, color, size]); session.flush()
        product = Product(name="è¡¬è¡«", slug="shirt", category_id=category.id, status="published", description="çº¯æ£")
        session.add(product); session.flush(); sku = ProductSku(product_id=product.id, color_id=color.id, size_id=size.id, code="S-M", sale_price=100)
        session.add(sku); session.flush(); session.add(Inventory(sku_id=sku.id, quantity=7, available_quantity=7, locked_quantity=0)); session.commit()
        result = query_inventory(session, InventoryQueryInput(sku_id=sku.id))
    assert result.available_quantity == 7


def test_search_products_excludes_unavailable_products(tmp_path):
    from app.db.base import Base, import_models
    from app.agents.tools import ProductSearchInput, search_products
    from app.models.catalog import Product, ProductCategory

    import_models(); engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'search.db'}"); Base.metadata.create_all(engine)
    with Session(engine) as session:
        category = ProductCategory(name="ä¸è¡¡", slug="tops2"); session.add(category); session.flush()
        session.add_all([
            Product(name="å¯å®è¡¬è¡«", slug="ok", category_id=category.id, status="published", description="æ£"),
            Product(name="ä¸æ¶è¡¬è¡«", slug="off", category_id=category.id, status="draft", description="æ£"),
        ]); session.commit()
        result = search_products(session, ProductSearchInput(query="è¡¬è¡«"))
    assert [item.name for item in result.items] == ["å¯å®è¡¬è¡«"]
