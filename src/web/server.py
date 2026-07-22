"""FastAPI app factory for the local web dashboard. Owns the WebSocket
ConnectionManager (broadcast target for src/web/live.py's event consumer)
and mounts the built frontend as static files, if present."""

from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

from src.core.events import EventBus

_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


class ConnectionManager:
    """Tracks currently-connected WebSocket clients and fans out broadcasts
    to all of them, silently dropping any that have gone away."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, payload: dict) -> None:
        dead = []
        for websocket in self._connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(websocket)


def create_app(event_bus: EventBus) -> FastAPI:
    app = FastAPI(title="Autonomous RAG Optimizer Dashboard")
    app.state.event_bus = event_bus
    app.state.connections = ConnectionManager()

    from src.web.history import router as history_router
    from src.web.live import router as live_router

    app.include_router(live_router)
    app.include_router(history_router)

    if _FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")

    return app
