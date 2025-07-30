import asyncio
import typing

import fastapi

from . import create_tests, models, responses, utils


import websockets

class TestGeneratorManager:
    def __init__(self):
        self.generators = {
            "unit": create_tests.UnitTest(),
            "memory": create_tests.MemoryTest(),
            "performance": create_tests.PerformanceTest(),
        }

        self.response_types: dict[str, models.response_message_types] = {
            "unit": "return_unit_tests",
            "memory": "return_memory_tests",
            "performance": "return_performance_tests",
        }

        self.error_handlers = {
            "unit": responses.send_unit_tests_generation_error,
            "memory": responses.send_memory_tests_generation_error,
            "performance": responses.send_performance_tests_generation_error,
        }

    async def generate_and_send_test(
        self,
        test_type: str,
        websocket: fastapi.WebSocket,
        valid_function: typing.Callable,
        code: str,
        message_id: str,
    ) -> None:
        try:
            generator = self.generators[test_type]
            tests = await generator.get_tests_async(valid_function, code)

            results = await self.send_tests_to_runner(tests)

            response_message = utils.prepare_response_message(
                message_type=self.response_types[test_type],
                message_id=message_id,
                **{f"{test_type}_tests": results},
            )
            await utils.send_response_message(websocket, response_message)

        except Exception as e:
            error_handler = self.error_handlers[test_type]
            await error_handler(websocket, e)

    async def send_tests_to_runner(self, tests: str):
        uri = "ws://test-runner-service:8001/ws"
        async with websockets.connect(uri) as websocket:
            await websocket.send(tests)
            results = await websocket.recv()
            return results

    async def generate_all_tests(
        self,
        websocket: fastapi.WebSocket,
        valid_function: typing.Callable,
        code: str,
        message_id: str,
    ) -> None:
        tasks = [
            asyncio.create_task(
                self.generate_and_send_test(
                    test_type, websocket, valid_function, code, message_id
                )
            )
            for test_type in self.generators.keys()
        ]

        await asyncio.gather(*tasks, return_exceptions=True)


test_manager = TestGeneratorManager()
