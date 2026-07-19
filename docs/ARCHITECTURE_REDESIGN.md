# Production-Grade Long-Term Memory Architecture for Autonomous Software Engineering Agents

**Author:** Lead Architect  
**Date:** 2026-07-18  
**Status:** Design Document (Not Yet Implemented)  
**Target:** Autonomous software engineering agents operating over months/years

---

## Executive Summary

This document designs a production-grade long-term memory architecture for AI agents, transforming the current proof-of-concept into a knowledge-based memory system optimized for:

- **Correctness** - Evidence-driven, validated memories
- **Maintainability** - Clear separation of concerns, extensible interfaces
- **Scalability** - Handles millions of memories across hundreds of repositories
- **Explainability** - Every memory has provenance, confidence, and justification
- **Repository Understanding** - Deep knowledge of codebases, not just facts
- **Low Token Usage** - Intelligent retrieval, compression, and summarization

**Key Architecture Decisions:**

1. **Graphiti as Knowledge Graph Backend** - Not a storage layer; use Graphiti's entity extraction and graph capabilities
2. **Conversation → Knowledge Separation** - Never store raw conversations; extract facts, decisions, patterns
3. **Admission Policy Gate** - Most inputs rejected; only high-value, novel knowledge admitted
4. **Multi-Stage Retrieval** - Combine semantic, graph, temporal, and context-aware retrieval
5. **Background Processing** - Latency-sensitive requests never wait for memory processing
6. **Provider Abstraction** - Business logic never depends directly on Graphiti

---

## Phase 2: Memory Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Autonomous Agent Execution                       │
│  (OpenHands, Aider, Cursor, etc.)                                       │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────┐
        │   Execution Recorder Service            │
        │   (captures: task, result, files, time)  │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │   Knowledge Extraction Pipeline          │
        │   (Conversation → Facts → Entities)      │
        │                                          │
        │   ┌────────────────────────────────┐   │
        │   │ LLM-based Fact Extractor        │   │
        │   │ Entity Recognizer               │   │
        │   │ Relationship Extractor          │   │
        │   │ Confidence Estimator            │   │
        │   └────────────────────────────────┘   │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │   Admission Policy Service               │
        │   (Should this be stored?)               │
        │                                          │
        │   Scoring:                               │
        │   - Importance (impact scope)           │
        │   - Novelty (new vs. duplicate)         │
        │   - Confidence (source reliability)     │
        │   - Persistence (long-term value)       │
        │   - Repository relevance                │
        │                                          │
        │   Decision: ADMIT | REJECT | DEFER       │
        └──────────────┬───────────────────────────┘
                       │ ADMIT
                       ▼
        ┌──────────────────────────────────────────┐
        │   Entity Resolution Service             │
        │   (Merge duplicates, resolve conflicts)  │
        │                                          │
        │   - Fuzzy entity matching               │
        │   - Conflict detection                  │
        │   - Merge strategy selection            │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │   Memory Provider Interface             │
        │   (Abstraction Layer)                   │
        │                                          │
        │   ┌──────────────┐  ┌────────────────┐  │
        │   │ Graphiti     │  │ Future: Other  │  │
        │   │ Provider     │  │ Providers      │  │
        │   └──────────────┘  └────────────────┘  │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │   Knowledge Graph (Graphiti + Neo4j)     │
        │                                          │
        │   Nodes: Entities (Service, Module,      │
        │          Pattern, Decision, Bug, Fix)    │
        │                                          │
        │   Edges: DEPENDS_ON, FIXES,              │
        │          IMPLEMENTS, CONFLICTS_WITH     │
        └──────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                        RETRIEVAL PATH (Before Task)                      │
└─────────────────────────────────────────────────────────────────────────┘

        Agent Task Request
                │
                ▼
        ┌──────────────────────────────────────────┐
        │   Retrieval Pipeline                     │
        │                                          │
        │   Stage 1: Semantic Search               │
        │   - Embed task description              │
        │   - Top-K similar memories              │
        │                                          │
        │   Stage 2: Graph Traversal               │
        │   - Follow relationships from seeds     │
        │   - 2-hop expansion                     │
        │                                          │
        │   Stage 3: Entity Lookup                 │
        │   - Extract entities from task          │
        │   - Direct entity queries               │
        │                                          │
        │   Stage 4: Context Filtering             │
        │   - Repository scope                    │
        │   - Branch scope                        │
        │   - Module scope                         │
        │                                          │
        │   Stage 5: Temporal Boosting             │
        │   - Recent memories weighted higher     │
        │   - Execution success bonus             │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │   Memory Scoring Service                │
        │                                          │
        │   Calculate:                             │
        │   - Relevance to task                   │
        │   - Confidence score                    │
        │   - Recency weight                      │
        │   - Graph centrality                    │
        │   - Execution success rate              │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │   Ranking Algorithm                      │
        │                                          │
        │   final_score = 0.30 * semantic_sim      │
        │                + 0.25 * graph_distance   │
        │                + 0.20 * confidence        │
        │                + 0.15 * recency           │
        │                + 0.10 * success_rate     │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │   Context Builder Service                │
        │                                          │
        │   - Token budget allocation              │
        │   - Memory deduplication                 │
        │   - Hierarchical formatting              │
        │   - Summarization (if needed)           │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │   Prompt Injection                       │
        │                                          │
        │   Inject into agent context:             │
        │                                          │
        │   <RELEVANT_KNOWLEDGE>                   │
        │   [Architecture] AuthService depends... │
        │   [Decision] Use PostgreSQL because...   │
        │   [BugFix] Fixed race condition by...    │
        │                                          │
        │   Confidence: HIGH | MEDIUM | LOW        │
        │   Last verified: 2025-03-15             │
        │   </RELEVANT_KNOWLEDGE>                  │
        └──────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                     BACKGROUND PROCESSING (Async)                       │
└─────────────────────────────────────────────────────────────────────────┘

        ┌──────────────────────────────────────────┐
        │   Queue-Based Architecture                │
        │                                          │
        │   ┌────────────────┐                    │
        │   │ Extraction Q   │ (high priority)    │
        │   └────────────────┘                    │
        │   ┌────────────────┐                    │
        │   │ Admission Q     │ (medium priority)  │
        │   └────────────────┘                    │
        │   ┌────────────────┐                    │
        │   │ Archival Q      │ (low priority)     │
        │   └────────────────┘                    │
        │                                          │
        │   Background Workers:                    │
        │   - Extraction Worker Pool              │
        │   - Admission Worker Pool               │
        │   - Entity Resolution Worker            │
        │   - Memory Governance Worker             │
        │   - Summarization Worker                 │
        └──────────────────────────────────────────┘

