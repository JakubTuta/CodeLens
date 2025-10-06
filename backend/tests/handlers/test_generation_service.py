import asyncio
import logging
import typing

import api.responses
import fastapi
import models.websocket
import tests.generators.performance
import tests.generators.unit_test
import tests.runners.test_runner_client
import utils.websocket_utils

logger = logging.getLogger(__name__)


class TestGeneratorManager:
    """Manages different test generators and coordinates test generation and execution."""

    def __init__(self):
        self.generators = {
            "unit": tests.generators.unit_test.UnitTestGenerator(),
            "memory": tests.generators.performance.MemoryTestGenerator(),
            "performance": tests.generators.performance.PerformanceTestGenerator(),
        }

        self.response_types: dict[str, models.websocket.response_message_types] = {
            "unit": "return_unit_tests",
            "memory": "return_memory_tests",
            "performance": "return_performance_tests",
        }

        self.error_handlers = {
            "unit": api.responses.send_unit_tests_generation_error,
            "memory": api.responses.send_memory_tests_generation_error,
            "performance": api.responses.send_performance_tests_generation_error,
        }

    async def generate_and_send_test(
        self,
        test_type: str,
        websocket: fastapi.WebSocket,
        valid_function: typing.Callable,
        code: str,
        message_id: str,
    ) -> None:
        """Generate and execute tests of a specific type with streaming results."""
        try:
            generator = self.generators[test_type]
            generated_tests = await generator.get_tests_async(valid_function, code)

            logger.info(f"Generated {len(generated_tests)} {test_type} tests")

            # Set initial status to pending
            for test in generated_tests:
                test.status = "pending"

            # Send tests with pending status
            response_message = utils.websocket_utils.prepare_response_message(
                message_type=self.response_types[test_type],
                message_id=message_id,
                **{f"{test_type}_tests": generated_tests},
            )
            await utils.websocket_utils.send_response_message(
                websocket, response_message
            )
            logger.info(f"Sent {test_type} tests with pending status to client")

            # Create callback for handling individual test results
            def handle_test_result_sync(test_id: str, result):
                completed_test = None
                for test in generated_tests:
                    if test.id == test_id:
                        completed_test = test
                        break

                if completed_test:
                    completed_test.execution_success = result.success
                    completed_test.execution_output = result.output
                    completed_test.execution_error = result.error
                    completed_test.execution_time = result.execution_time
                    completed_test.status = "success" if result.success else "failed"

                    # Send individual test result update
                    def send_update_in_background():
                        async def send_update():
                            try:
                                response_message = (
                                    utils.websocket_utils.prepare_response_message(
                                        message_type="test_result_update",
                                        message_id=message_id,
                                        test_result=completed_test,
                                    )
                                )
                                await utils.websocket_utils.send_response_message(
                                    websocket, response_message
                                )
                                logger.info(
                                    f"Sent individual test result update for {test_id}"
                                )
                            except Exception as e:
                                logger.error(f"Error sending test result update: {e}")

                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(send_update())
                        else:
                            loop.run_until_complete(send_update())

                    send_update_in_background()

            # Update status to running
            for test in generated_tests:
                test.status = "running"

            response_message = utils.websocket_utils.prepare_response_message(
                message_type=self.response_types[test_type],
                message_id=message_id,
                **{f"{test_type}_tests": generated_tests},
            )
            await utils.websocket_utils.send_response_message(
                websocket, response_message
            )
            logger.info(f"Sent {test_type} tests with running status to client")

            # Execute tests with streaming results
            await tests.runners.test_runner_client.test_runner_client.execute_tests_streaming(
                generated_tests, handle_test_result_sync
            )

            logger.info(f"Completed streaming execution for {test_type} tests")

        except Exception as e:
            logger.error(f"Error in generate_and_send_test for {test_type}: {e}")
            error_handler = self.error_handlers[test_type]
            await error_handler(websocket, e)

    async def generate_all_tests(
        self,
        websocket: fastapi.WebSocket,
        valid_function: typing.Callable,
        code: str,
        message_id: str,
    ) -> None:
        """Generate and execute all types of tests concurrently with streaming results."""
        tasks = [
            asyncio.create_task(
                self.generate_and_send_test(
                    test_type, websocket, valid_function, code, message_id
                )
            )
            for test_type in self.generators.keys()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test_type = list(self.generators.keys())[i]
                logger.error(f"Error generating {test_type} tests: {result}")

    async def generate_tests_without_execution(
        self,
        websocket: fastapi.WebSocket,
        valid_function: typing.Callable,
        code: str,
        message_id: str,
    ) -> None:
        """Generate tests without execution when test runner is unavailable."""

        async def generate_single_test_type(test_type: str):
            try:
                generator = self.generators[test_type]
                generated_tests = await generator.get_tests_async(valid_function, code)

                for test in generated_tests:
                    test.status = "pending"

                response_message = utils.websocket_utils.prepare_response_message(
                    message_type=self.response_types[test_type],
                    message_id=message_id,
                    **{f"{test_type}_tests": generated_tests},
                )
                await utils.websocket_utils.send_response_message(
                    websocket, response_message
                )

            except Exception as e:
                error_handler = self.error_handlers[test_type]
                await error_handler(websocket, e)

        tasks = [
            asyncio.create_task(generate_single_test_type(test_type))
            for test_type in self.generators.keys()
        ]

        await asyncio.gather(*tasks, return_exceptions=True)


# Global instance
test_manager = TestGeneratorManager()
