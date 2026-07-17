# Graphiti Memory System for OpenHands

## Project Overview

This is a **persistent long-term memory system** for OpenHands built on Graphiti knowledge graphs. It stores durable project knowledge (architecture, decisions, conventions) separate from source code.

## Key Architecture

### Separation of Concerns
- **Graphiti Memory (This System)**: Stores KNOWLEDGE about code
  - Architecture decisions
  - Design rationale
  - Bug fix discoveries
  - Coding conventions
  - Entity relationships

- **Code Index (Separate MCP)**: Stores actual SOURCE CODE
  - Function definitions
  - Class implementations
  - AST nodes
  - Code embeddings

### Technology Stack
- **Database**: Neo4j or FalkorDB (Redis-based)
- **LLM**: OpenAI, Anthropic, or Azure OpenAI
- **Protocol**: MCP (Model Context Protocol)
- **Framework**: Graphiti Core (knowledge graph)

## Project Structure

```
graphiti_memory/
├── client/
│   └── graphiti_client.py    # Graphiti wrapper with retry/timeout
├── service/
│   ├── memory_scorer.py      # Determines what's worth remembering
│   └── memory_service.py     # Core business logic
├── mcp/
│   └── server.py             # MCP tools implementation
├── config/
│   └── settings.py           # Configuration management
├── utils/
│   └── logging.py            # Structured logging & metrics
├── models.py                  # Pydantic data models
├── exceptions.py              # Custom exceptions
└── pipeline.py                # Automatic memory lifecycle
```

## Key Components

### 1. GraphitiClient
- Connection pooling
- Automatic retries with exponential backoff
- Timeout handling
- Graceful degradation

### 2. MemoryScorer
- Detects durable vs. transient knowledge
- Calculates confidence scores
- Prevents duplicate memories
- Calculates similarity

### 3. MemoryService
- Store/retrieve/update/delete memories
- Scoped by repository/branch/module
- Automatic deduplication
- Confidence-based filtering

### 4. MCP Server
Exposes tools:
- `remember_architecture`
- `remember_decision`
- `remember_bug_fix`
- `remember_convention`
- `remember_relationship`
- `search_memory`
- `update_memory`
- `delete_memory`
- `recent_changes`
- `get_status`

### 5. MemoryPipeline
- **Before Task**: Retrieve relevant memories
- **After Task**: Extract and store durable knowledge

## Configuration

All configuration via environment variables (see `.env.example`):

```bash
# Database
GRAPHITI_DATABASE_PROVIDER=neo4j
GRAPHITI_DATABASE_URI=bolt://localhost:7687

# LLM
GRAPHITI_LLM_PROVIDER=openai
GRAPHITI_LLM_MODEL=gpt-4o-mini
GRAPHITI_LLM_API_KEY=your_key

# Memory Settings
GRAPHITI_REPOSITORY_SCOPE=default
GRAPHITI_RETRIEVAL_LIMIT=10
GRAPHITI_CONFIDENCE_THRESHOLD=0.7
```

## How to Use

### As MCP Server

1. Start Neo4j/FalkorDB:
   ```bash
   docker-compose up
   ```

2. Configure MCP client (Claude Desktop, Cursor):
   ```json
   {
     "mcpServers": {
       "graphiti-memory": {
         "command": "uv",
         "args": ["run", "graphiti_memory/mcp/server.py"]
       }
     }
   }
   ```

3. Use tools in conversations

### Programmatically

```python
from graphiti_memory.pipeline import integrate_with_openhands

# Before task
memory_context, pipeline = await integrate_with_openhands(
    config, "Fix auth bug", {"repository": "myapp"}
)

# After task
await pipeline.after_task("Fix auth bug", result, context)
```

## Testing

```bash
# Unit tests
pytest graphiti_memory/tests/

# Integration tests (requires running Graphiti)
pytest -m integration
```

## Important Conventions

### Memory Types
- **Architecture**: Service dependencies, component structure
- **Decision**: Design choices with rationale
- **Bug Fix**: Root cause → solution mapping
- **Convention**: Patterns and best practices
- **Relationship**: Entity connections
- **Implementation**: Important gotchas

### Never Store
- Source code (use Code Index MCP)
- Conversation history
- Temporary information
- Raw stack traces without analysis

### Always Store
- Why decisions were made
- How bugs were fixed
- Discovered patterns
- Important warnings/gotchas

## Failure Handling

The system is designed to be **optional**:
- OpenHands continues if Graphiti is down
- Falls back to local cache
- All errors logged but don't crash
- Retry logic with exponential backoff

## Metrics Tracked

- Retrieval latency
- Storage latency
- Hit/miss rates
- Memory counts by type
- Error rates

## Development Notes

### Adding New Memory Type
1. Add model in `models.py`
2. Add convenience method in `MemoryService`
3. Add tool in `mcp/server.py`
4. Add extraction logic in `pipeline.py`
5. Add tests in `tests/`

### Tuning Memory Scoring
Adjust patterns in `MemoryScorer.__init__`:
- `durable_patterns`: What to remember
- `transient_patterns`: What to ignore
- Adjust scoring weights

### Database Migration
Supports both Neo4j and FalkorDB:
- Neo4j: Better for production, more features
- FalkorDB: Simpler, Redis-based, good for dev

## Common Issues

### Issue: "Graphiti not connected"
**Solution**: Check database is running, credentials correct

### Issue: "429 Rate Limit errors"
**Solution**: Lower `GRAPHITI_SEMAPHORE_LIMIT` (default: 10)

### Issue: "Duplicate memories"
**Solution**: System auto-detects; tune similarity threshold in config

### Issue: "Memory not retrieved"
**Solution**: Lower `GRAPHITI_CONFIDENCE_THRESHOLD` (default: 0.7)

## Integration with OpenHands

The system integrates via MCP protocol:

1. **Before Task**: Agent calls `search_memory` to get relevant context
2. **During Task**: Agent has memory context in prompt
3. **After Task**: Agent determines if knowledge should be stored
4. **Automatic**: Pipeline can analyze and store automatically

This is **project memory**, not conversation memory - it persists across sessions.

## Future Enhancements

- [ ] LLM-based memory extraction (better quality)
- [ ] Memory expiration policies
- [ ] Community detection among entities
- [ ] Temporal queries (what changed when)
- [ ] Memory versioning UI
- [ ] Cross-repository memory sharing

## References

- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [OpenHands Docs](https://docs.openhands.dev/)
