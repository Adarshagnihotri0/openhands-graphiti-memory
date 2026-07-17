# OpenHands Integration Guide - Making Memory Automatic

## The Critical Question

**Does OpenHands automatically consult Graphiti before tasks, or must the user manually invoke `search_memory`?**

This is the difference between a **memory database** and an **integrated memory system**.

---

## Solution 1: OpenHands Agent Hooks

### Approach A: Pre-Task Hook (Recommended)

OpenHands should have a pre-task hook that **automatically**:

```python
async def before_task_hook(task: str, context: dict):
    """
    Automatically invoked before OpenHands starts any task.
    
    Flow:
    1. Query Graphiti for relevant project memory
    2. Query Code Index MCP for relevant source code
    3. Merge both contexts
    4. Inject into OpenHands prompt
    """
    
    # 1. Query Graphiti Memory
    graphiti_client = get_graphiti_client()
    memory_context = await graphiti_client.search_memory(
        query=task,
        limit=10,
        min_confidence=0.7
    )
    
    # 2. Query Code Index MCP
    code_index_client = get_code_index_client()
    code_context = await code_index_client.search_symbols(
        query=task,
        limit=15
    )
    
    # 3. Merge contexts
    merged_context = format_memory_for_context(memory_context)
    merged_context += format_code_for_context(code_context)
    
    # 4. Inject into OpenHands
    return {
        "system_prompt_append": merged_context,
        "metadata": {
            "memory_hit_count": len(memory_context),
            "code_hit_count": len(code_context)
        }
    }
```

### Integration Point

This hook should be registered in OpenHands' agent initialization:

```python
# In OpenHands agent initialization (pseudo-code)
class OpenHandsAgent:
    def __init__(self):
        self.register_pre_task_hook(before_task_hook)
        self.register_post_task_hook(after_task_hook)
```

---

## Solution 2: Memory Promotion Pipeline

### Problem

"After every completed task determine whether it is durable."

**How?** We need explicit promotion logic.

### Implementation

```python
async def after_task_hook(task: str, result: str, context: dict):
    """
    Automatically invoked after OpenHands completes any task.
    
    Flow:
    1. Extract candidate facts
    2. Score them
    3. Remove duplicates
    4. Store (with confidence adjustment)
    """
    
    # 1. Extract candidate facts using LLM
    extractor = FactExtractor()
    candidates = await extractor.extract_facts(
        task=task,
        result=result,
        context=context
    )
    
    # 2. Score each candidate
    scorer = MemoryScorer()
    for candidate in candidates:
        score = scorer.should_remember(candidate)
        candidate.confidence = score
    
    # 3. Filter by minimum confidence
    viable_candidates = [
        c for c in candidates 
        if c.confidence >= MIN_CONFIDENCE_TO_STORE
    ]
    
    # 4. Deduplicate against existing memories
    deduplicated = []
    for candidate in viable_candidates:
        similar = await graphiti_client.find_similar(
            content=candidate.content,
            threshold=0.75
        )
        
        if similar:
            # Update existing memory (increment confidence)
            await graphiti_client.update_memory(
                uuid=similar.uuid,
                increment_confidence=True,
                new_information=candidate.content
            )
        else:
            deduplicated.append(candidate)
    
    # 5. Store new memories
    for memory in deduplicated:
        await graphiti_client.store_memory(memory)
    
    return {"stored_count": len(deduplicated)}
```

### Fact Extraction Prompt

```python
FACT_EXTRACTION_PROMPT = """
Analyze the following task execution and extract durable knowledge.

Task: {task}
Result: {result}

Extract facts that are:
1. NOT temporary (not just for this conversation)
2. NOT code (code goes in Code Index)
3. DURABLE knowledge about:
   - Architecture (service dependencies, data flows)
   - Decisions (why X was chosen)
   - Bug fixes (root cause, solution)
   - Conventions (patterns discovered)
   - Gotchas (important warnings)

For each fact, provide:
- type: architecture|decision|bug_fix|convention|gotcha
- title: brief summary
- content: detailed explanation
- confidence: 0.0-1.0 (how certain is this?)
- scope: repository/module/service

Output JSON array of facts.
"""
```

---

## Solution 3: Repository Bootstrap

### Problem

"A brand-new repository starts empty."

### Implementation

