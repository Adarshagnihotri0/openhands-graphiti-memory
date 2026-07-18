# Repository Evolution Audit: Candidate Legacy Files

**Date:** 2026-07-18  
**Methodology:** Repository Evolution Audit (Phases 0-8)  
**Question:** What is the role of the candidate legacy files?

---

## Decision Matrix

| Question | Evidence | Status | Confidence |
|----------|----------|--------|------------|
| **Is there a canonical implementation?** | Docker entry point, install script, package structure | ✅ **VERIFIED** | ★★★★☆ (Direct) |
| **Did a rename/refactor occur?** | Git commit `7e0e3ab`: "File renaming (milestone → descriptive)" | ✅ **VERIFIED** | ★★★★☆ (Direct) |
| **Were imports updated during refactor?** | Git shows: files renamed via `git mv`, contents unchanged | ✅ **VERIFIED** | ★★★★☆ (Direct) |
| **Are renamed files imported?** | AST analysis: 33 static imports of `milestone*` modules | ✅ **VERIFIED** | ★★★★☆ (Direct) |
| **Are renamed files executed at runtime?** | Not yet tested | ⏳ **UNKNOWN** | — |
| **Are they part of the public API?** | No entry points in `pyproject.toml` | ✅ **VERIFIED** | ★★★☆☆ (Inferred) |
| **Are external users depending on them?** | Not yet verified (check package publishing) | ⏳ **UNKNOWN** | — |
| **Is a compatibility layer required?** | Depends on external users (unknown) | ⏳ **DECISION PENDING** | — |
| **What is their intended role?** | Git history suggests: **renamed but imports not updated** | ⚠️ **HYPOTHESIS** | ★★★☆☆ (Inferred) |

---

## Phase Findings

### Phase 0: Canonical Implementation ✅ VERIFIED

**Question:** What is the production implementation?

**Evidence:**
- Docker: `CMD ["uv", "run", "python", "-m", "graphiti_memory.mcp.server"]`
- Install: `scripts/verify_installation.sh` imports `graphiti_memory.*`
- Package: `src/graphiti_memory/` with proper structure
- Config: `pyproject.toml` defines `openhands-graphiti-memory`

**Finding:** `src/graphiti_memory/` is canonical.

---

### Phase 1: Repository History ✅ VERIFIED

**Question:** What does git history reveal?

**Timeline:**
```
2026-07-18 03:13  feat: Complete Knowledge Admission MVP with Graphiti integration
2026-07-18 08:31  refactor: reorganize project structure
```

**Refactor commit (`7e0e3ab`) details:**
```
File renaming (milestone → descriptive):
- milestone1_models.py → data_models.py
- milestone2_backend.py → backend_interface.py
- milestone3_builder.py → pipeline_builder.py
- milestone4_classifier.py → admission_classifier.py
- milestone5_provider.py → graphiti_provider.py
- milestone6_graphiti.py → graphiti_adapter.py
- milestone7_metrics.py → metrics_collector.py
- milestone8_real_graphiti.py → graphiti_client.py
- milestone9_persistence.py → persistence_layer.py
- milestone10_metrics.py → performance_metrics.py
- milestone11_feedback.py → feedback_processor.py
- milestone12_ranking.py → result_ranker.py
```

**Critical Finding:** Files were **renamed** but **imports were NOT updated**.

**Evidence:**
- Renamed via `git mv` (showing `=>` syntax)
- File contents unchanged (`0` bytes diff)
- No commit updating import statements

**Interpretation:** Incomplete refactor.

---

### Phase 2: Architecture Graph ✅ VERIFIED

**Question:** What is the architecture?

**From Git/Governance:**
```
Task Execution
      ↓
Execution Recorder
      ↓
Admission Policy
      ↓
Metadata Enricher
      ↓
Graphiti (entity extraction, relationship mapping)
      ↓
Knowledge Graph (Neo4j)
```

