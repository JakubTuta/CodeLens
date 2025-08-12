def create_test_title(test_name: str) -> str:
    """Create a human-readable title from a test name."""
    if test_name.startswith("test_"):
        test_name = test_name[5:]

    return " ".join(word.capitalize() for word in test_name.split("_"))


def indent_code(code: str, spaces: int) -> str:
    """Indent code by a specified number of spaces."""
    indent = " " * spaces
    return "\n".join(
        indent + line if line.strip() else line for line in code.split("\n")
    )