```

---

## Phase 3: Knowledge Model

### What Is Stored

**Entities:**

1. **Service** - Microservice, API, daemon
   - Properties: name, language, repository, status, owner
   - Example: AuthService, PaymentGateway, NotificationService

2. **Module** - Code module, package, directory
   - Properties: path, language, responsibilities, size
   - Example: auth/, payments/merchant/, notification/email/

3. **Repository** - Git repository
   - Properties: url, name, primary_language, framework, owner
   - Example: github.com/company/auth-service

4. **API** - REST endpoint, GraphQL query, RPC method
   - Properties: endpoint, method, request_schema, response_schema
   - Example: POST /auth/login, GET /users/{id}

5. **Database** - Database instance, schema
   - Properties: name, type (PostgreSQL, Redis), schema_version, migration_policy
   - Example: auth-db, user-cache, payment-ledger

6. **Library** - External dependency
   - Properties: name, version, license, language, repository_url
   - Example: Django@4.2, react@18.2, redis-py@5.0

7. **Pattern** - Architectural pattern, design pattern
   - Properties: name, category, description, pros, cons
   - Example: Repository Pattern, CQRS, Circuit Breaker

8. **Decision** - Design decision, architectural choice
   - Properties: title, rationale, alternatives, tradeoffs, status, made_by, made_at
   - Example: Use PostgreSQL instead of MongoDB, Implement CQRS

9. **Bug** - Known bug, issue, limitation
   - Properties: title, symptoms, root_cause, status, severity, discovered_at
   - Example: Race condition in token refresh, Memory leak in worker process

10. **Fix** - Bug fix, workaround
    - Properties: title, solution, prevention, implemented_at, verified_at
    - Example: Add idempotency key to token refresh, Implement connection pooling

11. **Convention** - Coding standard, best practice
    - Properties: rule, rationale, examples, anti_patterns, scope
    - Example: Use dependency injection for services, Never commit API keys

**Relationships:**

1. **DEPENDS_ON** - Runtime dependency
   - Source: Service, Module
   - Target: Service, Database, Library
   - Properties: type (sync, async), criticality (critical, non-critical)

2. **USES** - Usage relationship
   - Source: Service, Module, API
   - Target: Library, Pattern, API
   - Properties: purpose, frequency

3. **IMPLEMENTS** - Implementation relationship
   - Source: Service, Module
   - Target: Pattern, API
   - Properties: variant, completeness

4. **FIXES** - Bug fix relationship
   - Source: Fix
   - Target: Bug
   - Properties: verified, verified_at

5. **CONFLICTS_WITH** - Incompatibility
   - Source: Decision, Pattern, Convention
   - Target: Decision, Pattern, Convention
   - Properties: reason, resolution

6. **PART_OF** - Containment
   - Source: Module, API
   - Target: Service, Repository
   - Properties: layer

7. **OWNS** - Ownership
   - Source: Service, Module
   - Target: API, Database
   - Properties: since

8. **SUPERSEDES** - Replacement
   - Source: Decision, Pattern, Convention
   - Target: Decision, Pattern, Convention
   - Properties: reason, superseded_at

9. **RELATES_TO** - Related concept (only when no specific edge applies)
   - Source: Any
   - Target: Any
   - Properties: relationship_type (explain in properties)

**What is NOT Stored:**

- Raw conversations
- Stack traces (unless bug context, then stored as Bug.symptoms)
- Temporary debugging notes
- Unverified assumptions
- Low-confidence guesses
- Temporary file paths or temporary directories

---

## Phase 4: Memory Lifecycle

### Complete Flow

```
Conversation (Agent Execution)
    │
    ▼
┌─────────────────────────────────────┐
│ Stage 1: Execution Recording        │
│                                     │
│ Capture:                            │
│ - Task description                  │
│ - Agent response                    │
│ - Files changed                     │
│ - Execution time                    │
│ - Success/failure flag             │
│ - Repository, branch, module       │
│ - User/workspace context            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Stage 2: Knowledge Extraction       │
│ (Background, LLM-powered)           │
│                                     │
│ Extract Facts:                      │
│ - What was learned?                 │
│ - Which entities involved?          │
│ - What relationships discovered?    │
│ - What decisions made?              │
│ - What patterns applied?            │
│ - What bugs fixed/encountered?      │
│                                     │
│ Output:                             │
│ - facts: List[Fact]                 │
│ - entities: List[Entity]            │
│ - relationships: List[Relation]     │
│ - confidence: float (0-1)           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Stage 3: Admission Policy           │
│                                     │
│ Score each fact:                    │
│                                     │
│ Importance:                          │
│ - Does it affect core system?       │
│ - How many components impacted?     │
│                                     │
│ Novelty:                             │
│ - Is this already known?            │
│ - Similarity to existing memories   │
│                                     │
│ Confidence:                          │
│ - Source reliability (verified code │
│   vs. speculation)                  │
│ - Execution success                 │
│                                     │
│ Persistence:                         │
│ - Will this be valid in 6 months?   │
│ - Is it specific to current code?   │
│                                     │
│ Repository relevance:               │
│ - Does it apply broadly?            │
│ - Is it repository-specific?        │
│                                     │
│ Decision:                           │
│ - ADMIT (score >= 0.7)              │
│ - REJECT (score < 0.3)              │
│ - DEFER (score 0.3-0.7)             │
└──────────────┬──────────────────────┘
               │ ADMIT
               ▼
