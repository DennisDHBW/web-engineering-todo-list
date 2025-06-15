# auth_schema use `from_attributes = True` for ORM compatibility.
# This enables fast conversion between SQLAlchemy models and JSON-compatible objects.

from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str

class UserMe(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True
