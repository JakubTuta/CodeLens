import ast
import inspect
import typing
from typing import Optional, Tuple


def validate_single_function_with_errors(
    function_text: str,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a single function and return validation result with error message.

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        # Check if code is empty
        if not function_text or not function_text.strip():
            return False, "Code cannot be empty"

        # Check line count limit (150 lines)
        lines = function_text.strip().split("\n")
        if len(lines) > 150:
            return False, "Code exceeds maximum limit of 150 lines"

        # Parse the code into an AST
        try:
            tree = ast.parse(function_text.strip())
        except IndentationError:
            return (
                False,
                "Indentation error detected. Please check your code indentation",
            )
        except SyntaxError as e:
            # Handle common syntax errors with user-friendly messages
            if "invalid syntax" in str(e).lower():
                return (
                    False,
                    "Syntax error detected. Please check your code for typos or missing punctuation",
                )
            elif "unexpected indent" in str(e).lower():
                return (
                    False,
                    "Indentation error detected. Please check your code indentation",
                )
            elif "unindent does not match" in str(e).lower():
                return False, "Indentation error: inconsistent indentation levels"
            else:
                return (
                    False,
                    "Syntax error in your code. Please review and fix any syntax issues",
                )

        # Count different types of top-level nodes
        function_count = 0
        has_class = False
        invalid_constructs = []

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                function_count += 1
            elif isinstance(node, ast.ClassDef):
                has_class = True
            # Allow imports, global variables, constants, etc.
            elif isinstance(
                node,
                (
                    ast.Import,
                    ast.ImportFrom,
                    ast.Assign,
                    ast.AnnAssign,
                    ast.AugAssign,
                    ast.Expr,
                    ast.Pass,
                ),
            ):
                continue
            # Check for disallowed top-level constructs
            else:
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    invalid_constructs.append("control flow statements")
                elif isinstance(node, (ast.With, ast.Try)):
                    invalid_constructs.append("context managers or exception handling")
                else:
                    invalid_constructs.append("unsupported constructs")

        # Validation checks with specific error messages
        if function_count == 0:
            return (
                False,
                "No function found. Please include exactly one function definition",
            )

        if function_count > 1:
            return (
                False,
                f"Found {function_count} functions. Please include only one function",
            )

        if has_class:
            return (
                False,
                "Classes are not allowed. The function must be globally accessible",
            )

        if invalid_constructs:
            unique_constructs = list(set(invalid_constructs))
            return False, f"Top-level {', '.join(unique_constructs)} are not allowed"

        # Check for compilation issues
        try:
            compile(function_text, "<string>", "exec")
        except SyntaxError:
            return (
                False,
                "Syntax error detected. Please check your code for typos or missing punctuation",
            )
        except Exception as e:
            return False, "Code compilation failed. Please check your code syntax"

        # Additional validation: check for classes anywhere in the code
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                return False, "Classes are not allowed anywhere in the code"

        # Validate that the function is properly defined and accessible
        try:
            namespace = {}
            exec(function_text, namespace)

            # Count actual functions in the namespace (excluding built-ins)
            defined_functions = [
                obj
                for obj in namespace.values()
                if callable(obj) and hasattr(obj, "__code__")
            ]

            if len(defined_functions) == 0:
                return False, "No executable function found in the code"
            elif len(defined_functions) > 1:
                return (
                    False,
                    "Multiple functions detected. Please include only one function",
                )

        except Exception as e:
            return (
                False,
                "Code execution failed. Please check your function implementation",
            )

        return True, None

    except Exception as e:
        return False, "Unexpected error during validation. Please check your code"


def validate_single_function(function_text: str) -> bool:
    """
    Legacy validation function for backward compatibility.
    """
    is_valid, _ = validate_single_function_with_errors(function_text)
    return is_valid


def text_to_function(function_text: str) -> typing.Callable[..., typing.Any]:
    is_valid, error_message = validate_single_function_with_errors(function_text)
    if not is_valid:
        raise ValueError(error_message or "Invalid function text")

    namespace = {}
    exec(function_text, namespace)

    # Find the single function that should be defined
    defined_functions = [
        obj for obj in namespace.values() if callable(obj) and hasattr(obj, "__code__")
    ]

    if len(defined_functions) != 1:
        raise ValueError(
            "Expected exactly one function, found " + str(len(defined_functions))
        )

    return defined_functions[0]


def function_to_text(func: typing.Callable) -> str:
    try:
        source = inspect.getsource(func)
        lines = source.split("\n")

        if lines and lines[0].strip():
            non_empty_lines = [line for line in lines if line.strip()]

            if non_empty_lines:
                min_indent = min(
                    len(line) - len(line.lstrip()) for line in non_empty_lines
                )
                source = "\n".join(
                    line[min_indent:] if len(line) > min_indent else line
                    for line in lines
                )

        is_valid, error_message = validate_single_function_with_errors(source)
        if not is_valid:
            raise ValueError(f"Function source is not valid: {error_message}")

        return source.strip()

    except (OSError, TypeError) as e:
        raise ValueError(f"Cannot get source code: {e}")


def get_function_name(func: typing.Callable) -> str:
    if not callable(func):
        raise ValueError("Provided object is not callable")

    if hasattr(func, "__name__"):
        return func.__name__
    else:
        raise ValueError("Function does not have a name attribute")
