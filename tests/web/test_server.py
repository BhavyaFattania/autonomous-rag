"""Tests for the FastAPI app factory and its WebSocket connection registry."""

import pytest
from src.core.events import EventBus
from src.web.server import ConnectionManager, create_app


def test_create_app_stores_event_bus_on_state():
    bus = EventBus()
    app = create_app(bus)
    assert app.state.event_bus is bus


def test_create_app_has_a_connection_manager():
    app = create_app(EventBus())
    assert isinstance(app.state.connections, ConnectionManager)


@pytest.mark.asyncio
async def test_connection_manager_broadcasts_to_all_registered_sockets():
    manager = ConnectionManager()

    class _FakeSocket:
        def __init__(self):
            self.accepted = False
            self.received = []

        async def accept(self):
            self.accepted = True

        async def send_json(self, payload):
            self.received.append(payload)

    sock_a, sock_b = _FakeSocket(), _FakeSocket()
    await manager.connect(sock_a)
    await manager.connect(sock_b)

    await manager.broadcast({"hello": "world"})

    assert sock_a.accepted is True
    assert sock_a.received == [{"hello": "world"}]
    assert sock_b.received == [{"hello": "world"}]


@pytest.mark.asyncio
async def test_connection_manager_drops_dead_sockets_on_broadcast():
    manager = ConnectionManager()

    class _DeadSocket:
        async def accept(self):
            pass

        async def send_json(self, payload):
            raise RuntimeError("connection closed")

    class _LiveSocket:
        def __init__(self):
            self.received = []

        async def accept(self):
            pass

        async def send_json(self, payload):
            self.received.append(payload)

    dead, live = _DeadSocket(), _LiveSocket()
    await manager.connect(dead)
    await manager.connect(live)

    await manager.broadcast({"x": 1})
    # second broadcast proves the dead socket was actually removed, not just
    # skipped this once -- if it were still registered, broadcasting again
    # would raise the same RuntimeError and fail this test
    await manager.broadcast({"x": 2})

    assert live.received == [{"x": 1}, {"x": 2}]


def test_connection_manager_disconnect_is_safe_for_unknown_socket():
    manager = ConnectionManager()
    manager.disconnect(object())  # must not raise
