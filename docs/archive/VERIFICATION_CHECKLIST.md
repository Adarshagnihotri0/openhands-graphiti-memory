# Production Verification Checklist

Before claiming this is production-ready, you must verify these critical points.

---

## 🔴 RED: Must Verify

### 1. Do OpenHands Hooks Actually Exist?

**The Question:** Does OpenHands expose `register_pre_task_hook` or similar?

**How to Verify:**
```bash
# Clone OpenHands repo
git clone https://github.com/All-Hands-AI/OpenHands
cd OpenHands

# Search for lifecycle hooks
grep -r "pre_task" --include="*.py" | head -20
grep -r "hook" --include="*.py" agenthub/ | head -20
grep -r "register.*hook" --include="*.py" | head -20

# Check agent base class
find . -name "agent.py" -o -name "base_agent.py" | xargs grep -l "class.*Agent"
```

**If hooks DON'T exist**, alternative integration points:
- **Prompt Builder**: Modify system prompt construction
- **MCP Orchestrator**: Hook into MCP tool resolution layer
- **Task Planner**: Intercept task planning phase
- **Middleware Layer**: Add memory layer between agent and tools

**What I need to check:**
```
openhands/
├── agent/           # Check agent.py for hook registration
├── controller/      # Check task orchestration
├── llm/             # Check prompt building
└── mcp/             # Check MCP integration layer
```

**Status:** ❓ NEEDS VERIFICATION

---

### 2. Memory Injection Budget

**The Problem:**
```
Retrieve 20 memories → 40k tokens → LLM timeout
```

**What I implemented:**
- `limit=10` in config (GRAPHITI_RETRIEVAL_LIMIT)
- Rank by confidence + recency
- Format concisely (title + preview only)

**What's missing:**
```python
# Add token budget management
MAX_MEMORY_TOKENS = 2000  # Conservative budget

def _format_memories_for_injection(memories: list, task: str) -> str:
    """
    Format with token budget.
    """
    selected = []
    current_tokens = 0
    
    # Sort by score
    memories.sort(key=lambda m: m.score, reverse=True)
    
    # Select top memories within budget
    for mem in memories[:20]:  # Cap at 20
        mem_tokens = estimate_tokens(mem)
        
        if current_tokens + mem_tokens <= MAX_MEMORY_TOKENS:
            selected.append(mem)
            current_tokens += mem_tokens
        
        if len(selected) >= 5:  # Top 5 max
            break
    
    return format_concise(selected)
```

**Add to config:**
```bash
GRAPHITI_MAX_MEMORY_TOKENS=2000
GRAPHITI_MAX_MEMORIES_INJECTED=5
```

**Status:** ⚠️ NEEDS IMPLEMENTATION

---

### 3. Conflict Detection

**The Problem:**
```
Memory 1: "Redis is source of truth"
Memory 2: "PostgreSQL is source of truth"  # Contradicts!
```

**What's needed:**
```python
class MemoryStatus(Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded_by"
    DEPRECATED = "deprecated"
    INVALID = "invalid"
    VERIFIED = "verified"
    DISPUTED = "disputed"
```

**Add to memory model:**
```python
class MemoryBase(BaseModel):
    # ... existing fields
    status: MemoryStatus = MemoryStatus.ACTIVE
    superseded_by: UUID | None = None
    deprecated_at: datetime | None = None
    deprecated_reason: str | None = None
    verified_at: datetime | None = None
    verified_by: str | None = None  # Agent or human
```

**Conflict detection logic:**
```python
async def store_with_conflict_detection(memory: MemoryBase):
    """
    Store memory with conflict detection.
    """
    # Find potentially conflicting memories
    similar = await find_similar_memories(memory, threshold=0.8)
    
    for existing in similar:
        if contradicts(memory, existing):
            if memory.confidence > existing.confidence:
                # New memory supersedes old
                await mark_superseded(
                    existing.uuid,
                    reason=f"Superseded by {memory.uuid}",
                    superseded_by=memory.uuid
                )
            else:
                # Mark as disputed
                await mark_disputed(
                    memory.uuid,
                    reason=f"Conflicts with {existing.uuid}"
                )
                return
    
    await store_memory(memory)
```

**Status:** ⚠️ NEEDS IMPLEMENTATION

---

### 4. Source Provenance

**The Problem:** "Why do I believe this?"

**Add to memory model:**
```python
class Provenance(BaseModel):
    """Track where knowledge came from."""
    source_type: str  # "ADR", "commit", "conversation", "code_review"
    source_id: str | None = None  # ADR-003, commit Sha, PR number
    source_title: str | None = None  # "Use PostgreSQL for ACID"
    source_url: str | None = None  # Link to source document
    author: str | None = None
    timestamp: datetime
    
class MemoryBase(BaseModel):
    # ... existing fields
    provenance: Provenance | None = None
```

