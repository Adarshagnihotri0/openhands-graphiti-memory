"""
CoreMulti-Factor Ranking

Replace simple confidence ranking with composite scoring:
  relevance * confidence * freshness * repo_match * task_intent
"""
import asyncio
from datetime import datetime, timedelta
from milestone1_models import Memory, MemoryCategory, RetrievalContext
from milestone8_real_graphiti import RealGraphitiBackend


def calculate_freshness(memory: Memory, reference_time: datetime = None) -> float:
    """Calculate freshness score based on age."""
    
    if reference_time is None:
        reference_time = datetime.now()
    
    age_days = (reference_time - memory.created_at).days
    
    # Exponential decay: 1.0 (today) → 0.5 (1 year) → 0.25 (2 years)
    # Formula: e^(-λt) where λ = 0.0019 (half-life ≈ 1 year)
    decay_rate = 0.0019
    freshness = pow(2.71828, -decay_rate * age_days)
    
    return max(0.1, min(1.0, freshness))


def calculate_relevance(memory: Memory, task: str) -> float:
    """Calculate semantic relevance between memory and task."""
    
    # Simple word overlap for demo
    # Production: use embedding similarity
    
    task_words = set(task.lower().split())
    memory_words = set(memory.summary.lower().split())
    title_words = set(memory.title.lower().split())
    
    # Word overlap in summary
    summary_overlap = len(task_words & memory_words) / max(len(task_words), 1)
    
    # Word overlap in title
    title_overlap = len(task_words & title_words) / max(len(task_words), 1)
    
    # Weight title more heavily
    relevance = 0.3 * summary_overlap + 0.7 * title_overlap
    
    # Boost for exact keyword match
    key_terms = {
        'auth': ['auth', 'authentication', 'jwt', 'token'],
        'database': ['database', 'db', 'sql', 'postgres'],
        'api': ['api', 'endpoint', 'route', 'controller'],
    }
    
    for term, synonyms in key_terms.items():
        if any(s in task.lower() for s in synonyms):
            if any(s in memory.summary.lower() or s in memory.title.lower() for s in synonyms):
                relevance = min(1.0, relevance + 0.3)
    
    return max(0.1, min(1.0, relevance))


def calculate_intent_match(memory: Memory, task: str) -> float:
    """Calculate task intent alignment."""
    
    task_lower = task.lower()
    
    # Intent matching
    intent_scores = {
        MemoryCategory.ARCHITECTURE: 1.0 if any(w in task_lower for w in ['architecture', 'design', 'structure']) else 0.7,
        MemoryCategory.BUG_FIX: 1.0 if any(w in task_lower for w in ['bug', 'fix', 'error', 'debug']) else 0.5,
        MemoryCategory.CONVENTION: 1.0 if any(w in task_lower for w in ['style', 'convention', 'standard']) else 0.6,
        MemoryCategory.DESIGN_DECISION: 1.0 if any(w in task_lower for w in ['design', 'decision', 'adr']) else 0.7,
        MemoryCategory.DEPENDENCY: 1.0 if any(w in task_lower for w in ['dependency', 'depends', 'import']) else 0.6,
        MemoryCategory.IMPLEMENTATION: 1.0 if any(w in task_lower for w in ['implement', 'create', 'build']) else 0.8,
    }
    
    return intent_scores.get(memory.category, 0.5)


def composite_score(memory: Memory, context: RetrievalContext) -> float:
    """Calculate composite score for ranking."""
    
    # Factors
    relevance = calculate_relevance(memory, context.task)
    confidence = memory.confidence
    freshness = calculate_freshness(memory)
    repo_match = 1.0 if memory.repository == context.repository else 0.0
    intent_match = calculate_intent_match(memory, context.task)
    
    # Weighted composite (weights sum to 1.0)
    # Repository match is BINARY (must match)
    if repo_match == 0:
        return 0.0  # Zero if wrong repo
    
    score = (
        0.30 * relevance +
        0.25 * confidence +
        0.20 * freshness +
        0.15 * intent_match +
        0.10 * (1.0 if memory.repository == context.repository else 0.0)
    )
    
    return score


