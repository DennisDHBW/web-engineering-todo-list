from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas import board_schema as board_schema
from app.models.board_model import Board

router = APIRouter()

@router.post("/", response_model=board_schema.BoardOut)
def create(board: board_schema.BoardCreate, db: Session = Depends(get_db)):
    obj = Board(**board.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/", response_model=list[board_schema.BoardOut])
def get_all(db: Session = Depends(get_db)):
    return db.query(Board).all()
