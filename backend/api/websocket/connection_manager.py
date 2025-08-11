import fastapi
from models import websocket as models


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[fastapi.WebSocket] = []

    async def connect(self, websocket: fastapi.WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: fastapi.WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(
        self, websocket: fastapi.WebSocket, message: models.ResponseMessage
    ):
        await websocket.send_text(message.model_dump_json())
