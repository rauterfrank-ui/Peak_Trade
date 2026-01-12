# RUNBOOK — Peak_Trade Phase 5B FULL (Cursor Multi-Agent Chat)

**Title:** Trend Seed → Trend Ledger (Canonical JSON + MD Summary + CI Artifact Workflow) — Full

**Version:** 2.0.0  
**Date:** 2026-01-12  
**Phase:** 5B  
**Scope:** AIOps / Trend Analysis  
**Delivery Model:** Cursor Multi-Agent Chat

---

## 0) PURPOSE

Erzeuge ein deterministisches **Trend Ledger** aus **Trend Seed** und liefere es als **CI-Artefakt**:
- `trend_ledger.json` (canonical, diff-friendly)
- `trend_ledger.md` (operator summary)
- `manifest.json` (CI metadata)

**Full Scope:**
- ✅ Library (consumer logic)
- ✅ CLI (generator script)
- ✅ Tests (unit + determinism)
- ✅ Fixture (golden reference)
- ✅ Documentation (runbook + index)
- ✅ **CI Workflow** (artifact generation + upload)

**Primary Outcome:**  
Ein "Trend Ledger" wird automatisch als CI-Artefakt erzeugt, maschinenlesbar, deterministisch, governance-freundlich, mit operator-freundlicher Markdown-Summary.

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
Lock scope to Phase 5B FULL:

**IN SCOPE:**
- ✅ Ledger schema v1.0.0
- ✅ Library: `src/ai_orchestration/trends/trend_ledger.py`
- ✅ CLI: `scripts/aiops/generate_trend_ledger_from_seed.py`
- ✅ Tests + fixture
- ✅ Docs updates
- ✅ **CI Workflow:** `.github/workflows/aiops-trend-ledger-from-seed.yml`
- ✅ **CI Artifacts:** `trend-ledger-<run_id>` (JSON + MD + manifest)

**OUT OF SCOPE (deferred to Phase 5C+):**
- ❌ Multi-seed aggregation (time-series)
- ❌ Persistent storage backend
- ❌ Dashboard/visualization
- ❌ Cross-run trend analysis
- ❌ Alert generation from trends

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

### 5.5 CI_GUARDIAN

**Task:**  
Implement CI workflow for automated ledger generation.

#### Workflow Design Decision (Option A - Recommended)

**Choice:** Option A (workflow_run trigger + artifact download)

**Justification:**
- ✅ Clean separation of concerns (Phase 5A → Phase 5B pipeline)
- ✅ Robust artifact dependency (explicit download)
- ✅ Supports manual trigger (workflow_dispatch) for testing
- ✅ Minimal duplication (no re-running Phase 5A logic)

#### `.github/workflows/aiops-trend-ledger-from-seed.yml`

**Triggers:**
- `workflow_run`: Triggered when Phase 5A workflow completes (success only, main branch only)
- `workflow_dispatch`: Manual trigger for testing/debugging

**Key Steps:**
1. Checkout repository
2. Setup Python 3.12 + uv
3. **Download Phase 5A artifact:** `trend-seed-<run_id>`
4. Verify artifact contents (fail-fast if missing)
5. Run CLI: `generate_trend_ledger_from_seed.py`
6. Verify outputs (JSON + MD + manifest)
7. **Upload artifacts:** `trend-ledger-<run_id>`
8. Generate GitHub step summary (preview + status)

**Artifact Naming:**
- **Input:** `trend-seed-<run_id>` (from Phase 5A)
- **Output:** `trend-ledger-<run_id>` (contains: `trend_ledger.json`, `trend_ledger.md`, `manifest.json`)
- **Retention:** 30 days

**Permissions:**
- `contents: read`
- `actions: read`
- (Minimal, read-only)

**Error Handling:**
- Fail-fast on missing artifacts
- Structured output validation
- Clear error messages in GitHub step summary

**Deliverable:**  
Complete, tested CI workflow YAML.

---

### 5.6 DOCS_SCRIBE

**Task:**  
Create documentation files:

#### A) `docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md`

