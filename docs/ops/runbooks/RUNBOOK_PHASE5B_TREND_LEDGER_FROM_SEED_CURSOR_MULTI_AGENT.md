# RUNBOOK — Peak_Trade Phase 5B (Cursor Multi-Agent Chat)

**Title:** Trend Seed → Trend Ledger (Canonical JSON + Determinism Tests) — Minimal

**Version:** 1.0.0  
**Date:** 2026-01-12  
**Phase:** 5B  
**Scope:** AIOps / Trend Analysis  
**Delivery Model:** Cursor Multi-Agent Chat

---

## 0) PURPOSE

Erzeuge ein deterministisches, kanonisches **Trend Ledger** (JSON) aus einem **Trend Seed** (Phase 5A output).

**Minimal Scope:**
- ✅ Library (consumer logic)
- ✅ CLI (generator script)
- ✅ Tests (unit + determinism)
- ✅ Fixture (golden reference)
- ✅ Documentation (runbook + index)
- ❌ CI Workflow (deferred to Phase 5C or Full)

**Primary Outcome:**  
Ein "Trend Ledger" wird lokal/manuell reproduzierbar erzeugt, maschinenlesbar, deterministisch, governance-freundlich.

---

## 1) INPUTS / CONTEXT

**Prerequisites:**
- Phase 5A is on `main`:
  - `src/ai_orchestration/trends/trend_seed_consumer.py`
  - `scripts/aiops/generate_trend_seed_from_normalized_report.py`
  - `tests/fixtures/validator_report.normalized.sample.json`
  - Runbook: `RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md`

**Trend Seed Schema (v0.1.0):**
```json
{
  "schema_version": "0.1.0",
  "generated_at": "ISO-8601",
  "source": {
    "repo": "owner/repo",
    "workflow_name": "...",
    "run_id": "...",
    "head_sha": "...",
    "ref": "refs/heads/main"
  },
  "normalized_report": {
    "conclusion": "pass|fail|error",
    "determinism": {"hash": "...", "is_deterministic": true},
    "counts": {"checks_total": N, "checks_passed": N, ...}
  }
}
```

---

## 2) GUARDRAILS (NON-NEGOTIABLE)

- ✅ **Additive only, low risk:** No trading-core / execution code touched
- ✅ **Determinism-first:** Canonical JSON bytes, stable sorting, explicit `schema_version`
- ✅ **No timestamps in hash:** Timestamps optional, excluded from determinism hash
- ✅ **Tests mandatory:** Golden fixture + determinism test (repeated runs → identical bytes)
- ✅ **Fail-closed validation:** Schema mismatch → hard fail
- ✅ **CI artifacts small + clearly named** (when CI workflow added in future)

---

## 3) DEFINITION OF DONE (ACCEPTANCE CRITERIA)

### A) CI/Quality Gates
- ✅ Lint Gate (Always Run): PASS
- ✅ Audit: PASS
- ✅ Policy Guards / L4 Critic: PASS
- ✅ CI/tests: PASS (3.9/3.10/3.11)

### B) Functionality
- ✅ CLI can generate `trend_ledger.json` from `trend_seed.json` (canonical)
- ✅ CLI can optionally generate `trend_ledger.md` (summary)
- ✅ Library API is importable and testable

### C) Determinism
- ✅ Repeated-run determinism test: identical JSON bytes for identical input
- ✅ SHA-256 hash stable across runs
- ✅ Canonical rules documented (runbook + docstring)

---

## 4) MULTI-AGENT ROLE MODEL

**Roles (6-agent pattern):**

1. **ORCHESTRATOR**  
   - Drives conversation order
   - Ensures deliverables produced
   - Produces final PR body + checklist

2. **FACTS_COLLECTOR**  
   - Inspects Phase 5A outputs/APIs
   - Documents seed schema
   - Identifies existing patterns (naming, artifacts, docs)

3. **SCOPE_KEEPER**  
   - Locks scope (NO CI workflow in minimal)
   - Prevents scope creep
   - Guards guardrails

4. **IMPLEMENTER**  
   - Implements Python library + CLI
   - Ensures canonical JSON + determinism

5. **TEST_ENGINEER**  
   - Creates golden fixture
   - Writes unit tests + determinism tests

6. **DOCS_SCRIBE**  
   - Creates operator runbook
   - Updates README index

7. **RISK_OFFICER**  
   - Risk assessment
   - Determinism contract notes
   - PR risk section

---

## 5) TASK BREAKDOWN (WHAT EACH AGENT MUST PRODUCE)

### 5.1 FACTS_COLLECTOR

**Task:**  
Produce **FACTS PACK** with:
- Phase 5A artifact naming conventions
- Current trend_seed schema (fields, ordering assumptions)
- Existing JSON canonicalization helpers (if any) in repo

