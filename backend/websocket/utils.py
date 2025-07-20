import typing

import fastapi
import pydantic

from . import models


async def send_error_message(websocket: fastapi.WebSocket, error_message: str):
    response_message = prepare_response_message(
        message_type="error",
        error_message=error_message,
    )
    await send_response_message(websocket, response_message)


def validate_request_message(
    message: typing.Dict[str, typing.Any],
) -> typing.Optional[models.RequestMessage]:
    try:
        validated_message = models.RequestMessage(**message)

        return validated_message

    except pydantic.ValidationError:
        return


def prepare_response_message(
    message_type: models.response_message_types,
    error_message: typing.Optional[str] = None,
    unit_tests: typing.Optional[typing.List[models.Test]] = None,
    memory_tests: typing.Optional[typing.List[models.Test]] = None,
    performance_tests: typing.Optional[typing.List[models.Test]] = None,
    docs: typing.Optional[str] = None,
    improvements: typing.Optional[typing.List[str]] = None,
    is_ok: typing.Optional[bool] = None,
) -> models.ResponseMessage:
    return models.ResponseMessage(
        type=message_type,
        error_message=error_message,
        unit_tests=unit_tests,
        memory_tests=memory_tests,
        performance_tests=performance_tests,
        docs=docs,
        improvements=improvements,
        is_ok=is_ok,
    )


async def send_response_message(
    websocket: typing.Any, response_message: models.ResponseMessage
) -> None:
    await websocket.send_json(response_message.model_dump())
