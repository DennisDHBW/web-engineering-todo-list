from datetime import datetime, timezone
from sqlalchemy import Table, Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    due_date = Column(DateTime)
    completed = Column(Boolean, default=False)
    project_id = Column(Integer, ForeignKey("projects.id"))
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=True)
    priority = Column(String, default="medium")
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

class Board(Base):
    __tablename__ = "boards"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

project_members = Table(
    "project_members", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("project_id", Integer, ForeignKey("projects.id"))
)

Project.members = relationship("User", secondary=project_members, backref="projects")