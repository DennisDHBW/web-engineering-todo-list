from typing import Type

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectMemberAdd

def create_project(project: ProjectCreate, db: Session) -> Project:
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def get_all_projects(db: Session) -> list[Type[Project]]:
    return db.query(Project).all()

def add_member(project_id: int, member: ProjectMemberAdd, db: Session, user: User):
    project = db.query(Project).filter(Project.id == project_id).first()
    target_user = db.query(User).filter(User.id == member.user_id).first()

    if not project or not target_user:
        raise HTTPException(status_code=404, detail="Project or user not found")

    if target_user in project.members:
        return {"detail": "User already a member"}

    project.members.append(target_user)
    db.commit()
    return {"detail": "User added to project"}
