import asyncio
import json
import logging
import os
import uuid
from typing import List, Optional

import fastapi
import pydantic
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
from kubernetes.client.rest import ApiException

KUBERNETES_NAMESPACE = "default"
JOB_TTL_SECONDS = 300
JOB_TIMEOUT_SECONDS = 120
# Use environment variable for test executor image, default to local image
CONTAINER_IMAGE = os.getenv("TEST_EXECUTOR_IMAGE", "codelens-k8s-test-executor:latest")
FALLBACK_IMAGE = "python:3.12.9-alpine"
CPU_LIMIT = "500m"
MEMORY_LIMIT = "512Mi"
CPU_REQUEST = "100m"
MEMORY_REQUEST = "128Mi"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = fastapi.FastAPI(title="CodeLens Test Runner")

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


class KubernetesTestRunner:
    def __init__(self):
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes configuration")
        except Exception:
            try:
                config.load_kube_config()
                logger.info("Loaded local Kubernetes configuration")
            except Exception as e:
                logger.error(f"Failed to load Kubernetes configuration: {e}")
                raise

        self.core_v1 = client.CoreV1Api()
        self.batch_v1 = client.BatchV1Api()
        self.namespace = KUBERNETES_NAMESPACE

    async def execute_tests(self, tests: List[TestRequest]) -> List[TestResult]:
        """Execute multiple tests concurrently in separate Kubernetes Jobs"""
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

    async def execute_tests_streaming(
        self, tests: List[TestRequest], websocket
    ) -> None:
        """Execute multiple tests concurrently and send results as they complete"""

        async def execute_and_send(test: TestRequest, message_id: str):
            try:
                result = await self._execute_single_test(test)

                individual_result = IndividualTestResult(
                    message_id=message_id, test_result=result
                )
                await websocket.send_text(individual_result.model_dump_json())
                logger.info(f"Sent individual result for test {test.id}")

            except Exception as e:
                error_result = TestResult(
                    test_id=test.id, success=False, output="", error=str(e)
                )
                individual_result = IndividualTestResult(
                    message_id=message_id, test_result=error_result
                )
                await websocket.send_text(individual_result.model_dump_json())
                logger.error(f"Sent error result for test {test.id}: {e}")

        tasks = []
        for test in tests:
            task = asyncio.create_task(execute_and_send(test, ""))
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_single_test(self, test: TestRequest) -> TestResult:
        """Execute a single test in a Kubernetes Job"""
        job_name = f"test-{test.id.lower()}-{uuid.uuid4().hex[:8]}"

        try:
            configmap = await self._create_test_configmap(job_name, test.code)

            job = await self._create_test_job(job_name, test.type)

            result = await self._wait_for_job_completion(job_name, test.id)

            await self._cleanup_resources(job_name)

            return result

        except Exception as e:
            logger.error(f"Error executing test {test.id}: {e}")
            await self._cleanup_resources(job_name)
            return TestResult(
                test_id=test.id,
                success=False,
                output="",
                error=f"Execution error: {str(e)}",
            )

    async def _create_test_configmap(
        self, job_name: str, test_code: str
    ) -> client.V1ConfigMap:
        """Create a ConfigMap containing the test code"""
        configmap = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(
                name=f"{job_name}-code", namespace=self.namespace
            ),
            data={"test_code.py": test_code},
        )

        return self.core_v1.create_namespaced_config_map(
            namespace=self.namespace, body=configmap
        )

    async def _create_test_job(self, job_name: str, test_type: str) -> client.V1Job:
        """Create a Kubernetes Job to run the test"""

        # Using optimized image with pre-installed packages
        if "codelens-k8s-test-executor" in CONTAINER_IMAGE:
            image = CONTAINER_IMAGE
            # Packages already installed, just run the test
            command = ["sh", "-c", "cd /test && python test_code.py"]
        else:
            # Fallback to base Python image with runtime package installation
            if test_type in ["unit", "memory", "performance"]:
                image = FALLBACK_IMAGE
                command = [
                    "sh",
                    "-c",
                    "pip install --quiet hypothesis pytest memory-profiler psutil && "
                    "cd /test && python test_code.py",
                ]
            else:
                image = FALLBACK_IMAGE
                command = ["sh", "-c", "cd /test && python test_code.py"]

        job = client.V1Job(
            metadata=client.V1ObjectMeta(name=job_name, namespace=self.namespace),
            spec=client.V1JobSpec(
                ttl_seconds_after_finished=JOB_TTL_SECONDS,
                backoff_limit=0,
                template=client.V1PodTemplateSpec(
                    spec=client.V1PodSpec(
                        restart_policy="Never",
                        containers=[
                            client.V1Container(
                                name="test-executor",
                                image=image,
                                command=command,
                                volume_mounts=[
                                    client.V1VolumeMount(
                                        name="test-code", mount_path="/test"
                                    )
                                ],
                                resources=client.V1ResourceRequirements(
                                    limits={"cpu": CPU_LIMIT, "memory": MEMORY_LIMIT},
                                    requests={
                                        "cpu": CPU_REQUEST,
                                        "memory": MEMORY_REQUEST,
                                    },
                                ),
                            )
                        ],
                        volumes=[
                            client.V1Volume(
                                name="test-code",
                                config_map=client.V1ConfigMapVolumeSource(
                                    name=f"{job_name}-code"
                                ),
                            )
                        ],
                    )
                ),
            ),
        )

        return self.batch_v1.create_namespaced_job(namespace=self.namespace, body=job)

    async def _wait_for_job_completion(
        self, job_name: str, test_id: str, timeout: int = JOB_TIMEOUT_SECONDS
    ) -> TestResult:
        """Wait for job completion and retrieve results"""
        start_time = asyncio.get_event_loop().time()

        while True:
            try:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    return TestResult(
                        test_id=test_id,
                        success=False,
                        output="",
                        error="Test execution timeout",
                    )

                job = self.batch_v1.read_namespaced_job(
                    name=job_name, namespace=self.namespace
                )

                if job.status.succeeded:
                    logs = await self._get_pod_logs(job_name)
                    execution_time = asyncio.get_event_loop().time() - start_time

                    return TestResult(
                        test_id=test_id,
                        success=True,
                        output=logs,
                        execution_time=execution_time,
                    )

                elif job.status.failed:
                    logs = await self._get_pod_logs(job_name)

                    return TestResult(
                        test_id=test_id,
                        success=False,
                        output=logs,
                        error="Test execution failed",
                    )

                await asyncio.sleep(2)

            except ApiException as e:
                return TestResult(
                    test_id=test_id,
                    success=False,
                    output="",
                    error=f"Kubernetes API error: {e}",
                )

    async def _get_pod_logs(self, job_name: str) -> str:
        """Get logs from the job's pod"""
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=self.namespace, label_selector=f"job-name={job_name}"
            )

            if not pods.items:
                return "No pod found for job"

            pod_name = pods.items[0].metadata.name

            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name, namespace=self.namespace, container="test-executor"
            )

            return logs

        except Exception as e:
            return f"Failed to retrieve logs: {str(e)}"

    async def _cleanup_resources(self, job_name: str):
        """Clean up job and related resources"""
        try:
            self.batch_v1.delete_namespaced_job(
                name=job_name, namespace=self.namespace, propagation_policy="Background"
            )

            self.core_v1.delete_namespaced_config_map(
                name=f"{job_name}-code", namespace=self.namespace
            )

        except Exception as e:
            logger.warning(f"Failed to cleanup resources for {job_name}: {e}")


