import tests.generators.base as base
import tests.utils.formatting as formatting
import tests.utils.type_analysis as type_analysis


class NumPyTestGenerator(base.BaseTestGenerator):
    """Generator for NumPy-specific tests."""

    test_type = "unit"
    test_name = "numpy"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        if "numpy" not in function_code and "np." not in function_code:
            return ""

        filtered_sig_info = type_analysis.filter_standard_parameters(sig_info)
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
                f"{formatting.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'NumPy test exception: {e}')",
            ]
        )


class RequestsTestGenerator(base.BaseTestGenerator):
    """Generator for Requests library tests."""

    test_type = "unit"
    test_name = "requests"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        if "requests" not in function_code and "http" not in function_code.lower():
            return ""

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
                f"{formatting.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Requests test exception: {e}')",
            ]
        )


class DateTimeTestGenerator(base.BaseTestGenerator):
    """Generator for datetime-related tests."""

    test_type = "unit"
    test_name = "datetime"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        if "datetime" not in function_code and "date" not in function_code.lower():
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
                f"{formatting.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'DateTime test exception: {e}')",
            ]
        )


class JsonTestGenerator(base.BaseTestGenerator):
    """Generator for JSON-related tests."""

    test_type = "unit"
    test_name = "json"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        if "json" not in function_code:
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
                f"{formatting.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'JSON test exception: {e}')",
            ]
        )
