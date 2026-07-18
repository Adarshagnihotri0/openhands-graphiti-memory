"""
Milestone 2: MockBackend for testing
"""
from abc import ABC, abstractmethod
from milestone1_models import Memory, MemoryCategory, RetrievalContext


class MemoryBackend(ABC):
    @abstractmethod
    async def retrieve(self, context: RetrievalContext, limit: int = 10) -> list[Memory]:
        pass
    
    @abstractmethod
    async def store(self, memory: Memory) -> None:
        pass


class MockBackend(MemoryBackend):
    def __init__(self):
        self.memories: list[Memory] = []
    
    async def retrieve(self, context: RetrievalContext, limit: int = 10) -> list[Memory]:
        # For testing, return all memories (real implementation would use semantic search)
        return self.memories[:limit]
    
    async def store(self, memory: Memory) -> None:
        self.memories.append(memory)


if __name__ == "__main__":
    import asyncio
    
    async def test_milestone2():
        print("Testing Milestone 2: MockBackend")
        
        backend = MockBackend()
        
        # Store test memories
        m1 = Memory(
            id="1",
            title="Auth Architecture",
            summary="AuthService depends on TokenService",
            category=MemoryCategory.ARCHITECTURE,
            confidence=0.95,
            source="ADR-003",
            repository="myorg/myapp",
            branch="main"
        )
        await backend.store(m1)
        
        m2 = Memory(
            id="2",
            title="Bug Fix",
            summary="Race condition in auth flow",
            category=MemoryCategory.BUG_FIX,
            confidence=0.85,
            source="debug-2024",
            repository="myorg/myapp",
            branch="main"
        )
        await backend.store(m2)
        
        print(f"✅ Stored {len(backend.memories)} memories")
        
        # Test retrieval
        ctx = RetrievalContext(
            task="auth",
            repository="myorg/myapp",
            branch="main",
            workspace_path="/tmp"
        )
        
        results = await backend.retrieve(ctx)
        assert len(results) >= 1
        print(f"✅ Retrieved {len(results)} memories")
        
        # Verify content
        assert any("TokenService" in m.summary for m in results)
        print("✅ Memory content correct")
        
        print("\n✅ MILESTONE 2 COMPLETE")
    
    asyncio.run(test_milestone2())
