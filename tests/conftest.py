import importlib.metadata


def pytest_sessionstart() -> None:
    """Emit the lxml version in the Pytest output."""
    lxml_version = importlib.metadata.version("lxml")
    print(f"lxml: {lxml_version}")
