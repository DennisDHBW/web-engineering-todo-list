from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    owner_id: int

class ProjectOut(ProjectCreate):
    id: int

    class Config:
        from_attributes = True

class ProjectMemberAdd(BaseModel):
    user_id: int
