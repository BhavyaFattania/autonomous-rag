from src.storage.cost_tracker import get_total, initialize
from src.utils.openrouter import OpenRouterClient, _extract_reasoning_text


def test_extract_reasoning_text_from_reasoning_field():
    assert _extract_reasoning_text({"reasoning": "because retrieval improved"}) == (
        "because retrieval improved"
    )


def test_extract_reasoning_text_from_reasoning_details():
    message = {
        "reasoning_details": [
            {"type": "reasoning", "text": "first"},
            {"type": "reasoning", "content": "second"},
        ]
    }

    assert _extract_reasoning_text(message) == "first\nsecond"


class _FakeCostTracker:
    def __init__(self):
        self.reported = []

    def initialize(self, hard_ceiling, warning_threshold, start_cost=0.0):
        pass

    def add_cost(self, usd: float) -> float:
        self.reported.append(usd)
        return sum(self.reported)

    def get_total(self) -> float:
        return sum(self.reported)


def test_report_cost_uses_injected_tracker_not_module_singleton():
    """The real bug the audit flagged: cost must go to the tracker the client
    was actually constructed with, not whichever tracker the module-level
    singleton happens to be pointing at."""
    tracker = _FakeCostTracker()
    client = OpenRouterClient(api_key="sk-test", cost_tracker=tracker)

    client._report_cost(1.23)

    assert tracker.reported == [1.23]


def test_report_cost_falls_back_to_module_singleton_when_no_tracker_injected():
    """Backward compat: constructing without a tracker (e.g. the module-level
    _default_client) still reports through src.storage.cost_tracker's global."""
    initialize(hard_ceiling=100.0, warning_threshold=90.0)
    client = OpenRouterClient(api_key="sk-test")

    client._report_cost(2.5)

    assert get_total() == 2.5
