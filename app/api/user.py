from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=list[str])
def list_usernames(db: Session = Depends(get_db)):
    return [u.username for u in db.query(User).all()]
