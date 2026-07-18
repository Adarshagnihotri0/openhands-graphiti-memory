# Milestone Migration Plan

**Date:** 2026-07-18  
**Canoncial Implementation:** `src/graphiti_memory/`  
**Evidence Source:** `scripts/verify_installation.sh`, `Dockerfile`

---

## Executive Summary

**Repository has two parallel implementations:**
1. **Production (Canonical):** `src/graphiti_memory/` - 50 imports, Docker entry point, installation verification
2. **Legacy (Milestone):** 14 files in `src/` root - 0 imports, limited test coverage, outdated documentation

**Recommendation:** Migrate to single canonical implementation via phased approach.

---

## Phase 0: Canonical Implementation ✅ VERIFIED

**Evidence:**
- Docker entry point: `python -m graphiti_memory.mcp.server`
- Installation verification imports from `graphiti_memory.*`
- 50 import occurrences across repository
- Comprehensive package structure in `src/graphiti_memory/`

**API Surface:**
```python
from graphiti_memory.config.settings import GraphitiConfig
from graphiti_memory.models import ArchitectureMemory, MemoryType
from graphiti_memory.service.memory_scorer import MemoryScorer
from graphiti_memory.service.memory_service import MemoryService
from graphiti_memory.mcp.server import GraphitiMemoryMCPServer
from graphiti_memory.pipeline import MemoryPipeline
```

---

## Phase 1: Dependency Audit ✅ COMPLETED

**Audit Results:** See `.github/migration-audit.json`

### Summary:

| Status | Count | Files |
|--------|-------|-------|
| **Safe to Archive** | 7 | feedback_processor, graphiti_client, memory_loader, metrics_collector, performance_metrics, persistence_layer, result_ranker |
| **In README Only** | 6 | backend_interface, data_models, admission_classifier, graphiti_adapter, graphiti_provider, pipeline_builder |
| **In Tests** | 1 | knowledge_admission_mvp |

### Detailed Findings:

#### Files Safe to Archive (No Dependencies):
```
src/feedback_processor.py         - 0 imports, not in docs/tests
src/graphiti_client.py            - 0 imports, in examples only (via sys.path)
src/memory_loader.py              - 0 imports, not in docs/tests
src/metrics_collector.py          - 0 imports, not in docs/tests
src/performance_metrics.py        - 0 imports, not in docs/tests
src/persistence_layer.py          - 0 imports, not in docs/tests
src/result_ranker.py             - 0 imports, not in docs/tests
```

#### Files in Documentation (README.md):
```
src/backend_interface.py          - Referenced in README
src/data_models.py               - Referenced in README
src/admission_classifier.py      - Referenced in README
src/graphiti_adapter.py          - Referenced in README
src/graphiti_provider.py         - Referenced in README
src/pipeline_builder.py          - Referenced in README
src/knowledge_admission_mvp.py   - Referenced in README + Test dependency
```

#### Active Test Dependencies:
```
tests/test_knowledge_admission.py → imports from knowledge_admission_mvp
```

---

## Phase 2: Migration Steps

### Step 2.1: Update Test Dependencies
**Blocker:** `tests/test_knowledge_admission.py` imports from `knowledge_admission_mvp`

**Action:**
- [ ] Determine if test should be migrated to graphiti_memory test suite
- [ ] Or: Determine if test is legacy and should be archived
- [ ] Execute migration or archival

**Verification:**
```bash
pytest tests/test_knowledge_admission.py -v
```

### Step 2.2: Update README Examples
**Issue:** README.md shows outdated import paths

**Current (Wrong):**
```python
from src.knowledge_admission_mvp import GraphitiAdapter
```

**Should Be:**
```python
from graphiti_memory.mcp.server import GraphitiMemoryMCPServer
from graphiti_memory.service.memory_service import MemoryService
```

**Action:**
- [ ] Update README.md usage examples
- [ ] Update README.md architecture diagram
- [ ] Update README.md installation steps

