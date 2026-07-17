# PHASE 1.5: Execution Path Tracing - NO ASSUMPTIONS

## OBJECTIVE

Trace ONE complete request from HTTP entrypoint to model API call.

**Output required:**
- Sequence diagram with filenames, functions, line numbers
- Exact location where context is finalized
- NO implementation yet

---

## METHOD: Instrumentation

### Step 1: Find Agent Server Process

```bash
# Find actual process running on port 18000
lsof -i :18000 | grep LISTEN
ps aux | grep $(lsof -ti :18000)
```

### Step 2: Locate Agent Server Code

```bash
# Find the actual source files
find /Users/adarshagnihotri -name "*.py" -path "*openhands*" -o -path "*agent*server*" 2>/dev/null | grep -v __pycache__ | grep -v test
```

### Step 3: Add Instrumentation

Before tracing, find where to add print statements:
- Entry point handler
- Prompt builder
- Tool selector
- Model caller

### Step 4: Execute One Request

Send minimal request, capture execution order.

### Step 5: Produce Sequence Diagram

```text
HTTP Request
  ↓
[filename.py:line] ConversationManager.handle()
  ↓
[filename.py:line] Planner.execute()
  ↓
[filename.py:line] PromptBuilder.build()
  ↓
[filename.py:line] ToolRegistry.select()
  ↓
[filename.py:line] LLM.generate()
  ↓
Model API Request
```

---

## EXECUTING NOW

Starting instrumentation...
