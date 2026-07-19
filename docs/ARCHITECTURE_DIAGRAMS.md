# Memory Architecture - Visual Reference

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                  Autonomous Agent (OpenHands/Cursor/Aider)             │
│                                                                         │
│  Task Input: "Fix authentication race condition in AuthService"         │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      PRE-TASK HOOK (Automatic)                         │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  RETRIEVAL PIPELINE (5 Stages, ~200-300ms total)             │     │
│  │                                                                │     │
│  │  Stage 1: Semantic Search                                     │     │
│  │    Query: "Fix authentication race condition"                 │     │
│  │    Method: Vector similarity (Graphiti)                      │     │
│  │    Result: Top-50 candidate memories                          │     │
│  │    Time: ~50ms                                                │     │
│  └────────────────┬───────────────────────────────────────────────┘     │
│                   │                                                      │
│                   ▼                                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Stage 2: Graph Traversal                                     │     │
│  │    From: Top 10 seeds                                         │     │
│  │    Follow: DEPENDS_ON, FIXES, IMPLEMENTS (2 hops)            │     │
│  │    Result: Expanded graph context (150+ nodes)              │     │
│  │    Time: ~100ms                                               │     │
│  └────────────────┬───────────────────────────────────────────────┘     │
│                   │                                                      │
│                   ▼                                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Stage 3: Entity Lookup                                       │     │
│  │    Entities: [AuthService, TokenService, Race Condition]    │     │
│  │    Method: Direct entity queries                              │     │
│  │    Result: Entity-centric context                            │     │
│  │    Time: ~30ms                                                │     │
│  └────────────────┬───────────────────────────────────────────────┘     │
│                   │                                                      │
│                   ▼                                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Stage 4: Context Filtering                                   │     │
│  │    Filters:                                                   │     │
│  │      - repository == current_repo                            │     │
│  │      - confidence >= 0.5                                      │     │
│  │      - types: [ARCHITECTURE, DECISION, BUG_FIX]              │     │
│  │    Result: Scoped, filtered memories                         │     │
│  │    Time: ~5ms                                                 │     │
│  └────────────────┬───────────────────────────────────────────────┘     │
│                   │                                                      │
│                   ▼                                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Stage 5: Temporal Boosting                                   │     │
│  │    Boost factors:                                             │     │
│  │      - Age < 7 days: +0.3                                     │     │
│  │      - Verified execution: +0.15                              │     │
│  │    Result: Temporal-weighted memories                        │     │
│  │    Time: ~5ms                                                 │     │
│  └────────────────┬───────────────────────────────────────────────┘     │
│                   │                                                      │
│                   ▼                                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  MEMORY SCORING & RANKING                                     │     │
│  │                                                                │     │
│  │  For each memory, calculate:                                  │     │
│  │    final_score = 0.30 × semantic_similarity                   │     │
│  │                 + 0.25 × graph_centrality                     │     │
│  │                 + 0.20 × confidence                           │     │
│  │                 + 0.15 × recency                             │     │
│  │                 + 0.10 × execution_success_rate              │     │
│  │                                                                │     │
│  │  Return: Top 20 ranked memories                               │     │
│  └────────────────┬───────────────────────────────────────────────┘     │
│                   │                                                      │
│                   ▼                                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  CONTEXT BUILDER                                              │     │
│  │                                                                │     │
│  │  1. Token budget allocation (max 2000 tokens)                 │     │
│  │  2. Memory deduplication                                      │     │
│  │  3. Hierarchical formatting                                   │     │
│  │  4. Summarization (if needed)                                 │     │
│  └────────────────┬───────────────────────────────────────────────┘     │
│                   │                                                      │
│                   ▼                                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  PROMPT INJECTION                                             │     │
│  │                                                                │     │
│  │  Inject:                                                      │     │
│  │  <RELEVANT_KNOWLEDGE>                                         │     │
│  │  [Architecture] AuthService                                   │     │
│  │    Depends on: TokenService, UserDB                           │     │
│  │    Pattern: Repository Pattern                                │     │
│  │    Confidence: HIGH (0.92)                                    │     │
│  │    Last verified: 2025-03-15                                  │     │
│  │                                                                │     │
│  │  [BugFix] Fixed Token Race Condition                          │     │
│  │    Root cause: Concurrent token refresh requests             │     │
│  │    Solution: Idempotency key + request deduplication         │     │
│  │    Prevention: Use idempotency keys for all critical ops     │     │
│  │    Confidence: VERIFIED (0.98)                                │     │
│  │    Verified: 2025-07-10                                       │     │
│  │  </RELEVANT_KNOWLEDGE>                                        │     │
│  └────────────────┬───────────────────────────────────────────────┘     │
│                   │                                                      │
└───────────────────┼──────────────────────────────────────────────────────┘
                    │
                    │ Return retrieved context
                    ▼
      ┌─────────────────────────────────────────┐
      │  Agent executes task with context       │
      └──────────────┬──────────────────────────┘
                     │
                     │ Task completed
                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     POST-TASK HOOK (Automatic)                         │
