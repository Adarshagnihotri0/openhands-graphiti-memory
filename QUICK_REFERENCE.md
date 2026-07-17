# Graphiti Memory System - Quick Reference

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repository-url>
cd graphiti-memory

# Verify installation
./verify_installation.sh

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start Database

```bash
# Option A: Neo4j (recommended for production)
docker-compose up -d

# Option B: FalkorDB (simpler, good for dev)
docker-compose -f docker-compose.falkordb.yml up -d
```

### 3. Run MCP Server

```bash
# Development
uv run python -m graphiti_memory.mcp.server

# Production (Docker)
docker-compose up
```

## MCP Tools Reference

### Remember Architecture

Store architectural knowledge:

```json
{
  "title": "AuthService Architecture",
  "content": "AuthService validates JWT tokens",
  "component_type": "service",
  "dependencies": ["TokenService", "SessionStore"],
  "interfaces": ["validate_token()", "create_session()"],
  "service": "AuthService",
  "module": "auth"
}
```

### Remember Decision

Store design decisions:

```json
{
  "title": "Database Selection",
  "decision_type": "database",
  "rationale": "Need ACID transactions",
  "content": "Selected PostgreSQL over MongoDB",
  "alternatives_considered": ["MongoDB", "Cassandra"],
  "trade_offs": "Slower writes than NoSQL"
}
```

### Remember Bug Fix

Store bug fixes:

```json
{
  "title": "Race Condition Fix",
  "bug_type": "race condition",
  "root_cause": "Concurrent cache updates",
  "solution": "Implemented Redlock",
  "symptoms": ["Inconsistent state"],
  "prevention": "Always use distributed locks",
  "module": "cache"
}
```

### Remember Convention

Store coding conventions:

```json
{
  "title": "Error Handling",
  "convention_type": "pattern",
  "rule": "Always use Result<T>",
  "rationale": "Explicit error handling",
  "examples": ["Result<User> createUser()"],
  "anti_patterns": ["Throwing exceptions"]
}
```

### Search Memory

Query memories:

```json
{
  "query": "authentication service",
  "memory_types": ["architecture", "decision"],
  "min_confidence": 0.7,
  "limit": 10
}
```

## Environment Variables

### Essential

```bash
# Database
GRAPHITI_DATABASE_URI=bolt://localhost:7687
GRAPHITI_DATABASE_PASSWORD=password

# LLM
GRAPHITI_LLM_API_KEY=sk-xxx
```

### Optional

```bash
# Fine-tuning
GRAPHITI_RETRIEVAL_LIMIT=10
GRAPHITI_CONFIDENCE_THRESHOLD=0.7
GRAPHITI_SEMAPHORE_LIMIT=10
GRAPHITI_LOG_LEVEL=INFO
```

## Programmatic Usage

### Basic Usage

```python
from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.client.graphiti_client import GraphitiClient
from graphiti_memory.service.memory_service import MemoryService
from graphiti_memory.utils.logging import MemoryLogger

# Initialize
config = GraphitiConfig()
logger = MemoryLogger(config)
client = GraphitiClient(config, logger)
await client.initialize()

from graphiti_memory.service.memory_scorer import MemoryScorer
scorer = MemoryScorer(config, logger)
service = MemoryService(config, client, scorer, logger)

# Store memory
uuid = await service.remember_architecture(
    title="Service Architecture",
    content="Description",
    component_type="service",
    dependencies=["OtherService"]
)

# Search memories
from graphiti_memory.models import MemoryQuery
results = await service.search_memories(
    MemoryQuery(query_text="service architecture", limit=10)
)
```

### Pipeline Integration

```python
from graphiti_memory.pipeline import integrate_with_openhands

# Before task
memory_context, pipeline = await integrate_with_openhands(
    config,
    "Fix authentication bug",
    {"repository": "myapp", "module": "auth"}
)

# Use memory_context in task
# ...

# After task
await pipeline.after_task(
    "Fix authentication bug",
    "Fixed JWT validation",
    {"module": "auth"}
)
```

## Memory Types

