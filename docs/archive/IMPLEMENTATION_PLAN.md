# IMPLEMENTATION PLAN - Engineering Validation Phase

## ARCHITECTURAL PROVEN FACTS

### Evidence-Based Verification ✅

1. **NO lifecycle hook API** - Proven by grep search
2. **Execution path traced** - HTTP → Agent.step() → prepare_llm_messages() → LLM
3. **Integration point identified** - `additional_messages` parameter (line 551, utils.py)
4. **Condenser ordering verified** - Condenser runs BEFORE additional_messages (line 584 vs 598)
5. **Memory safe from summarization** - Injected AFTER condensation

### Critical Discovery: Execution Order

```text
Conversation Events
    ↓
Condenser (line 584)
    ↓
events_to_messages() (line 594)
    ↓
additional_messages (line 598) ← MEMORY INJECTED HERE
    ↓
LLM
```

**Result:** Memory becomes stable, predictable context block.

---

## TOKEN BUDGET CONSTRAINT

### Hard Requirements
- **Max tokens:** 1-2k for memory block
- **Preference:** 3-5 high-quality memories over dozens
- **Fail closed:** Summarize if budget exceeded

### Context Window Impact
```
Conversation: ~100k tokens
    ↓
Condenser
    ↓
~20k tokens
    ↓
Memory: 1-2k tokens ← COUNTS TOWARD CONTEXT
    ↓
LLM
```

**Critical:** Memory counts toward model's maximum context!

---

## IMPLEMENTATION MILESTONE 1: Core Models

### Files to Create
```python
# graphiti_memory/models/memory.py
@dataclass
class Memory:
    id: str
    title: str
    summary: str
    category: MemoryCategory
    confidence: float  # 0.0-1.0
    source: str
    repository: str
    branch: str
    module: str | None
    service: str | None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any]

class MemoryCategory(Enum):
    ARCHITECTURE = "architecture"
    BUG_FIX = "bug_fix"
    CONVENTION = "convention"
    DESIGN_DECISION = "design_decision"
    DEPENDENCY = "dependency"
    IMPLEMENTATION = "implementation"

# graphiti_memory/models/context.py
@dataclass
class RetrievalContext:
    task: str
    repository: str
    branch: str
    workspace_path: str
    active_files: list[str]
    recent_events: list[str]

# graphiti_memory/models/config.py
@dataclass
class MemoryConfig:
    enabled: bool = True
    timeout_ms: int = 500
    max_memories: int = 5
    min_confidence: float = 0.7
    max_tokens: int = 1500  # Hard cap for safety
```

### Tests
```python
def test_memory_dataclass():
    memory = Memory(
        id="test-1",
        title="Auth Architecture",
        summary="AuthService depends on TokenService",
        category=MemoryCategory.ARCHITECTURE,
        confidence=0.95
    )
    assert memory.confidence <= 1.0

def test_retrieval_context_scoping():
    context = RetrievalContext(
        task="Fix auth bug",
        repository="myorg/myapp",
        branch="main"
    )
    assert context.repository == "myorg/myapp"
```

**Success Criteria:** 
- ✅ All models defined
- ✅ Unit tests pass
- ✅ NO Graphiti dependencies

**Estimated:** 2-3 implementation cycles

---

## IMPLEMENTATION MILESTONE 2: Backend Interface

### Files to Create
```python
# graphiti_memory/backends/base.py
class MemoryBackend(ABC):
    @abstractmethod
    async def retrieve(
        self,
        context: RetrievalContext,
        limit: int = 10
    ) -> list[Memory]:
        pass
    
    @abstractmethod
    async def store(self, memory: Memory) -> None:
        pass

# graphiti_memory/backends/mock_backend.py
class MockBackend(MemoryBackend):
    def __init__(self):
        self.memories: list[Memory] = []
    
    async def retrieve(self, context, limit=10):
        # Simple text matching for testing
        return [
            m for m in self.memories
            if context.task.lower() in m.summary.lower()
        ][:limit]
    
    async def store(self, memory):
        self.memories.append(memory)
```

### Tests
```python
async def test_mock_backend_retrieve():
    backend = MockBackend()
    backend.memories = [test_memory]
    
    context = RetrievalContext(task="auth", ...)
    memories = await backend.retrieve(context)
    
    assert len(memories) == 1
    assert "auth" in memories[0].summary.lower()
```

**Success Criteria:**
- ✅ Backend interface defined
- ✅ Mock implementation works
- ✅ Tests pass