**Canonical Components:**
- `graphiti_memory.mcp.server` - MCP server entry point
- `graphiti_memory.service.memory_service` - Core service
- `graphiti_memory.client.graphiti_client` - Graphiti wrapper
- `graphiti_memory.models` - Pydantic models

**Legacy Components (renamed but unused?):**
- `src/knowledge_admission_mvp.py` - Described in README
- `src/data_models.py` - Renamed from `milestone1_models`
- `src/backend_interface.py` - Renamed from `milestone2_backend`
- etc.

---

### Phase 3: Dependency Graph ✅ VERIFIED

**Question:** What are the static dependencies?

**AST Analysis Results:**

| Module | Static Imports | Imported By |
|--------|----------------|-------------|
| `milestone1_models` | 33 | 10 files (all in `src/`) |
| `milestone2_backend` | 4 | 3 files |
| `milestone3_builder` | 3 | 3 files |
| `milestone8_real_graphiti` | 4 | 4 files |
| `milestone4_classifier` | 2 | 2 files |
| `milestone5_provider` | 2 | 2 files |
| `milestone6_graphiti` | 1 | 1 file |

**Critical Finding:** All imports reference **original module names** (`milestone*`), not renamed files.

**Dependency Chain:**
```
milestone1_models.Memory
    ↓ imported by
backend_interface.py, data_models.py, etc.
    ↓ but files were renamed to
data_models.py, backend_interface.py
    ↓ creating
BROKEN IMPORTS
```

---

### Phase 4: Runtime Verification ⏳ UNKNOWN

**Question:** Do these files execute?

**Status:** Not yet tested

**Next Verification:**
```bash
# Test if renamed files can be imported
python3 -c "import src.data_models"
python3 -c "import src.backend_interface"

# Test if milestone imports work
python3 -c "from milestone1_models import Memory"
```

**Hypothesis:** Files will fail to import due to missing `milestone*` modules.

---

### Phase 5: External API Verification ⏳ UNKNOWN

**Question:** Are these files part of the public API?

**Evidence Found:**
- No entry points in `pyproject.toml`
- README.md references `knowledge_admission_mvp`
- Examples reference milestone modules

**Status:** Internal API (likely), but needs verification of package publishing.

---

### Phase 6: Migration Status ✅ VERIFIED

**Question:** Is migration complete?

**Finding:** Migration is **incomplete**.

**Evidence:**
1. Files were renamed (commit `7e0e3ab`)
2. Imports were NOT updated (no subsequent commit)
3. Result: Files import from non-existent modules

**Hypothesis:** Refactor was started but not finished.

---

### Phase 7: Migration Strategy ⏳ DECISION REQUIRED

**Question:** What should happen to these files?

**Options:**

**Option A: Complete the refactor**
- Update all `milestone*` imports to use renamed files
- Run tests
- Verify execution
- Archive or integrate

**Option B: Revert the rename**
- Rename files back to `milestone*.py`
- Verify everything works
- Plan proper migration

**Option C: Delete unused files**
- Verify no external dependencies
- Check if files are dead code
- Remove without migration

**Decision Required from Maintainer:**
- [ ] Which option to pursue?
- [ ] Are there external users?
- [ ] Is backward compatibility required?

---

### Phase 8: Validation ⏸️ PENDING DECISION

**Cannot proceed to archival until:**
1. Runtime execution verified
2. External API usage determined
3. Migration strategy chosen
4. Tests passing

---

## Verified Facts

1. ✅ **Canonical implementation exists:** `src/graphiti_memory/`
2. ✅ **Refactor occurred:** Commit `7e0e3ab` renamed milestone files
3. ✅ **Imports not updated:** Files still reference `milestone*` modules
4. ✅ **Canonical is used:** Docker, install script, 50 imports from `graphiti_memory`
5. ✅ **Renamed files are not imported:** 0 imports of `data_models`, `backend_interface`, etc.

---

## Unknowns

1. ⏳ Do renamed files execute without error?
2. ⏳ Are there external package consumers?
3. ⏳ Is backward compatibility required?
4. ⏳ What was the intent of the refactor?
5. ⏳ Why were imports not updated?

