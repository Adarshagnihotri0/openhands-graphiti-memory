"""
MILESTONE 0 AGENT PATCH

This is the SMALLEST POSSIBLE PATCH to Agent.step() and Agent.astep().
It proves the integration point works.

Copy these modifications to:
/Users/adarshagnihotri/.cache/uv/archive-v0/6IutzZ5k9UG5GtZO/lib/python3.13/site-packages/openhands/sdk/agent/agent.py
"""


# ============================================================================
# PATCH 1: Agent.__init__ (add memory_provider field)
# ============================================================================

"""
In Agent.__init__ method, add:

def __init__(
    self,
    llm: LLM,
    ...
):
    # ... existing initialization ...
    
    # === MILESTONE 0: Add memory provider ===
    self.memory_provider: MemoryProvider | None = None
    # ==========================================
"""


# ============================================================================
# PATCH 2: Agent.step() at line ~651
# ============================================================================

"""
Around line 651, modify the prepare_llm_messages call:

BEFORE:
    _messages_or_condensation = prepare_llm_messages(
        state.view, condenser=self.condenser, llm=self.llm
    )

AFTER:
    # === MILESTONE 0: Inject memory (sync) ===
    memory_messages = None
    if self.memory_provider:
        try:
            import asyncio
            memory_messages = self.memory_provider.retrieve_sync(conversation, state)
        except Exception as e:
            logger.warning(f"Memory retrieval failed: {e}")
    # ==========================================
    
    _messages_or_condensation = prepare_llm_messages(
        state.view, 
        condenser=self.condenser, 
        llm=self.llm,
        additional_messages=memory_messages  # ← USE EXISTING PARAMETER
    )
"""


# ============================================================================
# PATCH 3: Agent.astep() at line ~840
# ============================================================================

"""
Around line 840, modify the aprepare_llm_messages call:

BEFORE:
    _messages_or_condensation = await aprepare_llm_messages(
        state.view, condenser=self.condenser, llm=self.llm
    )

AFTER:
    # === MILESTONE 0: Inject memory (async) ===
    memory_messages = None
    if self.memory_provider:
        try:
            memory_messages = await self.memory_provider.retrieve(conversation, state)
        except Exception as e:
            logger.warning(f"Memory retrieval failed: {e}")
    # ==========================================
    
    _messages_or_condensation = await aprepare_llm_messages(
        state.view,
        condenser=self.condenser,
        llm=self.llm,
        additional_messages=memory_messages  # ← USE EXISTING PARAMETER
    )
"""


# ============================================================================
# VALIDATION TEST
# ============================================================================

"""
To validate this works:

1. Patch Agent class with the changes above
2. Create a test conversation with architecture question
3. Initialize agent with fake provider:

    from fake_memory_provider import FakeMemoryProvider
    
    agent = Agent(llm=my_llm)
    agent.memory_provider = FakeMemoryProvider()

4. Run agent.step(conversation, callback)
5. Check events for memory content in LLM request

Expected result:
- Memory block appears in messages sent to LLM
- Model references "AuthService depends on TokenService"
- No crashes if memory_provider is None

This proves:
✅ Integration point works
✅ additional_messages parameter works
✅ Memory survives condensation
✅ Model receives memory context
"""


# ============================================================================
# MANUAL PATCH INSTRUCTIONS
# ============================================================================

"""
STEP 1: Backup original file
```bash
cp ~/.cache/uv/archive-v0/6IutzZ5k9UG5GtZO/lib/python3.13/site-packages/openhands/sdk/agent/agent.py \
   ~/.cache/uv/archive-v0/6IutzZ5k9UG5GtZO/lib/python3.13/site-packages/openhands/sdk/agent/agent.py.backup
```

STEP 2: Apply patches (use text editor)
- Add field in __init__: self.memory_provider = None
- Modify Agent.step() at line ~651
- Modify Agent.astep() at line ~840

STEP 3: Test with fake provider
```python
from openhands.sdk.agent import Agent
from openhands.sdk.conversation import LocalConversation
from fake_memory_provider import FakeMemoryProvider

agent = Agent(llm=my_llm)
agent.memory_provider = FakeMemoryProvider()

conversation = LocalConversation(workspace="/tmp/test")
conversation.send_message("Explain the auth architecture")

await agent.astep(conversation, my_callback)
```

STEP 4: Verify memory appears
Check conversation.state.view.events for memory content in LLM request.

SUCCESS CRITERIA:
- No exceptions
- Memory block in messages
- Model responds with knowledge of AuthService/TokenService

IF SUCCESS: Integration point proven ✅
IF FAILURE: Debug and fix before proceeding
"""

print(__doc__)