│                                                                         │
│  Result: "Fixed by adding idempotency key to token refresh..."          │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 EXECUTION RECORDER SERVICE                              │
│                                                                         │
│  Captures:                                                              │
│    - Task: "Fix authentication race condition"                         │
│    - Result: "Fixed by adding idempotency key..."                     │
│    - Files changed: [auth_service.py, token_manager.py]              │
│    - Success: true                                                     │
│    - Execution time: 45s                                                │
│    - Repository: github.com/company/auth-service                       │
│    - Branch: main                                                       │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│            KNOWLEDGE EXTRACTION PIPELINE (Background)                  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  LLM-BASED EXTRACTOR                                          │     │
│  │                                                                │     │
│  │  Extract from execution:                                      │     │
│  │    - Facts: What was learned?                                │     │
│  │    - Entities: Which services/modules involved?              │     │
│  │    - Relationships: Dependencies, fixes, patterns?            │     │
│  │    - Confidence: How reliable?                                │     │
│  │                                                                │     │
│  │  Output:                                                      │     │
│  │    Fact 1: AuthService::token_refresh has race condition      │     │
│  │    Entity: AuthService (Service)                              │     │
│  │    Entity: TokenService (Service)                            │     │
│  │    Relationship: AuthService DEPENDS_ON TokenService         │     │
│  │    Fix: Add idempotency key to prevent concurrent refresh     │     │
│  │    Confidence: 0.85                                            │     │
│  └────────────────┬───────────────────────────────────────────────┘     │
│                   │                                                      │
│                   ▼                                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  ENQUEUE TO ADMISSION QUEUE                                   │     │
│  └────────────────┬───────────────────────────────────────────────┘     │
│                   │                                                      │
└───────────────────┼──────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 ADMISSION POLICY SERVICE                                │
│                                                                         │
│  For each extracted fact, calculate 5 dimensions:                      │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Fact: "AuthService::token_refresh has race condition"           │  │
│  │                                                                    │  │
│  │  Dimension 1: IMPORTANCE (0.8)                                   │  │
│  │    - Affects critical path (authentication): +0.3                │  │
│  │    - Bug fix with prevention: +0.3                               │  │
│  │    - Affects core service: +0.2                                  │  │
│  │    Total: 0.8                                                     │  │
│  │                                                                    │  │
│  │  Dimension 2: NOVELTY (1.0)                                      │  │
│  │    - Not in memory graph: +1.0                                   │  │
│  │    - Unique bug, no similar facts found                          │  │
│  │    Total: 1.0                                                     │  │
│  │                                                                    │  │
│  │  Dimension 3: CONFIDENCE (0.85)                                  │  │
│  │    - From successful execution: +0.7                            │  │
│  │    - Code modified: +0.15                                         │  │
│  │    Total: 0.85                                                    │  │
│  │                                                                    │  │
│  │  Dimension 4: PERSISTENCE (0.9)                                  │  │
│  │    - Bug fix pattern: +0.9                                       │  │
│  │    - Will remain valid long-term                                 │  │
│  │    Total: 0.9                                                     │  │
│  │                                                                    │  │
│  │  Dimension 5: REPOSITORY_RELEVANCE (0.7)                        │  │
│  │    - Service-wide scope: +0.7                                   │  │
│  │    - Applies to all AuthService usage                           │  │
│  │    Total: 0.7                                                     │  │
│  │                                                                    │  │
│  │  FINAL SCORE:                                                   │  │
│  │    = 0.30 × 0.8 + 0.25 × 1.0 + 0.20 × 0.85                      │  │
│  │      + 0.15 × 0.9 + 0.10 × 0.7                                  │  │
│  │    = 0.24 + 0.25 + 0.17 + 0.135 + 0.07                          │  │
│  │    = 0.865                                                       │  │
│  │                                                                    │  │
│  │  DECISION: ADMIT (score >= 0.7)                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Rejected facts (example):                                              │
│    - "Agent thought about trying cache first" (speculation, conf=0.3) │
│    - "Line 42 has a typo" (too specific, importance=0.2)              │
│                                                                         │
└────────────────────────────┬───────────────────────────────────────────┘
                             │ ADMIT
                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                ENTITY RESOLUTION SERVICE                                │
