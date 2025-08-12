import asyncio
import typing

import models.websocket as models
import tests.utils.formatting as formatting
import tests.utils.type_analysis as type_analysis
import utils.function_utils as function_utils


class BaseTestGenerator:
    """Base class for all test generators."""

    test_type: typing.Literal["unit", "memory", "performance"] = "unit"
    test_name: str = "base"

    async def get_tests_async(
        self, function: typing.Callable, function_text: typing.Optional[str] = None
    ) -> typing.List[models.Test]:
        """Generate tests asynchronously."""
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

                sig_info = type_analysis.analyze_function_signature(function)
                test_code = self._generate_test(func_name, function_string, sig_info)

                if test_code:
                    test_name = f"test_{func_name}_{self.test_name}"
                    result.append(
                        models.Test(
                            type=self.test_type,
                            name=test_name,
                            title=formatting.create_test_title(test_name),
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
        """Generate test code. Must be implemented by subclasses."""
        raise NotImplementedError
        raise NotImplementedError
