"""
All API calls MUST go through src/utils/openrouter.py,
which calls add_cost() after every successful call.
"""

import threading
from src.utils.logger import get_logger

log = get_logger("cost_tracker")

_lock = threading.Lock()
_total_cost_usd: float = 0.0
_hard_ceiling: float = 10.00
_warning_threshold: float = 7.00


def initialize(hard_ceiling: float, warning_threshold: float):
    global _hard_ceiling, _warning_threshold, _total_cost_usd
    with _lock:
        _hard_ceiling = hard_ceiling
        _warning_threshold = warning_threshold
        _total_cost_usd = 0.0


def add_cost(usd: float) -> float:
    """Add cost and return new total. Raises BudgetExceededError if ceiling hit."""
    global _total_cost_usd
    with _lock:
        _total_cost_usd += usd
        total = _total_cost_usd
        if total >= _hard_ceiling:
            log.critical("budget_ceiling_hit", total=total, ceiling=_hard_ceiling)
            raise BudgetExceededError(
                f"Cost ${total:.4f} exceeds ceiling ${_hard_ceiling:.2f}. Stopping."
            )
        elif total >= _warning_threshold:
            log.warning("budget_warning", total=total, threshold=_warning_threshold)
        return total


def get_total() -> float:
    with _lock:
        return _total_cost_usd


class BudgetExceededError(Exception):
    pass
