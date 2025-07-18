import asyncio
import json

import fastapi

from . import functions


async def send_error_message(websocket: fastapi.WebSocket, error_message: str):
    response_message = functions.prepare_response_message(
        type="error",
        error_message=error_message,
    )
    await functions.send_response_message(websocket, response_message)