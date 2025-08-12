import datetime
import pathlib
import typing


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
    elif param_type == pathlib.Path:
        return "Path('test_path.txt')"

    # Handle third-party library types
    elif hasattr(param_type, "__name__"):
        type_name = param_type.__name__
        if "ndarray" in type_name.lower():
            return "np.array([1, 2, 3, 4, 5])"
        elif "dataframe" in type_name.lower():
            return "pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})"
        elif "series" in type_name.lower():
            return "pd.Series([1, 2, 3, 4, 5])"
        elif "response" in type_name.lower():
            return "requests.get('https://httpbin.org/get')"
        elif "tensor" in type_name.lower():
            if "torch" in str(param_type):
                return "torch.tensor([1, 2, 3, 4, 5])"
            else:
                return "tf.constant([1, 2, 3, 4, 5])"
        elif "figure" in type_name.lower():
            return "plt.figure()"
        elif "pattern" in type_name.lower():
            return "re.compile(r'\\d+')"

    # Handle string type annotations (for when actual types aren't available)
    elif isinstance(param_type, str):
        if "ndarray" in param_type.lower():
            return "np.array([1, 2, 3, 4, 5])"
        elif "dataframe" in param_type.lower():
            return "pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})"
        elif "series" in param_type.lower():
            return "pd.Series([1, 2, 3, 4, 5])"
        elif "response" in param_type.lower():
            return "requests.get('https://httpbin.org/get')"
        elif "tensor" in param_type.lower():
            return "torch.tensor([1, 2, 3, 4, 5])"
        elif "figure" in param_type.lower():
            return "plt.figure()"
        elif "pattern" in param_type.lower():
            return "re.compile(r'\\d+')"

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
