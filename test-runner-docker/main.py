import asyncio
import json
import uuid
from typing import List, Optional

import docker
import fastapi
import pydantic
import uvicorn
from docker.errors import APIError, ContainerError, ImageNotFound
from fastapi.middleware.cors import CORSMiddleware

CONTAINER_IMAGE = "codelens-test-executor:latest"
CPU_LIMIT = int(0.5 * 1e9)
MEMORY_LIMIT = "512m"
CONTAINER_TIMEOUT_SECONDS = 120

app = fastapi.FastAPI(title="CodeLens Test Runner (Docker)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TestRequest(pydantic.BaseModel):
    id: str
    type: str
    name: str
    title: str
    code: str


class TestMessage(pydantic.BaseModel):
    message_id: str
    tests: List[TestRequest]
    streaming: bool = False


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


class DockerTestRunner:
    def __init__(self):
        global CONTAINER_IMAGE
        try:
            self.client = docker.from_env()
            self.client.ping()

            try:
                self.client.images.get(CONTAINER_IMAGE)
            except docker.errors.ImageNotFound:
                CONTAINER_IMAGE = "python:3.12.9-alpine"

        except Exception as e:
            raise

    async def execute_tests(self, tests: List[TestRequest]) -> List[TestResult]:
        """Execute multiple tests concurrently in separate Docker containers"""
        tasks = []
        for test in tests:
            task = asyncio.create_task(self._execute_single_test(test))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    TestResult(
                        test_id=tests[i].id, success=False, output="", error=str(result)
                    )
                )
            else:
                final_results.append(result)

        return final_results

    async def _execute_single_test(self, test: TestRequest) -> TestResult:
        """Execute a single test in a Docker container"""
        container_name = f"test-{test.id.lower()}-{uuid.uuid4().hex[:8]}"

        try:
            # Use heredoc to write test file - handles all special characters safely
            # Add verbose output to debug
            if CONTAINER_IMAGE == "codelens-test-executor:latest":
                # Write the test code using heredoc and execute it
                command = [
                    "sh",
                    "-c",
                    f"""set -x
cat > /test/test_code.py << 'EOFMARKER'
{test.code}
EOFMARKER
echo "File created, size:"
ls -lh /test/test_code.py
echo "File contents:"
cat /test/test_code.py
echo "Running test:"
python /test/test_code.py
""",
                ]
            else:
                if test.type in ["unit", "memory", "performance"]:
                    command = [
                        "sh",
                        "-c",
                        f"""set -x
pip install --quiet hypothesis pytest memory-profiler psutil
cat > /test/test_code.py << 'EOFMARKER'
{test.code}
EOFMARKER
cd /test
python test_code.py
""",
                    ]
                else:
                    command = [
                        "sh",
                        "-c",
                        f"""set -x
cat > /test/test_code.py << 'EOFMARKER'
{test.code}
EOFMARKER
cd /test
python test_code.py
""",
                    ]

            start_time = asyncio.get_event_loop().time()

            try:
                container = await asyncio.to_thread(
                    self.client.containers.run,
                    image=CONTAINER_IMAGE,
                    command=command,
                    name=container_name,
                    detach=True,
                    remove=True,  # Auto-remove container after execution
                    mem_limit=MEMORY_LIMIT,
                    nano_cpus=CPU_LIMIT,
                )
            except Exception as e:
                raise

            # Wait for container to finish
            try:
                result = await asyncio.to_thread(
                    container.wait, timeout=CONTAINER_TIMEOUT_SECONDS
                )
            except Exception as e:
                raise

            execution_time = asyncio.get_event_loop().time() - start_time

            # Get logs (container will auto-remove after we're done)
            logs_bytes = await asyncio.to_thread(container.logs)
            logs = (
                logs_bytes.decode("utf-8")
                if isinstance(logs_bytes, bytes)
                else logs_bytes
            )

            # Get exit code
            exit_code = result.get("StatusCode", 1)
            success = exit_code == 0

            return TestResult(
                test_id=test.id,
                success=success,
                output=logs,
                error=(
                    None
                    if success
                    else f"Test execution failed (exit code: {exit_code})"
                ),
                execution_time=execution_time,
            )

        except ContainerError as e:
            stderr = e.stderr.decode() if e.stderr else ""
            return TestResult(
                test_id=test.id,
                success=False,
                output=stderr,
                error=f"Container error: {str(e)}",
            )

        except ImageNotFound as e:
            return TestResult(
                test_id=test.id,
                success=False,
                output="",
                error=f"Docker image not found: {CONTAINER_IMAGE}. Please run: docker-compose up -d --build",
            )

        except APIError as e:
            return TestResult(
                test_id=test.id,
                success=False,
                output="",
                error=f"Docker API error: {str(e)}",
            )

        except Exception as e:
            return TestResult(
                test_id=test.id,
                success=False,
                output="",
                error=f"Execution error: {str(e)}",
            )


test_runner = DockerTestRunner()


@app.websocket("/ws")
async def websocket_endpoint(websocket: fastapi.WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)

                if message_data.get("type") == "ping":
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "pong",
                                "message_id": message_data.get("message_id", ""),
                            }
                        )
                    )
                    continue

                test_message = TestMessage(**message_data)

                if test_message.streaming:

                    async def execute_and_send_with_id(test: TestRequest):
                        try:
                            result = await test_runner._execute_single_test(test)

                            individual_result = IndividualTestResult(
                                message_id=test_message.message_id, test_result=result
                            )
                            await websocket.send_text(
                                individual_result.model_dump_json()
                            )

                        except Exception as e:
                            error_result = TestResult(
                                test_id=test.id, success=False, output="", error=str(e)
                            )
                            individual_result = IndividualTestResult(
                                message_id=test_message.message_id,
                                test_result=error_result,
                            )
                            await websocket.send_text(
                                individual_result.model_dump_json()
                            )

                    tasks = []
                    for test in test_message.tests:
                        task = asyncio.create_task(execute_and_send_with_id(test))
                        tasks.append(task)

                    await asyncio.gather(*tasks, return_exceptions=True)

                else:
                    results = await test_runner.execute_tests(test_message.tests)

                    response = TestResponse(
                        message_id=test_message.message_id, results=results
                    )

                    await websocket.send_text(response.model_dump_json())

            except json.JSONDecodeError as e:
                await websocket.send_text(
                    json.dumps({"error": "Invalid JSON format", "details": str(e)})
                )

            except pydantic.ValidationError as e:
                await websocket.send_text(
                    json.dumps({"error": "Invalid message format", "details": str(e)})
                )

            except Exception as e:
                await websocket.send_text(
                    json.dumps({"error": "Internal server error", "details": str(e)})
                )

    except fastapi.WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
