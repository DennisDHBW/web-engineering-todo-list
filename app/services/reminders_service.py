# This task currently pushes Redis messages for due tasks only.
# TODO: Extend to send email reminders or push notifications in future iterations.

from celery import Celery
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.task_model import Task
from app.core.config import settings
import redis

celery_app = Celery("reminder", broker=settings.REDIS_URL)
redis_client = redis.Redis.from_url(settings.REDIS_URL)

@celery_app.task
# Celery task to send daily reminders for overdue tasks via Redis Pub/Sub
def send_reminders():
    db: Session = SessionLocal()
    today = datetime.now(timezone.utc)
    due_tasks = db.query(Task).filter(Task.due_date <= today, Task.completed == False).all()

    # Each due task is broadcasted via Redis to clients.
    # Future version may trigger emails using an SMTP provider inside this task.
    for task in due_tasks:
        message = {
            "type": "reminder",
            "task_id": task.id,
            "task_title": task.title,
            "due_date": task.due_date.isoformat(),
            "project_id": task.project_id
        }
        # Push reminder messages to Redis Pub/Sub so WebSocket clients get notified immediately.
        # Can be extended to trigger email or push notifications.
        redis_client.publish(f"task_updates:{task.project_id}", str(message))

    db.close()
    return f"Sent {len(due_tasks)} reminders"
