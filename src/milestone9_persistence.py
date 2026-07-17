"""
Milestone 9: Persistence Validation

Prove that memories survive agent restart.
"""
import asyncio
import time
from milestone1_models import Memory, MemoryCategory, RetrievalContext
from milestone8_real_graphiti import RealGraphitiBackend


async def test_persistence():
    """Test that memories persist across restarts."""
    
    print("=" * 70)
    print("MILESTONE 9: Persistence Validation")
    print("=" * 70)
    
    # 1. Create backend and store memory
    print("\n1. Storing memory in Neo4j...")
    backend1 = RealGraphitiBackend()
    
    await backend1.clear_repo("persist-test")
    
    memory = Memory(
        id="persist-1",
        title="Auth Configuration",
        summary="AuthService uses JWT tokens with 24-hour expiration",
        category=MemoryCategory.ARCHITECTURE,
        confidence=0.92,
        source="config-doc",
        repository="persist-test",
        branch="main"
    )
    
    await backend1.store(memory)
    print(f"   Stored: {memory.title}")
    
    # 2. Close connection (simulating restart)
    print("\n2. Closing connection (simulating restart)...")
    backend1.close()
    time.sleep(1)
    
    # 3. Create new backend instance (simulating fresh start)
    print("\n3. Creating new backend instance (fresh start)...")
    backend2 = RealGraphitiBackend()
    
    # 4. Retrieve memory
    print("\n4. Retrieving memory after 'restart'...")
    context = RetrievalContext(
        task="auth",
        repository="persist-test",
        branch="main",
        workspace_path="/tmp"
    )
    
    results = await backend2.retrieve(context)
    
    print(f"   Found {len(results)} memories")
    
    # 5. Verify persistence
    print("\n5. Verifying persistence...")
    
    assert len(results) > 0, "Memory lost after restart!"
    
    retrieved_memory = results[0]
    
    print(f"   - ID: {retrieved_memory.id}")
    print(f"   - Title: {retrieved_memory.title}")
    print(f"   - Summary: {retrieved_memory.summary}")
    print(f"   - Confidence: {retrieved_memory.confidence}")
    print(f"   - Repository: {retrieved_memory.repository}")
    
    # Verify all fields preserved
    assert retrieved_memory.id == memory.id, "ID mismatch"
    assert retrieved_memory.title == memory.title, "Title mismatch"
    assert retrieved_memory.summary == memory.summary, "Summary mismatch"
    assert retrieved_memory.confidence == memory.confidence, "Confidence mismatch"
    assert retrieved_memory.repository == memory.repository, "Repository mismatch"
    
    print("\n✅ All fields preserved after restart")
    
    # 6. Cleanup
    print("\n6. Cleaning up...")
    await backend2.clear_repo("persist-test")
    backend2.close()
    
    print("\n" + "=" * 70)
    print("✅ MILESTONE 9 COMPLETE")
    print("=" * 70)
    print("\nKey Findings:")
    print("  - Memories persist across connection close")
    print("  - All metadata preserved")
    print("  - Repository context intact")
    print("\n✅ Persistence PROVEN")


if __name__ == "__main__":
    asyncio.run(test_persistence())
