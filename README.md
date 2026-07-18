# OpenHands Graphiti Memory System

Persistent knowledge graph memory for OpenHands AI agents using Graphiti.

---

## Problem

OpenHands agents execute tasks but don't remember what they learned. Each session starts from zero.

Existing solutions:
- **No memory**: Agents re-learn the same codebase relationships repeatedly
- **Vector-only memory**: Lacks relational context (e.g., "AuthService depends on TokenService")
- **Graph databases**: Require manual schema design and entity extraction

What's missing: A system that automatically extracts knowledge from task executions and makes it retrievable in future sessions.

---

## Goals

Primary goals:
- Capture execution outcomes automatically
- Decide what's worth remembering
- Store in knowledge graph (via Graphiti)
- Retrieve relevant context for future tasks

Non-goals:
- Not replacing Graphiti's entity extraction
- Not implementing custom graph algorithms
- Not building a general-purpose knowledge base
- Not handling real-time streaming (batch processing only)

---

## Architecture

```
Task Execution
      ↓
Execution Recorder (captures: prompt, response, files changed, success/fail)
      ↓
Admission Policy (filters: trivial operations, failed tasks, secrets)
      ↓
Metadata Enricher (adds: repository, branch, workspace path)
      ↓
Graphiti (entity extraction, relationship mapping, semantic search)
      ↓
Knowledge Graph (stored in Neo4j)
```

### Components

**ExecutionRecorder**
- Captures task context (prompt, response, success flag)
- Tracks changed files and repository details
- Output: `ExecutionRecord` dataclass

**AdmissionPolicy**
- Filters trivial operations (e.g., "list files")
- Rejects failed executions
- Blocks secrets/credentials
- Output: `admit` boolean + reason

**MetadataEnricher**
- Builds repository-scoped `group_id`
- Adds workspace context
- Output: enriched episode body

**GraphitiAdapter**
- Wrapper around Graphiti SDK
- Handles connection pooling
- Error handling with fallback

---

## Design Principles

1. **Delegate to Graphiti**: Don't reimplement entity extraction or embeddings
2. **Admission focus**: Our job is deciding *what* to remember, not *how* to store it
3. **Graceful degradation**: Memory failures don't break agent execution
4. **Repository isolation**: Each repo's knowledge is separate (`group_id`)
5. **Evidence first**: Verify capabilities before assuming (see Architecture Audit)

---

## Features

Implemented:
- [x] Execution recording with context capture
- [x] Rule-based admission policy
- [x] Secret detection (basic patterns)
- [x] Repository isolation via Graphiti `group_id`
- [x] Metadata enrichment (repo/branch/workspace)
- [x] Graphiti SDK integration
- [x] 27 unit tests (all passing)

Not implemented:
- [ ] Entity extraction quality benchmarks
- [ ] Retrieval quality metrics
- [ ] Admission precision tracking
- [ ] Performance benchmarks at scale
- [ ] Long-running graph evolution tests

---

## Project Structure

```
openhands-graphiti-memory/
├── src/                          # Source code
│   ├── knowledge_admission_mvp.py
│   ├── data_models.py
│   ├── backend_interface.py
│   ├── pipeline_builder.py
│   ├── admission_classifier.py
│   ├── graphiti_provider.py
│   ├── graphiti_adapter.py
│   └── graphiti_memory/         # Main memory module
├── tests/                        # Test suite
├── examples/                     # Usage examples
├── scripts/                      # Utility scripts
├── mocks/                        # Test mocks
└── pyproject.toml                # Package config
```

---

## Installation

### Prerequisites

- Python 3.10+
- Neo4j 5.x (local or remote)
- Docker (optional, for Neo4j)

### Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Start Neo4j (Docker):
```bash
docker-compose up -d
```

Or use existing Neo4j instance:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

3. Verify installation:
```bash
bash scripts/verify_installation.sh
```

---

## Usage

### Basic Example

```python
from src.knowledge_admission_mvp import (
    GraphitiAdapter,
    KnowledgeAdmissionPipeline,
    ExecutionRecorder
)

# Connect to Graphiti
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
    response="Implemented JWT validation in auth/service.py",
    repository="myorg/myapp",
    branch="main",
    workspace_path="/workspace",
    success=True,
    changed_files=["auth/service.py", "auth/models.py"]
)

# Process and store
await pipeline.process_execution(record)
```

### Repository Isolation

Each repository uses a separate `group_id`:

```python
# Automatic isolation
group_id = f"repo_{repository}_branch_{branch}"

# Search within repository scope
results = await graphiti.search(
    query="authentication implementation",
    group_id=group_id
)
```

### Admission Filtering

Automatic rejection of:
- Failed executions
- Trivial operations (file listing, directory changes)
- Secrets/credentials (patterns: `password`, `api_key`, `token`, etc.)
- Executions without file changes

---

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src

# Specific test
pytest tests/test_knowledge_admission.py -v
```

Test coverage: 27 tests
- Admission filtering: 5 tests
- Metadata enrichment: 2 tests
- Execution recording: 2 tests
- Governance: 4 tests
- Repository isolation: 2 tests
- Pipeline integration: 5 tests
- Parameterized scenarios: 7 tests

### Development Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linter
ruff check src/

# Run type checker
mypy src/

# Format code
black src/
```

---

## Current Limitations

### Not Benchmarked

These are unknowns (not "good" or "bad", just untested):

1. **Entity extraction quality**: Does Graphiti extract "AuthService" or generic "Authentication Service"?
   
2. **Admission precision**: What percentage of stored memories are actually useful?

3. **Retrieval quality**: Does "explain auth flow" return relevant entities?

4. **Scale performance**: Latency at 10K, 50K, 100K episodes?

5. **Long-running behavior**: Graph quality after 30 days of continuous use?

### Known Constraints

- Admission policy is rule-based (no ML)
- Secret detection uses regex patterns only
- No semantic deduplication (relies on Graphiti)
- Batch processing only (not real-time)
- No memory expiration/decay

---

## References

- [Graphiti Documentation](https://help.getzep.com/graphiti)
- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [OpenHands](https://github.com/All-Hands-AI/openhands)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)

---

## License

MIT