**When storing:**
```python
await store_memory(
    memory,
    provenance=Provenance(
        source_type="ADR",
        source_id="ADR-003",
        source_title="Use PostgreSQL for ACID transactions",
        source_url="https://github.com/org/repo/blob/main/docs/adr/003-postgres.md",
        author="Jane Doe",
        timestamp=datetime.utcnow()
    )
)
```

**Status:** ⚠️ NEEDS IMPLEMENTATION

---

## 🟡 YELLOW: Should Implement

### 5. Multi-Agent Safety

**The Problem:** Concurrent writes create race conditions.

**Solution:**
```python
import asyncio

class GraphitiClient:
    def __init__(self):
        self._write_lock = asyncio.Lock()
    
    async def store_memory(self, memory: MemoryBase):
        """
        Store with optimistic locking.
        """
        async with self._write_lock:
            # Check for duplicate
            similar = await self._find_similar(memory)
            
            if similar:
                # Update instead of duplicate
                return await self._update_existing(similar, memory)
            else:
                # Store new
                return await self._store_new(memory)
```

**Add idempotency key:**
```python
class MemoryBase(BaseModel):
    idempotency_key: str | None = None
    
# Generate deterministic key
memory.idempotency_key = hashlib.sha256(
    f"{memory.title}:{memory.content[:100]}:{memory.repository}".encode()
).hexdigest()
```

**Status:** ⚠️ NEEDS IMPLEMENTATION

---

### 6. Prompt Hygiene

**Current output (bad):**
```
Memory(uuid=abc123, title=Architecture, content=AuthService...)
Memory(uuid=def456, title=Decision, content=We chose...)
```

**Better output:**
```
Relevant project knowledge:

• AuthService depends on TokenService for JWT validation
• Decision: Use PostgreSQL for ACID transactions (ADR-003)
• Bug: Race condition in cache fixed with Redlock (commit abc123)

Use these only if relevant to the current task.
```

**Implementation:**
```python
def _format_memories_for_injection(memories: list, task: str) -> str:
    """
    Format memories as clean bullet points.
    """
    if not memories:
        return ""
    
    lines = ["Relevant project knowledge:\n"]
    
    for mem in memories[:5]:  # Top 5
        # Clean, concise bullet point
        bullet = f"• {mem.title}"
        
        if mem.confidence >= 0.9:
            bullet += " (verified)"
        
        lines.append(bullet)
    
    lines.append("\nUse these only if relevant to the current task.")
    
    return "\n".join(lines)
```

**Status:** ⚠️ NEEDS IMPLEMENTATION

---

### 7. Memory Quality Threshold

**Rule:** "Would this help 6 months from now?"

**Implementation:**
```python
def should_promote_to_memory(task: str, result: str) -> bool:
    """
    Determine if task result contains durable knowledge.
    """
    # Quick heuristics to reject transient info
    transient_indicators = [
        "failed once",
        "temporary",
        "workaround",
        "my machine",
        "my local",
        "wifi",
        "network issue"
    ]
    
    full_text = f"{task} {result}".lower()
    
    for indicator in transient_indicators:
        if indicator in full_text:
            return False
    
    # Check for durable patterns
    durable_indicators = [
        "depends on",
        "architecture",
        "design",
        "convention",
        "always",
        "never",
        "pattern",
        "decision"
    ]
    
    for indicator in durable_indicators:
        if indicator in full_text:
            return True
    
    return False
```

**Status:** ⚠️ NEEDS IMPLEMENTATION

---

### 8. Retrieval Tracing

**Add detailed logging:**
```python
async def pre_task_hook(task: str, context: TaskContext):
    """
    Automatic retrieval with tracing.
    """
    logger.info(
        "Memory retrieval started",
        task=task[:100],
        repository=context.repository
    )
    
    # Retrieve
    raw_results = await graphiti.search(task, limit=20)
    logger.info("Retrieved from Graphiti", count=len(raw_results))
    
    # Filter
    filtered = [r for r in raw_results if r.confidence >= MIN_CONFIDENCE]
    logger.info("Filtered by confidence", count=len(filtered))
    
    # Select top
    selected = filtered[:5]
    logger.info(
        "Selected top memories",
        count=len(selected),
        rejected_count=len(filtered) - len(selected),
        reasons=[f"low confidence: {len(raw_results) - len(filtered)}"]
    )
    
    # Inject
    context_str = format_concise(selected)
    token_count = estimate_tokens(context_str)
    logger.info(
        "Injected into prompt",
        memories=len(selected),
        tokens=token_count
    )
    
    return context_str
```

