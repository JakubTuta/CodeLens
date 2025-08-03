import asyncio
import json
import logging
import uuid
from typing import Callable, List, Optional

import pydantic
import websockets
from websockets.exceptions import ConnectionClosed, InvalidURI

from .models import Test

TEST_RUNNER_URL = "ws://codelens-test-runner:8001/ws"
CONNECTION_TIMEOUT = 60
EXECUTION_TIMEOUT = 300

logger = logging.getLogger(__name__)


class TestRequest(pydantic.BaseModel):
    id: str
    type: str
    name: str
    title: str
    code: str


class TestMessage(pydantic.BaseModel):
    message_id: str
    tests: List[TestRequest]


class TestResult(pydantic.BaseModel):
    test_id: str
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: Optional[float] = None


class TestResponse(pydantic.BaseModel):
    message_id: str
    results: List[TestResult]


class IndividualTestResult(pydantic.BaseModel):
    message_id: str
    test_result: TestResult


class TestRunnerClient:
    def __init__(self):
        self.test_runner_url = TEST_RUNNER_URL
        self.connection_timeout = CONNECTION_TIMEOUT
        self.execution_timeout = EXECUTION_TIMEOUT

    async def execute_tests(self, tests: List[Test]) -> List[TestResult]:
        """
        Execute tests using the test-runner service (legacy method for backwards compatibility)

        Args:
            tests: List of Test objects to execute

        Returns:
            List of TestResult objects with execution results
        """
        try:
            test_requests = []
            for test in tests:
                test_requests.append(
                    TestRequest(
                        id=test.id,
                        type=test.type,
                        name=test.name,
                        title=test.title,
                        code=test.code,
                    )
                )

            message_id = str(uuid.uuid4())
            test_message = TestMessage(message_id=message_id, tests=test_requests)

            results = await self._send_and_receive(test_message)

            return results

        except Exception as e:
            logger.error(f"Error executing tests: {e}")
            error_results = []
            for test in tests:
                error_results.append(
                    TestResult(
                        test_id=test.id,
                        success=False,
                        output="",
                        error=f"Test runner communication error: {str(e)}",
                    )
                )
            return error_results

    async def execute_tests_streaming(
        self, tests: List[Test], result_callback: Callable[[str, TestResult], None]
    ) -> None:
        """
        Execute tests using the test-runner service with streaming results

        Args:
            tests: List of Test objects to execute
            result_callback: Callback function to call when each test completes
                             Parameters: (test_id, TestResult)
        """
        try:
            test_requests = []
            for test in tests:
                test_requests.append(
                    TestRequest(
                        id=test.id,
                        type=test.type,
                        name=test.name,
                        title=test.title,
                        code=test.code,
                    )
                )

            message_id = str(uuid.uuid4())
            test_message = TestMessage(message_id=message_id, tests=test_requests)

            await self._send_and_receive_streaming(test_message, result_callback)

        except Exception as e:
            logger.error(f"Error executing tests: {e}")
            for test in tests:
                error_result = TestResult(
                    test_id=test.id,
                    success=False,
                    output="",
                    error=f"Test runner communication error: {str(e)}",
                )
                result_callback(test.id, error_result)

    async def _send_and_receive_streaming(
        self,
        test_message: TestMessage,
        result_callback: Callable[[str, TestResult], None],
    ) -> None:
        """Send test message to test-runner and handle streaming responses"""
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            websocket = None
            try:
                logger.info(
                    f"Attempting to connect to test-runner (attempt {attempt + 1}/{max_retries})"
                )

                websocket = await asyncio.wait_for(
                    websockets.connect(self.test_runner_url),
                    timeout=self.connection_timeout,
                )

                logger.info(f"Connected to test-runner at {self.test_runner_url}")

                streaming_message = {**test_message.model_dump(), "streaming": True}
                message_json = json.dumps(streaming_message)
                await websocket.send(message_json)
                logger.info(
                    f"Sent streaming test message {test_message.message_id} with {len(test_message.tests)} tests"
                )

                completed_tests = 0
                total_tests = len(test_message.tests)

                while completed_tests < total_tests:
                    try:
                        response_text = await asyncio.wait_for(
                            websocket.recv(), timeout=self.execution_timeout
                        )

                        response_data = json.loads(response_text)

                        if "error" in response_data:
                            logger.error(f"Test runner error: {response_data['error']}")
                            raise Exception(
                                f"Test runner error: {response_data['error']}"
                            )

                        if "test_result" in response_data:
                            individual_result = IndividualTestResult(**response_data)
                            if individual_result.message_id == test_message.message_id:
                                result_callback(
                                    individual_result.test_result.test_id,
                                    individual_result.test_result,
                                )
                                completed_tests += 1
                                logger.info(
                                    f"Received individual test result {completed_tests}/{total_tests}"
                                )

                        elif "results" in response_data:
                            test_response = TestResponse(**response_data)
                            if test_response.message_id == test_message.message_id:
                                for result in test_response.results:
                                    result_callback(result.test_id, result)
                                    completed_tests += 1
                                logger.info(
                                    f"Received batch test results: {len(test_response.results)}"
                                )
                                break

                    except asyncio.TimeoutError:
                        logger.error("Timeout waiting for test result")
                        break

                logger.info(
                    f"Completed streaming execution for message {test_message.message_id}"
                )
                return

            except asyncio.TimeoutError as e:
                logger.error(f"Timeout on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception("Test execution timeout after all retries")

            except (ConnectionClosed, InvalidURI, OSError) as e:
                logger.error(
                    f"WebSocket connection error on attempt {attempt + 1}: {e}"
                )
                if attempt == max_retries - 1:
                    raise Exception(f"Cannot connect to test runner: {str(e)}")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from test runner: {e}")
                raise Exception("Invalid response from test runner")

            except pydantic.ValidationError as e:
                logger.error(f"Invalid response format from test runner: {e}")
                raise Exception("Invalid response format from test runner")

            finally:
                if websocket:
                    await websocket.close()

            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2

        raise Exception("All connection attempts failed")

    async def _send_and_receive(self, test_message: TestMessage) -> List[TestResult]:
        """Send test message to test-runner and wait for response (legacy method)"""
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            websocket = None
            try:
                logger.info(
                    f"Attempting to connect to test-runner (attempt {attempt + 1}/{max_retries})"
                )

                websocket = await asyncio.wait_for(
                    websockets.connect(self.test_runner_url),
                    timeout=self.connection_timeout,
                )

                logger.info(f"Connected to test-runner at {self.test_runner_url}")

                message_json = test_message.model_dump_json()
                await websocket.send(message_json)
                logger.info(
                    f"Sent test message {test_message.message_id} with {len(test_message.tests)} tests"
                )

                response_text = await asyncio.wait_for(
                    websocket.recv(), timeout=self.execution_timeout
                )

                response_data = json.loads(response_text)

                if "error" in response_data:
                    logger.error(f"Test runner error: {response_data['error']}")
                    raise Exception(f"Test runner error: {response_data['error']}")

                test_response = TestResponse(**response_data)

                if test_response.message_id != test_message.message_id:
                    logger.warning(
                        f"Message ID mismatch: sent {test_message.message_id}, received {test_response.message_id}"
                    )

                logger.info(f"Received {len(test_response.results)} test results")
                return test_response.results

            except asyncio.TimeoutError as e:
                logger.error(f"Timeout on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception("Test execution timeout after all retries")

            except (ConnectionClosed, InvalidURI, OSError) as e:
                logger.error(
                    f"WebSocket connection error on attempt {attempt + 1}: {e}"
                )
                if attempt == max_retries - 1:
                    raise Exception(f"Cannot connect to test runner: {str(e)}")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from test runner: {e}")
                raise Exception("Invalid response from test runner")

            except pydantic.ValidationError as e:
                logger.error(f"Invalid response format from test runner: {e}")
                raise Exception("Invalid response format from test runner")

            finally:
                if websocket:
                    await websocket.close()

            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2

        raise Exception("All connection attempts failed")


test_runner_client = TestRunnerClient()
