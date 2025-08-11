import fastapi
from ai import ai
from api.websocket import responses, validation
from services import documentation_generation as create_docs
from services import improvement_generation as create_improvements
from services import test_generation_service as test_generation
from utils import function_utils
from utils import websocket_utils as utils


async def handle_test_ai_message(websocket: fastapi.WebSocket, message: dict):
    try:
        validated_message = utils.validate_request_message(message)

        if not validated_message or not validated_message.ai_api_key:
            raise Exception("API key not provided in the message.")

        detected_model = await ai.detect_ai_model_async(validated_message.ai_api_key)

        if detected_model:
            response_message = utils.prepare_response_message(
                message_type="ai_test_result",
                message_id=message.get("id", ""),
                is_ok=True,
                detected_model=detected_model,
            )
            await utils.send_response_message(websocket, response_message)
        else:
            response_message = utils.prepare_response_message(
                message_type="error",
                message_id=message.get("id", ""),
                error_message="API key is not valid for any supported AI service.",
            )
            await utils.send_response_message(websocket, response_message)

    except Exception as e:
        await responses.send_ai_connection_error(websocket, e)


async def handle_verify_code_message(websocket: fastapi.WebSocket, message: dict):
    if utils.validate_request_message(message) is None:
        await responses.send_invalid_message_format_error(websocket)
        return

    code = message.get("code", None)

    if code is None:
        await responses.send_no_code_provided_error(websocket)
        return

    if not function_utils.validate_single_function(code):
        await responses.send_invalid_code_format_error(websocket)
        return

    response_message = utils.prepare_response_message(
        message_type="verify_code_result",
        message_id=message.get("id", ""),
        is_ok=True,
    )

    await utils.send_response_message(websocket, response_message)


async def handle_generate_tests_message(websocket: fastapi.WebSocket, message: dict):
    validated_message, valid_function, _ = (
        await validation.validate_and_prepare_request(
            websocket=websocket,
            message=message,
            require_ai=False,
        )
    )

    if not validated_message or not valid_function:
        return

    await test_generation.test_manager.generate_all_tests(
        websocket=websocket,
        valid_function=valid_function,
        code=validated_message.code,
        message_id=validated_message.id,
    )


async def handle_generate_docs_message(websocket: fastapi.WebSocket, message: dict):
    validated_message, valid_function, ai_api_key = (
        await validation.validate_and_prepare_request(
            websocket=websocket,
            message=message,
            require_ai=True,
        )
    )

    if not validated_message or not valid_function or not ai_api_key:
        return

    try:
        docs_generator = create_docs.Documentation()
        docs = await docs_generator.get_docs_async(
            valid_function, api_key=ai_api_key, function_text=validated_message.code  # type: ignore
        )

        response_message = utils.prepare_response_message(
            message_type="return_docs", message_id=validated_message.id, docs=docs
        )
        await utils.send_response_message(websocket, response_message)

    except Exception as e:
        await responses.send_docs_generation_error(websocket, e)


async def handle_generate_improvements_message(
    websocket: fastapi.WebSocket, message: dict
):
    validated_message, valid_function, ai_api_key = (
        await validation.validate_and_prepare_request(
            websocket=websocket,
            message=message,
            require_ai=True,
        )
    )

    if not validated_message or not valid_function or not ai_api_key:
        return

    try:
        improvements = await create_improvements.Improvements.generate_improvements_from_ai(
            valid_function, api_key=ai_api_key, function_text=validated_message.code  # type: ignore
        )

        response_message = utils.prepare_response_message(
            message_type="return_improvements",
            message_id=validated_message.id,
            improvements=improvements,
        )
        await utils.send_response_message(websocket, response_message)

    except Exception as e:
        await responses.send_improvements_generation_error(websocket, e)