```python
async def bootstrap_repository(repository_path: str):
    """
    Initialize Graphiti memory from existing repository.
    
    Scans:
    - README.md
    - docs/ (architecture, ADRs)
    - package.json/pyproject.toml (dependencies)
    - docker-compose.yml (services)
    - .github/workflows/ (CI/CD)
    - Existing design documents
    """
    
    extractor = BootstrapExtractor()
    
    # 1. Extract from README
    readme_path = f"{repository_path}/README.md"
    if os.path.exists(readme_path):
        readme_knowledge = await extractor.extract_from_readme(readme_path)
        await store_batch(readme_knowledge)
    
    # 2. Extract ADRs (Architecture Decision Records)
    adr_path = f"{repository_path}/docs/adr"
    if os.path.exists(adr_path):
        adr_knowledge = await extractor.extract_from_adrs(adr_path)
        await store_batch(adr_knowledge)
    
    # 3. Extract architecture docs
    arch_path = f"{repository_path}/docs/architecture"
    if os.path.exists(arch_path):
        arch_knowledge = await extractor.extract_from_arch_docs(arch_path)
        await store_batch(arch_knowledge)
    
    # 4. Extract dependencies
    deps_knowledge = await extractor.extract_dependencies(repository_path)
    await store_batch(deps_knowledge)
    
    # 5. Extract services from docker-compose
    compose_path = f"{repository_path}/docker-compose.yml"
    if os.path.exists(compose_path):
        services_knowledge = await extractor.extract_from_compose(compose_path)
        await store_batch(services_knowledge)
    
    # 6. Extract CI/CD knowledge
    workflows_path = f"{repository_path}/.github/workflows"
    if os.path.exists(workflows_path):
        ci_knowledge = await extractor.extract_from_workflows(workflows_path)
        await store_batch(ci_knowledge)
```

### Bootstrap Extraction Prompt

```python
BOOTSTRAP_PROMPT = """
Extract architecturally significant knowledge from this file.

File: {filename}
Content:
{content}

Extract:
1. Architecture decisions (why X over Y)
2. Service dependencies (A depends on B)
3. Design patterns used
4. Important constraints or limitations
5. Key technical choices

Output JSON array of memory objects.
"""
```

---

## Solution 4: Memory Freshness & Invalidation

### Problem

"Six months later, AuthService renamed to IdentityService."

### Implementation

```python
async def detect_stale_memories():
    """
    Periodically check for stale memories.
    
    Strategies:
    1. Code entity changes (renames, deletions)
    2. File changes (docs updated)
    3. Time-based decay
    4. Git history analysis
    """
    
    # 1. Check for entity renames via Code Index
    code_index = get_code_index_client()
    graphiti = get_graphiti_client()
    
    memories = await graphiti.get_all_memories()
    
    for memory in memories:
        # Check if entities still exist
        if memory.module:
            entity_exists = await code_index.entity_exists(
                name=memory.source_entity,
                type=memory.component_type
            )
            
            if not entity_exists:
                # Entity was renamed or deleted
                await graphiti.mark_stale(
                    uuid=memory.uuid,
                    reason="entity_not_found",
                    suggestion="Check for renames in git history"
                )
    
    # 2. Time-based aging
    for memory in memories:
        age_days = (now - memory.updated_at).days
        
        if age_days > 180:  # 6 months
            # Decay confidence
            decay_factor = 0.95 ** (age_days / 30)  # 5% per month
            new_confidence = memory.confidence * decay_factor
            
            await graphiti.update_memory(
                uuid=memory.uuid,
                confidence=new_confidence,
                stale=True
            )
```

### Git Integration for Freshness

```python
async def on_git_merge_event(event: GitMergeEvent):
    """
    Triggered when PR/merge occurs.
    
    Analyzes diff for structural changes.
    """
    
    changed_files = event.files_changed
    changed_entities = await code_index.get_changed_entities(changed_files)
    
    # Update affected memories
    for entity in changed_entities:
        memories = await graphiti.find_memories_mentioning(entity)
        
        for memory in memories:
            # Mark for review
            await graphiti.flag_for_review(
                uuid=memory.uuid,
                reason=f"Entity {entity} changed in merge {event.merge_commit}"
            )
```

---

## Solution 5: Git Integration (High Value)

### Implementation

