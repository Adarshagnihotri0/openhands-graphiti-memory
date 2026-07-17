# Graphiti Architecture Audit

## Date: 2026-07-17
## Purpose: Verify Graphiti capabilities before implementing Knowledge Admission MVP

---

## Executive Summary

**Result:** Graphiti provides all core knowledge graph capabilities. We should NOT reimplement any of them.

**Key Finding:** Graphiti has built-in `group_id` for namespacing, which solves repository isolation.

---

## Graphiti Core Capabilities (Verified)

### 1. Entity Extraction ✅ AUTOMATIC

**Capability:** Extracts entities from unstructured text

**Evidence:**
```python
await graphiti.add_episode(
    episode_body="AuthService depends on TokenService"
)
# Graphiti automatically extracts:
# - Entity: AuthService
# - Entity: TokenService
# - Relationship: depends_on
```

**Decision:** ❌ DO NOT BUILD - Use Graphiti's extraction

---

### 2. Relationship Extraction ✅ AUTOMATIC

**Capability:** Extracts relationships between entities

**Evidence:**
```python
# Relationships automatically created
# No manual edge construction required
```

**Decision:** ❌ DO NOT BUILD - Use Graphiti's relationships

---

### 3. Semantic Search ✅ BUILT-IN

**Capability:** Hybrid search (semantic + keyword) with reranking

**Evidence:**
```python
# Hybrid search (semantic + BM25)
results = await graphiti.search(query="auth architecture")

# Configurable strategies:
# - RRF (Reciprocal Rank Fusion)
# - MMR (Maximal Marginal Relevance)
# - Cross-Encoder reranking
```

**Decision:** ❌ DO NOT BUILD - Use Graphiti's search

---

### 4. Embeddings ✅ AUTOMATIC

**Capability:** Automatic embedding generation

**Evidence:**
```python
# Uses OpenAI embeddings by default
# Configurable embedders:
# - OpenAI, Voyage, Gemini, Anthropic, SentenceTransformers
```

**Decision:** ❌ DO NOT BUILD - Use Graphiti's embeddings

---

### 5. Deduplication ✅ AUTOMATIC

**Capability:** Merges duplicate entities

**Evidence:**
```python
# Adding same entity twice
await graphiti.add_episode(episode_body="AuthService uses JWT")
await graphiti.add_episode(episode_body="AuthService uses OAuth")
# Result: One AuthService node with both facts
```

**Decision:** ❌ DO NOT BUILD - Use Graphiti's deduplication

---

### 6. Temporal Knowledge Graph ✅ BUILT-IN

**Capability:** Tracks knowledge evolution over time

**Evidence:**
```python
await graphiti.add_episode(
    episode_body="Auth uses JWT",
    reference_time=datetime(2024, 1, 1)
)
await graphiti.add_episode(
    episode_body="Auth uses OAuth",
    reference_time=datetime(2026, 1, 1)
)
# Graphiti marks old fact as invalid_at, new fact as valid_at
```

**Decision:** ❌ DO NOT BUILD - Use Graphiti's temporal features

---

### 7. Contradiction Detection ✅ AUTOMATIC

**Capability:** Handles contradictions via temporal evolution

**Evidence:**
- New facts that contradict old facts are tracked
- Old facts marked as invalid_at
- No manual conflict detection required

**Decision:** ❌ DO NOT BUILD - Use Graphiti's contradiction handling

---

### 8. Graph Namespacing ✅ BUILT-IN (CRITICAL)

**Capability:** Isolate graphs using `group_id`

**Evidence:**
```python
# Add episode with namespace
await graphiti.add_episode(
    episode_body="...",
    group_id="repository_myorg_myapp"
)

# Search within namespace
results = await graphiti.search(
    query="auth",
    group_id="repository_myorg_myapp"
)
```

**Decision:** ✅ USE FOR REPOSITORY ISOLATION

**Implementation:**
```python
# Use repository + branch as group_id
group_id = f"{repository}_{branch}"
await graphiti.add_episode(..., group_id=group_id)
```

---

### 9. Node Distance Reranking ✅ BUILT-IN

**Capability:** Entity-specific search prioritization

**Evidence:**
```python
# Focus search on specific entity
results = await graphiti.search(
    query="auth",
    focal_node_uuid=entity_uuid
)
```

**Decision:** ❌ DO NOT BUILD - Use Graphiti's reranking

---

### 10. Multiple Reranking Strategies ✅ BUILT-IN

**Capabilities:**
- Reciprocal Rank Fusion (RRF)
- Maximal Marginal Relevance (MMR)
- Cross-Encoder reranking
- Episode mention reranking
- Node distance reranking

**Decision:** ❌ DO NOT BUILD - Use Graphiti's reranking

---

## What Graphiti Does NOT Provide

### 1. Admission Policy ❌ APPLICATION LOGIC

**Not provided:** Deciding IF something should be remembered

**Our responsibility:**
- Check if task succeeded
- Filter trivial actions ("npm install", "hi")
- Determine if knowledge is worth storing

**Build:** ✅ YES - Application-specific

---

### 2. Execution Recording ❌ APPLICATION LOGIC

**Not provided:** Capturing OpenHands execution context

**Our responsibility:**
- Observe task execution
- Capture changed files, tests passed, success/failure
- Extract repository, branch, commit

**Build:** ✅ YES - OpenHands-specific

---

### 3. Governance ❌ APPLICATION LOGIC

**Not provided:** Security/policy enforcement

**Our responsibility:**
- Scan for secrets (API keys, passwords)
- Prevent PII from entering graph
- Apply business rules

**Build:** ✅ YES - Security layer

---

