"""Report generation for RAG optimization runs.

Generates markdown summaries of experiment results, including best configs,
metrics, successful/failed patterns, and recommendations for next experiments.
"""

from src.reporter.report_writer import report_writer_node

__all__ = [
    "report_writer_node",
]
