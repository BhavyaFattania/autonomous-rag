"""Langfuse observability integration with graceful fallback.

Provides the @observe decorator for tracing LLM calls. Falls back to a no-op
decorator if Langfuse is not installed, allowing optional observability.
"""

try:
    from langfuse import observe
except ImportError:

    def observe(*args, **kwargs):
        """No-op fallback decorator when Langfuse is unavailable."""

        def decorator(func):
            return func

        return decorator
