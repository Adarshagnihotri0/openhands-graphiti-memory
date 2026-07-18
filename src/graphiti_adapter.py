"""
CoreGraphitiBackend (with mock for testing)
"""
from milestone1_models import Memory, MemoryCategory, RetrievalContext
from milestone2_backend import MemoryBackend
from datetime import datetime
from typing import Any


class GraphitiBackend(MemoryBackend):
    """
    Graphiti backend with repository scoping.
    
    In production, this would connect to real Graphiti instance.
    For testing, we use a mock implementation.
    """
    
    def __init__(self, uri: str = "bolt://localhost:7687", database: str = "neo4j"):
        self.uri = uri
        self.database = database
        self._mock_memories: list[Memory] = []
        
        # In production: self.client = GraphitiClient(uri, database)
        print(f"GraphitiBackend initialized (mock mode): {uri}/{database}")
    
    async def retrieve(self, context: RetrievalContext, limit: int = 10) -> list[Memory]:
        """
        Retrieve from Graphiti with repository scoping.
        
        Production query:
        ```
        MATCH (m:Memory {
            repository: 'myorg/myapp',
            branch: 'main'
        })
        WHERE m.summary CONTAINS 'auth'
        RETURN m
        ORDER BY m.confidence DESC
        LIMIT 10
        ```
        """
        
        # Mock implementation for testing
        results = []
        for memory in self._mock_memories:
            # Enforce repository scoping
            if memory.repository == context.repository and memory.branch == context.branch:
                results.append(memory)
        
        return results[:limit]
    
    async def store(self, memory: Memory) -> None:
        """Store memory in Graphiti."""
        
        # Mock implementation
        self._mock_memories.append(memory)
        
        # Production would create node:
        # CREATE (m:Memory {
        #     id: $id,
        #     repository: $repository,
        #     branch: $branch,
        #     summary: $summary,
        #     confidence: $confidence
        # })
    
    async def search_related(self, entity: str, max_depth: int = 2) -> list[Memory]:
        """
        Search related entities using graph traversal.
        
        Production query:
        ```
        MATCH path = (e:Entity {name: 'AuthService'})-[*1..2]-(related)
        RETURN related
        ```
        """
        
        # Mock implementation
        return []
    
    async def get_recent_changes(self, repository: str, since: datetime) -> list[Memory]:
        """Get recent changes for a repository."""
        
        # Mock implementation
        return [m for m in self._mock_memories if m.repository == repository and m.updated_at >= since]


if __name__ == "__main__":
    import asyncio
    
    async def test_milestone6():
        print("Testing CoreGraphitiBackend")
        
        backend = GraphitiBackend(uri="bolt://test:7687", database="test_db")
        
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
            title="Different Repo",
            summary="Other project memory",
            category=MemoryCategory.ARCHITECTURE,
            confidence=0.90,
            source="test",
            repository="other/repo",
            branch="main"
        )
        await backend.store(m2)
        
        
        ctx1 = RetrievalContext(
            task="auth",
            repository="myorg/myapp",
            branch="main",
            workspace_path="/tmp"
        )
        
        results1 = await backend.retrieve(ctx1)
        assert len(results1) == 1, f"Expected 1 result, got {len(results1)}"
        assert results1[0].repository == "myorg/myapp"
        
        ctx2 = RetrievalContext(
            task="test",
            repository="other/repo",
            branch="main",
            workspace_path="/tmp"
        )
        
        results2 = await backend.retrieve(ctx2)
        assert len(results2) == 1
        assert results2[0].repository == "other/repo"
        
        assert results1[0].id != results2[0].id
        
        recent = await backend.get_recent_changes("myorg/myapp", datetime.min)
        assert len(recent) == 1
        
        print("\nKey features:")
    
    asyncio.run(test_milestone6())
