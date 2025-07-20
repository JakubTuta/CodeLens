import fastapi

from . import utils


async def send_error_response(
    websocket: fastapi.WebSocket, message_type: str, error_message: str
):
    response_message = utils.prepare_response_message(
        message_type=message_type, error_message=error_message  # type: ignore
    )
    await utils.send_response_message(websocket, response_message)


async def send_invalid_message_format_error(websocket: fastapi.WebSocket):
    await send_error_response(websocket, "error", "Invalid message format.")


async def send_no_code_provided_error(websocket: fastapi.WebSocket):
    await send_error_response(websocket, "error", "No code provided.")


async def send_invalid_code_format_error(websocket: fastapi.WebSocket):
    await send_error_response(websocket, "error", "Invalid code format.")


async def send_invalid_api_key_error(websocket: fastapi.WebSocket):
    await send_error_response(websocket, "error", "AI model or API key is invalid.")


async def send_ai_connection_error(websocket: fastapi.WebSocket, error: Exception):
    await send_error_response(
        websocket, "error", f"Failed to get AI information: {str(error)}"
    )


async def send_validation_error(websocket: fastapi.WebSocket, error: Exception):
    await send_error_response(
        websocket, "error", f"Error validating function: {str(error)}"
    )


async def send_docs_generation_error(websocket: fastapi.WebSocket, error: Exception):
    await send_error_response(
        websocket, "error", f"Failed to generate docs: {str(error)}"
    )


async def send_unit_tests_generation_error(
    websocket: fastapi.WebSocket, error: Exception
):
    await send_error_response(
        websocket, "error", f"Failed to generate unit tests: {str(error)}"
    )


async def send_memory_tests_generation_error(
    websocket: fastapi.WebSocket, error: Exception
):
    await send_error_response(
        websocket, "error", f"Failed to generate memory tests: {str(error)}"
    )


async def send_performance_tests_generation_error(
    websocket: fastapi.WebSocket, error: Exception
):
    await send_error_response(
        websocket, "error", f"Failed to generate performance tests: {str(error)}"
    )


async def send_improvements_generation_error(
    websocket: fastapi.WebSocket, error: Exception
):
    await send_error_response(
        websocket, "error", f"Failed to generate improvements: {str(error)}"
    )