┌─────────────────────────────────────┐
│ Stage 4: Entity Resolution          │
│                                     │
│ For each entity:                     │
│ - Find similar existing entities    │
│ - Calculate similarity score        │
│ - If match found:                   │
│   - Merge or link                   │
│ - If no match:                      │
│   - Create new entity                │
│                                     │
│ Conflict Detection:                  │
│ - Does this contradict existing?    │
│ - If yes: resolve conflict          │
│   - Human validation (if critical)  │
│   - Auto-resolve (if trivial)       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Stage 5: Storage                    │
│                                     │
│ For each admitted fact:             │
│ - Store entity (if new)             │
│ - Update entity (if exists)         │
│ - Store relationships               │
│ - Add provenance metadata:          │
│   - source_execution_id             │
│   - extracted_at                    │
│   - extracted_by                    │
│   - confidence_score                │
│   - admission_score                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Stage 6: Retrieval (Before Task)    │
│                                     │
│ Multi-stage retrieval:              │
│                                     │
│ 1. Semantic search (vector sim)    │
│ 2. Graph traversal (relationships) │
│ 3. Entity lookup (direct)           │
│ 4. Context filtering               │
│ 5. Temporal boosting                │
│                                     │
│ Ranking:                            │
│ - Combine 5 signals                 │
│ - Return top-K                       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Stage 7: Ranking                     │
│                                     │
│ For each candidate memory:          │
│                                     │
│ Calculate:                           │
│ - relevance_score                   │
│ - confidence_score                  │
│ - recency_score                      │
│ - centrality_score                  │
│ - success_rate_score                │
│                                     │
│ Weighted sum:                        │
│ final = 0.30 * relevance            │
│       + 0.25 * centrality            │
│       + 0.20 * confidence            │
│       + 0.15 * recency               │
│       + 0.10 * success_rate          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Stage 8: Prompt Injection           │
│                                     │
│ Format for agent:                    │
│                                     │
│ <RELEVANT_KNOWLEDGE>                │
│                                     │
│ [Architecture] AuthService          │
│ Service: Authentication             │
│ Depends on: TokenService, UserDB    │
│ Pattern: Repository Pattern          │
│ Confidence: HIGH                     │
│ Last verified: 2025-03-15           │
│                                     │
│ [Decision] Use PostgreSQL           │
│ Rationale: ACID transactions needed │
│ Alternatives: MongoDB (rejected)    │
│ Confidence: VERIFIED                │
│ Made: 2024-11-20                    │
│                                     │
│ </RELEVANT_KNOWLEDGE>                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Stage 9: Memory Update              │
│                                     │
│ After task execution:               │
│ - Update memory confidence          │
│ - If successful: increase           │
│ - If failed: decrease               │
│ - Record usage_timestamp            │
│                                     │
│ Verification:                        │
│ - If code executed successfully,    │
│   mark as VERIFIED                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Stage 10: Archival                  │
│                                     │
│ Trigger conditions:                 │
│ - Age > expiry_days (default 365)  │
│ - Not accessed in 180 days         │
│ - Confidence drops below 0.3       │
│ - Contradicted by newer fact        │
│                                     │
│ Actions:                            │
│ - Mark as ARCHIVED                  │
│ - Move to cold storage              │
│ - Keep reference for provenance     │
│ - Do not delete (audit trail)       │
└─────────────────────────────────────┘
```

---

## Phase 5: Admission Policy

### Scoring System Design

**Five-Dimensional Score:**

Each extracted fact receives 5 scores (0.0 to 1.0):

```python
class AdmissionScore:
    importance: float      # How impactful is this knowledge?
    novelty: float         # How new is this knowledge?
    confidence: float      # How reliable is the source?
    persistence: float     # How long will this remain valid?
    repository_relevance: float  # How broadly does this apply?

    @property
    def final_score(self) -> float:
        """Weighted combination."""
        return (
            0.30 * self.importance +
            0.25 * self.novelty +
            0.20 * self.confidence +
            0.15 * self.persistence +
            0.10 * self.repository_relevance
        )
```

### Dimension Rationales

**1. Importance (30% weight)**

**Why:** Not all knowledge is equal. Some affects core architecture; some is minor details.

**Calculation:**
- Affects multiple services: +0.3
- Affects critical path: +0.2
- Architectural decision: +0.3
- Bug fix with prevention: +0.2
- Coding convention: +0.1

**Example:**
- Fact: "AuthService depends on TokenService"
  - Importance: 0.9 (affects critical path, multiple services)
- Fact: "Variable naming uses snake_case"
  - Importance: 0.3 (minor convention)

**2. Novelty (25% weight)**

**Why:** Duplicates waste storage and retrieval. We need to detect what's truly new.

**Calculation:**
- Exact duplicate exists: 0.0
- Similar fact exists (similarity > 0.8): 0.3
- Partially overlaps (similarity 0.5-0.8): 0.6
- Completely new: 1.0

**Example:**
- Fact: "AuthService uses TokenService" (already exists as "AuthService depends on TokenService")
  - Novelty: 0.2 (near duplicate)
- Fact: "New payment gateway integration"
  - Novelty: 1.0 (new knowledge)

**3. Confidence (20% weight)**

**Why:** Source reliability varies. Verified code execution > speculation.

**Calculation:**
- Verified via execution: 0.95
- Extracted from successful task: 0.85
- Extracted from failed task (but intent clear): 0.7
- Speculation or hypothesis: 0.4
- Contradicted by evidence: 0.1

**Example:**
- Fact: "Fixed bug by adding idempotency key" (verified execution)
  - Confidence: 0.95
- Fact: "Might need to refactor later" (speculation)
  - Confidence: 0.3

**4. Persistence (15% weight)**

**Why:** Some knowledge is transient (current implementation); some is durable (architectural).

**Calculation:**
- Architectural pattern: 0.95 (very durable)
- Design decision: 0.85
- Dependency version: 0.5 (will change)
- Current code structure: 0.4 (will refactor)
- Temporary workaround: 0.2

**Example:**
- Fact: "Use Repository Pattern for data access"
  - Persistence: 0.95 (long-term pattern)
- Fact: "Current auth module in /tmp/auth"
  - Persistence: 0.2 (will move)

**5. Repository Relevance (10% weight)**

**Why:** Knowledge scope matters. Some is repository-specific; some applies broadly.

**Calculation:**
- Applies across multiple repos: 0.9
- Repository-wide (all modules): 0.7
- Module-specific: 0.5
- File-specific: 0.3
- Line-specific: 0.1

**Example:**
- Fact: "Use PostgreSQL for all services"
  - Repository relevance: 0.8 (cross-repo)
- Fact: "Line 42 has a bug"
  - Repository relevance: 0.1 (line-specific)

### Admission Decision

```python
if admission_score.final_score >= 0.7:
    decision = AdmissionDecision.ADMIT
elif admission_score.final_score >= 0.3:
    decision = AdmissionDecision.DEFER  # Re-evaluate later
else:
    decision = AdmissionDecision.REJECT
```

---

## Phase 6: Retrieval Pipeline

### Five-Stage Retrieval

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: Semantic Search (Vector Similarity)               │
│                                                             │
│ Input: Task description embedding                          │
│ Output: Top-50 similar memories                            │
│                                                             │
│ Method: Graphiti search_nodes(query=task, limit=50)        │
│ Time: ~50ms                                                 │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Graph Traversal (Relationship Expansion)          │
│                                                             │
│ For each seed memory from Stage 1:                         │
│ - Follow DEPENDS_ON edges (2 hops)                         │
│ - Follow IMPLEMENTS edges                                  │
│ - Follow FIXES edges (for bug context)                     │
│                                                             │
│ Output: Expanded graph context (additional 100-200 nodes)  │
│ Time: ~100ms                                                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: Entity Lookup (Direct Query)                       │
│                                                             │
│ Extract entities from task description:                     │
│ - Named entities (AuthService, UserDB)                     │
│ - Concepts (authentication, payment)                         │
│                                                             │
│ Direct query for each entity:                               │
│ - Get entity node                                          │
│ - Get all relationships                                     │
│                                                             │
│ Output: Entity-centric context                             │
│ Time: ~30ms                                                 │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 4: Context Filtering                                  │
│                                                             │
│ Filter by scope:                                            │
│ - Repository: repository == current_repo                   │
│ - Branch: branch == current_branch OR branch == 'main'     │
│ - Module: module == current_module OR module == null        │
│                                                             │
│ Filter by type:                                             │
│ - Include: ARCHITECTURE, DECISION, BUG_FIX, CONVENTION      │
│ - Exclude: Low confidence (< 0.5)                           │
│                                                             │
│ Output: Scoped, filtered memories                          │
│ Time: ~5ms                                                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 5: Temporal Boosting                                  │
│                                                             │
│ Boost recent memories:                                      │
│ - Age < 7 days: boost by 0.3                               │
│ - Age 7-30 days: boost by 0.2                              │
│ - Age 30-90 days: boost by 0.1                             │
│                                                             │
│ Boost verified execution:                                   │
│ - If last_execution_success: boost by 0.15                 │
│                                                             │
│ Output: Temporal-weighted memories                         │
│ Time: ~5ms                                                   │
└─────────────────────────────────────────────────────────────┘
```

