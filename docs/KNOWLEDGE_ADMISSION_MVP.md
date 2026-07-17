# Knowledge Admission MVP - Incremental Build Plan

## Core Principle

> **Don't build because you think you'll need it.  
> Build because a benchmark proves you need it.**

---

## Version 1: MVP (Minimum Viable Pipeline)

### Components (4 total)

```
Task Completed
      ↓
Execution Recorder ✅
      ↓
Admission Policy ✅
      ↓
Metadata Enricher ✅
      ↓
Graphiti Adapter ✅
```

**That's it.** Nothing else in v1.

---

## Phase 1: Graphiti Adapter (Week 1)

### Goal
Prove Graphiti integration works before adding logic.

### Implementation
```python
from graphiti_core import Graphiti
from datetime import datetime

class GraphitiAdapter:
    """Thin wrapper around Graphiti SDK."""
    
    def __init__(self, uri: str, user: str, password: str):
        self.graphiti = Graphiti(uri=uri, user=user, password=password)
    
    async def submit_episode(
        self,
        name: str,
        episode_body: str,
        metadata: dict
    ) -> bool:
        """Submit episode to Graphiti with error handling."""
        try:
            await self.graphiti.add_episode(
                name=name,
                episode_body=episode_body,
                source_description="OpenHands task execution",
                reference_time=datetime.now(),
                metadata=metadata
            )
            return True
        except Exception as e:
            logger.error(f"Graphiti submission failed: {e}")
            return False
    
    async def search(
        self,
        query: str,
        metadata_filter: dict,
        limit: int = 10
    ):
        """Search Graphiti for relevant episodes."""
        try:
            results = await self.graphiti.search(
                query=query,
                metadata_filter=metadata_filter,
                num_results=limit
            )
            return results
        except Exception as e:
            logger.error(f"Graphiti search failed: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Graphiti is accessible."""
        try:
            # Try a simple operation
            await self.graphiti.search(query="test", num_results=0)
            return True
        except:
            return False
```

### Responsibilities
- ✅ Create Graphiti client
- ✅ Convert to Graphiti episode format
- ✅ Add metadata
- ✅ Handle errors/retries
- ✅ Health checks

### Verification
```python
# Test 1: Can we connect?
adapter = GraphitiAdapter("bolt://localhost:7687", "neo4j", "password")
assert await adapter.health_check()

# Test 2: Can we write?
success = await adapter.submit_episode(
    name="test-1",
    episode_body="Test episode",
    metadata={"test": True}
)
assert success

# Test 3: Can we read?
results = await adapter.search("test", metadata_filter={})
assert len(results) >= 0
```

**Stop if this fails. Fix Graphiti integration first.**

---

## Phase 2: Metadata Enricher (Week 1)

### Goal
Add repository/branch context for isolation.

### Implementation
```python
class MetadataEnricher:
    """Add retrieval-critical metadata."""
    
    def enrich(self, record: 'ExecutionRecord') -> dict:
        """Create metadata for episode."""
        return {
            "repository": record.repository,
            "branch": record.branch,
            "commit": record.commit_sha,
            "workspace": record.workspace_path,
            "task_id": record.task_id,
            "timestamp": record.timestamp.isoformat(),
            "success": record.success,
        }
```

### Responsibilities
- ✅ Repository scope
- ✅ Branch scope
- ✅ Commit reference
- ✅ Timestamp

### Verification
```python
# Test: Metadata is attached correctly
enricher = MetadataEnricher()
record = ExecutionRecord(
    repository="myorg/myapp",
    branch="main",
    commit_sha="abc123",
    workspace_path="/path/to/workspace",
    task_id="task-123",
    timestamp=datetime.now(),
    success=True
)

metadata = enricher.enrich(record)
assert metadata["repository"] == "myorg/myapp"
assert metadata["branch"] == "main"
assert metadata["commit"] == "abc123"

# Test: Can retrieve by metadata
await adapter.submit_episode("test", "body", metadata)
results = await adapter.search(
    query="test",
    metadata_filter={"repository": "myorg/myapp"}
)
assert all(r.metadata["repository"] == "myorg/myapp" for r in results)
```