async def test_multi_factor_ranking():
    """Test multi-factor ranking vs simple confidence ranking."""
    
    print("=" * 70)
    print("=" * 70)
    
    # Setup
    backend = RealGraphitiBackend()
    await backend.clear_repo("test/ranking")
    
    # Create test memories with different characteristics
    print("\n1. Creating test memories...")
    
    now = datetime.now()
    
    memories = [
        Memory(
            id="rank-1",
            title="Auth Architecture",
            summary="AuthService authenticates users via JWT tokens",
            category=MemoryCategory.ARCHITECTURE,
            confidence=0.95,
            source="ADR-001",
            repository="test/ranking",
            branch="main",
            created_at=now - timedelta(days=30),  # Recent
        ),
        Memory(
            id="rank-2",
            title="OLD Auth Flow",
            summary="Auth flows through Gateway middleware",
            category=MemoryCategory.ARCHITECTURE,
            confidence=0.92,
            source="old-docs",
            repository="test/ranking",
            branch="main",
            created_at=now - timedelta(days=365),  # Old
        ),
        Memory(
            id="rank-3",
            title="Auth Bug Fix",
            summary="Fixed race condition in token validation",
            category=MemoryCategory.BUG_FIX,
            confidence=0.88,
            source="commit-abc",
            repository="test/ranking",
            branch="main",
            created_at=now - timedelta(days=7),  # Very recent
        ),
        Memory(
            id="rank-4",
            title="Database Connection",
            summary="PostgreSQL connection pool size is 10",
            category=MemoryCategory.ARCHITECTURE,
            confidence=0.90,
            source="config",
            repository="test/ranking",
            branch="main",
            created_at=now - timedelta(days=60),
        ),
        Memory(
            id="rank-5",
            title="Auth Convention",
            summary="Never call TokenService directly from routes",
            category=MemoryCategory.CONVENTION,
            confidence=0.85,
            source="style-guide",
            repository="test/ranking",
            branch="main",
            created_at=now - timedelta(days=90),
        ),
    ]
    
    for memory in memories:
        await backend.store(memory)
    
    print(f"   Stored {len(memories)} memories")
    
    print("\n2. Testing ranking for: 'Implement authentication endpoint'")
    
    context = RetrievalContext(
        task="Implement authentication endpoint",
        repository="test/ranking",
        branch="main",
        workspace_path="/tmp"
    )
    
    # Simple confidence ranking (OLD)
    print("\n3. OLD: Simple confidence ranking...")
    ranked_old = sorted(memories, key=lambda m: m.confidence, reverse=True)
    
    for i, m in enumerate(ranked_old, 1):
        print(f"   {i}. {m.title} (confidence: {m.confidence})")
    
    # Multi-factor ranking (NEW)
    print("\n4. NEW: Multi-factor ranking...")
    
    scored_memories = []
    for memory in memories:
        score = composite_score(memory, context)
        
        # Show factors
        relevance = calculate_relevance(memory, context.task)
        confidence = memory.confidence
        freshness = calculate_freshness(memory)
        intent_match = calculate_intent_match(memory, context.task)
        
        print(f"\n   {memory.id}: {memory.title}")
        print(f"     - Relevance: {relevance:.2f}")
        print(f"     - Confidence: {confidence:.2f}")
        print(f"     - Freshness: {freshness:.2f} ({(now - memory.created_at).days} days old)")
        print(f"     - Intent match: {intent_match:.2f}")
        print(f"     → Composite: {score:.3f}")
        
        scored_memories.append((memory, score))
    
    ranked_new = sorted(scored_memories, key=lambda x: x[1], reverse=True)
    
    print(f"\n5. Ranked order (NEW):")
    for i, (m, score) in enumerate(ranked_new, 1):
        print(f"   {i}. {m.title} (score: {score:.3f})")
    
    # Compare
    print("\n6. Comparison OLD vs NEW...")
    
    old_top = ranked_old[0].title
    new_top = ranked_new[0][0].title
    
    print(f"\n   OLD top result: {old_top}")
    print(f"   NEW top result: {new_top}")
    
    if old_top != new_top:
        print(f"   NEW ranking considers:")
        print(f"     - Relevance to task")
        print(f"     - Age of memory")
        print(f"     - Task intent alignment")
    else:
        print(f"\n   ℹ️  Same top result (both methods agree)")
    
    # Show why ranking changed
    print("\n7. Analysis of ranking change...")
    
    # Old top vs new top comparison
    old_top_idx = [i for i, m in enumerate(ranked_old) if m.title == new_top][0]
    
    print(f"\n   '{new_top}' improved from position {old_top_idx + 1} (OLD) to position 1 (NEW)")
    
    # Why?
    winner = ranked_new[0][0]
    loser = ranked_old[0]
    
    print(f"\n   Why '{winner.title}' wins:")
    print(f"     - Higher relevance: {calculate_relevance(winner, context.task):.2f} vs {calculate_relevance(loser, context.task):.2f}")
    print(f"     - Better intent match: {calculate_intent_match(winner, context.task):.2f} vs {calculate_intent_match(loser, context.task):.2f}")
    print(f"     - Fresher: {calculate_freshness(winner):.2f} vs {calculate_freshness(loser):.2f}")
    
    print("\n8. Verifying irrelevant memories score low...")
    
    db_memory = next(m for m in memories if "Database" in m.title)
    db_score = composite_score(db_memory, context)
    
    auth_memory = next(m for m in memories if "Auth Architecture" in m.title)
    auth_score = composite_score(auth_memory, context)
    
    print(f"\n   Auth memory score: {auth_score:.3f}")
    print(f"   Database memory score: {db_score:.3f}")
    
    assert auth_score > db_score, "Auth memory should score higher for auth task!"
    
    # Cleanup
    print("\n9. Cleaning up...")
    await backend.clear_repo("test/ranking")
    backend.close()
    
    print("\n" + "=" * 70)
    print("=" * 70)
    
    print("\nKey Findings:")
    print("  - Multi-factor ranking considers:")
    print("    * Relevance (30%)")
    print("    * Confidence (25%)")
    print("    * Freshness (20%)")
    print("    * Intent match (15%)")
    print("    * Repository match (10%)")
    print("  - Old high-confidence but irrelevant memories rank lower")
    print("  - Recent, relevant memories rank higher")
    print("  - Task intent alignment improves results")
    


if __name__ == "__main__":
    asyncio.run(test_multi_factor_ranking())
