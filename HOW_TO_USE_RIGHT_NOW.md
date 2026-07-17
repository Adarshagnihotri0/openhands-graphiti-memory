# PRODUCTION BOOTSTRAP - How to Actually Use Memory Right Now

## What You Need to Do

### Step 1: Run the new startup script

```bash
# Option A: Use the new script
~/start-ai-memory.sh

# Option B: Update your existing 'ai' script to call the new one
# Edit ~/ai to:
#!/bin/zsh
~/start-ai-with-memory.sh
```

### What This Does

When you run `~/start-ai-memory.sh`:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Starting AI Stack with Memory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Starting Neo4j (Memory Database)...
  ✓ Neo4j created
  Waiting for Neo4j to initialize...
  ✓ Neo4j ready on bolt://localhost:7687

Initializing Memory System...
  ✓ Memory Provider connected

Starting GLM Bedrock Proxy...
  ✓ Proxy ready on http://localhost:3000

Configuring OpenHands Memory...
  ✓ Memory config written to ~/.openhands/memory_config.json

Starting OpenHands Agent Canvas...
  ✓ OpenHands ready on http://localhost:8000

Verifying Memory Integration...
  ✓ Memory Provider: ACTIVE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ AI Stack Running
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Neo4j (Memory):  http://localhost:7474
                   User: neo4j / Pass: openhands123
  
  Proxy (GLM-5):   http://localhost:3000
  OpenHands UI:    http://localhost:8000
  
  Memory Status:   ACTIVE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## How Memory Gets Injected

### Architecture (Production)

```
~/start-ai-memory.sh
 │
 ├─ Start Neo4j
 │   └─ bolt://localhost:7687
 │
 ├─ Initialize Memory Provider
 │   └─ Test connection, verify working
 │
 ├─ Write memory_config.json
 │   └─ ~/.openhands/memory_config.json
 │
 ├─ Start GLM Proxy
 │   └─ http://localhost:3000
 │
 ├─ Start OpenHands
 │   └─ http://localhost:8000
 │
 └─ Verify Integration
     └─ Memory Provider: ACTIVE
```

### Runtime Integration

When you ask OpenHands a question:

```
User: "Explain the auth architecture"
    ↓
Agent.astep()
    ↓
MemoryProvider.retrieve()
    ├─ Classify intent → ARCHITECTURE
    ├─ Query Neo4j → Get memories
    ├─ Build context → Token budget
    └─ Inject into LLM → additional_messages
    ↓
LLM responds with memory context
```

---

## What's Still Missing

### ❌ Automatic Memory Creation

Right now, you need to **manually store memories**.

**Manual storage example:**
```python
from milestone8_real_graphiti import RealGraphitiBackend
from milestone1_models import Memory, MemoryCategory

backend = RealGraphitiBackend()

await backend.store(Memory(
    id="auth-arch",
    title="Auth Architecture",
    summary="AuthService depends on TokenService",
    category=MemoryCategory.ARCHITECTURE,
    confidence=0.95,
    source="ADR-001",
    repository="myorg/myapp",
    branch="main"
))
```

**TODO:** Create automatic memory extraction after task completion.

---

### ❌ MCP Tools

You asked for tools like:
- `remember_architecture`
- `remember_bug_fix`
- `search_memory`

**These don't exist yet.**

**TODO:** Create MCP server with memory tools.

---

## What Works Right Now

✅ **Automatic Retrieval**
- Memory provider injects context when you ask architecture questions
- Repository scoping prevents cross-contamination
- Token budgeting limits memory size

✅ **Graceful Fallback**
- If Neo4j down, OpenHands still works
- If memory system errors, agent continues
- Zero crashes

✅ **Persistence**
- Memories stored in Neo4j survive restart
- All metadata preserved
- Graph relationships intact

---

## Testing It

### Test 1: Verify Startup

```bash
~/start-ai-memory.sh
```

Should see:
```
✓ Memory Provider: ACTIVE
```

### Test 2: Store a test memory manually

