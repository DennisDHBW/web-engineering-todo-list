from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas import auth as auth_schema
from app.db.database import get_db
from app.services import auth as auth_service

router = APIRouter()

@router.post("/register")
def register(user: auth_schema.UserCreate, db: Session = Depends(get_db)):
    return auth_service.register_user(user, db)

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return auth_service.login_user(form_data, db)

@router.get("/users/me", response_model=auth_schema.UserMe)
def get_me(user=Depends(auth_service.get_current_user)):
    return user
