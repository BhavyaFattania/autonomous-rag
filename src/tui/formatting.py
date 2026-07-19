"""Pure display-formatting helpers shared by TUI widgets."""


def compute_config_diff(current: dict, best: dict) -> list[tuple[str, object, str]]:
    """Returns one (field, value, note) triple per field in `current`, so the
    hero panel can show 'chunk_size 768, up from 512' instead of a bare value."""
    rows: list[tuple[str, object, str]] = []
    for key, cur_val in current.items():
        best_val = best.get(key)
        if cur_val == best_val:
            rows.append((key, cur_val, "same"))
        elif isinstance(cur_val, int | float) and isinstance(best_val, int | float):
            arrow = "↑" if cur_val > best_val else "↓"
            rows.append((key, cur_val, f"{arrow} from {best_val}"))
        else:
            rows.append((key, cur_val, "changed"))
    return rows
