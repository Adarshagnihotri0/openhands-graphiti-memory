"""
CoreContextBuilder with token budgeting
"""
from collections import defaultdict
from milestone1_models import Memory, MemoryConfig
from openhands.sdk.llm import Message, TextContent


class ContextBuilder:
    def __init__(self, config: MemoryConfig):
        self.config = config
    
    def build(self, memories: list[Memory]) -> list[Message]:
        if not memories:
            return []
        
        print(f"DEBUG: Building context from {len(memories)} memories")
        
        # 1. Rank by confidence
        ranked = sorted(memories, key=lambda m: m.confidence, reverse=True)
        
        # 2. Deduplicate by title similarity
        deduped = []
        seen_titles = set()
        for m in ranked:
            if m.title not in seen_titles:
                deduped.append(m)
                seen_titles.add(m.title)
        
        # 3. Apply token budget
        budgeted = self._apply_token_budget(deduped)
        
        # 4. Format as single structured message
        content = self._format_structured(budgeted)
        
        return [Message(role="system", content=[TextContent(text=content)])]
    
    def _apply_token_budget(self, memories: list[Memory]) -> list[Memory]:
        budgeted = []
        total_tokens = 0
        
        for memory in memories:
            # Estimate: ~4 chars per token
            memory_tokens = len(memory.summary) // 4
            if total_tokens + memory_tokens <= self.config.max_tokens:
                budgeted.append(memory)
                total_tokens += memory_tokens
            else:
                break
        
        return budgeted
    
    def _format_structured(self, memories: list[Memory]) -> str:
        sections = defaultdict(list)
        
        for memory in memories:
            sections[memory.category.value].append(memory)
        
        output = ["# Relevant Project Knowledge\n"]
        
        category_labels = {
            "architecture": "Architecture",
            "bug_fix": "Previous Bugs",
            "convention": "Conventions",
            "design_decision": "Design Decisions",
        }
        
        for category, label in category_labels.items():
            if category in sections:
                output.append(f"\n## {label}\n")
                for memory in sections[category]:
                    output.append(f"• {memory.summary}\n")
        
        output.append("\nUse this information if relevant.\n")
        
        return "".join(output)


if __name__ == "__main__":
    from milestone1_models import MemoryCategory
    
    print("Testing CoreContextBuilder")
    
    config = MemoryConfig(max_tokens=1500)
    builder = ContextBuilder(config)
    
    # Create test memories
    memories = [
        Memory(
            id="1",
            title="Auth Architecture",
            summary="AuthService depends on TokenService for JWT validation",
            category=MemoryCategory.ARCHITECTURE,
            confidence=0.95,
            source="ADR-003",
            repository="myorg/myapp",
            branch="main"
        ),
        Memory(
            id="2",
            title="Race Condition Bug",
            summary="Fixed race condition in auth middleware",
            category=MemoryCategory.BUG_FIX,
            confidence=0.85,
            source="commit-abc",
            repository="myorg/myapp",
            branch="main"
        ),
        Memory(
            id="3",
            title="Controller Convention",
            summary="Never call repositories directly from controllers",
            category=MemoryCategory.CONVENTION,
            confidence=0.90,
            source="style-guide",
            repository="myorg/myapp",
            branch="main"
        )
    ]
    
    # Build context
    messages = builder.build(memories)
    
    assert len(messages) == 1
    
    assert messages[0].role == "system"
    
    content = messages[0].content[0].text
    assert "## Architecture" in content
    assert "## Previous Bugs" in content
    assert "## Conventions" in content
    
    assert "AuthService depends on TokenService" in content
    
    large_config = MemoryConfig(max_tokens=50)
    small_builder = ContextBuilder(large_config)
    
    # Create many memories
    many_memories = [
        Memory(
            id=str(i),
            title=f"Memory {i}",
            summary="X" * 200,  # ~50 tokens each
            category=MemoryCategory.ARCHITECTURE,
            confidence=0.8,
            source="test",
            repository="test",
            branch="main"
        )
        for i in range(20)
    ]
    
    budgeted = small_builder._apply_token_budget(many_memories)
    
    # Should only include memories that fit budget
    total_chars = sum(len(m.summary) for m in budgeted)
    assert total_chars <= 200  # 50 tokens * 4 chars/token
    
