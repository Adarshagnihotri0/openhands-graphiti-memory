"""Intelligent scoring to determine what's worth remembering."""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.models import (
    ArchitectureMemory,
    BugFixMemory,
    ConfidenceLevel,
    ConventionMemory,
    DecisionMemory,
    ImplementationMemory,
    MemoryBase,
    MemoryType,
    RelationshipMemory,
)
from graphiti_memory.utils.logging import MemoryLogger


class MemoryScorer:
    """
    Determines what's worth remembering and assigns confidence scores.
    Uses heuristics and patterns to identify durable knowledge.
    """

    def __init__(self, config: GraphitiConfig, logger: MemoryLogger) -> None:
        self.config = config
        self.logger = logger

        # Patterns indicating durable knowledge
        self.durable_patterns = [
            r"(architecture|design|pattern|convention|standard|practice)",
            r"(depends on|uses|imports|requires|connects to)",
            r"(decision|chose|selected|picked|rationale)",
            r"(bug|fix|issue|problem|solution|root cause)",
            r"(important|critical|must|should|always|never)",
            r"(remember|note|warning|caution|gotcha)",
            r"(pattern|anti-pattern|best practice)",
            r"(lesson learned|takeaway|discovered)",
        ]

        # Patterns indicating temporary/conversational content
        self.transient_patterns = [
            r"^(hi|hello|hey|good morning|good afternoon)",
            r"^(thanks|thank you|please|sorry)",
            r"^(can you|could you|would you|will you)",
            r"^(what is|how do|why does|when should)",
            r"(stack trace|exception trace|error message)",
            r"^(test|testing|debugging|trying)",
        ]

    def should_remember(
        self,
        content: str,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, float, str | None]:
        """
        Determine if content is worth remembering.

        Returns:
            Tuple of (should_remember, confidence, memory_type)
        """
        content_lower = content.lower()

        # Check if content matches transient patterns
        for pattern in self.transient_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return False, 0.0, None

        # Count durable pattern matches
        durable_score = 0.0
        matched_types = []

        for pattern in self.durable_patterns:
            match = re.search(pattern, content_lower, re.IGNORECASE)
            if match:
                durable_score += 0.15
                matched_types.append(match.group(1))

        # Adjust score based on content length and structure
        if len(content) < 20:
            durable_score *= 0.5  # Too short
        elif len(content) > 200:
            durable_score *= 1.2  # Detailed content

        # Bonus for structured content
        if any(marker in content for marker in ["```", ":", "-", "1.", "*"]):
            durable_score *= 1.1

        # Context-based adjustments
        if context:
            if context.get("is_verification"):
                durable_score *= 0.5  # Less valuable if just verification
            if context.get("is_exploration"):
                durable_score *= 0.7  # Less certain during exploration
            if context.get("is_implemented") or context.get("is_confirmed"):
                durable_score *= 1.3  # More valuable if proven

        # Cap at 1.0
        confidence = min(durable_score, 1.0)

        # Determine memory type from matched patterns
        memory_type = self._infer_memory_type(content, matched_types)

        # Make final decision
        should_remember = confidence >= self.config.min_confidence_to_store

        return should_remember, confidence, memory_type

    def _infer_memory_type(self, content: str, matched_types: list[str]) -> str | None:
        """Infer memory type from content and matched patterns."""
        content_lower = content.lower()

        # Priority order for type detection
        if any(
            word in content_lower
            for word in ["architecture", "component", "service", "module", "system"]
        ):
            return MemoryType.ARCHITECTURE.value

        if any(word in content_lower for word in ["decision", "chose", "selected", "rationale"]):
            return MemoryType.DECISION.value

        if any(
            word in content_lower for word in ["bug", "fix", "issue", "error", "solution"]
        ):
            return MemoryType.BUG_FIX.value

        if any(
            word in content_lower
            for word in ["convention", "pattern", "practice", "standard", "rule"]
        ):
            return MemoryType.CONVENTION.value

        if any(
            word in content_lower
            for word in ["depends", "uses", "imports", "connects", "relates"]
        ):
            return MemoryType.RELATIONSHIP.value

        if any(
            word in content_lower
            for word in ["implementation", "feature", "function", "method", "note"]
        ):
            return MemoryType.IMPLEMENTATION.value

        return None

    def calculate_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Convert numerical confidence to confidence level."""
        if confidence >= 0.95:
            return ConfidenceLevel.VERIFIED
        elif confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.70:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def calculate_similarity(
        self,
        memory1: MemoryBase,
        memory2: MemoryBase,
    ) -> float:
        """Calculate similarity between two memories."""
        # Title similarity
        title_sim = self._text_similarity(memory1.title, memory2.title)

        # Content similarity
        content_sim = self._text_similarity(memory1.content, memory2.content)

        # Type match
        type_match = 1.0 if memory1.memory_type == memory2.memory_type else 0.5

        # Scope overlap
        scope_sim = self._scope_similarity(memory1, memory2)

        # Weighted combination
        similarity = (title_sim * 0.3 + content_sim * 0.4 + type_match * 0.2 + scope_sim * 0.1)

        return min(similarity, 1.0)

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts."""
        # Normalize and tokenize
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Remove common stopwords
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being"}
        words1 -= stopwords
        words2 -= stopwords

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _scope_similarity(self, memory1: MemoryBase, memory2: MemoryBase) -> float:
        """Calculate scope similarity between two memories."""
        score = 0.0

        if memory1.repository == memory2.repository:
            score += 0.5
        if memory1.branch == memory2.branch:
            score += 0.2
        if memory1.module and memory2.module and memory1.module == memory2.module:
            score += 0.2
        if memory1.service and memory2.service and memory1.service == memory2.service:
            score += 0.1

        return min(score, 1.0)

    def calculate_memory_importance(self, memory: MemoryBase) -> float:
        """Calculate overall importance score for a memory."""
        # Base importance from confidence
        importance = memory.confidence * 0.4

        # Boost for verified confidence level
        if memory.confidence_level == ConfidenceLevel.VERIFIED:
            importance += 0.2
        elif memory.confidence_level == ConfidenceLevel.HIGH:
            importance += 0.1

        # Boost for certain memory types
        type_boosts = {
            MemoryType.ARCHITECTURE: 0.15,
            MemoryType.DECISION: 0.12,
            MemoryType.BUG_FIX: 0.10,
            MemoryType.CONVENTION: 0.08,
            MemoryType.RELATIONSHIP: 0.05,
            MemoryType.IMPLEMENTATION: 0.03,
        }
        importance += type_boosts.get(memory.memory_type, 0.0)

        # Boost for rich metadata
        if memory.tags:
            importance += min(len(memory.tags) * 0.01, 0.05)
        if memory.metadata:
            importance += min(len(memory.metadata) * 0.005, 0.05)

        return min(importance, 1.0)

    def should_update_existing(
        self,
        existing_memory: MemoryBase,
        new_content: str,
        similarity_score: float,
    ) -> bool:
        """Determine if existing memory should be updated."""
        # If very similar, prefer update over duplicate
        if similarity_score >= 0.8:
            return True

        # If moderately similar but new content has higher confidence
        if similarity_score >= 0.6:
            _, new_confidence, _ = self.should_remember(new_content)
            if new_confidence > existing_memory.confidence:
                return True

        return False
