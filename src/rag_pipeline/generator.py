from src.utils.langfuse_compat import observe
from src.utils.openrouter import call_openrouter
from src.core.provider import Provider


@observe(name="generate_answer")
async def generate_answer(
    question: str,
    contexts: list[str],
    model_id: str = "deepseek/deepseek-v4-flash",
    provider: Provider | None = None,
) -> str:
    context_text = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    prompt = f"""Answer the following question using only the provided context.
If the context does not contain enough information, say "I don't know."

Context:
{context_text}

Question: {question}
Answer:"""

    llm = provider.llm_client if provider else None
    if llm:
        answer = await llm.call(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            task="rag_generation",
            reasoning_effort=None,
            temperature=0.1,
            fallback_model_id="deepseek/deepseek-v4-flash" if model_id.endswith(":free") else None,
        )
    else:
        answer = await call_openrouter(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            task="rag_generation",
            reasoning_effort=None,
            temperature=0.1,
            fallback_model_id="deepseek/deepseek-v4-flash" if model_id.endswith(":free") else None,
        )
    return answer
