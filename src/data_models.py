"""Core data models for memory system."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MemoryCategory(Enum):
    ARCHITECTURE = "architecture"
    BUG_FIX = "bug_fix"
    CONVENTION = "convention"
    DESIGN_DECISION = "design_decision"
    DEPENDENCY = "dependency"
    IMPLEMENTATION = "implementation"


@dataclass
class Memory:
    id: str
    title: str
    summary: str
    category: MemoryCategory
    confidence: float
    source: str
    repository: str
    branch: str
    module: str | None = None
    service: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {self.confidence}")


@dataclass
class RetrievalContext:
    task: str
    repository: str
    branch: str
    workspace_path: str
    active_files: list[str] = field(default_factory=list)
    recent_events: list[str] = field(default_factory=list)


@dataclass
class MemoryConfig:
    enabled: bool = True
    timeout_ms: int = 500
    max_memories: int = 5
    min_confidence: float = 0.7
    max_tokens: int = 1500


if __name__ == "__main__":
    m = Memory(
        id="test-1",
        title="Auth",
        summary="Auth depends on Token",
        category=MemoryCategory.ARCHITECTURE,
        confidence=0.95,
        source="ADR-003",
        repository="myorg/myapp",
        branch="main"
    )
    assert m.confidence == 0.95
    
    try:
        Memory(
            id="test-2",
            title="Test",
            summary="Test",
            category=MemoryCategory.BUG_FIX,
            confidence=1.5,
            source="test",
            repository="test",
            branch="main"
        )
        assert False
    except ValueError:
        pass
    
    ctx = RetrievalContext(
        task="Fix auth",
        repository="myorg/myapp",
        branch="main",
        workspace_path="/tmp"
    )
    assert ctx.repository == "myorg/myapp"
    
    cfg = MemoryConfig(max_tokens=1000)
    assert cfg.max_tokens == 1000

