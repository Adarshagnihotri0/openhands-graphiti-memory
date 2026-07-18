"""
MILESTONE 0: Fake Memory Provider

Purpose: PROVE the integration point works BEFORE building the subsystem.

This is a hardcoded provider that injects one test memory.
If this works, we know the Agent.step() → additional_messages path is correct.
"""

from openhands.sdk.llm import Message, TextContent


class FakeMemoryProvider:
    """Hardcoded memory provider for Milestone 0 validation."""
    
    async def retrieve(
        self,
        conversation,
        state
    ) -> list[Message] | None:
        """
        Return one hardcoded memory.
        
        This proves:
        1. additional_messages parameter works
        2. Message is injected AFTER condenser
        3. Model receives and uses the memory
        """
        
        # Single hardcoded test memory
        memory_text = """# Relevant Project Knowledge

## Architecture
• AuthService depends on TokenService for JWT validation.
• All API routes flow through Gateway middleware.

## Conventions
• Never call repositories directly from controllers.
• Use Result<T> pattern for error handling.

Use this information if relevant."""
        
        return [
            Message(
                role="system",
                content=[TextContent(text=memory_text)]
            )
        ]
    
    def retrieve_sync(
        self,
        conversation,
        state
    ) -> list[Message] | None:
        """Sync version for Agent.step()."""
        return self.retrieve.__wrapped__(self, conversation, state)


# Integration patch for Agent (Milestone 0 test)
"""
# In Agent.__init__:
from fake_memory_provider import FakeMemoryProvider
self.memory_provider = FakeMemoryProvider()

# In Agent.step() at line 651:
memory_messages = None
if self.memory_provider:
    try:
        memory_messages = self.memory_provider.retrieve_sync(conversation, state)
    except Exception as e:
        logger.warning(f"Memory retrieval failed: {e}")

_messages_or_condensation = prepare_llm_messages(
    state.view, 
    condenser=self.condenser, 
    llm=self.llm,
    additional_messages=memory_messages  # ← INJECT HERE
)

# In Agent.astep() at line 840:
memory_messages = None
if self.memory_provider:
    try:
        memory_messages = await self.memory_provider.retrieve(conversation, state)
    except Exception as e:
        logger.warning(f"Memory retrieval failed: {e}")

_messages_or_condensation = await aprepare_llm_messages(
    state.view,
    condenser=self.condenser,
    llm=self.llm,
    additional_messages=memory_messages  # ← INJECT HERE
)
"""


# Validation test
async def test_fake_provider_injects():
    """Verify fake provider injects memory."""
    provider = FakeMemoryProvider()
    
    messages = await provider.retrieve(None, None)
    
    assert messages is not None
    assert len(messages) == 1
    assert messages[0].role == "system"
    assert "AuthService depends on TokenService" in messages[0].content[0].text
    print("✅ Fake provider works")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_fake_provider_injects())
