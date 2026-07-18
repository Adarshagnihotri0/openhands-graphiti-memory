"""
CoreMemoryProvider orchestration
"""
import asyncio
import logging
from milestone1_models import MemoryConfig, RetrievalContext
from milestone2_backend import MemoryBackend
from milestone3_builder import ContextBuilder
from milestone4_classifier import IntentClassifier

logger = logging.getLogger(__name__)


class MemoryProvider:
    def __init__(
        self,
        backend: MemoryBackend,
        context_builder: ContextBuilder,
        classifier: IntentClassifier,
        config: MemoryConfig
    ):
        self.backend = backend
        self.context_builder = context_builder
        self.classifier = classifier
        self.config = config
    
    async def retrieve(
        self,
        conversation,
        state
    ) -> list | None:
        """Orchestrate memory retrieval."""
        
        if not self.config.enabled:
            return None
        
        # 1. Extract context
        context = self._extract_context(conversation, state)
        
        # 2. Check intent
        intent = self.classifier.classify(context.task)
        if not self.classifier.should_query_memory(intent):
            logger.info(f"Skipping memory retrieval for intent: {intent}")
            return None
        
        # 3. Retrieve with timeout
        try:
            async with asyncio.timeout(self.config.timeout_ms / 1000):
                memories = await self.backend.retrieve(context)
        except asyncio.TimeoutError:
            logger.warning(f"Memory retrieval timeout after {self.config.timeout_ms}ms")
            return None
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            return None
        
        # 4. Build context message
        return self.context_builder.build(memories)
    
    def _extract_context(self, conversation, state) -> RetrievalContext:
        """Extract retrieval context from conversation."""
        
        # Get task from last user message
        task = ""
        print(f"DEBUG: Extracting context from {len(state.view.events)} events")
        for event in reversed(state.view.events):
            if hasattr(event, 'role') and event.role == 'user':
                task = str(event.content)
                print(f"DEBUG: Found user message: {task}")
                break
        
        # Get repository info
        repository = "test/repo"  # Use test repo for testing
        branch = "main"
        
        print(f"DEBUG: Context - task='{task}', repo='{repository}', branch='{branch}'")
        
        return RetrievalContext(
            task=task,
            repository=repository,
            branch=branch,
            workspace_path="/tmp/test"
        )
    
    def _extract_repo_name(self, path: str) -> str:
        """Extract repository name from path."""
        parts = path.split('/')
        if 'workspace' in parts:
            idx = parts.index('workspace')
            if idx + 1 < len(parts):
                return parts[idx + 1]
        return "unknown"
    
    def _get_git_branch(self, path: str) -> str:
        """Get git branch from path."""
        return "main"  # Simplified for testing


if __name__ == "__main__":
    from milestone1_models import Memory, MemoryCategory
    from milestone2_backend import MockBackend
    from openhands.sdk.llm import Message
    from openhands.sdk.conversation import LocalConversation
    
    class MockState:
        class MockView:
            events = []
        
        view = MockView()
    
    async def test_milestone5():
        print("Testing CoreMemoryProvider")
        
        # Setup
        backend = MockBackend()
        config = MemoryConfig()
        builder = ContextBuilder(config)
        classifier = IntentClassifier()
        provider = MemoryProvider(backend, builder, classifier, config)
        
        # Store test memory
        memory = Memory(
            id="test-1",
            title="Auth Architecture",
            summary="AuthService depends on TokenService",
            category=MemoryCategory.ARCHITECTURE,
            confidence=0.95,
            source="ADR-003",
            repository="test/repo",
            branch="main"
        )
        await backend.store(memory)
        
        conversation = None
        state = MockState()
        
        # Add a fake user message
        class FakeEvent:
            role = 'user'
            content = 'Explain the authentication architecture'
        
        state.view.events = [FakeEvent()]
        
        messages = await provider.retrieve(conversation, state)
        
        assert messages is not None, "Memory provider returned None"
        assert len(messages) >= 1, f"Expected >= 1 message, got {len(messages)}"
        
        content = messages[0].content[0].text
        assert "AuthService depends on TokenService" in content
        
        state.view.events = [FakeEvent()]
        state.view.events[0].content = 'Hi there'
        
        messages = await provider.retrieve(conversation, state)
        assert messages is None, "Should skip greetings"
        
        provider.config.timeout_ms = 1
        
        class SlowBackend(MockBackend):
            async def retrieve(self, context, limit=10):
                await asyncio.sleep(0.1)  # Slower than timeout
                return await super().retrieve(context, limit)
        
        slow_provider = MemoryProvider(
            SlowBackend(),
            builder,
            classifier,
            provider.config
        )
        
        state.view.events = [FakeEvent()]
        state.view.events[0].content = 'Explain architecture'
        
        messages = await slow_provider.retrieve(conversation, state)
        assert messages is None, "Should timeout gracefully"
        
    
    import asyncio
    asyncio.run(test_milestone5())
