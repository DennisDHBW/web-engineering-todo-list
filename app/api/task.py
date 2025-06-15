from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from app.schemas import task as task_schema
from app.services import task as task_service
from app.services.auth import get_current_user
from app.db.database import get_db

router = APIRouter()

@router.post("/", response_model=task_schema.TaskOut)
def create(task: task_schema.TaskCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return task_service.create_task(task, db, user)

@router.get("/", response_model=list[task_schema.TaskOut])
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
def patch(task_id: int, fields: dict = Body(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    return task_service.update_task_partial(task_id, fields, db)

@router.put("/{task_id}", response_model=task_schema.TaskOut)
def update(task_id: int, task: task_schema.TaskCreate, db: Session = Depends(get_db)):
    return task_service.update_task(task_id, task, db)

@router.put("/{task_id}/toggle")
def toggle_done(task_id: int, db: Session = Depends(get_db)):
    return task_service.toggle_completion(task_id, db)

@router.delete("/{task_id}")
def delete(task_id: int, db: Session = Depends(get_db)):
    return task_service.delete_task(task_id, db)
