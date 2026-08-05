from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "neveo",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.services.document_processing"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,  # don't lose a task if a worker dies mid-processing
    worker_prefetch_multiplier=1,
)
