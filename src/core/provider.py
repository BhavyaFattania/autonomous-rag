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
    IEmbeddingService,
    ILLMClient,
    IModelRoutingProvider,
    IRagasFactory,
    IReranker,
)


class Provider:
    """Dependency injection container holding all external service implementations."""

    def __init__(
        self,
        cost_tracker: ICostTracker | None = None,
        llm_client: ILLMClient | None = None,
        embedding_service: IEmbeddingService | None = None,
        reranker: IReranker | None = None,
        database: IDatabase | None = None,
        chroma_factory: IChromaClientFactory | None = None,
        ragas_factory: IRagasFactory | None = None,
        model_routing_provider: IModelRoutingProvider | None = None,
        env: dict | None = None,
        settings: Any | None = None,
    ):
        self._cost_tracker = cost_tracker
        self._llm_client = llm_client
        self._embedding_service = embedding_service
        self._reranker = reranker
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
    def embedding_service(self) -> IEmbeddingService:
        assert self._embedding_service is not None
        return self._embedding_service

    @property
    def reranker(self) -> IReranker:
        assert self._reranker is not None
        return self._reranker

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

    @property
    def env(self) -> dict | None:
        return self._env

    @property
    def settings(self) -> Any | None:
        return self._settings
