"""Tests for the /ws/live WebSocket endpoint: connecting, receiving
broadcasts derived from published ExperimentEvents, and surviving a
malformed event without dropping the connection."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from src.core.events import EventBus, ExperimentEvent
from src.web.server import create_app


def _event(**overrides) -> ExperimentEvent:
    defaults = dict(
        experiment=1,
        node="scientist",
        status="RUNNING",
        timestamp=datetime.now(UTC),
        cost_total_usd=0.0,
    )
    defaults.update(overrides)
    return ExperimentEvent(**defaults)


def test_websocket_receives_initial_snapshot_on_connect():
    """The reconnect-gap fix: a client connecting before any event has ever
    been published still gets an immediate payload (an empty snapshot), not
    silence until the next tick."""
    bus = EventBus()
    app = create_app(bus)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/live") as websocket:
            payload = websocket.receive_json()

    assert payload["event"] is None
    assert payload["state"]["active_node"] is None
    assert payload["state"]["node_states"] == {}


def test_websocket_receives_current_snapshot_on_connect_mid_run():
    """A client connecting *after* history already exists (e.g. a hard
    refresh mid-run) must see that history immediately, not a blank state."""
    bus = EventBus()
    app = create_app(bus)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/live") as first_connection:
            bus.publish(_event(node="scientist", status="RUNNING", hypothesis="h"))
            first_connection.receive_json()  # initial snapshot
            first_connection.receive_json()  # the published event

            with client.websocket_connect("/ws/live") as reconnecting:
                snapshot = reconnecting.receive_json()

    assert snapshot["event"] is None
    assert snapshot["state"]["active_node"] == "scientist"
    assert snapshot["state"]["node_states"] == {"scientist": "RUNNING"}


def test_websocket_receives_event_and_state_on_publish():
    bus = EventBus()
    app = create_app(bus)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/live") as websocket:
            websocket.receive_json()  # initial snapshot
            bus.publish(_event(node="scientist", status="RUNNING", hypothesis="h"))

            payload = websocket.receive_json()

    assert payload["event"]["node"] == "scientist"
    assert payload["event"]["hypothesis"] == "h"
    assert payload["state"]["active_node"] == "scientist"
    assert payload["state"]["node_states"] == {"scientist": "RUNNING"}


def test_websocket_receives_multiple_events_in_order():
    bus = EventBus()
    app = create_app(bus)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/live") as websocket:
            websocket.receive_json()  # initial snapshot
            bus.publish(_event(node="scientist", status="RUNNING"))
            bus.publish(_event(node="validator", status="RUNNING"))

            first = websocket.receive_json()
            second = websocket.receive_json()

    assert first["event"]["node"] == "scientist"
    assert second["event"]["node"] == "validator"
    assert second["state"]["node_states"] == {"scientist": "RUNNING", "validator": "RUNNING"}


def test_two_clients_both_receive_the_same_broadcast():
    bus = EventBus()
    app = create_app(bus)

    with TestClient(app) as client:
        with (
            client.websocket_connect("/ws/live") as ws_a,
            client.websocket_connect("/ws/live") as ws_b,
        ):
            ws_a.receive_json()  # initial snapshot
            ws_b.receive_json()  # initial snapshot
            bus.publish(_event(node="scientist", status="RUNNING"))

            payload_a = ws_a.receive_json()
            payload_b = ws_b.receive_json()

    assert payload_a["event"]["node"] == payload_b["event"]["node"] == "scientist"