| Type | Use Case | Key Fields |
|------|----------|------------|
| Architecture | Service/component structure | `component_type`, `dependencies`, `interfaces` |
| Decision | Design choices | `rationale`, `alternatives_considered`, `trade_offs` |
| Bug Fix | Debugging discoveries | `root_cause`, `solution`, `prevention` |
| Convention | Coding patterns | `rule`, `examples`, `anti_patterns` |
| Relationship | Entity connections | `source_entity`, `target_entity`, `relation_type` |
| Implementation | Important notes | `feature`, `gotchas` |

## Confidence Levels

| Level | Range | Description |
|-------|-------|-------------|
| VERIFIED | 0.95-1.0 | Proven multiple times |
| HIGH | 0.85-0.94 | Well-established |
| MEDIUM | 0.70-0.84 | Reasonably certain |
| LOW | 0.50-0.69 | Tentative knowledge |

## Scoping

Memories are scoped by:

```
{repository}_{branch}_{group_id}
```

Example: `myapp_main_openhands_default`

## Common Patterns

### Store Service Dependency

```python
await service.remember_relationship(
    title="AuthService depends on TokenService",
    source_entity="AuthService",
    target_entity="TokenService",
    relation_type="DEPENDS_ON",
    module="auth"
)
```

### Get Recent Bug Fixes

```python
await service.search_memories(
    MemoryQuery(
        query_text="",
        memory_types=[MemoryType.BUG_FIX],
        time_range_days=7,
        limit=20
    )
)
```

### Update Memory

```python
from graphiti_memory.models import MemoryUpdate

await service.update_memory(
    MemoryUpdate(
        uuid=uuid,
        confidence=0.9,
        increment_confidence=True
    )
)
```

## Troubleshooting

### Connection Failed

```bash
# Check database is running
docker ps | grep neo4j

# Check credentials
cat .env | grep GRAPHITI_DATABASE

# Test connection
uv run python -c "
from graphiti_memory.config.settings import GraphitiConfig
config = GraphitiConfig()
print(config.database_uri)
"
```

### Rate Limiting

```bash
# Reduce concurrent operations
export GRAPHITI_SEMAPHORE_LIMIT=5
```

### Low Retrieval

```bash
# Lower threshold
export GRAPHITI_CONFIDENCE_THRESHOLD=0.5

# Increase limit
export GRAPHITI_RETRIEVAL_LIMIT=20
```

## Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f graphiti-mcp

# Stop services
docker-compose down

# Clear data
docker-compose down -v
```

## Testing

```bash
# Unit tests
pytest graphiti_memory/tests/

# With coverage
pytest --cov=graphiti_memory

# Integration tests (requires DB)
pytest -m integration
```

## Metrics Endpoint

```bash
# Get status
curl http://localhost:8000/status

# Via MCP tool
get_status()
```

## File Structure

```
graphiti_memory/
├── client/          # Graphiti client
├── service/         # Business logic
├── mcp/            # MCP server
├── config/         # Configuration
├── utils/          # Logging & metrics
├── tests/          # Test suite
├── models.py       # Data models
├── exceptions.py   # Error handling
└── pipeline.py     # Automation
```

## Best Practices

1. **Scope Properly**: Use repository/branch/module for isolation
2. **Be Specific**: Detailed content improves retrieval
3. **Set Confidence**: Higher confidence = higher priority
4. **Use Tags**: Add tags for better filtering
5. **Update Regularly**: Keep memories current
6. **Check Metrics**: Monitor hit rate and latency

## Anti-Patterns

❌ Don't store source code
❌ Don't store conversation logs
❌ Don't store temporary info
❌ Don't duplicate memories
❌ Don't ignore confidence scores

## Pro Tips

1. Use `increment_confidence=True` for iterative improvements
2. Set module scope for service-specific knowledge
3. Use tags for cross-cutting concerns
4. Query with multiple types for broader context
5. Check metrics to tune thresholds

## Support

- **Docs**: README.md
- **Issues**: GitHub Issues
- **Discord**: Zep #graphiti channel
- **Examples**: examples/quickstart.py