### Ranking Algorithm

```python
def rank_memories(
    memories: List[Memory],
    task: str,
    context: TaskContext
) -> List[RankedMemory]:
    
    ranked = []
    
    for memory in memories:
        # Calculate 5 signals
        
        # Signal 1: Semantic relevance (from Stage 1)
        semantic_score = memory.semantic_similarity_score  # 0.0-1.0
        
        # Signal 2: Graph distance (from Stage 2)
        # Shorter path = higher score
        graph_score = 1.0 / (memory.hops_from_seed + 1)
        
        # Signal 3: Confidence (stored value)
        confidence_score = memory.confidence  # 0.0-1.0
        
        # Signal 4: Recency (from Stage 5)
        age_days = (now - memory.created_at).days
        if age_days < 7:
            recency_score = 1.0
        elif age_days < 30:
            recency_score = 0.85
        elif age_days < 90:
            recency_score = 0.7
        else:
            recency_score = 0.5
        
        # Signal 5: Execution success rate
        success_rate = memory.successful_uses / max(memory.total_uses, 1)
        
        # Weighted combination
        final_score = (
            0.30 * semantic_score +
            0.25 * graph_score +
            0.20 * confidence_score +
            0.15 * recency_score +
            0.10 * success_rate
        )
        
        ranked.append(RankedMemory(
            memory=memory,
            final_score=final_score,
            breakdown={
                "semantic": semantic_score,
                "graph": graph_score,
                "confidence": confidence_score,
                "recency": recency_score,
                "success_rate": success_rate
            }
        ))
    
    # Sort by final_score descending
    ranked.sort(key=lambda x: x.final_score, reverse=True)
    
    return ranked[:20]  # Return top 20
```

---

## Phase 7: Graph Schema

### Neo4j/Graphiti Schema

```cypher
// === ENTITY NODES ===

// Service entity
CREATE CONSTRAINT service_unique IF NOT EXISTS
FOR (s:Service) REQUIRE s.uuid IS UNIQUE;

CREATE INDEX service_name IF NOT EXISTS
FOR (s:Service) ON (s.name);

CREATE INDEX service_repository IF NOT EXISTS
FOR (s:Service) ON (s.repository);

// Module entity
CREATE CONSTRAINT module_unique IF NOT EXISTS
FOR (m:Module) REQUIRE m.uuid IS UNIQUE;

CREATE INDEX module_path IF NOT EXISTS
FOR (m:Module) ON (m.path);

// Repository entity
CREATE CONSTRAINT repository_unique IF NOT EXISTS
FOR (r:Repository) REQUIRE r.uuid IS UNIQUE;

CREATE INDEX repository_url IF NOT EXISTS
FOR (r:Repository) ON (r.url);

// API entity
CREATE CONSTRAINT api_unique IF NOT EXISTS
FOR (a:API) REQUIRE a.uuid IS UNIQUE;

CREATE INDEX api_endpoint IF NOT EXISTS
FOR (a:API) ON (a.endpoint);

// Database entity
CREATE CONSTRAINT database_unique IF NOT EXISTS
FOR (d:Database) REQUIRE d.uuid IS UNIQUE;

// Library entity
CREATE CONSTRAINT library_unique IF NOT EXISTS
FOR (l:Library) REQUIRE l.uuid IS UNIQUE;

// Pattern entity
CREATE CONSTRAINT pattern_unique IF NOT EXISTS
FOR (p:Pattern) REQUIRE p.uuid IS UNIQUE;

// Decision entity
CREATE CONSTRAINT decision_unique IF NOT EXISTS
FOR (d:Decision) REQUIRE d.uuid IS UNIQUE;

CREATE INDEX decision_status IF NOT EXISTS
FOR (d:Decision) ON (d.status);

// Bug entity
CREATE CONSTRAINT bug_unique IF NOT EXISTS
FOR (b:Bug) REQUIRE b.uuid IS UNIQUE;

CREATE INDEX bug_status IF NOT EXISTS
FOR (b:Bug) ON (b.status);

// Fix entity
CREATE CONSTRAINT fix_unique IF NOT EXISTS
FOR (f:Fix) REQUIRE f.uuid IS UNIQUE;

// Convention entity
CREATE CONSTRAINT convention_unique IF NOT EXISTS
FOR (c:Convention) REQUIRE c.uuid IS UNIQUE;

// === RELATIONSHIP EDGES ===

// DEPENDS_ON relationship
CREATE INDEX depends_on_type IF NOT EXISTS
FOR ()-[r:DEPENDS_ON]-() ON (r.type);

// IMPLEMENTS relationship
CREATE INDEX implements_variant IF NOT EXISTS
FOR ()-[r:IMPLEMENTS]-() ON (r.variant);

// === TEMPORAL INDEXES ===

CREATE INDEX memory_created_at IF NOT EXISTS
FOR (n:Memory) ON (n.created_at);

CREATE INDEX memory_updated_at IF NOT EXISTS
FOR (n:Memory) ON (n.updated_at);

CREATE INDEX memory_verified_at IF NOT EXISTS
FOR (n:Memory) ON (n.verified_at);

// === CONFIDENCE INDEX ===

CREATE INDEX memory_confidence IF NOT EXISTS
FOR (n:Memory) ON (n.confidence);

// === SCOPE INDEXES ===

CREATE INDEX memory_repository IF NOT EXISTS
FOR (n:Memory) ON (n.repository);

CREATE INDEX memory_branch IF NOT EXISTS
FOR (n:Memory) ON (n.branch);
```

### Node Properties

