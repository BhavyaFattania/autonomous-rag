"""Tests for the RAGAS output-parser compat patch: JSON repair and unwrapping of malformed LLM judge output."""

from langchain_core.prompt_values import StringPromptValue
from pydantic import BaseModel
from ragas.prompt.pydantic_prompt import RagasOutputParser
from src.evaluator.ragas_setup import (
    _build_openrouter_extra_body,
    _build_openrouter_model_kwargs,
)
from src.evaluator.ragas_setup import (
    build_ragas_metrics as _build_ragas_metrics,
)
from src.utils.json_repair import (
    install_ragas_output_parser_compat_patch as _install_ragas_output_parser_compat_patch,
)


class Verification(BaseModel):
    reason: str
    verdict: int


class ContextRecallClassification(BaseModel):
    statement: str
    reason: str
    attributed: int


class ContextRecallClassifications(BaseModel):
    classifications: list[ContextRecallClassification]


async def test_ragas_parser_unwraps_text_wrapped_json():
    """Output wrapped in a {"text": "..."} envelope is unwrapped before pydantic parsing."""
    _install_ragas_output_parser_compat_patch()
    parser = RagasOutputParser(pydantic_object=Verification)

    result = await parser.parse_output_string(
        output_string='{"text": "{\\"reason\\": \\"not useful\\", \\"verdict\\": 0}"}',
        prompt_value=StringPromptValue(text="Output: "),
        llm=None,  # type: ignore
        callbacks=[],
        retries_left=0,
    )

    assert result == Verification(reason="not useful", verdict=0)


async def test_ragas_parser_wraps_bare_recall_classification_list():
    """A bare JSON list is wrapped into the expected {"classifications": [...]} shape."""
    _install_ragas_output_parser_compat_patch()
    parser = RagasOutputParser(pydantic_object=ContextRecallClassifications)

    result = await parser.parse_output_string(
        output_string=('[{"statement": "A", "reason": "supported", "attributed": 1}]'),
        prompt_value=StringPromptValue(text="Output: "),
        llm=None,  # type: ignore
        callbacks=[],
        retries_left=0,
    )

    assert result.classifications == [
        ContextRecallClassification(
            statement="A",
            reason="supported",
            attributed=1,
        )
    ]


async def test_ragas_parser_uses_conservative_fallback_for_malformed_verdict():
    """Non-JSON key:value text still parses, defaulting to a conservative (0) verdict."""
    _install_ragas_output_parser_compat_patch()
    parser = RagasOutputParser(pydantic_object=Verification)

    result = await parser.parse_output_string(
        output_string='reason: not useful verdict: "0"',
        prompt_value=StringPromptValue(text="Output: "),
        llm=None,  # type: ignore
        callbacks=[],
        retries_left=0,
    )

    assert result.verdict == 0


async def test_ragas_parser_repairs_bang_corrupted_verdict_json():
    """JSON corrupted with stray "!" characters (a known judge-model quirk) is repaired before parsing."""
    _install_ragas_output_parser_compat_patch()
    parser = RagasOutputParser(pydantic_object=Verification)

    result = await parser.parse_output_string(
        output_string='!{! "reason": "supported!", "verdict": !!1! }',
        prompt_value=StringPromptValue(text="Output: "),
        llm=None,  # type: ignore
        callbacks=[],
        retries_left=0,
    )

    assert result.verdict == 1


async def test_ragas_parser_repairs_bang_corrupted_recall_keys():
    """The same "!"-corruption repair also works when keys (not just values) are corrupted."""
    _install_ragas_output_parser_compat_patch()
    parser = RagasOutputParser(pydantic_object=ContextRecallClassifications)

    result = await parser.parse_output_string(
        output_string=(
            '{! "classifications!": [!{! "statement!": "A", '
            '"reason!": "supported", "attributed!!!": !1! }!]}'
        ),
        prompt_value=StringPromptValue(text="Output: "),
        llm=None,  # type: ignore
        callbacks=[],
        retries_left=0,
    )

    assert result.classifications[0].attributed == 1


def test_ragas_judge_openrouter_kwargs_force_json_without_reasoning():
    """A judge ModelConfig with exclude_reasoning=True produces the OpenRouter kwargs to disable reasoning tokens."""
    from config.models import ModelConfig

    judge_config = ModelConfig(
        model_id="openrouter/test-model",
        response_format="json_object",
        exclude_reasoning=True,
    )

    assert _build_openrouter_model_kwargs(judge_config) == {
        "response_format": {"type": "json_object"}
    }
    assert _build_openrouter_extra_body(judge_config) == {
        "reasoning": {"effort": "none", "exclude": True}
    }


def test_build_ragas_metrics_uses_requested_names():
    """build_ragas_metrics returns metric objects matching the requested names, in the same order."""
    metrics = _build_ragas_metrics(
        [
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
            "context_utilization",
        ]
    )

    assert [metric.name for metric in metrics] == [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "context_utilization",
    ]
