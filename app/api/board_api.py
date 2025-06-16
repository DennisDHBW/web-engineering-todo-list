from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import Project
from app.schemas import board_schema as board_schema
from app.models.board_model import Board
from app.services.auth_service import get_current_user

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

@router.put("/{board_id}", response_model=board_schema.BoardOut)
# Rename a board
def rename_board(board_id: int, board: board_schema.BoardCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    board_obj = db.query(Board).filter(Board.id == board_id).first()
    if not board_obj:
        raise HTTPException(status_code=404, detail="Board not found")

    # Zugriff prüfen
    project = db.query(Project).filter(Project.id == board_obj.project_id).first()
    if user not in project.members:
        raise HTTPException(status_code=403, detail="Access denied")

    board_obj.name = board.name
    db.commit()
    db.refresh(board_obj)
    return board_obj