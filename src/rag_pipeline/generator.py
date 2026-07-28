from src.core.provider import Provider
from src.prompts.templates import QA_GENERATION_TEMPLATE
from src.utils.langfuse_compat import observe


@observe(name="generate_answer")
async def generate_answer(
    question: str,
    contexts: list[str],
    provider: Provider,
    model_id: str | None = None,
) -> str:
    context_text = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    prompt = QA_GENERATION_TEMPLATE.format(context_text=context_text, question=question)

    configured_model = provider.get_model_config("rag_generator_primary")
    resolved_model_id = model_id or configured_model.model_id
    answer = await provider.call_model(
        "rag_generator_primary",
        messages=[{"role": "user", "content": prompt}],
        model_id=resolved_model_id,
        max_tokens=1024,
        task="rag_generation",
        reasoning_effort=None,
        temperature=0.1,
        fallback_model_id=(
            "deepseek/deepseek-v4-flash" if resolved_model_id.endswith(":free") else None
        ),
    )
    return answer if isinstance(answer, str) else answer.get("content", "")