```yaml
Service:
  uuid: UUID (required, unique)
  name: String (required, indexed)
  repository: String (required, indexed)
  branch: String (required)
  language: String
  status: Enum [active, deprecated, removed]
  owner: String
  confidence: Float (0.0-1.0, indexed)
  created_at: DateTime (indexed)
  updated_at: DateTime (indexed)
  verified_at: DateTime (indexed)
  source_execution_id: UUID
  successful_uses: Integer (default: 0)
  total_uses: Integer (default: 0)

Module:
  uuid: UUID (required, unique)
  path: String (required, indexed)
  repository: String (required, indexed)
  branch: String (required)
  service: String
  language: String
  responsibilities: List<String>
  confidence: Float
  created_at: DateTime
  updated_at: DateTime

Repository:
  uuid: UUID (required, unique)
  url: String (required, indexed)
  name: String
  primary_language: String
  framework: String
  owner: String
  confidence: Float
  created_at: DateTime
  
API:
  uuid: UUID (required, unique)
  endpoint: String (required, indexed)
  method: Enum [GET, POST, PUT, DELETE, PATCH]
  request_schema: JSON
  response_schema: JSON
  service: String
  repository: String
  confidence: Float
  created_at: DateTime

Decision:
  uuid: UUID (required, unique)
  title: String (required)
  rationale: String (required)
  alternatives: List<String>
  tradeoffs: String
  status: Enum [proposed, accepted, rejected, superseded] (indexed)
  made_by: String
  made_at: DateTime
  repository: String
  confidence: Float
  created_at: DateTime

Bug:
  uuid: UUID (required, unique)
  title: String (required)
  symptoms: List<String>
  root_cause: String
  status: Enum [open, fixed, wontfix] (indexed)
  severity: Enum [critical, high, medium, low]
  discovered_at: DateTime
  repository: String
  module: String
  confidence: Float
  created_at: DateTime

Fix:
  uuid: UUID (required, unique)
  title: String (required)
  solution: String (required)
  prevention: String
  implemented_at: DateTime
  verified_at: DateTime (indexed)
  repository: String
  confidence: Float
  created_at: DateTime
```

### Relationship Properties

```yaml
DEPENDS_ON:
  type: Enum [sync, async]
  criticality: Enum [critical, non_critical]
  created_at: DateTime
  confidence: Float

USES:
  purpose: String
  frequency: Enum [always, often, sometimes, rarely]
  created_at: DateTime
  confidence: Float

IMPLEMENTS:
  variant: String
  completeness: Float (0.0-1.0)
  created_at: DateTime
  confidence: Float

FIXES:
  verified: Boolean
  verified_at: DateTime
  confidence: Float

CONFLICTS_WITH:
  reason: String (required)
  resolution: String
  created_at: DateTime
  confidence: Float

PART_OF:
  layer: Enum [presentation, business, data, infrastructure]
  created_at: DateTime

OWNS:
  since: DateTime
  created_at: DateTime

SUPERSEDES:
  reason: String (required)
  superseded_at: DateTime (required)
  confidence: Float
```

---

## Phase 8: Provider Architecture

### Interface Design

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

