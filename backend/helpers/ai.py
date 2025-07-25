import re
import typing

import anthropic
import websocket.models as models
from google import genai
from google.genai import types as genai_types


async def fetch_latest_model_async(
    client: typing.Union[anthropic.AsyncAnthropic, genai.Client],
) -> typing.Optional[str]:
    if isinstance(client, anthropic.AsyncAnthropic):
        response = await client.models.list(limit=5)

        latest_model = next(
            (model for model in response.data if "sonnet" in model.id), None
        )

        if latest_model:
            return latest_model.id

    elif isinstance(client, genai.Client):
        models = []
        model_list = await client.aio.models.list()
        async for model in model_list:
            models.append(model)

        pattern = r"^models/gemini-([\d.]+)-(pro|flash)$"

        matching_models = [
            (model, *re.match(pattern, model.name).groups())  # type: ignore
            for model in models
            if model.name and re.match(pattern, model.name)
        ]

        latest_model = (
            max(
                matching_models,
                key=lambda x: (tuple(map(int, x[1].split("."))), x[2] == "pro"),  # type: ignore
                default=(None, None, None),
            )[0]
            if matching_models
            else None
        )

        if latest_model:
            return latest_model.name


def get_async_client(
    model: models.available_ai_models, api_key: str
) -> typing.Optional[typing.Union[anthropic.AsyncAnthropic, genai.Client]]:
    if model == "sonnet":
        return anthropic.AsyncAnthropic(api_key=api_key)

    elif model == "gemini":
        return genai.Client(api_key=api_key)

    else:
        return None


async def send_request_async(
    model: models.available_ai_models,
    api_key: str,
    user_query: str,
    system_instructions: typing.Optional[str] = None,
) -> typing.Optional[
    typing.Union[
        genai_types.GenerateContentResponse,
        anthropic.types.Message,
    ]
]:
    client = get_async_client(model, api_key)

    if not client:
        raise ValueError(f"Unsupported model: {model}")

    if isinstance(client, anthropic.AsyncAnthropic):
        latest_model = await fetch_latest_model_async(client)

        if not latest_model:
            raise ValueError("No suitable model found for Anthropic.")

        response = await client.messages.create(
            model=latest_model,
            max_tokens=1024,
            system=(
                system_instructions if system_instructions else anthropic.NOT_GIVEN
            ),
            messages=[
                {
                    "role": "user",
                    "content": user_query,
                }
            ],
        )

        return response

    elif isinstance(client, genai.Client):
        latest_model = await fetch_latest_model_async(client)

        if not latest_model:
            raise ValueError("No suitable model found for Gemini.")

        response = await client.aio.models.generate_content(
            model=latest_model,
            contents=[user_query],
            config=(
                genai_types.GenerateContentConfig(
                    system_instruction=system_instructions
                )
                if system_instructions
                else None
            ),
        )

        return response


def get_text_from_response(
    response: typing.Union[
        genai_types.GenerateContentResponse,
        anthropic.types.Message,
    ],
) -> typing.Optional[str]:
    if isinstance(response, genai_types.GenerateContentResponse):
        return response.text

    elif isinstance(response, anthropic.types.Message):
        if response.content:
            return response.content[0].text  # type: ignore


async def test_bot_connection_async(
    model: models.available_ai_models, api_key: str
) -> bool:
    try:
        client = get_async_client(model, api_key)

        if not client:
            return False

        if isinstance(client, anthropic.AsyncAnthropic):
            await client.models.list(limit=1)
        elif isinstance(client, genai.Client):
            model_list = await client.aio.models.list()
            async for _ in model_list:
                break

        return True

    except Exception:
        return False


async def detect_ai_model_async(
    api_key: str,
) -> typing.Optional[models.available_ai_models]:
    if await test_bot_connection_async("gemini", api_key):
        return "gemini"

    if await test_bot_connection_async("sonnet", api_key):
        return "sonnet"

    return None


async def send_request_with_auto_detection_async(
    api_key: str,
    user_query: str,
    system_instructions: typing.Optional[str] = None,
) -> typing.Optional[
    typing.Union[
        genai_types.GenerateContentResponse,
        anthropic.types.Message,
    ]
]:
    detected_model = await detect_ai_model_async(api_key)

    if not detected_model:
        return None

    return await send_request_async(
        model=detected_model,
        api_key=api_key,
        user_query=user_query,
        system_instructions=system_instructions,
    )
