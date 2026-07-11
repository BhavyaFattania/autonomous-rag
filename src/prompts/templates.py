# src/prompts/templates.py
"""
Central registry of LLM prompt templates used across the codebase.

Each template is a plain ``str.format``-style string constant. Callers own
building the substitution values; this module owns the wording, so the same
prompt text can't drift into multiple copy-pasted inline f-strings.
"""

from __future__ import annotations

QA_GENERATION_TEMPLATE = """\
Answer the following question using only the provided context.
If the context does not contain enough information, say "I don't know."

Context:
{context_text}

Question: {question}
Answer:"""

REFLECTION_TEMPLATE = """\
You are analyzing a RAG optimization run.

Current best score: {best_score:.4f}
Current best config: {best_config}

Accepted patterns:
{successful}

Rejected or failed patterns:
{failed}

Extract concise, actionable rules for the next scientist prompt. Focus on which
chunking, top_k, hybrid_alpha, reranker, and generator choices appear to help or
hurt. Do not invent evidence. Return 5-8 bullet points only."""

REPORT_TEMPLATE = """\
Write a concise markdown report for this autonomous RAG optimization run.
Include: final result, best config, metric summary, what improved, what failed,
and recommended next experiments. Be specific and do not overstate evidence.

Run data:
{payload_json}"""

HISTORY_SUMMARY_TEMPLATE = """\
You are summarising the history of a RAG hyperparameter optimisation experiment.

{prior_block}Experiment entries to summarise:
{entries_text}

Write a concise factual bullet-point summary (3-6 bullets) covering:
- Which retrieval/chunking configs performed well and why
- Which configs failed and the likely cause
- Any clear patterns (e.g. "hybrid_alpha > 0.5 consistently hurts recall")

Rules:
- Do not invent information. Be specific and brief.
- Each bullet must start with "•"
- Do not repeat the current best config verbatim — focus on patterns."""
