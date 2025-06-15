from celery import Celery
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Task
import redis

celery_app = Celery("tasks", broker="redis://redis:6379/0")
redis_client = redis.Redis.from_url("redis://redis:6379/0")

@celery_app.task
def send_reminders():
    # Background task to notify users about tasks due today
    db: Session = SessionLocal()
    today = datetime.now(timezone.utc)
    due_tasks = db.query(Task).filter(Task.due_date <= today, Task.completed == False).all()

    r = redis.Redis.from_url("redis://redis:6379/0")
    for task in due_tasks:
        r.publish("task_updates", f"Reminder: '{task.title}' is due today!")
    db.close()

    for task in due_tasks:
        message = {
            "type": "reminder",
            "task_id": task.id,
            "task_title": task.title,
            "due_date": task.due_date.isoformat(),
            "project_id": task.project_id
        }
        redis_client.publish("task_updates", str(message))
        print(f"Reminder sent: Task '{task.title}' is due!")

    db.close()
    return f"Sent {len(due_tasks)} reminders"

@celery_app.task
def daily_reminder_check():
    return send_reminders()