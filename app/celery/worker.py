from celery import Celery
from app.core.config import settings

# Celery app initialisieren
celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Autodiscovery für Tasks in services.reminders
celery_app.autodiscover_tasks([
    "app.services.reminders"
])
