# Milestone Migration Plan (Revised - AST-Based)

**Date:** 2026-07-18  
**Methodology:** AST-based dependency analysis  
**Status:** Blocked - Migration path required

---

## Executive Summary

**Finding:** Repository contains two parallel implementations with **dependency entanglement**. Milestone files cannot be archived without migration.

**Evidence:**
- AST analysis shows 33 static imports of `milestone1_models`
- 10 milestone files import from non-existent `milestone*` modules  
- Only 4 milestone files have no static imports
- `graphiti_memory/` is confirmed canonical (Docker, installation script, package structure)

---

## Phase 0: Canonical Implementation ✅ VERIFIED

**Evidence:**
1. Docker entry point: `CMD ["uv", "run", "python", "-m", "graphiti_memory.mcp.server"]`
2. Installation verification imports `graphiti_memory.*` modules
3. Package structure: `src/graphiti_memory/` with proper `__init__.py` throughout
4. No entry points exported for milestone modules (checked `pyproject.toml`)

**Confirmed Production API:**
```python
from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.models import ArchitectureMemory, MemoryType
from graphiti_memory.service.memory_service import MemoryService
from graphiti_memory.service.memory_scorer import MemoryScorer
from graphiti_memory.mcp.server import GraphitiMemoryMCPServer
from graphiti_memory.pipeline import MemoryPipeline
from graphiti_memory.integration.context_builder import ContextBuilder
```

---

## Phase 1: Dependency Analysis (AST-Based) ✅ COMPLETED

### Key Discovery: Dependency Chain

**Milestone modules are NOT defined anywhere in the repository:**
- `milestone1_models` - ❌ Not found
- `milestone2_backend` - ❌ Not found  
- `milestone3_builder` - ❌ Not found
- `milestone4_classifier` - ❌ Not found
- `milestone5_provider` - ❌ Not found
- `milestone6_graphiti` - ❌ Not found
- `milestone8_real_graphiti` - ❌ Not found

**But 10 files import them:**

```
milestone1_models → 33 imports across 10 files
milestone2_backend → 4 imports across 3 files
milestone3_builder → 3 imports across 3 files
milestone4_classifier → 2 imports across 2 files
milestone5_provider → 2 imports across 2 files
milestone6_graphiti → 1 import
milestone8_real_graphiti → 4 imports across 4 files
```

### Existing Equivalents in graphiti_memory:

| Milestone Module | Equivalent in `graphiti_memory/` |
|------------------|-----------------------------------|
| `milestone1_models.Memory` | `graphiti_memory.models.MemoryBase` variants |
| `milestone1_models.MemoryCategory` | `graphiti_memory.models.MemoryType` |
| `milestone1_models.RetrievalContext` | Not found - needs creation |
| `milestone1_models.MemoryConfig` | `graphiti_memory.config.settings.GraphitiConfig` |
| `milestone3_builder.ContextBuilder` | `graphiti_memory.integration.context_builder.ContextBuilder` |
| `milestone2_backend.MemoryBackend` | Not found - needs creation or is internal |

### Files Blocked by Missing Dependencies:

| File | Missing Imports | Can Archive? |
|------|-----------------|--------------|
| `backend_interface.py` | `milestone1_models.Memory/MemoryCategory/RetrievalContext` | ❌ NO |
| `feedback_processor.py` | `milestone1_models`, `milestone8_real_graphiti` | ❌ NO |
| `graphiti_adapter.py` | `milestone1_models`, `milestone2_backend` | ❌ NO |
| `graphiti_client.py` | `milestone1_models.Memory/MemoryCategory/RetrievalContext` | ❌ NO |
| `graphiti_provider.py` | `milestone1_models`, `milestone2_backend`, `milestone3_builder`, `milestone4_classifier` | ❌ NO |
| `memory_loader.py` | `milestone1/3/4/5/8` (5 dependencies!) | ❌ NO |
| `metrics_collector.py` | `milestone1/2/3/4/5/6` (6 dependencies!) | ❌ NO |
| `persistence_layer.py` | `milestone1_models`, `milestone8_real_graphiti` | ❌ NO |
| `pipeline_builder.py` | `milestone1_models.Memory/MemoryConfig/MemoryCategory` | ❌ NO |
| `result_ranker.py` | `milestone1_models`, `milestone8_real_graphiti` | ❌ NO |

### Files with No Static Imports:

| File | Import Count | Status |
|------|--------------|--------|
| `src/admission_classifier.py` | 0 | ✅ Candidate for archive |
| `src/data_models.py` | 0 | ✅ Candidate for archive |
| `src/performance_metrics.py` | 0 | ✅ Candidate for archive |

**⚠️ NOTE:** "No static imports" ≠ "Safe to archive"

Still need to verify:
1. Dynamic imports (importlib, __import__)
2. Entry points
3. Plugin loading
4. Documentation references
5. Example usage
6. Test coverage

---

## Phase 2: Classification (Not Archive)

**Status Classification:**

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| **CANDIDATE** | No static imports found | Verify dynamic/runtime references |
| **BLOCKED** | Imports missing modules | Must fix imports before migration |
| **DOCUMENTED** | Referenced in README/docs | Update documentation |
| **TEST_DEPENDENCY** | Imported by tests | Migrate tests first |

---

## Phase 3: Migration Path

### Step 3.1: Create Compatibility Layer (Optional)

**Purpose:** Allow gradual migration with deprecation warnings

