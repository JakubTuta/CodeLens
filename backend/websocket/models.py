import typing

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
]

message_types = {
    "request": {
        "generate_tests",
        "generate_docs",
        "generate_improvements",
        "test_ai",
        "verify_code",
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
    },
}


class RequestMessage(pydantic.BaseModel):
    id: str
    type: typing.Literal["generate_tests", "generate_docs", "generate_improvements", "test_ai", "verify_code"]
    code: typing.Optional[str] = None
    language: typing.Optional[typing.Literal["python"]] = None


class Test(pydantic.BaseModel):
    type: typing.Literal["unit", "memory", "performance"]
    name: str
    title: str
    code: str


class ResponseMessage(pydantic.BaseModel):
    id: str
    type: response_message_types

    # Error message or general message
    error_message: typing.Optional[str] = None

    # Tests
    unit_tests: typing.Optional[typing.List[Test]] = None
    memory_tests: typing.Optional[typing.List[Test]] = None
    performance_tests: typing.Optional[typing.List[Test]] = None

    # Documentation
    docs: typing.Optional[str] = None

    # Improvements
    improvements: typing.Optional[typing.List[str]] = None

    # AI test / code verification result
    is_ok: typing.Optional[bool] = None

    # Detected AI model name
    detected_model: typing.Optional[available_ai_models] = None