**Deliverable:**  
"FACTS PACK" (bullets) + recommended naming + compatibility constraints.

---

### 5.2 SCOPE_KEEPER

**Task:**  
Lock scope to Phase 5B minimal only:

**IN SCOPE:**
- ✅ Ledger schema v1.0.0
- ✅ Library: `src/ai_orchestration/trends/trend_ledger.py`
- ✅ CLI: `scripts/aiops/generate_trend_ledger_from_seed.py`
- ✅ Tests + fixture
- ✅ Docs updates

**OUT OF SCOPE (deferred):**
- ❌ CI workflow (Phase 5C or Full)
- ❌ Multi-seed aggregation (time-series)
- ❌ Persistent storage backend
- ❌ Dashboard/visualization
- ❌ Cross-run trend analysis

**Deliverable:**  
"SCOPE LOCK" statement + explicit out-of-scope list.

---

### 5.3 IMPLEMENTER (Python)

**Task:**  
Implement these files:

#### A) `src/ai_orchestration/trends/trend_ledger.py`

**Data Model:**
```python
@dataclass
class TrendLedgerSnapshot:
    schema_version: str         # "1.0.0"
    generated_at: str           # ISO-8601 (from seed)
    source_run: Dict[str, Any]  # {repo, workflow_name, run_id, head_sha, ref}
    items: List[Dict[str, Any]] # Sorted canonically
    counters: Dict[str, Any]    # {checks_total, checks_passed, items_total, ...}
```

**API:**
```python
def load_trend_seed(path: str) -> Dict[str, Any]:
    """Load trend seed from JSON file."""

def ledger_from_seed(seed: Dict[str, Any]) -> TrendLedgerSnapshot:
    """Generate ledger from seed (fail-closed validation)."""

def to_canonical_json(ledger: TrendLedgerSnapshot) -> str:
    """Serialize to canonical JSON (deterministic)."""

def compute_canonical_hash(ledger: TrendLedgerSnapshot) -> str:
    """Compute SHA-256 hash of canonical JSON."""

def render_markdown_summary(ledger: TrendLedgerSnapshot) -> str:
    """Render operator-friendly markdown summary."""
```

**Canonicalization Rules:**
- Stable field ordering: `json.dumps(sort_keys=True, indent=2, ensure_ascii=False)`
- Stable list ordering: items sorted by `(category, key)` tuple
- Exclude volatile metadata from hash (if any)
- Single trailing newline

**Error Model:**
```python
class TrendLedgerError(Exception): ...
class SchemaVersionError(TrendLedgerError): ...
class ValidationError(TrendLedgerError): ...
```

#### B) `scripts/aiops/generate_trend_ledger_from_seed.py`

**CLI Options (minimum):**
```bash
--input <path>              # Required: trend_seed.json
--output-json <path>        # Required: output ledger JSON
--output-markdown <path>    # Optional: output markdown summary
--run-manifest <path>       # Optional: CI metadata JSON
--verbose                   # Optional: verbose output
```

**Exit Codes:**
- 0: Success
- 1: Error (schema mismatch, validation failure, IO error)
- 2: Usage error (missing required arguments)

**Features:**
- Help text (`--help`)
- Operator-friendly output (progress indicators)
- Error messages with context

**Deliverable:**  
Complete, tested, executable code.

---

### 5.4 TEST_ENGINEER

**Task:**  
Add test files:

#### `tests/fixtures/trend_seed.sample.json`

Minimal but representative Phase 5A seed:
```json
{
  "schema_version": "0.1.0",
  "generated_at": "2026-01-11T12:00:00Z",
  "source": {
    "repo": "owner/repo",
    "workflow_name": "L4 Critic Replay Determinism",
    "run_id": "12345",
    "head_sha": "abc123",
    "ref": "refs/heads/main"
  },
  "normalized_report": {
    "conclusion": "pass",
    "counts": {
      "checks_total": 2,
      "checks_passed": 2,
      "checks_failed": 0
    },
    "determinism": {
      "hash": "abc123def456",
      "is_deterministic": true
    }
  }
}
```

#### `tests/ai_orchestration/test_trend_ledger_from_seed.py`

**Test Cases (minimum):**

**Load & Validation:**
- `test_load_valid_seed`
- `test_load_missing_file`
- `test_load_invalid_json`
- `test_fail_on_missing_schema_version`
- `test_fail_on_unsupported_schema_version`
- `test_fail_on_missing_required_fields`

**Ledger Generation:**
- `test_generate_ledger_from_valid_seed`
- `test_ledger_items_structure`
- `test_ledger_counters_structure`

