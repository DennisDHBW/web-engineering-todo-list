# NOTE: Currently all connected clients for a project receive all task updates.
# TODO: Extend message routing to support per-user channels or permissions.
# This would allow sending private updates (e.g., assigned tasks) only to relevant users.


from fastapi import WebSocket
import asyncio
import logging
import redis
from app.core.config import settings
from app.core.websocket_manager import ConnectionManager

manager = ConnectionManager()
redis_client = redis.Redis.from_url(settings.REDIS_URL)

# This function sets up a Redis-based listener inside a coroutine loop.
# It enables real-time task updates across all clients subscribed to a project.
async def websocket_endpoint(websocket: WebSocket, user_id: int, project_id: int):
    # Handles WebSocket connection for real-time updates in a project
    await manager.connect(websocket, project_id)
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f"task_updates:{project_id}")

    async def listen_to_redis():
        # Listens for Redis Pub/Sub messages published by task updates or reminders.
        # This keeps the client UI in sync without needing polling.
        for message in pubsub.listen():
            if message['type'] == 'message':
                await websocket.send_text(message['data'].decode())

    redis_task = asyncio.create_task(listen_to_redis())
    try:
        while True:
            client_message = await websocket.receive_text()
            await manager.broadcast(project_id, f"Client {user_id}: {client_message}")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        redis_task.cancel()
        manager.disconnect(websocket)
        pubsub.close()
