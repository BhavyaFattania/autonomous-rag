from src.utils.openrouter import call_openrouter

async def generate_answer(question: str, contexts: list[str]) -> str:
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
        model_id="deepseek/deepseek-v4-flash:free",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        task="rag_generation",
        reasoning_effort=None,
        temperature=0.1,
        fallback_model_id="deepseek/deepseek-v4-flash",
    )
    return answer