---

## Phase 3: Admission Policy (Week 2)

### Goal
Decide if execution should become an episode.

### Implementation
```python
class AdmissionPolicy:
    """Decide whether to remember execution."""
    
    def should_admit(self, record: 'ExecutionRecord') -> tuple[bool, str]:
        """
        Returns: (should_admit, reason)
        """
        # Check 1: Task must succeed
        if not record.success:
            return False, "Task failed"
        
        # Check 2: Must have execution outcome
        if not self._has_outcome(record):
            return False, "No meaningful outcome"
        
        # Check 3: Not trivial action
        if self._is_trivial(record):
            return False, "Trivial action"
        
        return True, "Meets admission criteria"
    
    def _has_outcome(self, record) -> bool:
        """Did something meaningful happen?"""
        return bool(record.changed_files) or bool(record.tests_passed)
    
    def _is_trivial(self, record) -> bool:
        """Is this a trivial action?"""
        trivial_keywords = [
            "npm install",
            "pip install",
            "hi",
            "hello",
            "thanks",
            "run tests",
            "create file",
            "delete file",
            "fix typo",
            "open file",
        ]
        prompt_lower = record.prompt.lower()
        return any(kw in prompt_lower for kw in trivial_keywords)
```

### Decision Table

| Task | Success | Outcome | Trivial | Decision |
|------|---------|---------|---------|----------|
| "Hi" | true | none | ✅ yes | ❌ DON'T ADMIT |
| "Run npm install" | true | none | ✅ yes | ❌ DON'T ADMIT |
| "Explain auth arch" | true | files changed | ❌ no | ✅ ADMIT |
| "Fix Redis race" | true | tests passed | ❌ no | ✅ ADMIT |
| "Open README" | true | none | ✅ yes | ❌ DON'T ADMIT |
| "Implement OAuth" | **false** | files changed | ❌ no | ❌ DON'T ADMIT (failed) |

### Responsibilities
- ✅ Success check
- ✅ Outcome check
- ✅ Triviality check
- ❌ NO governance yet (Phase 4)
- ❌ NO evidence collection yet
- ❌ NO advanced heuristics

### Verification
```python
# Test: Admission decisions
policy = AdmissionPolicy()

# Should reject trivial
trivial_record = ExecutionRecord(
    prompt="npm install",
    success=True,
    changed_files=[]
)
assert not policy.should_admit(trivial_record)[0]

# Should reject failed
failed_record = ExecutionRecord(
    prompt="Implement OAuth",
    success=False,
    changed_files=["auth.py"]
)
assert not policy.should_admit(failed_record)[0]

# Should accept meaningful
meaningful_record = ExecutionRecord(
    prompt="AuthService depends on TokenService",
    success=True,
    changed_files=["auth/service.py"],
    tests_passed=True
)
assert policy.should_admit(meaningful_record)[0]
```

---

## Phase 4: Execution Recorder (Week 2)

### Goal
Capture execution outcomes for admission.

### Implementation
```python
@dataclass
class ExecutionRecord:
    """Record of a completed task execution."""
    
    # Identity
    task_id: str
    timestamp: datetime
    
    # Context
    repository: str
    branch: str
    commit_sha: str
    workspace_path: str
    
    # Execution
    prompt: str
    success: bool
    duration_seconds: float
    
    # Outcomes
    changed_files: List[str]
    tests_passed: bool
    commands_executed: List[str]
    
    # Optional
    agent_response: Optional[str] = None


class ExecutionRecorder:
    """Capture execution outcomes."""
    
    def record(
        self,
        conversation,
        agent_response,
        workspace_path: str
    ) -> ExecutionRecord:
        """Create execution record from task completion."""
        
        # Extract context
        repository = self._get_repository(workspace_path)
        branch = self._get_branch(workspace_path)
        commit_sha = self._get_commit(workspace_path)
        
        # Extract outcomes
        changed_files = self._extract_changed_files(agent_response)
        tests_passed = self._check_tests_passed(agent_response)
        commands = self._extract_commands(agent_response)
        
        return ExecutionRecord(
            task_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            repository=repository,
            branch=branch,
            commit_sha=commit_sha,
            workspace_path=workspace_path,
            prompt=self._extract_prompt(conversation),
            success=self._determine_success(agent_response),
            duration_seconds=self._measure_duration(conversation),
            changed_files=changed_files,
            tests_passed=tests_passed,
            commands_executed=commands,
            agent_response=str(agent_response)
        )
    
    def _get_repository(self, path: str) -> str:
        """Extract repository from git remote."""
        # git remote get-url origin
        # Parse: myorg/myapp
        ...
    
    def _get_branch(self, path: str) -> str:
        """Extract current branch."""
        # git branch --show-current
        ...
    
    def _get_commit(self, path: str) -> str:
        """Extract current commit."""
        # git rev-parse HEAD
        ...
```

