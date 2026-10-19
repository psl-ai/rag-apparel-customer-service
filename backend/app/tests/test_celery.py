def test_celery_uses_configured_redis_broker(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/4")
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.tasks.celery_app import celery_app

    assert celery_app.conf.broker_url == "redis://redis:6379/4"
    assert celery_app.conf.task_serializer == "json"
