import asyncio

import fastapi
from helpers import ai, function_utils

from . import create_docs, create_improvements, create_tests, functions


async def handle_test_ai_message(websocket: fastapi.WebSocket, message: dict):
    try:
        ai_model, ai_api_key = function_utils.get_bot_information(websocket)

        if ai.test_bot_connection(ai_model, ai_api_key):  # type: ignore
            response_message = functions.prepare_response_message(
                type="test_generation_started",
                ai_model=ai_model,
                ai_api_key_status="valid",
            )
            await functions.send_response_message(websocket, response_message)

    except Exception as e:
        response_message = functions.prepare_response_message(
            type="error",
            error_message=f"Failed to process AI test: {str(e)}",
        )
        await functions.send_response_message(websocket, response_message)


async def handle_send_code_message(websocket: fastapi.WebSocket, message: dict):
    if (validated_message := functions.validate_request_message(message)) is None:
        response_message = functions.prepare_response_message(
            type="error",
            error_message="Invalid message format.",
        )
        await functions.send_response_message(websocket, response_message)
        return

    try:
        ai_model, ai_api_key = function_utils.get_bot_information(websocket)

        if not ai.test_bot_connection(ai_model, ai_api_key):  # type: ignore
            response_message = functions.prepare_response_message(
                type="error",
                error_message="AI model or API key is invalid.",
            )
            await functions.send_response_message(websocket, response_message)
            return
    except Exception as e:
        response_message = functions.prepare_response_message(
            type="error",
            error_message=f"Failed to get AI information: {str(e)}",
        )
        await functions.send_response_message(websocket, response_message)
        return

    code = validated_message.code

    if code is None:
        response_message = functions.prepare_response_message(
            type="error",
            error_message="No code provided.",
        )
        await functions.send_response_message(websocket, response_message)
        return

    try:
        valid_function = function_utils.text_to_function(code)
    except ValueError as e:
        response_message = functions.prepare_response_message(
            type="error",
            error_message=f"Error validating function: {str(e)}",
        )
        await functions.send_response_message(websocket, response_message)
        return

    async def generate_and_send_docs():
        try:
            docs_generator = create_docs.Documentation()
            docs = await docs_generator.get_docs_async(
                valid_function, api_key=ai_api_key
            )

            response_message = functions.prepare_response_message(
                type="return_docs", docs=docs
            )
            await functions.send_response_message(websocket, response_message)

        except Exception as e:
            print(f"Error generating docs: {e}")
            response_message = functions.prepare_response_message(
                type="error",
                error_message=f"Failed to generate docs: {str(e)}",
            )
            await functions.send_response_message(websocket, response_message)

    async def generate_and_send_unit_tests():
        try:
            unit_test_generator = create_tests.UnitTest()
            unit_tests = await unit_test_generator.get_tests_async(valid_function)

            response_message = functions.prepare_response_message(
                type="return_unit_tests",
                unit_tests=unit_tests,
            )
            await functions.send_response_message(websocket, response_message)

        except Exception as e:
            print(f"Error generating unit tests: {e}")
            response_message = functions.prepare_response_message(
                type="error",
                error_message=f"Failed to generate unit tests: {str(e)}",
            )
            await functions.send_response_message(websocket, response_message)

    async def generate_and_send_memory_tests():
        try:
            memory_test_generator = create_tests.MemoryTest()
            memory_tests = await memory_test_generator.get_tests_async(valid_function)

            response_message = functions.prepare_response_message(
                type="return_memory_tests",
                memory_tests=memory_tests,
            )
            await functions.send_response_message(websocket, response_message)

        except Exception as e:
            print(f"Error generating memory tests: {e}")
            response_message = functions.prepare_response_message(
                type="error",
                error_message=f"Failed to generate memory tests: {str(e)}",
            )
            await functions.send_response_message(websocket, response_message)

    async def generate_and_send_performance_tests():
        try:
            performance_test_generator = create_tests.PerformanceTest()
            performance_tests = await performance_test_generator.get_tests_async(
                valid_function
            )

            response_message = functions.prepare_response_message(
                type="return_performance_tests",
                performance_tests=performance_tests,
            )
            await functions.send_response_message(websocket, response_message)

        except Exception as e:
            print(f"Error generating performance tests: {e}")
            response_message = functions.prepare_response_message(
                type="error",
                error_message=f"Failed to generate performance tests: {str(e)}",
            )
            await functions.send_response_message(websocket, response_message)

    async def generate_and_send_improvements():
        try:
            improvements = (
                create_improvements.Improvements.generate_improvements_from_ai(
                    valid_function, api_key=ai_api_key
                )
            )

            response_message = functions.prepare_response_message(
                type="return_improvements",
                improvements=improvements,
            )
            await functions.send_response_message(websocket, response_message)

        except Exception as e:
            print(f"Error generating improvements: {e}")
            response_message = functions.prepare_response_message(
                type="error",
                error_message=f"Failed to generate improvements: {str(e)}",
            )
            await functions.send_response_message(websocket, response_message)

    tasks = [
        asyncio.create_task(generate_and_send_docs()),
        asyncio.create_task(generate_and_send_unit_tests()),
        asyncio.create_task(generate_and_send_memory_tests()),
        asyncio.create_task(generate_and_send_performance_tests()),
        asyncio.create_task(generate_and_send_improvements()),
    ]

    await asyncio.gather(*tasks, return_exceptions=True)
