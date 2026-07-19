# Architecture Redesign Summary

**Date:** 2026-07-18  
**Status:** Design Complete - Awaiting Approval  
**Document:** Full design in `ARCHITECTURE_REDESIGN.md`

---

## Core Architecture Transformation

**From:** Proof-of-concept conversation storage with pattern-based extraction  
**To:** Production-grade knowledge-based memory system for autonomous agents

---

## Key Design Decisions

### 1. Provider Abstraction
- **Before:** Direct Graphiti dependency throughout codebase
- **After:** `MemoryProvider` interface, Graphiti as one implementation
- **Benefit:** Extensible to Neo4j, PostgreSQL, future backends
- **Cost:** Additional abstraction layer

### 2. Knowledge Extraction (Not Conversation Storage)
- **Before:** Store episodes with `to_episode_content()`
- **After:** Extract facts, entities, relationships via LLM
- **Benefit:** Structured knowledge, not raw conversations
- **Cost:** LLM dependency for extraction

### 3. 5-Dimension Admission Policy
- **Before:** Simple threshold (confidence > 0.7)
- **After:** Multi-dimensional scoring (importance, novelty, confidence, persistence, repository_relevance)
- **Benefit:** Quality filter, prevents garbage accumulation
- **Cost:** More complex admission logic

### 4. Multi-Stage Retrieval Pipeline
- **Before:** Graphiti semantic search only
- **After:** 5-stage pipeline (semantic + graph + entity + context + temporal)
- **Benefit:** Higher recall, better ranking
- **Cost:** Higher latency (target: <300ms)

### 5. Background Processing
- **Before:** Synchronous memory operations
- **After:** Queue-based workers (Extraction, Admission, Archival)
- **Benefit:** Request latency isolation, throughput scaling
- **Cost:** Operational complexity (queues, dead letters)

### 6. Memory Lifecycle Management
- **Before:** No lifecycle, memories live forever
- **After:** Automatic archival, conflict resolution, expiration
- **Benefit:** Storage efficiency, maintained quality
- **Cost:** Additional governance service

---

## Component Overview

### Processing Path (After Task)

```
Execution Recorder
    ↓
Knowledge Extraction Pipeline (LLM-based)
    ↓
Admission Policy (5-dimension scoring)
    ↓
Entity Resolution (deduplication)
    ↓
Memory Provider Interface
    ↓
Graphiti (knowledge graph backend)
```

### Retrieval Path (Before Task)

```
Agent Task Request
    ↓
Retrieval Pipeline:
  1. Semantic Search (vector similarity)
  2. Graph Traversal (relationship expansion)
  3. Entity Lookup (direct query)
  4. Context Filtering (repository/branch scope)
  5. Temporal Boosting (recent + verified)
    ↓
Memory Scoring (relevance, confidence, recency, centrality, success_rate)
    ↓
Ranking (weighted combination)
    ↓
Context Builder (token budget, deduplication, formatting)
    ↓
Prompt Injection (<RELEVANT_KNOWLEDGE>)
```

### Background Processing

```
Queues:
- Extraction Queue (high priority)
- Admission Queue (medium priority)
- Archival Queue (low priority)

Workers:
- Extraction Workers (×3)
- Admission Workers (×2)
- Archival Workers (×1)
- Dead Letter Processor
```

---

## Knowledge Model

### Entities (11 types)

| Entity | Purpose | Key Properties |
|--------|---------|----------------|
| Service | Microservice, API, daemon | name, repository, language, status |
| Module | Code module, package | path, repository, responsibilities |
| Repository | Git repository | url, name, primary_language |
| API | REST endpoint, GraphQL query | endpoint, method, schemas |
| Database | Database instance, schema | name, type, schema_version |
| Library | External dependency | name, version, license |
| Pattern | Architectural/design pattern | name, category, pros/cons |
| Decision | Design decision, choice | title, rationale, alternatives, status |
| Bug | Known bug, issue | title, symptoms, root_cause, severity |
| Fix | Bug fix, workaround | title, solution, prevention |
| Convention | Coding standard | rule, rationale, examples |

### Relationships (9 types)

| Relationship | Meaning | Example |
|--------------|---------|---------|
| DEPENDS_ON | Runtime dependency | AuthService → TokenService |
| USES | Usage relationship | Service → Library |
| IMPLEMENTS | Implementation of pattern | AuthService → Repository Pattern |
| FIXES | Bug fix relationship | Idempotency Fix → Race Condition Bug |
| CONFLICTS_WITH | Incompatibility | Decision A ↔ Decision B |
| PART_OF | Containment | Module → Service |
| OWNS | Ownership | Service → API |
| SUPERSEDES | Replacement | New Decision → Old Decision |
| RELATES_TO | Generic relation | Use sparingly, prefer specific edges |

---

## Admission Policy