test_runner = KubernetesTestRunner()


@app.websocket("/ws")
async def websocket_endpoint(websocket: fastapi.WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established with main backend")

    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message from backend: {data[:100]}...")

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

                logger.info(
                    f"Processing {len(test_message.tests)} tests for message {test_message.message_id}"
                )

                if test_message.streaming:
                    logger.info(
                        f"Using streaming mode for message {test_message.message_id}"
                    )

                    async def execute_and_send_with_id(test: TestRequest):
                        try:
                            result = await test_runner._execute_single_test(test)

                            individual_result = IndividualTestResult(
                                message_id=test_message.message_id, test_result=result
                            )
                            await websocket.send_text(
                                individual_result.model_dump_json()
                            )
                            logger.info(f"Sent individual result for test {test.id}")

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
                            logger.error(f"Sent error result for test {test.id}: {e}")

                    tasks = []
                    for test in test_message.tests:
                        task = asyncio.create_task(execute_and_send_with_id(test))
                        tasks.append(task)

                    await asyncio.gather(*tasks, return_exceptions=True)
                    logger.info(
                        f"Completed streaming execution for message {test_message.message_id}"
                    )

                else:
                    results = await test_runner.execute_tests(test_message.tests)

                    response = TestResponse(
                        message_id=test_message.message_id, results=results
                    )

                    await websocket.send_text(response.model_dump_json())
                    logger.info(
                        f"Sent batch results for message {test_message.message_id}"
                    )

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await websocket.send_text(
                    json.dumps({"error": "Invalid JSON format", "details": str(e)})
                )

            except pydantic.ValidationError as e:
                logger.error(f"Invalid message format: {e}")
                await websocket.send_text(
                    json.dumps({"error": "Invalid message format", "details": str(e)})
                )

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_text(
                    json.dumps({"error": "Internal server error", "details": str(e)})
                )

    except fastapi.WebSocketDisconnect:
        logger.info("WebSocket connection closed by client")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