**Sections:**
1. **Purpose:** What is the trend ledger?
2. **Architecture:** Input → Processing → Output
3. **Usage:** CLI examples, exit codes
4. **CI Workflow:** Trigger mechanism, artifacts, access instructions
5. **Testing:** How to run unit tests + determinism tests
6. **Schema:** Ledger schema v1.0.0 structure
7. **Troubleshooting:** Common errors + fixes (including CI artifact issues)
8. **Monitoring:** Success/failure indicators for CI workflow
9. **Integration:** How it links to Phase 5A
10. **References:** Code paths, workflow YAML, related docs

#### B) Update `docs/ops/README.md`

Add Phase 5B section under "Phase 5A" with:
- Link to both runbooks (Cursor Multi-Agent + Operator)
- Key deliverables (including CI workflow)
- Risk statement (LOW)
- Artifact access instructions

**Deliverable:**  
Complete runbook + index update.

---

### 5.7 RISK_OFFICER

**Task:**  
Produce **RISK NOTE** covering:

**Risk Assessment:** LOW

**Potential Risks:**
1. **Artifact dependency drift:** Seed schema v0.1.0 → v0.2.0 break
   - **Impact:** CI workflow fails to parse seed
   - **Mitigation:** Fail-closed schema validation, explicit version checks in code

2. **Nondeterminism via metadata:** Timestamps in hash calculation
   - **Impact:** False positive diffs in ledger comparison
   - **Mitigation:** Timestamps excluded from canonical JSON hash, only in metadata section

3. **CI artifact retrieval fragility:** workflow_run dependency on Phase 5A
   - **Impact:** Artifact not found, workflow fails
   - **Mitigation:** Well-defined artifact naming (`trend-seed-<run_id>`), fallback to manual trigger (workflow_dispatch)

4. **Markdown summary nondeterminism:** Unstable "top N" selection
   - **Impact:** Markdown diffs on identical ledgers
   - **Mitigation:** Deterministic sorting for top N selection (canonical ordering)

**Impact:**  
Tooling/CI artifacts only, no trading core touched. Additive changes.

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

1. **FACTS_COLLECTOR** → Produce FACTS PACK (seed schema + Phase 5A artifact patterns)
2. **SCOPE_KEEPER** → Produce SCOPE LOCK (includes CI workflow)
3. **CI_GUARDIAN** → Choose workflow design (Option A vs B) + justify
4. **RISK_OFFICER** → Produce RISK NOTE (based on schema + workflow proposal)
5. **IMPLEMENTER** → Write library + CLI (complete code)
6. **TEST_ENGINEER** → Add fixtures + tests (including determinism)
7. **CI_GUARDIAN** → Implement workflow YAML (complete)
8. **DOCS_SCRIBE** → Add runbook + README update (includes CI workflow docs)
9. **ORCHESTRATOR** → Produce PR body + final checklist

**No parallel execution.** Each agent waits for previous agent's output.

---

## 8) PR BODY TEMPLATE (ORCHESTRATOR OUTPUT)

**Title:**  
```
feat(aiops): Phase 5B trend ledger consumer from seed + CI workflow
```

**Body (compact format):**

```markdown
## Summary
Implements Phase 5B consumer that converts Phase 5A Trend Seeds into canonical Trend Ledger snapshots, produced as CI artifacts with deterministic JSON and markdown summaries.

## Why
Establishes a stable, canonical ledger primitive from trend seeds, enabling future trend aggregation (Phase 5C+) with fail-closed validation, deterministic output, and automated CI artifact generation.

## Changes
- Consumer library: `src/ai_orchestration/trends/trend_ledger.py`
  - Fail-closed validation (missing keys / unsupported schema)
  - Deterministic JSON serialization (sorted keys, stable ordering)
  - Canonical hash computation for determinism verification
- CLI: `scripts/aiops/generate_trend_ledger_from_seed.py`
  - Inputs: trend seed JSON
  - Outputs: ledger JSON (canonical), ledger.md (summary), manifest.json (metadata)
- **CI workflow:** `.github/workflows/aiops-trend-ledger-from-seed.yml`
  - Trigger: `workflow_run` for Phase 5A completion (success, main only)
  - Downloads Phase 5A artifact, runs consumer, uploads Trend Ledger artifact
  - Minimal permissions (contents: read, actions: read)
- Tests: `tests/ai_orchestration/test_trend_ledger_from_seed.py` (21 tests)
- Fixture: `tests/fixtures/trend_seed.sample.json`
- Runbooks:
  - Operator: `docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md`
  - Multi-agent: `docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED_CURSOR_MULTI_AGENT.md`
- Index: `docs/ops/README.md` updated

## Verification
- Pre-commit hooks: all passed
- Test suite: 21/21 passed
- Determinism: verified byte-identical output
  - SHA-256: `8867a623725c5f97fa9ddadac06b9bad295380a89f5c8c87afe2d2ddb0fefb58`
  - Repeated runs: identical hashes
- CI workflow: tested locally, ready for auto-trigger

## Risk
LOW — tooling/CI artifacts only; no trading/live execution code touched.

**Potential Issues:**
- Artifact dependency drift (seed schema change) → Mitigated by fail-closed validation
- CI artifact retrieval fragility → Mitigated by workflow_dispatch fallback

## Operator How-To

### Local Usage
```bash
# Generate ledger from seed (local)
python scripts/aiops/generate_trend_ledger_from_seed.py \
  --input trend_seed.json \
  --output-json trend_ledger.json \
  --output-markdown trend_ledger.md
