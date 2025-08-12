import asyncio
import typing

import models.websocket as models
import tests.generators.base as base
import tests.generators.edge_cases as edge_cases
import tests.generators.library_specific as library_specific
import tests.generators.performance as performance
import tests.generators.property_based as property_based


class UnitTestGenerator(base.BaseTestGenerator):
    """Main unit test generator that coordinates all individual generators."""

    test_type = "unit"
    test_name = "unit"

    def __init__(self):
        self.generators = [
            property_based.HypothesisTestGenerator(),
            property_based.PropertyTestGenerator(),
            property_based.TypeConsistencyTestGenerator(),
            property_based.DeterministicTestGenerator(),
            edge_cases.EdgeCaseTestGenerator(),
            edge_cases.BoundaryTestGenerator(),
            edge_cases.ExceptionHandlingTestGenerator(),
            library_specific.NumPyTestGenerator(),
            library_specific.RequestsTestGenerator(),
            library_specific.DateTimeTestGenerator(),
            library_specific.JsonTestGenerator(),
            performance.ConcurrencyTestGenerator(),
        ]

    async def get_tests_async(
        self, function: typing.Callable, function_text: typing.Optional[str] = None
    ) -> typing.List[models.Test]:
        """Generate tests using all available unit test generators."""
        tasks = [
            gen.get_tests_async(function, function_text) for gen in self.generators
        ]
        results = await asyncio.gather(*tasks)

        all_tests = []
        for test_list in results:
            all_tests.extend(test_list)

        return all_tests

    def _generate_test(self, func_name: str, function_code: str, sig_info: dict) -> str:
        """Not used in this generator as it coordinates other generators."""
        return ""
