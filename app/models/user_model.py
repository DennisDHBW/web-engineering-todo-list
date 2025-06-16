from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")

    # Add this: back-reference from many-to-many project_members table
    projects = relationship(
        "Project",
        secondary="project_members",
        back_populates="members"
    )
