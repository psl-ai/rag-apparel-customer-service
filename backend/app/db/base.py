from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_models() -> None:
    """Load ORM modules into metadata when migrations or schema checks need them."""
    from app.models import audit, catalog, commerce, conversation, idempotency, knowledge, user  # noqa: F401
