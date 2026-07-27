"""
DI container — wires all external dependencies.
Substitute implementations in tests via Provider(impl_class(...)).
"""

from __future__ import annotations

from typing import Any

from src.core.interfaces import (
    IChromaClientFactory,
    ICostTracker,
    IDatabase,
    ILLMClient,
    IModelRoutingProvider,
    IRagasFactory,
)


class Provider:
    """Dependency injection container holding all external service implementations."""

    def __init__(
        self,
        cost_tracker: ICostTracker | None = None,
        llm_client: ILLMClient | None = None,
        database: IDatabase | None = None,
        chroma_factory: IChromaClientFactory | None = None,
        ragas_factory: IRagasFactory | None = None,
        model_routing_provider: IModelRoutingProvider | None = None,
        env: dict | None = None,
        settings: Any | None = None,
    ):
        self._cost_tracker = cost_tracker
        self._llm_client = llm_client
        self._database = database
        self._chroma_factory = chroma_factory
        self._ragas_factory = ragas_factory
        self._model_routing_provider = model_routing_provider
        self._env = env
        self._settings = settings

    @property
    def cost_tracker(self) -> ICostTracker:
        assert self._cost_tracker is not None
        return self._cost_tracker

    @property
    def llm_client(self) -> ILLMClient:
        assert self._llm_client is not None
        return self._llm_client

    @property
    def database(self) -> IDatabase:
        assert self._database is not None
        return self._database

    @property
    def chroma_factory(self) -> IChromaClientFactory:
        assert self._chroma_factory is not None
        return self._chroma_factory

    @property
    def ragas_factory(self) -> IRagasFactory:
        assert self._ragas_factory is not None
        return self._ragas_factory

    @property
    def model_routing_provider(self) -> IModelRoutingProvider:
        assert self._model_routing_provider is not None
        return self._model_routing_provider

    def get_model_config(self, role: str) -> Any:
        """Return the configured model for a workflow role."""
        return self.model_routing_provider.get_config(role)

    async def call_model(self, role: str, messages: list[dict], **overrides: Any) -> str | dict:
        """Call a configured role while keeping model parameters in one place."""
        config = self.get_model_config(role)
        return await self.llm_client.call(
            model_id=overrides.pop("model_id", config.model_id),
            messages=messages,
            max_tokens=overrides.pop("max_tokens", config.max_tokens),
            task=overrides.pop("task", config.task),
            reasoning_effort=overrides.pop("reasoning_effort", config.reasoning_effort),
            temperature=overrides.pop("temperature", config.temperature),
            response_format=overrides.pop("response_format", config.response_format),
            **overrides,
        )

    def build_ragas_llm(self) -> Any:
        """Create the RAGAS judge from the same role routing as workflow nodes."""
        from src.evaluator.ragas_setup import build_ragas_llm

        return build_ragas_llm(
            self.get_model_config("ragas_judge"),
            env=self.env,
            cost_tracker=self._cost_tracker,
        )

    def build_ragas_embeddings(self) -> Any:
        """Create RAGAS embeddings from the configured embedding role."""
        from src.evaluator.ragas_setup import build_ragas_embeddings

        return build_ragas_embeddings(self.get_model_config("ragas_embedding_model"), env=self.env)

    def build_ragas_metrics(self, metric_names: list[str]) -> list:
        from src.evaluator.ragas_setup import build_ragas_metrics

        return build_ragas_metrics(metric_names)

    @property
    def env(self) -> dict | None:
        return self._env

    @property
    def settings(self) -> Any | None:
        return self._settings