```

### CI Workflow
- Phase 5A workflow run completes on `main`
- Trend ledger workflow triggers automatically via `workflow_run`
- Produced artifact: `trend-ledger-<run_id>` (contains ledger JSON + markdown + manifest)
- **Manual trigger:** Actions tab → "AIOps - Trend Ledger from Seed" → Run workflow

## References
- Operator runbook: `docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md`
- Multi-agent runbook: `docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED_CURSOR_MULTI_AGENT.md`
- Phase 5A: `docs/ops/runbooks/RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md`
- CI workflow: `.github/workflows/aiops-trend-ledger-from-seed.yml`
```

---

## 9) FINAL CHECKLIST (MUST BE EXPLICITLY CHECKED)

**Before submitting PR:**

- [ ] New files compiled/importable
- [ ] Tests cover determinism (repeated runs → identical bytes)
- [ ] **CI workflow produces artifacts with stable filenames** (`trend-ledger-<run_id>`)
- [ ] **Workflow YAML triggers correctly** (workflow_run + workflow_dispatch)
- [ ] Fixture is minimal but representative
- [ ] Docs runbook added (includes CI workflow section)
- [ ] README index updated (includes CI workflow reference)
- [ ] No trading-core files touched
- [ ] Ruff/format compliance (pre-commit hooks passed)
- [ ] PR body includes all sections (Summary/Why/Changes/Verification/Risk/How-To/References)
- [ ] **Artifact naming convention documented** (in runbook + workflow)

---

## 10) DELIVERABLES — REQUIRED FINAL OUTPUT

The assistant must output:

### A) Full Code (Copy-Paste Ready)
- ✅ `src/ai_orchestration/trends/trend_ledger.py` (complete)
- ✅ `scripts/aiops/generate_trend_ledger_from_seed.py` (executable)

### B) CI Workflow
- ✅ `.github/workflows/aiops-trend-ledger-from-seed.yml` (complete, tested)

### C) Fixture Contents (JSON)
- ✅ `tests/fixtures/trend_seed.sample.json` (explicit content)

### D) Test Suite
- ✅ `tests/ai_orchestration/test_trend_ledger_from_seed.py` (complete)
- ✅ Includes determinism tests (repeated runs → identical hashes)

### E) Documentation
- ✅ `docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md` (includes CI workflow)
- ✅ `docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED_CURSOR_MULTI_AGENT.md` (this file)
- ✅ `docs/ops/README.md` (update section with both runbooks)

### F) PR Components
- ✅ PR title (includes "+ CI workflow")
- ✅ PR description (all sections including CI workflow)

### G) Risk & Mitigation Note
- ✅ Risk assessment (including CI-specific risks)
- ✅ Mitigation strategies

---

## 11) WORKFLOW DESIGN — CI_GUARDIAN DECISION

### Option A: workflow_run Trigger + Artifact Download (RECOMMENDED)

**Selected:** ✅ Option A

