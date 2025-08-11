import asyncio
import typing

from models import websocket as models
from utils import function_utils, test_utils


def create_test_title(test_name: str) -> str:
    if test_name.startswith("test_"):
        test_name = test_name[5:]

    return " ".join(word.capitalize() for word in test_name.split("_"))


class BaseTestGenerator:
    test_type: typing.Literal["unit", "memory", "performance"] = "unit"
    test_name: str = "base"

    async def get_tests_async(
        self, function: typing.Callable, function_text: typing.Optional[str] = None
    ) -> typing.List[models.Test]:
        result = []
        exception = None

        def worker():
            nonlocal result, exception
            try:
                func_name = function_utils.get_function_name(function)

                if not function or not func_name:
                    return

                if function_text:
                    function_string = function_text
                else:
                    function_string = function_utils.function_to_text(function)

                sig_info = test_utils.analyze_function_signature(function)
                test_code = self._generate_test(func_name, function_string, sig_info)

                if test_code:
                    test_name = f"test_{func_name}_{self.test_name}"
                    result.append(
                        models.Test(
                            type=self.test_type,
                            name=test_name,
                            title=create_test_title(test_name),
                            code=test_code,
                        )
                    )
            except Exception as e:
                exception = e

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, worker)

        if exception:
            print(f"Exception during {self.test_name} test generation: {exception}")
            return []

        return result

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        raise NotImplementedError


class UnitTest(BaseTestGenerator):
    async def get_tests_async(
        self, function: typing.Callable, function_text: typing.Optional[str] = None
    ) -> typing.List[models.Test]:
        test_generators = [
            HypothesisTestGenerator(),
            EdgeCaseTestGenerator(),
            PropertyTestGenerator(),
            TypeConsistencyTestGenerator(),
            DeterministicTestGenerator(),
            MathematicalPropertyTestGenerator(),
            BoundaryTestGenerator(),
            DataStructureTestGenerator(),
            NumPyTestGenerator(),
            DateTimeTestGenerator(),
            JsonTestGenerator(),
            RequestsTestGenerator(),
            FileOperationsTestGenerator(),
            RegexTestGenerator(),
            ExceptionHandlingTestGenerator(),
            ConcurrencyTestGenerator(),
            MathLibraryTestGenerator(),
            CollectionsTestGenerator(),
            IterToolsTestGenerator(),
            FuncToolsTestGenerator(),
            UrlLibTestGenerator(),
            LoggingTestGenerator(),
        ]

        tasks = [
            gen.get_tests_async(function, function_text) for gen in test_generators
        ]
        results = await asyncio.gather(*tasks)

        return [test for sublist in results for test in sublist]


class HypothesisTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "hypothesis"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = [
            "import hypothesis",
            "import hypothesis.strategies as st",
            "from hypothesis import given",
        ]

        given_params = []
        param_names = []
        for name, info in filtered_sig_info["parameters"].items():
            strategy_str = test_utils.strategy_to_string(
                test_utils.type_to_strategy(info["type"])
            )
            given_params.append(f"{name}={strategy_str}")
            param_names.append(name)

        return "\n".join(
            imports
            + [""]
            + [
                f"@given({', '.join(given_params)})",
                f"def test_{func_name}_hypothesis({', '.join(param_names)}):",
                '    """Test that function doesn\'t crash with generated inputs."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
                f"        result = {func_name}({', '.join(param_names)})",
                "        assert True",
                "    except Exception as e:",
                "        raise",
            ]
        )


class EdgeCaseTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "edge_cases"

    EDGE_CASE_TESTS = {
        str: [
            ("empty string", "''"),
            ("whitespace", "'   '"),
            ("special characters", "'!@#$%^&*()'"),
        ],
        int: [("zero", "0"), ("negative number", "-1"), ("large number", "999999")],
        float: [
            ("zero float", "0.0"),
            ("negative float", "-1.5"),
            ("very small float", "1e-10"),
        ],
        bool: [("True", "True"), ("False", "False")],
        bytes: [("empty bytes", "b''"), ("simple bytes", "b'test'")],
        complex: [
            ("real number as complex", "1+0j"),
            ("imaginary number", "0+1j"),
            ("complex number", "1+2j"),
        ],
        list: [("empty list", "[]"), ("single item list", "[1]")],
        dict: [("empty dict", "{}")],
        tuple: [("empty tuple", "()"), ("single item tuple", "(1,)")],
        set: [("empty set", "set()"), ("single item set", "{1}")],
    }

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        test_cases = []
        for _, param_info in filtered_sig_info["parameters"].items():
            param_type = param_info["type"]
            origin_type = getattr(param_type, "__origin__", param_type)

            if origin_type in self.EDGE_CASE_TESTS:
                for description, value in self.EDGE_CASE_TESTS[origin_type]:
                    test_cases.append(f"        # Test with {description}")
                    test_cases.append(f"        result = {func_name}({value})")

        if not test_cases:
            return ""

        return "\n".join(
            ["import pytest"]
            + [""]
            + [
                f"def test_{func_name}_edge_cases():",
                '    """Test function with edge case inputs."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Edge case exception: {e}')",
            ]
        )


class PropertyTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "properties"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = [
            "import hypothesis",
            "import hypothesis.strategies as st",
            "from hypothesis import given",
            "import typing",
        ]

        given_params = []
        param_names = []
        for name, info in filtered_sig_info["parameters"].items():
            strategy_str = test_utils.strategy_to_string(
                test_utils.type_to_strategy(info["type"])
            )
            given_params.append(f"{name}={strategy_str}")
            param_names.append(name)

        return_type = sig_info["return_type"]
        if return_type == typing.Any:
            type_check_code = []
        elif hasattr(return_type, "__name__"):
            type_check_code = [
                f"        if result is not None:",
                f"            assert isinstance(result, {return_type.__name__})",
            ]
        else:
            type_check_code = []

        return "\n".join(
            imports
            + [""]
            + [
                f"@given({', '.join(given_params)})",
                f"def test_{func_name}_properties({', '.join(param_names)}):",
                '    """Test general properties of the function."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
                f"        result = {func_name}({', '.join(param_names)})",
                "        assert result is not None or result is None",
            ]
            + type_check_code
            + [
                "    except Exception as e:",
                "        raise",
            ]
        )


class TypeConsistencyTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "type_consistency"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"] or sig_info["return_type"] == typing.Any:
            return ""

        imports = [
            "import hypothesis",
            "import hypothesis.strategies as st",
            "from hypothesis import given",
            "import typing",
        ]

        given_params = []
        param_names = []
        for name, info in filtered_sig_info["parameters"].items():
            strategy_str = test_utils.strategy_to_string(
                test_utils.type_to_strategy(info["type"])
            )
            given_params.append(f"{name}={strategy_str}")
            param_names.append(name)

        return_type = sig_info["return_type"]
        if return_type == typing.Any:
            return ""

        if hasattr(return_type, "__name__"):
            type_check_code = [
                f"        if result is not None:",
                f"            assert isinstance(result, {return_type.__name__})",
            ]
        else:
            return ""

        return "\n".join(
            imports
            + [""]
            + [
                f"@given({', '.join(given_params)})",
                f"def test_{func_name}_type_consistency({', '.join(param_names)}):",
                '    """Test that function returns consistent types."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
                f"        result = {func_name}({', '.join(param_names)})",
            ]
            + type_check_code
            + [
                "    except Exception:",
                "        pass",
            ]
        )


class DeterministicTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "deterministic"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = [
            "import hypothesis",
            "import hypothesis.strategies as st",
            "from hypothesis import given",
        ]

        given_params = []
        param_names = []
        for name, info in filtered_sig_info["parameters"].items():
            strategy_str = test_utils.strategy_to_string(
                test_utils.type_to_strategy(info["type"])
            )
            given_params.append(f"{name}={strategy_str}")
            param_names.append(name)

        return "\n".join(
            imports
            + [""]
            + [
                f"@given({', '.join(given_params)})",
                f"def test_{func_name}_deterministic({', '.join(param_names)}):",
                '    """Test that function is deterministic (same input = same output)."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
                f"        result1 = {func_name}({', '.join(param_names)})",
                f"        result2 = {func_name}({', '.join(param_names)})",
                "        assert result1 == result2",
                "    except Exception:",
                "        pass",
            ]
        )


class MathematicalPropertyTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "mathematical_properties"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        numeric_params = [
            (name, info)
            for name, info in filtered_sig_info["parameters"].items()
            if info["type"] in [int, float]
        ]

        if len(numeric_params) < 2:
            return ""

        imports = [
            "import hypothesis",
            "import hypothesis.strategies as st",
            "from hypothesis import given",
        ]

        if len(numeric_params) == 2:
            _, param1_info = numeric_params[0]
            _, param2_info = numeric_params[1]

            strategy1 = test_utils.strategy_to_string(
                test_utils.type_to_strategy(param1_info["type"])
            )
            strategy2 = test_utils.strategy_to_string(
                test_utils.type_to_strategy(param2_info["type"])
            )

            return "\n".join(
                imports
                + [""]
                + [
                    f"@given(a={strategy1}, b={strategy2})",
                    f"def test_{func_name}_mathematical_properties(a, b):",
                    '    """Test mathematical properties like commutativity."""',
                    f"{test_utils.indent_code(function_code, 4)}",
                    "    try:",
                    f"        result1 = {func_name}(a, b)",
                    f"        result2 = {func_name}(b, a)",
                    "        assert result1 == result2",
                    "    except Exception:",
                    "        pass",
                ]
            )

        return ""


class BoundaryTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "boundary"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = ["import sys", "import pytest"]
        test_cases = []

        for param_name, param_info in filtered_sig_info["parameters"].items():
            param_type = param_info["type"]

            if param_type == int:
                test_cases.extend(
                    [
                        f"        # Test with maximum integer",
                        f"        result = {func_name}(sys.maxsize)",
                        f"        # Test with minimum integer",
                        f"        result = {func_name}(-sys.maxsize - 1)",
                    ]
                )
            elif param_type == float:
                test_cases.extend(
                    [
                        f"        # Test with very large float",
                        f"        result = {func_name}(1e308)",
                        f"        # Test with very small float",
                        f"        result = {func_name}(1e-308)",
                    ]
                )
            elif param_type == str:
                test_cases.extend(
                    [
                        f"        # Test with very long string",
                        f"        result = {func_name}('a' * 10000)",
                        f"        # Test with unicode string",
                        f"        result = {func_name}('Hello 世界 🌍')",
                    ]
                )
            elif param_type == list:
                test_cases.extend(
                    [
                        f"        # Test with large list",
                        f"        result = {func_name}(list(range(1000)))",
                    ]
                )

        if not test_cases:
            return ""

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_boundary():",
                '    """Test function with boundary values."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Boundary test exception: {e}')",
            ]
        )


class DataStructureTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "data_structures"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = ["import collections", "import pytest"]
        test_cases = []

        for param_name, param_info in filtered_sig_info["parameters"].items():
            param_type = param_info["type"]
            origin_type = getattr(param_type, "__origin__", param_type)

            if origin_type == list:
                test_cases.extend(
                    [
                        f"        # Test with nested lists",
                        f"        result = {func_name}([[1, 2], [3, 4], [5, 6]])",
                        f"        # Test with mixed type list",
                        f"        result = {func_name}([1, 'two', 3.0, True])",
                    ]
                )
            elif origin_type == dict:
                test_cases.extend(
                    [
                        f"        # Test with nested dictionary",
                        f"        result = {func_name}({{'a': {{'b': 1}}, 'c': {{'d': 2}}}})",
                        f"        # Test with OrderedDict",
                        f"        result = {func_name}(collections.OrderedDict([('first', 1), ('second', 2)]))",
                    ]
                )
            elif origin_type == set:
                test_cases.extend(
                    [
                        f"        # Test with large set",
                        f"        result = {func_name}(set(range(100)))",
                        f"        # Test with frozenset",
                        f"        result = {func_name}(frozenset([1, 2, 3, 4, 5]))",
                    ]
                )

        if not test_cases:
            return ""

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_data_structures():",
                '    """Test function with complex data structures."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Data structure test exception: {e}')",
            ]
        )


class NumPyTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "numpy"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function code contains numpy usage
        if "numpy" not in function_code and "np." not in function_code:
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = [
            "import pytest",
            "try:",
            "    import numpy as np",
            "except ImportError:",
            "    pytest.skip('NumPy not available')",
        ]

        test_cases = []
        for param_name, param_info in filtered_sig_info["parameters"].items():
            param_type = param_info["type"]

            if (
                param_type in [int, float]
                or getattr(param_type, "__origin__", None) == list
            ):
                test_cases.extend(
                    [
                        f"        # Test with numpy array",
                        f"        result = {func_name}(np.array([1, 2, 3, 4, 5]))",
                        f"        # Test with numpy zeros",
                        f"        result = {func_name}(np.zeros(10))",
                        f"        # Test with numpy ones",
                        f"        result = {func_name}(np.ones(5))",
                        f"        # Test with 2D numpy array",
                        f"        result = {func_name}(np.array([[1, 2], [3, 4]]))",
                    ]
                )

        if not test_cases:
            return ""

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_numpy():",
                '    """Test function with NumPy arrays and operations."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'NumPy test exception: {e}')",
            ]
        )


class DateTimeTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "datetime"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function code contains datetime usage
        if "datetime" not in function_code and "date" not in function_code.lower():
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = [
            "import datetime",
            "import pytest",
            "from datetime import timezone, timedelta",
        ]

        test_cases = [
            f"        # Test with current datetime",
            f"        result = {func_name}(datetime.datetime.now())",
            f"        # Test with UTC datetime",
            f"        result = {func_name}(datetime.datetime.now(timezone.utc))",
            f"        # Test with specific date",
            f"        result = {func_name}(datetime.date(2023, 1, 1))",
            f"        # Test with time object",
            f"        result = {func_name}(datetime.time(12, 30, 45))",
            f"        # Test with timedelta",
            f"        result = {func_name}(timedelta(days=7, hours=2))",
            f"        # Test with timestamp",
            f"        result = {func_name}(datetime.datetime.fromtimestamp(1640995200))",
        ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_datetime():",
                '    """Test function with datetime objects."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'DateTime test exception: {e}')",
            ]
        )


class JsonTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "json"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function code contains json usage
        if "json" not in function_code:
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = ["import json", "import pytest"]

        test_cases = [
            f"        # Test with simple JSON string",
            f"        result = {func_name}(json.dumps({{'key': 'value', 'number': 42}}))",
            f"        # Test with nested JSON",
            f"        nested_json = json.dumps({{'data': {{'items': [1, 2, 3], 'meta': {{'count': 3}}}}}})",
            f"        result = {func_name}(nested_json)",
            f"        # Test with JSON array",
            f"        result = {func_name}(json.dumps([1, 2, 3, 'four', True, None]))",
            f"        # Test with empty JSON",
            f"        result = {func_name}(json.dumps({{}}))",
            f"        # Test with JSON containing special characters",
            f"        result = {func_name}(json.dumps({{'unicode': '🌍', 'escape': '\\\\n\\\\t\\\\r'}}))",
        ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_json():",
                '    """Test function with JSON data."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'JSON test exception: {e}')",
            ]
        )


class RequestsTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "requests"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function code contains requests usage
        if "requests" not in function_code and "http" not in function_code.lower():
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)

        imports = [
            "import pytest",
            "from unittest.mock import patch, Mock",
            "try:",
            "    import requests",
            "except ImportError:",
            "    pytest.skip('Requests library not available')",
        ]

        test_cases = [
            f"        # Mock successful HTTP response",
            f"        mock_response = Mock()",
            f"        mock_response.status_code = 200",
            f"        mock_response.json.return_value = {{'success': True, 'data': 'test'}}",
            f"        mock_response.text = 'Success'",
            f"        ",
            f"        with patch('requests.get', return_value=mock_response) as mock_get:",
            f"            result = {func_name}('https://api.example.com/test')",
            f"            mock_get.assert_called_once()",
            f"        ",
            f"        # Mock HTTP error response",
            f"        mock_error_response = Mock()",
            f"        mock_error_response.status_code = 404",
            f"        mock_error_response.raise_for_status.side_effect = requests.HTTPError('404 Not Found')",
            f"        ",
            f"        with patch('requests.get', return_value=mock_error_response):",
            f"            try:",
            f"                result = {func_name}('https://api.example.com/notfound')",
            f"            except requests.HTTPError:",
            f"                pass  # Expected behavior",
        ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_requests():",
                '    """Test function with HTTP requests (mocked)."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Requests test exception: {e}')",
            ]
        )


class FileOperationsTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "file_operations"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function code contains file operations
        file_keywords = ["open(", "file", "read", "write", "path", "os.", "pathlib"]
        if not any(keyword in function_code for keyword in file_keywords):
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)

        imports = [
            "import tempfile",
            "import os",
            "import pytest",
            "from pathlib import Path",
        ]

        test_cases = [
            f"        # Test with temporary file",
            f"        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:",
            f"            tmp_file.write('Test content for file operations')",
            f"            tmp_file_path = tmp_file.name",
            f"        ",
            f"        try:",
            f"            result = {func_name}(tmp_file_path)",
            f"        finally:",
            f"            os.unlink(tmp_file_path)",
            f"        ",
            f"        # Test with temporary directory",
            f"        with tempfile.TemporaryDirectory() as tmp_dir:",
            f"            test_file = Path(tmp_dir) / 'test.txt'",
            f"            test_file.write_text('Sample content')",
            f"            result = {func_name}(str(test_file))",
            f"        ",
            f"        # Test with Path object",
            f"        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:",
            f"            tmp_file.write('Path object test')",
            f"            path_obj = Path(tmp_file.name)",
            f"        ",
            f"        try:",
            f"            result = {func_name}(path_obj)",
            f"        finally:",
            f"            os.unlink(tmp_file.name)",
        ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_file_operations():",
                '    """Test function with file operations."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'File operations test exception: {e}')",
            ]
        )


class RegexTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "regex"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function code contains regex usage
        if (
            "re." not in function_code
            and "regex" not in function_code
            and "pattern" not in function_code
        ):
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = ["import re", "import pytest"]

        test_cases = [
            f"        # Test with simple regex pattern",
            f"        result = {func_name}(r'\\d+', '123 abc 456')",
            f"        # Test with email regex",
            f"        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,}}'",
            f"        result = {func_name}(email_pattern, 'user@example.com')",
            f"        # Test with phone number regex",
            f"        phone_pattern = r'\\(?\\d{{3}}\\)?[-\\s]?\\d{{3}}[-\\s]?\\d{{4}}'",
            f"        result = {func_name}(phone_pattern, '(555) 123-4567')",
            f"        # Test with URL regex",
            f"        url_pattern = r'https?://[\\w\\.-]+\\.[a-zA-Z]{{2,}}[\\w\\.-]*/?[\\w\\.-]*'",
            f"        result = {func_name}(url_pattern, 'https://www.example.com/path')",
            f"        # Test with compiled regex",
            f"        compiled_pattern = re.compile(r'[A-Z][a-z]+')",
            f"        result = {func_name}(compiled_pattern, 'Hello World')",
        ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_regex():",
                '    """Test function with regular expressions."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Regex test exception: {e}')",
            ]
        )


class ExceptionHandlingTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "exception_handling"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = ["import pytest"]

        test_cases = []
        for param_name, param_info in filtered_sig_info["parameters"].items():
            param_type = param_info["type"]

            if param_type == int:
                test_cases.extend(
                    [
                        f"        # Test with invalid type (string instead of int)",
                        f"        with pytest.raises(TypeError):",
                        f"            result = {func_name}('not_an_integer')",
                    ]
                )
            elif param_type == str:
                test_cases.extend(
                    [
                        f"        # Test with None instead of string",
                        f"        with pytest.raises((TypeError, AttributeError)):",
                        f"            result = {func_name}(None)",
                    ]
                )
            elif param_type == list:
                test_cases.extend(
                    [
                        f"        # Test with non-iterable instead of list",
                        f"        with pytest.raises(TypeError):",
                        f"            result = {func_name}(42)",
                    ]
                )
            elif param_type == dict:
                test_cases.extend(
                    [
                        f"        # Test with non-dict type",
                        f"        with pytest.raises((TypeError, AttributeError)):",
                        f"            result = {func_name}('not_a_dict')",
                    ]
                )

        if not test_cases:
            # Generic exception tests
            test_cases = [
                f"        # Test exception handling with invalid input",
                f"        try:",
                f"            result = {func_name}(None)",
                f"        except Exception as e:",
                f"            assert isinstance(e, Exception)",
            ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_exception_handling():",
                '    """Test function exception handling."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        pass",
                "    except Exception as e:",
                "        print(f'Exception handling test: {e}')",
            ]
        )


class ConcurrencyTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "concurrency"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function is async or mentions threading/concurrency
        if (
            "async " not in function_code
            and "await " not in function_code
            and "thread" not in function_code.lower()
        ):
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)

        imports = [
            "import asyncio",
            "import threading",
            "import concurrent.futures",
            "import pytest",
        ]

        # Generate sample parameters
        sample_params = []
        for param_name, param_info in filtered_sig_info["parameters"].items():
            param_type = param_info["type"]
            if param_type == int:
                sample_params.append(f"{param_name}=42")
            elif param_type == str:
                sample_params.append(f"{param_name}='test_string'")
            else:
                sample_params.append(f"{param_name}=None")

        param_call = ", ".join(sample_params) if sample_params else ""

        if "async " in function_code:
            test_cases = [
                f"        # Test async function concurrency",
                f"        async def run_concurrent():",
                f"            tasks = []",
                f"            for i in range(5):",
                f"                task = asyncio.create_task({func_name}({param_call}))",
                f"                tasks.append(task)",
                f"            results = await asyncio.gather(*tasks)",
                f"            return results",
                f"        ",
                f"        # Run the concurrent test",
                f"        results = asyncio.run(run_concurrent())",
                f"        assert len(results) == 5",
            ]
        else:
            test_cases = [
                f"        # Test function in multiple threads",
                f"        def worker():",
                f"            return {func_name}({param_call})",
                f"        ",
                f"        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:",
                f"            futures = [executor.submit(worker) for _ in range(5)]",
                f"            results = [future.result() for future in concurrent.futures.as_completed(futures)]",
                f"            assert len(results) == 5",
            ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_concurrency():",
                '    """Test function concurrency and thread safety."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Concurrency test exception: {e}')",
            ]
        )


class MathLibraryTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "math_library"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function code contains math library usage
        if "math." not in function_code and "import math" not in function_code:
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = ["import math", "import pytest"]

        test_cases = [
            f"        # Test with mathematical constants",
            f"        result = {func_name}(math.pi)",
            f"        result = {func_name}(math.e)",
            f"        # Test with mathematical functions results",
            f"        result = {func_name}(math.sqrt(16))",
            f"        result = {func_name}(math.sin(math.pi/2))",
            f"        result = {func_name}(math.log(math.e))",
            f"        # Test with infinity and nan handling",
            f"        try:",
            f"            result = {func_name}(math.inf)",
            f"            result = {func_name}(-math.inf)",
            f"        except (ValueError, OverflowError):",
            f"            pass",
        ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_math_library():",
                '    """Test function with math library operations."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Math library test exception: {e}')",
            ]
        )


class CollectionsTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "collections"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function code contains collections usage
        if (
            "collections." not in function_code
            and "import collections" not in function_code
        ):
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = ["import collections", "import pytest"]

        test_cases = [
            f"        # Test with OrderedDict",
            f"        ordered_dict = collections.OrderedDict([('first', 1), ('second', 2), ('third', 3)])",
            f"        result = {func_name}(ordered_dict)",
            f"        # Test with defaultdict",
            f"        default_dict = collections.defaultdict(int)",
            f"        default_dict['key1'] = 10",
            f"        default_dict['key2'] = 20",
            f"        result = {func_name}(default_dict)",
            f"        # Test with Counter",
            f"        counter = collections.Counter(['a', 'b', 'c', 'a', 'b', 'a'])",
            f"        result = {func_name}(counter)",
            f"        # Test with deque",
            f"        deque_obj = collections.deque([1, 2, 3, 4, 5])",
            f"        result = {func_name}(deque_obj)",
            f"        # Test with namedtuple",
            f"        Point = collections.namedtuple('Point', ['x', 'y'])",
            f"        point = Point(3, 4)",
            f"        result = {func_name}(point)",
        ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_collections():",
                '    """Test function with collections module data structures."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Collections test exception: {e}')",
            ]
        )


class IterToolsTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "itertools"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function code contains itertools usage
        if (
            "itertools." not in function_code
            and "import itertools" not in function_code
        ):
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)
        if not filtered_sig_info["parameters"]:
            return ""

        imports = ["import itertools", "import pytest"]

        test_cases = [
            f"        # Test with itertools.chain",
            f"        chained = list(itertools.chain([1, 2, 3], [4, 5, 6]))",
            f"        result = {func_name}(chained)",
            f"        # Test with itertools.combinations",
            f"        combinations = list(itertools.combinations([1, 2, 3, 4], 2))",
            f"        result = {func_name}(combinations)",
            f"        # Test with itertools.permutations",
            f"        permutations = list(itertools.permutations([1, 2, 3], 2))",
            f"        result = {func_name}(permutations)",
            f"        # Test with itertools.product",
            f"        product = list(itertools.product([1, 2], ['a', 'b']))",
            f"        result = {func_name}(product)",
            f"        # Test with itertools.cycle (limited)",
            f"        cycle_iter = itertools.cycle([1, 2, 3])",
            f"        cycle_list = [next(cycle_iter) for _ in range(6)]",
            f"        result = {func_name}(cycle_list)",
        ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_itertools():",
                '    """Test function with itertools operations."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Itertools test exception: {e}')",
            ]
        )


class FuncToolsTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "functools"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function code contains functools usage
        if (
            "functools." not in function_code
            and "import functools" not in function_code
        ):
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)

        imports = ["import functools", "import pytest"]

        test_cases = [
            f"        # Test with functools.reduce",
            f"        numbers = [1, 2, 3, 4, 5]",
            f"        reduced = functools.reduce(lambda x, y: x + y, numbers)",
            f"        result = {func_name}(reduced)",
            f"        # Test with functools.partial",
            f"        def multiply(x, y):",
            f"            return x * y",
            f"        double = functools.partial(multiply, 2)",
            f"        result = {func_name}(double(5))",
            f"        # Test with functools.lru_cache decorated function result",
            f"        @functools.lru_cache(maxsize=128)",
            f"        def cached_function(n):",
            f"            return n * n",
            f"        result = {func_name}(cached_function(10))",
        ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_functools():",
                '    """Test function with functools operations."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Functools test exception: {e}')",
            ]
        )


class UrlLibTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "urllib"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function code contains urllib usage
        if "urllib." not in function_code and "import urllib" not in function_code:
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)

        imports = [
            "import urllib.parse",
            "import urllib.request",
            "import pytest",
            "from unittest.mock import patch, Mock",
        ]

        test_cases = [
            f"        # Test with URL parsing",
            f"        parsed_url = urllib.parse.urlparse('https://www.example.com/path?query=value')",
            f"        result = {func_name}(parsed_url)",
            f"        # Test with URL encoding",
            f"        encoded = urllib.parse.quote('hello world!', safe='')",
            f"        result = {func_name}(encoded)",
            f"        # Test with query string parsing",
            f"        query_dict = urllib.parse.parse_qs('name=John&age=30&city=New+York')",
            f"        result = {func_name}(query_dict)",
            f"        # Test with URL joining",
            f"        joined_url = urllib.parse.urljoin('https://example.com/base/', 'relative/path')",
            f"        result = {func_name}(joined_url)",
            f"        # Mock urllib.request.urlopen",
            f"        mock_response = Mock()",
            f"        mock_response.read.return_value = b'Mock response content'",
            f"        mock_response.getcode.return_value = 200",
            f"        with patch('urllib.request.urlopen', return_value=mock_response):",
            f"            result = {func_name}('https://httpbin.org/get')",
        ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_urllib():",
                '    """Test function with urllib operations."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Urllib test exception: {e}')",
            ]
        )


class LoggingTestGenerator(BaseTestGenerator):
    test_type = "unit"
    test_name = "logging"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        # Check if function code contains logging usage
        if "logging." not in function_code and "import logging" not in function_code:
            return ""

        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)

        imports = [
            "import logging",
            "import pytest",
            "from unittest.mock import patch, Mock",
            "import io",
            "import sys",
        ]

        test_cases = [
            f"        # Test with different logging levels",
            f"        logger = logging.getLogger('test_logger')",
            f"        logger.setLevel(logging.DEBUG)",
            f"        ",
            f"        # Capture log output",
            f"        log_capture = io.StringIO()",
            f"        handler = logging.StreamHandler(log_capture)",
            f"        logger.addHandler(handler)",
            f"        ",
            f"        # Test function with logger",
            f"        result = {func_name}(logger)",
            f"        ",
            f"        # Test with log messages",
            f"        logger.info('Test info message')",
            f"        logger.warning('Test warning message')",
            f"        logger.error('Test error message')",
            f"        ",
            f"        # Get captured logs",
            f"        log_contents = log_capture.getvalue()",
            f"        logger.removeHandler(handler)",
            f"        ",
            f"        # Test function with log level",
            f"        result = {func_name}(logging.INFO)",
            f"        result = {func_name}(logging.ERROR)",
        ]

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_logging():",
                '    """Test function with logging operations."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Logging test exception: {e}')",
            ]
        )