**Approach:**
```python
# src/milestone1_models.py (temporary compatibility layer)
import warnings
from graphiti_memory.models import MemoryBase as Memory
from graphiti_memory.models import MemoryType as MemoryCategory

warnings.warn(
    "milestone1_models is deprecated. Use graphiti_memory.models instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export with same API
__all__ = ['Memory', 'MemoryCategory', 'RetrievalContext', 'MemoryConfig']
```

**Benefit:** Existing code continues working while migration happens.

### Step 3.2: Fix Imports File-by-File

**Priority Order:**
1. Files with fewest dependencies first
2. Test files (to verify migration)
3. Example files  
4. Documentation

**Example Migration:**

```python
# BEFORE (src/backend_interface.py)
from milestone1_models import Memory, MemoryCategory, RetrievalContext

# AFTER
from graphiti_memory.models import MemoryBase as Memory, MemoryType as MemoryCategory
from graphiti_memory.models import RetrievalContext  # May need to create this
```

### Step 3.3: Test Each Migration

After each file:
```bash
# Verify syntax
python3 -m py_compile src/filename.py

# Run tests (if any)
pytest tests/ -v

# Verify import
python3 -c "from src.filename import ClassName" 
```

---

## Phase 4: Documentation Migration

**Files to Update:**
- [ ] README.md - Update all import examples
- [ ] examples/ - Update example scripts
- [ ] docs/ - Update any tutorials

**README.md Current State:**
```python
from src.knowledge_admission_mvp import (
    GraphitiAdapter,
    KnowledgeAdmissionPipeline,
    ExecutionRecorder
)
```

**Should Be:**
```python
from graphiti_memory.mcp.server import GraphitiMemoryMCPServer
from graphiti_memory.pipeline import MemoryPipeline
from graphiti_memory.service.memory_service import MemoryService
```

---

## Phase 5: Test Migration

**Current Test Dependency:**
- `tests/test_knowledge_admission.py` imports from `knowledge_admission_mvp`

**Decision Required:**
- [ ] Migrate test to use `graphiti_memory`
- [ ] Archive test (if it's for legacy code)
- [ ] Rewrite test for canonical implementation

---

## Phase 6: Validation Gates

**Before declaring any file "safe to archive":**

- [ ] AST analysis: 0 static imports ✅
- [ ] Dynamic import check: No `importlib`, `__import__`, `exec` usage
- [ ] Entry point check: Not in `pyproject.toml` console_scripts
- [ ] Docker check: Not in Dockerfile COPY or CMD
- [ ] Documentation check: Not in README or docs
- [ ] Example check: Not in examples/
- [ ] Test check: Not imported by tests
- [ ] Execution test: File can be imported without error
- [ ] Integration test: Full system still works

**Verification Commands:**
```bash
# 1. AST analysis
python3 /tmp/build_dependency_graph.py

# 2. Dynamic import check
grep -r "importlib\|__import__\|exec(" --include="*.py" src/${FILE}

# 3. Entry point check
cat pyproject.toml | grep -A 5 "entry_points"

# 4. Docker check
cat Dockerfile | grep "${FILE}"

# 5. Documentation check  
grep -r "${FILE}" README.md docs/ examples/

# 6. Import test
python3 -c "import ${FILE}"

# 7. Full system test
bash scripts/verify_installation.sh
```

---

## Phase 7: Archive (Not Delete)

**Archive Structure:**
```
archive/
├── milestone-prototypes/
│   ├── README.md                    # Historical context
│   ├── MIGRATION_LOG.md             # When/why migrated
│   ├── admission_classifier.py
│   ├── data_models.py
│   ├── performance_metrics.py
│   └── [... other migrated files]
```

**Process:**
1. Move to `archive/milestone-prototypes/`
2. Run full validation suite
3. Keep for one release cycle
4. Delete only after production validation

---

## Unknowns Requiring Verification

**U1: Dynamic imports**
- [ ] Check for `importlib.import_module()` calls
- [ ] Check for `__import__()` calls
- [ ] Check for plugin loading patterns
- [ ] Check for runtime module discovery

**U2: RetrievalContext location**
- Current: Imported from `milestone1_models`
- Canonical: Not found in `graphiti_memory`
- Action: May need to create or find equivalent

**U3: MemoryBackend location**
- Current: Imported from `milestone2_backend`
- Canonical: Not found in `graphiti_memory`
- Action: May be internal or need creation

**U4: IntentClassifier location**
- Current: Imported from `milestone4_classifier`
- Canonical: Not found in `graphiti_memory`
- Action: Check if still needed

**U5: Example dependencies**
- `examples/integrate_memory.py` uses `sys.path` hack
- Imports `milestone1_models` and `milestone8_real_graphiti`
- Action: Determine if example is current or legacy

---

## Revised Timeline

**Phase 0:** ✅ Canonical implementation identified  
**Phase 1:** ✅ AST dependency analysis complete  
**Phase 2:** ⏸️ Status classification (in progress)  
**Phase 3:** ⏸️ Compatibility layer (pending decision)  
**Phase 4:** ⏸️ Migration execution  
**Phase 5:** ⏸️ Documentation updates  
**Phase 6:** ⏸️ Validation  
**Phase 7:** ⏸️ Archival  

---

## Next Steps

1. **Decision needed:** Create compatibility layer OR break imports immediately?
2. **Decision needed:** Migrate tests OR archive tests?
3. **Investigation needed:** Locate/create missing canonical classes
4. **Verification needed:** Check for dynamic imports
5. **Execution:** Begin file-by-file migration

---

## References

- AST Analysis: `.github/dependency-graph.json`
- Installation Script: `scripts/verify_installation.sh`
- Canonical Package: `src/graphiti_memory/`
- Docker Configuration: `Dockerfile`
