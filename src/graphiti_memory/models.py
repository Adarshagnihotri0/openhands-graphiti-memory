"""Data models for Graphiti memory system."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class MemoryType(str, Enum):
    """Types of durable project memory."""

    ARCHITECTURE = "architecture"
    DECISION = "decision"
    BUG_FIX = "bug_fix"
    CONVENTION = "convention"
    RELATIONSHIP = "relationship"
    IMPLEMENTATION = "implementation"


class EntityType(str, Enum):
    """Entity types in the knowledge graph."""

    SERVICE = "Service"
    MODULE = "Module"
    REPOSITORY = "Repository"
    API = "API"
    DATABASE = "Database"
    LIBRARY = "Library"
    PATTERN = "Pattern"
    DECISION = "Decision"
    BUG = "Bug"
    FIX = "Fix"
    CONVENTION = "Convention"
    ARCHITECTURE = "Architecture"


class RelationType(str, Enum):
    """Relationship types between entities."""

    DEPENDS_ON = "DEPENDS_ON"
    USES = "USES"
    IMPLEMENTS = "IMPLEMENTS"
    FIXES = "FIXES"
    FOLLOWS = "FOLLOWS"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    RELATES_TO = "RELATES_TO"
    PART_OF = "PART_OF"
    CONNECTS_TO = "CONNECTS_TO"
    OWNS = "OWNS"


class ConfidenceLevel(str, Enum):
    """Confidence levels for memories."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


class MemoryBase(BaseModel):
    """Base model for all memory types."""

    uuid: UUID = Field(default_factory=uuid4, description="Unique identifier")
    memory_type: MemoryType = Field(description="Type of memory")
    title: str = Field(description="Brief title/summary")
    content: str = Field(description="Detailed memory content")
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence score (0-1)"
    )
    confidence_level: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM, description="Confidence level"
    )

    # Scope metadata
    repository: str = Field(default="default", description="Repository identifier")
    branch: str = Field(default="main", description="Branch identifier")
    module: str | None = Field(default=None, description="Module path")
    service: str | None = Field(default=None, description="Service name")

    # Temporal metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    valid_at: datetime | None = Field(default=None, description="When this memory is valid")
    invalid_at: datetime | None = Field(default=None, description="When this memory expires")

    # Provenance
    source: str | None = Field(default=None, description="Source of memory (e.g., 'bug_fix', 'code_review')")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Round confidence to 2 decimal places."""
        return round(v, 2)

    def to_episode_content(self) -> str:
        """Convert memory to episode content for Graphiti."""
        parts = [
            f"[{self.memory_type.value.upper()}] {self.title}",
            f"\n{self.content}",
            f"\n\nScope: {self.repository}/{self.branch}",
        ]

        if self.module:
            parts.append(f"\nModule: {self.module}")
        if self.service:
            parts.append(f"\nService: {self.service}")
        if self.tags:
            parts.append(f"\nTags: {', '.join(self.tags)}")
        if self.confidence < 1.0:
            parts.append(f"\nConfidence: {self.confidence:.0%}")

        return "".join(parts)


class ArchitectureMemory(MemoryBase):
    """Memory about system architecture."""

    memory_type: MemoryType = MemoryType.ARCHITECTURE

    # Architecture-specific fields
    component_type: str = Field(description="Type of component (service, database, api, etc.)")
    dependencies: list[str] = Field(default_factory=list, description="Component dependencies")
    interfaces: list[str] = Field(default_factory=list, description="Exposed interfaces")
    responsibilities: list[str] = Field(default_factory=list, description="Component responsibilities")


class DecisionMemory(MemoryBase):
    """Memory about design decisions."""

    memory_type: MemoryType = MemoryType.DECISION

    # Decision-specific fields
    decision_type: str = Field(description="Type of decision (pattern, library, architecture)")
    rationale: str = Field(description="Why this decision was made")
    alternatives_considered: list[str] = Field(default_factory=list, description="Alternatives considered")
    trade_offs: str | None = Field(default=None, description="Trade-offs of the decision")
    impact: str | None = Field(default=None, description="Impact of the decision")


class BugFixMemory(MemoryBase):
    """Memory about bug fixes and debugging discoveries."""

    memory_type: MemoryType = MemoryType.BUG_FIX

    # Bug fix-specific fields
    bug_type: str = Field(description="Type of bug (race condition, null pointer, logic)")
    root_cause: str = Field(description="Root cause of the bug")
    solution: str = Field(description="Solution implemented")
    symptoms: list[str] = Field(default_factory=list, description="Symptoms observed")
    prevention: str | None = Field(default=None, description="How to prevent similar bugs")


class ConventionMemory(MemoryBase):
    """Memory about coding conventions and best practices."""

    memory_type: MemoryType = MemoryType.CONVENTION

    # Convention-specific fields
    convention_type: str = Field(description="Type of convention (naming, structure, pattern)")
    rule: str = Field(description="The convention rule")
    rationale: str = Field(description="Why this convention exists")
    examples: list[str] = Field(default_factory=list, description="Examples of the convention")
    anti_patterns: list[str] = Field(default_factory=list, description="Anti-patterns to avoid")


class RelationshipMemory(MemoryBase):
    """Memory about relationships between entities."""

    memory_type: MemoryType = MemoryType.RELATIONSHIP

    # Relationship-specific fields
    source_entity: str = Field(description="Source entity name")
    target_entity: str = Field(description="Target entity name")
    relation_type: RelationType = Field(description="Type of relationship")
    properties: dict[str, Any] = Field(default_factory=dict, description="Relationship properties")


class ImplementationMemory(MemoryBase):
    """Memory about important implementation details."""

    memory_type: MemoryType = MemoryType.IMPLEMENTATION

    # Implementation-specific fields
    feature: str = Field(description="Feature/Functionality name")
    implementation_notes: str = Field(description="Key implementation details")
    gotchas: list[str] = Field(default_factory=list, description="Important gotchas/warnings")
    dependencies: list[str] = Field(default_factory=list, description="Required dependencies")


class SearchResult(BaseModel):
    """Result from memory search."""

    memory: MemoryBase
    score: float = Field(ge=0.0, le=1.0, description="Relevance score")
    matched_entities: list[str] = Field(default_factory=list, description="Matched entity names")
    relationship_path: list[str] = Field(default_factory=list, description="Path through relationships")
    retrieval_method: str = Field(description="How this result was found")


class MemoryQuery(BaseModel):
    """Query for searching memories."""

    query_text: str = Field(description="Search query text")
    memory_types: list[MemoryType] | None = Field(default=None, description="Filter by memory types")
    repositories: list[str] | None = Field(default=None, description="Filter by repositories")
    modules: list[str] | None = Field(default=None, description="Filter by modules")
    services: list[str] | None = Field(default=None, description="Filter by services")
    tags: list[str] | None = Field(default=None, description="Filter by tags")
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum confidence")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    include_relationships: bool = Field(default=True, description="Include related memories")
    time_range_days: int | None = Field(default=None, description="Recent memories in days")


class MemoryUpdate(BaseModel):
    """Update for an existing memory."""

    uuid: UUID = Field(description="Memory UUID to update")
    title: str | None = Field(default=None, description="New title")
    content: str | None = Field(default=None, description="New content")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="New confidence")
    tags: list[str] | None = Field(default=None, description="New tags")
    metadata: dict[str, Any] | None = Field(default=None, description="New metadata")
    increment_confidence: bool = Field(
        default=False, description="Increment confidence when updating with similar content"
    )
