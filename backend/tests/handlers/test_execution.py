import logging

import api.responses
import fastapi
import models.websocket
import tests.runners.test_runner_client
import utils.websocket_utils

test_runner_client = tests.runners.test_runner_client.test_runner_client

logger = logging.getLogger(__name__)


async def handle_run_tests_message(websocket: fastapi.WebSocket, message: dict):
    """
    Handle a request to run specific tests.

    Expected message format:
    {
        "id": "message_id",
        "type": "run_tests",
        "tests": [
            {
                "type": "unit",
                "name": "test_example",
                "title": "Test Example Function",
                "code": "def test_example():\n    assert True"
            }
        ]
    }
    """
    try:
        message_id = message.get("id", "")
        tests_data = message.get("tests", [])

        if not tests_data:
            await api.responses.send_no_tests_provided_error(websocket, message_id)
            return

        # Parse and validate tests
        tests = []
        for test_data in tests_data:
            try:
                test = models.websocket.Test(**test_data)
                tests.append(test)
            except Exception as e:
                logger.error(f"Invalid test format: {e}")
                await api.responses.send_invalid_test_format_error(
                    websocket, message_id, str(e)
                )
                return

        logger.info(f"Running {len(tests)} tests for message {message_id}")

        # Execute tests
        test_results = await test_runner_client.execute_tests(tests)

        # Update test objects with results
        for i, test in enumerate(tests):
            if i < len(test_results):
                result = test_results[i]
                test.execution_success = result.success
                test.execution_output = result.output
                test.execution_error = result.error
                test.execution_time = result.execution_time

        # Group tests by type
        unit_tests = [t for t in tests if t.type == "unit"]
        memory_tests = [t for t in tests if t.type == "memory"]
        performance_tests = [t for t in tests if t.type == "performance"]

        # Send results for each test type
        if unit_tests:
            response_message = utils.websocket_utils.prepare_response_message(
                message_type="return_unit_tests",
                message_id=message_id,
                unit_tests=unit_tests,
            )
            await utils.websocket_utils.send_response_message(
                websocket, response_message
            )

        if memory_tests:
            response_message = utils.websocket_utils.prepare_response_message(
                message_type="return_memory_tests",
                message_id=message_id,
                memory_tests=memory_tests,
            )
            await utils.websocket_utils.send_response_message(
                websocket, response_message
            )

        if performance_tests:
            response_message = utils.websocket_utils.prepare_response_message(
                message_type="return_performance_tests",
                message_id=message_id,
                performance_tests=performance_tests,
            )
            await utils.websocket_utils.send_response_message(
                websocket, response_message
            )

        logger.info(f"Completed test execution for message {message_id}")

    except Exception as e:
        logger.error(f"Error handling run_tests_message: {e}")
        await api.responses.send_test_execution_error(
            websocket, message.get("id", ""), e
        )
