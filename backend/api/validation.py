import typing

import ai.ai as ai
import api.responses as responses
import fastapi
import utils.function_utils as function_utils
import utils.websocket_utils as utils


async def validate_code_and_get_function(
    websocket: fastapi.WebSocket, message: dict
) -> tuple[typing.Any, typing.Callable | None] | tuple[None, None]:
    if (validated_message := utils.validate_request_message(message)) is None:
        await responses.send_invalid_message_format_error(websocket)
        return None, None

    code = validated_message.code
    if code is None:
        await responses.send_no_code_provided_error(websocket)
        return None, None

    try:
        valid_function = function_utils.text_to_function(code)
        return validated_message, valid_function
    except ValueError as e:
        await responses.send_validation_error(websocket, e)
        return None, None


async def validate_ai_access(
    websocket: fastapi.WebSocket, validated_message: typing.Any
) -> str | None:
    ai_model = validated_message.ai_model
    ai_api_key = validated_message.ai_api_key

    if ai_model and ai_api_key:
        try:
            if await ai.test_bot_connection_async(ai_model, ai_api_key):  # type: ignore
                return ai_api_key
            else:
                await responses.send_invalid_api_key_error(websocket)
                return None
        except Exception as e:
            await responses.send_ai_connection_error(websocket, e)
            return None
    elif ai_api_key and not ai_model:
        try:
            detected_model = await ai.detect_ai_model_async(ai_api_key)
            if detected_model:
                return ai_api_key
        except Exception:
            pass

    await responses.send_invalid_api_key_error(websocket)
    return None


async def validate_and_prepare_request(
    websocket: fastapi.WebSocket,
    message: dict,
    require_ai: bool = False,
) -> tuple[typing.Any, typing.Callable, str | None] | tuple[None, None, None]:
    validated_message, valid_function = await validate_code_and_get_function(
        websocket, message
    )
    if not validated_message or not valid_function:
        return None, None, None

    ai_api_key = None
    if require_ai:
        ai_api_key = await validate_ai_access(websocket, validated_message)
        if not ai_api_key:
            return None, None, None

    return validated_message, valid_function, ai_api_key
