# src/utils/json_repair.py

import json
import re

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompt_values import StringPromptValue
from ragas.llms import LangchainLLMWrapper
from ragas.prompt.pydantic_prompt import RagasOutputParser
from ragas.prompt.utils import extract_json

from src.utils.logger import get_logger

log = get_logger("json_repair")


def install_ragas_output_parser_compat_patch() -> None:
    if getattr(RagasOutputParser, "_autonomous_rag_compat_patch", False):
        return

    RagasOutputParser.parse_output_string = _parse_ragas_output_string_compat
    RagasOutputParser._autonomous_rag_compat_patch = True


async def _parse_ragas_output_string_compat(
    self,
    output_string: str,
    prompt_value: StringPromptValue,
    llm: LangchainLLMWrapper,
    callbacks,
    retries_left: int = 1,
):
    callbacks = callbacks or []
    try:
        jsonstr = _normalize_ragas_json(output_string, self.pydantic_object)
        parser = PydanticOutputParser(pydantic_object=self.pydantic_object)
        return parser.invoke(jsonstr)
    except OutputParserException:
        fallback = _fallback_ragas_output(output_string, self.pydantic_object)
        log.warning(
            "ragas_output_parse_fallback",
            output_model=self.pydantic_object.__name__,
            output_preview=output_string[:240],
        )
        return self.pydantic_object(**fallback)


def _normalize_ragas_json(output_string: str, output_model: type) -> str:
    parsed = None
    parsed_jsonstr = output_string.strip()
    for jsonstr in [output_string.strip(), extract_json(output_string).strip()]:
        for candidate in _json_repair_candidates(jsonstr):
            try:
                parsed = json.loads(candidate)
                parsed_jsonstr = candidate
                break
            except json.JSONDecodeError:
                continue
        if parsed is not None:
            break

    if parsed is None:
        return _strip_json_bang_artifacts(extract_json(output_string).strip())

    fields = set(output_model.model_fields)
    if "classifications" in fields and isinstance(parsed, list):
        return json.dumps({"classifications": parsed})
    if "classifications" in fields and _looks_like_recall_item(parsed):
        return json.dumps({"classifications": [parsed]})
    if "classifications" in fields and isinstance(parsed, dict):
        classifications = parsed.get("classification")
        if isinstance(classifications, list):
            parsed["classifications"] = classifications
            return json.dumps(parsed)

    return parsed_jsonstr


def _json_repair_candidates(jsonstr: str) -> list[str]:
    unwrapped = _unwrap_text_wrapped_json(jsonstr)
    cleaned = _strip_json_bang_artifacts(jsonstr)
    cleaned_unwrapped = _unwrap_text_wrapped_json(cleaned)
    unwrapped_cleaned = _strip_json_bang_artifacts(unwrapped)
    return list(dict.fromkeys([unwrapped, unwrapped_cleaned, cleaned_unwrapped, cleaned, jsonstr]))


def _strip_json_bang_artifacts(text: str) -> str:
    return text.replace("!", "")


def _unwrap_text_wrapped_json(jsonstr: str) -> str:
    try:
        parsed = json.loads(jsonstr)
    except json.JSONDecodeError:
        return jsonstr

    if isinstance(parsed, dict) and isinstance(parsed.get("text"), str):
        text = parsed["text"].strip()
        if text.startswith("{") or text.startswith("["):
            return text
    return jsonstr


def _fallback_ragas_output(output_string: str, output_model: type) -> dict:
    output_string = _strip_json_bang_artifacts(output_string)
    fields = set(output_model.model_fields)
    if {"reason", "verdict"}.issubset(fields):
        return {
            "reason": _extract_reason(output_string),
            "verdict": _extract_binary_field(output_string, "verdict"),
        }
    if "classifications" in fields:
        return {
            "classifications": [
                {
                    "statement": _extract_quoted_field(output_string, "statement"),
                    "reason": _extract_reason(output_string),
                    "attributed": _extract_binary_field(output_string, "attributed"),
                }
            ]
        }
    return {}


def _looks_like_recall_item(value) -> bool:
    return isinstance(value, dict) and {"statement", "reason", "attributed"}.issubset(value)


def _extract_binary_field(text: str, field: str) -> int:
    pattern = rf'"?{re.escape(field)}"?\s*[:=]\s*"?([01]|yes|no|true|false)"?'
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return 0
    value = match.group(1).lower()
    return 1 if value in {"1", "yes", "true"} else 0


def _extract_reason(text: str) -> str:
    reason = _extract_quoted_field(text, "reason")
    if reason:
        return reason
    return "Could not parse judge rationale; using conservative fallback."


def _extract_quoted_field(text: str, field: str) -> str:
    pattern = rf'"{re.escape(field)}"\s*:\s*"((?:\\.|[^"\\])*)"'
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        return ""
    try:
        return json.loads(f'"{match.group(1)}"')
    except json.JSONDecodeError:
        return match.group(1)