│                                                                         │
│  For each entity:                                                      │
│                                                                         │
│  Entity: AuthService                                                   │
│    - Search: name ~= "AuthService", repository == current_repo        │
│    - Found: AuthService (uuid: abc-123, confidence: 0.88)             │
│    - Similarity: 0.95 (high match)                                    │
│    - Decision: MERGE - Update existing entity                         │
│                                                                         │
│  Entity: TokenService                                                   │
│    - Search: name ~= "TokenService", repository == current_repo       │
│    - Found: TokenService (uuid: def-456, confidence: 0.90)           │
│    - Similarity: 0.98 (exact match)                                   │
│    - Decision: LINK - Add relationship to existing                     │
│                                                                         │
│  Conflict Detection:                                                   │
│    - Check: Does this contradict existing relationships?              │
│    - None found → Proceed                                              │
│                                                                         │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   MEMORY PROVIDER INTERFACE                             │
│                                                                         │
│  Abstract interface - implementation agnostic                          │
│                                                                         │
│  Methods:                                                              │
│    - store_entity(entity_type, properties) → UUID                     │
│    - update_entity(uuid, properties) → bool                           │
│    - store_relationship(source, target, type, props) → UUID           │
│    - search_semantic(query, types, limit) → [(entity, score)]        │
│    - traverse_graph(start_uuid, relation_types, max_hops) → [entity]│
│                                                                         │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      GRAPHITI PROVIDER                                 │
│                                                                         │
│  Implementation of MemoryProvider using Graphiti SDK                    │
│                                                                         │
│  Actions:                                                              │
│    1. Update AuthService entity (confidence: 0.88 → 0.90)            │
│       (verified via successful execution)                              │
│                                                                         │
│    2. Create Fix entity:                                               │
│       {                                                                 │
│         uuid: "fix-789",                                               │
│         title: "Add idempotency key to token refresh",                │
│         solution: "Use request-idempotency-key...",                   │
│         prevention: "Apply idempotency pattern to all critical ops",  │
│         implemented_at: "2025-07-18T10:30:00Z",                        │
│         verified_at: "2025-07-18T10:30:45Z",                          │
│         confidence: 0.98                                               │
│       }                                                                 │
│                                                                         │
│    3. Create relationships:                                            │
│       - Fix FIXES Bug (race conditioner)                              │
│       - AuthService DEPENDS_ON TokenService (update confidence)        │
│                                                                         │
│    4. Add provenance metadata:                                         │
│       - source_execution_id: "exec-12345"                              │
│       - extracted_at: "2025-07-18T10:35:00Z"                           │
│       - admission_score: 0.865                                        │
│                                                                         │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE GRAPH (Neo4j)                               │
│                                                                         │
│  ┌───────────────┐         ┌───────────────┐                          │
│  │ AuthService  │─DEPENDS_ON─▶│ TokenService │                          │
│  │ Service      │         │ Service      │                          │
│  │ conf: 0.90   │         │ conf: 0.92   │                          │
│  └───────────────┘         └───────────────┘                          │
│         │                                                                │
│         │ HAS_ISSUE                                                      │
│         ▼                                                                │
│  ┌───────────────┐                                                      │
│  │ Race Condition │                                                      │
│  │ Bug            │                                                      │
│  │ status: fixed│                                                      │
│  └───────────────┘                                                      │
│         │                                                                │
│         │ FIXED_BY                                                       │
│         ▼                                                                │
│  ┌─────────────────────────────────────┐                               │
│  │ Idempotency Fix                     │                               │
│  │ Fix                                  │                               │
│  │ solution: Use request-idempotency-key │                               │
│  │ prevention: Apply to all critical ops │                               │
│  │ verified: 2025-07-18                │                               │
│  │ confidence: 0.98                    │                               │
│  └─────────────────────────────────────┘                               │
│                                                                         │
│  Indexes Used:                                                         │
│    - service_name, module_path, repository_url                          │
│    - memory_created_at, memory_confidence                              │
│    - relationship_types (DEPENDS_ON, FIXES, etc.)                     │
│                                                                         │
│  Constraints:                                                          │
│    - UUIDs unique                                                       │
│    - Entity types valid                                                 │
│    - Relationship schemas enforced                                      │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                BACKGROUND WORKERS (Continuous)                          │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  EXTRACTION WORKERS (×3)                                      │     │
│  │    - Process Extraction Queue (high priority)                │     │
│  │    - Extract knowledge from conversations                    │     │
│  │    - Enqueue to Admission Queue                              │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  ADMISSION WORKERS (×2)                                       │     │
│  │    - Process Admission Queue (medium priority)               │     │
│  │    - Apply admission policy scoring                          │     │
│  │    - Enqueue to Entity Resolution Queue                      │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  ARCHIVAL WORKER (×1)                                         │     │
│  │    - Process Archival Queue (low priority)                   │     │
│  │    - Find stale memories (>365 days old)                     │     │
│  │    - Mark as ARCHIVED                                         │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  DEAD LETTER PROCESSOR                                        │     │
│  │    - Review failed jobs                                       │     │
│  │    - Retry if temporary error                                │     │
│  │    - Alert if permanent error                                 │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Memory Lifecycle Timeline

