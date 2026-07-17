# Knowledge Admission Pipeline - Graphiti Audit Decision

## Executive Summary

**Decision:** Build minimal Knowledge Admission Pipeline, delegate all graph mechanics to Graphiti.

**Scope Reduction:** 15 components → 6 components (60% reduction)

---

## The New Architecture

### Before (Original Roadmap)
```
Task
 ↓
Execution Observer
 ↓
Candidate Extraction
 ↓
Evidence Collection
 ↓
Verification Engine
 ↓
Governance Layer
 ↓
Duplicate Detection ❌
 ↓
Entity Extraction ❌
 ↓
Relationship Extraction ❌
 ↓
Temporal Tracking ❌
 ↓
Embedding ❌
 ↓
Contradiction Detection ❌
 ↓
Store in Neo4j ❌
```

### After (Graphiti-Based)
```
Task
 ↓
Execution Observer ✅
 ↓
Admission Decision ✅
 ↓
Governance Check ✅
 ↓
Metadata Enrichment ✅
 ↓
Graphiti.add_episode() ← Graphiti handles rest
```

---

## What We Must Build (Admission Layer)

### 1. Execution Observer ✅ REQUIRED

**Why:** Graphiti doesn't know about OpenHands tasks

**What it captures:**
```python
@dataclass
class ExecutionRecord:
    task_id: str
    prompt: str
    repository: str  # For metadata
    branch: str       # For metadata
    changed_files: List[str]
    tests_passed: bool
    commands_executed: List[str]
    duration_seconds: float
    success: bool
    timestamp: datetime
```

**Integration point:**
```python
# After Agent.astep() completes
async def astep(self, conversation, state):
    response = await self.llm.generate(messages)
    
    # NEW: Observe execution
    record = ExecutionObserver.observe(conversation, response)
    await self._queue_for_admission(record)
    
    return response
```

**Decision:** ✅ BUILD - Application-specific, Graphiti doesn't know agent execution

---

### 2. Admission Decision Engine ✅ REQUIRED

**Why:** Graphiti can't decide if something is worth remembering

**Examples:**
```
Task: "Run npm install"
Decision: ❌ DON'T REMEMBER (temporary action)

Task: "Auth architecture uses JWT tokens"
Decision: ✅ REMEMBER (architectural knowledge)

Task: "Fix typo in README"
Decision: ❌ DON'T REMEMBER (trivial change)

Task: "AuthService depends on TokenService"
Decision: ✅ REMEMBER (dependency relationship)
```

**Logic:**
```python
class AdmissionDecider:
    def should_remember(self, record: ExecutionRecord) -> bool:
        # Rule 1: Skip trivial tasks
        if not record.changed_files:
            return False
        
        # Rule 2: Skip temporary operations
        if self._is_temporary_action(record.prompt):
            return False
        
        # Rule 3: Require architectural significance
        if not self._has_architectural_impact(record):
            return False
        
        # Rule 4: Verify success
        if not record.success:
            return False
        
        return True
    
    def _is_temporary_action(self, prompt: str) -> bool:
        temporary_keywords = [
            "npm install",
            "pip install",
            "run tests",
            "create file",
            "delete file",
            "fix typo"
        ]
        return any(kw in prompt.lower() for kw in temporary_keywords)
```

**Decision:** ✅ BUILD - Domain logic, Graphiti can't make admission decisions

---

### 3. Governance Layer ✅ REQUIRED

**Why:** Graphiti won't prevent secret/PII leakage

**Checks:**
```python
class GovernanceLayer:
    async def approve(self, record: ExecutionRecord) -> GovernanceResult:
        # Check 1: No secrets
        if self._contains_secrets(record):
            return GovernanceResult.REJECTED("Contains secrets")
        
        # Check 2: No PII
        if self._contains_pii(record):
            return GovernanceResult.REJECTED("Contains PII")
        
        # Check 3: Not temporary
        if self._is_temporary(record):
            return GovernanceResult.REJECTED("Temporary information")
        
        # Check 4: Worth remembering
        if not self._worth_remembering(record):
            return GovernanceResult.REJECTED("Not worth storing")
        
        # Check 5: Repository scoped
        if not record.repository:
            return GovernanceResult.REJECTED("Missing repository scope")
        
        return GovernanceResult.APPROVED()
    
    def _contains_secrets(self, record: ExecutionRecord) -> bool:
        secret_patterns = [
            r"password\s*=\s*['\"]",
            r"api_key\s*=\s*['\"]",
            r"secret\s*=\s*['\"]",
            r"token\s*=\s*['\"]",
            r"-----BEGIN.*KEY-----",
        ]
        # Scan prompt, changed files, commands
        for pattern in secret_patterns:
            if re.search(pattern, record.to_text()):
                return True
        return False
```

**Decision:** ✅ BUILD - Security/policy layer, critical for production

---

### 4. Evidence Collection ⚠️ OPTIONAL BUT VALUABLE

**Why:** Richer episodes = better knowledge graph

