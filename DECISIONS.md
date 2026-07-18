# Architecture Decision Records

This document tracks significant architectural decisions made during development.

---

## ADR-001: Delegate to Graphiti

**Status**: Accepted

**Context**: We need entity extraction, relationship mapping, and semantic search.

**Decision**: Use Graphiti for all knowledge graph operations. Don't reimplement.

**Rationale**:
- Graphiti already implements entity extraction using LLMs
- Graphiti handles deduplication
- Graphiti provides semantic search via embeddings
- Our value add is *admission control*, not graph mechanics

**Consequences**:
- Positive: Less code to maintain
- Positive: Leverage tested Graphiti implementation
- Negative: Dependency on Graphiti API stability
- Negative: Limited control over extraction quality

---

## ADR-002: Repository Isolation via group_id

**Status**: Accepted

**Context**: Multiple repositories will use the same knowledge graph.

**Decision**: Use Graphiti's `group_id` parameter for repository isolation.

**Rationale**:
```python
group_id = f"repo_{repository}_branch_{branch}"
```

**Consequences**:
- Positive: Simple implementation
- Positive: Graphiti-native approach
- Positive: Easy to query per-repository
- Negative: No cross-repository knowledge sharing
- Negative: Branch proliferation if not managed

---

## ADR-003: Rule-Based Admission Policy

**Status**: Accepted

**Context**: We need to decide what knowledge to store.

**Decision**: Implement rule-based admission policy (not ML-based).

**Approach**:
1. Filter trivial operations (file listing, directory changes)
2. Reject failed executions
3. Block secrets/credentials (regex patterns)
4. Require file changes

**Rationale**:
- Simple to implement and test
- Easy to understand and debug
- No training data required
- Fast execution (no model inference)

**Consequences**:
- Positive: Predictable behavior
- Positive: Easy to modify rules
- Negative: May reject useful non-file-changing operations
- Negative: May admit low-value content
- **Future**: May need ML-based policy for precision

---

## ADR-004: Graceful Degradation

**Status**: Accepted

**Context**: Memory system failures shouldn't break agent execution.

**Decision**: Wrap all Graphiti operations in try-except. Log errors, don't raise.

**Implementation**:
```python
try:
    await graphiti.add_episode(episode_body)
except Exception as e:
    logger.error(f"Memory storage failed: {e}")
    # Continue execution
    return None
```

**Consequences**:
- Positive: Agent continues even if memory fails
- Negative: Silent failures may hide issues
- Negative: Difficult to debug production issues

---

## ADR-005: Batch Processing Only

**Status**: Accepted

**Context**: Real-time processing adds complexity.

**Decision**: Process executions in batches, not real-time streaming.

**Rationale**:
- Simpler error handling
- Easier to retry failed batches
- Better performance (batch API calls)
- Matches OpenHands workflow

**Consequences**:
- Positive: Simpler implementation
- Positive: Better throughput
- Negative: Memory not immediately available
- Negative: Delay between execution and storage

---

## ADR-006: No Memory Expiration

**Status**: Accepted (temporary)

**Context**: Knowledge graphs can grow indefinitely.

**Decision**: No automatic expiration in v1.0.

**Rationale**:
- Unknown retention requirements
- Need benchmarks first
- Neo4j can handle large graphs
- Manual cleanup possible

**Consequences**:
- Positive: Simpler implementation
- Negative: Unbounded growth
- Negative: May store outdated knowledge
- **Future**: Implement TTL or relevance-based expiration

---

## Templates for Future ADRs

```markdown
## ADR-XXX: Title

**Status**: [Proposed | Accepted | Deprecated | Superseded]

**Context**: What is the issue?

**Decision**: What are we doing?

**Rationale**: Why?

**Consequences**:
- Positive: ...
- Negative: ...
```
