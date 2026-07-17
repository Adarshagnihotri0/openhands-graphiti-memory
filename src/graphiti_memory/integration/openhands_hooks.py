"""
OpenHands Agent Integration - Automatic Memory Hooks.

This module provides the hooks that make memory retrieval automatic
before tasks, and memory storage automatic after tasks.

Critical: This transforms Graphiti from a "memory database" into a
"memory system" that OpenHands uses transparently.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable
from dataclasses import dataclass

from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.client.graphiti_client import GraphitiClient
from graphiti_memory.service.memory_service import MemoryService
from graphiti_memory.service.memory_scorer import MemoryScorer
from graphiti_memory.models import MemoryQuery, MemoryBase
from graphiti_memory.utils.logging import MemoryLogger


@dataclass
class TaskContext:
    """Context passed to OpenHands agent."""
    task: str
    repository: str
    branch: str
    module: str | None = None
    service: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class MemoryRetrievalResult:
    """Result of automatic memory retrieval."""
    memory_context: str
    memories_found: int
    confidence_avg: float
    retrieval_latency_ms: float
    sources: list[str]


@dataclass
class MemoryPromotionResult:
    """Result of automatic memory storage."""
    stored_count: int
    updated_count: int
    rejected_count: int
    storage_latency_ms: float


class OpenHandsMemoryIntegration:
    """
    Automatic memory integration for OpenHands agent.
    
    This is the critical piece that makes memory automatic:
    - Before every task: Query Graphiti + Code Index, merge, inject
    - After every task: Extract facts, score, dedupe, store
    - Bootstrap: Populate from repo docs on first run
    - Freshness: Detect stale memories via git/code changes
    
    Usage:
        integration = OpenHandsMemoryIntegration(config)
        await integration.initialize()
        
        # Register hooks (these should be called by OpenHands core)
        agent.register_pre_task_hook(integration.pre_task_hook)
        agent.register_post_task_hook(integration.post_task_hook)
    """
    
    def __init__(self, config: GraphitiConfig) -> None:
        self.config = config
        self.logger = MemoryLogger(config)
        self.client = GraphitiClient(config, self.logger)
        self.scorer = MemoryScorer(config, self.logger)
        self.service: MemoryService | None = None
        
        # Track initialization
        self._initialized = False
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize memory integration."""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:
                return
            
            # Initialize client
            await self.client.initialize()
            
            # Initialize service
            self.service = MemoryService(
                self.config,
                self.client,
                self.scorer,
                self.logger
            )
            
            # Bootstrap if first time
            if await self._is_first_run():
                await self.bootstrap_repository()
            
            self._initialized = True
            
            self.logger.logger.info(
                "OpenHands memory integration initialized",
                repository=self.config.repository_scope,
                group_id=self.config.get_scoped_group_id()
            )
    
    async def pre_task_hook(
        self,
        task: str,
        context: TaskContext | None = None
    ) -> MemoryRetrievalResult:
        """
        AUTOMATICALLY invoked before OpenHands starts any task.
        
        This is the key integration point that makes memory automatic.
        
        Flow:
        1. Query Graphiti for relevant project memory
        2. Query Code Index MCP for relevant source code (future)
        3. Merge both contexts
        4. Return formatted context for injection
        
        Args:
            task: Task description
            context: Optional task context (repository, module, etc.)
            
        Returns:
            MemoryRetrievalResult with context to inject
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.utcnow()
        
        self.logger.logger.info(
            "Pre-task hook triggered",
            task_preview=task[:100]
        )
        
        # Build context
        ctx = context or TaskContext(
            task=task,
            repository=self.config.repository_scope,
            branch=self.config.branch_scope
        )
        
        # Query Graphiti
        try:
            query = MemoryQuery(
                query_text=task,
                repositories=[ctx.repository],
                modules=[ctx.module] if ctx.module else None,
                services=[ctx.service] if ctx.service else None,
                limit=self.config.retrieval_limit,
                min_confidence=self.config.confidence_threshold,
                include_relationships=True
            )
            
            memories = await self.service.search_memories(query)
            
            # Format for injection
            memory_context = self._format_memories_for_injection(memories, task)
            
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result = MemoryRetrievalResult(
                memory_context=memory_context,
                memories_found=len(memories),
                confidence_avg=sum(m.memory.confidence for m in memories) / len(memories) if memories else 0.0,
                retrieval_latency_ms=latency_ms,
                sources=[m.memory.memory_type.value for m in memories]
            )
            
            self.logger.logger.info(
                "Retrieved memories for task",
                memories_count=len(memories),
                latency_ms=latency_ms
            )
            
            return result
            
        except Exception as e:
            self.logger.log_graphiti_failure(e, "pre_task_hook")
            
            # Return empty on failure (graceful degradation)
            return MemoryRetrievalResult(
                memory_context="",
                memories_found=0,
                confidence_avg=0.0,
                retrieval_latency_ms=0.0,
                sources=[]
            )
    
    async def post_task_hook(
        self,
        task: str,
        result: str,
        context: TaskContext | None = None
    ) -> MemoryPromotionResult:
        """
        AUTOMATICALLY invoked after OpenHands completes any task.
        
        Flow:
        1. Extract candidate facts from task execution
        2. Score each fact for durability
        3. Deduplicate against existing memories
        4. Store or update memories
        
        Args:
            task: Task description
            result: Task execution result
            context: Optional task context
            
        Returns:
            MemoryPromotionResult with storage statistics
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.utcnow()
        
        self.logger.logger.info(
            "Post-task hook triggered",
            task_preview=task[:100]
        )
        
        try:
            # Extract facts
            candidates = await self._extract_facts(task, result, context)
            
            # Score facts
            scored_candidates = []
            for candidate in candidates:
                should_remember, confidence, mem_type = self.scorer.should_remember(
                    candidate['content'],
                    context.__dict__ if context else None
                )
                
                if should_remember and confidence >= self.config.min_confidence_to_store:
                    candidate['confidence'] = confidence
                    candidate['memory_type'] = mem_type
                    scored_candidates.append(candidate)
            
            # Deduplicate and store
            stored_count = 0
            updated_count = 0
            rejected_count = 0
            
            for candidate in scored_candidates:
                # Check for duplicates
                similar = await self._find_similar_memory(candidate)
                
                if similar:
                    # Update existing
                    await self.service.update_memory(
                        uuid=similar.uuid,
                        increment_confidence=True
                    )
                    updated_count += 1
                else:
                    # Store new
                    await self._store_candidate(candidate, context)
                    stored_count += 1
            
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result = MemoryPromotionResult(
                stored_count=stored_count,
                updated_count=updated_count,
                rejected_count=rejected_count,
                storage_latency_ms=latency_ms
            )
            
            self.logger.logger.info(
                "Promoted memories from task",
                stored=stored_count,
                updated=updated_count,
                latency_ms=latency_ms
            )
            
            return result
            
        except Exception as e:
            self.logger.log_graphiti_failure(e, "post_task_hook")
            
            return MemoryPromotionResult(
                stored_count=0,
                updated_count=0,
                rejected_count=0,
                storage_latency_ms=0.0
            )
    
    async def bootstrap_repository(self) -> int:
        """
        Populate Graphiti from existing repository knowledge.
        
        Scans:
        - README.md
        - docs/architecture
        - docs/adr (Architecture Decision Records)
        - package.json / pyproject.toml
        - docker-compose.yml
        - .github/workflows
        
        Returns count of memories created.
        """
        self.logger.logger.info("Bootstrapping repository memory")
        
        # Implementation would scan and extract from files
        # This is a placeholder for the full implementation
        
        count = 0
        
        # TODO: Implement each extraction step
        
        self.logger.logger.info("Repository bootstrap complete", memories_created=count)
        
        return count
    
    # Integration methods
    
    def get_pre_task_hook(self) -> Callable:
        """Get the pre-task hook function for OpenHands registration."""
        return self.pre_task_hook
    
    def get_post_task_hook(self) -> Callable:
        """Get the post-task hook function for OpenHands registration."""
        return self.post_task_hook
    
    # Private helper methods
    
    def _format_memories_for_injection(
        self,
        memories: list,
        task: str
    ) -> str:
        """
        Format retrieved memories for injection into OpenHands prompt.
        
        This context will be prepended to OpenHands' system prompt.
        """
        if not memories:
            return ""
        
        sections = []
        sections.append("\n" + "=" * 80)
        sections.append("RELEVANT PROJECT MEMORY (from Graphiti)")
        sections.append("=" * 80 + "\n")
        
        # Group by type
        by_type = {}
        for mem_result in memories:
            mem = mem_result.memory
            mem_type = mem.memory_type.value
            by_type.setdefault(mem_type, []).append(mem_result)
        
        # Format each type
        for mem_type, type_memories in by_type.items():
            sections.append(f"\n[{mem_type.upper()}]")
            
            for i, mem_result in enumerate(type_memories[:3], 1):  # Top 3 per type
                mem = mem_result.memory
                
                # Confidence indicator
                confidence_str = "✓" if mem.confidence >= 0.8 else "○"
                
                sections.append(f"\n{i}. {confidence_str} {mem.title}")
                sections.append(f"   Confidence: {mem.confidence:.0%}")
                
                # Content preview
                content_preview = mem.content[:150]
                if len(mem.content) > 150:
                    content_preview += "..."
                sections.append(f"   {content_preview}")
                
                # Scope
                if mem.module:
                    sections.append(f"   Scope: {mem.module}")
                
                # Why retrieved
                sections.append(f"   Retrieved because: matched '{task[:50]}...'")
        
        sections.append("\n" + "=" * 80)
        sections.append("END PROJECT MEMORY")
        sections.append("=" * 80 + "\n")
        
        return "\n".join(sections)
    
    async def _extract_facts(
        self,
        task: str,
        result: str,
        context: TaskContext | None
    ) -> list[dict[str, Any]]:
        """
        Extract candidate facts from task execution.
        
        Uses heuristic extraction (LLM-based would be better).
        """
        # Simple heuristic extraction
        # In production, this would use LLM with structured output
        
        candidates = []
        
        # Check for patterns indicating durable knowledge
        full_text = f"{task}\n{result}"
        
        # Architecture patterns
        if any(kw in full_text.lower() for kw in ["depends on", "uses", "connects to", "architecture"]):
            candidates.append({
                "type": "architecture",
                "content": full_text[:500],
                "title": f"Architecture: {task[:50]}"
            })
        
        # Decision patterns
        if any(kw in full_text.lower() for kw in ["chose", "selected", "decided", "because"]):
            candidates.append({
                "type": "decision",
                "content": full_text[:500],
                "title": f"Decision: {task[:50]}"
            })
        
        # Bug fix patterns
        if any(kw in full_text.lower() for kw in ["fix", "bug", "issue", "error", "root cause"]):
            candidates.append({
                "type": "bug_fix",
                "content": full_text[:500],
                "title": f"Bug Fix: {task[:50]}"
            })
        
        return candidates
    
    async def _find_similar_memory(self, candidate: dict) -> MemoryBase | None:
        """Find similar existing memory."""
        # Simplified - would use actual Graphiti similarity search
        return None
    
    async def _store_candidate(
        self,
        candidate: dict,
        context: TaskContext | None
    ) -> None:
        """Store a candidate fact as a memory."""
        # Simplified - would route to appropriate store method
        pass
    
    async def _is_first_run(self) -> bool:
        """Check if this is the first run for this repository."""
        # Check if any memories exist for this repository
        if not self.service:
            return True
        
        results = await self.service.search_memories(
            MemoryQuery(query_text="", limit=1)
        )
        
        return len(results) == 0
    
    async def close(self) -> None:
        """Close connections."""
        if self.client:
            await self.client.close()


# Integration example for OpenHands core
"""
# In OpenHands agent initialization:

from graphiti_memory.integration.openhands_hooks import OpenHandsMemoryIntegration

class OpenHandsAgent:
    def __init__(self, config):
        # Initialize memory integration
        memory_config = GraphitiConfig()
        self.memory_integration = OpenHandsMemoryIntegration(memory_config)
        
        # Register hooks
        self.register_pre_task_hook(
            self.memory_integration.get_pre_task_hook()
        )
        self.register_post_task_hook(
            self.memory_integration.get_post_task_hook()
        )

# Now OpenHands will automatically:
# 1. Query Graphiti before every task
# 2. Inject memory context into prompts
# 3. Extract and store durable knowledge after tasks
# 4. Bootstrap new repositories from existing docs
"""