**Without evidence:**
```python
await graphiti.add_episode(
    episode_body="AuthService depends on TokenService"
)
```

**With evidence:**
```python
await graphiti.add_episode(
    episode_body="""
    AuthService depends on TokenService
    
    Evidence:
    - Source: auth/service.py:84
    - Commit: abc123
    - Import: from auth.token_service import TokenService
    - Test: tests/auth/test_integration.py passed
    """,
    metadata={
        "repository": "myorg/myapp",
        "branch": "main",
        "files": ["auth/service.py"],
        "commit": "abc123"
    }
)
```

**Decision:** ⚠️ BUILD IF BENCHMARKS SHOW VALUE - Enhances Graphiti's extraction quality

---

### 5. Metadata Enrichment ✅ REQUIRED

**Why:** Repository/branch isolation

**What we add:**
```python
metadata = {
    "repository": record.repository,
    "branch": record.branch,
    "task_id": record.task_id,
    "timestamp": record.timestamp.isoformat(),
    "success": record.success,
    "changed_files": record.changed_files,
    "tests_passed": record.tests_passed
}

await graphiti.add_episode(
    episode_body=episode_text,
    metadata=metadata
)
```

**Retrieval with metadata:**
```python
results = await graphiti.search(
    query="auth architecture",
    metadata_filter={
        "repository": "myorg/myapp",
        "branch": "main"
    }
)
```

**Decision:** ✅ BUILD - Application-level scoping, critical for isolation

---

### 6. Token Budgeting ✅ REQUIRED (Retrieval)

**Why:** Graphiti returns raw results, application must budget

**Implementation:**
```python
class TokenBudgetManager:
    def apply_budget(self, results: List[SearchResult], max_tokens: int = 1500):
        budgeted = []
        total_tokens = 0
        
        for result in results:
            # Estimate tokens (~4 chars per token)
            tokens = len(result.summary) // 4
            
            if total_tokens + tokens <= max_tokens:
                budgeted.append(result)
                total_tokens += tokens
            else:
                break
        
        return budgeted
```

**Decision:** ✅ BUILD - Application concern, Graphiti doesn't know LLM limits

---

## What We DON'T Build (Delegate to Graphiti)

### ❌ DELETE: Entity Extraction
**Graphiti provides:**
```python
# We just call:
await graphiti.add_episode(episode_body="...")

# Graphiti automatically:
# - Extracts "AuthService" entity
# - Extracts "TokenService" entity
# - Creates DEPENDS_ON relationship
```

**Decision:** ❌ DON'T BUILD - Use Graphiti's extraction

---

### ❌ DELETE: Relationship Extraction
**Graphiti provides:**
```python
# We just call:
await graphiti.add_episode(
    episode_body="AuthService depends on TokenService"
)

# Graphiti automatically creates:
# (AuthService)-[:DEPENDS_ON]->(TokenService)
```

**Decision:** ❌ DON'T BUILD - Use Graphiti's relationship extraction

---

### ❌ DELETE: Deduplication
**Graphiti provides:**
```python
# Episode 1
await graphiti.add_episode(
    episode_body="AuthService uses JWT"
)

# Episode 2 (same entity)
await graphiti.add_episode(
    episode_body="AuthService uses OAuth"
)

# Graphiti automatically:
# - Merges "AuthService" into one node
# - Updates relationships
# - Handles contradiction via temporal tracking
```

**Decision:** ❌ DON'T BUILD - Use Graphiti's deduplication

---

### ❌ DELETE: Embedding Generation
**Graphiti provides:**
```python
# Automatic embedding generation
results = await graphiti.search(query="auth")

# Graphiti uses:
# - OpenAI embeddings by default
# - Or custom embedding model
# - Automatic similarity scoring
```

**Decision:** ❌ DON'T BUILD - Use Graphiti's embeddings

---

### ❌ DELETE: Temporal Tracking
**Graphiti provides:**
```python
# Knowledge evolution
await graphiti.add_episode(
    episode_body="AuthService uses JWT",
    reference_time=datetime(2024, 1, 1)
)

await graphiti.add_episode(
    episode_body="AuthService uses OAuth",
    reference_time=datetime(2026, 1, 1)
)

# Graphiti automatically:
# - Marks old fact as invalid_at
# - Creates new fact with valid_at
# - Enables point-in-time queries
```

**Decision:** ❌ DON'T BUILD - Use Graphiti's temporal features

---

### ❌ DELETE: Contradiction Detection
**Graphiti provides:**
```python
# Automatic contradiction handling
# When new episode contradicts old:
# - Graphiti marks old as superseded
# - Creates new version
# - Maintains history
```

**Decision:** ❌ DON'T BUILD - Use Graphiti's contradiction handling

---

