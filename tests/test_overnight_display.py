"""Unit tests for overnight display utilities."""

import pytest
import importlib.util
import sys

# Load the module directly without triggering package imports
spec = importlib.util.spec_from_file_location(
    "overnight_display",
    "src/orchestrator/overnight_display.py"
)
overnight_display = importlib.util.module_from_spec(spec)
sys.modules["overnight_display"] = overnight_display
spec.loader.exec_module(overnight_display)
fmt_elapsed = overnight_display.fmt_elapsed


class TestFmtElapsed:
    """Tests for the fmt_elapsed pure function."""

    def test_zero_seconds(self):
        assert fmt_elapsed(0) == "0s"

    def test_seconds_only(self):
        assert fmt_elapsed(45) == "45s"

    def test_minutes_and_seconds(self):
        assert fmt_elapsed(90) == "1m 30s"

    def test_hours_minutes_seconds(self):
        assert fmt_elapsed(3661) == "1h 1m 1s"

    def test_hours_with_zero_minutes_seconds(self):
        assert fmt_elapsed(7200) == "2h 0m 0s"

    def test_float_input_truncates_to_int(self):
        """Float input should be truncated to integer seconds."""
        assert fmt_elapsed(90.9) == "1m 30s"

    def test_exact_minute_boundary(self):
        """Exactly 60 seconds should show as 1m 0s."""
        assert fmt_elapsed(60) == "1m 0s"

    def test_exact_hour_boundary(self):
        """Exactly 3600 seconds should show as 1h 0m 0s."""
        assert fmt_elapsed(3600) == "1h 0m 0s"

    def test_large_hours(self):
        """Multiple hours should format correctly."""
        assert fmt_elapsed(7265) == "2h 1m 5s"