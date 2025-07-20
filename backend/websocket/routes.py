import json

import fastapi

from . import connection_manager, dependencies, handlers, utils

router = fastapi.APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: fastapi.WebSocket,
    manager: connection_manager.ConnectionManager = fastapi.Depends(
        dependencies.get_connection_manager
    ),
):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await utils.send_error_message(websocket, "Invalid JSON format.")
                continue

            message_type = message.get("type")

            if message_type == "test_ai":
                await handlers.handle_test_ai_message(websocket, message)

            elif message_type == "verify_code":
                await handlers.handle_verify_code_message(websocket, message)

            elif message_type == "send_code":
                await handlers.handle_send_code_message(websocket, message)

    except fastapi.WebSocketDisconnect:
        manager.disconnect(websocket)
