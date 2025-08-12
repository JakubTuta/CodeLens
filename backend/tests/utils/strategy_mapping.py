import datetime
import pathlib
import re
import typing

import hypothesis
import hypothesis.strategies

SIMPLE_TYPE_STRATEGIES = {
    int: hypothesis.strategies.integers(),
    float: hypothesis.strategies.floats(allow_nan=False, allow_infinity=False),
    str: hypothesis.strategies.text(),
    bool: hypothesis.strategies.booleans(),
    bytes: hypothesis.strategies.binary(),
    complex: hypothesis.strategies.complex_numbers(),
    type(None): hypothesis.strategies.none(),
    datetime.datetime: hypothesis.strategies.datetimes(),
    datetime.date: hypothesis.strategies.dates(),
    datetime.time: hypothesis.strategies.times(),
    datetime.timedelta: hypothesis.strategies.timedeltas(),
    pathlib.Path: hypothesis.strategies.text().map(
        lambda x: pathlib.Path(x.replace("/", "_").replace("\\", "_"))
    ),
}


LIBRARY_TYPE_STRATEGIES = {
    "re.Pattern": hypothesis.strategies.text().map(lambda x: re.compile(r"\w*")),
    "numpy.ndarray": hypothesis.strategies.lists(
        hypothesis.strategies.floats(allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=10,
    ),
    "pandas.DataFrame": hypothesis.strategies.dictionaries(
        hypothesis.strategies.text(min_size=1, max_size=10),
        hypothesis.strategies.lists(
            hypothesis.strategies.integers(), min_size=1, max_size=5
        ),
        min_size=1,
        max_size=3,
    ),
    "pandas.Series": hypothesis.strategies.lists(
        hypothesis.strategies.integers(), min_size=1, max_size=10
    ),
    "requests.Response": hypothesis.strategies.just(None),
    "tensorflow.Tensor": hypothesis.strategies.lists(
        hypothesis.strategies.floats(allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=10,
    ),
    "torch.Tensor": hypothesis.strategies.lists(
        hypothesis.strategies.floats(allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=10,
    ),
    "numpy.float32": hypothesis.strategies.floats(
        allow_nan=False, allow_infinity=False
    ),
    "numpy.float64": hypothesis.strategies.floats(
        allow_nan=False, allow_infinity=False
    ),
    "numpy.int32": hypothesis.strategies.integers(),
    "numpy.int64": hypothesis.strategies.integers(),
    "matplotlib.pyplot.Figure": hypothesis.strategies.just(None),
    "matplotlib.figure.Figure": hypothesis.strategies.just(None),
}


def type_to_strategy(type_hint: typing.Any) -> hypothesis.strategies.SearchStrategy:
    """Convert a type hint to a Hypothesis strategy."""
    if type_hint in SIMPLE_TYPE_STRATEGIES:
        return SIMPLE_TYPE_STRATEGIES[type_hint]

    if isinstance(type_hint, str) and type_hint in LIBRARY_TYPE_STRATEGIES:
        return LIBRARY_TYPE_STRATEGIES[type_hint]

    if hasattr(type_hint, "__origin__") and not isinstance(type_hint, str):
        origin = type_hint.__origin__
        args = type_hint.__args__

        if origin is typing.Union:
            if len(args) == 2 and type(None) in args:
                non_none_type = args[0] if args[1] is type(None) else args[1]
                return hypothesis.strategies.one_of(
                    hypothesis.strategies.none(), type_to_strategy(non_none_type)
                )
            return hypothesis.strategies.one_of([type_to_strategy(arg) for arg in args])

        if origin is list:
            element_strategy = (
                type_to_strategy(args[0]) if args else hypothesis.strategies.integers()
            )
            return hypothesis.strategies.lists(
                element_strategy, min_size=0, max_size=10
            )

        if origin is dict:
            key_strategy = (
                type_to_strategy(args[0])
                if len(args) > 0
                else hypothesis.strategies.text()
            )
            value_strategy = (
                type_to_strategy(args[1])
                if len(args) > 1
                else hypothesis.strategies.integers()
            )
            return hypothesis.strategies.dictionaries(
                key_strategy, value_strategy, min_size=0, max_size=5
            )

        if origin is tuple:
            if args:
                return hypothesis.strategies.tuples(
                    *(type_to_strategy(arg) for arg in args)
                )
            return hypothesis.strategies.tuples(
                hypothesis.strategies.integers(), hypothesis.strategies.text()
            )

        if origin in {set, frozenset}:
            element_strategy = (
                type_to_strategy(args[0]) if args else hypothesis.strategies.integers()
            )
            return hypothesis.strategies.sets(element_strategy, min_size=0, max_size=5)

    if type_hint == datetime.datetime:
        return hypothesis.strategies.datetimes()
    elif type_hint == datetime.date:
        return hypothesis.strategies.dates()
    elif type_hint == datetime.time:
        return hypothesis.strategies.times()
    elif type_hint == datetime.timedelta:
        return hypothesis.strategies.timedeltas()

    if type_hint == pathlib.Path:
        return hypothesis.strategies.text().map(
            lambda x: pathlib.Path(x.replace("/", "_").replace("\\", "_"))
        )

    return hypothesis.strategies.text()


def strategy_to_string(strategy: hypothesis.strategies.SearchStrategy) -> str:
    """Convert a Hypothesis strategy to its string representation."""
    strategy_repr = repr(strategy)
    if "integers" in strategy_repr:
        return "st.integers()"
    if "floats" in strategy_repr:
        return "st.floats(allow_nan=False, allow_infinity=False)"
    if "text" in strategy_repr:
        return "st.text()"
    if "booleans" in strategy_repr:
        return "st.booleans()"
    if "binary" in strategy_repr:
        return "st.binary()"
    if "complex" in strategy_repr:
        return "st.complex_numbers()"
    if "lists" in strategy_repr:
        return "st.lists(st.integers(), min_size=0, max_size=10)"
    if "dictionaries" in strategy_repr:
        return "st.dictionaries(st.text(), st.integers(), min_size=0, max_size=5)"
    if "tuples" in strategy_repr:
        return "st.tuples(st.integers(), st.text())"
    if "sets" in strategy_repr:
        return "st.sets(st.integers(), min_size=0, max_size=5)"
    if "one_of" in strategy_repr:
        return "st.one_of(st.none(), st.text())"
    if "none" in strategy_repr:
        return "st.none()"
    if "datetimes" in strategy_repr:
        return "st.datetimes()"
    if "dates" in strategy_repr:
        return "st.dates()"
    if "times" in strategy_repr:
        return "st.times()"
    if "timedeltas" in strategy_repr:
        return "st.timedeltas()"
    return "st.text()"