## Final Decision Matrix

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Execution Observer | ✅ BUILD | Application-specific |
| Admission Decision | ✅ BUILD | Domain logic |
| Governance | ✅ BUILD | Security/policy |
| Evidence Collection | ⚠️ OPTIONAL | Enhances quality |
| Metadata Enrichment | ✅ BUILD | Repository isolation |
| Entity Extraction | ❌ GRAPHITI | Built-in |
| Relationship Extraction | ❌ GRAPHITI | Built-in |
| Deduplication | ❌ GRAPHITI | Built-in |
| Embeddings | ❌ GRAPHITI | Built-in |
| Temporal Tracking | ❌ GRAPHITI | Built-in |
| Contradiction Detection | ❌ GRAPHITI | Built-in |
| Token Budgeting | ✅ BUILD | Application concern |

---

## Simplified Pipeline Implementation

```python
class KnowledgeAdmissionPipeline:
    """Minimal admission logic before Graphiti."""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.observer = ExecutionObserver()
        self.decider = AdmissionDecider()
        self.governance = GovernanceLayer()
        self.budgetmgr = TokenBudgetManager()
    
    async def process_execution(self, conversation, agent_response):
        """Process completed task for knowledge admission."""
        
        # Step 1: Observe execution
        record = self.observer.observe(conversation, agent_response)
        
        # Step 2: Decide if worth remembering
        if not self.decider.should_remember(record):
            return  # Skip
        
        # Step 3: Governance check
        governance_result = await self.governance.approve(record)
        if not governance_result.approved:
            logger.warning(f"Rejected: {governance_result.reason}")
            return  # Skip
        
        # Step 4: Prepare episode
        episode_body = self._prepare_episode(record)
        metadata = self._prepare_metadata(record)
        
        # Step 5: Submit to Graphiti
        # (Graphiti handles: entities, relationships, embedding, dedup, temporal)
        await self.graphiti.add_episode(
            name=f"task-{record.task_id}",
            episode_body=episode_body,
            source_description=f"Task execution: {record.prompt}",
            reference_time=record.timestamp,
            metadata=metadata
        )
        
        logger.info(f"✅ Knowledge admitted: {record.task_id}")
    
    async def retrieve_knowledge(self, context: RetrievalContext):
        """Retrieve knowledge with application-level filtering."""
        
        # Step 1: Call Graphiti search
        results = await self.graphiti.search(
            query=context.task,
            metadata_filter={
                "repository": context.repository,
                "branch": context.branch
            },
            num_results=20  # Get more than needed
        )
        
        # Step 2: Apply token budget
        budgeted = self.budgetmgr.apply_budget(results, max_tokens=1500)
        
        # Step 3: Format for injection
        return self._format_for_injection(budgeted)
```

---

## Scope Reduction Summary

### Original Roadmap (15 components)
- Execution Observer ✅
- Candidate Extraction ❌ (Graphiti extracts)
- Evidence Collection ⚠️ (Optional)
- Verification Engine ❌ (Simplify to governance)
- Governance Layer ✅
- Duplicate Detection ❌ (Graphiti dedupes)
- Entity Extraction ❌ (Graphiti extracts)
- Relationship Extraction ❌ (Graphiti extracts)
- Temporal Tracking ❌ (Graphiti temporal)
- Embedding ❌ (Graphiti embeds)
- Contradiction Detection ❌ (Graphiti handles)
- Memory Lifecycle ❌ (Graphiti lifecycle)
- Repository Metadata ✅
- Token Budgeting ✅
- Storage ❌ (Graphiti stores)

### New Pipeline (6 components)
1. Execution Observer ✅
2. Admission Decision ✅
3. Governance Layer ✅
4. Metadata Enrichment ✅
5. Token Budgeting ✅
6. Graphiti Client ✅ (adapter)

**60% reduction in components**

---

## Benchmark Requirements Before Implementation

**Phase 1: Validate Graphiti Defaults (MANDATORY)**

Before implementing, verify:

1. **Entity Extraction Quality**
   ```python
   # Test: Does Graphiti extract code entities?
   await graphiti.add_episode(
       episode_body="AuthService class depends on TokenService class"
   )
   # Verify: Entities extracted correctly
   ```

2. **Relationship Accuracy**
   ```python
   # Test: Are code relationships extracted?
   # Verify: (AuthService)-[:DEPENDS_ON]->(TokenService)
   ```

3. **Metadata Filtering Performance**
   ```python
   # Test: Can we efficiently filter by repository/branch?
   # Benchmark: < 200ms at 10K entities
   ```

4. **Semantic Search Quality**
   ```python
   # Test: Does "auth" find "authentication"?
   # Benchmark: Precision > 90% on test set
   ```

**If any fail:** Extend Graphiti, don't replace

---

## Final Recommendation

**Build:** Knowledge Admission Pipeline (6 components)
- Focus on what Graphiti doesn't know: admission decisions, governance, metadata
- Keep architecture: separation of concerns preserved
- Delegate to Graphiti: entities, relationships, deduplication, embeddings, temporal

**Result:** 60% less code, better quality (Graphiti's extraction), clean separation

**The pipeline is now:**
```
Task → Observe → Decide → Govern → graphiti.add_episode()
```

Everything after `add_episode()` is Graphiti's responsibility.
