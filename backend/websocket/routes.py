import json
import typing

import fastapi

from . import connection_manager, dependencies, functions

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
            message = json.loads(data)

            if (
                validated_message := functions.validate_request_message(message)
            ) is None:
                response_message = functions.prepare_response_message(
                    type="error",
                    message="Invalid message format",
                )

                await manager.send_message(
                    websocket,
                    response_message,
                )

                continue

            if validated_message.type == "send_code":
                code = validated_message.code

                tests = []

                response_message = functions.prepare_response_message(
                    type="return_tests",
                    tests=tests,
                )

                await manager.send_message(
                    websocket,
                    response_message,
                )

    except fastapi.WebSocketDisconnect:
        manager.disconnect(websocket)
