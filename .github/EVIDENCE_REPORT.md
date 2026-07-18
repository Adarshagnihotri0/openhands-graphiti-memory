# Repository Evidence Report

**Date:** 2026-07-18  
**Methodology:** Reachability Audit (Phases 1-4)  
**Purpose:** Report facts about repository structure and reachability

---

## Phase 1: Structure Graph (Facts)

### Observation: Python Files
- **Count:** 44 Python files
- **Packages:** 12 Python packages (directories with `__init__.py`)

### Observation: Directory Structure
```
src/
├── graphiti_memory/          # Package with 8 subdirectories
│   ├── client/
│   ├── config/
│   ├── integration/
│   ├── mcp/
│   ├── service/
│   ├── tests/
│   └── utils/
├── knowledge_admission_mvp.py
├── data_models.py
├── backend_interface.py
├── graphiti_adapter.py
├── graphiti_client.py
├── graphiti_provider.py
├── memory_loader.py
├── metrics_collector.py
├── performance_metrics.py
├── persistence_layer.py
├── pipeline_builder.py
├── admission_classifier.py
├── result_ranker.py
└── feedback_processor.py

examples/
├── integrate_memory.py
├── quickstart.py
└── __init__.py

tests/
├── test_knowledge_admission.py
├── test_milestone0.py
└── __init__.py
```

**Observation:** Two tree structures exist:
1. `src/graphiti_memory/` - Package structure
2. `src/*.py` - 14 individual files at root level

---

## Phase 2: Dependency Graph (Facts)

### Observation: Import Statements (AST-Analyzed)

**Static imports of `milestone*` modules:**
- `milestone1_models`: 33 occurrences across 10 files
- `milestone2_backend`: 4 occurrences across 3 files  
- `milestone3_builder`: 3 occurrences across 3 files
- `milestone4_classifier`: 2 occurrences across 2 files
- `milestone5_provider`: 2 occurrences across 2 files
- `milestone6_graphiti`: 1 occurrence
- `milestone8_real_graphiti`: 4 occurrences across 4 files

**Static imports of `graphiti_memory`:**
- 50 occurrences across repository

**Files importing from `milestone*`:**
```
src/backend_interface.py         → milestone1_models
src/data_models.py               → (no imports)
src/admission_classifier.py      → (no imports)
src/feedback_processor.py        → milestone1_models, milestone8_real_graphiti
src/graphiti_adapter.py          → milestone1_models, milestone2_backend
src/graphiti_client.py           → milestone1_models
src/graphiti_provider.py         → milestone1_models, milestone2_backend, milestone3_builder, milestone4_classifier
src/memory_loader.py             → milestone1_models, milestone3_builder, milestone4_classifier, milestone5_provider, milestone8_real_graphiti
src/metrics_collector.py         → milestone1_models, milestone2_backend, milestone3_builder, milestone4_classifier, milestone5_provider, milestone6_graphiti
src/performance_metrics.py       → (no imports)
src/persistence_layer.py         → milestone1_models, milestone8_real_graphiti
src/pipeline_builder.py          → milestone1_models
src/result_ranker.py             → milestone1_models, milestone8_real_graphiti
src/knowledge_admission_mvp.py   → (no imports)
```

**Observation:** 10 out of 14 files in `src/*.py` import from `milestone*` modules.

### Observation: Module Definitions

**Query:** Do `milestone*.py` files exist?

**Result:**
```bash
$ find . -name "milestone*.py"
[no results]
```

**Observation:** No files matching `milestone*.py` pattern exist in repository.

### Observation: Reverse Dependencies

**Query:** What imports from `src/*.py` (excluding `graphiti_memory/`)?

**Result:**
- `src/backend_interface`: 0 imports
- `src/data_models`: 0 imports
- `src/admission_classifier`: 0 imports
- `src/feedback_processor`: 0 imports
- `src/graphiti_adapter`: 0 imports
- `src/graphiti_client`: 0 imports
- `src/graphiti_provider`: 0 imports
- `src/memory_loader`: 0 imports
- `src/metrics_collector`: 0 imports
- `src/performance_metrics`: 0 imports
- `src/persistence_layer`: 0 imports
- `src/pipeline_builder`: 0 imports
- `src/result_ranker`: 0 imports
- `src/knowledge_admission_mvp`: 0 imports from production code