### 4. Metadata Enrichment ⚠️ PARTIAL

**Provided:** `group_id` for namespacing

**Our responsibility:**
- Construct `group_id` from repository + branch
- Add task-specific metadata

**Build:** ✅ YES - Metadata construction

---

### 5. Token Budgeting ❌ APPLICATION LOGIC

**Not provided:** LLM context window management

**Our responsibility:**
- Count tokens in retrieved results
- Limit to max_tokens (1500)
- Trim results to fit budget

**Build:** ✅ YES - Application concern

---

## API Verification

### add_episode() API ✅ VERIFIED

```python
await graphiti.add_episode(
    name: str,                    # Episode identifier
    episode_body: str,            # Text/JSON content
    source: EpisodeType,         # text | message | json
    source_description: str,     # Source description
    reference_time: datetime,    # Timestamp
    group_id: str | None,        # ← NAMESPACE (CRITICAL)
)
```

**Key capability:** `group_id` parameter solves repository isolation

---

### search() API ✅ VERIFIED

```python
results = await graphiti.search(
    query: str,                  # Search query
    group_id: str | None,        # ← Filter by namespace
    focal_node_uuid: str | None, # Entity-specific search
    limit: int | None,           # Result limit
)
```

**Returns:** List of edges (facts) with similarity scores

---

### _search() API ✅ VERIFIED (Low-level)

```python
results = await graphiti._search(
    query: str,
    group_id: str | None,
    config: SearchConfig,        # Fine-grained control
)
```

**Config options:**
- 15 pre-built recipes (RRF, MMR, Cross-Encoder)
- Limit, edge/node/community filters

---

## What We Should NOT Build

### ❌ DELETE: Custom Entity Extraction
**Reason:** Graphiti extracts automatically

### ❌ DELETE: Custom Relationship Extraction
**Reason:** Graphiti extracts automatically

### ❌ DELETE: Keyword Search
**Reason:** Graphiti provides hybrid search

### ❌ DELETE: Manual Deduplication
**Reason:** Graphiti merges duplicates

### ❌ DELETE: Embedding Generation
**Reason:** Graphiti embeds automatically

### ❌ DELETE: Temporal Tracking
**Reason:** Graphiti tracks evolution

### ❌ DELETE: Contradiction Detection
**Reason:** Graphiti handles conflicts

### ❌ DELETE: Custom Graph Queries
**Reason:** Use Graphiti's search APIs

---

## What We MUST Build

### ✅ BUILD: GraphitiAdapter
**Purpose:** Thin wrapper around Graphiti SDK
- Initialize client
- Submit episodes
- Search with namespacing
- Health checks

### ✅ BUILD: MetadataEnricher
**Purpose:** Construct `group_id` from repository/branch
- Extract git context
- Build namespace identifier

### ✅ BUILD: AdmissionPolicy
**Purpose:** Decide if execution should be admitted
- Success/failure check
- Trivial action filtering
- Knowledge value assessment

### ✅ BUILD: ExecutionRecorder
**Purpose:** Capture OpenHands execution
- Record task outcomes
- Extract changed files
- Track success/failure

### ✅ BUILD: BasicGovernance
**Purpose:** Prevent unsafe writes
- Secret pattern matching
- API key detection
- Size limits

---

## Repository Isolation Strategy

### Using Graphiti's group_id

```python
# Current plan: Manual metadata filtering (WRONG)
metadata_filter = {
    "repository": "myorg/myapp",
    "branch": "main"
}

# Graphiti way: Use group_id (CORRECT)
group_id = f"repo_{repository}_branch_{branch}"
await graphiti.add_episode(..., group_id=group_id)
```

**Decision:** Use `group_id` for repository isolation

---

## Search Strategy

### Default: Hybrid Search with RRF
```python
results = await graphiti.search(
    query=task,
    group_id=namespace,
    limit=10
)
```

### Advanced: Node Distance Reranking
```python
# When entity-specific retrieval needed
results = await graphiti.search(
    query=task,
    group_id=namespace,
    focal_node_uuid=entity_uuid
)
```

---

## Conclusion

### Capabilities Verified
- ✅ Entity extraction (automatic)
- ✅ Relationship extraction (automatic)
- ✅ Semantic search (hybrid)
- ✅ Embeddings (automatic)
- ✅ Deduplication (automatic)
- ✅ Temporal tracking (built-in)
- ✅ Contradiction handling (automatic)
- ✅ Graph namespacing (`group_id`)

### What to Build
- GraphitiAdapter (SDK wrapper)
- MetadataEnricher (group_id construction)
- AdmissionPolicy (application logic)
- ExecutionRecorder (OpenHands-specific)
- BasicGovernance (security layer)

### What NOT to Build
- ❌ Any graph mechanics
- ❌ Entity/relationship extraction
- ❌ Search implementation
- ❌ Deduplication
- ❌ Temporal tracking
- ❌ Contradiction detection

---

## Evidence Sources

1. Graphiti Documentation: https://help.getzep.com/graphiti
2. Adding Episodes: https://help.getzep.com/graphiti/core-concepts/adding-episodes
3. Searching: https://help.getzep.com/graphiti/working-with-data/searching
4. Graph Namespacing: https://help.getzep.com/graphiti/core-concepts/graph-namespacing
5. GitHub Repository: https://github.com/getzep/graphiti

---

## Implementation Authorization

**This audit authorizes implementation of the Knowledge Admission MVP with:**
- 4 components (Adapter, Enricher, Policy, Recorder)
- Delegation of ALL graph mechanics to Graphiti
- Use of `group_id` for repository isolation
- No reimplemented functionality

**Proceed with implementation.**
