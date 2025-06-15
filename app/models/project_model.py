# NOTE: The current implementation only supports adding/removing users as members.
# Role-based access control (RBAC) with owner/editor/viewer roles is modeled,
# but not yet enforced in route-level authorization.
# TODO: Add permission checks in API endpoints based on member roles.


from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy import Enum as SQLAEnum
from app.models.enums_model import ProjectRole

project_members = Table(
    "project_members", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("project_id", Integer, ForeignKey("projects.id")),
    # The RBAC system allows fine-grained permissions but is not yet enforced in route logic
    Column("role", SQLAEnum(ProjectRole), default=ProjectRole.viewer)
)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Members relationship allows many-to-many user-project bindings with custom roles (RBAC ready).
    # Useful for controlling access levels (e.g., owner, editor, viewer).
    members = relationship("User", secondary=project_members, backref="projects")
