def test_settings_reads_local_service_values_from_environment(monkeypatch):
    """Removing environment-based settings construction must break local startup."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://fashion:pass@db:5432/fashionrag")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("MINIO_ENDPOINT", "minio:9000")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://models.example.test/v1")

    from app.core.config import Settings

    settings = Settings(_env_file=None)

    assert "db:5432/fashionrag" in settings.database_url
    assert settings.chat_model == "mock-chat"


def test_configure_logging_does_not_duplicate_handlers():
    from app.core.logging import configure_logging

    first = configure_logging()
    second = configure_logging()

    assert first is second
