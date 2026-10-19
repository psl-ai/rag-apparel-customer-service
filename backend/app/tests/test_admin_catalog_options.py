from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


def test_catalog_options_are_ordered_and_have_display_fields(tmp_path):
    from app.db.base import Base, import_models
    from app.models.catalog import Color, Size

    import_models()
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'options.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([Color(name="曜石黑", hex_value="#161616"), Size(name="M", sort_order=2), Size(name="S", sort_order=1)])
        session.commit()
        colors = session.scalars(select(Color).order_by(Color.name)).all()
        sizes = session.scalars(select(Size).order_by(Size.sort_order, Size.name)).all()

    assert colors[0].hex_value == "#161616"
    assert [item.name for item in sizes] == ["S", "M"]
