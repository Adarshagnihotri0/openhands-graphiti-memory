# MILESTONE 0: INTEGRATION VALIDATION PLAN

## HYPOTHESIS TO TEST

**Hypothesis 1:** Injecting a memory block through `additional_messages` improves task quality.

**Test:** Can we prove the integration point works BEFORE building the subsystem?

---

## MILESTONE 0 APPROACH

### Step 1: Create Fake Provider
✅ DONE - `fake_memory_provider.py` created and tested

**What it does:**
- Returns ONE hardcoded memory
- No Graphiti, no backend, no complexity
- Pure integration test

---

### Step 2: Patch Agent (MANUAL)

**File to modify:**
```
/Users/adarshagnihotri/.cache/uv/archive-v0/6IutzZ5k9UG5GtZO/lib/python3.13/site-packages/openhands/sdk/agent/agent.py
```

**Changes:**
1. Add field: `self.memory_provider = None` in `__init__`
2. Modify line ~651 in `Agent.step()`
3. Modify line ~840 in `Agent.astep()`

⚠️ **NOTE:** Cannot modify programmatically - read-only location

---

### Step 3: Run E2E Validation

**Test script:**
```python
from openhands.sdk.agent import Agent
from openhands.sdk.llm import LLM
from openhands.sdk.conversation import LocalConversation
from fake_memory_provider import FakeMemoryProvider

# Create agent with fake provider
agent = Agent(llm=my_llm)
agent.memory_provider = FakeMemoryProvider()

# Create test conversation
conversation = LocalConversation(workspace="/tmp/test_milestone0")

# Send architecture question
conversation.send_message("Explain the auth architecture")

# Run agent
await agent.astep(conversation, my_callback)

# CHECK: Did model receive memory?
# Check conversation.state.view.events for memory content
```

---

### Step 4: VERIFY BEHAVIOR

**Success Criteria:**
- ✅ No exceptions
- ✅ Memory block appears in messages
- ✅ Model references "AuthService depends on TokenService"
- ✅ Memory survives condensation

**Failure Indicators:**
- ❌ Exception during Agent.step()
- ❌ No memory in message list
- ❌ Model doesn't reference injected knowledge

---

## VALIDATION CHECKLIST

### Pre-Patch
- [ ] Backup original agent.py
- [ ] Review patch locations (lines 651, 840)
- [ ] Understand changes needed

### During Patch
- [ ] Add memory_provider field in __init__
- [ ] Modify Agent.step() at line 651
- [ ] Modify Agent.astep() at line 840
- [ ] Verify no syntax errors

### Post-Patch
- [ ] Run fake_memory_provider.py test
- [ ] Create test conversation
- [ ] Run Agent.astep() with fake provider
- [ ] Inspect message list for memory content
- [ ] Verify model uses memory in response

---

## EVIDENCE TO COLLECT

### What to Measure

**Integration Success:**
```
Memory injected: ✅ Yes / ❌ No
Message count before memory: X
Message count after memory: X + 1
Memory content: "# Relevant Project Knowledge\n..."
```

**Model Behavior:**
```
Model references AuthService: ✅ Yes / ❌ No
Model references TokenService: ✅ Yes / ❌ No
Model references memory content: ✅ Yes / ❌ No
```

**Error Handling:**
```
Exception count: 0
Warning messages: 0
Graceful fallback works: ✅ Yes
```

---

## NEXT STEPS AFTER VALIDATION

### IF SUCCESS ✅

**Proceed to Milestone 1:** Core models
- Replace FakeMemoryProvider with real MemoryProvider
- Implement Memory data structure
- Add MockBackend

**We now know:**
- Integration point works
- additional_messages parameter works
- Memory survives condensation
- Model receives memory

### IF FAILURE ❌

**DO NOT PROCEED** - Debug and fix:
- Check patch locations (lines 651, 840)
- Verify additional_messages parameter usage
- Check message format
- Test with simpler memory block

**Root cause analysis:**
- Is memory_provider being called?
- Is memory returned correctly?
- Is memory added to message list?
- Does memory reach the LLM?

---

## SUCCESS METRICS

### Milestone 0 Success
- **Binary outcome:** Works / Doesn't work
- **Time to validate:** 1-2 hours
- **Code change:** 3 lines in agent.py + fake_memory_provider.py

### Failure Is OK
- If integration fails, we learned something
- Better to fail early with fake provider
- No wasted effort building subsystem

---

## LESSONS FROM MILESTONE 0

### What We're Testing
1. **Integration point validity** - Does additional_messages work?
2. **Condenser safety** - Does memory survive condensation?
3. **Model behavior** - Does model use injected memory?
4. **Error tolerance** - Can we handle failures gracefully?

### What We're NOT Testing (Yet)
- Graphiti integration (that's Milestone 6)
- Token budgeting (that's Milestone 3)
- Intent classification (that's Milestone 4)
- Repository scoping (that's Milestone 6)

**Focus:** PROVE integration works FIRST

---

## HYPOTHESIS TRACKING

### Hypothesis 1: Integration Point Works
**Test:** Inject fake memory, verify model receives it
**Status:** VALIDATION IN PROGRESS
**Evidence:** Pending manual patch and E2E test

---

## MILESTONE 0 STATUS

- ✅ Fake provider created
- ✅ Fake provider tested
- ⏳ Agent patch pending (manual)
- ⏳ E2E validation pending
- ⏳ Evidence collection pending

**CURRENT ACTION:** Apply manual patch to agent.py

---

## MILESTONE 0 COMPLETE WHEN

1. ✅ FakeMemoryProvider injects memory
2. ✅ Agent.step() uses additional_messages
3. ✅ Memory appears in LLM request
4. ✅ Model references memory content
5. ✅ No crashes when memory_provider is None

**THEN:** Proceed to Milestone 1 (Core models)
