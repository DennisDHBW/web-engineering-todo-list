from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import Project, ProjectRole, project_members, User
from app.schemas import project_schema as project_schema, ProjectOut, ProjectCreate
from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.services.project_service import create_project, get_all_projects, add_member

router = APIRouter()

@router.post("/", response_model=ProjectOut)
def create(project: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_project(project, db, user)

@router.get("/", response_model=list[project_schema.ProjectOut])
def list_all(db: Session = Depends(get_db)):
    return get_all_projects(db)

@router.get("/me", response_model=list[project_schema.ProjectOut])
# Returns all projects where the user is a member
def get_my_projects(user=Depends(get_current_user)):
    return user.projects

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

@router.get("/{project_id}/members", response_model=list[str])
# Returns list of usernames in a given project
def list_project_members(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user not in project.members:
        raise HTTPException(status_code=403, detail="No access to this project")

    return [member.username for member in project.members]

@router.post("/{project_id}/leave")
# Allows a user to leave a project (unless they are the owner)
def leave_project(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id == user.id:
        raise HTTPException(status_code=400, detail="Owner cannot leave the project")

    if user not in project.members:
        raise HTTPException(status_code=400, detail="You are not a member of this project")

    project.members.remove(user)
    db.commit()
    return {"detail": "You have left the project"}

@router.get("/{project_id}", response_model=project_schema.ProjectOut)
# Get details of a specific project
def get_project(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user not in project.members:
        raise HTTPException(status_code=403, detail="Access denied")

    return project

@router.delete("/{project_id}")
# Only owner can delete a project
def delete_project(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the owner can delete this project")

    db.delete(project)
    db.commit()
    return {"detail": "Project deleted"}

