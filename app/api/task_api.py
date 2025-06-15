from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
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
    return task_service.update_task_partial(task_id, fields, db)

@router.put("/{task_id}", response_model=task_schema.TaskOut)
# update task
def update(task_id: int, task: task_schema.TaskCreate, db: Session = Depends(get_db)):
    return task_service.update_task(task_id, task, db)

@router.put("/{task_id}/toggle")
# Toggles task completion status (done/undone)
def toggle_done(task_id: int, db: Session = Depends(get_db)):
    return task_service.toggle_completion(task_id, db)

@router.delete("/{task_id}")
# delete task
def delete(task_id: int, db: Session = Depends(get_db)):
    return task_service.delete_task(task_id, db)

@router.get("/reminders/today", response_model=list[task_schema.TaskOut])
# Returns all tasks due today for the logged-in user
def get_today_reminders(db: Session = Depends(get_db), user=Depends(get_current_user)):
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
