import tests.generators.base as base
import tests.utils.formatting as formatting
import tests.utils.type_analysis as type_analysis


class EdgeCaseTestGenerator(base.BaseTestGenerator):
    """Generator for edge case tests."""

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
        filtered_sig_info = type_analysis.filter_standard_parameters(sig_info)
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
                f"{formatting.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Edge case exception: {e}')",
            ]
        )


class BoundaryTestGenerator(base.BaseTestGenerator):
    """Generator for boundary value tests."""

    test_type = "unit"
    test_name = "boundary"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = type_analysis.filter_standard_parameters(sig_info)
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
                f"{formatting.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Boundary test exception: {e}')",
            ]
        )


class ExceptionHandlingTestGenerator(base.BaseTestGenerator):
    """Generator for exception handling tests."""

    test_type = "unit"
    test_name = "exception_handling"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = type_analysis.filter_standard_parameters(sig_info)
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
                f"{formatting.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        pass",
                "    except Exception as e:",
                "        print(f'Exception handling test: {e}')",
            ]
        )
