# IMPLEMENTATION-READY STATUS REPORT

## RATING: Implementation-Ready (NOT 10/10)

Based on expert feedback, this is **ready to build**, not "perfect".

---

## ARCHITECTURAL UNCERTAINTIES STILL PRESENT

### 1. Context Window Interaction ⚠️

**Unknown:** Where does condenser run relative to `additional_messages`?

**Risk:** Memory might be summarized away if condenser runs AFTER injection

**Need to verify:**
```bash
grep -n "condenser" ~/.cache/uv/archive-v0/6IutzZ5k9UG5GtZO/lib/python3.13/site-packages/openhands/sdk/agent/utils.py
```

Look for order:
```
Option A: Memory → Condenser → LLM  ❌ (memory may be removed)
Option B: Condenser → Memory → LLM  ✅ (memory preserved)
```

**Action required:** Trace condenser call order before Phase 4

---

### 2. Streaming / Multi-turn Execution ⚠️

**Unknown:** Should memory run once per task or every LLM call?

**Risk:** Repeated Graphiti queries during long tool loops

**Recommendation:** Cache memory per conversation turn

**Implementation:**
```python
class MemoryProvider:
    def __init__(self):
        self._cache: dict[str, list[Memory]] = {}
    
    async def retrieve(self, conversation, state):
        turn_id = state.last_user_message_id
        
        # Check cache first
        if turn_id in self._cache:
            return self._cache[turn_id]
        
        # Retrieve and cache
        memories = await self._retrieve_from_backend(...)
        self._cache[turn_id] = memories
        return memories
```

**Action required:** Implement per-turn caching

---

### 3. Post-task Promotion ⚠️

**Unknown:** How to extract candidate memories after task completion?

**Current:** Only designed retrieval

**Missing:** Write pipeline

**Required design:**
```
Task finishes
    ↓
Candidate Extraction (what did we learn?)
    ↓
Confidence Scoring (is it durable?)
    ↓
Duplicate Detection (already known?)
    ↓
Store in Graphiti
```

**Action required:** Design post-task memory extraction

**Estimated effort:** Same as retrieval pipeline

---

### 4. Memory Ownership ⚠️

**Uncertainty:** Who owns memory? Agent or Conversation?

**Current:** Tied to Agent
**Better:** Tied to Conversation

**Issue:** Multi-agent scenarios

**Recommendation:**
```
Conversation
    ↓
MemoryManager (per-conversation)
    ↓
MemoryProvider (reusable)
    ↓
Backend (shared)
```

**Action required:** Review conversation-centric vs agent-centric design

---

## IMPLEMENTATION APPROACH

### Milestone 1: Core Models (NO Graphiti)
**Files:**
- `graphiti_memory/models/memory.py`
- `graphiti_memory/models/context.py`
- `graphiti_memory/models/config.py`
- `graphiti_memory/backends/base.py`
- `graphiti_memory/backends/mock_backend.py`

**Validates:** Data structures work

**Tests:** Unit tests for Memory, RetrievalContext

**Time:** 2-3 implementation cycles

---

### Milestone 2: Context Building (NO Graphiti)
**Files:**
- `graphiti_memory/builder/context_builder.py`
- `graphiti_memory/classifier/intent_classifier.py`
- `graphiti_memory/provider/memory_provider.py`

**Validates:** Formatting and intent classification work

**Tests:** 
- Test context builder formats correctly
- Test intent classifier skips greetings
- Test token budgeting

**Time:** 3-4 implementation cycles

---

### Milestone 3: Graphiti Backend
**Files:**
- `graphiti_memory/backends/graphiti_backend.py`

**Validates:** Can query Graphiti

**Tests:**
- Integration test with real Graphiti instance
- Mock test with simulated responses

**Time:** 3-4 implementation cycles

**Requires:** Graphiti server running

---

### Milestone 4: Agent Integration (SMALLEST PATCH)
**Files to MODIFY:**
- `/openhands/sdk/agent/agent.py` (2 locations: lines 651, 840)

**Approach:**
```python
# In Agent.__init__
self.memory_provider: MemoryProvider | None = None

# In Agent.step (line 651)
if self.memory_provider:
    memory_messages = await self.memory_provider.retrieve(conversation, state)
else:
    memory_messages = None

_messages = prepare_llm_messages(
    state.view,
    condenser=self.condenser,
    llm=self.llm,
    additional_messages=memory_messages  # Use existing parameter
)
```

**Validates:** End-to-end integration

**Tests:**
- E2E test with memory provider
- Test memory injected into messages
- Test graceful fallback when Graphiti fails

**Time:** 4-5 implementation cycles

---

## OPENHANDS INTEGRATION STRATEGY

### Option A: Direct Modification ❌
**Pros:** Fastest
**Cons:** Hard to maintain fork, upgrade pain

### Option B: Plugin/Extension ⚠️
**Requires:** Check if OpenHands supports plugins
**Action:** Research extension mechanisms

### Option C: Minimal Patch ✅
**Approach:** Isolate changes to smallest surface area
**Files:** Only modify agent.py initialization and step()
**Benefits:** Easier to rebase on OpenHands updates

**Recommendation:** Option C unless plugin mechanism exists

---

## SUCCESS METRICS (NOT ARCHITECTURE)

**Replace "good architecture" with measurable outcomes:**

### Performance Metrics
- **Latency:** p95 retrieval < 500ms
- **Token usage:** Memory context < 2000 tokens
- **Cache hit rate:** > 80% for multi-turn tasks

### Utility Metrics
- **Repository re-exploration:** Compare before/after
- **Repeat task success:** Measure improvement on similar tasks
- **Memory relevance:** Track how often memories are used

### Quality Metrics
- **Retrieval precision:** Human eval of memory relevance
- **False positive rate:** How often memory is unhelpful
- **Coverage:** % of tasks where memory was requested

---

## REMAINING RISKS

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Condenser removes memory | Medium | High | Verify order before Phase 4 |
| Cross-repo contamination | High | Critical | Repository scoping from day 1 |
| Graphiti unavailable | High | Medium | Timeout + graceful fallback |
| Memory write quality | Unknown | High | Design post-task pipeline |
| Performance overhead | Medium | Medium | Lazy loading + caching |

---

## NEXT ACTIONS (NO MORE ARCHITECTURE)

1. ⏹️ STOP designing architecture
2. ✅ Start Milestone 1 (create data models)
3. ⚠️ Verify condenser call order
4. ⚠️ Research OpenHands extension mechanism
5. ⚠️ Design memory write pipeline (after retrieval works)

---

## PROJECT BOARD

### TODO
- [ ] Verify condenser call order
- [ ] Research OpenHands plugin mechanism
- [ ] Create Memory data model
- [ ] Create MockBackend
- [ ] Create ContextBuilder
- [ ] Create IntentClassifier
- [ ] Create MemoryProvider
- [ ] Create GraphitiBackend
- [ ] Modify Agent.step()
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Write E2E tests

### IN PROGRESS
- None (architecture complete)

### BLOCKED
- None yet

---

## FINAL STATUS

**Architecture:** Implementation-ready
**Uncertainty:** Medium (condenser order, write pipeline)
**Risk:** Manageable

**Recommendation:** 
Stop designing. Start building Milestone 1.
Measure results, don't theorize about architecture.
