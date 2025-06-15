from celery import Celery
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.task import Task
from app.core.config import settings
import redis

celery_app = Celery("reminder", broker=settings.REDIS_URL)
redis_client = redis.Redis.from_url(settings.REDIS_URL)

@celery_app.task
def send_reminders():
    db: Session = SessionLocal()
    today = datetime.now(timezone.utc)
    due_tasks = db.query(Task).filter(Task.due_date <= today, Task.completed == False).all()

    for task in due_tasks:
        message = {
            "type": "reminder",
            "task_id": task.id,
            "task_title": task.title,
            "due_date": task.due_date.isoformat(),
            "project_id": task.project_id
        }
        redis_client.publish(f"task_updates:{task.project_id}", str(message))

    db.close()
    return f"Sent {len(due_tasks)} reminders"
