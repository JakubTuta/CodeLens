import typing
import uuid

import pydantic

available_ai_models = typing.Literal["gemini", "sonnet"]

response_message_types = typing.Literal[
    "error",
    "return_unit_tests",
    "return_memory_tests",
    "return_performance_tests",
    "return_docs",
    "return_improvements",
    "ai_test_result",
    "verify_code_result",
    "test_result_update",
]

message_types = {
    "request": {
        "generate_tests",
        "generate_docs",
        "generate_improvements",
        "test_ai",
        "verify_code",
        "run_tests",
    },
    "response": {
        "error",
        "return_unit_tests",
        "return_memory_tests",
        "return_performance_tests",
        "return_docs",
        "return_improvements",
        "ai_test_result",
        "verify_code_result",
        "test_result_update",
    },
}


class RequestMessage(pydantic.BaseModel):
    id: str
    type: typing.Literal[
        "generate_tests",
        "generate_docs",
        "generate_improvements",
        "test_ai",
        "verify_code",
        "run_tests",
    ]
    code: typing.Optional[str] = None
    language: typing.Optional[typing.Literal["python"]] = None
    ai_model: typing.Optional[available_ai_models] = None
    ai_api_key: typing.Optional[str] = None
    generate_tests: bool = True
    generate_docs: bool = True
    generate_improvements: bool = True
    tests: typing.Optional[typing.List["Test"]] = None


class Test(pydantic.BaseModel):
    id: str = pydantic.Field(default_factory=lambda: str(uuid.uuid4()))
    type: typing.Literal["unit", "memory", "performance"]
    name: str
    title: str
    code: str

    status: typing.Optional[
        typing.Literal["pending", "running", "success", "failed"]
    ] = "pending"

    execution_success: typing.Optional[bool] = None
    execution_output: typing.Optional[str] = None
    execution_error: typing.Optional[str] = None
    execution_time: typing.Optional[float] = None


class ResponseMessage(pydantic.BaseModel):
    id: str
    type: response_message_types

    error_message: typing.Optional[str] = None

    unit_tests: typing.Optional[typing.List[Test]] = None
    memory_tests: typing.Optional[typing.List[Test]] = None
    performance_tests: typing.Optional[typing.List[Test]] = None

    docs: typing.Optional[str] = None

    improvements: typing.Optional[typing.List[str]] = None

    is_ok: typing.Optional[bool] = None

    detected_model: typing.Optional[available_ai_models] = None

    test_result: typing.Optional[Test] = None