**Canonical JSON:**
- `test_canonical_json_structure`
- `test_canonical_json_determinism` (run twice, compare bytes)
- `test_canonical_json_sorted_keys`
- `test_compute_canonical_hash_determinism`
- `test_different_ledgers_different_hashes`

**Markdown Summary:**
- `test_render_markdown_structure`
- `test_markdown_includes_source_metadata`
- `test_markdown_includes_counters`

**Integration:**
- `test_full_workflow_seed_to_ledger_to_json`
- `test_full_workflow_with_markdown`
- `test_determinism_across_multiple_runs` (3x, compare hashes)

**Deliverable:**  
Complete test suite with golden fixture.

---

### 5.5 DOCS_SCRIBE

**Task:**  
Create documentation files:

#### A) `docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md`

**Sections:**
1. **Purpose:** What is the trend ledger?
2. **Architecture:** Input → Processing → Output
3. **Usage:** CLI examples, exit codes
4. **Testing:** How to run unit tests + determinism tests
5. **Schema:** Ledger schema v1.0.0 structure
6. **Troubleshooting:** Common errors + fixes
7. **Integration:** How it links to Phase 5A
8. **References:** Code paths, related docs

#### B) Update `docs/ops/README.md`

Add Phase 5B section under "Phase 5A" with:
- Link to runbook
- Key deliverables
- Risk statement (LOW)

**Deliverable:**  
Complete runbook + index update.

---

### 5.6 RISK_OFFICER

**Task:**  
Produce **RISK NOTE** covering:

**Risk Assessment:** LOW

**Potential Risks:**
1. Artifact dependency drift (seed schema change)
2. Nondeterminism via metadata
3. Missing determinism contract enforcement

**Mitigations:**
1. Fail-closed schema validation + explicit version checks
2. Timestamps excluded from hash, only in metadata
3. Tests enforce determinism (compare hashes across runs)

**Impact:**  
Tooling/CI artifacts only, no trading core touched.

**Deliverable:**  
Risk note + PR risk section.

---

## 6) DESIGN SPEC — LEDGER SCHEMA v1.0.0

### TrendLedgerSnapshot Structure

```python
{
  "schema_version": "1.0.0",
  "generated_at": "2026-01-11T12:00:00Z",  # From seed (not in hash)
  "source_run": {
    "repo": "owner/repo",
    "workflow_name": "L4 Critic Replay Determinism",
    "run_id": "12345",
    "run_attempt": 1,
    "head_sha": "abc123",
    "ref": "refs/heads/main"
  },
  "items": [
    {
      "category": "validator_report",
      "key": "overall_status",
      "conclusion": "pass",
      "determinism_hash": "abc123",
      "is_deterministic": true,
      "report_id": "..."
    }
  ],
  "counters": {
    "items_total": 1,
    "checks_total": 2,
    "checks_passed": 2,
    "checks_failed": 0,
    "policy_findings_total": 0
  }
}
```

### Canonical Ordering Rules

**Items Sorting:**
- Primary: `category` (ascending)
- Secondary: `key` (ascending)
- Tertiary: `severity` (if present)

**JSON Serialization:**
```python
json.dumps(
    ledger.to_dict(),
    indent=2,
    sort_keys=True,
    ensure_ascii=False
) + "\n"
```

**Hash Calculation:**
```python
canonical_json = to_canonical_json(ledger)
sha256(canonical_json.encode("utf-8")).hexdigest()
```

---

## 7) IMPLEMENTATION PLAN (ORDER OF OPERATIONS)

**ORCHESTRATOR must drive the conversation in this strict order:**

1. **FACTS_COLLECTOR** → Produce FACTS PACK (seed schema + patterns)
2. **SCOPE_KEEPER** → Produce SCOPE LOCK (no CI workflow)
3. **RISK_OFFICER** → Produce RISK NOTE (based on schema proposal)
4. **IMPLEMENTER** → Write library + CLI (complete code)
5. **TEST_ENGINEER** → Add fixtures + tests
6. **DOCS_SCRIBE** → Add runbook + README update
7. **ORCHESTRATOR** → Produce PR body + final checklist

**No parallel execution.** Each agent waits for previous agent's output.

---

## 8) PR BODY TEMPLATE (ORCHESTRATOR OUTPUT)

**Title:**  
```
feat(aiops): Phase 5B trend ledger consumer from seed
```

**Body (compact format):**