### Step 2.3: Archive Unused Files
**Action:**
```bash
# Create archive directory
mkdir -p archive/milestone-prototypes

# Move safe-to-archive files
mv src/feedback_processor.py archive/milestone-prototypes/
mv src/memory_loader.py archive/milestone-prototypes/
mv src/metrics_collector.py archive/milestone-prototypes/
mv src/performance_metrics.py archive/milestone-prototypes/
mv src/persistence_layer.py archive/milestone-prototypes/
mv src/result_ranker.py archive/milestone-prototypes/
```

### Step 2.4: Handle Documented Files
**Files referenced in README but not imported:**

**Options:**
1. If functionality exists in graphiti_memory → Remove from README
2. If functionality needed → Migrate to graphiti_memory or document as future work

**Action:**
- [ ] Verify each module's functionality
- [ ] Check if equivalent exists in `graphiti_memory`
- [ ] Update or archive accordingly

### Step 2.5: Fix Example Scripts
**Issue:** `examples/integrate_memory.py` uses `sys.path` manipulation

**Current:**
```python
sys.path.insert(0, str(Path(__file__).parent))
from milestone8_real_graphiti import RealGraphitiBackend
```

**Should Be:**
```python
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from graphiti_memory.client.graphiti_client import GraphitiClient
```

**Action:**
- [ ] Update examples to use graphiti_memory package
- [ ] Remove sys.path hacks
- [ ] Verify examples run correctly

---

## Phase 3: Verification Checklist

Before archiving any file, verify:

- [ ] `grep -r "module_name" --include="*.py"` returns 0 results
- [ ] `grep -r "module_name" README.md` returns 0 results  
- [ ] `grep -r "module_name" examples/` returns 0 results
- [ ] `grep -r "module_name" tests/` returns 0 results
- [ ] pytest passes
- [ ] ruff passes
- [ ] mypy passes
- [ ] Docker build succeeds
- [ ] Installation verification script passes

---

## Phase 4: Cleanup

**After all migrations verified:**

- [ ] Create git branch: `feat/migrate-to-canonical-implementation`
- [ ] Move milestone files to `archive/milestone-prototypes/`
- [ ] Update all documentation
- [ ] Update CI/CD if needed
- [ ] Run full test suite
- [ ] Create PR with migration summary
- [ ] After merge + release, consider removing archive/

---

## Archive Structure

```
archive/
├── milestone-prototypes/
│   ├── README.md                    # Explain historical context
│   ├── backend_interface.py
│   ├── data_models.py
│   ├── ... (other milestone files)
│   └── knowledge_admission_mvp.py
└── MIGRATION_LOG.md                 # Detailed migration history
```

---

## Risk Mitigation

**Before Archival:**
1. ✅ Audit completed (`.github/migration-audit.json`)
2. ⚠️ Test migration required
3. ⚠️ Documentation update required
4. ⚠️ Example update required

**Rollback Plan:**
- Keep files in `archive/` (not deleted) for first release
- Can be restored immediately if needed
- Delete only after production validation

---

## Timeline

- [ ] Phase 1 (Audit): ✅ Completed
- [ ] Phase 2 (Migration): Pending approval
- [ ] Phase 3 (Verification): After migration
- [ ] Phase 4 (Cleanup): After verification passes

---

## Decision Required

**Question for maintainers:**

What should happen to `tests/test_knowledge_admission.py`?

- Option A: Migrate to `src/graphiti_memory/tests/` and update imports
- Option B: Archive with milestone files (if test is legacy)
- Option C: Rewrite to test graphiti_memory functionality

**Recommendation:** Option A - Migrate and verify test still provides value.

---

## References

- Audit Data: `.github/migration-audit.json`
- Canonical Implementation: `src/graphiti_memory/`
- Installation Script: `scripts/verify_installation.sh`
- Docker Entry: `Dockerfile`
