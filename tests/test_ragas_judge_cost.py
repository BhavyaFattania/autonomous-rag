from config.models import ModelConfig
from src.evaluator.ragas_setup import build_ragas_llm


def test_ragas_judge_chatmodel_carries_cost_callback():
    cfg = ModelConfig(
        model_id="openai/gpt-oss-safeguard-20b",
        task="ragas_judge",
        base_url="https://openrouter.ai/api/v1",
        provider="openrouter",
    )

    class _Tracker:
        def add_cost(self, usd):
            return usd

    wrapper = build_ragas_llm(cfg, env={"OPENROUTER_API_KEY": "k"}, cost_tracker=_Tracker())
    chat = wrapper.langchain_llm  # the underlying ChatOpenAI
    cb_names = [type(cb).__name__ for cb in (chat.callbacks or [])]
    assert "CostTrackingCallback" in cb_names
