from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy.orm import Session

from app.models import Project, User, Board
from app.models.task_model import TaskComment, Task
from app.schemas import task_schema as task_schema
from app.services import task_service as task_service
from app.services.auth_service import get_current_user
from app.db.database import get_db

router = APIRouter()

@router.post("/", response_model=task_schema.TaskOut)
def create(task: task_schema.TaskCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return task_service.create_task(task, db, user)

@router.get("/", response_model=list[task_schema.TaskOut])
# Retrieves tasks with optional filters and pagination
def get_all(
        completed: bool | None = None,
        project_id: int | None = None,
        board_id: int | None = None,
        priority: str | None = None,
        assigned_user_id: int | None = None,
        sort_by: str | None = Query(None, pattern="^(due_date|priority|created_at)$"),
        sort_order: str = Query("asc", pattern="^(asc|desc)$"),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        search: str | None = None,
        db: Session = Depends(get_db)
):
    return task_service.query_tasks(db, completed, project_id, board_id, priority, assigned_user_id, sort_by, sort_order, limit, offset, search)

@router.patch("/{task_id}", response_model=task_schema.TaskOut)
# Partially update task fields (e.g., change title or status)
def patch(task_id: int, fields: dict = Body(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    return task_service.update_task_partial(task_id, fields, db, user)

@router.put("/{task_id}", response_model=task_schema.TaskOut)
# update task
def update(task_id: int, task: task_schema.TaskCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return task_service.update_task(task_id, task, db, user=user)

@router.put("/{task_id}/toggle")
# Toggles task completion status (done/undone)
def toggle_done(task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return task_service.toggle_completion(task_id, db, user)

@router.delete("/{task_id}")
# delete task
def delete(task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return task_service.delete_task(task_id, db, user)

@router.get("/reminders/today", response_model=list[task_schema.TaskOut])
# Returns all tasks due today for the logged-in user
def get_today_reminders(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user)
):
    return task_service.get_tasks_due_today(db, user)

@router.post("/{task_id}/comments")
# Adds a comment to a task for collaboration
def add_comment(task_id: int, comment: str = Body(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    return task_service.add_comment_to_task(task_id, comment, db, user)

from fastapi import UploadFile, File

@router.post("/{task_id}/attachments")
# Simulated upload endpoint for task attachments.
# In a production system, files would be stored on a cloud storage (e.g. AWS S3, Azure Blob, Google Cloud Storage),
# and metadata like filename, uploader, and upload time would be saved in the database.
# Secure access links would be returned and protected via signed URLs or JWT-based permissions.
def upload_attachment(task_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Simulate upload success
    return {
        "task_id": task_id,
        "filename": file.filename,
        "status": "simulated upload",
        "note": "In production, this would store the file securely and return a protected access link."
    }

@router.get("/{task_id}/comments", response_model=list[task_schema.TaskCommentOut])
# Returns all comments for a given task
def get_task_comments(task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.project_id not in [p.id for p in user.projects]:
        raise HTTPException(status_code=403, detail="No access to this task")

    return db.query(TaskComment).filter(TaskComment.task_id == task_id).all()

@router.put("/{task_id}/assign/{user_id}")
# Assigns a task to a user within the same project
def assign_task(task_id: int, user_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project or user not in project.members:
        raise HTTPException(status_code=403, detail="No access to this project")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user or target_user not in project.members:
        raise HTTPException(status_code=400, detail="Target user is not a project member")

    task.assigned_user_id = user_id
    db.commit()
    db.refresh(task)
    return task

@router.get("/board/{board_id}", response_model=list[task_schema.TaskOut])
# Retrieves all tasks associated with a specific board
def get_tasks_by_board(board_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    project = db.query(Project).filter(Project.id == board.project_id).first()
    if not project or user not in project.members:
        raise HTTPException(status_code=403, detail="No access to this board")

    return db.query(Task).filter(Task.board_id == board_id).all()

@router.post("/{task_id}/duplicate", response_model=task_schema.TaskOut)
# Duplicates an existing task
def duplicate_task(task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    original = db.query(Task).filter(Task.id == task_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Task not found")

    project = db.query(Project).filter(Project.id == original.project_id).first()
    if user not in project.members:
        raise HTTPException(status_code=403, detail="No access to task")

    copy = Task(
        title=original.title + " (Copy)",
        description=original.description,
        due_date=original.due_date,
        project_id=original.project_id,
        board_id=original.board_id,
        priority=original.priority,
        assigned_user_id=original.assigned_user_id
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy
