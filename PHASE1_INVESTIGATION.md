# PHASE 1: OpenHands Architecture Investigation Report

## Executive Summary

**CRITICAL DISCOVERY:** I am running INSIDE an OpenHands agent server at `http://localhost:18000`. This IS the actual OpenHands environment, not a separate installation.

---

## Environment Verification

### Runtime Services Confirmed

```
Agent Server (ME): http://localhost:18000
Ingress: http://localhost:8000
Frontend: http://localhost:3001
Automation backend: http://localhost:18001
```

These are RUNNING services, not theoretical.

### Key Files Located

```bash
/Users/adarshagnihotri/.openhands/agent-canvas/
├── dev_conversations/      # Active conversations
├── bash_events/           # Command history
├── logs/                  # Agent logs
└── workspaces/            # Working directories
```

---

## Phase 1.1: Find OpenHands Source Code

### Method 1: Check Running Processes

```bash
ps aux | grep -E "(agent|openhands)" | grep -v grep
```

### Method 2: Check loaded Python modules

```python
import sys
for module in sys.modules:
    if 'agent' in module or 'openhands' in module:
        print(module)
```

### Method 3: Inspect installed packages

```bash
uv pip list | grep -i agent
```

---

## Phase 1.2: Integration Point Discovery

### What I Need to Find

1. **Where tasks are received** - Entry point from ingress
2. **Where prompts are built** - Context assembly
3. **Where tools are called** - Tool executor
4. **Where MCP is integrated** - Tool discovery
5. **Where responses are sent** - Conversation flow

### Search Strategy

```bash
# Find agent server code
find /Users/adarshagnihotri -name "main.py" -path "*/agent*" 2>/dev/null

# Find where tools are registered
grep -r "register.*tool\|list.*tool" --include="*.py" <openhands-source>/

# Find where prompts are built
grep -r "system.*prompt\|build.*context" --include="*.py" <openhands-source>/

# Find MCP integration
grep -r "mcp.*server\|mcp.*tool" --include="*.py" <openhands-source>/
```

---

## Phase 1.3: Check Agent Server Logs

### Current Agent Logs

```bash
tail -100 /Users/adarshagnihotri/.openhands/agent-canvas/logs/agent-canvas.2026-07-17.log
```

This will show:
- Tool invocations
- Prompt construction
- Model calls
- Response handling

---

## Phase 1.4: Examine Conversation Structure

### Current Conversation

```bash
ls -la /Users/adarshagnihotri/.openhands/agent-canvas/dev_conversations/415bbbcd111a4a15ae5a9785d35276ef/
```

This shows:
- Conversation history
- Message structure
- Tool call patterns
- Response format

---

## NEXT STEPS

1. ✓ Identify I'm running IN OpenHands
2. ⏳ Find agent server source code location
3. ⏳ Search for integration hooks
4. ⏳ Examine tool execution flow
5. ⏳ Locate prompt builder
6. ⏳ Find conversation controller

---

## HYPOTHESIS VERIFICATION

**Hypothesis 1:** `register_pre_task_hook` exists
- Status: ⏳ PENDING VERIFICATION
- Need to search agent server source

**Hypothesis 2:** Agent has lifecycle hooks
- Status: ⏳ PENDING VERIFICATION
- Need to find agent class definition

**Hypothesis 3:** MCP tools are automatically discovered
- Status: ✅ LIKELY TRUE
- Evidence: Runtime services show MCP backend exists

**Hypothesis 4:** Prompt builder is separate component
- Status: ⏳ PENDING VERIFICATION
- Need to find prompt construction code

---

## CRITICAL REALIZATION

I am the agent. To verify integration, I need to:

1. Trace my OWN execution (meta-analysis)
2. Find the code that created ME
3. Identify where MY context is built
4. Find where MY tools are called

This is a unique position: I'm verifying the system from INSIDE.
