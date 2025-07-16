import asyncio
import json

import config
import fastapi

from . import (
    connection_manager,
    create_docs,
    create_tests,
    dependencies,
    functions,
    models,
)

router = fastapi.APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: fastapi.WebSocket,
    manager: connection_manager.ConnectionManager = fastapi.Depends(
        dependencies.get_connection_manager
    ),
    settings: config.Settings = fastapi.Depends(dependencies.get_settings),
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
                    error_message="Invalid message format.",
                )
                await functions.prepare_and_send_response_message(
                    websocket, response_message
                )
                continue

            if validated_message.type == "send_code":
                # code = validated_message.code
                code = """
def sum_func(a: int, b: int) -> int:
    return a + b
                """

                async def generate_and_send_docs():
                    try:
                        docs_generator = create_docs.Documentation()
                        print(settings.ANTHROPIC_API_KEY)
                        docs = await docs_generator.get_docs_async(
                            code, api_key=settings.ANTHROPIC_API_KEY
                        )

                        response_message = functions.prepare_response_message(
                            type="return_docs", docs=docs
                        )
                        await functions.prepare_and_send_response_message(
                            websocket, response_message
                        )

                    except Exception as e:
                        print(f"Error generating docs: {e}")
                        response_message = functions.prepare_response_message(
                            type="error",
                            error_message=f"Failed to generate docs: {str(e)}",
                        )
                        await functions.prepare_and_send_response_message(
                            websocket, response_message
                        )

                async def generate_and_send_unit_tests():
                    try:
                        unit_test_generator = create_tests.UnitTest()
                        unit_tests = await unit_test_generator.get_tests_async(code)

                        response_message = functions.prepare_response_message(
                            type="return_unit_tests",
                            unit_tests=unit_tests,
                        )
                        await functions.prepare_and_send_response_message(
                            websocket, response_message
                        )

                    except Exception as e:
                        print(f"Error generating unit tests: {e}")
                        response_message = functions.prepare_response_message(
                            type="error",
                            error_message=f"Failed to generate unit tests: {str(e)}",
                        )
                        await functions.prepare_and_send_response_message(
                            websocket, response_message
                        )

                async def generate_and_send_memory_tests():
                    try:
                        memory_test_generator = create_tests.MemoryTest()
                        memory_tests = await memory_test_generator.get_tests_async(code)

                        response_message = functions.prepare_response_message(
                            type="return_memory_tests",
                            memory_tests=memory_tests,
                        )
                        await functions.prepare_and_send_response_message(
                            websocket, response_message
                        )

                    except Exception as e:
                        print(f"Error generating memory tests: {e}")
                        response_message = functions.prepare_response_message(
                            type="error",
                            error_message=f"Failed to generate memory tests: {str(e)}",
                        )
                        await functions.prepare_and_send_response_message(
                            websocket, response_message
                        )

                async def generate_and_send_performance_tests():
                    try:
                        performance_test_generator = create_tests.PerformanceTest()
                        performance_tests = (
                            await performance_test_generator.get_tests_async(code)
                        )

                        response_message = functions.prepare_response_message(
                            type="return_performance_tests",
                            performance_tests=performance_tests,
                        )
                        await functions.prepare_and_send_response_message(
                            websocket, response_message
                        )

                    except Exception as e:
                        print(f"Error generating performance tests: {e}")
                        response_message = functions.prepare_response_message(
                            type="error",
                            error_message=f"Failed to generate performance tests: {str(e)}",
                        )
                        await functions.prepare_and_send_response_message(
                            websocket, response_message
                        )

                tasks = [
                    asyncio.create_task(generate_and_send_docs()),
                    asyncio.create_task(generate_and_send_unit_tests()),
                    asyncio.create_task(generate_and_send_memory_tests()),
                    asyncio.create_task(generate_and_send_performance_tests()),
                ]

                await asyncio.gather(*tasks, return_exceptions=True)

    except fastapi.WebSocketDisconnect:
        manager.disconnect(websocket)
