from config.loader import load_model_routing

from src.core.provider import Provider
from src.prompts.templates import QA_GENERATION_TEMPLATE
from src.utils.langfuse_compat import observe

model_routing = load_model_routing()
generator_primary = model_routing.rag_generator_primary
generator_fallback = model_routing.rag_generator_fallback


@observe(name="generate_answer")
async def generate_answer(
    question: str,
    contexts: list[str],
    provider: Provider,
    model_id: str = generator_primary.model_id,
) -> str:
    context_text = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    prompt = QA_GENERATION_TEMPLATE.format(context_text=context_text, question=question)

    answer = await provider.llm_client.call(
        model_id=model_id,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        task="rag_generation",
        reasoning_effort=None,
        temperature=0.1,
        fallback_model_id="deepseek/deepseek-v4-flash" if model_id.endswith(":free") else None,
    )
    return answer
