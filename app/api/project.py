from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import project as project_schema
from app.db.database import get_db
from app.services.auth import get_current_user
from app.services.project import create_project, get_all_projects, add_member

router = APIRouter()

@router.post("/", response_model=project_schema.ProjectOut)
def create(project: project_schema.ProjectCreate, db: Session = Depends(get_db)):
    return create_project(project, db)

@router.get("/", response_model=list[project_schema.ProjectOut])
def list_all(db: Session = Depends(get_db)):
    return get_all_projects(db)

@router.post("/{project_id}/members")
def add_project_member(
        project_id: int,
        member: project_schema.ProjectMemberAdd,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    return add_member(project_id, member, db, user)