**Observation:** 1 test file imports from `knowledge_admission_mvp`:
```
tests/test_knowledge_admission.py → knowledge_admission_mvp
```

---

## Phase 3: Execution Graph (Facts)

### Observation: Docker Entrypoint
```
CMD ["uv", "run", "python", "-m", "graphiti_memory.mcp.server"]
```

**Observation:** Docker executes `graphiti_memory.mcp.server` module.

### Observation: Console Scripts
**Query:** Are entry points defined in `pyproject.toml`?

**Result:** No `console_scripts` or `entry_points` found.

### Observation: Test Files
```
tests/test_knowledge_admission.py
tests/test_milestone0.py
src/graphiti_memory/tests/test_automatic_memory.py
src/graphiti_memory/tests/test_memory_system.py
```

**Count:** 4 test files

### Observation: Example Files
```
examples/integrate_memory.py
examples/quickstart.py
examples/__init__.py
```

**Count:** 3 files (including `__init__.py`)

### Observation: MCP Servers
```
src/graphiti_memory/mcp/server.py
```

**Count:** 1 MCP server

### Observation: Scripts
```
scripts/verify_installation.sh
```

**Count:** 1 script

---

## Phase 4: Reachability Graph (Facts)

### Observation: Reachability Status

**Entry points (modules executed directly):**
```
src/graphiti_memory/mcp/server.py  → ENTRY_POINT
```

**Reachable modules (imported by entry points or reachable modules):**
```
src/graphiti_memory/*  → REACHABLE (via import chain from entry point)
```

**Possibly reachable (may be loaded dynamically or via scripts/examples):**
```
examples/integrate_memory.py         → POSSIBLY_REACHABLE
examples/quickstart.py              → POSSIBLY_REACHABLE
tests/test_knowledge_admission.py   → POSSIBLY_REACHABLE
tests/test_milestone0.py            → POSSIBLY_REACHABLE
mocks/fake_memory_provider.py       → POSSIBLY_REACHABLE
```

**Unreachable modules (not reachable via imports):**
```
src/persistence_layer.py            → UNREACHABLE
src/result_ranker.py                → UNREACHABLE
src/graphiti_adapter.py             → UNREACHABLE
src/performance_metrics.py          → UNREACHABLE
src/admission_classifier.py         → UNREACHABLE
src/pipeline_builder.py             → UNREACHABLE
src/memory_loader.py                → UNREACHABLE
src/backend_interface.py            → UNREACHABLE
src/data_models.py                  → UNREACHABLE
src/feedback_processor.py           → UNREACHABLE
src/graphiti_provider.py            → UNREACHABLE
src/graphiti_client.py              → UNREACHABLE
src/knowledge_admission_mvp.py      → UNREACHABLE
```

**Count by reachability:**
- ENTRY_POINT: 1
- REACHABLE: 36 (graphiti_memory package)
- POSSIBLY_REACHABLE: 7
- UNREACHABLE: 13

### Observation: Unreachable Modules Detail

For each unreachable file in `src/`:

| File | Imports From | Imported By | Reachability |
|------|--------------|-------------|--------------|
| `persistence_layer.py` | `milestone1_models`, `milestone8_real_graphiti` | None | UNREACHABLE |
| `result_ranker.py` | `milestone1_models`, `milestone8_real_graphiti` | None | UNREACHABLE |
| `graphiti_adapter.py` | `milestone1_models`, `milestone2_backend` | None | UNREACHABLE |
| `performance_metrics.py` | None | None | UNREACHABLE |
| `admission_classifier.py` | None | None | UNREACHABLE |
| `pipeline_builder.py` | `milestone1_models` | None | UNREACHABLE |
| `memory_loader.py` | `milestone1/3/4/5/8` modules | None | UNREACHABLE |
| `backend_interface.py` | `milestone1_models` | None | UNREACHABLE |
| `data_models.py` | None | None | UNREACHABLE |
| `feedback_processor.py` | `milestone1_models`, `milestone8_real_graphiti` | None | UNREACHABLE |
| `graphiti_provider.py` | `milestone1/2/3/4` modules | None | UNREACHABLE |
| `graphiti_client.py` | `milestone1_models` | None | UNREACHABLE |
| `knowledge_admission_mvp.py` | None | 1 test file | UNREACHABLE |

