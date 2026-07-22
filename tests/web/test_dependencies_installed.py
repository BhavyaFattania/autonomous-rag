"""Smoke test proving fastapi/uvicorn are installed in this project's venv,
not just declared in pyproject.toml."""


def test_fastapi_importable():
    import fastapi

    assert fastapi.__version__


def test_uvicorn_importable():
    import uvicorn

    assert uvicorn.__version__


def test_websockets_extra_installed():
    # uvicorn[standard] must include websocket support for /ws/live to work
    import uvicorn.protocols.websockets  # noqa: F401
