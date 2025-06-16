from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.models import User, Project
from app.schemas import auth_schema as auth_schema
from app.db.database import get_db
from app.services import auth_service as auth_service

router = APIRouter()

@router.post("/register")
# Endpoint for new user registration
def register(user: auth_schema.UserCreate, db: Session = Depends(get_db)):
    return auth_service.register_user(user, db)

@router.post("/token")
# Endpoint to login and receive JWT access token
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return auth_service.login_user(form_data, db)

@router.get("/users/me", response_model=auth_schema.UserMe)
# Returns current user info based on the access token
def get_me(user=Depends(auth_service.get_current_user)):
    return user

@router.delete("/me")
# Deletes the currently authenticated user's account
def delete_current_user(user=Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user.id).first()
    if db_user:
        projects = db.query(Project).filter(Project.owner_id == user.id).all()
        if projects:
            raise HTTPException(status_code=400, detail="User is owner of one or more projects and cannot be deleted.")
        db.delete(db_user)
        db.commit()
        return {"message": "User deleted"}
    raise HTTPException(status_code=404, detail="User not found")