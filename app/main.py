from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine
from app.api import auth, user, project, board, task
from app.core.websocket import websocket_endpoint

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Todo API")

# CORS (für Frontend-Zugriff)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register api routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(project.router, prefix="/projects", tags=["Projects"])
app.include_router(board.router, prefix="/boards", tags=["Boards"])
app.include_router(task.router, prefix="/tasks", tags=["Tasks"])

# webSocket endpoint
app.add_api_websocket_route("/ws/{user_id}/{project_id}", websocket_endpoint)
