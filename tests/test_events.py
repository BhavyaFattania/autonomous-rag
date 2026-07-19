"""Tests for the ExperimentEvent model and EventBus pub-sub broker."""

from datetime import UTC, datetime

import pytest
from src.core.events import EventBus, ExperimentEvent


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


def test_experiment_event_defaults():
    event = _event()
    assert event.message == ""
    assert event.config == {}
    assert event.metrics == {}
    assert event.progress_current is None
    assert event.progress_total is None
    assert event.raw_event == {}


def test_subscribe_returns_independent_queues():
    bus = EventBus()
    q1 = bus.subscribe()
    q2 = bus.subscribe()
    assert q1 is not q2


def test_publish_delivers_to_all_subscribers():
    bus = EventBus()
    q1 = bus.subscribe()
    q2 = bus.subscribe()
    event = _event()

    bus.publish(event)

    assert q1.get_nowait() is event
    assert q2.get_nowait() is event


def test_publish_before_any_subscriber_is_a_noop():
    bus = EventBus()
    bus.publish(_event())  # must not raise


def test_slow_subscriber_does_not_block_fast_one():
    bus = EventBus()
    slow = bus.subscribe()
    fast = bus.subscribe()

    for i in range(5):
        bus.publish(_event(experiment=i))

    assert fast.qsize() == 5
    assert slow.qsize() == 5  # neither queue blocked the other on publish

    fast.get_nowait()  # draining one subscriber doesn't affect the other
    assert fast.qsize() == 4
    assert slow.qsize() == 5


@pytest.mark.asyncio
async def test_progress_fields_round_trip():
    event = _event(node="indexer", progress_current=64, progress_total=150)
    assert event.progress_current == 64
    assert event.progress_total == 150
