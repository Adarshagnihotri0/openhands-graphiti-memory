"""
Context Builder - Merges Graphiti Memory + Code Index into unified context.

This is the critical component that:
1. Queries both memory systems in parallel
2. Merges and deduplicates results
3. Ranks by task relevance
4. Selects within token budget
5. Formats as clean, concise context

This prevents context flooding and ensures optimal prompt injection.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from dataclasses import dataclass

from graphiti_memory.config.settings import GraphitiConfig


@dataclass
class ContextSource:
    """Unified representation of context from any source."""
    content: str
    source: str  # "graphiti" or "code_index"
    source_type: str  # Memory type or symbol type
    confidence: float
    relevance_score: float
    metadata: dict[str, Any]


@dataclass
class TokenBudget:
    """Token budget management."""
    max_tokens: int
    current_tokens: int = 0
    
    def can_add(self, estimated_tokens: int) -> bool:
        return self.current_tokens + estimated_tokens <= self.max_tokens
    
    def add(self, tokens: int) -> None:
        self.current_tokens += tokens


class ContextBuilder:
    """
    Merges, deduplicates, ranks, and summarizes context from multiple sources.
    
    Usage:
        builder = ContextBuilder(config)
        context = await builder.build_context(
            task="Fix authentication race condition",
            max_tokens=2000
        )
        # Inject context into OpenHands prompt
    """
    
    def __init__(self, config: GraphitiConfig) -> None:
        self.config = config
        self.max_memories = 5
        self.max_code_symbols = 10
        self.default_token_budget = 2000
        
    async def build_context(
        self,
        task: str,
        max_tokens: int | None = None,
        graphiti_results: list | None = None,
        code_index_results: list | None = None
    ) -> str:
        """
        Build unified context from Graphiti + Code Index.
        
        Args:
            task: Task description
            max_tokens: Maximum tokens to inject (default 2000)
            graphiti_results: Pre-fetched Graphiti results (optional)
            code_index_results: Pre-fetched Code Index results (optional)
            
        Returns:
            Formatted context string for injection
        """
        budget = TokenBudget(max_tokens or self.default_token_budget)
        
        # Query both sources if not provided
        if graphiti_results is None or code_index_results is None:
            graphiti_results, code_index_results = await self._query_sources(task)
        
        # Merge with source attribution
        merged = self._merge_sources(graphiti_results, code_index_results)
        
        # Deduplicate
        deduped = self._deduplicate(merged)
        
        # Rank by task relevance
        ranked = self._rank_by_relevance(deduped, task)
        
        # Select within token budget
        selected = self._select_within_budget(ranked, budget)
        
        # Format as clean context
        return self._format_context(selected, task)
    
    async def _query_sources(self, task: str) -> tuple[list, list]:
        """
        Query both Graphiti and Code Index in parallel.
        """
        # Note: Code Index MCP is hypothetical
        # In production, this would call the actual Code Index MCP
        
        # For now, we'll query Graphiti and return empty for code index
        # TODO: Replace with actual Code Index MCP integration
        
        graphiti_results = []  # Would query actual Graphiti
        code_index_results = []  # Would query Code Index MCP
        
        return graphiti_results, code_index_results
    
    def _merge_sources(
        self,
        graphiti_results: list,
        code_index_results: list
    ) -> list[ContextSource]:
        """
        Merge results with source attribution.
        """
        merged = []
        
        # Add Graphiti memories
        for mem in graphiti_results:
            merged.append(ContextSource(
                content=mem.memory.content,
                source="graphiti",
                source_type=mem.memory.memory_type.value,
                confidence=mem.memory.confidence,
                relevance_score=mem.score,
                metadata={
                    "title": mem.memory.title,
                    "uuid": str(mem.memory.uuid),
                    "module": mem.memory.module,
                    "created_at": mem.memory.created_at.isoformat()
                }
            ))
        
        # Add Code Index symbols (hypothetical structure)
        for sym in code_index_results:
            merged.append(ContextSource(
                content=f"{sym.name} ({sym.type})",
                source="code_index",
                source_type=sym.type,
                confidence=0.7,  # Code index doesn't have confidence
                relevance_score=sym.relevance_score,
                metadata={
                    "file": sym.file_path,
                    "line": sym.line_number,
                    "definition": sym.definition[:100] if hasattr(sym, 'definition') else None
                }
            ))
        
        return merged
    
    def _deduplicate(self, merged: list[ContextSource]) -> list[ContextSource]:
        """
        Remove duplicate or highly similar context items.
        """
        deduped = []
        
        for item in merged:
            # Check if similar to existing
            is_duplicate = False
            
            for existing in deduped:
                # Simple similarity check
                if self._is_similar(item, existing):
                    # Keep higher confidence
                    if item.confidence > existing.confidence:
                        deduped.remove(existing)
                        deduped.append(item)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduped.append(item)
        
        return deduped
    
    def _is_similar(self, item1: ContextSource, item2: ContextSource) -> bool:
        """
        Check if two context items are similar.
        """
        # Simple heuristic - in production would use embeddings
        
        # Check content similarity
        words1 = set(item1.content.lower().split())
        words2 = set(item2.content.lower().split())
        
        if not words1 or not words2:
            return False
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        similarity = intersection / union if union > 0 else 0
        
        return similarity > 0.7
    
    def _rank_by_relevance(
        self,
        items: list[ContextSource],
        task: str
    ) -> list[ContextSource]:
        """
        Rank context items by relevance to the task.
        """
        # Score each item
        for item in items:
            score = self._calculate_relevance_score(item, task)
            item.relevance_score = score
        
        # Sort by relevance score
        items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return items
    
    def _calculate_relevance_score(
        self,
        item: ContextSource,
        task: str
    ) -> float:
        """
        Calculate relevance score for an item.
        
        Factors:
        - Base relevance score
        - Confidence
        - Task keyword overlap
        - Recency (for memories)
        - Source priority
        """
        score = item.relevance_score
        
        # Confidence boost
        score += item.confidence * 0.3
        
        # Task keyword overlap
        task_words = set(task.lower().split())
        content_words = set(item.content.lower().split())
        overlap = len(task_words & content_words) / len(task_words) if task_words else 0
        score += overlap * 0.2
        
        # Source priority (graphiti > code_index)
        if item.source == "graphiti":
            score += 0.1
        
        return min(score, 1.0)
    
    def _select_within_budget(
        self,
        items: list[ContextSource],
        budget: TokenBudget
    ) -> list[ContextSource]:
        """
        Select items within token budget.
        """
        selected = []
        
        for item in items:
            # Estimate tokens (rough: 1 token ≈ 4 chars)
            estimated_tokens = len(item.content) // 4
            
            if budget.can_add(estimated_tokens):
                selected.append(item)
                budget.add(estimated_tokens)
            
            # Enforce hard limits
            graphiti_count = sum(1 for s in selected if s.source == "graphiti")
            code_count = sum(1 for s in selected if s.source == "code_index")
            
            if graphiti_count >= self.max_memories and code_count >= self.max_code_symbols:
                break
        
        return selected
    
    def _format_context(
        self,
        items: list[ContextSource],
        task: str
    ) -> str:
        """
        Format as clean, concise context for injection.
        
        Example output:
        
        Relevant project knowledge:
          • AuthService depends on TokenService (verified)
          • Decision: Use PostgreSQL for ACID (ADR-003)
        
        Relevant code symbols:
          • AuthService (auth/service.py:45)
          • validate_token (auth/token.py:120)
        
        Use this context only if relevant to the current task.
        """
        if not items:
            return ""
        
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("RELEVANT CONTEXT")
        lines.append("=" * 80 + "\n")
        
        # Separate by source
        from_graphiti = [i for i in items if i.source == "graphiti"]
        from_code = [i for i in items if i.source == "code_index"]
        
        # Format Graphiti memories
        if from_graphiti:
            lines.append("Project knowledge:")
            
            for i, item in enumerate(from_graphiti, 1):
                # Truncate content
                content = item.content[:100]
                if len(item.content) > 100:
                    content += "..."
                
                # Add confidence indicator
                confidence_str = "✓" if item.confidence >= 0.9 else ""
                
                lines.append(f"  {i}. {content} {confidence_str}")
                
                # Add metadata
                if item.metadata.get("module"):
                    lines.append(f"     Module: {item.metadata['module']}")
        
        # Format Code Index symbols
        if from_code:
            lines.append("\nRelevant code symbols:")
            
            for i, item in enumerate(from_code, 1):
                lines.append(f"  • {item.content}")
                
                if item.metadata.get("file"):
                    lines.append(f"    Location: {item.metadata['file']}")
                    if item.metadata.get("line"):
                        lines[-1] += f":{item.metadata['line']}"
        
        lines.append("\n" + "=" * 80)
        lines.append("Use this context only if relevant to the current task.")
        lines.append("=" * 80 + "\n")
        
        return "\n".join(lines)
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Rough approximation: 1 token ≈ 4 characters
        """
        return len(text) // 4


# Example usage
"""
async def build_context_for_task(task: str) -> str:
    builder = ContextBuilder(config)
    
    # Query Graphiti via integration hooks
    graphiti_results = await memory_integration.pre_task_hook(task)
    
    # Query Code Index MCP (hypothetical)
    code_results = await code_index_mcp.search_symbols(task, limit=10)
    
    # Build merged context
    context = await builder.build_context(
        task=task,
        graphiti_results=graphiti_results,
        code_index_results=code_results,
        max_tokens=2000
    )
    
    return context

# Inject into OpenHands prompt
prompt = f"{context}\n\nTask: {task}"
"""
