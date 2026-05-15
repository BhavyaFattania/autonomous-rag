import pytest

@pytest.fixture(autouse=True)
def _setup_logging():
    from src.utils.logger import setup_logging
    setup_logging()
