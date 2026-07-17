# CORRECTED ARCHITECTURE - Clean Separation of Concerns

## PROBLEM WITH PREVIOUS APPROACH

**Issue:** Coupling message preparation with memory retrieval

```python
# WRONG - couples prepare_llm_messages to Graphiti
def prepare_llm_messages(view, condenser, llm):
    messages = events_to_messages(view.events)
    memory = get_memory()  # ❌ Network call in message formatter
    messages.insert(memory)  # ❌ Side effects
    return messages
```

**Why it's bad:**
- `prepare_llm_messages()` becomes impure
- Couples formatting to networking/storage/ranking
- Hard to test
- Hard to cache
- No timeout control

---

## CORRECT ARCHITECTURE

### Layered Approach

```text
Agent.step()
    ↓
Conversation (has workspace, state, etc.)
    ↓
MemoryProvider.retrieve(conversation, task) ← NEW LAYER
    ↓
    ├─ Check should_query_memory(task)
    ├─ Timeout control
    ├─ Async retrieval
    └─ Graceful fallback
    ↓
additional_messages (list[Message])
    ↓
prepare_llm_messages(view, condenser, llm, additional_messages)
    ↓
LLM
```

---

## EVIDENCE-BASED IMPLEMENTATION POINTS

### Point 1: Where to Inject (Agent.step)

**Evidence:**
- **File**: agent.py
- **Lines**: 651-653 (sync), 840-842 (async)
- **Quote**: 
```python
_messages_or_condensation = prepare_llm_messages(
    state.view, condenser=self.condenser, llm=self.llm
)
```
- **Source**: Code inspection verified

**Shows:** `additional_messages` parameter NOT USED (perfect injection point)

### Point 2: Context Available (Conversation object)

**Evidence:**
- **Field**: Conversation has workspace
- **Value**: `conversation.workspace` (LocalWorkspace)
- **Quote**: Line 147 in local_conversation.py shows `workspace: LocalWorkspace`
- **Source**: Class definition confirmed

**Shows:** Full task context available at injection point

### Point 3: State Has Last User Message

**Evidence:**
- **Field**: Last user message ID
- **Value**: `state.last_user_message_id`
- **Quote**: Line 633 in agent.py shows `state.last_user_message_id`
- **Source**: Agent.step() code verified

**Shows:** Can extract current task from conversation state

---

## IMPLEMENTATION DESIGN

### 1. MemoryProvider Interface

```python
class MemoryProvider:
    """Clean interface for memory retrieval."""
    
    async def retrieve(
        self,
        conversation: LocalConversation,
        state: ConversationState,
    ) -> list[Message] | None:
        """Retrieve relevant memories as system messages."""
        
        # Extract task context
        task = self._extract_task(state)
        
        # Check if memory retrieval needed
        if not self._should_query_memory(task):
            return None
        
        # Timeout-controlled retrieval
        try:
            async with asyncio.timeout(self.timeout_ms / 1000):
                memories = await self._query_graphiti(task, conversation.workspace)
                return self._format_as_system_messages(memories)
        except asyncio.TimeoutError:
            logger.warning(f"Memory retrieval timed out after {self.timeout_ms}ms")
            return None
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            return None
```

### 2. Inject in Agent.step()

```python
def step(self, conversation: LocalConversation, ...):
    state = conversation.state
    
    # ... existing code ...
    
    call_context: LLMCallContext = conversation.get_llm_call_context()
    
    # INJECT MEMORY HERE - use existing additional_messages parameter
    memory_messages = await self.memory_provider.retrieve(conversation, state)
    
    _messages_or_condensation = prepare_llm_messages(
        state.view, 
        condenser=self.condenser, 
        llm=self.llm,
        additional_messages=memory_messages  # ← USE EXISTING PARAMETER
    )
    
    # ... rest of existing code ...
```

### 3. Should Query Memory Logic

