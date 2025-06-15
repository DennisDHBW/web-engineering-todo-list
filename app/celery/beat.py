from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "beat",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Tasks aus reminder importieren
celery_app.autodiscover_tasks([
    "app.services.reminders"
])

# Beat-Schedule definieren
celery_app.conf.beat_schedule = {
    "daily_reminder": {
        "task": "app.services.reminders.send_reminders",
        "schedule": crontab(hour=7, minute=0),
    }
}