---

## Git History Evidence (Facts)

### Observation: Commit Timeline
```
2026-07-18 03:13  feat: Complete Knowledge Admission MVP with Graphiti integration
2026-07-18 08:31  refactor: reorganize project structure
```

### Observation: Refactor Commit Details

**Commit:** `7e0e3ab`  
**Message:** "refactor: reorganize project structure"  
**Commit body includes:**
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

**Observation:** Files were renamed via `git mv`.

### Observation: File Changes in Refactor
```
__pycache__/milestone1_models.cpython-313.pyc      | Bin 4009 -> 0 bytes
__pycache__/milestone2_backend.cpython-313.pyc     | Bin 3934 -> 0 bytes
...
src/{milestone1_models.py => data_models.py}       |   0
src/{milestone2_backend.py => backend_interface.py}|   0
```

**Observation:** Files show `0` bytes changed (rename only, no content modification).

### Observation: Import Statement Updates

**Query:** Were import statements updated in subsequent commits?

**Result:** No commits between refactor (`7e0e3ab`) and current HEAD (`9634950`) modifying import statements.

---

## Documentation Evidence (Facts)

### Observation: README.md References

**Query:** Does README.md reference candidate files?

**Result:** Yes. README.md contains:
```python
from src.knowledge_admission_mvp import (
    GraphitiAdapter,
    KnowledgeAdmissionPipeline,
    ExecutionRecorder
)
```

### Observation: Installation Script

**File:** `scripts/verify_installation.sh`  
**Content:** Script verifies imports from `graphiti_memory.*`:
```python
from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.models import ArchitectureMemory, MemoryType
from graphiti_memory.service.memory_scorer import MemoryScorer
from graphiti_memory.service.memory_service import MemoryService
from graphiti_memory.mcp.server import GraphitiMemoryMCPServer
```

**Observation:** Installation verification does not import from `src/*.py` files.

---

## Evidence Summary

### Verified Facts

1. **Structure:** 44 Python files, 12 packages
2. **Reachability:** 13 files are UNREACHABLE (36 are reachable/entry points)
3. **Imports:** 10 files import from non-existent `milestone*` modules
4. **Reverse imports:** 0 production files import `src/*.py` (excluding `graphiti_memory/`)
5. **Docker:** Executes `graphiti_memory.mcp.server`
6. **Tests:** 1 test imports from `knowledge_admission_mvp`
7. **Git history:** Files renamed from `milestone*.py` to descriptive names on 2026-07-18
8. **Git history:** No subsequent commit updating import statements
9. **README:** References `knowledge_admission_mvp`
10. **Installation script:** Imports from `graphiti_memory.*`, not `src/*.py`

### Not Verified (Unknown)

1. Whether renamed files can execute
2. Whether `milestone*` modules exist elsewhere (on PYTHONPATH)
3. Whether examples can execute
4. Whether README example can execute
5. Whether package is published to PyPI
6. Whether external users exist
7. Maintainer intent regarding renamed files
8. Why imports were not updated
9. Whether `knowledge_admission_mvp` is intentionally preserved
10. Whether files are used in unpublished/not-tracked locations

---

## Requires Maintainer Decision

1. **Reachability of candidate files:** Should unreachable files remain in repository?
2. **Import errors:** Should import statements be updated or files removed?
3. **Test dependency:** Should `tests/test_knowledge_admission.py` be migrated or removed?
4. **Documentation:** Should README.md be updated to reference `graphiti_memory`?
5. **Examples:** Should examples be updated or kept as-is?
6. **Package publishing:** Is the package public? Are there external consumers?
7. **Backward compatibility:** Is backward compatibility required for `milestone*` imports?
8. **Historical preservation:** Should files be archived for reference?

---

## STOP

This report provides reachability facts.

The following actions are **not within scope:**
- Recommending archival
- Recommending deletion
- Recommending migration
- Recommending refactoring
- Recommending any architectural changes

All decisions about repository changes require maintainer judgment.
