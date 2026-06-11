try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from src.utils.openrouter import call_openrouter

@traceable(name="generate_answer")
async def generate_answer(
    question: str,
    contexts: list[str],
    model_id: str = "deepseek/deepseek-v4-flash",
) -> str:
    """
    Returns answer string.
    Uses free V4-Flash first; falls back to paid V4-Flash on rate limit.
    """
    context_text = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    prompt = f"""Answer the following question using only the provided context.
If the context does not contain enough information, say "I don't know."

Context:
{context_text}

Question: {question}
Answer:"""

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
