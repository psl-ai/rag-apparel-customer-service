def test_initial_metadata_contains_core_tables():
    from app.db.base import Base, import_models

    import_models()

    names = set(Base.metadata.tables)

    assert {
        "users",
        "products",
        "product_skus",
        "inventories",
        "orders",
        "knowledge_chunks",
        "agent_traces",
    } <= names


def test_product_sku_code_is_indexed():
    from app.db.base import Base, import_models

    import_models()

    sku = Base.metadata.tables["product_skus"]

    assert any(index.name == "ix_product_skus_code" for index in sku.indexes)