---

## Hypotheses

**H1: Incomplete Refactor** ★★★☆☆
- **Evidence:** Files renamed, imports unchanged
- **Prediction:** Renamed files fail to import
- **Test:** Execute imports

**H2: Dead Code** ★★☆☆☆
- **Evidence:** 0 imports (renamed), not in production
- **Contradicted by:** README still references them
- **Test:** Check if README usage examples work

**H3: Parallel Implementation** ★☆☆☆☆
- **Evidence:** Two implementations exist
- **Contradicted by:** Renamed files can't execute (broken imports)
- **Test:** Runtime verification

---

## Decisions Required

### Decision 1: Migration Strategy
**Question:** How should the refactor be completed?

**Options:**
- A: Update imports in renamed files
- B: Revert rename, keep milestone files
- C: Delete renamed files if unused

**Evidence Needed:**
- [ ] Runtime execution test
- [ ] External consumer check
- [ ] Maintainer intent clarification

### Decision 2: Compatibility Layer
**Question:** Should we support the old API?

**Depends On:**
- Are there external users?
- Is the package published?
- Is there a backward compatibility policy?

**Status:** Cannot decide without evidence.

### Decision 3: Archival vs Deletion
**Question:** Should files be archived or deleted?

**Criteria for Archival:**
- Potential future reference
- Historical value
- Gradual transition

**Criteria for Deletion:**
- Proven unused
- No external dependencies
- Confirmed dead code

**Status:** Cannot decide until migration strategy is chosen.

---

## Next Verifications (Priority Order)

### P0: Runtime Execution Test
```bash
# Test if milestone imports work
python3 -c "from milestone1_models import Memory"

# Test if renamed files work
python3 -c "import src.data_models"

# Test if canonical works
python3 -c "from graphiti_memory.models import MemoryBase"
```

**Purpose:** Confirm hypothesis that renamed files are broken.

---

### P1: Package Publishing Check
```bash
# Check if package is published
grep -r "version" pyproject.toml
cat pyproject.toml | grep -A 10 "classifiers"

# Check for distribution
ls -la dist/ 2>/dev/null || echo "No dist directory"

# Check PyPI (if package is public)
# Would require: pip search openhands-graphiti-memory
```

**Purpose:** Determine if external users exist.

---

### P2: README Example Test
```bash
# Test README usage example
python3 << 'EOF'
from src.knowledge_admission_mvp import (
    GraphitiAdapter,
    KnowledgeAdmissionPipeline,
    ExecutionRecorder
)
EOF
```

**Purpose:** Verify if documentation examples work.

---

### P3: Maintainer Intent Investigation
```bash
# Check commit message details
git log --all --grep="refactor" --format="%H %s%n%b" -n 5

# Check for TODOs/FIXMEs in renamed files
grep -r "TODO\|FIXME" src/*.py

# Check governance docs for architecture decisions
find .github/governance -name "*.md" -exec grep -l "milestone\|refactor" {} \;
```

**Purpose:** Understand why refactor was incomplete.

---

## Summary

**Question Answered:** "What is the role of these files?"

**Answer:** These files are the **result of an incomplete refactor**. They were renamed from `milestone*.py` to descriptive names, but import statements were never updated, leaving them with broken dependencies.

**Role:** Dead code resulting from incomplete migration.

**Confidence:** ★★★☆☆ (Direct observation of rename + missing import updates)

---

## Recommended Actions

**Immediate:**
1. ✅ Runtime execution test (verify broken imports)
2. ✅ Check package publishing status
3. ✅ Test README examples
4. ✅ Contact maintainer for intent clarification

**After Evidence:**
5. Choose migration strategy (A, B, or C)
6. Execute migration
7. Validate
8. Archive or delete

**NOT Recommended Yet:**
- ❌ Archival (runtime not verified)
- ❌ Deletion (external usage unknown)
- ❌ Compatibility layer (backward compat unknown)
