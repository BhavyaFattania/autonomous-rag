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
    from config.models import ModelConfig

    judge_config = ModelConfig(
        model_id="openrouter/test-model",
        response_format="json_object",
        reasoning=False,
        task="ragas_judge",
    )

    assert _build_openrouter_model_kwargs(judge_config) == {
        "response_format": {"type": "json_object"}
    }
    assert _build_openrouter_extra_body(judge_config) == {
        "reasoning": {"effort": "none", "exclude": True}
    }


def test_ragas_judge_defaults_to_openrouter_provider():
    from config.models import ModelConfig

    judge_config = ModelConfig(model_id="openrouter/test-model", task="ragas_judge")

    assert judge_config.provider == "openrouter"


def test_resolve_api_key_uses_provider_specific_env_var():
    from src.evaluator.ragas_setup import _resolve_api_key

    env = {"OPENROUTER_API_KEY": "or-key", "OPENAI_API_KEY": "oai-key"}

    assert _resolve_api_key("openrouter", env, None) == "or-key"
    assert _resolve_api_key("openai", env, None) == "oai-key"
    assert _resolve_api_key("openai", env, "explicit-override") == "explicit-override"


def test_resolve_api_key_rejects_unknown_provider():
    import pytest
    from src.evaluator.ragas_setup import _resolve_api_key

    with pytest.raises(ValueError, match="Unknown llm_provider"):
        _resolve_api_key("anthropic", {}, None)


def test_ragas_header_and_extra_body_builders_default_to_no_ops_for_openai():
    from config.models import ModelConfig
    from src.evaluator.ragas_setup import _EXTRA_BODY_BUILDERS, _HEADER_BUILDERS, _no_extra_body

    judge_config = ModelConfig(
        model_id="gpt-4o-mini",
        response_format="json_object",
        reasoning=False,
        task="ragas_judge",
        provider="openai",
    )

    assert "openai" not in _HEADER_BUILDERS
    assert _HEADER_BUILDERS.get("openai", lambda: {})() == {}
    assert _EXTRA_BODY_BUILDERS.get("openai", _no_extra_body)(judge_config) == {}


def test_build_ragas_metrics_uses_requested_names():
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