```
Time →

T+0s:    Agent completes task
         │
         ├─▶ Execution Recorder captures result
         │    (task, result, files, time, success flag)
         │
         ▼
T+5s:    Job enqueued: Extraction Queue
         │
         ├─▶ EXTRACTED (background worker starts)
         │
         └─▶ [AGENT CONTINUES - DOES NOT WAIT]
             (This is the key benefit: async processing)

T+30s:   Extraction Worker processing
         │
         ├─▶ LLM extracts facts, entities, relationships
         │
         └─▶ Job enqueued: Admission Queue

T+35s:   Admission Worker processing
         │
         ├─▶ 5-dimension scoring
         │
         └─▶ Decision: ADMIT (score 0.865)

T+40s:   Entity Resolution
         │
         ├─▶ Fuzzy matching on AuthService, TokenService
         │
         └─▶ Decision: MERGE existing, LINK relationships

T+45s:   STORED in Graphiti/Neo4j
         │
         ├─▶ Entities updated
         ├─▶ Relationships created
         └─▶ Provenance metadata added

T+50s:   Memory available for future retrieval
         │
         └─▶ Next task will retrieve this knowledge


[TIME SKIP: 6 MONTHS LATER]

T+180 days: Archival Worker processing
            │
            ├─▶ Memory age > 365 days? No
            ├─▶ Not accessed in 90 days? No
            └─▶ Keep in active memory

[TIME SKIP: 1 YEAR LATER]

T+365 days: Archival Worker processing
            │
            ├─▶ Memory age > 365 days? Yes
            ├─▶ Last accessed 30 days ago
            │
            └─▶ Decision: Keep active (still relevant)

[TIME SKIP: 2 YEARS LATER]

T+730 days: Archival Worker processing
            │
            ├─▶ Memory age > 365 days? Yes
            ├─▶ Last accessed 400 days ago
            │
            └─▶ Decision: ARCHIVE
                - Mark as ARCHIVED
                - Move to cold storage
                - Keep UUID for provenance
                - Remove from active retrieval
```

---

## Token Budget Example

```
Retrieval returned 35 memories (before filtering)

Context Builder allocates 2000 tokens:

Tier 1 (HIGH confidence, HIGH relevance): Top 10 memories
  - Full content: ~1000 tokens

Tier 2 (MEDIUM confidence, MEDIUM relevance): Next 15 memories
  - Summarized: ~600 tokens

Tier 3 (LOW confidence, HIGH novelty): Next 10 memories
  - Titles only: ~200 tokens

Total injected: 1800 tokens (within 2000 budget)
Memory hit rate: 85% (35/41 memories presented)

Example injection:

<RELEVANT_KNOWLEDGE>
[ARCHITECTURE] AuthService - Authentication Service
  Depends: TokenService, UserDB
  Pattern: Repository Pattern
  Conf: HIGH (0.92)
  Verified: 2025-03-15

[BUG_FIX] Race Condition Fix (FULL)
  Root cause: Concurrent token refresh requests
  Solution: Added idempotency key header
  Prevention: Apply to all critical operations
  Conf: VERIFIED (0.98)
  Verified: 2025-07-10

The AuthService component requires idempotency patterns for...
[SUMMARY] 15 additional memories about token management...
</RELEVANT_KNOWLEDGE>
```

---

## Queue Backpressure Example