```python
async def on_pr_merged(pr_event: PullRequestEvent):
    """
    Automatically triggered when PR merges.
    
    Extracts knowledge from:
    - PR title and description
    - Code changes
    - Review comments
    - Commit messages
    """
    
    # 1. Extract from PR metadata
    pr_knowledge = await extract_from_pr_metadata(
        title=pr_event.title,
        description=pr_event.description,
        labels=pr_event.labels
    )
    
    # 2. Extract from changes
    change_knowledge = await extract_from_diff(
        diff=pr_event.diff,
        files_changed=pr_event.files_changed
    )
    
    # 3. Check for architecture changes
    if is_architecture_change(pr_event):
        arch_knowledge = await extract_architecture_change(pr_event)
        await store_memory(arch_knowledge, confidence=0.9)
    
    # 4. Check for bug fixes
    if is_bug_fix(pr_event):
        bug_knowledge = await extract_bug_fix(pr_event)
        await store_memory(bug_knowledge, confidence=0.85)
    
    # 5. Store all extracted knowledge
    all_knowledge = pr_knowledge + change_knowledge
    await store_batch(all_knowledge)
```

### Git Hook Setup

```bash
# .git/hooks/post-merge
#!/bin/bash
# Trigger memory update after merge

curl -X POST http://localhost:8000/hooks/git-merged \
  -H "Content-Type: application/json" \
  -d '{"merge_commit": "'$MERGE_HEAD'", "branch": "'$(git branch --show-current)'"}'
```

---

## Solution 6: Entity Normalization

### Problem

"Replay Engine vs ReplayEngine vs replay engine"

### Implementation

```python
class EntityNormalizer:
    """
    Canonicalize entity names for consistent graph nodes.
    """
    
    def __init__(self):
        self.entity_canonical_forms = {}  # cache
        
    async def normalize(self, entity_name: str, entity_type: str) -> str:
        """
        Convert entity name to canonical form.
        
        Rules:
        1. Remove special chars (spaces, dashes, underscores)
        2. Standard case (PascalCase for classes/services)
        3. Check against Code Index for actual names
        4. Use LLM to resolve ambiguity
        """
        
        # 1. Basic normalization
        normalized = self._basic_normalize(entity_name)
        
        # 2. Check Code Index for actual entity
        code_index = get_code_index_client()
        actual_name = await code_index.find_entity(
            pattern=normalized,
            type=entity_type
        )
        
        if actual_name:
            return actual_name
        
        # 3. Check existing graph
        graphiti = get_graphiti_client()
        existing = await graphiti.find_entity_node(
            name=normalized,
            fuzzy_match=True
        )
        
        if existing:
            return existing.canonical_name
        
        # 4. LLM disambiguation
        canonical = await self._llm_normalize(entity_name, entity_type)
        
        return canonical
    
    def _basic_normalize(self, name: str) -> str:
        """Remove noise and standardize case."""
        # Remove spaces, dashes, underscores
        name = re.sub(r'[-_\s]+', '', name)
        
        # Convert to PascalCase
        return name.title().replace(' ', '')  # e.g., "replay engine" -> "ReplayEngine"
```

---

## Solution 7: Memory Aging & Expiration

### Implementation

```python
class MemoryAgingPolicy:
    """
    Manage memory lifecycle and expiration.
    """
    
    async def apply_aging(self):
        """Apply time-based aging to memories."""
        
        memories = await graphiti.get_all_memories()
        
        for memory in memories:
            # Calculate age
            age_days = (datetime.utcnow() - memory.created_at).days
            
            # Apply decay based on memory type
            decay_rate = {
                MemoryType.ARCHITECTURE: 0.98,  # Very stable
                MemoryType.DECISION: 0.99,      # Highly stable
                MemoryType.CONVENTION: 0.97,   # Stable
                MemoryType.BUG_FIX: 0.95,      # May become obsolete
                MemoryType.IMPLEMENTATION: 0.92,  # Changes frequently
            }.get(memory.memory_type, 0.95)
            
            # Monthly decay
            decayed_confidence = memory.confidence * (decay_rate ** (age_days / 30))
            
            # Update if significantly decayed
            if decayed_confidence < memory.confidence - 0.1:
                await graphiti.update_memory(
                    uuid=memory.uuid,
                    confidence=decayed_confidence,
                    aged=True
                )
            
            # Archive if very old and low confidence
            if age_days > 365 and decayed_confidence < 0.5:
                await graphiti.archive_memory(
                    uuid=memory.uuid,
                    reason="expired"
                )
```

---

## Solution 8: Feedback Loop

### Implementation

