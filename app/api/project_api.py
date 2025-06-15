from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import Project, ProjectRole, project_members
from app.schemas import project_schema as project_schema
from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.services.project_service import create_project, get_all_projects, add_member

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

@router.put("/{project_id}/members/{user_id}/role")
# Changes the role of a member within a project
def change_role(project_id: int, user_id: int, role: ProjectRole, db: Session = Depends(get_db), user=Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stmt = project_members.update().where(
        (project_members.c.user_id == user_id) &
        (project_members.c.project_id == project_id)
    ).values(role=role)
    db.execute(stmt)
    db.commit()
    return {"message": f"User role updated to {role.value}"}