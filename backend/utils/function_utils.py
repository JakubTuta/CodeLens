import ast
import importlib
import inspect
import sys
import typing
from typing import Optional, Tuple


def create_safe_execution_namespace() -> dict:
    """
    Create a safe execution namespace with commonly used modules.
    This allows user code to import and use third-party libraries without causing errors.
    """
    namespace = {"__builtins__": __builtins__}

    standard_modules = [
        "datetime",
        "json",
        "os",
        "sys",
        "math",
        "random",
        "time",
        "collections",
        "itertools",
        "functools",
        "re",
        "pathlib",
        "tempfile",
        "threading",
        "asyncio",
        "concurrent",
        "urllib",
        "logging",
        "tracemalloc",
        "csv",
        "xml",
        "sqlite3",
        "unittest",
    ]

    for module_name in standard_modules:
        try:
            namespace[module_name] = importlib.import_module(module_name)
        except ImportError:
            pass

    third_party_modules = {
        "numpy": ["np"],
        "pandas": ["pd"],
        "requests": [],
        "hypothesis": [],
        "pytest": [],
        "matplotlib": ["plt"],
        "scipy": [],
        "sklearn": [],
        "tensorflow": ["tf"],
        "torch": [],
    }

    for module_name, aliases in third_party_modules.items():
        try:
            module = importlib.import_module(module_name)
            namespace[module_name] = module

            # Add common type references for type hints
            if module_name == "numpy" and hasattr(module, "ndarray"):
                namespace["ndarray"] = module.ndarray
            elif module_name == "pandas":
                if hasattr(module, "DataFrame"):
                    namespace["DataFrame"] = module.DataFrame
                if hasattr(module, "Series"):
                    namespace["Series"] = module.Series
            elif module_name == "requests" and hasattr(module, "Response"):
                namespace["Response"] = module.Response
            elif module_name == "tensorflow":
                if hasattr(module, "Tensor"):
                    namespace["Tensor"] = module.Tensor
            elif module_name == "torch":
                if hasattr(module, "Tensor"):
                    namespace["Tensor"] = module.Tensor

            for alias in aliases:
                if alias == "np":
                    namespace[alias] = module
                elif alias == "pd":
                    namespace[alias] = module
                elif alias == "plt":
                    namespace[alias] = getattr(module, "pyplot", module)
                elif alias == "tf":
                    namespace[alias] = module
                else:
                    namespace[alias] = module
        except ImportError:
            mock_module = create_mock_module(module_name)
            namespace[module_name] = mock_module

            # Add mock type references for type hints
            if module_name == "numpy":
                namespace["ndarray"] = mock_module.ndarray
            elif module_name == "pandas":
                namespace["DataFrame"] = mock_module.DataFrame
                namespace["Series"] = mock_module.Series
            elif module_name == "requests":
                namespace["Response"] = mock_module.Response
            elif module_name == "tensorflow":
                namespace["Tensor"] = mock_module.Tensor
            elif module_name == "torch":
                namespace["Tensor"] = mock_module.Tensor

            for alias in aliases:
                namespace[alias] = mock_module

    return namespace


