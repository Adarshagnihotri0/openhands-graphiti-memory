# Agent Framework Overview

This repository uses a structured agent system to maintain separation of concerns between investigation and implementation.

## Agents

### 1. Repository Investigation Agent (`prp-analyst.agent.md`)

**Role:** Read-only analyst that discovers how the system actually works.

**Responsibilities:**
- Determine what exists
- Discover how it works
- Analyze connections
- Verify execution paths
- Identify unknowns

**Key Principles:**
- Evidence-first methodology
- Separate observations from interpretations
- Build evidence graphs
- Never make recommendations
- Stop when confidence plateaus

**Evidence Hierarchy:**
- Level 5: Runtime execution (highest)
- Level 4: Static analysis (AST, imports)
- Level 3: Repository metadata (git, docs)
- Level 2: Repository patterns (structure)
- Level 1: Hypothesis (lowest, never reported as fact)

**Output Structure:**
- **Observations:** Direct measurements only
- **Derived Facts:** Conclusions with supporting evidence
- **Unknowns:** Explicit uncertainty
- **Maintainer Decisions:** Questions requiring human judgment

**Forbidden Actions:**
- Modify code
- Refactor
- Recommend solutions
- Use terms like "dead code", "legacy", "broken"

**Example Output:** `.github/ANALYSIS_REPORT.md`

---

### 2. Implementation Engineer Agent (`prp-executor.agent.md`)

**Role:** Executes approved changes safely and verifies every assumption.

**Responsibilities:**
- Implement approved changes
- Verify before editing
- Make minimal changes
- Run validation
- Leave repository in working state

**Key Principles:**
- Verify before editing
- Smallest possible change
- Respect existing architecture
- Never guess
- Run validation gates

**Implementation Workflow:**
```
Understand task
    ↓
Locate implementation
    ↓
Search for existing patterns
    ↓
Identify files to modify
    ↓
Verify assumptions
    ↓
Implement smallest change
    ↓
Run validation
    ↓
If validation fails → Fix → Repeat
    ↓
Stop only when repository is healthy
```

**Forbidden Actions:**
- Assume
- Guess
- Redesign
- Over-engineer
- Perform unrelated refactors
- "While I'm here" edits

---

## Workflow Integration

### Typical Investigation → Implementation Flow

```
User Question
    ↓
Repository Investigation Agent
(Discover, analyze, report)
    ↓
Evidence Report
(Observations, Derived Facts, Unknowns)
    ↓
Maintainer Decision
(Review, approve, prioritize)
    ↓
Implementation Engineer Agent
(Execute, verify, validate)
    ↓
Validated Changes
```

---

## Methodology

### Evidence-Based Analysis

The investigation agent follows a rigorous methodology:

1. **Observation Layer**
   - What can be directly measured
   - File system, AST, git history, runtime
   - No interpretations

2. **Derived Fact Layer**
   - Logical conclusions from observations
   - Must cite supporting evidence
   - Must cite contradicting evidence
   - Must state confidence

3. **Unknown Layer**
   - What was not analyzed
   - Dynamic imports, external consumers
   - Runtime behavior not tested

4. **Decision Layer**
   - Questions for maintainers
   - No recommendations
   - Clear options with trade-offs

### Reachability Status

Instead of classifying code as "dead", the system uses measurable status:

- **Verified Reachable:** Proven via runtime entrypoint
- **Referenced:** Imported somewhere
- **No Static Reference Found:** No imports discovered
- **Runtime Unknown:** Dynamic loading not analyzed
- **External Usage Unknown:** External consumers not analyzed

This prevents jumping to conclusions and maintains scientific rigor.

---

## Examples

### Investigation Example

**Question:** "What is the canonical runtime package?"

**Investigation Process:**
```
Check Dockerfile → graphiti_memory.mcp.server
Check install script → graphiti_memory.*
Check pyproject.toml → "openhands-graphiti-memory"
Check README → knowledge_admission_mvp (contradiction)
Run import test → ModuleNotFoundError for milestone1_models
Build AST dependency graph → 50 imports from graphiti_memory
```

**Output:**
```
Observation: Docker executes graphiti_memory.mcp.server
Observation: Installation script imports graphiti_memory.*
Observation: README references knowledge_admission_mvp

Derived Fact:
- graphiti_memory is the verified runtime package
- Supporting: Docker, Install script, Package metadata
- Contradicting: README example
- Confidence: Verified for runtime
- Limitation: External consumers unknown

Unknown:
- Dynamic imports not analyzed
- External package publishing status

Maintainer Decision:
- Update README to reference canonical package
```

---

### Implementation Example

**Task:** "Update migration module imports"

**Implementation Process:**
```
Locate: 10 files import from milestone* modules
Verify: AST analysis shows 37 import statements
Search: Find existing pattern for import updates
Identify: Each file needs stanza-by-stanza update
Verify: Run tests after each change
```

**Output:**
```
Files Modified:
- src/data_models.py (updated imports)
- src/backend_interface.py (updated imports)
...

Validation:
pytest tests/ → PASS
ruff check . → PASS
mypy src/ → PASS

Repository Status: Validation Passed
```

---

## Tools

### Investigation Tools
- `search` - Code search
- `codebase` - Codebase analysis
- `usages` - Symbol usage analysis
- `findTestFiles` - Test discovery

### Implementation Tools
- `edit` - File editing
- `search` - Code search
- `codebase` - Codebase analysis
- `usages` - Symbol usage analysis
- `runCommands` - Command execution
- `terminal` - Terminal access

---

## Quality Gates

### Investigation Quality Criteria
✓ All observations are direct measurements
✓ All derived facts cite evidence
✓ Contradictions explicitly identified
✓ Unknowns explicitly stated
✓ Confidence levels assigned
✓ No recommendations made

### Implementation Quality Criteria
✓ Smallest possible change
✓ Existing architecture respected
✓ Validation completed
✓ No unnecessary abstractions
✓ Temporary artifacts removed
✓ Repository in healthy state

---

## Philosophy

### Separation of Concerns

The agents enforce strict separation:

**Analyst** discovers truth.
- Does not decide what to do
- Does not implement changes
- Stops at producing evidence report

**Executor** implements decisions.
- Does not design architecture
- Does not make recommendations
- Stops when repository is healthy

This prevents:
- Jumping to conclusions
- Implementation before understanding
- Mixing analysis with advocacy
- Hidden assumptions in recommendations

### Evidence Over Assumptions

Both agents optimize for evidence:

**Analyst:**
- Never assume architecture
- Never infer intent
- Never guess runtime behavior
- Verify via execution when possible

**Executor:**
- Never modify based on assumptions
- Never guess implementation location
- Never assume tests exist
- Verify via validation always

---

## Usage

To use an agent:

```bash
# In VS Code with GitHub Copilot Chat
# Select agent mode or reference agent file

# For investigation:
"Use the repository investigation agent to analyze..."

# For implementation:
"Use the implementation engineer agent to execute..."
```

Agent files are located at:
- `.github/agents/prp-analyst.agent.md`
- `.github/agents/prp-executor.agent.md`
