# Graphiti Memory System for OpenHands

**Persistent Long-Term Memory for AI Agents**

This module integrates [Graphiti](https://github.com/getzep/graphiti) as a persistent long-term memory system for OpenHands, enabling durable knowledge storage and intelligent retrieval across coding sessions.

## Overview

Unlike traditional conversation memory, this system stores **project memory** - durable knowledge about the repository, architecture, conventions, and discoveries that accumulates over time.

### What It Stores

✅ **Architecture Knowledge**
- Service dependencies (AuthService → depends on → TokenService)
- Component relationships (API Gateway → routes to → Microservices)
- Data flows (Request → Gateway → Auth → Service)

✅ **Design Decisions**
- Rationale (Why we chose PostgreSQL over MongoDB)
- Trade-offs (CQRS adds complexity but enables scalability)
- Alternatives considered

✅ **Debugging Discoveries**
- Root causes (Race condition in Redis cache)
- Solutions (Implemented Redlock distributed locking)
- Prevention strategies

✅ **Coding Conventions**
- Patterns (Always use Result<T> for error handling)
- Anti-patterns (Never call repositories from controllers)
- Best practices

✅ **Entity Relationships**
- Module imports (Module A → imports → Utility B)
- Service dependencies (PaymentService → uses → NotificationService)
- API structure (Gateway → owns → Routes → Middleware)

### What It Does NOT Store

❌ Source code (use Code Intelligence MCP for that)
❌ Function definitions
❌ Class implementations
❌ Large code snippets
❌ Conversation history
❌ Reasoning chains
❌ Temporary information

## Architecture

```
                 OpenHands
                      │
             MCP Orchestrator
          ┌───────────┴───────────┐
          │                       │
      Graphiti MCP           Code Index MCP
      (Memory)                (Read Code)
          │                       │
 Architecture              Symbols
 Decisions                 Functions
 Bug history               References
 Conventions               Call Graph
 Relationships             Dependencies
```

**Separation of Concerns:**
- **Graphiti**: Stores *knowledge* about code (what we've learned)
- **Code Index**: Stores actual code (what exists in the repository)

## Features

### 🧠 Intelligent Memory Scoring
- Automatic detection of durable vs. transient knowledge
- Confidence scoring based on context and verification
- Similarity detection to prevent duplicates

### 🔍 Advanced Retrieval
- Semantic search + graph traversal hybrid
- Entity overlap scoring
- Dependency distance ranking
- Recency weighting
- Relationship strength

### 📊 Scoped Memory
- Repository isolation
- Branch-specific memories
- Module/service filtering
- Multi-repository support

### 🔄 Automatic Memory Pipeline
- **Before Task**: Retrieve relevant memories automatically
- **After Task**: Extract and store durable knowledge
- No manual intervention required

### 🛡️ Production Ready
- Graceful degradation when unavailable
- Comprehensive logging and metrics
- Connection pooling and retry logic
- Configurable timeouts

## Installation

### Prerequisites

1. **Graphiti Database**: Neo4j or FalkorDB
2. **LLM API**: OpenAI, Anthropic, or Azure OpenAI
3. **Python**: 3.10 or higher

### Quick Start

```bash
# Clone and install
git clone <repository>
cd graphiti-memory

# Install dependencies
pip install -e .

# Or use uv
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### Docker Setup (Recommended)

```bash
# Using Neo4j
docker-compose -f docker/docker-compose-neo4j.yml up

# Using FalkorDB (Redis-based)
docker-compose up
```

## Configuration

### Environment Variables

Key configuration options (see `.env.example` for complete list):

```bash
# Database
GRAPHITI_DATABASE_PROVIDER=neo4j
GRAPHITI_DATABASE_URI=bolt://localhost:7687
GRAPHITI_DATABASE_USER=neo4j
GRAPHITI_DATABASE_PASSWORD=password

# LLM
GRAPHITI_LLM_PROVIDER=openai
GRAPHITI_LLM_MODEL=gpt-4o-mini
GRAPHITI_LLM_API_KEY=your_key_here

# Memory Settings
GRAPHITI_GROUP_ID=openhands_main
GRAPHITI_REPOSITORY_SCOPE=default
GRAPHITI_RETRIEVAL_LIMIT=10
GRAPHITI_CONFIDENCE_THRESHOLD=0.7
```

### MCP Client Configuration

#### For Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/graphiti-memory",
        "graphiti_memory/mcp/server.py"
      ],
      "env": {
        "GRAPHITI_DATABASE_URI": "bolt://localhost:7687",
        "GRAPHITI_LLM_API_KEY": "your_key_here"
      }
    }
  }
}
```

#### For Cursor IDE

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "url": "http://localhost:8000/mcp/"
    }
  }
}
```

## Usage

### MCP Tools

#### Store Knowledge

```python
# Architecture
remember_architecture(
    title="AuthService Architecture",
    content="AuthService validates JWT tokens and manages sessions",
    component_type="service",
    dependencies=["TokenService", "SessionStore"],
    interfaces=["validate_token()", "create_session()"]
)

# Design Decision
remember_decision(
    title="Database Selection",
    decision_type="database",
    rationale="Need ACID transactions for financial data",
    content="Selected PostgreSQL for transaction support",
    alternatives_considered=["MongoDB", "Cassandra"]
)

# Bug Fix
remember_bug_fix(
    title="Race Condition in Cache",
    bug_type="race condition",
    root_cause="Concurrent updates without locking",
    solution="Implemented Redlock distributed locking",
    prevention="Always use distributed locks for shared resources"
)