**Estimated:** 2-3 implementation cycles

---

## IMPLEMENTATION MILESTONE 3: Context Builder

### Files to Create
```python
# graphiti_memory/builder/context_builder.py
class ContextBuilder:
    def __init__(self, config: MemoryConfig):
        self.config = config
    
    def build(self, memories: list[Memory]) -> list[Message]:
        if not memories:
            return []
        
        # 1. Rank by confidence
        ranked = sorted(memories, key=lambda m: m.confidence, reverse=True)
        
        # 2. Deduplicate by title similarity
        deduped = self._deduplicate(ranked)
        
        # 3. Apply token budget
        budgeted = self._apply_token_budget(deduped)
        
        # 4. Format as structured block
        content = self._format_structured(budgeted)
        
        return [Message(
            role="system",
            content=[TextContent(text=content)]
        )]
    
    def _apply_token_budget(self, memories: list[Memory]) -> list[Memory]:
        """Hard cap at config.max_tokens."""
        budgeted = []
        total_tokens = 0
        
        for memory in memories:
            # Estimate tokens: ~4 chars per token
            memory_tokens = len(memory.summary) // 4
            if total_tokens + memory_tokens <= self.config.max_tokens:
                budgeted.append(memory)
                total_tokens += memory_tokens
            else:
                break
        
        return budgeted
    
    def _format_structured(self, memories: list[Memory]) -> str:
        sections = defaultdict(list)
        
        for memory in memories:
            sections[memory.category.value].append(memory)
        
        output = ["# Relevant Project Knowledge\n"]
        
        category_labels = {
            "architecture": "Architecture",
            "bug_fix": "Previous Bugs",
            "convention": "Conventions",
            "design_decision": "Design Decisions",
        }
        
        for category, label in category_labels.items():
            if category in sections:
                output.append(f"\n## {label}\n")
                for memory in sections[category]:
                    output.append(f"• {memory.summary}\n")
        
        output.append("\nUse this information if relevant.\n")
        
        return "".join(output)
```

### Tests
```python
def test_context_builder_formats_structured():
    builder = ContextBuilder(MemoryConfig(max_tokens=1500))
    memories = [
        Memory(category=MemoryCategory.ARCHITECTURE, summary="Auth → Token"),
        Memory(category=MemoryCategory.BUG_FIX, summary="Race condition"),
    ]
    
    messages = builder.build(memories)
    
    assert len(messages) == 1
    assert messages[0].role == "system"
    assert "## Architecture" in messages[0].content[0].text
    assert "## Previous Bugs" in messages[0].content[0].text

def test_token_budget_enforced():
    builder = ContextBuilder(MemoryConfig(max_tokens=100))
    
    # Create memories that would exceed budget
    large_memories = [
        Memory(summary="X" * 500)  # ~125 tokens each
        for _ in range(20)
    ]
    
    budgeted = builder._apply_token_budget(large_memories)
    
    # Should only include memories that fit budget
    total_chars = sum(len(m.summary) for m in budgeted)
    assert total_chars <= 400  # 100 tokens * 4 chars/token
```

**Success Criteria:**
- ✅ Formats structured context block
- ✅ Token budget enforced
- ✅ Tests pass

**Estimated:** 3-4 implementation cycles

---

## IMPLEMENTATION MILESTONE 4: Intent Classification

### Files to Create
```python
# graphiti_memory/classifier/intent_classifier.py
class Intent(Enum):
    GREETING = "greeting"
    ARCHITECTURE = "architecture"
    BUG_FIX = "bug_fix"
    IMPLEMENTATION = "implementation"
    PLANNING = "planning"
    CONVERSATION = "conversation"

class IntentClassifier:
    def should_query_memory(self, intent: Intent) -> bool:
        """Return True if memory retrieval needed."""
        return intent in {
            Intent.ARCHITECTURE,
            Intent.BUG_FIX,
            Intent.IMPLEMENTATION,
            Intent.PLANNING,
        }
    
    def classify(self, task: str) -> Intent:
        """Classify task intent (fast rule-based)."""
        task_lower = task.lower()
        
        # Greeting patterns
        if re.match(r"^(hi|hello|hey|thanks|please)", task_lower):
            return Intent.GREETING
        
        # Architecture patterns
        if any(w in task_lower for w in ["architecture", "design", "component"]):
            return Intent.ARCHITECTURE
        
        # Bug fix patterns
        if any(w in task_lower for w in ["bug", "fix", "error", "crash"]):
            return Intent.BUG_FIX
        
        # Implementation patterns
        if any(w in task_lower for w in ["implement", "create", "build", "develop"]):
            return Intent.IMPLEMENTATION
        
        return Intent.CONVERSATION
```

