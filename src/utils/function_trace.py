"""
Function-level trace logging for deep debugging of the scientist pipeline.

Provides a @trace_call decorator that logs every function call with:
- Timestamp (ISO 8601)
- Function name and qualified module
- All argument values (repr'd, truncated)
- Return value (repr'd, truncated)
- Duration in milliseconds
- Thread name

Writes to data/traces/trace_{run_id}.jsonl (one JSON line per call).

Usage:
    from src.utils.function_trace import trace_call, init_trace, close_trace

    # At run start:
    init_trace(run_id="...")

    # Decorate any function:
    @trace_call
    async def my_func(a, b, c=3):
        ...

    @trace_call(log_args=False)  # hide args for large datasets
    def big_func(data):
        ...

    # At run end:
    close_trace()
"""

import functools
import inspect
import json
import os
import time
import threading
from datetime import datetime, timezone
from pathlib import Path

_TRACE_DIR = Path("data/traces")
_trace_file: "TextIO | None" = None
_trace_lock = threading.RLock()  # RLock so init_trace → _write_entry doesn't deadlock


def init_trace(run_id: str):
    """Open the trace JSONL file for a given run_id."""
    global _trace_file
    _TRACE_DIR.mkdir(parents=True, exist_ok=True)
    path = _TRACE_DIR / f"trace_{run_id}.jsonl"
    with _trace_lock:
        if _trace_file:
            try:
                _trace_file.close()
            except Exception:
                pass
        _trace_file = open(path, "w", encoding="utf-8")
        _write_entry({
            "event": "trace_start",
            "run_id": run_id,
            "path": str(path),
        })


def close_trace():
    """Close the trace file if open."""
    global _trace_file
    with _trace_lock:
        if _trace_file:
            try:
                _write_entry({"event": "trace_end"})
                _trace_file.close()
            except Exception:
                pass
            _trace_file = None


def _safe_repr(obj, max_len: int = 300) -> str:
    """Safely repr an object, truncating if too long."""
    try:
        r = repr(obj)
        if len(r) > max_len:
            half = max_len // 2 - 2
            r = r[:half] + "..." + r[-half:]
        return r
    except Exception:
        return "<repr-error>"


def _write_entry(entry: dict):
    """Write a JSON line to the trace file. Thread-safe."""
    global _trace_file
    if _trace_file is None:
        return
    try:
        line = json.dumps(entry, default=str, ensure_ascii=False) + "\n"
        with _trace_lock:
            if _trace_file:
                _trace_file.write(line)
                _trace_file.flush()
    except Exception:
        pass  # never let logging crash the application


def _format_call_args(func, args, kwargs, max_len: int) -> dict:
    """Bind actual args to parameter names and repr each value."""
    try:
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
    except (TypeError, ValueError):
        # Fallback: positional
        result = {}
        for i, a in enumerate(args):
            result[f"_arg{i}"] = _safe_repr(a, max_len)
        for k, v in kwargs.items():
            result[k] = _safe_repr(v, max_len)
        return result

    result = {}
    for name, value in bound.arguments.items():
        if name == "self":
            result[name] = type(value).__name__
        elif name == "cls":
            result[name] = f"<class {value.__name__}>"
        elif name == "state" and isinstance(value, dict):
            # For the WorkflowState dict, log summary keys, not the whole thing
            keys = list(value.keys())
            result[name] = f"<dict keys={keys[:15]}>"
        else:
            result[name] = _safe_repr(value, max_len)
    return result


def trace_call(func=None, *, log_args: bool = True, log_return: bool = True,
               max_len: int = 300, label: str | None = None):
    """
    Decorator that traces function entry/exit to the trace JSONL file.

    Can be used with or without arguments:
        @trace_call
        def foo(): ...

        @trace_call(log_args=False)
        def bar(): ...

    Parameters
    ----------
    func : callable, optional
        The function to decorate (when used without arguments).
    log_args : bool
        Whether to log argument values (default True).
    log_return : bool
        Whether to log the return value (default True).
    max_len : int
        Max length of repr'd args/return (default 300).
    label : str, optional
        Override the logged function name (defaults to func.__name__).
    """
    if func is None:
        return lambda f: trace_call(
            f, log_args=log_args, log_return=log_return,
            max_len=max_len, label=label,
        )

    _func_name = label or func.__name__
    _mod_name = func.__module__

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        return await _trace_impl(
            func, args, kwargs, _func_name, _mod_name,
            log_args, log_return, max_len,
        )

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        return _trace_impl_sync(
            func, args, kwargs, _func_name, _mod_name,
            log_args, log_return, max_len,
        )

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


async def _trace_impl(func, args, kwargs, func_name, mod_name,
                      log_args, log_return, max_len):
    """Async trace implementation."""
    if _trace_file is None:
        return await func(*args, **kwargs)

    call_args = _format_call_args(func, args, kwargs, max_len) if log_args else {}
    start = time.monotonic()
    exc = None

    try:
        result = await func(*args, **kwargs)
    except Exception as e:
        exc = e
        result = None
        raise
    finally:
        _emit_trace_entry(
            func_name, mod_name, call_args,
            result if not exc else None,
            _safe_repr(exc) if exc else None,
            time.monotonic() - start, log_return, max_len,
        )
    return result


def _trace_impl_sync(func, args, kwargs, func_name, mod_name,
                     log_args, log_return, max_len):
    """Sync trace implementation."""
    if _trace_file is None:
        return func(*args, **kwargs)

    call_args = _format_call_args(func, args, kwargs, max_len) if log_args else {}
    start = time.monotonic()
    exc = None

    try:
        result = func(*args, **kwargs)
    except Exception as e:
        exc = e
        result = None
        raise
    finally:
        _emit_trace_entry(
            func_name, mod_name, call_args,
            result if not exc else None,
            _safe_repr(exc) if exc else None,
            time.monotonic() - start, log_return, max_len,
        )
    return result


def _emit_trace_entry(func_name, mod_name, call_args,
                      result, exc_str, duration, log_return, max_len):
    """Write a single trace line."""
    entry = {
        "event": "call_exception" if exc_str else "call_return",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "function": func_name,
        "module": mod_name,
        "thread": threading.current_thread().name,
        "args": call_args,
        "duration_ms": round(duration * 1000, 2),
    }
    if exc_str:
        entry["exception"] = exc_str
    elif log_return:
        entry["return"] = _safe_repr(result, max_len)
    else:
        entry["return"] = "<hidden>"

    _write_entry(entry)
