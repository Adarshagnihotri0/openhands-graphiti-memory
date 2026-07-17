# ACTION PLAN - Production Validation

## Current Status
- Architecture: ✅ Complete (9.5/10)
- Implementation: ❌ NOT PROVEN (0/10)

---

## Critical Missing Pieces

### 1. Multi-Factor Ranking (HIGH PRIORITY)
**File:** `milestone3_builder.py`
**Current:** Rank by confidence only
**Needed:**
```python
def score_memory(memory, context, task_intent):
    relevance = semantic_similarity(memory.summary, context.task)
    confidence = memory.confidence
    freshness = decay_function(memory.updated_at)
    repo_match = 1.0 if memory.repository == context.repository else 0.0
    
    return relevance * confidence * freshness * repo_match
```

---

### 2. Feedback Loop (HIGH PRIORITY)
**File:** NEW `milestone8_feedback.py`
**Needed:**
```python
class FeedbackTracker:
    def track_usage(self, memory_id: str, used: bool, contradicted: bool):
        if used:
            memory.used_count += 1
        if contradicted:
            memory.confidence *= 0.9  # Downgrade
```

---

### 3. Memory Expiration (MEDIUM PRIORITY)
**File:** `milestone1_models.py`
**Needed:**
```python
class MemoryState(Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"
```

---

### 4. Explainability (MEDIUM PRIORITY)
**File:** `milestone5_provider.py`
**Needed:**
```python
def log_retrieval_decision(memories, skipped):
    logger.info(f"Retrieved {len(memories)} memories:")
    for m in memories:
        logger.info(f"  - {m.title} (conf: {m.confidence}, source: {m.source})")
    logger.info(f"Skipped {len(skipped)} memories (low confidence)")
```

---

### 5. Real Metric: Repository Rediscovery Reduction (CRITICAL)
**File:** NEW `milestone10_metrics.py`
**Needed:**
```python
class ExplorationMetrics:
    files_opened: int = 0
    grep_calls: int = 0
    search_queries: int = 0
    time_to_solution: float = 0.0
    
    def calculate_reduction(baseline):
        return {
            'files': (baseline.files - current.files) / baseline.files,
            'grep': (baseline.grep - current.grep) / baseline.grep,
            'time': (baseline.time - current.time) / baseline.time
        }
```

---

## Next Milestones (PROOF-FOCUSED)

### Milestone 8: Real Graphiti Integration
```bash
# Spin up Graphiti
docker run -p 7687:7687 -p 7474:7474 neo4j:latest

# Test repository scoping
python milestone8_real_graphiti.py
```

**Criteria:**
- ✅ Store memory in Repo A
- ✅ Store memory in Repo B
- ✅ Query Repo A → No Repo B memories
- ✅ Query Repo B → No Repo A memories

---

### Milestone 9: Persistence Validation
```bash
# Store memory
python store_memory.py --repo "test/repo" --message "Auth uses TokenService"

# Restart agent
python restart_agent.py

# Query memory
python query_memory.py --repo "test/repo"
```

**Criteria:**
- ✅ Memory survives restart
- ✅ Repository context preserved
- ✅ Metadata intact

---

### Milestone 10: Measure Real Utility
```bash
# BASELINE (without memory)
python run_task.py --task "Implement OAuth" --no-memory
# Count: files_opened=42, grep_calls=31, time=180s

# WITH MEMORY
python run_task.py --task "Implement OAuth" --with-memory
# Count: files_opened=11, grep_calls=7, time=95s

# Calculate reduction
python calculate_reduction.py
# files: -74%, grep: -77%, time: -47%
```

**Success Criteria:**
- ✅ files_opened reduction > 50%
- ✅ grep_calls reduction > 50%
- ✅ time_to_solution reduction > 30%

---

### Milestone 11: Feedback Loop Implementation
```python
# Track memory usage
if model_response_mentions("TokenService"):
    memory.used_count += 1
    memory.confidence = min(1.0, memory.confidence * 1.05)

if model_contradicts("Auth depends on TokenService"):
    memory.validated = False
    memory.confidence *= 0.9
```

**Criteria:**
- ✅ Used memories gain confidence
- ✅ Contradicted memories lose confidence
- ✅ Ignored memories flagged for review

---

### Milestone 12: Multi-Factor Ranking
```python
# Replace simple confidence ranking
# with composite scoring
memories = sorted(memories, 
    key=lambda m: composite_score(m, context, task_intent),
    reverse=True
)
```

**Factors:**
- Relevance (semantic similarity)
- Confidence
- Freshness (decay over time)
- Repository match
- Task intent alignment

---

## Process Change

**OLD:** Design architecture → Write docs → Claim completion
**NEW:** Verify assumption → Measure outcome → Prove utility

---

## Success Metrics (REDEFINED)

| Metric | Current | Target | Evidence |
|--------|---------|--------|----------|
| Repository scoping | Logic exists | Verified with real Graphiti | Milestone 8 |
| Persistence | Not tested | Survives restart | Milestone 9 |
| Real utility | Unknown | >50% exploration reduction | Milestone 10 |
| Feedback loop | Missing | Adjusts confidence | Milestone 11 |
| Ranking quality | Confidence only | Multi-factor | Milestone 12 |

---

## What I Learned

1. **Architecture ≠ Implementation**
   - Good design is necessary but not sufficient
   - Real Graphiti reveals problems mocks hide

2. **Proxy metrics are dangerous**
   - Token usage ≠ utility
   - Latency ≠ helpfulness
   - Need actual outcome metrics

3. **Feedback loops are critical**
   - Without usage tracking, quality stagnates
   - Without expiration, graph accumulates noise
   - Without contradiction detection, hallucination propagates

4. **Evidence > Documentation**
   - Every design decision needs validation
   - Mock tests prove logic, not production behavior
   - Only real usage shows actual value

---

## Next Action

**STOP writing documentation.**

**START Milestone 8: Real Graphiti Integration.**

Run real Graphiti. Store real memories. Query real repository scoping.

Prove it works in production, not just in mock tests.
