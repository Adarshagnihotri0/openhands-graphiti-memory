"""Graphiti client wrapper with connection pooling and error handling."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncIterator
from uuid import UUID

from graphiti_core import Graphiti
from graphiti_core.edges import EntityEdge
from graphiti_core.llm_client import OpenAIClient
from graphiti_core.nodes import EntityNode, EpisodicNode
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.exceptions import (
    ConnectionError,
    GraphOperationError,
    TimeoutError,
)
from graphiti_memory.utils.logging import MemoryLogger


class GraphitiClient:
    """
    Graphiti client wrapper with:
    - Connection pooling
    - Automatic retry with exponential backoff
    - Timeout handling
    - Graceful error handling
    """

    def __init__(self, config: GraphitiConfig, logger: MemoryLogger) -> None:
        self.config = config
        self.logger = logger
        self._graphiti: Graphiti | None = None
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize Graphiti connection."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            try:
                # Configure LLM client
                llm_client = self._create_llm_client()

                # Create Graphiti instance
                self._graphiti = Graphiti(
                    uri=self.config.database_uri,
                    user=self.config.database_user,
                    password=self.config.database_password,
                    llm_client=llm_client,
                )

                # Initialize graph indices
                await self._graphiti.build_indices_and_constraints()
                self._initialized = True

                self.logger.logger.info(
                    "Graphiti client initialized",
                    database=self.config.database_provider,
                    group_id=self.config.get_scoped_group_id(),
                )

            except Exception as e:
                self.logger.log_graphiti_failure(e, "initialization")
                if not self.config.fail_silently:
                    raise ConnectionError(f"Failed to initialize Graphiti: {e}", {"error": str(e)})
                self.logger.log_fallback_activated(f"Initialization failed: {e}")

    async def close(self) -> None:
        """Close Graphiti connection."""
        if self._graphiti:
            await self._graphiti.close()
            self._graphiti = None
            self._initialized = False

    @asynccontextmanager
    async def get_client(self) -> AsyncIterator[Graphiti]:
        """Get Graphiti client with automatic retry and error handling."""
        if not self._initialized:
            await self.initialize()

        if not self._graphiti:
            raise ConnectionError("Graphiti client not initialized")

        try:
            yield self._graphiti
        except asyncio.TimeoutError as e:
            raise TimeoutError("graph_operation", self.config.timeout_seconds)
        except Exception as e:
            if not self.config.fail_silently:
                raise GraphOperationError(f"Graph operation failed: {e}", {"error": str(e)})
            self.logger.log_graphiti_failure(e, "operation")
            raise

    async def with_retry(self, coro: Any, operation: str) -> Any:
        """Execute operation with retry logic."""
        retryer = AsyncRetrying(
            stop=stop_after_attempt(self.config.max_retries),
            wait=wait_exponential(
                multiplier=self.config.retry_delay,
                min=0.5,
                max=10.0,
            ),
            retry=retry_if_exception_type((ConnectionError, GraphOperationError)),
            reraise=True,
        )

        async for attempt in retryer:
            with attempt:
                try:
                    async with asyncio.timeout(self.config.timeout_seconds):
                        return await coro
                except asyncio.TimeoutError:
                    raise TimeoutError(operation, self.config.timeout_seconds)

    def _create_llm_client(self) -> OpenAIClient:
        """Create LLM client based on configuration."""
        # Use OpenAI client by default (supports other providers via API)
        from graphiti_core.llm_client import OpenAIClient
        from graphiti_core.llm_client.config import LLMConfig

        config = LLMConfig(
            api_key=self.config.llm_api_key or "",
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
            base_url=self.config.llm_base_url,
        )

        return OpenAIClient(config=config)

    async def add_episode(
        self,
        name: str,
        episode_body: str,
        source: str = "text",
        source_description: str = "",
        reference_time: datetime | None = None,
        group_id: str | None = None,
        previous_episode_uuids: list[UUID] | None = None,
    ) -> EpisodicNode:
        """Add an episode to the knowledge graph."""
        async with self.get_client() as client:
            episode = await self.with_retry(
                client.add_episode(
                    name=name,
                    episode_body=episode_body,
                    source_description=source_description,
                    reference_time=reference_time or datetime.utcnow(),
                    source=source,
                    group_id=group_id or self.config.get_scoped_group_id(),
                    previous_episode_uuids=previous_episode_uuids,
                ),
                "add_episode",
            )
            return episode

    async def search_nodes(
        self,
        query: str,
        group_ids: list[str] | None = None,
        limit: int = 10,
    ) -> list[tuple[EntityNode, float]]:
        """Search for entity nodes."""
        async with self.get_client() as client:
            results = await self.with_retry(
                client.search(
                    query=query,
                    group_ids=group_ids or [self.config.get_scoped_group_id()],
                    num_results=limit,
                ),
                "search_nodes",
            )
            return results

    async def get_entity_node(self, uuid: UUID) -> EntityNode | None:
        """Get entity node by UUID."""
        async with self.get_client() as client:
            node = await self.with_retry(
                client.get_entity_node(uuid=uuid),
                "get_entity_node",
            )
            return node

    async def get_entity_edge(self, uuid: UUID) -> EntityEdge | None:
        """Get entity edge by UUID."""
        async with self.get_client() as client:
            edge = await self.with_retry(
                client.get_entity_edge(uuid=uuid),
                "get_entity_edge",
            )
            return edge

    async def delete_episode(self, episode_uuid: UUID) -> None:
        """Delete an episode."""
        async with self.get_client() as client:
            await self.with_retry(
                client.delete_episode(episode_uuid),
                "delete_episode",
            )

    async def clear_graph(self, group_ids: list[str] | None = None) -> None:
        """Clear graph data."""
        async with self.get_client() as client:
            await self.with_retry(
                client.clear(group_ids=group_ids or [self.config.get_scoped_group_id()]),
                "clear_graph",
            )

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._initialized and self._graphiti is not None