```python
class MemoryFeedbackLoop:
    """
    Learn from memory usage patterns.
    """
    
    async def on_memory_used(self, memory_uuid: str, was_helpful: bool):
        """
        Called when memory is used in a task.
        
        was_helpful: True if memory contributed to solution
        """
        
        memory = await graphiti.get_memory(memory_uuid)
        
        if was_helpful:
            # Boost confidence
            new_confidence = min(memory.confidence + 0.05, 1.0)
            await graphiti.update_memory(
                uuid=memory_uuid,
                confidence=new_confidence,
                usage_count=memory.usage_count + 1,
                last_helpful=datetime.utcnow()
            )
        else:
            # Slightly reduce confidence
            new_confidence = max(memory.confidence - 0.02, 0.0)
            await graphiti.update_memory(
                uuid=memory_uuid,
                confidence=new_confidence,
                last_unhelpful=datetime.utcnow()
            )
    
    async def on_task_completed(self, task: str, result: str, retrieved_memories: list):
        """
        After task completion, analyze which memories helped.
        """
        
        # Use LLM to judge memory usefulness
        for mem_uuid in retrieved_memories:
            memory = await graphiti.get_memory(mem_uuid)
            
            helpfulness = await self._judge_helpfulness(
                task=task,
                result=result,
                memory=memory
            )
            
            await self.on_memory_used(mem_uuid, was_helpful=helpfulness > 0.5)
```

---

## Solution 9: Cross-Memory Linking

### Implementation

```python
async def link_memories():
    """
    Create dense links between related memories.
    """
    
    memories = await graphiti.get_all_memories()
    
    for memory in memories:
        # Find related memories through shared entities
        shared_entities = extract_entities(memory)
        
        related = await graphiti.find_memories_with_entities(
            entities=shared_entities,
            exclude_uuid=memory.uuid
        )
        
        # Create edges between related memories
        for related_mem in related:
            similarity = calculate_similarity(memory, related_mem)
            
            if similarity > 0.6:
                await graphiti.create_edge(
                    source=memory.uuid,
                    target=related_mem.uuid,
                    relation="RELATES_TO",
                    strength=similarity
                )
```

---

## Solution 10: Explainability

### Implementation

```python
async def explain_retrieval(query: str, retrieved_memories: list) -> str:
    """
    Generate human-readable explanation of why memories were retrieved.
    """
    
    explanation = "Retrieved memories because:\n\n"
    
    for i, memory in enumerate(retrieved_memories, 1):
        # Explain semantic similarity
        semantic_score = memory.semantic_score
        explanation += f"{i}. **{memory.title}** (Score: {memory.score:.2f})\n"
        
        # Explain entity overlap
        if memory.matched_entities:
            explanation += f"   - Matches entities: {', '.join(memory.matched_entities)}\n"
        
        # Explain graph path
        if memory.relationship_path:
            explanation += f"   - Connected via: {' → '.join(memory.relationship_path)}\n"
        
        # Explain recency
        days_old = (datetime.utcnow() - memory.created_at).days
        if days_old < 30:
            explanation += f"   - Recently created ({days_old} days ago)\n"
        
        # Explain confidence
        explanation += f"   - Confidence: {memory.confidence:.0%}\n"
        
        explanation += "\n"
    
    return explanation
```

---

## Summary: Production Checklist

### Must Have (🔴)

- [ ] **Pre-task hook**: OpenHands automatically queries Graphiti before every task
- [ ] **Post-task hook**: OpenHands automatically extracts and stores durable knowledge
- [ ] **Bootstrap**: New repositories auto-populate from READMEs, ADRs, docs
- [ ] **Freshness**: Detects stale memories when entities are renamed/deleted

### Should Have (🟡)

- [ ] **Git integration**: Auto-update on PR merges
- [ ] **Entity normalization**: Canonical entity names across memories
- [ ] **Memory aging**: Time-based confidence decay and expiration
- [ ] **Feedback loop**: Learn from helpful/unhelpful retrievals
- [ ] **Cross-memory linking**: Dense knowledge graph connections

### Nice to Have (🟢)

- [ ] **Explainability**: Human-readable retrieval explanations
- [ ] **Memory dashboard**: Visual stats and monitoring
- [ ] **Code Index integration**: Real-time entity existence checks

---

## Key Insight

The difference between a **memory database** and a **memory system**:

| Memory Database | Memory System |
|----------------|---------------|
| Manual queries | Automatic retrieval |
| User-triggered storage | Auto-promotion pipeline |
| Static knowledge | Living, evolving graph |
| No freshness | Auto-invalidation |
| No feedback | Continuous improvement |

**This implementation needs hooks into OpenHands core to become a true memory system.**