```python
def _should_query_memory(self, task: str) -> bool:
    """Determine if memory retrieval is needed."""
    
    # Skip for simple conversational exchanges
    trivial_patterns = [
        r"^(hi|hello|hey|good morning|good afternoon)",
        r"^(thanks|thank you|please|sorry)",
        r"^(can you|could you|would you|will you)",
    ]
    
    task_lower = task.lower()
    
    for pattern in trivial_patterns:
        if re.match(pattern, task_lower):
            return False
    
    # Check if task requires context
    context_patterns = [
        r"(architecture|design|component|module|service)",
        r"(bug|fix|issue|error|debug)",
        r"(implement|create|build|develop)",
        r"(explain|understand|analyze)",
        r"(convention|pattern|practice|standard)",
    ]
    
    for pattern in context_patterns:
        if re.search(pattern, task_lower):
            return True
    
    return False
```

---

## WHY THIS IS BETTER

### 1. Separation of Concerns

```
prepare_llm_messages: View → Messages (pure)

MemoryProvider.retrieve: Conversation → System Messages (side effects)
```

### 2. Testable

```python
# Can test memory provider independently
provider = MemoryProvider()
messages = await provider.retrieve(mock_conversation, mock_state)
assert len(messages) > 0

# Can test message preparation independently
messages = prepare_llm_messages(view, condenser, llm)
assert len(messages) > 0
```

### 3. Observable

```python
# Can log retrieval separately
logger.info(f"Memory retrieval took {latency_ms}ms")
logger.info(f"Retrieved {count} memories")
```

### 4. Fault Tolerant

```python
# Timeouts and fallbacks are isolated
try:
    async with timeout(500):
        memories = await retrieve()
except TimeoutError:
    return None  # Continue without memory
```

### 5. Configurable

```python
# Can disable memory without code changes
if config.disable_memory:
    provider = NoOpMemoryProvider()
```

---

## INTEGRATION LAYER COMPARISON

| Aspect | Direct Modification | MemoryProvider Layer |
|--------|---------------------|---------------------|
| **Separation** | ❌ Couple formatting + retrieval | ✅ Clean separation |
| **Testability** | ❌ Hard to mock | ✅ Easy to mock |
| **Observability** | ❌ Scattered logs | ✅ Centralized metrics |
| **Fault tolerance** | ❌ No timeout control | ✅ Timeout + fallback |
| **Configurability** | ❌ Requires code change | ✅ Provider swapping |
| **Performance** | ❌ Every request | ✅ Conditional retrieval |

---

## FILES TO MODIFY

### Primary
```python
# Agent class - inject memory retrieval
/Users/adarshagnihotri/.cache/uv/archive-v0/6IutzZ5k9UG5GtZO/lib/python3.13/site-packages/openhands/sdk/agent/agent.py

# Lines to modify:
# - Line 651-653 (step)
# - Line 840-842 (astep)
```

### New Files to Create
```python
# Memory provider implementation
graphiti_memory/integration/memory_provider.py

# Memory provider interface
graphiti_memory/integration/base.py
```

---

## MIGRATION PATH

### Phase 1: Create MemoryProvider
- Implement clean interface
- Add should_query_memory logic
- Add timeout control
- Add fallback handling

### Phase 2: Register with Agent
- Add memory_provider field to Agent class
- Initialize in Agent.__init__

### Phase 3: Inject in Agent.step()
- Retrieve memory before prepare_llm_messages
- Pass via additional_messages parameter

### Phase 4: Test End-to-End
- Verify automatic retrieval
- Verify performance
- Verify fallback behavior

---

## TASK CONTEXT AVAILABILITY

**Evidence:**
- `conversation.workspace` contains working directory
- `state.last_user_message_id` gives task ID
- Can extract full task from events

**Implementation:**
```python
def _extract_task(self, state: ConversationState) -> str:
    """Extract current task from conversation state."""
    # Get last user message
    for event in reversed(state.view.events):
        if event.kind == "user_message":
            return event.content
    return ""
```

---

## ARCHITECTURAL VERDICT

**This IS the correct integration point:**

1. ✅ **Uses existing extension point** (additional_messages)
2. ✅ **Preserves separation of concerns**
3. ✅ **Has full task context** (conversation + workspace + state)
4. ✅ **Called before every LLM request**
5. ✅ **Can implement timeout + fallback cleanly**

**Previous approach was wrong because:**
- Coupled message formatting to network I/O
- Violated single responsibility
- Made testing difficult
- No performance isolation

**This approach is right because:**
- Clean layered architecture
- Testable components
- Observable and configurable
- Graceful degradation