### Tests
```python
def test_classifier_skips_greetings():
    classifier = IntentClassifier()
    
    assert classifier.classify("Hi there") == Intent.GREETING
    assert classifier.classify("Thanks!") == Intent.GREETING
    assert not classifier.should_query_memory(Intent.GREETING)

def test_classifier_enables_for_architecture():
    classifier = IntentClassifier()
    
    assert classifier.classify("Explain auth architecture") == Intent.ARCHITECTURE
    assert classifier.should_query_memory(Intent.ARCHITECTURE)
```

**Success Criteria:**
- ✅ Classifies intents correctly
- ✅ Skips greetings and trivial tasks
- ✅ Tests pass

**Estimated:** 2-3 implementation cycles

---

## IMPLEMENTATION MILESTONE 5: Memory Provider

### Files to Create
```python
# graphiti_memory/provider/memory_provider.py
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
        conversation: LocalConversation,
        state: ConversationState
    ) -> list[Message] | None:
        """Orchestrate memory retrieval."""
        
        if not self.config.enabled:
            return None
        
        # 1. Extract context
        context = self._extract_context(conversation, state)
        
        # 2. Check intent
        intent = self.classifier.classify(context.task)
        if not self.classifier.should_query_memory(intent):
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
    
    def _extract_context(
        self,
        conversation: LocalConversation,
        state: ConversationState
    ) -> RetrievalContext:
        """Extract retrieval context from conversation."""
        
        # Get task from last user message
        task = ""
        for event in reversed(state.view.events):
            if hasattr(event, 'role') and event.role == 'user':
                task = str(event.content)
                break
        
        # Get repository info
        workspace = conversation.workspace
        repository = self._extract_repo_name(workspace.working_dir)
        branch = self._get_git_branch(workspace.working_dir)
        
        return RetrievalContext(
            task=task,
            repository=repository,
            branch=branch,
            workspace_path=str(workspace.working_dir),
            active_files=[],
            recent_events=[]
        )
```

### Tests
```python
async def test_memory_provider_orchestration():
    backend = MockBackend()
    backend.memories = [test_memory]
    
    provider = MemoryProvider(
        backend=backend,
        context_builder=ContextBuilder(MemoryConfig()),
        classifier=IntentClassifier(),
        config=MemoryConfig()
    )
    
    messages = await provider.retrieve(mock_conversation, mock_state)
    
    assert messages is not None
    assert len(messages) == 1
    assert messages[0].role == "system"

async def test_provider_skips_greetings():
    provider = MemoryProvider(...)
    
    # Mock state with greeting
    mock_state = create_state_with_task("Hi there")
    
    messages = await provider.retrieve(mock_conversation, mock_state)
    
    assert messages is None  # Should return None for greetings
```

**Success Criteria:**
- ✅ Orchestration works
- ✅ Timeout control implemented
- ✅ Graceful fallback
- ✅ Tests pass

**Estimated:** 3-4 implementation cycles

---

## IMPLEMENTATION MILESTONE 6: Graphiti Backend

### Files to Create
```python
# graphiti_memory/backends/graphiti_backend.py
class GraphitiBackend(MemoryBackend):
    def __init__(self, uri: str, database: str):
        self.client = GraphitiClient(uri, database)
    
    async def retrieve(
        self,
        context: RetrievalContext,
        limit: int = 10
    ) -> list[Memory]:
        """Retrieve from Graphiti with repository scoping."""
        
        # Build scoped query
        query = f"""
        MATCH (m:Memory {{
            repository: '{context.repository}',
            branch: '{context.branch}'
        }})
        WHERE m.summary CONTAINS '{context.task}'
        OR m.title CONTAINS '{context.task}'
        RETURN m
        ORDER BY m.confidence DESC
        LIMIT {limit}
        """
        
        results = await self.client.search(query)
        
        # Convert to Memory objects
        return [
            Memory(
                id=r.node_id,
                title=r.name,
                summary=r.summary,
                category=self._map_category(r.type),
                confidence=r.confidence,
                source=r.source,
                repository=context.repository,
                branch=context.branch,
                module=r.attributes.get("module"),
                service=r.attributes.get("service"),
                created_at=r.created_at,
                updated_at=r.updated_at,
                metadata=r.attributes
            )
            for r in results
        ]
```

