from fastapi import FastAPI, WebSocket, Depends, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from database import SessionLocal, engine
from models import User, Project, Task, Board, Base
from auth import verify_password, get_password_hash, create_access_token, oauth2_scheme
from websocket_manager import manager
from dotenv import load_dotenv
import redis
import asyncio
import os
import logging

# Constants
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.Redis.from_url(REDIS_URL)

# Create DB tables
Base.metadata.create_all(bind=engine)

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app instance
app = FastAPI()

# Enable CORS for all origins (can be restricted for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schemas
class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"

class ProjectCreate(BaseModel):
    name: str
    owner_id: int

class ProjectOut(ProjectCreate):
    id: int
    class Config:
        orm_mode = True

class BoardCreate(BaseModel):
    name: str
    project_id: int

class BoardOut(BoardCreate):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    project_id: int
    board_id: Optional[int] = None
    priority: Optional[str] = "medium"
    assigned_user_id: Optional[int] = None

class TaskOut(TaskCreate):
    id: int
    completed: bool
    created_at: datetime
    class Config:
        orm_mode = True

# Auth-related helpers
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Auth Endpoints
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed_pw = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_pw, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"username": new_user.username, "role": new_user.role}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role, "id": current_user.id}

# Project Endpoints
@app.post("/projects", response_model=ProjectOut)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects", response_model=List[ProjectOut])
def get_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()

@app.post("/projects/{project_id}/members")
def add_project_member(project_id: int, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if not project or not user:
        raise HTTPException(status_code=404, detail="Project or user not found")
    if user in project.members:
        return {"detail": "User already a member"}
    project.members.append(user)
    db.commit()
    return {"detail": "User added to project"}


# Board Endpoints
@app.post("/boards", response_model=BoardOut)
def create_board(board: BoardCreate, db: Session = Depends(get_db)):
    db_board = Board(**board.model_dump())
    db.add(db_board)
    db.commit()
    db.refresh(db_board)
    return db_board

@app.get("/boards", response_model=List[BoardOut])
def get_boards(db: Session = Depends(get_db)):
    return db.query(Board).all()

# Task Endpoints
@app.post("/tasks", response_model=TaskOut)
def create_task(task: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project or current_user not in project.members:
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    db_task = Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    redis_client.publish("task_updates", f"New task: {db_task.title}")
    return db_task

@app.get("/tasks", response_model=List[TaskOut])
def get_tasks(
        db: Session = Depends(get_db),
        completed: Optional[bool] = None,
        project_id: Optional[int] = None,
        board_id: Optional[int] = None,
        priority: Optional[str] = None,
        assigned_user_id: Optional[int] = None,
        sort_by: Optional[str] = Query(None, regex="^(due_date|priority|created_at)$"),
        sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$")
):
    query = db.query(Task)
    if completed is not None:
        query = query.filter(Task.completed == completed)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if board_id:
        query = query.filter(Task.board_id == board_id)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_user_id:
        query = query.filter(Task.assigned_user_id == assigned_user_id)
    if sort_by:
        column = getattr(Task, sort_by)
        query = query.order_by(column.desc() if sort_order == "desc" else column.asc())
    return query.all()

@app.patch("/tasks/{task_id}", response_model=TaskOut)
def patch_task(task_id: int, fields: dict = Body(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in fields.items():
        if hasattr(db_task, key):
            setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    redis_client.publish("task_updates", f"Task updated: {db_task.title}")
    return db_task


@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: TaskCreate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in task.model_dump().items():
        setattr(db_task, field, value)
    db.commit()
    db.refresh(db_task)
    redis_client.publish("task_updates", f"Task updated: {db_task.title}")
    return db_task

@app.put("/tasks/{task_id}/toggle")
def toggle_completion(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.completed = not db_task.completed
    db.commit()
    redis_client.publish("task_updates", f"Task status changed: {db_task.title} -> {db_task.completed}")
    return {"id": db_task.id, "completed": db_task.completed}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    redis_client.publish("task_updates", f"Task deleted: {db_task.title}")
    return {"detail": "Task deleted"}

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket)
    pubsub = redis_client.pubsub()
    pubsub.subscribe("task_updates")

    async def listen_to_redis():
        for message in pubsub.listen():
            if message['type'] == 'message':
                await websocket.send_text(message['data'].decode())

    redis_task = asyncio.create_task(listen_to_redis())
    try:
        while True:
            client_message = await websocket.receive_text()
            await manager.broadcast(f"Client {user_id}: {client_message}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        logger.error(f"WebSocket error: {e}")
    finally:
        redis_task.cancel()
        manager.disconnect(websocket)
        pubsub.close()

# Manual trigger for Celery reminder (for testing only)
@app.post("/reminders/run")
def trigger_reminders():
    from tasks import send_reminders
    send_reminders.delay()
    return {"detail": "Reminder triggered"}
