import typing

import pydantic

from . import models


def validate_request_message(
    message: typing.Dict[str, typing.Any],
) -> typing.Optional[models.RequestMessage]:
    try:
        validated_message = models.RequestMessage(**message)

        return validated_message

    except pydantic.ValidationError:
        return


def prepare_response_message(
    type: typing.Literal[
        "error",
        "return_tests",
        "return_docs",
        "return_improvements",
    ],
    message: typing.Optional[str] = None,
    tests: typing.Optional[typing.List[str]] = None,
) -> models.ResponseMessage:
    return models.ResponseMessage(
        type=type,
        message=message,
        tests=tests,
    )