# Convention
remember_convention(
    title="Error Handling Pattern",
    convention_type="pattern",
    rule="Always use Result<T> type for operations that can fail",
    rationale="Explicit error handling without exceptions",
    examples=["Result<User> createUser()", "Result<None> deleteUser()"]
)

# Relationship
remember_relationship(
    title="Service Dependencies",
    source_entity="PaymentService",
    target_entity="NotificationService",
    relation_type="DEPENDS_ON"
)
```

#### Query Knowledge

```python
# Search for relevant memories
search_memory(
    query="authentication service architecture",
    memory_types=["architecture", "decision"],
    min_confidence=0.7,
    limit=10
)

# Get recent changes
recent_changes(
    days=7,
    memory_type="bug_fix"
)
```

### Programmatic Integration

```python
from graphiti_memory.pipeline import integrate_with_openhands
from graphiti_memory.config.settings import GraphitiConfig

# Initialize
config = GraphitiConfig()
memory_context, pipeline = await integrate_with_openhands(
    config,
    "Fix authentication bug in AuthService",
    context={"repository": "myapp", "module": "auth"}
)

# Inject memory_context into OpenHands prompt
# memory_context contains relevant architecture, bug fixes, conventions

# After task completes
await pipeline.after_task(
    "Fix authentication bug",
    result="Fixed JWT validation race condition",
    context={"module": "auth"}
)
```

## Memory Quality

### Deduplication

The system automatically detects and updates similar memories instead of creating duplicates:

- Semantic similarity detection
- Scope-aware matching
- Confidence-based merging

### Confidence Scoring

Memories are scored for confidence:

- **Verified** (0.95-1.0): Proven in multiple contexts
- **High** (0.85-0.94): Well-established knowledge
- **Medium** (0.70-0.84): Reasonably certain
- **Low** (0.50-0.69): Tentative knowledge

### Versioning

All memories include:

- Creation timestamp
- Last update timestamp
- Version history (stored in Graphiti)
- Provenance tracking

## Observability

### Metrics

The system tracks:

- Retrieval latency
- Storage latency
- Hit/miss rates
- Memory counts by type
- Error rates

### Logging

All operations are logged with structured logging:

```python
{
    "timestamp": "2024-01-15T10:30:00Z",
    "operation": "store",
    "memory_type": "architecture",
    "confidence": 0.85,
    "latency_ms": 150.5
}
```

### Health Checks

```python
status = get_status()
# Returns: {
#   "connected": True,
#   "config": {...},
#   "metrics": {...}
# }
```

## Failure Handling

The system is designed to be **optional**:

1. **Graceful Degradation**: OpenHands continues working if Graphiti is unavailable
2. **Local Cache**: Falls back to in-memory cache on failure
3. **No Crashes**: All errors are caught and logged
4. **Retry Logic**: Automatic retries with exponential backoff

## Development

### Running Tests

```bash
# Unit tests
pytest graphiti_memory/tests/

# With coverage
pytest --cov=graphiti_memory graphiti_memory/tests/

# Integration tests (requires running Graphiti)
pytest -m integration graphiti_memory/tests/
```

### Code Quality

```bash
# Linting
ruff check graphiti_memory/

# Type checking
mypy graphiti_memory/

# Formatting
black graphiti_memory/
```

## Architecture Decisions

### Why Graphiti?

- **Knowledge Graph**: Native support for entities and relationships
- **Temporal Awareness**: Time-based queries and bi-temporal storage
- **Hybrid Search**: Semantic + graph traversal
- **MCP Native**: Built-in MCP server support
- **Production Ready**: Used in production at Zep

### Why Separate from Code Index?

- **Different Use Cases**: Memory (what we learned) vs. Code (what exists)
- **Different Access Patterns**: Narrative knowledge vs. structural queries
- **Different Providers**: Graphiti (Neo4j/FalkorDB) vs. Code Index (various)
- **Clean Separation**: Following advanced agent system patterns

### Why Project Memory Not Conversation Memory?

- **Durable**: Persists across sessions
- **Scoped**: Repository-specific, not user-specific
- **Structured**: Entities and relationships, not chat logs
- **Relevant**: High-value knowledge only

## Examples

### Storing Architecture

```
User: "AuthService depends on TokenService"
System:
  - Creates Entity: AuthService (type: Service)
  - Creates Entity: TokenService (type: Service)
  - Creates Edge: DEPENDS_ON
  - Stores relationships
  - Calculates confidence: 0.85
```

### Storing Bug Fix

```
User: "Fixed race condition in Redis cache by adding Redlock"
System:
  - Creates Memory: BugFix
  - Extracts: root_cause, solution, prevention
  - Links to: Redis (Entity)
  - Links to: Cache (Entity)
  - Adds tags: ["race condition", "redis", "distributed lock"]
  - Confidence: 0.90 (verified by implementation)
```

### Retrieving Before Task

```
Task: "Optimize database queries in PaymentService"

Retrieved Memories:
1. [ARCHITECTURE] PaymentService uses PostgreSQL
2. [CONVENTION] Always use query builders, never raw SQL
3. [DECISION] Selected connection pooling with PGBouncer
4. [BUG_FIX] Fixed N+1 queries by eager loading
5. [RELATIONSHIP] PaymentService → depends on → TransactionDB

Injected into context for better task execution.
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Support

- **Issues**: GitHub Issues
- **Discord**: Zep Discord #graphiti channel
- **Docs**: https://docs.openhands.dev/

## Acknowledgments

- Built on [Graphiti](https://github.com/getzep/graphiti) by Zep
- Integrated with [OpenHands](https://github.com/All-Hands-AI/OpenHands)
- MCP protocol by Anthropic