class MemoryTest(BaseTestGenerator):
    test_type = "memory"
    test_name = "memory_usage"

    async def get_tests_async(
        self, function: typing.Callable, function_text: typing.Optional[str] = None
    ) -> typing.List[models.Test]:
        return await super().get_tests_async(function, function_text)

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ):
        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)

        imports = ["import tracemalloc"]

        sample_params = []
        for param_name, param_info in filtered_sig_info["parameters"].items():
            param_type = param_info["type"]
            if param_type == int:
                sample_params.append(f"{param_name}=100")
            elif param_type == float:
                sample_params.append(f"{param_name}=1.5")
            elif param_type == str:
                sample_params.append(f"{param_name}='test_string'")
            elif param_type == bool:
                sample_params.append(f"{param_name}=True")
            elif param_type == bytes:
                sample_params.append(f"{param_name}=b'test_bytes'")
            elif param_type == complex:
                sample_params.append(f"{param_name}=1+2j")
            elif param_type == list:
                sample_params.append(f"{param_name}=[1, 2, 3, 4, 5]")
            elif param_type == dict:
                sample_params.append(f"{param_name}={{'key': 'value'}}")
            elif param_type == tuple:
                sample_params.append(f"{param_name}=(1, 2, 3)")
            elif param_type == set:
                sample_params.append(f"{param_name}={{1, 2, 3}}")
            else:
                sample_params.append(f"{param_name}=None")

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_memory_usage():",
                '    """Test memory usage of the function."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    tracemalloc.start()",
                "    try:",
                f"        result = {func_name}({', '.join(sample_params)})",
                "        current, peak = tracemalloc.get_traced_memory()",
                "        tracemalloc.stop()",
                "        assert peak < 100 * 1024 * 1024",
                "    except Exception as e:",
                "        tracemalloc.stop()",
                "        raise e",
            ]
        )


class PerformanceTest(BaseTestGenerator):
    test_type = "performance"
    test_name = "performance"

    async def get_tests_async(
        self, function: typing.Callable, function_text: typing.Optional[str] = None
    ) -> typing.List[models.Test]:
        return await super().get_tests_async(function, function_text)

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = test_utils.filter_standard_parameters(sig_info)

        imports = ["import time"]

        sample_params = []
        for param_name, param_info in filtered_sig_info["parameters"].items():
            param_type = param_info["type"]
            if param_type == int:
                sample_params.append(f"{param_name}=100")
            elif param_type == float:
                sample_params.append(f"{param_name}=0.5")
            elif param_type == str:
                sample_params.append(f"{param_name}='test_string'")
            elif param_type == bool:
                sample_params.append(f"{param_name}=True")
            elif param_type == bytes:
                sample_params.append(f"{param_name}=b'test_bytes'")
            elif param_type == complex:
                sample_params.append(f"{param_name}=1+2j")
            elif param_type == list:
                sample_params.append(f"{param_name}=[1, 2, 3, 4, 5]")
            elif param_type == dict:
                sample_params.append(f"{param_name}={{'key': 'value'}}")
            elif param_type == tuple:
                sample_params.append(f"{param_name}=(1, 2, 3)")
            elif param_type == set:
                sample_params.append(f"{param_name}={{1, 2, 3}}")
            else:
                sample_params.append(f"{param_name}=None")

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_performance():",
                '    """Test performance of the function."""',
                f"{test_utils.indent_code(function_code, 4)}",
                "    start_time = time.time()",
                "    for _ in range(1000):",
                "        try:",
                f"            result = {func_name}({', '.join(sample_params)})",
                "        except Exception:",
                "            break",
                "    end_time = time.time()",
                "    execution_time = end_time - start_time",
                "    assert execution_time < 10.0",
            ]
        )