def create_mock_module(module_name: str):
    """
    Create a mock module that can be imported without causing errors.
    This prevents ImportError when user code tries to import unavailable modules.
    """

    class MockModule:
        def __init__(self, name):
            self.__name__ = name

            if name == "pandas":
                self.DataFrame = MockDataFrameClass("DataFrame")
                self.Series = MockSeriesClass("Series")
                self.read_csv = MockCallable("read_csv")
                self.read_excel = MockCallable("read_excel")
                self.read_json = MockCallable("read_json")
                self.to_datetime = MockCallable("to_datetime")
                self.concat = MockCallable("concat")
                self.merge = MockCallable("merge")
            elif name == "numpy":
                self.array = MockCallable("array")
                self.ndarray = MockNdarrayClass("ndarray")
                self.mean = MockCallable("mean")
                self.sum = MockCallable("sum")
                self.zeros = MockCallable("zeros")
                self.ones = MockCallable("ones")
                self.arange = MockCallable("arange")
                self.linspace = MockCallable("linspace")
                self.reshape = MockCallable("reshape")
                self.dtype = MockCallable("dtype")
                self.float32 = MockCallable("float32")
                self.float64 = MockCallable("float64")
                self.int32 = MockCallable("int32")
                self.int64 = MockCallable("int64")
            elif name == "requests":
                self.get = MockCallable("get")
                self.post = MockCallable("post")
                self.put = MockCallable("put")
                self.delete = MockCallable("delete")
                self.Response = MockResponseClass("Response")
            elif name == "matplotlib":
                self.pyplot = MockPyplotModule("pyplot")
            elif name == "scipy":
                self.sparse = MockModule("sparse")
                self.linalg = MockModule("linalg")
                self.stats = MockModule("stats")
            elif name == "sklearn":
                self.linear_model = MockModule("linear_model")
                self.ensemble = MockModule("ensemble")
                self.metrics = MockModule("metrics")
                self.model_selection = MockModule("model_selection")
            elif name == "tensorflow":
                self.Tensor = MockTensorClass("Tensor")
                self.Variable = MockCallable("Variable")
                self.constant = MockCallable("constant")
            elif name == "torch":
                self.Tensor = MockTensorClass("Tensor")
                self.tensor = MockCallable("tensor")
                self.zeros = MockCallable("zeros")
                self.ones = MockCallable("ones")

        def __getattr__(self, name):
            return MockCallable(f"{self.__name__}.{name}")

    class MockCallable:
        def __init__(self, name):
            self.__name__ = name

        def __call__(self, *args, **kwargs):
            return MockObject()

        def __getattr__(self, name):
            return MockCallable(f"{self.__name__}.{name}")

    class MockObject:
        def __getattr__(self, name):
            return MockCallable(name)

        def __call__(self, *args, **kwargs):
            return MockObject()

        def __len__(self):
            return 0

        def __iter__(self):
            return iter([])

        def __getitem__(self, key):
            return MockObject()

        def __setitem__(self, key, value):
            pass

        def __str__(self):
            return "MockObject"

        def __repr__(self):
            return "MockObject"

    class MockDataFrameClass:
        """Mock pandas DataFrame class"""

        def __init__(self, name):
            self.__name__ = name

        def __call__(self, *args, **kwargs):
            return MockDataFrame()

        def __getattr__(self, name):
            return MockCallable(f"DataFrame.{name}")

    class MockDataFrame:
        """Mock pandas DataFrame instance"""

        def __init__(self):
            self.shape = (0, 0)
            self.columns = []
            self.index = []

        def __getattr__(self, name):
            return MockCallable(f"DataFrame.{name}")

        def __getitem__(self, key):
            return MockSeries()

        def __setitem__(self, key, value):
            pass

        def __len__(self):
            return 0

    class MockSeriesClass:
        """Mock pandas Series class"""

        def __init__(self, name):
            self.__name__ = name

        def __call__(self, *args, **kwargs):
            return MockSeries()

    class MockSeries:
        """Mock pandas Series instance"""

        def __init__(self):
            self.shape = (0,)
            self.dtype = object

        def __getattr__(self, name):
            return MockCallable(f"Series.{name}")

        def __len__(self):
            return 0

    class MockNdarrayClass:
        """Mock numpy ndarray class"""

        def __init__(self, name):
            self.__name__ = name

        def __call__(self, *args, **kwargs):
            return MockNdarray()

    class MockNdarray:
        """Mock numpy ndarray instance"""

        def __init__(self):
            self.shape = (0,)
            self.dtype = object
            self.ndim = 1
            self.size = 0

        def __getattr__(self, name):
            return MockCallable(f"ndarray.{name}")

        def __getitem__(self, key):
            return MockObject()

        def __setitem__(self, key, value):
            pass

        def __len__(self):
            return 0

    class MockResponseClass:
        """Mock requests Response class"""

        def __init__(self, name):
            self.__name__ = name

        def __call__(self, *args, **kwargs):
            return MockResponse()

    class MockResponse:
        """Mock requests Response instance"""

        def __init__(self):
            self.status_code = 200
            self.text = ""
            self.content = b""

        def json(self):
            return {}

        def __getattr__(self, name):
            return MockCallable(f"Response.{name}")

    class MockPyplotModule:
        """Mock matplotlib pyplot module"""

        def __init__(self, name):
            self.__name__ = name
            self.plot = MockCallable("plot")
            self.show = MockCallable("show")
            self.figure = MockCallable("figure")
            self.subplot = MockCallable("subplot")

        def __getattr__(self, name):
            return MockCallable(f"pyplot.{name}")

    class MockTensorClass:
        """Mock TensorFlow/PyTorch Tensor class"""

        def __init__(self, name):
            self.__name__ = name

        def __call__(self, *args, **kwargs):
            return MockTensor()

    class MockTensor:
        """Mock Tensor instance"""

        def __init__(self):
            self.shape = []
            self.dtype = object

        def __getattr__(self, name):
            return MockCallable(f"Tensor.{name}")

    return MockModule(module_name)


