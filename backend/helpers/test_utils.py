import inspect
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
}


def type_to_strategy(type_hint: typing.Any) -> hypothesis.strategies.SearchStrategy:
    if type_hint in SIMPLE_TYPE_STRATEGIES:
        return SIMPLE_TYPE_STRATEGIES[type_hint]

    if hasattr(type_hint, "__origin__"):
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

    return hypothesis.strategies.text()


def strategy_to_string(strategy: hypothesis.strategies.SearchStrategy) -> str:
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
    return "st.text()"


def analyze_function_signature(
    func: typing.Callable, remove_none: bool = False
) -> dict:
    sig = inspect.signature(func)
    type_hints = typing.get_type_hints(func)

    params_info = {}
    for param_name, param in sig.parameters.items():
        param_type = type_hints.get(param_name)
        if remove_none and param_type is None:
            continue

        params_info[param_name] = {
            "name": param_name,
            "type": param_type,
            "default": (
                param.default if param.default != inspect.Parameter.empty else None
            ),
            "has_default": param.default != inspect.Parameter.empty,
        }

    return {
        "parameters": params_info,
        "return_type": type_hints.get("return", typing.Any),
        "signature": sig,
    }


def is_standard_python_type(type_hint: typing.Any) -> bool:
    if type_hint is None:
        return False
    if type_hint in SIMPLE_TYPE_STRATEGIES:
        return True

    if hasattr(type_hint, "__origin__"):
        origin = type_hint.__origin__
        args = type_hint.__args__

        if origin is typing.Union:
            return all(is_standard_python_type(arg) for arg in args)

        if origin in {list, dict, tuple, set, frozenset}:
            return not args or all(is_standard_python_type(arg) for arg in args)

    return False


def filter_standard_parameters(sig_info: dict) -> dict:
    filtered_params = {
        name: info
        for name, info in sig_info["parameters"].items()
        if is_standard_python_type(info["type"])
    }
    return {**sig_info, "parameters": filtered_params}


def indent_code(code: str, spaces: int) -> str:
    indent = " " * spaces
    return "\n".join(
        indent + line if line.strip() else line for line in code.split("\n")
    )
