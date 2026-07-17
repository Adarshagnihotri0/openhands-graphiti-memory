# OpenHands Graphiti Memory System

**Persistent knowledge graph memory for OpenHands AI agents**

## Status

- **Architecture:** 10/10 ✅ (Clean separation of concerns)
- **Implementation:** 8.5/10 ✅ (Code complete, 27/27 tests passing)
- **Validation:** 6/10 ⚠️ (Quality benchmarks pending)
- **Production-Readiness:** 4/10 ⚠️ (Needs benchmarks before production)

## Overview

Integrates [Graphiti](https://github.com/getzep/graphiti) as persistent knowledge graph memory for OpenHands AI agents.

**Key Insight:** We don't reimplement Graphiti. We delegate all knowledge graph mechanics to Graphiti and focus only on **admission decisions** - deciding what knowledge is worth remembering.

## Architecture

```
Task Completed
      ↓
Execution Recorder (Capture outcome)
      ↓
Admission Policy (Should we remember?)
      ↓
Metadata Enricher (Add repository scope)
      ↓
Graphiti (Knowledge graph management)
```

**Graphiti handles:**
- Entity extraction ✅
- Relationship extraction ✅
- Semantic search ✅
- Embeddings ✅
- Deduplication ✅
- Temporal tracking ✅

**We handle:**
- Admission decisions ✅
- Repository isolation ✅
- Governance (secrets) ✅
- Metadata enrichment ✅

## Quick Start

```python
from src.knowledge_admission_mvp import (
    GraphitiAdapter,
    KnowledgeAdmissionPipeline,
    ExecutionRecorder
)

# Initialize Graphiti
adapter = GraphitiAdapter(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

# Create pipeline
pipeline = KnowledgeAdmissionPipeline(adapter)

# Record execution
recorder = ExecutionRecorder()
record = recorder.record(
    task_id="task-123",
    prompt="AuthService depends on TokenService",
    response="Implemented JWT validation",
    repository="myorg/myapp",
    branch="main",
    workspace_path="/workspace",
    success=True,
    changed_files=["auth/service.py"]
)

# Process - Graphiti extracts entities and relationships
await pipeline.process_execution(record)
```

## Project Structure

```
openhands-graphiti-memory/
├── src/
│   ├── knowledge_admission_mvp.py     # Main implementation
│   ├── test_knowledge_admission.py   # Tests (27/27 passing)
│   └── milestone*.py                  # Development milestones
├── docs/
│   ├── GRAPHITI_ARCHITECTURE_AUDIT.md         # Graphiti verification
│   ├── HONEST_ASSESSMENT_VALIDATION_GAP.md    # Benchmark roadmap
│   └── KNOWLEDGE_ADMISSION_MVP_COMPLETE.md    # Usage guide
├── examples/
│   └── quickstart.py                  # Example usage
└── README.md
```

## Documentation

### Essential Reading
- **[Architecture Audit](docs/GRAPHITI_ARCHITECTURE_AUDIT.md)** - Verified Graphiti capabilities
- **[Honest Assessment](docs/HONEST_ASSESSMENT_VALIDATION_GAP.md)** - Current status and what's needed
- **[Complete Guide](docs/KNOWLEDGE_ADMISSION_MVP_COMPLETE.md)** - Full usage documentation

## Testing

```bash
pytest src/test_knowledge_admission.py -v
```

**All 27 tests passing:**
- Admission filtering (5 tests)
- Metadata enrichment (2 tests)
- Execution recording (2 tests)
- Governance (4 tests)
- Repository isolation (2 tests)
- Pipeline integration (5 tests)
- Parameterized scenarios (7 tests)

## Repository Isolation

Uses Graphiti's built-in `group_id`:

```python
# Each repository isolated
group_id = f"repo_{repository}_branch_{branch}"
await graphiti.add_episode(episode_body="...", group_id=group_id)
results = await graphiti.search(query="auth", group_id=group_id)
```

## What's NOT Done Yet

### Benchmarks Needed (See [Honest Assessment](docs/HONEST_ASSESSMENT_VALIDATION_GAP.md))

1. **Entity extraction quality** - Does Graphiti produce `AuthService` or generic `Authentication`?
2. **Admission precision** - What % of memories are useful vs garbage?
3. **Retrieval quality** - Does "explain auth" return relevant entities?
4. **Scale performance** - Latency at 10K, 100K episodes?
5. **Long-running quality** - Graph evolution over 30 days?

**These benchmarks determine production-readiness.**

## Key Components

1. **GraphitiAdapter** - Thin wrapper around Graphiti SDK
2. **MetadataEnricher** - Builds `group_id` for repository isolation
3. **AdmissionPolicy** - Rule-based admission decisions
4. **ExecutionRecorder** - Captures task execution context
5. **BasicGovernance** - Secret detection and size limits

## Architecture Principles

1. **Delegate to Graphiti** - Don't reimplement knowledge graph mechanics
2. **Focus on quality** - Admission decisions are our responsibility
3. **Evidence-based** - Verify before assuming
4. **Graceful degradation** - Memory is optional, not required

## Requirements

```bash
pip install graphiti-core pytest pytest-asyncio
```

## License

MIT

## References

- [Graphiti Documentation](https://help.getzep.com/graphiti)
- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [OpenHands](https://github.com/All-Hands-AI/openhands)

## Contributing

See [Honest Assessment](docs/HONEST_ASSESSMENT_VALIDATION_GAP.md) for validation roadmap.
