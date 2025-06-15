from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy import Enum as SQLAEnum
from app.models.enums import ProjectRole

project_members = Table(
    "project_members", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("project_id", Integer, ForeignKey("projects.id")),
    Column("role", SQLAEnum(ProjectRole), default=ProjectRole.viewer)
)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    members = relationship("User", secondary=project_members, backref="projects")
