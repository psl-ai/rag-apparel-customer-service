from celery import Celery

from app.core.config import get_settings


settings = get_settings()
celery_app = Celery("fashionrag", broker=str(settings.redis_url), backend=str(settings.redis_url))
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