def validate_single_function_with_errors(
    function_text: str,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a single function and return validation result with error message.

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        if not function_text or not function_text.strip():
            return False, "Code cannot be empty"

        lines = function_text.strip().split("\n")
        if len(lines) > 150:
            return False, "Code exceeds maximum limit of 150 lines"

        try:
            tree = ast.parse(function_text.strip())
        except IndentationError:
            return (
                False,
                "Indentation error detected. Please check your code indentation",
            )
        except SyntaxError as e:
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

        function_count = 0
        has_class = False
        invalid_constructs = []

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                function_count += 1
            elif isinstance(node, ast.ClassDef):
                has_class = True
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
                    ast.Try,
                ),
            ):
                continue
            else:
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    invalid_constructs.append("control flow statements")
                elif isinstance(node, ast.With):
                    invalid_constructs.append("context managers")
                else:
                    invalid_constructs.append("unsupported constructs")

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

        try:
            compile(function_text, "<string>", "exec")
        except SyntaxError:
            return (
                False,
                "Syntax error detected. Please check your code for typos or missing punctuation",
            )
        except Exception as e:
            return False, "Code compilation failed. Please check your code syntax"

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                return False, "Classes are not allowed anywhere in the code"

        namespace = None
        try:
            namespace = create_safe_execution_namespace()
            initial_functions = set(
                name
                for name, obj in namespace.items()
                if callable(obj) and hasattr(obj, "__code__")
            )

            exec(function_text, namespace)

            defined_functions = [
                obj
                for name, obj in namespace.items()
                if callable(obj)
                and hasattr(obj, "__code__")
                and name not in initial_functions
            ]

            if len(defined_functions) == 0:
                return False, "No executable function found in the code"
            elif len(defined_functions) > 1:
                return (
                    False,
                    "Multiple functions detected. Please include only one function",
                )

        except ImportError as e:
            try:
                tree = ast.parse(function_text.strip())
                function_defs = [
                    node for node in tree.body if isinstance(node, ast.FunctionDef)
                ]

                if len(function_defs) == 1:
                    return True, None
                elif len(function_defs) == 0:
                    return False, "No function definition found in the code"
                else:
                    return (
                        False,
                        "Multiple function definitions found. Please include only one function",
                    )
            except Exception:
                return (
                    False,
                    f"Import error: {e}. Please check if all required modules are available",
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

    namespace = create_safe_execution_namespace()
    initial_functions = set(
        name
        for name, obj in namespace.items()
        if callable(obj) and hasattr(obj, "__code__")
    )

    exec(function_text, namespace)

    defined_functions = [
        obj
        for name, obj in namespace.items()
        if callable(obj) and hasattr(obj, "__code__") and name not in initial_functions
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
