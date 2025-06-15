from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.task_model import Task, TaskComment
from app.models.project_model import Project
from app.schemas.task_schema import TaskCreate
from app.core.config import settings
import redis

redis_client = redis.Redis.from_url(settings.REDIS_URL)

# Only users who are project members can create tasks in that project.
# This enforces basic access control (RBAC planned for fine-grained permissions).
def create_task(task_data: TaskCreate, db: Session, user) -> Task:
    project = db.query(Project).filter(Project.id == task_data.project_id).first()
    if not project or user not in project.members:
        raise HTTPException(status_code=403, detail="No access to project")

    db_task = Task(**task_data.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # This publish call enables instant WebSocket updates by notifying subscribed clients via Redis Pub/Sub.
    # This is crucial for real-time collaboration across users.
    redis_client.publish(f"task_updates:{db_task.project_id}", f"New task: {db_task.title}")
    return db_task

# Flexible task querying with multiple optional filters.
# Useful for dashboard views with dynamic sorting and searching.
def query_tasks(db: Session, completed=None, project_id=None, board_id=None, priority=None,
                assigned_user_id=None, sort_by=None, sort_order="asc", limit=20, offset=0, search=None):
    query = db.query(Task)

    if completed is not None:
        query = query.filter(Task.completed == completed)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if board_id:
        query = query.filter(Task.board_id == board_id)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_user_id:
        query = query.filter(Task.assigned_user_id == assigned_user_id)
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    if sort_by:
        sort_column = getattr(Task, sort_by)
        sort_column = sort_column.desc() if sort_order == "desc" else sort_column.asc()
        query = query.order_by(sort_column)

    return query.offset(offset).limit(limit).all()

# Partial update (PATCH) allows frontend to modify individual fields
# without re-sending the entire task object.
def update_task_partial(task_id: int, fields: dict, db: Session):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for key, value in fields.items():
        if hasattr(task, key):
            setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task

def update_task(task_id: int, task_data: TaskCreate, db: Session):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in task_data.model_dump().items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task

def toggle_completion(task_id: int, db: Session):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.completed = not task.completed
    db.commit()
    db.refresh(task)
    return {"task_id": task.id, "completed": task.completed}

def delete_task(task_id: int, db: Session):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"detail": "Task deleted"}

from datetime import datetime, timezone

# Returns all uncompleted tasks that are due today for the current user
def get_tasks_due_today(db: Session, user):
    today = datetime.now(timezone.utc).date()
    user_projects = [p.id for p in user.projects]

    return db.query(Task).filter(
        Task.due_date >= datetime.combine(today, datetime.min.time()).astimezone(timezone.utc),
        Task.due_date <= datetime.combine(today, datetime.max.time()).astimezone(timezone.utc),
        Task.project_id.in_(user_projects),
        Task.completed == False
    ).all()

# Adds a new comment to the given task if the user has access
def add_comment_to_task(task_id: int, content: str, db: Session, user):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.project_id not in [p.id for p in user.projects]:
        raise HTTPException(status_code=403, detail="No access to this task")

    comment = TaskComment(task_id=task.id, user_id=user.id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

