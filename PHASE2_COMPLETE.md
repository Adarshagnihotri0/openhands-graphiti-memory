# PHASE 2 COMPLETE: Execution Path Traced

## EVIDENCE-BASED EXECUTION FLOW

### Complete Request Path (VERIFIED with source code)

```
HTTP Request
  ↓
[agent_server/conversation_router.py] HTTP endpoint
  ↓
[agent_server/conversation_service.py] Business logic
  ↓
[sdk/agent/agent.py:613] Agent.step()
  ↓
[sdk/agent/agent.py:651] prepare_llm_messages(view, condenser, llm)
  ↓
[sdk/agent/utils.py:594] LLMConvertibleEvent.events_to_messages(events)
  ↓
[sdk/agent/agent.py:691] make_llm_completion(llm, messages, tools)
  ↓
[sdk/agent/utils.py:645] llm.completion(messages, tools, call_context)
  ↓
[sdk/llm/llm.py] LLM API call
```

---

## CRITICAL INTEGRATION POINTS

### Point 1: `prepare_llm_messages()` - Line 651 in agent.py

**Field**: Function that converts View to messages
- **Value**: `prepare_llm_messages(view, condenser, llm)`
- **Quote**: Line 651 in `/Users/adarshagnihotri/.cache/uv/archive-v0/6IutzZ5k9UG5GtZO/lib/python3.13/site-packages/openhands/sdk/agent/agent.py`
- **Source**: Verified by code inspection

**This is WHERE messages are finalized before LLM call.**

### Point 2: `View.events` - Line 577 in utils.py

**Field**: Source of conversation events
- **Value**: `view.events` (list of LLMConvertibleEvent)
- **Quote**: Line 577 in `/Users/adarshagnihotri/.cache/uv/archive-v0/6IutzZ5k9UG5GtZO/lib/python3.13/site-packages/openhands/sdk/agent/utils.py`
- **Source**: Verified by code inspection

**This is WHAT gets converted to messages.**

### Point 3: `Condenser.condense()` - Line 584 in utils.py

**Field**: Context window management
- **Value**: `condenser.condense(view, agent_llm=llm)`
- **Quote**: Line 584 in `/Users/adarshagnihotri/.cache/uv/archive-v0/6IutzZ5k9UG5GtZO/lib/python3.13/site-packages/openhands/sdk/agent/utils.py`
- **Source**: Verified by code inspection

**This is WHERE context is condensed.**

---

## INTEGRATION OPTIONS EVALUATION

### Option A: Modify `prepare_llm_messages()`

**Evidence:**
- Function signature shows it accepts `view` and returns `messages`
- Located at utils.py:548-600
- Called by `Agent.step()` at agent.py:651

**Pros:**
- Central location for message preparation
- Already handles `additional_messages` parameter
- Called before every LLM completion

**Cons:**
- Modifies utils.py (medium invasiveness)

**Implementation:**
```python
def prepare_llm_messages(
    view: View,
    condenser: CondenserBase | None = None,
    additional_messages: list[Message] | None = None,
    llm: LLM | None = None,
    memory_context: str | None = None,  # ADD THIS
) -> list[Message] | Condensation:
    # ... existing code ...
    
    messages = LLMConvertibleEvent.events_to_messages(llm_convertible_events)
    
    # INJECT MEMORY HERE
    if memory_context:
        messages.insert(1, Message(
            role="system",
            content=[TextContent(text=memory_context)]
        ))
    
    if additional_messages:
        messages.extend(additional_messages)
    
    return messages
```

---

### Option B: Modify `Agent.step()`

**Evidence:**
- Located at agent.py:613 (step), 798 (astep)
- Already calls `prepare_llm_messages()` at line 651
- Handles conversation state and context

**Pros:**
- Orchestration layer
- Can conditionally inject memory based on conversation
- Access to conversation state

**Cons:**
- More invasive
- Would need to modify both sync and async versions

**Implementation:**
```python
def step(self, conversation: LocalConversation, ...):
    # ... existing code ...
    
    # RETRIEVE MEMORY BEFORE PREPARING MESSAGES
    memory_context = await memory_integration.retrieve(
        task=conversation.state.last_user_message,
        scope=conversation.workspace
    )
    
    _messages = prepare_llm_messages(
        state.view, 
        condenser=self.condenser, 
        llm=self.llm,
        additional_messages=[Message(
            role="system",
            content=[TextContent(text=memory_context)]
        )] if memory_context else None
    )
    
    # ... existing code ...
```

---

### Option C: Add Custom Condenser

**Evidence:**
- Condensers implement `CondenserBase`
- Called at utils.py:584
- Can transform `view.events` before message conversion

**Pros:**
- Non-invasive (adds new class)
- Uses existing mechanism
- Called before every LLM call

**Cons:**
- Condenser intended for context window management
- Not semantically correct for memory injection

---

### Option D: Modify View.events

**Evidence:**
- View contains events at sdk/context/view/view.py
- Events converted to messages at utils.py:594
- View is passed to condenser at utils.py:584

**Pros:**
- Memory becomes part of event history
- Natural integration point

**Cons:**
- View is treated as read-only (documented)
- Would require event system modification

---

## PROOF: What Gets Sent to LLM

**Field**: Final message structure
- **Value**: List of `Message` objects created by `LLMConvertibleEvent.events_to_messages()`
- **Quote**: Line 594 in utils.py shows `messages = LLMConvertibleEvent.events_to_messages(llm_convertible_events)`
- **Source**: Code inspection confirmed

**Message structure:**
```python
messages = [
    Message(role="system", content=[TextContent(text=system_prompt)]),
    Message(role="user", content=[TextContent(text=user_message)]),
    Message(role="assistant", content=[TextContent(text=assistant_response)]),
    # ... more messages ...
]
```

---

## RECOMMENDATION

**Based on evidence, Option A (modify `prepare_llm_messages()`) is best:**

1. ✅ **Automatic**: Called before every LLM completion
2. ✅ **Context-aware**: Has access to view and condenser
3. ✅ **Medium invasiveness**: Single function modification
4. ✅ **Already accepts additional_messages**: Native parameter for injection
5. ✅ **Called from Agent.step()**: Verified at agent.py:651

**Integration point:**
```
Agent.step() → prepare_llm_messages() → make_llm_completion() → llm.completion()
```

**Exact injection location:** utils.py:594 (right after events_to_messages)

---

## NEXT STEPS

1. ✓ Traced execution path (DONE)
2. ✓ Identified integration points (DONE)
3. ⏳ Implement memory integration at `prepare_llm_messages()`
4. ⏳ Test with actual conversation
5. ⏳ Verify automatic retrieval works

---

## FILES TO MODIFY

**Primary:**
- `/Users/adarshagnihotri/.cache/uv/archive-v0/6IutzZ5k9UG5GtZO/lib/python3.13/site-packages/openhands/sdk/agent/utils.py`
- Lines 548-600 (prepare_llm_messages function)

**Pattern:**
Memory injection happens at line 594, immediately after:
```python
messages = LLMConvertibleEvent.events_to_messages(llm_convertible_events)
```

Insert before:
```python
if additional_messages:
    messages.extend(additional_messages)
```

---

## ARCHITECTURAL VERDICT

**This is a message-driven system.**

Memory integration should:
- **Inject into messages list** (via prepare_llm_messages)
- **Add as system message** (role="system")
- **Happen before every LLM call** (automatic via Agent.step)

**NO HOOKS NEEDED** - Use existing `prepare_llm_messages()` mechanism.
