# VERIFICATION PLAN - Proving Not Assuming

This is the **correct approach**: Start with Level 0 (verify integration exists), then work up.

---

## ⚠️ Critical Realization

**I built on assumptions.**

I assumed:
- `agent.register_pre_task_hook()` exists
- OpenHands has lifecycle hooks
- Integration point is clearly defined

**I need to VERIFY first, then integrate.**

---

## Level 0: Verify Integration Points (BEFORE ANY TESTING)

### Step 1: Inspect OpenHands Codebase

```bash
# Clone OpenHands
git clone https://github.com/All-Hands-AI/OpenHands
cd OpenHands

# Search for hook mechanisms
grep -r "pre_task" --include="*.py" | head -20
grep -r "register.*hook" --include="*.py" | head -20
grep -r "lifecycle" --include="*.py" | head -20

# Find agent classes
find . -name "*agent*.py" | grep -v test | grep -v __pycache__

# Find MCP integration points
find . -name "*mcp*.py" | grep -v test | grep -v __pycache__

# Find tool execution
grep -r "execute.*tool\|run.*tool" --include="*.py" | head -20

# Find context building
grep -r "build.*context\|construct.*prompt" --include="*.py" | head -20
```

### Step 2: Examine Key Files

Based on OpenHands architecture, likely integration points:

1. **Agent Class** (`openhands/agent/`)
   - Look for task execution methods
   - Look for context building
   - Look for pre/post execution hooks

2. **Controller** (`openhands/controller/`)
   - Look for task orchestration
   - Look for state management

3. **MCP Integration** (`openhands/mcp/` or similar)
   - Look for tool discovery
   - Look for tool execution

4. **Prompt Builder** (wherever prompts are constructed)
   - This is WHERE memory should be injected

### Step 3: Identify ACTUAL Integration Point

**If hooks exist:**
```python
# Use my hook design
agent.register_pre_task_hook(memory_integration.pre_task_hook)
agent.register_post_task_hook(memory_integration.post_task_hook)
```

**If hooks DON'T exist, find alternatives:**

#### Alternative A: Prompt Builder Injection
```python
# Find where prompts are built
# Example: openhands/llm/prompt_builder.py

class PromptBuilder:
    def build_system_prompt(self, task: str):
        # INJECT HERE
        memory_context = await memory_integration.retrieve(task)
        prompt = f"{memory_context}\n\n{task}"
        return prompt
```

#### Alternative B: MCP Orchestrator Middleware
```python
# Find MCP orchestration layer
# Example: openhands/mcp/orchestrator.py

class MCPOrchestrator:
    async def execute_task(self, task: str):
        # INJECT HERE - before task execution
        memory_context = await memory_integration.pre_task(task)
        
        result = await self.agent.execute(task)
        
        # INJECT HERE - after task execution
        await memory_integration.post_task(task, result)
        
        return result
```

#### Alternative C: Agent Task Method
```python
# Find agent's main execution method
# Example: openhands/agent/base.py

class Agent:
    async def run(self, task: str):
        # INJECT HERE
        context = await memory_integration.pre_task(task)
        enhanced_task = f"{context}\n\n{task}"
        
        result = await self._execute(enhanced_task)
        
        # INJECT HERE
        await memory_integration.post_task(task, result)
        
        return result
```

#### Alternative D: MCP Tool Wrapper
```python
# Wrap all MCP tool calls
# Example: openhands/mcp/tool_executor.py

class ToolExecutor:
    async def execute(self, tool: str, args: dict):
        if tool == "task_start":  # Or similar
            # Inject memory before task tools
            memory_context = await memory_integration.pre_task(args['task'])
            args['context'] = memory_context
        
        result = await self._execute_raw(tool, args)
        
        if tool == "task_complete":
            await memory_integration.post_task(args['task'], result)
        
        return result
```

---

## Level 1: Test Graphiti Itself (Forget OpenHands)

### Test

