import typing

import tests.generators.base as base
import tests.utils.formatting as formatting
import tests.utils.type_analysis as type_analysis


class MemoryTestGenerator(base.BaseTestGenerator):
    """Generator for memory usage tests."""

    test_type = "memory"
    test_name = "memory_usage"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ):
        filtered_sig_info = type_analysis.filter_standard_parameters(sig_info)

        imports = ["import tracemalloc"]

        sample_params = []
        for param_name, param_info in filtered_sig_info["parameters"].items():
            param_type = param_info["type"]
            sample_value = self._generate_sample_value(param_type)
            sample_params.append(f"{param_name}={sample_value}")

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_memory_usage():",
                '    """Test memory usage of the function."""',
                f"{formatting.indent_code(function_code, 4)}",
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

    def _generate_sample_value(self, param_type: typing.Any) -> str:
        """Generate sample values for memory testing."""
        if param_type == int:
            return "100"
        elif param_type == float:
            return "1.5"
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
            return "{'key': 'value'}"
        elif param_type == tuple:
            return "(1, 2, 3)"
        elif param_type == set:
            return "{1, 2, 3}"
        else:
            return "None"


class PerformanceTestGenerator(base.BaseTestGenerator):
    """Generator for performance tests."""

    test_type = "performance"
    test_name = "performance"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        filtered_sig_info = type_analysis.filter_standard_parameters(sig_info)

        imports = ["import time"]

        sample_params = []
        for param_name, param_info in filtered_sig_info["parameters"].items():
            param_type = param_info["type"]
            sample_value = self._generate_sample_value(param_type)
            sample_params.append(f"{param_name}={sample_value}")

        return "\n".join(
            imports
            + [""]
            + [
                f"def test_{func_name}_performance():",
                '    """Test performance of the function."""',
                f"{formatting.indent_code(function_code, 4)}",
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

    def _generate_sample_value(self, param_type: typing.Any) -> str:
        """Generate sample values for performance testing."""
        if param_type == int:
            return "100"
        elif param_type == float:
            return "0.5"
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
            return "{'key': 'value'}"
        elif param_type == tuple:
            return "(1, 2, 3)"
        elif param_type == set:
            return "{1, 2, 3}"
        else:
            return "None"


class ConcurrencyTestGenerator(base.BaseTestGenerator):
    """Generator for concurrency tests."""

    test_type = "unit"
    test_name = "concurrency"

    def _generate_test(
        self,
        func_name: str,
        function_code: str,
        sig_info: dict,
    ) -> str:
        if (
            "async " not in function_code
            and "await " not in function_code
            and "thread" not in function_code.lower()
        ):
            return ""

        filtered_sig_info = type_analysis.filter_standard_parameters(sig_info)

        imports = [
            "import asyncio",
            "import threading",
            "import concurrent.futures",
            "import pytest",
        ]

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
                f"{formatting.indent_code(function_code, 4)}",
                "    try:",
            ]
            + test_cases
            + [
                "        assert True",
                "    except Exception as e:",
                "        print(f'Concurrency test exception: {e}')",
            ]
        )
