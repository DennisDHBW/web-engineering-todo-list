from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    project_id: int
    board_id: Optional[int] = None
    priority: Optional[str] = "medium"
    assigned_user_id: Optional[int] = None

class TaskOut(TaskCreate):
    id: int
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True
