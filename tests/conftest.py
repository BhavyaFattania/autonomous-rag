"""Global test fixtures: logging setup and teardown."""

import pytest


@pytest.fixture(autouse=True)
def _setup_logging():
    """Initializes logging before each test."""
    from src.utils.logger import setup_logging

    setup_logging()