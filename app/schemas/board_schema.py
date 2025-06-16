# board_schema use `from_attributes = True` for ORM compatibility.
# This enables fast conversion between SQLAlchemy models and JSON-compatible objects.

from datetime import datetime
from pydantic import BaseModel

class BoardCreate(BaseModel):
    name: str
    project_id: int

class BoardOut(BoardCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
