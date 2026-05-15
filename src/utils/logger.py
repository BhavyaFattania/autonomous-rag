import sys
import structlog
import logging


def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.dev.ConsoleRenderer(
                exception_formatter=structlog.dev.plain_traceback,
                colors=True,
            ),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Only show WARNING+ from noisy third-party libs
    for noisy in ("httpx", "httpcore", "openai", "chromadb", "llama_index"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def get_logger(name: str):
    return structlog.get_logger(name)