**Status:** ⚠️ NEEDS IMPLEMENTATION

---

## End-to-End Test Plan

**The definitive proof that this works:**

### Test 1: Bootstrap and Learn

```python
# Start fresh
await graphiti.clear_graph()

# Solve task
task = "Fix authentication race condition in token refresh"
result = await openhands.solve(task)

# Verify storage
memories = await graphiti.search("authentication race condition")
assert len(memories) > 0
assert any("race condition" in m.content.lower() for m in memories)
```

### Test 2: Retrieval in New Session

```python
# New session (simulated)
openhands2 = create_agent()

# Related task
task = "Implement idempotent token refresh"
result = await openhands2.solve(task)

# Verify automatic retrieval happened
# Check logs for:
# "Retrieved from Graphiti: 5 memories"
# "Injected into prompt: 3 memories"

# Verify result mentions previous learning
assert "race condition" in result.lower() or "idempotent" in result.lower()
```

### Test 3: No Manual Tool Calls

```python
# Monitor MCP calls
mcp_calls = []

def track_mcp_call(tool: str, args: dict):
    mcp_calls.append((tool, args))

# Run task
result = await openhands.solve("Fix auth bug")

# Verify NO manual search_memory calls
manual_searches = [c for c in mcp_calls if c[0] == "search_memory"]
assert len(manual_searches) == 0  # Must be zero!

# Memory should have been injected automatically via hook
assert any("memory" in str(c).lower() for c in mcp_calls)
```

---

## Context Builder Component

**The missing piece between Graphiti + Code Index → LLM:**

```python
class ContextBuilder:
    """
    Merge, dedupe, rank, and summarize from multiple sources.
    """
    
    async def build_context(
        self,
        task: str,
        max_tokens: int = 2000
    ) -> str:
        """
        Build unified context from Graphiti + Code Index.
        """
        # Query both in parallel
        graphiti_task = graphiti.search(task, limit=20)
        code_index_task = code_index.search_symbols(task, limit=20)
        
        graphiti_results, code_results = await asyncio.gather(
            graphiti_task,
            code_index_task
        )
        
        # Merge
        merged = self._merge_sources(graphiti_results, code_results)
        
        # Deduplicate
        deduped = self._deduplicate(merged)
        
        # Rank by relevance
        ranked = self._rank_by_task_relevance(deduped, task)
        
        # Select within token budget
        selected = self._select_within_budget(ranked, max_tokens)
        
        # Format as clean context
        return self._format_context(selected)
    
    def _merge_sources(self, graphiti, code_index):
        """
        Merge with source attribution.
        """
        merged = []
        
        for mem in graphiti:
            merged.append({
                "content": mem.content,
                "source": "graphiti",
                "type": mem.memory_type,
                "confidence": mem.confidence,
                "score": mem.score
            })
        
        for sym in code_index:
            merged.append({
                "content": f"{sym.name} ({sym.type})",
                "source": "code_index",
                "type": sym.type,
                "file": sym.file_path,
                "score": sym.relevance_score
            })
        
        return merged
    
    def _format_context(self, selected: list) -> str:
        """
        Format as clean, concise context.
        """
        lines = ["Relevant context:\n"]
        
        # Group by source
        from_graphiti = [s for s in selected if s["source"] == "graphiti"]
        from_code = [s for s in selected if s["source"] == "code_index"]
        
        if from_graphiti:
            lines.append("Project knowledge:")
            for item in from_graphiti[:3]:
                lines.append(f"  • {item['content'][:100]}")
        
        if from_code:
            lines.append("\nRelevant code:")
            for item in from_code[:5]:
                lines.append(f"  • {item['content']} ({item['file']})")
        
        return "\n".join(lines)
```

---

## Final Verification

**Before claiming victory, run this test:**

```bash
# 1. Check OpenHands has hook mechanism
./scripts/verify_openhands_hooks.sh

# 2. Run end-to-end test
pytest tests/test_automatic_memory.py::test_e2e_automatic_retrieval

# 3. Verify no manual tool calls
pytest tests/test_automatic_memory.py::test_no_manual_search

# 4. Verify bootstrap works
pytest tests/test_automatic_memory.py::test_repo_bootstrap
```

**If all tests pass, you've achieved:**
- ✅ Automatic memory retrieval
- ✅ No manual intervention
- ✅ Persistence across sessions
- ✅ Production-ready quality

**Only then can you say: "This is a memory system, not a memory database."**
