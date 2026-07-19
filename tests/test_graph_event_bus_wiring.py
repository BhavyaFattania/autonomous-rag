"""Confirms build_graph() threads event_bus into the indexer node's partial
without requiring every other node to know about it."""

import inspect

from src.core.events import EventBus
from src.core.provider import Provider
from src.orchestrator.graph import build_graph


class _Settings:
    pass


def test_build_graph_accepts_event_bus_param():
    sig = inspect.signature(build_graph)
    assert "event_bus" in sig.parameters
    assert sig.parameters["event_bus"].default is None


def test_indexer_node_partial_receives_event_bus():
    bus = EventBus()
    graph = build_graph(settings=_Settings(), provider=Provider(), event_bus=bus)

    # LangGraph wraps an async node function in a RunnableCallable; the actual
    # bound functools.partial lives at .afunc (async), not on the wrapper itself.
    # .afunc is a RunnableCallable implementation detail, not part of the public
    # Runnable type, so it's reached via getattr rather than dotted access.
    indexer_runnable = graph.get_graph().nodes["indexer"].data
    afunc = getattr(indexer_runnable, "afunc", None)
    bound_kwargs = getattr(afunc, "keywords", {})
    assert bound_kwargs.get("event_bus") is bus


def test_build_graph_without_event_bus_defaults_to_none():
    graph = build_graph(settings=_Settings(), provider=Provider())

    # LangGraph wraps an async node function in a RunnableCallable; the actual
    # bound functools.partial lives at .afunc (async), not on the wrapper itself.
    # .afunc is a RunnableCallable implementation detail, not part of the public
    # Runnable type, so it's reached via getattr rather than dotted access.
    indexer_runnable = graph.get_graph().nodes["indexer"].data
    afunc = getattr(indexer_runnable, "afunc", None)
    bound_kwargs = getattr(afunc, "keywords", {})
    assert bound_kwargs.get("event_bus") is None
