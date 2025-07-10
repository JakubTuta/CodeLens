import typing

import pydantic

response_message_types = typing.Literal[
    "error",
    "return_unit_tests",
    "return_memory_tests",
    "return_performance_tests",
    "return_docs",
    "return_improvements",
    "test_generation_started",
]

message_types = {
    "request": {
        "send_code",
    },
    "response": {
        "error",
        "return_unit_tests",
        "return_memory_tests",
        "return_performance_tests",
        "return_docs",
        "return_improvements",
        "test_generation_started",
    },
}


class RequestMessage(pydantic.BaseModel):
    type: typing.Literal["send_code"]
    code: str
    language: typing.Literal["python"]


class Test(pydantic.BaseModel):
    type: typing.Literal["unit", "memory", "performance"]
    name: str
    code: str


class ResponseMessage(pydantic.BaseModel):
    type: response_message_types

    # Error message or general message
    error_message: typing.Optional[str] = None

    # Tests
    unit_tests: typing.Optional[typing.List[Test]] = None
    memory_tests: typing.Optional[typing.List[Test]] = None
    performance_tests: typing.Optional[typing.List[Test]] = None