```python
# test_graphiti_basic.py
import asyncio
from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.client.graphiti_client import GraphitiClient
from graphiti_memory.service.memory_service import MemoryService

async def test_level1():
    """
    Level 1: Does Graphiti work?
    
    NO OpenHands involved.
    """
    config = GraphitiConfig()
    client = GraphitiClient(config)
    await client.initialize()
    
    # Test 1: Store
    uuid = await client.add_episode(
        name="Test Architecture",
        episode_body="AuthService depends on TokenService",
        source="test"
    )
    print(f"✓ Memory stored: {uuid}")
    
    # Test 2: Retrieve
    results = await client.search_nodes("authentication")
    print(f"✓ Memory retrieved: {len(results)} results")
    
    assert len(results) > 0, "Should retrieve stored memory"
    
    await client.close()
    print("✅ Level 1 PASSED: Graphiti works")

asyncio.run(test_level1())
```

### Expected

```
✓ Memory stored: abc-123
✓ Memory retrieved: 1 results
✅ Level 1 PASSED: Graphiti works
```

**If this FAILS, stop. Everything else is pointless.**

---

## Level 2: Test MCP Server (Still No OpenHands)

### Test

```bash
# Start MCP server
uv run python -m graphiti_memory.mcp.server &

# Use MCP inspector or direct call
mcp-client call remember_architecture '{
  "title": "AuthService",
  "content": "Depends on TokenService",
  "component_type": "service"
}'

mcp-client call search_memory '{"query": "authentication"}'
```

### Expected

```
✓ MCP tool called successfully
✓ Memory returned
✓ Correct format

OpenHands NOT involved.
MCP works independently.
```

---

## Level 3: Can OpenHands SEE the MCP?

### Test

```bash
# Start OpenHands with Graphiti MCP configured
openhands --mcp-servers='{"graphiti": "http://localhost:8000/mcp"}'

# Ask trivial question
User: "Search project memory for authentication"

# Watch logs
```

### Expected Logs

```
[INFO] MCP server connected: graphiti
[INFO] Discovered tools: remember_architecture, search_memory, ...
[INFO] Tool call: search_memory(args={"query": "authentication"})
[INFO] Result: {...}
```

### What This Proves

- OpenHands can discover Graphiti MCP
- OpenHands can call tools
- MCP responds correctly

**If no tool call happens, you don't have integration.**

---

## Level 4: The Persistence Test ⭐ (CRITICAL)

### Session A

```bash
# Start fresh
docker-compose down -v  # Delete all data
docker-compose up -d

# OpenHands Session 1
User: "Analyze the architecture and remember that AuthService depends on TokenService"

# Or manually:
User: "Remember: AuthService depends on TokenService"

# Check memory count
curl localhost:8000/status
# Expected: {"storage_count": 1, ...}

# Shutdown
docker-compose down
```

### Session B (NEW SESSION)

```bash
# Restart everything
docker-compose up -d

# OpenHands Session 2 (NO PRIOR CONTEXT)
User: "How does authentication work?"
# DO NOT mention AuthService

# CRITICAL: Check logs for automatic retrieval
```

### Expected Automatic Flow

```
User: How does authentication work?
    ↓
[PRE-TASK HOOK FIRES]  ← THIS MUST HAPPEN
    ↓
search Graphiti: "authentication"
    ↓
Found: AuthService memory
    ↓
Inject into prompt
    ↓
LLM answers with knowledge from previous session
```

### What To Check

```bash
# Logs should show:
grep "Retrieved memories" logs/openhands.log
grep "Injected into prompt" logs/openhands.log

# Should see memory was queried AUTOMATICALLY
# NOT manually invoked by user
```

### Success Criteria

✅ Memory retrieved **without** manual `search_memory` call
✅ OpenHands mentions AuthService/TokenService relationship
✅ Knowledge from Session A used in Session B

**This proves persistence.**

---

## Level 5: Automatic Retrieval Test (NO MANUAL SEARCH)

### Test

```bash
User: "Fix login bug"

# DO NOT CALL search_memory
# Check logs automatically
```

### Expected Logs

```
[INFO] Task received: Fix login bug
[INFO] Pre-task hook executed
[INFO] Searching Graphiti...
[INFO] Retrieved: 3 memories
[INFO] Injecting: 2 memories (1500 tokens)
[INFO] LLM processing...
[INFO] Result: ...
```

