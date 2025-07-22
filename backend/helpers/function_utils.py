import ast
import inspect
import typing

import fastapi


def validate_single_function(function_text: str) -> bool:
    try:
        tree = ast.parse(function_text.strip())

        if len(tree.body) != 1:
            return False

        node = tree.body[0]
        if not isinstance(node, ast.FunctionDef):
            return False

        compile(function_text, "<string>", "exec")

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                return False

        return True

    except (SyntaxError, IndentationError, TypeError):
        return False


def text_to_function(function_text: str) -> typing.Callable[..., typing.Any]:
    if not validate_single_function(function_text):
        raise ValueError("Invalid function text")

    namespace = {}
    exec(function_text, namespace)

    for obj in namespace.values():
        if callable(obj) and hasattr(obj, "__code__"):
            return obj

    raise ValueError("No function found in the provided text")


def function_to_text(func: typing.Callable) -> str:
    try:
        source = inspect.getsource(func)
        lines = source.split("\n")

        if lines and lines[0].strip():
            non_empty_lines = [line for line in lines if line.strip()]

            if non_empty_lines:
                min_indent = min(
                    len(line) - len(line.lstrip()) for line in non_empty_lines
                )
                source = "\n".join(
                    line[min_indent:] if len(line) > min_indent else line
                    for line in lines
                )

        if not validate_single_function(source):
            raise ValueError("Function source is not valid")

        return source.strip()

    except (OSError, TypeError) as e:
        raise ValueError(f"Cannot get source code: {e}")


def get_function_name(func: typing.Callable) -> str:
    if not callable(func):
        raise ValueError("Provided object is not callable")

    if hasattr(func, "__name__"):
        return func.__name__
    else:
        raise ValueError("Function does not have a name attribute")


def get_bot_information(websocket: fastapi.WebSocket):
    cookies = websocket.cookies
    ai_model = cookies.get("aiModel", None)
    ai_api_key = cookies.get("aiApiKey", None)

    if not ai_model or not ai_api_key:
        raise Exception("AI model or API key not provided in cookies.")

    return ai_model, ai_api_key


def get_api_key_from_cookies(websocket: fastapi.WebSocket):
    cookies = websocket.cookies
    ai_api_key = cookies.get("aiApiKey", None)

    if not ai_api_key:
        raise Exception("API key not provided in cookies.")

    return ai_api_key