class MemoryProvider(ABC):
    """
    Abstract interface for memory storage backends.
    
    Business logic NEVER depends directly on Graphiti or Neo4j.
    All interactions go through this interface.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize connection to backend."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close connection."""
        pass
    
    @abstractmethod
    async def store_entity(
        self,
        entity_type: str,
        properties: Dict[str, Any]
    ) -> UUID:
        """
        Store an entity node.
        
        Args:
            entity_type: Entity type (Service, Module, Decision, etc.)
            properties: Entity properties (validated by schema)
            
        Returns:
            UUID of stored entity
        """
        pass
    
    @abstractmethod
    async def update_entity(
        self,
        uuid: UUID,
        properties: Dict[str, Any]
    ) -> bool:
        """Update entity properties."""
        pass
    
    @abstractmethod
    async def get_entity(self, uuid: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve entity by UUID."""
        pass
    
    @abstractmethod
    async def delete_entity(self, uuid: UUID) -> bool:
        """Delete entity."""
        pass
    
    @abstractmethod
    async def store_relationship(
        self,
        source_uuid: UUID,
        target_uuid: UUID,
        relation_type: str,
        properties: Dict[str, Any]
    ) -> UUID:
        """Store relationship edge."""
        pass
    
    @abstractmethod
    async def search_semantic(
        self,
        query: str,
        entity_types: List[str],
        limit: int = 10
    ) -> List[tuple[Dict[str, Any], float]]:
        """
        Semantic search using vector embeddings.
        
        Returns:
            List of (entity, similarity_score) tuples
        """
        pass
    
    @abstractmethod
    async def traverse_graph(
        self,
        start_uuid: UUID,
        relation_types: List[str],
        max_hops: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Traverse graph following relationships.
        
        Returns:
            List of connected entities
        """
        pass
    
    @abstractmethod
    async def query_entities(
        self,
        entity_type: str,
        filters: Dict[str, Any],
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query entities by type and filters."""
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """Check backend health."""
        pass


class GraphitiProvider(MemoryProvider):
    """
    Graphiti implementation of MemoryProvider.
    
    Wraps Graphiti SDK and translates interface calls
    to Graphiti operations.
    """
    
    def __init__(self, config: GraphitiConfig):
        self.config = config
        self._graphiti = None
    
    async def initialize(self) -> None:
        from graphiti_core import Graphiti
        # Initialize Graphiti...
        
    async def store_entity(
        self,
        entity_type: str,
        properties: Dict[str, Any]
    ) -> UUID:
        # Translate to Graphiti add_episode or direct node creation
        # Graphiti extracts entities from episode text
        # We'll need to format properties as structured text
        pass
    
    # ... implement all methods
```

### Dependency Injection

```python
class MemoryService:
    """
    Core business logic for memory management.
    
    Dependencies:
    - MemoryProvider (injected, never Graphiti directly)
    - KnowledgeExtractor
    - AdmissionPolicy
    - EntityResolver
    """
    
    def __init__(
        self,
        provider: MemoryProvider,
        extractor: KnowledgeExtractor,
        admission_policy: AdmissionPolicy,
        entity_resolver: EntityResolver,
        logger: MemoryLogger
    ):
        self.provider = provider
        self.extractor = extractor
        self.admission_policy = admission_policy
        self.entity_resolver = entity_resolver
        self.logger = logger
    
    async def store_knowledge(
        self,
        conversation: str,
        context: ExecutionContext
    ) -> List[UUID]:
        """
        Business logic never knows about Graphiti.
        Works through provider interface.
        """
        # Extract facts
        facts = await self.extractor.extract(conversation, context)
        
        # Apply admission policy
        admitted = []
        for fact in facts:
            decision = await self.admission_policy.evaluate(fact)
            if decision == AdmissionDecision.ADMIT:
                admitted.append(fact)
        
        # Resolve entities
        resolved_entities = await self.entity_resolver.resolve(admitted)
        
        # Store through provider
        stored_uuids = []
        for entity in resolved_entities:
            uuid = await self.provider.store_entity(
                entity_type=entity.type,
                properties=entity.properties
            )
            stored_uuids.append(uuid)
        
        return stored_uuids
```

---

## Phase 9: Background Processing

### Queue Architecture

```python
from enum import Enum
from dataclasses import dataclass
from typing import Any
from uuid import UUID
import asyncio
from datetime import datetime

class QueueType(Enum):
    EXTRACTION = "extraction"      # High priority
    ADMISSION = "admission"         # Medium priority
    ARCHIVAL = "archival"           # Low priority
    ENTITY_RESOLUTION = "entity_resolution"
    SUMMARIZATION = "summarization"

@dataclass
class Job:
    id: UUID
    queue_type: QueueType
    payload: Dict[str, Any]
    created_at: datetime
    attempts: int = 0
    max_attempts: int = 3
    priority: int = 0  # Higher = more urgent

class MemoryQueue:
    """
    Priority queue with backpressure.
    
    Implements:
    - Multiple queues by priority
    - Dead-letter queue for failed jobs
    - Backpressure (max queue size)
    """
    
    def __init__(self, max_size: int = 10000):
        self.queues = {
            QueueType.EXTRACTION: asyncio.PriorityQueue(maxsize=max_size),
            QueueType.ADMISSION: asyncio.PriorityQueue(maxsize=max_size),
            QueueType.ARCHIVAL: asyncio.PriorityQueue(maxsize=max_size),
            QueueType.ENTITY_RESOLUTION: asyncio.PriorityQueue(maxsize=max_size),
            QueueType.SUMMARIZATION: asyncio.PriorityQueue(maxsize=max_size),
        }
        self.dead_letter_queue: List[Job] = []
        self.failed_jobs: Dict[UUID, Exception] = {}
    
    async def enqueue(self, job: Job) -> bool:
        """Enqueue job. Returns False if queue full."""
        try:
            queue = self.queues[job.queue_type]
            await queue.put((job.priority, job.created_at, job))
            return True
        except asyncio.QueueFull:
            return False
    
    async def dequeue(self, queue_type: QueueType) -> Job | None:
        """Dequeue job with timeout."""
        try:
            queue = self.queues[queue_type]
            _, _, job = await asyncio.wait_for(queue.get(), timeout=5.0)
            return job
        except asyncio.TimeoutError:
            return None
    
    async def mark_failed(self, job: Job, error: Exception) -> None:
        """Move job to dead-letter queue."""
        job.attempts += 1
        if job.attempts >= job.max_attempts:
            self.dead_letter_queue.append(job)
            self.failed_jobs[job.id] = error
        else:
            # Re-enqueue with exponential backoff
            await asyncio.sleep(2 ** job.attempts)
            await self.enqueue(job)

class WorkerPool:
    """
    Pool of background workers.
    
    Each worker type processes specific queue.
    """
    
    def __init__(
        self,
        queue: MemoryQueue,
        provider: MemoryProvider,
        num_extraction_workers: int = 3,
        num_admission_workers: int = 2,
        num_archival_workers: int = 1
    ):
        self.queue = queue
        self.provider = provider
        self.workers = []
        self.running = False
        
        # Create worker pools
        for _ in range(num_extraction_workers):
            self.workers.append(ExtractionWorker(queue, provider))
        
        for _ in range(num_admission_workers):
            self.workers.append(AdmissionWorker(queue, provider))
        
        for _ in range(num_archival_workers):
            self.workers.append(ArchivalWorker(queue, provider))
    
    async def start(self) -> None:
        """Start all workers."""
        self.running = True
        tasks = [worker.run() for worker in self.workers]
        await asyncio.gather(*tasks)
    
    async def stop(self) -> None:
        """Stop all workers gracefully."""
        self.running = False

class ExtractionWorker:
    """
    Processes EXTRACTION queue.
    
    Extracts knowledge from conversations.
    """
    
    async def process_job(self, job: Job) -> List[Fact]:
        conversation = job.payload["conversation"]
        context = job.payload["context"]
        
        # Use LLM to extract facts
        extractor = KnowledgeExtractor()
        facts = await extractor.extract(conversation, context)
        
        # Enqueue admission jobs
        for fact in facts:
            admission_job = Job(
                id=uuid4(),
                queue_type=QueueType.ADMISSION,
                payload={"fact": fact, "context": context},
                created_at=datetime.utcnow()
            )
            await self.queue.enqueue(admission_job)
        
        return facts

class AdmissionWorker:
    """Processes ADMISSION queue."""
    
    async def process_job(self, job: Job) -> Optional[UUID]:
        fact = job.payload["fact"]
        context = job.payload["context"]
        
        # Apply admission policy
        policy = AdmissionPolicy()
        decision = await policy.evaluate(fact)
        
        if decision.decision == AdmissionDecision.ADMIT:
            # Enqueue entity resolution
            resolution_job = Job(
                id=uuid4(),
                queue_type=QueueType.ENTITY_RESOLUTION,
                payload={"fact": fact, "context": context},
                created_at=datetime.utcnow()
            )
            await self.queue.enqueue(resolution_job)
            return fact.id
        return None

class ArchivalWorker:
    """Processes ARCHIVAL queue."""
    
    async def process_job(self, job: Job) -> int:
        # Find stale memories
        cutoff_date = datetime.utcnow() - timedelta(days=365)
        stale = await self.provider.query_entities(
            entity_type="Memory",
            filters={"updated_at_lt": cutoff_date},
            limit=100
        )
        
        # Archive each
        archived_count = 0
        for entity in stale:
            await self.provider.update_entity(
                entity["uuid"],
                {"status": "ARCHIVED"}
            )
            archived_count += 1
        
        return archived_count
```

### Failure Recovery

```python
class DeadLetterProcessor:
    """
    Processes dead-letter queue.
    
    Strategies:
    - Retry (if temporary error)
    - Alert (if permanent error)
    - Discard (if invalid)
    """
    
    async def process_dlq(self) -> None:
        for job in self.queue.dead_letter_queue:
            error = self.queue.failed_jobs[job.id]
            
            # Categorize error
            if self.is_retryable(error):
                # Reset attempts and re-enqueue
                job.attempts = 0
                await self.queue.enqueue(job)
            
            elif self.is_permanent(error):
                # Alert operators
                await self.alert_operators(job, error)
            
            else:
                # Log and discard
                self.logger.error(f"Discarding job {job.id}: {error}")
```

---

## Phase 10: Migration Plan

### Incremental Migration Steps

**Step 0: Preparation (No Changes)**

```yaml
Week 1:
  - Document current system architecture
  - Identify all integration points
  - Create comprehensive test suite
  - Baseline performance metrics
```

**Step 1: Provider Abstraction (Week 2-3)**

```yaml
Goal: Introduce MemoryProvider interface without breaking changes

Actions:
  - Create MemoryProvider abstract interface
  - Create GraphitiProvider implementation (wraps existing GraphitiClient)
  - Update MemoryService to use provider (behind feature flag)
  - Add provider.unit_tests
  
Validation:
  - All existing tests pass
  - No performance regression
  - Feature flag: use_provider_interface=false (default off)

Rollback:
  - Toggle feature flag to false
  - System reverts to direct Graphiti usage
```

**Step 2: Knowledge Extraction Pipeline (Week 4-5)**

```yaml
Goal: Separate knowledge extraction from storage

Actions:
  - Create KnowledgeExtractor interface
  - Implement LLMKnowledgeExtractor (replaces MemoryScorer pattern matching)
  - Create KnowledgeExtractionPipeline
  - Keep old MemoryScorer as fallback (feature flag)
  
Validation:
  - Compare extraction quality: pattern vs LLM
  - Measure latency impact
  - Feature flag: use_llm_extraction=false (default)

Rollback:
  - Toggle flag, revert to pattern matching
```

**Step 3: Admission Policy Service (Week 6-7)**

```yaml
Goal: Centralize admission policy

Actions:
  - Create AdmissionPolicy interface
  - Implement ScoringAdmissionPolicy (5-dimension scoring)
  - Create AdmissionPipeline
  - Add admission.metrics
  
Validation:
  - Track admission rates
  - Compare storage quality (admitted vs rejected)
  - Feature flag: use_admission_policy=false

Rollback:
  - Disable admission policy, admit all
```

**Step 4: Entity Resolution (Week 8-9)**

```yaml
Goal: Deduplicate entities intelligently

Actions:
  - Create EntityResolver interface
  - Implement FuzzyEntityResolver (similarity-based merging)
  - Create ConflictResolutionService
  - Add entity_resolution.metrics
  
Validation:
  - Measure duplicate rate
  - Track merge decisions
  - Feature flag: use_entity_resolution=false

Rollback:
  - Disable, create all entities as unique
```

**Step 5: Retrieval Pipeline Redesign (Week 10-12)**

```yaml
Goal: Implement 5-stage retrieval

Actions:
  - Create RetrievalPipeline interface
  - Implement FiveStageRetrievalPipeline
  - Create MemoryScoringService
  - Create RankingAlgorithm
  - Add retrieval.metrics
  
Components:
  - Stage 1: SemanticSearchStage
  - Stage 2: GraphTraversalStage
  - Stage 3: EntityLookupStage
  - Stage 4: ContextFilterStage
  - Stage 5: TemporalBoostingStage
  
Validation:
  - Compare retrieval quality: old vs new
  - Measure retrieval latency
  - A/B test with sample tasks
  - Feature flag: use_new_retrieval=false

Rollback:
  - Toggle flag, revert to basic semantic search
```

**Step 6: Background Queue Architecture (Week 13-15)**

```yaml
Goal: Asynchronous processing

Actions:
  - Create MemoryQueue with priorities
  - Create WorkerPool infrastructure
  - Implement ExtractionWorker
  - Implement AdmissionWorker
  - Implement ArchivalWorker
  - Create DeadLetterProcessor
  
Validation:
  - Measure request latency (should decrease)
  - Monitor queue depths
  - Track dead-letter rate
  - Feature flag: use_background_processing=false

Rollback:
  - Toggle flag, revert to synchronous processing
```

**Step 7: Remove MCP Manual Tools (Week 16)**

```yaml
Goal: Enforce automatic memory

Actions:
  - Deprecate MCP manual tools (remember_architecture, search_memory)
  - Add warnings to tool descriptions
  - Update documentation
  - Monitor usage metrics

Validation:
  - Track manual tool usage (should drop to near zero)
  - Verify automatic hooks working

Rollback:
  - Re-add tools if critical usage remains
```

**Step 8: Graph Schema Migration (Week 17-18)**

```yaml
Goal: Enforce schema constraints

Actions:
  - Create Neo4j migration script
  - Apply constraints and indexes
  - Migrate existing data to new schema
  - Validate entity properties

Validation:
  - Run integrity checks
  - Measure query performance
  - Feature flag: use_new_schema=false

Rollback:
  - Restore from backup if critical errors
```

**Step 9: Context Builder Enhancement (Week 19-20)**

```yaml
Goal: Intelligent context formatting

Actions:
  - Enhance ContextBuilder with token budgeting
  - Add summarization fallback
  - Implement hierarchical formatting
  - Add context.metrics

Validation:
  - Measure injection token usage
  - Track agent performance with context
  - Feature flag: use_smart_context=false

Rollback:
  - Toggle flag, revert to basic formatting
```

**Step 10: Memory Governance (Week 21-22)**

```yaml
Goal: Automated lifecycle management

Actions:
  - Create MemoryGovernanceService
  - Implement archival policies
  - Implement expiration checks
  - Add governance.metrics

Validation:
  - Track memory lifecycle
  - Measure storage efficiency
  - Feature flag: use_governance=false

Rollback:
  - Disable governance, keep all memories indefinitely
```

**Step 11: Monitoring & Observability (Week 23-24)**

```yaml
Goal: Production-ready observability

Actions:
  - Add comprehensive metrics (Prometheus/Grafana)
  - Add distributed tracing (if needed)
  - Create operational dashboards
  - Document runbooks

Deliverables:
  - metrics_dashboard.json
  - runbooks/memory_operations.md
  - alerts.yaml
```

**Step 12: Documentation & Training (Week 25-26)**

```yaml
Goal: Knowledge transfer

Actions:
  - Update architecture documentation
  - Create integration guide
  - Create operator runbooks
  - Training sessions (if team)

Deliverables:
  - ARCHITECTURE.md (this document)
  - INTEGRATION_GUIDE.md
  - OPERATIONS_RUNBOOK.md
```

---

## Phase 11: Architecture Review

### Self-Critique

**Strengths:**

1. **Clear Separation of Concerns**
   - Provider abstraction: Business logic isolated from Graphiti
   - Knowledge extraction separated from storage
   - Admission policy as explicit service
   - Each component has single responsibility

2. **Evidence-Driven Memory**
   - Every memory has provenance (source_execution_id)
   - Confidence scores from multiple dimensions
   - Verification via execution success
   - Traceable from conversation to storage

3. **Intelligent Retrieval**
   - Multi-stage retrieval (semantic + graph + entity + temporal)
   - Ranking with explainable scores
   - Token budget management
   - Repository and branch scoping

4. **Scalable Architecture**
   - Background processing via queues
   - Worker pools for throughput
   - Dead-letter handling
   - Backpressure support

5. **Lifecycle Management**
   - Admission policies prevent garbage accumulation
   - Entity resolution prevents duplication
   - Archival policies manage storage
   - Conflict resolution maintains integrity

**Weaknesses:**

1. **Complexity**
   - 12-phase migration is expensive (26 weeks)
   - Many moving parts (workers, queues, pipelines)
   - Higher operational burden (monitoring queues, dead letters)
   - **Tradeoff:** Complexity vs. correctness

2. **LLM Dependency for Extraction**
   - LLMKnowledgeExtractor requires LLM calls for every conversation
   - Cost and latency concerns
   - **Mitigation:** Batch processing, caching, fallback to heuristics

3. **Entity Resolution Ambiguity**
   - Fuzzy matching can merge distinct entities
   - Conflict resolution may require human intervention
   - **Mitigation:** Confidence thresholds, human review for critical items

4. **Retrieval Latency**
   - 5-stage retrieval is slower than single semantic search
   - Target: <300ms total latency
   - May exceed budget for complex queries
   - **Mitigation:** Parallelize stages, cache results, timeout limits

5. **No Real-Time Learning**
   - Admission weights fixed (importance: 30%, novelty: 25%, etc.)
   - No feedback loop from user behavior
   - **Mitigation:** Future: Add reinforcement learning based on memory value

### Comparison with Reference Systems

**vs. OpenHands Current Memory:**

| Dimension | Current (PoC) | Proposed |
|-----------|---------------|----------|
| Storage | Direct Graphiti | Provider abstraction |
| Extraction | Regex patterns | LLM-directed |
| Admission | Threshold only | 5-dimension scoring |
| Retrieval | Semantic search | 5-stage pipeline |
| Entities | Manual tools | Automatic hooks |
| Lifecycle | None | Governance service |
| Scalability | Synchronous | Async queues |

**Winner:** Proposed (but higher complexity)

**vs. Graphiti Reference Architecture:**

Graphiti's default: "Add episodes, extract entities automatically, search semantically."

Our design: "Explicit knowledge extraction, admission policy, multi-stage retrieval, lifecycle management."

**Graphiti's Strengths:**
- Simpler integration (just add_episode)
- Less code to maintain
- Lower latency (no pipeline)

**Our Strengths:**
- Higher quality memories (admission policy)
- Better retrieval (graph + temporal)
- Lifecycle management (archival)
- Provider abstraction (future extensibility)

**Tradeoff:** We trade simplicity for control and quality.

**vs. Mem0:**

Mem0: "Add memories, search memories." Simple key-value + vector.

**Mem0's Strengths:**
- Extremely simple API
- Low overhead
- Fast retrieval (single vector search)

**Our Strengths:**
- Rich knowledge graph (entities + relationships)
- Evidence-driven (provenance, confidence)
- Repository-aware (scoped memory)
- Lifecycle management

**Tradeoff:** We trade speed for depth and accuracy.

**vs. Cursor's Memory:**

Cursor: Uses LLM context + file indexing. No long-term memory.

**Cursor's Strengths:**
- No memory management overhead
- Fresh context every session
- No stale knowledge

**Our Strengths:**
- Remember across sessions
- Build cumulative knowledge
- Learn from past successes/failures

**Tradeoff:** We add persistence overhead.

**vs. Claude Code (Anthropic's artifact system):**

Claude Code: No memory, but can reference artifacts and files.

**Claude Code's Strengths:**
- No memory management needed
- Files are source of truth

**Our Strengths:**
- Knowledge graph enables reasoning beyond files
- Relationships (DEPENDS_ON, FIXES)
- Historical context (past decisions, bugs)

**Tradeoff:** Graph maintenance vs. file freshness.

### When This Architecture Is Stronger

**Use Cases:**

1. **Long-running agents** (months/years)
   - Memory accumulates value over time
   - Need to remember past decisions
   - Justifies complexity cost

2. **Multi-repo agents**
   - Need repository-aware memory
   - Scope isolation essential

3. **Evidence-critical applications**
   - Must justify decisions
   - Provenance and confidence required
   - Audit trail needed

4. **Learning agents**
   - Need to learn from successes/failures
   - Requires execution history
   - Improvement over time valued

### When This Architecture Is Weaker

**Anti-Patterns:**

1. **Short-lived tasks**
   - Single-session agents
   - No cumulative learning needed
   - Use simpler vector search

2. **High-frequency, low-latency tasks**
   - Need <100ms response
   - Can't afford multi-stage retrieval
   - Use cached semantic search

3. **Simple codebases**
   - Few dependencies
   - Flat architecture
   - Knowledge graph overkill

4. **Prototype/MVP stage**
   - Need 80% solution in 20% time
   - Use basic Graphiti + semantic search
   - Graduate to this architecture later

---

## Conclusion

### Architecture Summary

This architecture transforms a PoC conversation storage system into a production-grade knowledge-based memory system:

**Core Design Principles:**
1. Provider abstraction (no Graphiti lock-in)
2. Knowledge extraction (not conversation storage)
3. Admission policy (quality > quantity)
4. Multi-stage retrieval (semantic + graph + temporal)
5. Background processing (latency independence)
6. Lifecycle management (prevent accumulation)

**Key Components:**
- Execution Recorder Service
- Knowledge Extraction Pipeline
- Admission Policy Service
- Entity Resolution Service
- Memory Provider Interface
- Graphiti Provider
- Retrieval Pipeline (5-stage)
- Context Builder Service
- Background Worker Pool
- Memory Governance Service

**Migration Timeline:** 26 weeks, 12 steps, each step with rollback plan.

**Success Metrics:**
- Retrieval latency <300ms (p95)
- Admission rate 20-40% (quality filter)
- Duplicate rate <5% (entity resolution)
- Memory hit rate >70% (relevant context found)
- Token efficiency >50% reduction vs. raw context

### Final Recommendation

**Approve this architecture IF:**

1. Target use case is long-running autonomous agents (months/years)
2. Repository understanding is critical to agent success
3. Evidence-driven decisions are required (compliance, safety)
4. Team capacity exists for 6-month migration and ongoing operations

**Do NOT approve IF:**

1. Short-term prototype needed
2. Low-latency is top priority (<100ms)
3. Resources insufficient for migration
4. Codebase is simple (no complex architecture)

**This architecture is optimized for correctness, maintainability, and long-term value, NOT simplicity or speed.**

---

**Next Steps:**

1. Review this document with stakeholders
2. Approve architecture or request revisions
3. If approved, begin Phase 1 implementation (Step 1: Provider Abstraction)
4. Track progress via migration plan milestones

**Document Status:** DRAFT - Awaiting Approval