### Failure Mode

```
[INFO] Task received: Fix login bug
[INFO] Executing task...
[INFO] Result: ...

# NO memory retrieval
# Integration FAILED
```

---

## Level 6: Automatic Storage Test

### Test

```bash
User: "Fix the ReplayEngine bug caused by state hash mismatch"

# Task completes successfully
```

### Verify Storage

```bash
# Direct Graphiti query (bypass OpenHands)
curl -X POST localhost:8000/mcp/search_memory \
  -d '{"query": "ReplayEngine state hash"}'

# Should contain:
# - ReplayEngine
# - State hash
# - Bug fix
# - Verification status
```

### If Not Stored

Post-task hook isn't working.

---

## Level 7: Token Budget Test

### Setup

```bash
# Populate 500 memories
for i in {1..500}; do
  mcp-client call remember_architecture "..."
done
```

### Test

```bash
User: "Explain authentication"

# Check logs for budget management
```

### Expected Logs

```
[INFO] Retrieved from Graphiti: 312 memories
[INFO] Filtered by confidence: 45 memories
[INFO] Selected top: 5 memories (1900 tokens)
[INFO] Injecting into prompt...
```

### FAILURE Mode

```
[INFO] Retrieved: 312 memories
[INFO] Injecting all 312... (60k tokens)  ← BAD
```

---

## Level 8: Conflict Test

### Test

```bash
User: "Remember: Redis is source of truth"

# Later
User: "Remember: PostgreSQL is source of truth"
```

### Verify

```bash
# Query Graphiti
# Expect:
# Memory 1: "Redis is source of truth" [SUPERSEDED]
# Memory 2: "PostgreSQL is source of truth" [ACTIVE]
```

---

## Level 9: Failure Test

### Test

```bash
# Turn off Graphiti
docker-compose stop graphiti

# Try to use OpenHands
User: "Explain authentication"
```

### Expected

```
[WARN] Graphiti unavailable, using fallback
[INFO] Searching filesystem...
[INFO] Answer generated successfully
```

**Should NOT crash.**

---

## Level 10: Real-World Test (ONLY ONE THAT MATTERS)

### Setup

```bash
# Clone NEW repository
git clone https://github.com/someone/unknown-repo
cd unknown-repo

# Clear all memory
curl -X DELETE localhost:8000/clear

# Start fresh
```

### Workflow

```bash
# Session 1
User: "Explore this repository and understand the architecture"

# Agent explores, learns, stores memories

# Check memory count
curl localhost:8000/status
# Expect: Multiple memories stored
```

### The Real Test

```bash
# Shutdown, restart
docker-compose restart

# Session 2
User: "Where should I implement OAuth?"

# CRITICAL: Agent should immediately understand architecture
# WITHOUT re-exploring entire repository
```

### Success

```
Agent response:
"Based on the architecture, you should implement OAuth in AuthService,
 which depends on TokenService. The auth flow is: ..."
```

**Agent has INSTANT knowledge of new repository.**

**This is the goal.**

---

## Summary: The Proving Process

```
Level 0: Verify integration points exist in OpenHands ✓
Level 1: Test Graphiti alone ✓
Level 2: Test MCP alone ✓
Level 3: Test OpenHands can see MCP ✓
Level 4: Test persistence across sessions ⭐
Level 5: Test automatic retrieval (no manual calls) ⭐
Level 6: Test automatic storage ⭐
Level 7: Test token budget ⭐
Level 8: Test conflict handling ⭐
Level 9: Test failure mode ⭐
Level 10: Real-world new repo test ⭐⭐⭐
```

**Only Levels 4-10 actually prove the system works as intended.**

---

## Before Running ANY Tests

**MOST IMPORTANT STEP:**

```bash
# Verify hook mechanism exists
cd OpenHands
grep -r "register.*hook\|pre_task\|lifecycle" --include="*.py"

# If NOT FOUND → Find actual integration point
# Don't build on assumptions
```

**If hooks don't exist, my integration design is wrong.**

**I need to verify FIRST.**