```
Normal Operation:
┌─────────────────┐
│ Extraction Queue│ ████████░░ (8/10 jobs)
└─────────────────┘
Workers can keep up

Burst (Many executions completed):
┌─────────────────┐
│ Extraction Queue│ ████████████████████ (20/20 jobs, FULL)
└─────────────────┘
Backpressure: New jobs REJECTED
Agent logs warning, continues without memory storage

Worker scaling:
┌─────────────────┐
│ Extraction Queue│ ████████████████████ (FULL)
└─────────────────┘
         │
         ├─▶ Alert: Queue depth > 80%
         ├─▶ Auto-scale: Add 2 workers (3 → 5)
         │
         ▼ (30 seconds later)
┌─────────────────┐
│ Extraction Queue│ ████████░░ (8/10 jobs)
└─────────────────┘
Backpressure relieved
```

---

## Conflict Resolution Example

```
Scenario: Existing memory says "AuthService uses Redis for sessions"
          New extraction says "AuthService uses PostgreSQL for sessions"

┌────────────────────────────────────────────────────────────────────┐
│  CONFLICT DETECTED                                                 │
│                                                                     │
│  Existing: AuthService USES Redis (confidence: 0.75, age: 6 months)│
│  New Fact: AuthService USES PostgreSQL (confidence: 0.92, age: new)│
│                                                                     │
│  Detection: Same relationship type, different target              │
└────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│  RESOLUTION STRATEGY                                               │
│                                                                     │
│  Step 1: Confidence comparison                                     │
│    - Existing: 0.75                                                │
│    - New: 0.92 (higher)                                            │
│                                                                     │
│  Step 2: Temporal comparison                                       │
│    - Existing: 6 months old                                         │
│    - New: Current verification                                     │
│                                                                     │
│  Step 3: Conflict severity                                         │
│    - Severity: HIGH (both cannot be simultaneously true)          │
│                                                                     │
│  Decision:                                                          │
│    - If AUTO_RESOLVE_ENABLED:                                      │
│        - SUPERSEDE: Mark old as superseded by new                  │
│        - Add SUPERSEDES edge with reason                           │
│                                                                     │
│    - If MANUAL_REVIEW_REQUIRED:                                    │
│        - Create conflict alert                                      │
│        - Queue for human validation                                │
│        - Keep both temporaril                                      │
└────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│  RESULT (AUTO-RESOLVE)                                             │
│                                                                     │
│  AuthService ──USES──▶ PostgreSQL (conf: 0.92, current)          │
│     │                                                               │
│     └──formerly──▶ Redis (SUPERSEDED, conf: 0.75)                 │
│                       │                                             │
│                       └──SUPERSEDED_BY──▶ PostgreSQL              │
│                                                     (reason: ...)    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Comparison: Current vs. Proposed

| Dimension | Current (PoC) | Proposed |
|-----------|---------------|----------|
| **Storage Backend** | Direct Graphiti | Provider abstraction (Graphiti, Neo4j, etc.) |
| **Extraction** | Regex patterns (MemoryScorer) | LLM-directed (KnowledgeExtractor) |
| **Admission** | Single threshold (conf > 0.7) | 5-dimension scoring |
| **Entity Resolution** | Basic deduplication | Fuzzy matching + conflict resolution |
| **Retrieval** | Semantic search only | 5-stage pipeline |
| **Ranking** | Graphiti similarity | Weighted 5-signal algorithm |
| **Context Building** | Simple concatenation | Token budgeting + summarization |
| **Lifecycle** | None (memories live forever) | Archival, expiration, governance |
| **Processing** | Synchronous (blocks agent) | Asynchronous (background workers) |
| **Observability** | Basic logging | Metrics, tracing, dashboards |
| **Scalability** | Limited (sync) | High (queue-based) |
| **Provider Lock-in** | Tied to Graphiti | Interface abstraction |
| **Manual Tools** | MCP server (remember_*) | Removed (automatic only) |
| **Latency (retrieval)** | ~50ms (vector only) | ~200-300ms (5 stages) |
| **Quality (admission)** | 100% admitted | 20-40% admitted (quality filter) |
|**Duplicates** | Common (no resolution) | <5% (fuzzy matching) |
| **Memory Value** | Low (unfiltered) | High (curated knowledge) |

---

## Key Insight

**This architecture trades:**
- Simplicity → Complexity
- Speed → Accuracy
- Convenience → Control

**For:**
- Correctness (evidence-driven, verified)
- Maintainability (clear interfaces, separation)
- Scalability (async processing, queues)
- Explainability (provenance, scores)
- Long-term value (quality memory accumulation)

**Use when:** Long-running agents, evidence-critical applications, multi-repo environments  
**Avoid when:** Short-lived tasks, prototype phase, simple codebases
