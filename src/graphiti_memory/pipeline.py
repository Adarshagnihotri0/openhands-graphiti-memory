"""Automatic memory pipeline for before-task retrieval and after-task storage."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from graphiti_memory.client.graphiti_client import GraphitiClient
from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.models import MemoryQuery, MemoryType
from graphiti_memory.service.memory_scorer import MemoryScorer
from graphiti_memory.service.memory_service import MemoryService
from graphiti_memory.utils.logging import MemoryLogger


class MemoryPipeline:
    """
    Automatic memory pipeline that:
    1. Retrieves relevant memories before tasks
    2. Stores durable knowledge after tasks

    This is designed to be integrated into OpenHands' task execution flow.
    """

    def __init__(
        self,
        config: GraphitiConfig,
        client: GraphitiClient,
        service: MemoryService,
        scorer: MemoryScorer,
        logger: MemoryLogger,
    ) -> None:
        self.config = config
        self.client = client
        self.service = service
        self.scorer = scorer
        self.logger = logger

    async def before_task(self, task_description: str, context: dict[str, Any] | None = None) -> str:
        """
        Retrieve relevant memories before starting a task.

        Args:
            task_description: Description of the task to be performed
            context: Additional context (repository, module, etc.)

        Returns:
            Formatted memory context to inject into task context
        """
        if not self.client.is_connected:
            await self.client.initialize()

        # Extract scope from context
        repository = context.get("repository", self.config.repository_scope)
        module = context.get("module")
        service = context.get("service")

        # Build query based on task description
        query = MemoryQuery(
            query_text=task_description,
            repositories=[repository],
            modules=[module] if module else None,
            services=[service] if service else None,
            limit=self.config.retrieval_limit,
            min_confidence=self.config.confidence_threshold,
            include_relationships=True,
        )

        # Search for relevant memories
        memories = await self.service.search_memories(query)

        if not memories:
            return ""

        # Format memories for injection
        formatted = self._format_memories_for_context(memories)

        self.logger.logger.info(
            "Retrieved memories before task",
            task_description=task_description[:100],
            memories_count=len(memories),
        )

        return formatted

    async def after_task(
        self,
        task_description: str,
        task_result: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Analyze completed task and store durable knowledge.

        Args:
            task_description: Description of the task
            task_result: Result/outcome of the task
            context: Additional context (repository, module, etc.)
        """
        if not self.client.is_connected:
            await self.client.initialize()

        # Combine task and result for analysis
        full_context = f"{task_description}\n\nResult:\n{task_result}"

        # Determine if we learned something durable
        should_remember, confidence, memory_type = self.scorer.should_remember(
            full_context, context
        )

        if not should_remember:
            self.logger.logger.debug(
                "Task result not deemed worth remembering",
                confidence=confidence,
            )
            return

        # Extract and store knowledge
        await self._extract_and_store(full_context, confidence, memory_type, context)

    async def analyze_and_remember(
        self,
        content: str,
        content_type: str,
        context: dict[str, Any] | None = None,
    ) -> str | None:
        """
        Analyze content and store if it contains durable knowledge.

        This is a more general method that can be called after
        any operation that might produce durable knowledge.

        Args:
            content: Content to analyze
            content_type: Type of content (e.g., "code_review", "bug_fix", "implementation")
            context: Additional context

        Returns:
            UUID of stored memory if created, None otherwise
        """
        if not self.client.is_connected:
            await self.client.initialize()

        # Add content type to context
        enriched_context = (context or {}).copy()
        enriched_context["source"] = content_type

        # Check if worth remembering
        should_remember, confidence, memory_type = self.scorer.should_remember(
            content, enriched_context
        )

        if not should_remember:
            return None

        # Store based on inferred type or explicit type
        return await self._extract_and_store(content, confidence, memory_type, enriched_context)

    async def get_memory_summary(self, repository: str | None = None) -> dict[str, Any]:
        """
        Get summary of stored memories for a repository.

        Args:
            repository: Repository to summarize (uses default if not specified)

        Returns:
            Summary statistics
        """
        repo = repository or self.config.repository_scope

        # Query recent memories
        query = MemoryQuery(
            query_text="",
            repositories=[repo],
            limit=100,
        )

        memories = await self.service.search_memories(query)

        # Calculate statistics
        stats: dict[str, int] = {}
        for result in memories:
            mem_type = result.memory.memory_type.value
            stats[mem_type] = stats.get(mem_type, 0) + 1

        return {
            "repository": repo,
            "total_memories": len(memories),
            "by_type": stats,
            "last_updated": max(
                (m.memory.updated_at for m in memories), default=datetime.utcnow()
            ).isoformat(),
        }

    def _format_memories_for_context(self, memories: list[Any]) -> str:
        """Format memories for injection into task context."""
        if not memories:
            return ""

        sections = []
        sections.append("=== Relevant Project Memory ===")

        # Group by type
        by_type: dict[str, list[Any]] = {}
        for memory in memories:
            mem_type = memory.memory.memory_type.value
            by_type.setdefault(mem_type, []).append(memory)

        # Format each type
        for mem_type, type_memories in by_type.items():
            sections.append(f"\n[{mem_type.upper()}]")
            for memory in type_memories[:3]:  # Limit to top 3 per type
                confidence_indicator = "✓" if memory.memory.confidence >= 0.8 else "○"
                sections.append(f"  {confidence_indicator} {memory.memory.title}")
                # Truncate long content
                content_preview = memory.memory.content[:200]
                if len(memory.memory.content) > 200:
                    content_preview += "..."
                sections.append(f"    {content_preview}")

                # Add scope info if available
                if memory.memory.module:
                    sections.append(f"    Scope: {memory.memory.module}")

        sections.append("\n=== End Memory ===\n")

        return "\n".join(sections)

    async def _extract_and_store(
        self,
        content: str,
        confidence: float,
        memory_type: str | None,
        context: dict[str, Any] | None = None,
    ) -> str | None:
        """Extract structured knowledge and store it."""
        ctx = context or {}

        # Determine which storage method to use based on type
        if memory_type == MemoryType.ARCHITECTURE.value or self._is_architecture_content(content):
            # Extract architecture information
            extracted = self._extract_architecture(content)
            uuid = await self.service.remember_architecture(
                title=extracted["title"],
                content=extracted["content"],
                component_type=extracted.get("component_type", "unknown"),
                dependencies=extracted.get("dependencies"),
                repository=ctx.get("repository", self.config.repository_scope),
                module=ctx.get("module"),
                service=ctx.get("service"),
            )
            return str(uuid)

        elif memory_type == MemoryType.DECISION.value or self._is_decision_content(content):
            extracted = self._extract_decision(content)
            uuid = await self.service.remember_decision(
                title=extracted["title"],
                decision_type=extracted.get("decision_type", "unknown"),
                rationale=extracted.get("rationale", ""),
                content=extracted["content"],
                repository=ctx.get("repository", self.config.repository_scope),
            )
            return str(uuid)

        elif memory_type == MemoryType.BUG_FIX.value or self._is_bug_fix_content(content):
            extracted = self._extract_bug_fix(content)
            uuid = await self.service.remember_bug_fix(
                title=extracted["title"],
                bug_type=extracted.get("bug_type", "unknown"),
                root_cause=extracted.get("root_cause", ""),
                solution=extracted.get("solution", ""),
                module=ctx.get("module"),
            )
            return str(uuid)

        elif memory_type == MemoryType.CONVENTION.value or self._is_convention_content(content):
            extracted = self._extract_convention(content)
            uuid = await self.service.remember_convention(
                title=extracted["title"],
                convention_type=extracted.get("convention_type", "general"),
                rule=extracted.get("rule", ""),
                rationale=extracted.get("rationale", ""),
                repository=ctx.get("repository", self.config.repository_scope),
            )
            return str(uuid)

        # Default: store as implementation memory
        title = self._generate_title(content)
        # Create a basic implementation memory
        from graphiti_memory.models import ImplementationMemory

        memory = ImplementationMemory(
            title=title,
            content=content[:500],  # Limit content length
            feature=ctx.get("feature", ctx.get("task", "unknown")),
            implementation_notes=content[:200],
            repository=ctx.get("repository", self.config.repository_scope),
            confidence=min(confidence, 1.0),
        )

        uuid = await self.service.store_memory(memory)
        return str(uuid)

    def _is_architecture_content(self, content: str) -> bool:
        """Check if content is about architecture."""
        keywords = ["architecture", "component", "service", "module", "depends on", "uses", "connects to"]
        return any(kw in content.lower() for kw in keywords)

    def _is_decision_content(self, content: str) -> bool:
        """Check if content is about a design decision."""
        keywords = ["decision", "chose", "selected", "rationale", "because", "trade-off"]
        return any(kw in content.lower() for kw in keywords)

    def _is_bug_fix_content(self, content: str) -> bool:
        """Check if content is about a bug fix."""
        keywords = ["bug", "fix", "issue", "error", "root cause", "solution", "resolved"]
        return any(kw in content.lower() for kw in keywords)

    def _is_convention_content(self, content: str) -> bool:
        """Check if content is about coding conventions."""
        keywords = ["convention", "pattern", "practice", "standard", "rule", "always", "never"]
        return any(kw in content.lower() for kw in keywords)

    def _extract_architecture(self, content: str) -> dict[str, Any]:
        """Extract architecture information from content."""
        # Simple extraction - in production would use LLM
        lines = content.split("\n")
        title = lines[0][:100] if lines else "Architecture"
        return {
            "title": title,
            "content": content,
            "component_type": "service",  # Would be extracted
            "dependencies": [],  # Would be extracted
        }

    def _extract_decision(self, content: str) -> dict[str, Any]:
        """Extract decision information from content."""
        lines = content.split("\n")
        title = lines[0][:100] if lines else "Design Decision"
        return {
            "title": title,
            "content": content,
            "decision_type": "general",
            "rationale": "See content",
        }

    def _extract_bug_fix(self, content: str) -> dict[str, Any]:
        """Extract bug fix information from content."""
        lines = content.split("\n")
        title = lines[0][:100] if lines else "Bug Fix"
        return {
            "title": title,
            "bug_type": "unknown",
            "root_cause": "",
            "solution": content,
        }

    def _extract_convention(self, content: str) -> dict[str, Any]:
        """Extract convention information from content."""
        lines = content.split("\n")
        title = lines[0][:100] if lines else "Convention"
        return {
            "title": title,
            "convention_type": "general",
            "rule": content[:100],
            "rationale": "",
        }

    def _generate_title(self, content: str) -> str:
        """Generate a title from content."""
        # Take first meaningful line or first 50 chars
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if lines:
            return lines[0][:100]
        return content[:100]


async def integrate_with_openhands(
    config: GraphitiConfig,
    task_description: str,
    task_context: dict[str, Any] | None = None,
) -> tuple[str, MemoryPipeline]:
    """
    Convenience function to integrate memory pipeline with OpenHands.

    Usage:
        memory_context, pipeline = await integrate_with_openhands(
            config,
            "Fix the authentication bug",
            {"repository": "myapp", "module": "auth"}
        )

        # Inject memory_context into OpenHands context

        # After task completion:
        await pipeline.after_task(
            "Fix the authentication bug",
            result,
            context
        )

    Returns:
        Tuple of (memory_context, pipeline)
    """
    # Initialize components
    from graphiti_memory.utils.logging import MemoryLogger

    logger = MemoryLogger(config)
    client = GraphitiClient(config, logger)
    await client.initialize()

    scorer = MemoryScorer(config, logger)
    service = MemoryService(config, client, scorer, logger)
    pipeline = MemoryPipeline(config, client, service, scorer, logger)

    # Get memory context
    memory_context = await pipeline.before_task(task_description, task_context)

    return memory_context, pipeline
