from fastapi import WebSocket
from collections import defaultdict
from typing import List

class ConnectionManager:
    def __init__(self):
        # Store connections per project
        self.active_connections: dict[int, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, project_id: int):
        await websocket.accept()
        self.active_connections[project_id].append(websocket)

    def disconnect(self, websocket: WebSocket):
        # Remove from all projects (can be optimized)
        for conns in self.active_connections.values():
            if websocket in conns:
                conns.remove(websocket)

    async def broadcast(self, project_id: int, message: str):
        for connection in self.active_connections.get(project_id, []):
            await connection.send_text(message)

manager = ConnectionManager()
