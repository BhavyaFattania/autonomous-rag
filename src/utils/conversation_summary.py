# src/utils/conversation_summary.py
"""
Sliding-window conversation summary middleware.

Keeps the most recent `recent_k` entries verbatim and LLM-compresses all
older entries (plus any prior summary) into a compact bullet-point summary.
This controls context-window and prompt-size growth across long overnight runs.

Two public APIs:
- sliding_window_compress       — for plain string history entry lists
- sliding_window_compress_messages — for OpenAI-style message dicts
"""

from __future__ import annotations

from src.prompts.templates import HISTORY_SUMMARY_TEMPLATE
from src.utils.context_budget import truncate_to_token_budget
from src.utils.logger import get_logger

log = get_logger("conversation_summary")

# Model used for compression calls — flash is fast and cheap for summarisation.
_SUMMARY_MODEL = "deepseek/deepseek-v4-flash"
_MAX_SUMMARY_TOKENS = 512


def _call_summary_llm_sync_fallback(
    existing_summary: str,
    older_text: str,
    max_tokens: int = _MAX_SUMMARY_TOKENS,
) -> str:
    """Graceful fallback when the LLM call fails: concatenate + truncate at a sentence boundary."""
    raw = (existing_summary + "\n" + older_text).strip()
    return truncate_to_token_budget(raw, max_tokens)


async def sliding_window_compress(
    entries: list[str],
    recent_k: int = 10,
    existing_summary: str = "",
    model_id: str = _SUMMARY_MODEL,
) -> tuple[list[str], str]:
    """
    Apply sliding-window compression to a list of string history entries.

    If ``len(entries) <= recent_k`` nothing is compressed and the inputs are
    returned unchanged (no LLM call is made).

    Otherwise the oldest ``len(entries) - recent_k`` entries are LLM-summarised
    together with any ``existing_summary``. Only the most recent ``recent_k``
    entries are returned verbatim.

    Args:
        entries: Ordered list of history strings (oldest first).
        recent_k: Number of recent entries to keep verbatim.
        existing_summary: Previously generated summary of even older entries.
        model_id: OpenRouter model for summarisation (default: flash).

    Returns:
        ``(recent_entries, summary_text)``
        - ``recent_entries``: the last ``recent_k`` entries, unchanged.
        - ``summary_text``: LLM-compressed summary of everything older.
    """
    if len(entries) <= recent_k:
        # Nothing to compress — return as-is, no LLM call.
        return entries, existing_summary

    older = entries[:-recent_k]
    recent = entries[-recent_k:]

    prior_block = (
        f"Prior summary (already compressed):\n{existing_summary}\n\n" if existing_summary else ""
    )
    entries_text = "\n".join(older)
    prompt = HISTORY_SUMMARY_TEMPLATE.format(
        prior_block=prior_block,
        entries_text=entries_text,
    )

    try:
        from src.utils.openrouter import call_openrouter

        raw = await call_openrouter(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=_MAX_SUMMARY_TOKENS,
            task="history_summary",
            temperature=0.0,
        )
        # call_openrouter returns str or {"content": ..., "reasoning": ...}
        new_summary = (raw if isinstance(raw, str) else raw.get("content", "")).strip()  # type: ignore[union-attr]
    except Exception as exc:
        log.warning("history_summary_failed", error=str(exc))
        new_summary = _call_summary_llm_sync_fallback(existing_summary, entries_text)

    log.info(
        "history_compressed",
        older_count=len(older),
        recent_count=len(recent),
        summary_chars=len(new_summary),
    )
    return recent, new_summary


async def sliding_window_compress_messages(
    messages: list[dict],
    recent_k: int = 10,
    existing_summary: str = "",
    model_id: str = _SUMMARY_MODEL,
) -> tuple[list[dict], str]:
    """
    Apply sliding-window compression to an OpenAI-style messages list.

    Keeps the last ``recent_k`` messages verbatim. Compresses older messages
    into a summary injected as a leading ``system`` message.

    Args:
        messages: List of ``{"role": ..., "content": ...}`` dicts.
        recent_k: Number of recent messages to keep verbatim.
        existing_summary: Previously generated summary of even older messages.
        model_id: Model for summarisation.

    Returns:
        ``(compressed_messages, summary_text)``
        - ``compressed_messages``: ``[system_summary_msg] + recent_verbatim_msgs``
          (or just the original list if no compression was needed).
        - ``summary_text``: The raw text of the generated summary.
    """
    if len(messages) <= recent_k:
        return messages, existing_summary

    older = messages[:-recent_k]
    recent = messages[-recent_k:]

    older_text = "\n".join(f"[{m.get('role', '?')}]: {m.get('content', '')}" for m in older)
    prior_block = (
        f"Prior summary (already compressed):\n{existing_summary}\n\n" if existing_summary else ""
    )
    prompt = HISTORY_SUMMARY_TEMPLATE.format(
        prior_block=prior_block,
        entries_text=older_text,
    )

    try:
        from src.utils.openrouter import call_openrouter

        raw = await call_openrouter(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=_MAX_SUMMARY_TOKENS,
            task="history_summary",
            temperature=0.0,
        )
        new_summary = (raw if isinstance(raw, str) else raw.get("content", "")).strip()  # type: ignore[union-attr]
    except Exception as exc:
        log.warning("history_summary_failed_messages", error=str(exc))
        new_summary = _call_summary_llm_sync_fallback(existing_summary, older_text)

    log.info(
        "messages_compressed",
        older_count=len(older),
        recent_count=len(recent),
        summary_chars=len(new_summary),
    )

    # Prepend the summary as a system message so the LLM sees it as context.
    summary_message: dict = {
        "role": "system",
        "content": f"[Compressed conversation history]\n{new_summary}",
    }
    return [summary_message] + recent, new_summary