**Justification:**
1. **Clean separation:** Phase 5A and 5B remain independent
2. **Explicit dependencies:** Artifact download makes data flow clear
3. **Testability:** Manual trigger (workflow_dispatch) for debugging
4. **Efficiency:** No duplication of Phase 5A logic
5. **Robustness:** Fail-fast on missing artifacts

**Implementation:**
```yaml
on:
  workflow_run:
    workflows: ["AIOps - Trend Seed from Normalized Report"]
    types: [completed]
    branches: [main]
  workflow_dispatch:

jobs:
  generate-trend-ledger:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - uses: astral-sh/setup-uv@v4
      - uses: dawidd6/action-download-artifact@v6
        with:
          workflow: aiops-trend-seed-from-normalized-report.yml
          run_id: ${{ github.event.workflow_run.id }}
          name: trend-seed-${{ github.event.workflow_run.id }}
      - run: |
          uv run python scripts/aiops/generate_trend_ledger_from_seed.py \
            --input .tmp/phase5a_artifacts/trend_seed.normalized_report.json \
            --output-json .tmp/trend_ledger/trend_ledger.json \
            --output-markdown .tmp/trend_ledger/trend_ledger.md \
            --run-manifest .tmp/trend_ledger/manifest.json
      - uses: actions/upload-artifact@v4
        with:
          name: trend-ledger-${{ github.event.workflow_run.id }}
          path: .tmp/trend_ledger/
```

**Rejected:** ❌ Option B (regenerate seed)
- **Reason:** Higher coupling, duplicates Phase 5A logic, less maintainable

---

## 12) EXECUTION PROTOCOL

### Start Sequence

```
ORCHESTRATOR: "BEGIN PHASE 5B FULL EXECUTION"
↓
FACTS_COLLECTOR: "Produce FACTS PACK (seed schema + Phase 5A artifacts)"
↓
SCOPE_KEEPER: "Produce SCOPE LOCK (includes CI workflow)"
↓
CI_GUARDIAN: "Choose workflow design (Option A vs B) + justify"
↓
RISK_OFFICER: "Produce RISK NOTE (schema + workflow risks)"
↓
IMPLEMENTER: "Implement library + CLI"
↓
TEST_ENGINEER: "Add fixtures + tests (determinism)"
↓
CI_GUARDIAN: "Implement workflow YAML (complete)"
↓
DOCS_SCRIBE: "Add runbook + README (includes CI docs)"
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

## 13) SUCCESS CRITERIA

**Phase 5B FULL is COMPLETE when:**

1. ✅ PR created with all deliverables (code + CI workflow + docs)
2. ✅ All CI gates green (Lint/Audit/Policy/Tests)
3. ✅ Determinism verified (SHA-256 stable across runs)
4. ✅ **CI workflow tested** (workflow_dispatch run successful)
5. ✅ **Artifacts uploaded** with stable naming (`trend-ledger-<run_id>`)
6. ✅ Documentation complete (both runbooks + index)
7. ✅ Risk assessment LOW confirmed
8. ✅ No trading-core files touched

---

## 14) REFERENCES

**Related Runbooks:**
- Phase 5A: `RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md`
- Phase 4E: (see ops index)

**Code:**
- Library: `src/ai_orchestration/trends/trend_ledger.py`
- CLI: `scripts/aiops/generate_trend_ledger_from_seed.py`
- Tests: `tests/ai_orchestration/test_trend_ledger_from_seed.py`
- Fixture: `tests/fixtures/trend_seed.sample.json`

**CI:**
- Workflow: `.github/workflows/aiops-trend-ledger-from-seed.yml`
- Phase 5A workflow: `.github/workflows/aiops-trend-seed-from-normalized-report.yml`

**Docs:**
- Operator runbook: `RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md`
- Multi-agent runbook: `RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED_CURSOR_MULTI_AGENT.md` (this file)
- Ops index: `docs/ops/README.md`

---

## 15) CHANGE LOG

| Version | Date       | Author       | Changes                                      |
|---------|------------|--------------|----------------------------------------------|
| 1.0.0   | 2026-01-12 | AI Ops Team  | Initial Phase 5B minimal runbook             |
| 2.0.0   | 2026-01-12 | AI Ops Team  | Upgrade to FULL (added CI workflow section)  |

---

**Questions?** See operator runbook (`RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md`) or Phase 5A multi-agent runbook for context.
