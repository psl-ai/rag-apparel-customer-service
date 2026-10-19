from sqlalchemy import create_engine

from app.db.base import Base, import_models
from app.db.seed import seed_database


def initialize_sqlite_database(database_url: str) -> None:
    """Create the local development schema and idempotently add demo records."""
    import_models()
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        seed_database(session)
