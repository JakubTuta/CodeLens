import datetime
import inspect
import re
import typing
from pathlib import Path

import hypothesis
import hypothesis.strategies

SIMPLE_TYPE_STRATEGIES = {
    int: hypothesis.strategies.integers(),
    float: hypothesis.strategies.floats(allow_nan=False, allow_infinity=False),
    str: hypothesis.strategies.text(),
    bool: hypothesis.strategies.booleans(),
    bytes: hypothesis.strategies.binary(),
    complex: hypothesis.strategies.complex_numbers(),
    type(None): hypothesis.strategies.none(),
    datetime.datetime: hypothesis.strategies.datetimes(),
    datetime.date: hypothesis.strategies.dates(),
    datetime.time: hypothesis.strategies.times(),
    datetime.timedelta: hypothesis.strategies.timedeltas(),
    Path: hypothesis.strategies.text().map(
        lambda x: Path(x.replace("/", "_").replace("\\", "_"))
    ),
}

# Extended type strategies for common Python libraries
LIBRARY_TYPE_STRATEGIES = {
    "re.Pattern": hypothesis.strategies.text().map(lambda x: re.compile(r"\w*")),
    "numpy.ndarray": hypothesis.strategies.lists(
        hypothesis.strategies.floats(allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=10,
    ),
    "pandas.DataFrame": hypothesis.strategies.dictionaries(
        hypothesis.strategies.text(min_size=1, max_size=10),
        hypothesis.strategies.lists(
            hypothesis.strategies.integers(), min_size=1, max_size=5
        ),
        min_size=1,
        max_size=3,
    ),
}


def type_to_strategy(type_hint: typing.Any) -> hypothesis.strategies.SearchStrategy:
    if type_hint in SIMPLE_TYPE_STRATEGIES:
        return SIMPLE_TYPE_STRATEGIES[type_hint]

    # Handle string representations of types (for libraries)
    if isinstance(type_hint, str) and type_hint in LIBRARY_TYPE_STRATEGIES:
        return LIBRARY_TYPE_STRATEGIES[type_hint]

    if hasattr(type_hint, "__origin__") and not isinstance(type_hint, str):
        origin = type_hint.__origin__
        args = type_hint.__args__

        if origin is typing.Union:
            if len(args) == 2 and type(None) in args:
                non_none_type = args[0] if args[1] is type(None) else args[1]
                return hypothesis.strategies.one_of(
                    hypothesis.strategies.none(), type_to_strategy(non_none_type)
                )
            return hypothesis.strategies.one_of([type_to_strategy(arg) for arg in args])

        if origin is list:
            element_strategy = (
                type_to_strategy(args[0]) if args else hypothesis.strategies.integers()
            )
            return hypothesis.strategies.lists(
                element_strategy, min_size=0, max_size=10
            )

        if origin is dict:
            key_strategy = (
                type_to_strategy(args[0])
                if len(args) > 0
                else hypothesis.strategies.text()
            )
            value_strategy = (
                type_to_strategy(args[1])
                if len(args) > 1
                else hypothesis.strategies.integers()
            )
            return hypothesis.strategies.dictionaries(
                key_strategy, value_strategy, min_size=0, max_size=5
            )

        if origin is tuple:
            if args:
                return hypothesis.strategies.tuples(
                    *(type_to_strategy(arg) for arg in args)
                )
            return hypothesis.strategies.tuples(
                hypothesis.strategies.integers(), hypothesis.strategies.text()
            )

        if origin in {set, frozenset}:
            element_strategy = (
                type_to_strategy(args[0]) if args else hypothesis.strategies.integers()
            )
            return hypothesis.strategies.sets(element_strategy, min_size=0, max_size=5)

    # Handle datetime types
    if type_hint == datetime.datetime:
        return hypothesis.strategies.datetimes()
    elif type_hint == datetime.date:
        return hypothesis.strategies.dates()
    elif type_hint == datetime.time:
        return hypothesis.strategies.times()
    elif type_hint == datetime.timedelta:
        return hypothesis.strategies.timedeltas()

    # Handle Path objects
    if type_hint == Path:
        return hypothesis.strategies.text().map(
            lambda x: Path(x.replace("/", "_").replace("\\", "_"))
        )

    return hypothesis.strategies.text()


def strategy_to_string(strategy: hypothesis.strategies.SearchStrategy) -> str:
    strategy_repr = repr(strategy)
    if "integers" in strategy_repr:
        return "st.integers()"
    if "floats" in strategy_repr:
        return "st.floats(allow_nan=False, allow_infinity=False)"
    if "text" in strategy_repr:
        return "st.text()"
    if "booleans" in strategy_repr:
        return "st.booleans()"
    if "binary" in strategy_repr:
        return "st.binary()"
    if "complex" in strategy_repr:
        return "st.complex_numbers()"
    if "lists" in strategy_repr:
        return "st.lists(st.integers(), min_size=0, max_size=10)"
    if "dictionaries" in strategy_repr:
        return "st.dictionaries(st.text(), st.integers(), min_size=0, max_size=5)"
    if "tuples" in strategy_repr:
        return "st.tuples(st.integers(), st.text())"
    if "sets" in strategy_repr:
        return "st.sets(st.integers(), min_size=0, max_size=5)"
    if "one_of" in strategy_repr:
        return "st.one_of(st.none(), st.text())"
    if "none" in strategy_repr:
        return "st.none()"
    if "datetimes" in strategy_repr:
        return "st.datetimes()"
    if "dates" in strategy_repr:
        return "st.dates()"
    if "times" in strategy_repr:
        return "st.times()"
    if "timedeltas" in strategy_repr:
        return "st.timedeltas()"
    return "st.text()"


def analyze_function_signature(
    func: typing.Callable, remove_none: bool = False
) -> dict:
    sig = inspect.signature(func)
    type_hints = typing.get_type_hints(func)

    params_info = {}
    for param_name, param in sig.parameters.items():
        param_type = type_hints.get(param_name)
        if remove_none and param_type is None:
            continue

        params_info[param_name] = {
            "name": param_name,
            "type": param_type,
            "default": (
                param.default if param.default != inspect.Parameter.empty else None
            ),
            "has_default": param.default != inspect.Parameter.empty,
        }

    return {
        "parameters": params_info,
        "return_type": type_hints.get("return", typing.Any),
        "signature": sig,
    }


def is_standard_python_type(type_hint: typing.Any) -> bool:
    if type_hint is None:
        return False
    if type_hint in SIMPLE_TYPE_STRATEGIES:
        return True

    # Check for common library types
    if isinstance(type_hint, str) and type_hint in LIBRARY_TYPE_STRATEGIES:
        return True

    # Check for datetime types
    if type_hint in {
        datetime.datetime,
        datetime.date,
        datetime.time,
        datetime.timedelta,
    }:
        return True

    # Check for Path type
    if type_hint == Path:
        return True

    if hasattr(type_hint, "__origin__") and not isinstance(type_hint, str):
        origin = type_hint.__origin__
        args = type_hint.__args__

        if origin is typing.Union:
            return all(is_standard_python_type(arg) for arg in args)

        if origin in {list, dict, tuple, set, frozenset}:
            return not args or all(is_standard_python_type(arg) for arg in args)

    return False


def filter_standard_parameters(sig_info: dict) -> dict:
    filtered_params = {
        name: info
        for name, info in sig_info["parameters"].items()
        if is_standard_python_type(info["type"])
    }
    return {**sig_info, "parameters": filtered_params}


def indent_code(code: str, spaces: int) -> str:
    indent = " " * spaces
    return "\n".join(
        indent + line if line.strip() else line for line in code.split("\n")
    )


def detect_library_usage(function_code: str) -> set:
    """Detect which libraries are used in the function code."""
    libraries = set()

    # Common library patterns
    library_patterns = {
        "numpy": ["numpy", "np.", "import numpy", "from numpy"],
        "pandas": [
            "pandas",
            "pd.",
            "import pandas",
            "from pandas",
            "DataFrame",
            "Series",
        ],
        "datetime": ["datetime", "date", "time", "timedelta"],
        "json": ["json.", "import json", "from json"],
        "requests": ["requests.", "import requests", "from requests"],
        "os": ["os.", "import os", "from os"],
        "pathlib": ["pathlib", "Path(", "import pathlib", "from pathlib"],
        "regex": ["re.", "import re", "from re", "regex", "pattern"],
        "threading": ["threading", "Thread(", "import threading"],
        "asyncio": ["asyncio", "async ", "await ", "import asyncio"],
        "math": ["math.", "import math", "from math"],
        "random": ["random.", "import random", "from random"],
        "collections": ["collections.", "import collections", "from collections"],
        "itertools": ["itertools.", "import itertools", "from itertools"],
        "functools": ["functools.", "import functools", "from functools"],
        "urllib": ["urllib.", "import urllib", "from urllib"],
        "sqlite3": ["sqlite3.", "import sqlite3", "from sqlite3"],
        "csv": ["csv.", "import csv", "from csv"],
        "xml": ["xml.", "import xml", "from xml", "ElementTree"],
        "unittest": ["unittest.", "import unittest", "from unittest"],
        "logging": ["logging.", "import logging", "from logging"],
    }

    for library, patterns in library_patterns.items():
        for pattern in patterns:
            if pattern in function_code:
                libraries.add(library)
                break

    return libraries


def generate_sample_data_for_type(param_type: typing.Any) -> str:
    """Generate sample data string for a given type."""
    if param_type == int:
        return "42"
    elif param_type == float:
        return "3.14"
    elif param_type == str:
        return "'test_string'"
    elif param_type == bool:
        return "True"
    elif param_type == bytes:
        return "b'test_bytes'"
    elif param_type == complex:
        return "1+2j"
    elif param_type == list:
        return "[1, 2, 3, 4, 5]"
    elif param_type == dict:
        return "{'key': 'value', 'number': 42}"
    elif param_type == tuple:
        return "(1, 2, 3)"
    elif param_type == set:
        return "{1, 2, 3, 4, 5}"
    elif param_type == datetime.datetime:
        return "datetime.datetime.now()"
    elif param_type == datetime.date:
        return "datetime.date.today()"
    elif param_type == datetime.time:
        return "datetime.time(12, 30, 45)"
    elif param_type == datetime.timedelta:
        return "datetime.timedelta(days=1, hours=2)"
    elif param_type == Path:
        return "Path('test_path.txt')"
    else:
        return "None"


def get_library_specific_imports(libraries: set) -> list:
    """Get imports needed for detected libraries."""
    library_imports = {
        "numpy": [
            "try:",
            "    import numpy as np",
            "except ImportError:",
            '    pytest.skip("NumPy not available")',
        ],
        "pandas": [
            "try:",
            "    import pandas as pd",
            "except ImportError:",
            '    pytest.skip("Pandas not available")',
        ],
        "requests": [
            "try:",
            "    import requests",
            "except ImportError:",
            '    pytest.skip("Requests not available")',
        ],
        "sqlite3": ["import sqlite3"],
        "csv": ["import csv"],
        "xml": ["import xml.etree.ElementTree as ET"],
        "urllib": ["import urllib.request", "import urllib.parse"],
        "logging": ["import logging"],
        "threading": ["import threading"],
        "asyncio": ["import asyncio"],
        "math": ["import math"],
        "random": ["import random"],
        "collections": ["import collections"],
        "itertools": ["import itertools"],
        "functools": ["import functools"],
    }

    imports = []
    for library in libraries:
        if library in library_imports:
            imports.extend(library_imports[library])

    return imports
