import asyncio
import json
import logging
import os

import fastapi
from api.websocket import connection_manager, dependencies, handlers
from services import test_execution
from utils import websocket_utils as utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = fastapi.APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: fastapi.WebSocket,
    manager: connection_manager.ConnectionManager = fastapi.Depends(
        dependencies.get_connection_manager
    ),
):
    client_ip = websocket.client.host if websocket.client else "unknown"
    logger.info(f"WebSocket connection attempt from {client_ip}")

    try:
        await manager.connect(websocket)
        logger.info(f"WebSocket connected successfully from {client_ip}")
    except Exception as e:
        logger.error(f"Failed to connect WebSocket from {client_ip}: {e}")
        raise

    ping_interval = int(os.getenv("WEBSOCKET_PING_INTERVAL", "30"))

    async def keepalive():
        try:
            while True:
                await asyncio.sleep(ping_interval)
                try:
                    ping_message = {
                        "type": "ping",
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                    await websocket.send_text(json.dumps(ping_message))
                    logger.debug(f"Sent ping to {client_ip}")
                except Exception as e:
                    logger.warning(f"Failed to ping {client_ip}: {e}")
                    break
        except asyncio.CancelledError:
            logger.debug(f"Keepalive task cancelled for {client_ip}")

    keepalive_task = asyncio.create_task(keepalive())

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message from {client_ip}: {data[:100]}...")

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {client_ip}: {data}")
                await utils.send_error_message(websocket, "Invalid JSON format.")
                continue

            message_type = message.get("type")
            logger.debug(f"Processing message type '{message_type}' from {client_ip}")

            match message_type:
                case "test_ai":
                    await handlers.handle_test_ai_message(websocket, message)
                case "verify_code":
                    await handlers.handle_verify_code_message(websocket, message)
                case "generate_tests":
                    await handlers.handle_generate_tests_message(websocket, message)
                case "generate_docs":
                    await handlers.handle_generate_docs_message(websocket, message)
                case "generate_improvements":
                    await handlers.handle_generate_improvements_message(
                        websocket, message
                    )
                case "run_tests":
                    await test_execution.handle_run_tests_message(websocket, message)
                case "pong":
                    logger.debug(f"Received pong from {client_ip}")
                case _:
                    logger.warning(
                        f"Unknown message type '{message_type}' from {client_ip}"
                    )

    except fastapi.WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from {client_ip}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error from {client_ip}: {e}")
        manager.disconnect(websocket)
        raise
    finally:
        keepalive_task.cancel()
        try:
            await keepalive_task
        except asyncio.CancelledError:
            pass