### 5-Dimension Scoring

```
Final Score = 0.30 × Importance
            + 0.25 × Novelty
            + 0.20 × Confidence
            + 0.15 × Persistence
            + 0.10 × Repository Relevance
```

**Decision Thresholds:**
- `>= 0.7`: ADMIT (store memory)
- `0.3 - 0.7`: DEFER (re-evaluate later)
- `< 0.3`: REJECT (discard)

**Rationale per Dimension:**

1. **Importance (30%)** - Not all knowledge equal; core architecture > minor details
2. **Novelty (25%)** - Prevent duplicates; detect what's truly new
3. **Confidence (20%)** - Verified execution > speculation
4. **Persistence (15%)** - Architectural patterns > current implementation
5. **Repository Relevance (10%)** - Cross-repo knowledge > file-specific

---

## Retrieval Ranking

### Ranking Algorithm

```python
final_score = 0.30 × semantic_similarity
            + 0.25 × graph_centrality
            + 0.20 × confidence
            + 0.15 × recency
            + 0.10 × execution_success_rate
```

**Signal Definitions:**

1. **Semantic Similarity** - Vector embedding distance from task description
2. **Graph Centrality** - Shortest path from seed memories (inverse)
3. **Confidence** - Stored memory confidence (0.0-1.0)
4. **Recency** - Age-based decay (<7 days: 1.0, 7-30: 0.85, 30-90: 0.7, else: 0.5)
5. **Execution Success Rate** - successful_uses / total_uses

---

## Migration Plan

### Timeline: 26 weeks (12 steps)

1. **Week 2-3:** Provider Abstraction (MemoryProvider interface)
2. **Week 4-5:** Knowledge Extraction Pipeline (LLM-based)
3. **Week 6-7:** Admission Policy Service (5-dimension scoring)
4. **Week 8-9:** Entity Resolution (FuzzyEntityResolver)
5. **Week 10-12:** Retrieval Pipeline (5-stage)
6. **Week 13-15:** Background Queues (WorkerPool)
7. **Week 16:** Remove MCP Manual Tools
8. **Week 17-18:** Graph Schema Migration (constraints/indexes)
9. **Week 19-20:** Context Builder Enhancement (token budgeting)
10. **Week 21-22:** Memory Governance (archival policies)
11. **Week 23-24:** Monitoring & Observability
12. **Week 25-26:** Documentation & Training

**Each Step:**
- Feature flag control
- Validation metrics
- Rollback plan

---

## Strengths

1. **Provider Abstraction** - No vendor lock-in, future extensibility
2. **Evidence-Driven Memory** - Provenance, confidence, verification
3. **Intelligent Retrieval** - Multi-stage, explainable ranking
4. **Scalable Architecture** - Async processing, queue-based
5. **Lifecycle Management** - Admission policy, archival, conflict resolution

---

## Weaknesses

1. **Complexity** - Many moving parts, higher operational burden
2. **LLM Dependency** - Cost and latency for extraction
3. **Entity Resolution Ambiguity** - Fuzzy matching may merge distinct entities
4. **Retrieval Latency** - Multi-stage retrieval slower than single search
5. **No Real-Time Learning** - Admission weights fixed, no feedback loop

---

## When to Use This Architecture

**✅ Ideal For:**
- Long-running agents (months/years)
- Multi-repository environments
- Evidence-critical applications (compliance, safety)
- Learning agents that improve over time

**❌ Avoid If:**
- Short-lived tasks (<1 hour)
- High-frequency needs (<100ms latency)
- Simple codebases (<10 modules)
- Prototype/MVP stage

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Retrieval Latency (p95) | <300ms | Grafana dashboard |
| Admission Rate | 20-40% | Percentage of facts admitted |
| Duplicate Rate | <5% | Entity resolution metrics |
| Memory Hit Rate | >70% | Relevant context found |
| Token Efficiency | >50% reduction | Injected tokens vs. raw context |
| Execution Success Improvement | >10% | Agent success rate over time |

---

## Open Questions

1. **Human Validation:** Should critical entity conflicts require human review?
2. **Real-Time Learning:** Should we implement reinforcement learning for admission weights?
3. **LLM Cost:** Is LLM extraction cost acceptable? (Batching, caching strategies?)
4. **Alternative Extraction:** Hybrid approach (heuristics + LLM)?

---

## Next Steps

1. **Review:** Stakeholders review `ARCHITECTURE_REDESIGN.md`
2. **Approve:** Architecture approval and timeline confirmation
3. **Implement:** Begin Phase 1 (Provider Abstraction)
4. **Track:** Migration milestones via project board

---

## Quick Reference

- **Full Design:** `/docs/ARCHITECTURE_REDESIGN.md`
- **Analysis:** `/memories/session/architecture_redesign_analysis.md`
- **Status:** Design complete, awaiting approval before implementation
