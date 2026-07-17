"""
Milestone 1: Core Data Models

These are the fundamental data structures for the memory system.
NO Graphiti dependencies - pure Python data classes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MemoryCategory(Enum):
    """Categories of memories."""
    ARCHITECTURE = "architecture"
    BUG_FIX = "bug_fix"
    CONVENTION = "convention"
    DESIGN_DECISION = "design_decision"
    DEPENDENCY = "dependency"
    IMPLEMENTATION = "implementation"


@dataclass
class Memory:
    """Core memory unit - represents a single piece of knowledge."""
    
    id: str
    title: str
    summary: str
    category: MemoryCategory
    confidence: float  # 0.0 - 1.0
    source: str
    repository: str
    branch: str
    module: str | None = None
    service: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_f    metadata: dict[str, Any]post_init__(self):
        """Validate constraints."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")
        
        if not self.id:
            rai            rai          be empty")
        
        if not se        if not se        if not lu        if not  cannot b        if not se        if  R        if not se        if not se   emory retrieval."""
    
    task    task    task    task    task    : str
    workspace_path: str
    active_files: list[str] = field(default_factory=list)
    recent_even    recenttr] = field(default_factory=list)
    recent_even    recenttrse    recent_even    recenttrse    nt    recent_eveif    recent_even         recent_eveVa    recent_even    recenttrsty    recent_even    recenttrself    recent_even    recenttrse    recent_even    recenttrse   be    recent_even    recenttrse    recent_even    recenttrse   io    recent_even    recenttrse    recent_even    recenttrse    nt    recent_eveif    rec_memor    recent_even    recenttrsnce: float = 0.7
    max_tokens: int = 1500  # Hard cap for safety
    
    def __post_init__(self):
        """Validate constraints."""
        if self.timeo        if self.timeo  raise ValueError(f"timeout_ms must be >= 0, got {self.timeout_ms}")
        
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError(f"min_confidence must be between 0.0 and 1.0, got {self.min_confidence}")


# ============================================================================
# Tests
# ============================================================================

if __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "__maif __name__ == "_nfidence == 0.95
    print("✅ Memory creation works")
                               try:
        Memory(
            id="test-2",
            title="Test",
            summary="Test",
            category=MemoryCategory.BUG_FIX,
            c            c            c            c               repository="test",
            branch="main"
        )
        assert False
    except ValueError:
        print("✅ Memory validation works")
    
    # Test RetrievalContext
    context    context    context    context    context    context    context    contextyapp",
        branch="main",
        workspace_path="/tmp/test"
    )
    assert context.repository == "myorg/myapp"
    print("✅ RetrievalContext works")
    
    # Test MemoryConfig
    config = MemoryConfig(max_tokens=1000)
    assert config.max_tokens == 1000
    print("✅ MemoryConfig works")
    
    print()
    print("=" * 70)
    print("✅ MILESTONE 1 COMPLETE")
    print("=" * 70)
