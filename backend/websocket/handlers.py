import asyncio

import fastapi
from helpers import ai, function_utils

from . import create_docs, create_improvements, create_tests, responses, utils


async def handle_test_ai_message(websocket: fastapi.WebSocket, message: dict):
    try:
        ai_api_key = function_utils.get_api_key_from_cookies(websocket)

        detected_model = await ai.detect_ai_model_async(ai_api_key)

        if detected_model:
            response_message = utils.prepare_response_message(
                message_type="ai_test_result",
                message_id=message.get("id", ""),
                is_ok=True,
                detected_model=detected_model,
            )
            await utils.send_response_message(websocket, response_message)
        else:
            # API key doesn't work with either service - send 404-like error
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


async def handle_send_code_message(websocket: fastapi.WebSocket, message: dict):
    if (validated_message := utils.validate_request_message(message)) is None:
        await responses.send_invalid_message_format_error(websocket)
        return

    try:
        ai_model, ai_api_key = function_utils.get_bot_information(websocket)

        if not await ai.test_bot_connection_async(ai_model, ai_api_key):  # type: ignore
            await responses.send_invalid_api_key_error(websocket)
            return
    except Exception as e:
        await responses.send_ai_connection_error(websocket, e)
        return

    code = validated_message.code

    if code is None:
        await responses.send_no_code_provided_error(websocket)
        return

    try:
        valid_function = function_utils.text_to_function(code)
    except ValueError as e:
        await responses.send_validation_error(websocket, e)
        return

    async def generate_and_send_docs():
        try:
            docs_generator = create_docs.Documentation()
            docs = await docs_generator.get_docs_async(
                valid_function, api_key=ai_api_key
            )

            response_message = utils.prepare_response_message(
                message_type="return_docs", message_id=validated_message.id, docs=docs
            )
            await utils.send_response_message(websocket, response_message)

        except Exception as e:
            await responses.send_docs_generation_error(websocket, e)

    async def generate_and_send_unit_tests():
        try:
            unit_test_generator = create_tests.UnitTest()
            unit_tests = await unit_test_generator.get_tests_async(valid_function)

            response_message = utils.prepare_response_message(
                message_type="return_unit_tests",
                message_id=validated_message.id,
                unit_tests=unit_tests,
            )
            await utils.send_response_message(websocket, response_message)

        except Exception as e:
            await responses.send_unit_tests_generation_error(websocket, e)

    async def generate_and_send_memory_tests():
        try:
            memory_test_generator = create_tests.MemoryTest()
            memory_tests = await memory_test_generator.get_tests_async(valid_function)

            response_message = utils.prepare_response_message(
                message_type="return_memory_tests",
                message_id=validated_message.id,
                memory_tests=memory_tests,
            )
            await utils.send_response_message(websocket, response_message)

        except Exception as e:
            await responses.send_memory_tests_generation_error(websocket, e)

    async def generate_and_send_performance_tests():
        try:
            performance_test_generator = create_tests.PerformanceTest()
            performance_tests = await performance_test_generator.get_tests_async(
                valid_function
            )

            response_message = utils.prepare_response_message(
                message_type="return_performance_tests",
                message_id=validated_message.id,
                performance_tests=performance_tests,
            )
            await utils.send_response_message(websocket, response_message)

        except Exception as e:
            await responses.send_performance_tests_generation_error(websocket, e)

    async def generate_and_send_improvements():
        try:
            improvements = (
                await create_improvements.Improvements.generate_improvements_from_ai(
                    valid_function, api_key=ai_api_key
                )
            )

            response_message = utils.prepare_response_message(
                message_type="return_improvements",
                message_id=validated_message.id,
                improvements=improvements,
            )
            await utils.send_response_message(websocket, response_message)

        except Exception as e:
            await responses.send_improvements_generation_error(websocket, e)

    tasks = [
        asyncio.create_task(generate_and_send_docs()),
        asyncio.create_task(generate_and_send_unit_tests()),
        asyncio.create_task(generate_and_send_memory_tests()),
        asyncio.create_task(generate_and_send_performance_tests()),
        asyncio.create_task(generate_and_send_improvements()),
    ]

    await asyncio.gather(*tasks, return_exceptions=True)
