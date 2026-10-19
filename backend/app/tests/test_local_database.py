from pathlib import Path


def test_local_sqlite_initializer_creates_schema_and_seed(tmp_path: Path):
    from sqlalchemy import create_engine, select

    from app.db.local import initialize_sqlite_database
    from app.models.user import User

    url = f"sqlite+pysqlite:///{tmp_path / 'fashionrag.db'}"
    initialize_sqlite_database(url)

    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.scalar(select(User.email).limit(1)) == "demo@example.com"