### Responsibilities
- ✅ Capture execution context
- ✅ Determine success/failure
- ✅ Extract outcomes
- ✅ Track identity (task_id, timestamp)

### Integration Point
```python
# In Agent.astep()
async def astep(self, conversation, state):
    response = await self.llm.generate(messages)
    
    # NEW: Record execution
    if hasattr(self, 'execution_recorder'):
        record = self.execution_recorder.record(
            conversation,
            response,
            workspace_path=str(conversation.workspace.working_dir)
        )
        
        # Queue for admission
        await self._queue_for_admission(record)
    
    return response
```

### Verification
```python
# Test: Recording works
recorder = ExecutionRecorder()
record = recorder.record(
    conversation=mock_conversation,
    agent_response="Modified auth.py",
    workspace_path="/path/to/repo"
)

assert record.repository == "myorg/myapp"
assert record.branch == "main"
assert record.timestamp is not None
assert isinstance(record.changed_files, list)
```

---

## Phase 5: Basic Governance (Week 3)

### Goal
Prevent secrets from entering graph.

### Implementation
```python
class BasicGovernance:
    """Minimal secret scanning."""
    
    SECRET_PATTERNS = [
        r"password\s*=\s*['\"][^'\"]+['\"]",
        r"api_key\s*=\s*['\"][^'\"]+['\"]",
        r"secret\s*=\s*['\"][^'\"]+['\"]",
        r"token\s*=\s*['\"][^'\"]+['\"]",
        r"-----BEGIN.*KEY-----",
        r"aws_access_key_id\s*=",
        r"aws_secret_access_key\s*=",
    ]
    
    def check(self, record: ExecutionRecord) -> tuple[bool, str]:
        """Check for secrets."""
        
        # Scan all text fields
        text_to_scan = " ".join([
            record.prompt,
            str(record.agent_response),
            " ".join(record.changed_files),
            " ".join(record.commands_executed)
        ])
        
        for pattern in self.SECRET_PATTERNS:
            if re.search(pattern, text_to_scan, re.IGNORECASE):
                return False, f"Contains secret pattern: {pattern}"
        
        return True, "Passed governance checks"
```

### Responsibilities
- ✅ Secret pattern matching
- ❌ NO PII classifier (wait for evidence)
- ❌ NO complex policy engine
- ❌ NO advanced governance

### Verification
```python
# Test: Detect secrets
governance = BasicGovernance()

# Should reject secrets
secret_record = ExecutionRecord(
    prompt="Update config",
    agent_response="api_key='sk-12345'",
    ...
)
assert not governance.check(secret_record)[0]

# Should allow clean records
clean_record = ExecutionRecord(
    prompt="Refactor auth",
    agent_response="Created AuthService",
    ...
)
assert governance.check(clean_record)[0]
```

---

## What NOT to Build Yet (Wait for Evidence)

### ❌ Advanced Governance
- PII classifier
- Complex policy rules
- Advanced heuristics
- Custom validation engines

**Build when:** You see bad memories entering graph

### ❌ Evidence Collection
- AST extraction
- Import graph analysis
- Test result linking
- Code symbol tracking

