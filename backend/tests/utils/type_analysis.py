import datetime
import inspect
import pathlib
import typing


def analyze_function_signature(
    func: typing.Callable, remove_none: bool = False
) -> dict:
    """Analyze function signature and extract parameter information."""
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
    """Check if a type hint is a standard Python type that can be easily tested."""
    from .strategy_mapping import LIBRARY_TYPE_STRATEGIES, SIMPLE_TYPE_STRATEGIES

    if type_hint is None:
        return False
    if type_hint in SIMPLE_TYPE_STRATEGIES:
        return True

    if isinstance(type_hint, str) and type_hint in LIBRARY_TYPE_STRATEGIES:
        return True

    if type_hint in {
        datetime.datetime,
        datetime.date,
        datetime.time,
        datetime.timedelta,
    }:
        return True

    if type_hint == pathlib.Path:
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
    """Filter parameters to only include those with standard Python types."""
    filtered_params = {
        name: info
        for name, info in sig_info["parameters"].items()
        if is_standard_python_type(info["type"])
    }
    return {**sig_info, "parameters": filtered_params}


def detect_library_usage(function_code: str) -> set:
    """Detect which libraries are used in the function code."""
    libraries = set()

    library_patterns = {
        "numpy": [
            "numpy",
            "np.",
            "import numpy",
            "from numpy",
            "ndarray",
            "np.array",
            "np.ndarray",
        ],
        "pandas": [
            "pandas",
            "pd.",
            "import pandas",
            "from pandas",
            "DataFrame",
            "Series",
            "pd.DataFrame",
            "pd.Series",
        ],
        "datetime": ["datetime", "date", "time", "timedelta"],
        "json": ["json.", "import json", "from json"],
        "requests": ["requests.", "import requests", "from requests", "Response"],
        "os": ["os.", "import os", "from os"],
        "pathlib": ["pathlib", "Path(", "import pathlib", "from pathlib", "Path"],
        "regex": ["re.", "import re", "from re", "regex", "pattern", "Pattern"],
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
        "matplotlib": ["matplotlib", "plt.", "import matplotlib", "pyplot", "Figure"],
        "scipy": ["scipy", "import scipy", "from scipy"],
        "tensorflow": ["tensorflow", "tf.", "import tensorflow", "Tensor", "tf.Tensor"],
        "torch": ["torch", "import torch", "from torch", "torch.Tensor"],
    }

    for library, patterns in library_patterns.items():
        for pattern in patterns:
            if pattern in function_code:
                libraries.add(library)
                break

    return libraries
