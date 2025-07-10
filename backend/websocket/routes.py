import asyncio
import json

import fastapi

from . import connection_manager, create_tests, dependencies, functions

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
                await functions.prepare_and_send_response_message(
                    websocket,
                    type="error",
                    error_message="Invalid message format.",
                )
                continue

            if validated_message.type == "send_code":
                # code = validated_message.code
                code = """
def sum_func(a: int, b: int) -> int:
    return a + b
                """

                async def generate_and_send_unit_tests():
                    """Generate and send unit tests independently."""
                    try:
                        unit_test_generator = create_tests.UnitTest()
                        unit_tests = await unit_test_generator.get_tests_async(code)
                        await functions.prepare_and_send_response_message(
                            websocket,
                            type="return_unit_tests",
                            unit_tests=unit_tests,
                        )

                    except Exception as e:
                        print(f"Error generating unit tests: {e}")
                        await functions.prepare_and_send_response_message(
                            websocket,
                            type="error",
                            error_message=f"Failed to generate unit tests: {str(e)}",
                        )

                async def generate_and_send_memory_tests():
                    """Generate and send memory tests independently."""
                    try:
                        memory_test_generator = create_tests.MemoryTest()
                        memory_tests = await memory_test_generator.get_tests_async(code)
                        await functions.prepare_and_send_response_message(
                            websocket,
                            type="return_memory_tests",
                            memory_tests=memory_tests,
                        )

                    except Exception as e:
                        print(f"Error generating memory tests: {e}")
                        await functions.prepare_and_send_response_message(
                            websocket,
                            type="error",
                            error_message=f"Failed to generate memory tests: {str(e)}",
                        )

                async def generate_and_send_performance_tests():
                    """Generate and send performance tests independently."""
                    try:
                        performance_test_generator = create_tests.PerformanceTest()
                        performance_tests = (
                            await performance_test_generator.get_tests_async(code)
                        )
                        await functions.prepare_and_send_response_message(
                            websocket,
                            type="return_performance_tests",
                            performance_tests=performance_tests,
                        )

                    except Exception as e:
                        print(f"Error generating performance tests: {e}")
                        await functions.prepare_and_send_response_message(
                            websocket,
                            type="error",
                            error_message=f"Failed to generate performance tests: {str(e)}",
                        )

                tasks = [
                    asyncio.create_task(generate_and_send_unit_tests()),
                    asyncio.create_task(generate_and_send_memory_tests()),
                    asyncio.create_task(generate_and_send_performance_tests()),
                ]

                await asyncio.gather(*tasks, return_exceptions=True)

    except fastapi.WebSocketDisconnect:
        manager.disconnect(websocket)
