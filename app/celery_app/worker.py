# This setup allows independent scaling of background processing (reminders, email jobs, etc.).
# More worker instances can be added to handle high task volumes in production.

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Autodiscovery for tasks in services.reminders_service
celery_app.autodiscover_tasks([
    "app.services.reminders"
])
