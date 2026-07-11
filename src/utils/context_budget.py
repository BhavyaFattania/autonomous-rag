# src/utils/context_budget.py
"""
Shared token counting and budget-aware truncation for LLM context management.

Single source of truth for "how many tokens is this text" and "trim this text
to fit a token budget without cutting mid-sentence". Used by every history/
summary truncation path (conversation_summary, prompt_builder, reflection) so
they share one accounting method instead of three different char-based guesses.
"""

from __future__ import annotations

import tiktoken

from src.utils.logger import get_logger

log = get_logger("context_budget")

# cl100k_base is a reasonable general-purpose tokenizer for budgeting purposes
# across the various OpenRouter-hosted models used in this project; none of
# them ship a public tiktoken-compatible encoding, so an exact per-model
# encoding is not available. This is used only for budget estimation, not for
# billing-accurate counts.
_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens in text using the shared tokenizer."""
    if not text:
        return 0
    return len(_ENCODING.encode(text))


def truncate_to_token_budget(text: str, max_tokens: int) -> str:
    """
    Trim text to fit within max_tokens, cutting at a sentence boundary when
    possible rather than mid-word/mid-sentence.
    """
    if max_tokens <= 0 or not text:
        return ""

    tokens = _ENCODING.encode(text)
    if len(tokens) <= max_tokens:
        return text

    window = _ENCODING.decode(tokens[:max_tokens])
    for sep in ("\n", ".", "!", "?"):
        idx = window.rfind(sep)
        if idx > len(window) // 2:
            return window[: idx + 1].rstrip()
    return window.rstrip()
