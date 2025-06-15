# The Task schema is designed to be extendable with additional fields like tags, comments, attachments etc.
# This supports long-term feature growth without structural changes.

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

class TaskCommentOut(BaseModel):
    id: int
    content: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True