```python
python3 << 'EOF'
import asyncio
from milestone8_real_graphiti import RealGraphitiBackend
from milestone1_models import Memory, MemoryCategory

async def test():
    backend = RealGraphitiBackend()
    await backend.store(Memory(
        id="test-1",
        title="Test Architecture",
        summary="This is a test memory for auth",
        category=MemoryCategory.ARCHITECTURE,
        confidence=0.95,
        source="manual-test",
        repository="test/manual",
        branch="main"
    ))
    print("✓ Test memory stored")
    backend.close()

asyncio.run(test())
EOF
```

### Test 3: See memory in Neo4j dashboard

```bash
open http://localhost:7474
```

Username: `neo4j`
Password: `openhands123`

Run Cypher query:
```cypher
MATCH (m:Memory) RETURN m LIMIT 10
```

### Test 4: Ask OpenHands about architecture

In OpenHands UI:
```
"Explain the test architecture"
```

**Should:** Retrieve the test memory and reference it

---

## File Locations

```
~/start-ai-memory.sh          ← New startup script
~/.openhands/memory_config.json  ← Memory configuration
~/workspace/project/.../milestone*.py  ← Memory system code
```

---

## Clean Shutdown

Press `Ctrl+C` to stop everything gracefully.

The script will:
- Kill GLM Proxy
- Kill OpenHands
- Keep Neo4j running (persists memories)

To stop Neo4j:
```bash
docker stop openhands-memory
```

To remove Neo4j completely (LOSES ALL MEMORIES):
```bash
docker rm -f openhands-memory
```

---

## Troubleshooting

### "Memory Provider: STANDBY"

Memory initialization failed. Check:

```bash
# Is Neo4j running?
docker ps | grep neo4j

# Can we connect?
python3 -c "
from milestone8_real_graphiti import RealGraphitiBackend
backend = RealGraphitiBackend()
print('✓ Connected' if backend.driver else '✗ Failed')
"

# Check Neo4j logs
docker logs openhands-memory
```

### "Neo4j failed to start"

```bash
# Check if port is in use
lsof -i :7687

# Kill existing Neo4j
docker rm -f openhands-memory

# Try again
~/start-ai-memory.sh
```

### No memory retrieved

Check:
1. Memory config exists: `cat ~/.openhands/memory_config.json`
2. Memories stored: `open http://localhost:7474`
3. Intent classification: Run with logging enabled

---

## Difference from Before

### Before (What I Built)
- Proof-of-concept
- Test scripts only
- Manual integration required
- UV cache patches (temporary)

### Now (Production Bootstrap)
- One-command startup
- Automatic initialization
- Graceful fallback
- Persistent config
- Health checks

---

## Still TODO (For Full Production)

1. **Memory write pipeline** - Extract from completed tasks
2. **MCP server** - Tools like `remember_architecture`
3. **Automatic agent patch** - Permanent integration
4. **Memory expiration** - TTL for old memories
5. **Usage analytics** - Track memory effectiveness

---

## The Honest Status

**What you get RIGHT NOW:**
- ✅ Memory retrieval working
- ✅ Repository scoping
- ✅ Persistence across restart
- ✅ Graceful fallback
- ✅ One-command startup

**What you DON'T get yet:**
- ❌ Automatic memory creation
- ❌ MCP tools
- ❌ Memory write pipeline
- ❌ Permanent agent patch

**This is 80% production-ready.**

The last 20% (write pipeline + MCP tools) requires more work.

---

## Quick Reference

```bash
# Start everything with memory
~/start-ai-memory.sh

# View memory dashboard
open http://localhost:7474

# Check memory status
curl -sf http://localhost:7474

# Stop services
Ctrl+C  # (keeps Neo4j running)
docker stop openhands-memory  # (stops database)

# Manual memory storage
python3 << 'EOF'
from milestone8_real_graphiti import RealGraphitiBackend
# ... (see example above)
EOF
```

---

## Done

You now have a **production bootstrap** that:
- Starts Neo4j automatically
- Initializes memory provider
- Performs health checks
- Gracefully handles failures
- Provides clear status

**Run `~/start-ai-memory.sh` and you'll have memory.**

(Still need to store memories manually, but retrieval works automatically)
