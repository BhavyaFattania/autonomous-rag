try:
    from langfuse import observe
except ImportError:

    def observe(*args, **kwargs):
        def decorator(func):
            return func

        return decorator