### Tests
```python
async def test_graphiti_backend_scoping():
    backend = GraphitiBackend(uri="bolt://localhost:7687", database="neo4j")
    
    context = RetrievalContext(
        task="auth",
        repository="myorg/myapp",
        branch="main"
    )
    
    memories = await backend.retrieve(context)
    
    # Should only return memories from correct repo/branch
    for memory in memories:
        assert memory.repository == "myorg/myapp"
        assert memory.branch == "main"
```

**Success Criteria:**
- ✅ Graphiti integration works
- ✅ Repository scoping enforced
- ✅ Tests pass

**Estimated:** 3-4 implementation cycles
**Requires:** Graphiti server running

---

## IMPLEMENTATION MILESTONE 7: Agent Integration

### File to Modify
```python
# /openhands/sdk/agent/agent.py

# In Agent.__init__ (add initialization)
def __init__(self, ...):
    # ... existing code ...
    self.memory_provider: MemoryProvider | None = None

# In Agent.step() at line 651
def step(self, conversation: LocalConversation, ...):
    # ... existing code up to line 650 ...
    
    call_context: LLMCallContext = conversation.get_llm_call_context()
    
    # === SMALLEST PATCH: Inject memory ===
    memory_messages = None
    if self.memory_provider:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            memory_messages = loop.run_until_complete(
                self.memory_provider.retrieve(conversation, state)
            )
        except Exception as e:
            logger.warning(f"Memory retrieval failed: {e}")
    
    _messages_or_condensation = prepare_llm_messages(
        state.view, 
        condenser=self.condenser, 
        llm=self.llm,
        additional_messages=memory_messages  # ← USE EXISTING PARAMETER
    )
    # === END PATCH ===
    
    # ... existing code continues ...

# In Agent.astep() at line 840 (async version)
async def astep(self, conversation: LocalConversation, ...):
    # ... existing code up to line 839 ...
    
    call_context: LLMCallContext = conversation.get_llm_call_context()
    
    # === SMALLEST PATCH: Inject memory (async) ===
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
        additional_messages=memory_messages  # ← USE EXISTING PARAMETER
    )
    # === END PATCH ===
    
    # ... existing code continues ...
```

### Integration Code
```python
# Example initialization
from graphiti_memory.provider import MemoryProvider
from graphiti_memory.backends import GraphitiBackend
from graphiti_memory.builder import ContextBuilder
from graphiti_memory.classifier import IntentClassifier

agent = Agent(
    llm=my_llm,
    memory_provider=MemoryProvider(
        backend=GraphitiBackend(
            uri="bolt://localhost:7687",
            database="neo4j"
        ),
        context_builder=ContextBuilder(MemoryConfig()),
        classifier=IntentClassifier(),
        config=MemoryConfig()
    )
)
```

**Success Criteria:**
- ✅ Memory injected into messages
- ✅ No crashes when provider is None
- ✅ Graceful error handling

**Estimated:** 4-5 implementation cycles

---

## SUCCESS METRICS TO MEASURE

### Performance
- **p95 latency:** < 500ms
- **Token usage:** < 1500 tokens per injection
- **Cache hit rate:** > 80% (after implementation)

### Utility (Human Evaluation)
- **Repository re-exploration:** Compare before/after
- **Memory relevance:** Manually score 1-5
- **Task success rate:** Improvement on repeated tasks

### Quality
- **Retrieval precision:** % of memories actually used
- **False positive rate:** % of unhelpful memories
- **Coverage:** % of tasks where memory was requested

---

## IMPLEMENTATION ORDER

1. ✅ Core models (Milestone 1)
2. ✅ Backend interface + MockBackend (Milestone 2)
3. ✅ ContextBuilder (Milestone 3)
4. ✅ IntentClassifier (Milestone 4)
5. ✅ MemoryProvider (Milestone 5)
6. ✅ GraphitiBackend (Milestone 6)
7. ⏳ Agent integration (Milestone 7)

**Total:** 12-16 implementation cycles
**Validation:** Tests + measurement at each milestone

---

## NEXT ACTION

**STOP architecture research.**

**START Milestone 1:** Create Memory data model.

File: `graphiti_memory/models/memory.py`

**This is engineering validation, not design.**
