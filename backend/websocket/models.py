import typing

import pydantic

message_types = {
    "request": {
        "send_code",
    },
    "response": {
        "error" "return_tests",
        "return_docs",
        "return_improvements",
    },
}


class RequestMessage(pydantic.BaseModel):
    type: typing.Literal["send_code"]
    code: str
    language: typing.Literal["python"]


class ResponseMessage(pydantic.BaseModel):
    type: typing.Literal[
        "error",
        "return_tests",
        "return_docs",
        "return_improvements",
    ]
    message: typing.Optional[str] = None
    tests: typing.Optional[typing.List[str]] = None
