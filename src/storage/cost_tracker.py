"""
All API calls MUST go through src/utils/openrouter.py,
which calls add_cost() after every successful call.

Refactored to support DI: module-level singleton is now a
CostTracker instance. Functions delegate to it for backward compat.
"""

import threading
from src.utils.logger import get_logger

log = get_logger("cost_tracker")


class CostTracker:
    def __init__(self, hard_ceiling: float = 10.00, warning_threshold: float = 7.00):
        self._lock = threading.Lock()
        self._total_cost_usd: float = 0.0
        self._hard_ceiling: float = hard_ceiling
        self._warning_threshold: float = warning_threshold

    def initialize(self, hard_ceiling: float, warning_threshold: float, start_cost: float = 0.0):
        with self._lock:
            self._hard_ceiling = hard_ceiling
            self._warning_threshold = warning_threshold
            self._total_cost_usd = start_cost

    def add_cost(self, usd: float) -> float:
        with self._lock:
            self._total_cost_usd += usd
            total = self._total_cost_usd
            if total >= self._hard_ceiling:
                log.critical("budget_ceiling_hit", total=total, ceiling=self._hard_ceiling)
                raise BudgetExceededError(
                    f"Cost ${total:.4f} exceeds ceiling ${self._hard_ceiling:.2f}. Stopping."
                )
            elif total >= self._warning_threshold:
                log.warning("budget_warning", total=total, threshold=self._warning_threshold)
            return total

    def get_total(self) -> float:
        with self._lock:
            return self._total_cost_usd


# ── Global default instance (backward compat) ──────────────────────────────────
_default_tracker = CostTracker()


def initialize(hard_ceiling: float, warning_threshold: float, start_cost: float = 0.0):
    _default_tracker.initialize(hard_ceiling, warning_threshold, start_cost)


def add_cost(usd: float) -> float:
    return _default_tracker.add_cost(usd)


def get_total() -> float:
    return _default_tracker.get_total()


def set_default_tracker(tracker: CostTracker):
    global _default_tracker
    _default_tracker = tracker


class BudgetExceededError(Exception):
    pass