```markdown
## Summary
Implements Phase 5B consumer that converts Phase 5A Trend Seeds into canonical Trend Ledger snapshots with deterministic JSON and markdown summaries.

## Why
Establishes a stable, canonical ledger primitive from trend seeds, enabling future trend aggregation (Phase 5C+) with fail-closed validation and deterministic output.

## Changes
- Consumer library: `src/ai_orchestration/trends/trend_ledger.py`
- CLI: `scripts/aiops/generate_trend_ledger_from_seed.py`
- Tests: `tests/ai_orchestration/test_trend_ledger_from_seed.py` (21 tests)
- Fixture: `tests/fixtures/trend_seed.sample.json`
- Runbook: `docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md`
- Index: `docs/ops/README.md` updated

## Verification
- Pre-commit hooks: all passed
- Test suite: 21/21 passed
- Determinism: verified byte-identical output
  - SHA-256: `<hash>`
  - Repeated runs: identical hashes

## Risk
LOW — tooling/CI artifacts only; no trading/live execution code touched.

## Operator How-To
```bash
# Generate ledger from seed
python scripts/aiops/generate_trend_ledger_from_seed.py \
  --input trend_seed.json \
  --output-json trend_ledger.json \
  --output-markdown trend_ledger.md
```

## References
- Runbook: `docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md`
- Phase 5A: `docs/ops/runbooks/RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md`
```

---

## 9) FINAL CHECKLIST (MUST BE EXPLICITLY CHECKED)

**Before submitting PR:**

- [ ] New files compiled/importable
- [ ] Tests cover determinism (repeated runs → identical bytes)
- [ ] Fixture is minimal but representative
- [ ] Docs runbook added
- [ ] README index updated
- [ ] No trading-core files touched
- [ ] Ruff/format compliance (pre-commit hooks passed)
- [ ] PR body includes all sections (Summary/Why/Changes/Verification/Risk/How-To/References)

---

## 10) DELIVERABLES — REQUIRED FINAL OUTPUT

The assistant must output:

### A) Full Code (Copy-Paste Ready)
- ✅ `src/ai_orchestration/trends/trend_ledger.py` (complete)
- ✅ `scripts/aiops/generate_trend_ledger_from_seed.py` (executable)

### B) Fixture Contents (JSON)
- ✅ `tests/fixtures/trend_seed.sample.json` (explicit content)

### C) Test Suite
- ✅ `tests/ai_orchestration/test_trend_ledger_from_seed.py` (complete)

### D) Documentation
- ✅ `docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md`
- ✅ `docs/ops/README.md` (update section)

### E) PR Components
- ✅ PR title
- ✅ PR description (all sections)

### F) Risk & Mitigation Note
- ✅ Risk assessment
- ✅ Mitigation strategies

---

## 11) EXECUTION PROTOCOL

### Start Sequence

```
ORCHESTRATOR: "BEGIN PHASE 5B MINIMAL EXECUTION"
↓
FACTS_COLLECTOR: "Produce FACTS PACK"
↓
SCOPE_KEEPER: "Produce SCOPE LOCK"
↓
RISK_OFFICER: "Produce RISK NOTE"
↓
IMPLEMENTER: "Implement library + CLI"
↓
TEST_ENGINEER: "Add fixtures + tests"
↓
DOCS_SCRIBE: "Add runbook + README"
↓
ORCHESTRATOR: "Produce PR body + checklist"
↓
END
```

### Approval Gates

Each agent must receive **explicit approval** from ORCHESTRATOR before next agent proceeds.

**Example:**
```
ORCHESTRATOR: "FACTS_COLLECTOR, produce FACTS PACK now."
FACTS_COLLECTOR: [produces output]
ORCHESTRATOR: "✅ FACTS PACK approved. SCOPE_KEEPER, produce SCOPE LOCK now."
```

---

## 12) SUCCESS CRITERIA

**Phase 5B is COMPLETE when:**

1. ✅ PR created with all deliverables
2. ✅ All CI gates green (Lint/Audit/Policy/Tests)
3. ✅ Determinism verified (SHA-256 stable across runs)
4. ✅ Documentation complete (runbook + index)
5. ✅ Risk assessment LOW confirmed
6. ✅ No trading-core files touched

---

## 13) REFERENCES

**Related Runbooks:**
- Phase 5A: `RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md`
- Phase 4E: (see ops index)

**Code:**
- Library: `src/ai_orchestration/trends/trend_ledger.py`
- CLI: `scripts/aiops/generate_trend_ledger_from_seed.py`
- Tests: `tests/ai_orchestration/test_trend_ledger_from_seed.py`

**Docs:**
- Operator runbook: `RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md`
- Ops index: `docs/ops/README.md`

---

## 14) CHANGE LOG

| Version | Date       | Author       | Changes                              |
|---------|------------|--------------|--------------------------------------|
| 1.0.0   | 2026-01-12 | AI Ops Team  | Initial Phase 5B minimal runbook     |

---

**Questions?** See operator runbook (`RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md`) or Phase 5A multi-agent runbook for context.
