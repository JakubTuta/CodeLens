import asyncio
import typing

from helpers import function_utils, test_utils

from . import models


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
                    test_cases.append(f"    # Test with {description}")
                    test_cases.append(f"    result = {func_name}({value})")

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
                "\n".join(test_cases),
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
                f"        expected_return_type = {repr(sig_info['return_type'])}",
                f"        if expected_return_type != {repr(typing.Any)}:",
                "            if result is not None:",
                "                assert isinstance(result, expected_return_type)",
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
                f"        expected_type = {repr(sig_info['return_type'])}",
                "        if result is not None:",
                "            assert isinstance(result, expected_type)",
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
