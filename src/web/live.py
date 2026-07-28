"""WebSocket endpoint for the live event stream. On app startup, subscribes
to the shared EventBus and broadcasts one {event, state} JSON payload per
tick to every connected browser -- the direct replacement for the deleted
Textual RagOptimizerApp's _consume_events()/_apply_event() loop."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.web.schemas import DashboardStateSchema

router = APIRouter()


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket) -> None:
    manager = websocket.app.state.connections
    await manager.connect(websocket)
    # Send the current state immediately so a client connecting mid-run (a
    # fresh visitor, or a reconnect after a refresh) isn't blank until the
    # next tick happens to arrive -- there's no "since you've been gone"
    # replay, just a snapshot of where things stand right now.
    state = websocket.app.state.dashboard_state
    initial_payload = {
        "event": None,
        "state": DashboardStateSchema.from_state(state).model_dump(mode="json"),
    }
    await websocket.send_json(initial_payload)
    try:
        while True:
            # This endpoint is broadcast-only; it still needs to await
            # something so the connection stays open and FastAPI notices a
            # client-initiated disconnect (WebSocketDisconnect) promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def consume_events(app) -> None:
    """Runs for the lifetime of the app: pulls every ExperimentEvent off the
    app's EventBus, applies it to the shared DashboardState on app.state (also
    read by websocket_live() for new-connection snapshots), and broadcasts
    the result to all connected clients. Started from create_app's startup
    hook (see src/web/server.py) or directly by a test."""
    state = app.state.dashboard_state
    queue = app.state.event_bus.subscribe()
    while True:
        event = await queue.get()
        try:
            state.apply(event)
        except Exception:
            # A malformed event's blast radius stays contained to "this one
            # tick didn't update state" -- matches the crash-isolation
            # behavior DashboardState was originally built for in the TUI.
            continue
        payload = {
            "event": event.model_dump(mode="json"),
            "state": DashboardStateSchema.from_state(state).model_dump(mode="json"),
        }
        await app.state.connections.broadcast(payload)
