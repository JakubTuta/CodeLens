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
    type: models.response_message_types,
    error_message: typing.Optional[str] = None,
    unit_tests: typing.Optional[typing.List[models.Test]] = None,
    memory_tests: typing.Optional[typing.List[models.Test]] = None,
    performance_tests: typing.Optional[typing.List[models.Test]] = None,
    docs: typing.Optional[str] = None,
) -> models.ResponseMessage:
    return models.ResponseMessage(
        type=type,
        error_message=error_message,
        unit_tests=unit_tests,
        memory_tests=memory_tests,
        performance_tests=performance_tests,
        docs=docs,
    )


async def prepare_and_send_response_message(
    websocket: typing.Any, response_message: models.ResponseMessage
) -> None:
    await websocket.send_json(response_message.model_dump())
