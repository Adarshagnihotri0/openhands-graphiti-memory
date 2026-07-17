"""Core memory service for Graphiti integration."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from graphiti_memory.client.graphiti_client import GraphitiClient
from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.exceptions import (
    DuplicateMemoryError,
    MemoryNotFoundError,
    MemoryStorageError,
)
from graphiti_memory.models import (
    ArchitectureMemory,
    BugFixMemory,
    ConfidenceLevel,
    ConventionMemory,
    DecisionMemory,
    ImplementationMemory,
    MemoryBase,
    MemoryQuery,
    MemoryType,
    MemoryUpdate,
    RelationshipMemory,
    SearchResult,
)
from graphiti_memory.service.memory_scorer import MemoryScorer
from graphiti_memory.utils.logging import MemoryLogger


class MemoryService:
    """
    Core service for managing durable project memory.

    Responsibilities:
    - Store and retrieve memories
    - Intelligent deduplication
    - Scoped memory by repository/branch/service/module
    - Automatic memory lifecycle management
    """

    def __init__(
        self,
        config: GraphitiConfig,
        client: GraphitiClient,
        scorer: MemoryScorer,
        logger: MemoryLogger,
    ) -> None:
        self.config = config
        self.client = client
        self.scorer = scorer
        self.logger = logger

        # In-memory cache for frequently accessed memories
        self._cache: dict[UUID, MemoryBase] = {}
        self._cache_timestamps: dict[UUID, datetime] = {}

    async def store_memory(
        self,
        memory: MemoryBase,
        check_duplicates: bool = True,
    ) -> UUID:
        """
        Store a memory in the knowledge graph.

        Args:
            memory: Memory to store
            check_duplicates: Whether to check for similar memories first

        Returns:
            UUID of stored memory
        """
        with self.logger.log_operation("store", memory.uuid, {"type": memory.memory_type}):
            # Check for duplicates if enabled
            if check_duplicates and self.config.auto_update_similar:
                similar = await self._find_similar_memory(memory)
                if similar:
                    # Update existing instead of creating duplicate
                    updated = await self._update_existing_memory(
                        similar, memory, similarity_score=similar[1]
                    )
                    return updated

            # Store in Graphiti
            try:
                episode = await self.client.add_episode(
                    name=memory.title,
                    episode_body=memory.to_episode_content(),
                    source="text",
                    source_description=f"{memory.memory_type.value}:{memory.source or 'unknown'}",
                    reference_time=memory.created_at,
                    group_id=self._get_group_id(memory),
                )

                # Cache the memory
                self._cache[memory.uuid] = memory
                self._cache_timestamps[memory.uuid] = datetime.utcnow()

                self.logger.log_memory_created(
                    memory.uuid,
                    memory.memory_type.value,
                    memory.title,
                    memory.confidence,
                )

                return memory.uuid

            except Exception as e:
                self.logger.log_graphiti_failure(e, "store_memory")
                if not self.config.fail_silently:
                    raise MemoryStorageError(f"Failed to store memory: {e}", {"memory_uuid": str(memory.uuid)})
                return memory.uuid

    async def retrieve_memory(self, uuid: UUID) -> MemoryBase | None:
        """
        Retrieve a memory by UUID.

        Args:
            uuid: Memory UUID

        Returns:
            Memory if found, None otherwise
        """
        with self.logger.log_operation("retrieve", uuid):
            # Check cache first
            if uuid in self._cache:
                if self._is_cache_valid(uuid):
                    return self._cache[uuid]

            try:
                # Query from Graphiti
                node = await self.client.get_entity_node(uuid)
                if not node:
                    return None

                # Convert node to memory
                memory = self._node_to_memory(node)

                # Update cache
                self._cache[uuid] = memory
                self._cache_timestamps[uuid] = datetime.utcnow()

                self.logger.log_memory_retrieved(
                    uuid, memory.confidence, memory.title, "graph_lookup"
                )

                return memory

            except Exception as e:
                self.logger.log_graphiti_failure(e, "retrieve_memory")
                return None

    async def search_memories(self, query: MemoryQuery) -> list[SearchResult]:
        """
        Search for relevant memories.

        Args:
            query: Search query with filters

        Returns:
            List of search results ranked by relevance
        """
        with self.logger.log_operation("search", metadata={"query": query.query_text[:50]}):
            try:
                # Build search query
                group_ids = self._get_group_ids(query)

                # Perform semantic search
                start_time = datetime.utcnow()
                nodes = await self.client.search_nodes(
                    query=query.query_text,
                    group_ids=group_ids,
                    limit=query.limit * 2,  # Get extra for filtering
                )
                latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Convert nodes to search results
                results = []
                for node, score in nodes:
                    memory = self._node_to_memory(node)

                    # Apply filters
                    if not self._matches_filters(memory, query):
                        continue

                    # Adjust score based on confidence and recency
                    adjusted_score = self._adjust_score(
                        score, memory, query.semantic_weight, query.graph_weight
                    )

                    if adjusted_score >= query.min_confidence:
                        results.append(
                            SearchResult(
                                memory=memory,
                                score=adjusted_score,
                                retrieval_method="semantic_search",
                            )
                        )

                    if len(results) >= query.limit:
                        break

                self.logger.log_search_query(
                    query.query_text, len(results), latency_ms
                )

                return results

            except Exception as e:
                self.logger.log_graphiti_failure(e, "search_memories")
                return []

    async def update_memory(self, update: MemoryUpdate) -> MemoryBase | None:
        """
        Update an existing memory.

        Args:
            update: Memory update specification

        Returns:
            Updated memory if found
        """
        with self.logger.log_operation("update", update.uuid):
            # Retrieve existing memory
            existing = await self.retrieve_memory(update.uuid)
            if not existing:
                raise MemoryNotFoundError(str(update.uuid))

            # Apply updates
            if update.title is not None:
                existing.title = update.title
            if update.content is not None:
                existing.content = update.content
            if update.confidence is not None:
                existing.confidence = update.confidence
            elif update.increment_confidence:
                # Increment confidence (max 1.0)
                existing.confidence = min(existing.confidence + 0.05, 1.0)
            if update.tags is not None:
                existing.tags = update.tags
            if update.metadata is not None:
                existing.metadata.update(update.metadata)

            existing.updated_at = datetime.utcnow()

            # Store updated memory
            await self.store_memory(existing, check_duplicates=False)

            self.logger.log_memory_updated(
                update.uuid,
                [f for f in ["title", "content", "confidence", "tags", "metadata"] if getattr(update, f) is not None],
            )

            return existing

    async def delete_memory(self, uuid: UUID) -> bool:
        """
        Delete a memory.

        Args:
            uuid: Memory UUID

        Returns:
            True if deleted successfully
        """
        with self.logger.log_operation("delete", uuid):
            try:
                # Remove from Graphiti
                # Note: We delete the episode, which cascades to entities/edges
                await self.client.delete_episode(uuid)

                # Remove from cache
                self._cache.pop(uuid, None)
                self._cache_timestamps.pop(uuid, None)

                return True

            except Exception as e:
                self.logger.log_graphiti_failure(e, "delete_memory")
                return False

    async def get_related_memories(
        self,
        uuid: UUID,
        max_depth: int = 2,
        limit: int = 10,
    ) -> list[tuple[MemoryBase, list[str]]]:
        """
        Get memories related through graph relationships.

        Args:
            uuid: Starting memory UUID
            max_depth: Maximum graph traversal depth
            limit: Maximum results

        Returns:
            List of (memory, relationship_path) tuples
        """
        # Implementation would use Graphiti's graph traversal APIs
        # This is a simplified version
        results = []
        # TODO: Implement graph traversal once we have the full Graphiti API
        return results

    # Convenience methods for specific memory types

    async def remember_architecture(
        self,
        title: str,
        content: str,
        component_type: str,
        dependencies: list[str] | None = None,
        interfaces: list[str] | None = None,
        responsibilities: list[str] | None = None,
        repository: str | None = None,
        module: str | None = None,
        service: str | None = None,
    ) -> UUID:
        """Store architecture knowledge."""
        memory = ArchitectureMemory(
            title=title,
            content=content,
            component_type=component_type,
            dependencies=dependencies or [],
            interfaces=interfaces or [],
            responsibilities=responsibilities or [],
            repository=repository or self.config.repository_scope,
            module=module,
            service=service,
        )
        return await self.store_memory(memory)

    async def remember_decision(
        self,
        title: str,
        decision_type: str,
        rationale: str,
        content: str,
        alternatives_considered: list[str] | None = None,
        trade_offs: str | None = None,
        repository: str | None = None,
    ) -> UUID:
        """Store design decision."""
        memory = DecisionMemory(
            title=title,
            content=content,
            decision_type=decision_type,
            rationale=rationale,
            alternatives_considered=alternatives_considered or [],
            trade_offs=trade_offs,
            repository=repository or self.config.repository_scope,
        )
        return await self.store_memory(memory)

    async def remember_bug_fix(
        self,
        title: str,
        bug_type: str,
        root_cause: str,
        solution: str,
        symptoms: list[str] | None = None,
        prevention: str | None = None,
        module: str | None = None,
    ) -> UUID:
        """Store bug fix discovery."""
        memory = BugFixMemory(
            title=title,
            content=f"Bug: {root_cause}\nSolution: {solution}",
            bug_type=bug_type,
            root_cause=root_cause,
            solution=solution,
            symptoms=symptoms or [],
            prevention=prevention,
            module=module,
            repository=self.config.repository_scope,
        )
        return await self.store_memory(memory)

    async def remember_convention(
        self,
        title: str,
        convention_type: str,
        rule: str,
        rationale: str,
        examples: list[str] | None = None,
        anti_patterns: list[str] | None = None,
        repository: str | None = None,
    ) -> UUID:
        """Store coding convention."""
        memory = ConventionMemory(
            title=title,
            content=rule,
            convention_type=convention_type,
            rule=rule,
            rationale=rationale,
            examples=examples or [],
            anti_patterns=anti_patterns or [],
            repository=repository or self.config.repository_scope,
        )
        return await self.store_memory(memory)

    async def remember_relationship(
        self,
        title: str,
        source_entity: str,
        target_entity: str,
        relation_type: str,
        properties: dict[str, Any] | None = None,
        module: str | None = None,
    ) -> UUID:
        """Store entity relationship."""
        from graphiti_memory.models import RelationType

        memory = RelationshipMemory(
            title=title,
            content=f"{source_entity} {relation_type} {target_entity}",
            source_entity=source_entity,
            target_entity=target_entity,
            relation_type=RelationType(relation_type),
            properties=properties or {},
            module=module,
            repository=self.config.repository_scope,
        )
        return await self.store_memory(memory)

    # Private helper methods

    async def _find_similar_memory(self, memory: MemoryBase) -> tuple[MemoryBase, float] | None:
        """Find similar existing memory."""
        # Search for similar memories
        query = MemoryQuery(
            query_text=f"{memory.title} {memory.content}",
            repositories=[memory.repository],
            memory_types=[memory.memory_type],
            limit=5,
            min_confidence=0.5,
        )

        results = await self.search_memories(query)

        # Check similarity
        for result in results:
            similarity = self.scorer.calculate_similarity(memory, result.memory)
            if similarity >= 0.75:  # High similarity threshold
                return (result.memory, similarity)

        return None

    async def _update_existing_memory(
        self,
        existing: tuple[MemoryBase, float],
        new_memory: MemoryBase,
        similarity_score: float,
    ) -> UUID:
        """Update existing memory with new information."""
        existing_memory = existing[0]

        # Create update
        update = MemoryUpdate(
            uuid=existing_memory.uuid,
            content=self._merge_content(existing_memory.content, new_memory.content),
            tags=list(set(existing_memory.tags + new_memory.tags)),
            increment_confidence=True,
        )

        return (await self.update_memory(update)).uuid

    def _merge_content(self, existing: str, new: str) -> str:
        """Merge existing and new content intelligently."""
        # Simple merge: append new content if not duplicate
        if new not in existing:
            return f"{existing}\n\n[Updated]\n{new}"
        return existing

    def _node_to_memory(self, node: Any) -> MemoryBase:
        """Convert Graphiti node to memory object."""
        # This would parse the node data and reconstruct the appropriate memory type
        # Simplified implementation
        return ImplementationMemory(
            uuid=UUID(node.uuid) if isinstance(node.uuid, str) else node.uuid,
            title=node.name or "Untitled",
            content=node.summary or "",
            repository=self.config.repository_scope,
            created_at=datetime.fromisoformat(node.created_at) if isinstance(node.created_at, str) else node.created_at,
        )

    def _get_group_id(self, memory: MemoryBase) -> str:
        """Get group ID for a memory."""
        return f"{memory.repository}_{memory.branch}_{self.config.group_id}"

    def _get_group_ids(self, query: MemoryQuery) -> list[str]:
        """Get group IDs for query."""
        repositories = query.repositories or [self.config.repository_scope]
        branches = [self.config.branch_scope]  # Could be parameterized
        return [f"{repo}_{branch}_{self.config.group_id}" for repo in repositories for branch in branches]

    def _matches_filters(self, memory: MemoryBase, query: MemoryQuery) -> bool:
        """Check if memory matches query filters."""
        if query.memory_types and memory.memory_type not in query.memory_types:
            return False
        if query.repositories and memory.repository not in query.repositories:
            return False
        if query.modules and memory.module not in query.modules:
            return False
        if query.services and memory.service not in query.services:
            return False
        if query.min_confidence and memory.confidence < query.min_confidence:
            return False
        if query.time_range_days:
            cutoff = datetime.utcnow() - timedelta(days=query.time_range_days)
            if memory.created_at < cutoff:
                return False
        return True

    def _adjust_score(
        self,
        base_score: float,
        memory: MemoryBase,
        semantic_weight: float,
        graph_weight: float,
    ) -> float:
        """Adjust search score based on memory properties."""
        # Start with base semantic score
        score = base_score * semantic_weight

        # Add graph-based score component
        graph_score = self.scorer.calculate_memory_importance(memory)
        score += graph_score * graph_weight

        # Boost by recency
        days_old = (datetime.utcnow() - memory.created_at).days
        recency_boost = max(0, 1.0 - (days_old / 365))  # Decay over 1 year
        score *= (1.0 + recency_boost * 0.2)

        return min(score, 1.0)

    def _is_cache_valid(self, uuid: UUID) -> bool:
        """Check if cached memory is still valid."""
        if uuid not in self._cache_timestamps:
            return False
        age = (datetime.utcnow() - self._cache_timestamps[uuid]).total_seconds()
        return age < self.config.cache_ttl_seconds