**Build when:** Benchmarks show Graphiti extraction quality insufficient

### ❌ Sophisticated Admission
- ML-based admission
- Complex value scoring
- Advanced filtering

**Build when:** Simple admission policy proves insufficient

### ❌ Feedback Metrics
- Usage tracking
- Confidence adjustment
- Quality metrics

**Build when:** You have real usage data

---

## Implementation Order

### Week 1
1. ✅ Graphiti Adapter → Prove integration works
2. ✅ Metadata Enricher → Repository isolation

### Week 2
3. ✅ Admission Policy → Decide what to remember
4. ✅ Execution Recorder → Capture outcomes

### Week 3
5. ✅ Basic Governance → Prevent secrets

### Week 4+
6. ⬜ Observe real usage
7. ⬜ Benchmark quality
8. ⬜ Extend ONLY where needed

---

## Complete V1 Implementation

```python
class KnowledgeAdmissionPipeline:
    """Minimal admission pipeline (v1)."""
    
    def __init__(self, graphiti_uri: str):
        self.adapter = GraphitiAdapter(graphiti_uri, "neo4j", "password")
        self.enricher = MetadataEnricher()
        self.policy = AdmissionPolicy()
        self.recorder = ExecutionRecorder()
        self.governance = BasicGovernance()
    
    async def process_execution(self, conversation, agent_response, workspace: str):
        """Process completed execution."""
        
        # Step 1: Record execution
        record = self.recorder.record(conversation, agent_response, workspace)
        
        # Step 2: Check admission policy
        should_admit, reason = self.policy.should_admit(record)
        if not should_admit:
            logger.info(f"Not admitted: {reason}")
            return
        
        # Step 3: Check governance
        passed, reason = self.governance.check(record)
        if not passed:
            logger.warning(f"Governance rejected: {reason}")
            return
        
        # Step 4: Enrich metadata
        metadata = self.enricher.enrich(record)
        
        # Step 5: Submit to Graphiti
        # Prepare episode body
        episode_body = self._prepare_episode_body(record)
        
        success = await self.adapter.submit_episode(
            name=f"task-{record.task_id}",
            episode_body=episode_body,
            metadata=metadata
        )
        
        if success:
            logger.info(f"✅ Knowledge admitted: {record.task_id}")
        else:
            logger.error(f"❌ Failed to admit: {record.task_id}")
    
    def _prepare_episode_body(self, record: ExecutionRecord) -> str:
        """Format execution as episode."""
        parts = [
            f"Task: {record.prompt}",
            f"Changed files: {', '.join(record.changed_files)}",
        ]
        
        if record.tests_passed:
            parts.append("Tests: Passed")
        
        if record.agent_response:
            parts.append(f"Result: {record.agent_response[:500]}")
        
        return "\n".join(parts)
```

---

## Separation of Concerns

### Our System (v1)
- ✅ Decide **whether** to remember
- ✅ Provide **context** (metadata)
- ✅ Enforce **policy** (governance)
- ✅ Capture **outcomes** (recording)

### Graphiti
- ✅ Extract **entities**
- ✅ Create **relationships**
- ✅ Generate **embeddings**
- ✅ Handle **deduplication**
- ✅ Track **temporal** evolution
- ✅ Manage **lifecycle**

---

## Success Criteria for V1

### Functional
- ✅ Can submit episodes to Graphiti
- ✅ Can retrieve episodes by metadata
- ✅ Repository isolation works
- ✅ Admission policy filters correctly
- ✅ Governance blocks secrets

### Quality
- ✅ No agent crashes (graceful fallback)
- ✅ Integration tested
- ✅ Clear logging

### Performance
- ✅ Submission < 1 second
- ✅ Retrieval < 500ms

---

## The Honest Assessment

**Architecture:** 10/10 (clean separation)
**Implementation:** Start minimal, extend on evidence
**Timeline:** 3 weeks to v1

**Key insight:** This is the **MVP**. Everything else waits for real usage data and benchmarks.

**Result:** A production-ready v1 that works, with clear separation between admission logic and graph mechanics.
