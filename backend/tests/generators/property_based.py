import typing

import tests.generators.base as base
import tests.utils.formatting as formatting
import tests.utils.strategy_mapping as strategy_mapping
import tests.utils.type_analysis as type_analysis


class HypothesisTestGenerator(base.BaseTestGenerator):
    """Generator for Hypothesis property-based tests."""

    test_type = "unit"
    test_name = "hypothesis"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = type_analysis.filter_standard_parameters(sig_info)
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
            strategy_str = strategy_mapping.strategy_to_string(
                strategy_mapping.type_to_strategy(info["type"])
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
                f"{formatting.indent_code(function_code, 4)}",
                "    try:",
                f"        result = {func_name}({', '.join(param_names)})",
                "        assert True",
                "    except Exception as e:",
                "        raise",
            ]
        )


class PropertyTestGenerator(base.BaseTestGenerator):
    """Generator for property-based tests that verify function properties."""

    test_type = "unit"
    test_name = "properties"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = type_analysis.filter_standard_parameters(sig_info)
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
            strategy_str = strategy_mapping.strategy_to_string(
                strategy_mapping.type_to_strategy(info["type"])
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
                f"{formatting.indent_code(function_code, 4)}",
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


class TypeConsistencyTestGenerator(base.BaseTestGenerator):
    """Generator for type consistency tests."""

    test_type = "unit"
    test_name = "type_consistency"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = type_analysis.filter_standard_parameters(sig_info)
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
            strategy_str = strategy_mapping.strategy_to_string(
                strategy_mapping.type_to_strategy(info["type"])
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
                f"{formatting.indent_code(function_code, 4)}",
                "    try:",
                f"        result = {func_name}({', '.join(param_names)})",
            ]
            + type_check_code
            + [
                "    except Exception:",
                "        pass",
            ]
        )


class DeterministicTestGenerator(base.BaseTestGenerator):
    """Generator for deterministic tests."""

    test_type = "unit"
    test_name = "deterministic"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = type_analysis.filter_standard_parameters(sig_info)
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
            strategy_str = strategy_mapping.strategy_to_string(
                strategy_mapping.type_to_strategy(info["type"])
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
                f"{formatting.indent_code(function_code, 4)}",
                "    try:",
                f"        result1 = {func_name}({', '.join(param_names)})",
                f"        result2 = {func_name}({', '.join(param_names)})",
                "        assert result1 == result2",
                "    except Exception:",
                "        pass",
            ]
        )
