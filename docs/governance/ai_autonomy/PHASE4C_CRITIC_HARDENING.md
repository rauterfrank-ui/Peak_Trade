# Phase 4C: Governance Critic → Evidence Pack Integration Hardening

**Status:** ✅ Implemented  
**Date:** 2026-01-11  
**Scope:** P0 (Critical) — Standardized Outputs, Determinism, CI Gate  
**Risk:** 🟢 LOW (Replay-only, schema-versioned, deterministic)

---

## Executive Summary

Phase 4C hardens the L4 Governance Critic integration with:
1. **Standardized Output Artefakte** (schema-versioned JSON + derived Markdown)
2. **Deterministic Replay** (snapshot-based CI gate)
3. **Control Center One-Liners** (operator-friendly CLI flags)

**Deliverables:**
- `critic_report.json` (schema v1.0.0, canonical JSON)
- `critic_summary.md` (derived from JSON, human-readable)
- CI Gate: "L4 Critic Replay Determinism" (snapshot-based)
- CLI Flags: `--out`, `--pack-id`, `--schema-version`, `--deterministic`

**Governance:** Evidence-first, replay-only, deterministic outputs, no live calls, no network dependencies in CI.

---

## 1. Purpose

### Goals
- **Standardization:** Schema-versioned outputs for evolution and compatibility
- **Determinism:** Bit-identical outputs on replay for CI stability
- **Operator UX:** Simple one-liners for common workflows
- **Hardening:** Snapshot-based CI gate prevents regressions

### Non-Goals
- No changes to trading/execution logic
- No new "intelligence" heuristics (focus: packaging/hardening)
- No external services

---

## 2. Architecture

### 2.1 Component Overview

```
src/ai_orchestration/
├── critic_report_schema.py        # NEW: Pydantic schema for critic reports
├── l4_critic.py                   # UPDATED: Uses new schema
└── ...

scripts/aiops/
└── run_l4_governance_critic.py    # UPDATED: New CLI flags

tests/ai_orchestration/
└── test_l4_critic_determinism.py  # NEW: Determinism tests

tests/fixtures/l4_critic_determinism/
└── l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/
    ├── critic_report.json         # Snapshot (golden output)
    └── critic_summary.md          # Snapshot (golden output)

.github/workflows/
└── l4_critic_replay_determinism.yml  # NEW: CI gate
```

---

## 3. Standardized Output Artefakte

### 3.1 critic_report.json (Schema v1.0.0)

**Purpose:** Authoritative, machine-readable critic report.

**Schema Fields:**
```json
{
  "schema_version": "1.0.0",
  "pack_id": "<string>",
  "mode": "replay|live_disabled|dry",
  "critic": {
    "name": "L4_Governance_Critic",
    "version": "1.0.0"
  },
  "inputs": {
    "evidence_pack_path": "<normalized-path>",
    "fixture": "<string|null>",
    "schema_version_in": "<string>"
  },
  "summary": {
    "verdict": "PASS|FAIL|WARN",
    "risk_level": "LOW|MEDIUM|HIGH",
    "score": <number|null>,
    "finding_counts": {
      "high": <int>,
      "med": <int>,
      "low": <int>,
      "info": <int>
    }
  },
  "findings": [
    {
      "id": "<string>",
      "title": "<string>",
      "severity": "HIGH|MEDIUM|LOW|INFO",
      "status": "OPEN|ACK|CLOSED",
      "rationale": "<string>",
      "evidence_refs": ["<string>", ...],
      "metrics": { "<k>": "<scalar>", ... }
    }
  ],
  "meta": {
    "deterministic": true,
    "canonicalization": {
      "rules": ["sorted_keys", "sorted_lists", "normalized_paths"]
    },
    "created_at": null  // null in deterministic mode
  }
}
```

**Determinism Rules:**
- Stable key ordering (JSON keys sorted alphabetically)
- Stable list ordering (findings sorted by severity desc, then id)
- Normalized paths (repo-relative, no absolute paths)
- No timestamps in deterministic mode (`created_at: null`)
- No volatile fields (random seeds, temp paths)

### 3.2 critic_summary.md

**Purpose:** Human-readable summary (derived from JSON).

**Structure:**
```markdown
# L4 Governance Critic Summary

**Schema Version:** 1.0.0  
**Pack ID:** L1_sample_2026-01-10  
**Mode:** replay  
**Deterministic:** True  

---

## Verdict

- **Overall:** PASS
- **Risk Level:** LOW

## Finding Counts

- **HIGH:** 0
- **MED:** 0
- **LOW:** 1
- **INFO:** 1

## Top Findings

### F001: Governance Decision: ALLOW
- **Severity:** LOW
- **Status:** OPEN
- **Rationale:** ...
- **Evidence:** EVD-L1-001, EVD-L1-002

---

## Statistics

- **Total Findings:** 2
- **Critic:** L4_Governance_Critic v1.0.0
- **Input Schema:** 1.0

---

*Generated from `critic_report.json` (schema v1.0.0)*
```

**Key Properties:**
- Pure derivation from JSON (no additional computation)
- Stable formatting (no timestamps, no volatile data)
- Top 10 findings only (for readability)

---

## 4. Control Center: Operator One-Liners

### 4.1 Basic Replay (Deterministic, CI-Safe)

**Use Case:** Replay with snapshot validation

```bash
# Minimal replay (deterministic)
python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/l4_critic_out \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic
```

**Output:**
```
.tmp/l4_critic_out/
├── critic_report.json      # Schema-versioned, canonical
├── critic_summary.md       # Derived from JSON
├── critic_report.md        # Legacy (backward compatibility)
├── critic_decision.json    # Legacy
├── critic_manifest.json    # Legacy
└── operator_summary.txt    # Legacy
```

### 4.2 Custom Output Directory

**Use Case:** Operator-controlled output location

```bash
python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack evidence_packs/L1_var_research \
  --mode replay \
  --fixture l4_critic_sample \
  --out evidence_packs/L4_review_var_research
```

### 4.3 Custom Pack ID (Override)

**Use Case:** Determinism testing with fixed pack ID

```bash
python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --pack-id L1_FIXED_ID_FOR_TESTING \
  --deterministic
```

### 4.4 Schema Version Control

**Use Case:** Test schema evolution

```bash
python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --schema-version 1.1.0 \
  --deterministic
```

### 4.5 CI Replay Path (Snapshot Validation)

**Use Case:** CI gate validation

```bash
# Run critic in deterministic mode
python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/l4_critic_out \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic

# Compare with snapshot
SNAPSHOT_DIR="tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0"
diff -u "$SNAPSHOT_DIR/critic_report.json" .tmp/l4_critic_out/critic_report.json
diff -u "$SNAPSHOT_DIR/critic_summary.md" .tmp/l4_critic_out/critic_summary.md
```

---

## 5. CLI Flags Reference

### New Flags (Phase 4C)

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--pack-id` | `str` | (auto) | Evidence pack ID override (for determinism) |
| `--schema-version` | `str` | `1.0.0` | Critic report schema version |
| `--no-legacy-output` | flag | `false` | Suppress legacy artifacts (clean output) |

### Existing Flags (Phase 4B)

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--evidence-pack` | `str` | (required) | Path to Evidence Pack directory |
| `--mode` | `str` | `replay` | Run mode (`replay`, `dry`, `live`, `record`) |
| `--fixture` | `str` | - | Fixture ID (alternative to `--transcript`) |
| `--transcript` | `str` | - | Path to transcript file |
| `--out` | `str` | (auto) | Output directory for artifacts |
| `--notes` | `str` | `""` | Operator notes |
| `--deterministic` | flag | `false` | Use fixed clock for deterministic output |
| `--allow-network` | flag | `false` | Allow network calls (opt-in) |
| `--record` | flag | `false` | Record mode: save transcript |

---

## 6. Legacy Output Policy

### 6.1 Overview

**Phase 4C introduces standardized outputs** (`critic_report.json` + `critic_summary.md`) while **preserving legacy artifacts** for backward compatibility.

**Default Behavior (legacy_output=True):**
- ✅ `critic_report.json` (schema v1.0.0) [ALWAYS]
- ✅ `critic_summary.md` (derived from JSON) [ALWAYS]
- ✅ `critic_report.md` (legacy)
- ✅ `critic_decision.json` (legacy)
- ✅ `critic_manifest.json` (legacy)
- ✅ `operator_summary.txt` (legacy)

**With --no-legacy-output flag:**
- ✅ `critic_report.json` (schema v1.0.0) [ALWAYS]
- ✅ `critic_summary.md` (derived from JSON) [ALWAYS]
- ❌ No legacy files

### 6.2 Migration Strategy

**Phase 4C (Current):**
- Legacy outputs ON by default
- Operators can test new outputs with `--no-legacy-output`
- Both formats coexist

**Future Phase (TBD):**
- Legacy outputs OFF by default
- Enable via `--legacy-output` flag
- Deprecation warnings added

**End State:**
- Legacy outputs removed
- Only standardized outputs remain

### 6.3 Use Cases

**Use standardized outputs when:**
- CI/CD pipelines (deterministic, schema-versioned)
- Automated processing (JSON parsing, structured data)
- Long-term archival (schema evolution support)
- Cross-tool integration (stable API)

**Keep legacy outputs for:**
- Existing scripts/workflows (temporary compatibility)
- Human review (familiar format during transition)
- Gradual migration (test new format alongside old)

### 6.4 Legacy Output Suppression

**Command:**
```bash
python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/clean_output \
  --pack-id L1_sample_2026-01-10 \
  --deterministic \
  --no-legacy-output  # ← Suppress legacy files
```

**Output:**
```
.tmp/clean_output/
├── critic_report.json    ← Only standardized outputs
└── critic_summary.md     ← Clean, minimal
```

---

## 7. CI Gate: L4 Critic Replay Determinism

### 6.1 Purpose

Validates that L4 Critic produces **byte-identical outputs** in replay mode.

**Prevents:**
- Non-deterministic test failures
- CI flakes due to timestamps/random seeds
- Schema drift without explicit versioning

### 6.2 Workflow

**File:** `.github/workflows/l4_critic_replay_determinism.yml`

**Jobs:**
1. **l4-critic-replay-determinism:** Runs CLI in deterministic mode, compares with snapshot
2. **l4-critic-determinism-tests:** Runs pytest tests for determinism validation

**Trigger:**
- Push to `main`/`master`
- Pull requests
- Manual dispatch

**Path Filter:**
- `src/ai_orchestration/l4_critic.py`
- `src/ai_orchestration/critic_report_schema.py`
- `scripts/aiops/run_l4_governance_critic.py`
- `tests&#47;ai_orchestration&#47;test_l4_critic*.py`
- `tests&#47;fixtures&#47;l4_critic_determinism&#47;**`

### 6.3 Snapshot Validation

**Snapshot Location:**
```
tests/fixtures/l4_critic_determinism/
└── l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/
    ├── critic_report.json
    └── critic_summary.md
```

**Validation Steps:**
1. Run L4 Critic with `--deterministic` flag
2. Compare `critic_report.json` (byte-identical)
3. Compare `critic_summary.md` (text-identical)
4. Fail CI if differences detected

**On Failure:**
- Print unified diff
- Upload outputs as artifacts
- Clear error message with remediation steps

---

## 7. Determinism Strategy

### 7.1 Canonical JSON Rules

**Applied in `critic_report_schema.py`:**
1. **Sorted Keys:** JSON keys sorted alphabetically (`sort_keys=True`)
2. **Sorted Lists:** Findings sorted by severity (HIGH > MEDIUM > LOW > INFO), then by ID
3. **Normalized Paths:** Repo-relative paths (no `/Users/`, `/home/`, `C:\`)
4. **No Timestamps:** `created_at: null` in deterministic mode
5. **Trailing Newline:** Git-friendly file endings

### 7.2 Fixed Clock Injection

**In Tests:**
```python
from datetime import datetime, timezone

clock = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
runner = L4Critic(clock=clock)
```

**In CLI:**
```bash
python scripts/aiops/run_l4_governance_critic.py \
  --deterministic  # Injects fixed clock: 2026-01-10T12:00:00Z
```

### 7.3 Path Normalization

**Function:** `normalize_path_for_determinism(path, deterministic)`

**Behavior:**
- If `deterministic=False`: Return absolute path as-is
- If `deterministic=True`:
  - Strip user-specific prefixes (`/Users/`, `/home/`, `C:\Users\`)
  - Extract repo-relative path (anchor: `Peak_Trade` or `tests`)
  - Return normalized string

**Example:**
```python
# Input: /Users/frnkhrz/Peak_Trade/tests/fixtures/evidence_packs/L1_sample_2026-01-10
# Output: tests/fixtures/evidence_packs/L1_sample_2026-01-10
```

---

## 8. Testing

### 8.1 Unit Tests

**File:** `tests/ai_orchestration/test_l4_critic_determinism.py`

**Test Coverage:**
- ✅ `critic_report.json` byte-identical on repeated runs
- ✅ `critic_report.json` matches snapshot
- ✅ `critic_summary.md` matches snapshot
- ✅ Findings sorted by severity
- ✅ Paths normalized in deterministic mode
- ✅ Schema version present
- ✅ JSON write deterministic (sorted keys)

**Run Tests:**
```bash
# All determinism tests
pytest tests/ai_orchestration/test_l4_critic_determinism.py -v

# Specific test
pytest tests/ai_orchestration/test_l4_critic_determinism.py::TestL4CriticDeterminism::test_critic_report_json_determinism -v

# With coverage
pytest tests/ai_orchestration/test_l4_critic_determinism.py --cov=src/ai_orchestration/critic_report_schema --cov=src/ai_orchestration/l4_critic
```

### 8.2 CI Tests

**Workflow:** `.github/workflows/l4_critic_replay_determinism.yml`

**Expected Behavior:**
- ✅ Green on main (snapshot matches)
- ❌ Red if output changes (non-deterministic or schema drift)
- ⏭️ Skip on docs-only PRs (path filter)

---

## 9. Acceptance Criteria

### Phase 4C Deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | `critic_report.json` (schema v1.0.0) | ✅ Implemented |
| 2 | `critic_summary.md` (derived from JSON) | ✅ Implemented |
| 3 | CLI flags (`--pack-id`, `--schema-version`) | ✅ Implemented |
| 4 | Deterministic replay (fixed clock, normalized paths) | ✅ Implemented |
| 5 | Snapshot fixtures | ✅ Created |
| 6 | Unit tests (determinism) | ✅ Implemented |
| 7 | CI gate (snapshot-based) | ✅ Implemented |
| 8 | Control Center docs (one-liners) | ✅ This document |

### Validation Steps

**Step 1: Run CLI in deterministic mode**
```bash
python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/l4_critic_out \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic
```

**Expected Output:**
```
✅ L4 GOVERNANCE CRITIC COMPLETE
=================================================================
L4 Critic Run Complete
Run ID: L4-...
Evidence Pack: L1_sample_2026-01-10
Decision: ALLOW (LOW)
SoD: PASS
Capability Scope: PASS
Artifacts: 6 files
```

**Step 2: Validate outputs**
```bash
# Check files exist
ls .tmp/l4_critic_out/
# Expected: critic_report.json, critic_summary.md, ...

# Validate JSON schema
python -m json.tool .tmp/l4_critic_out/critic_report.json > /dev/null
echo "✅ JSON valid"

# Check schema version
jq '.schema_version' .tmp/l4_critic_out/critic_report.json
# Expected: "1.0.0"

# Check deterministic flag
jq '.meta.deterministic' .tmp/l4_critic_out/critic_report.json
# Expected: true

# Check no timestamp
jq '.meta.created_at' .tmp/l4_critic_out/critic_report.json
# Expected: null
```

**Step 3: Run twice, compare bytes**
```bash
# Run 1
python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/run1 \
  --pack-id L1_sample_2026-01-10 \
  --deterministic

# Run 2
python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/run2 \
  --pack-id L1_sample_2026-01-10 \
  --deterministic

# Compare (should be identical)
diff .tmp/run1/critic_report.json .tmp/run2/critic_report.json
# Expected: no output (files identical)
```

**Step 4: Run tests**
```bash
pytest tests/ai_orchestration/test_l4_critic_determinism.py -v
# Expected: all tests pass
```

**Step 5: Trigger CI**
```bash
# Push to branch, open PR
# CI workflow "L4 Critic Replay Determinism" should run and pass
```

---

## 10. Snapshot Update Procedure

### 10.1 When to Update Snapshots

**Update snapshots when:**
- ✅ Intentional schema changes (new fields, renamed fields)
- ✅ Improved determinism logic (better path normalization)
- ✅ Bug fixes that change output format
- ✅ Schema version bump (e.g., 1.0.0 → 1.1.0)

**Do NOT update for:**
- ❌ Random test failures (investigate non-determinism instead)
- ❌ Convenience (snapshots are contract, not burden)
- ❌ CI flakes (fix root cause, not snapshot)

### 10.2 Update Procedure

**Step 1: Verify Intentional Change**
```bash
# Run critic with current code
python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/new_output \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic

# Compare with snapshot
SNAPSHOT_DIR="tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0"
diff -u "$SNAPSHOT_DIR/critic_report.json" .tmp/new_output/critic_report.json

# Review diff carefully
# If intentional and correct, proceed to Step 2
```

**Step 2: Update Snapshot**
```bash
# Copy new outputs to snapshot directory
cp .tmp/new_output/critic_report.json "$SNAPSHOT_DIR/critic_report.json"
cp .tmp/new_output/critic_summary.md "$SNAPSHOT_DIR/critic_summary.md"

echo "✅ Snapshot updated"
```

**Step 3: Verify Determinism**
```bash
# Run twice, verify identical
rm -rf .tmp/verify_a .tmp/verify_b

python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/verify_a \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic

python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/verify_b \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic

# Should be byte-identical
diff .tmp/verify_a/critic_report.json .tmp/verify_b/critic_report.json
diff .tmp/verify_a/critic_summary.md .tmp/verify_b/critic_summary.md
# Expected: no output (files identical)
```

**Step 4: Run Tests**
```bash
# All tests should pass with new snapshot
pytest tests/ai_orchestration/test_l4_critic_determinism.py -v
```

**Step 5: Commit with Justification**
```bash
git add tests/fixtures/l4_critic_determinism/
git commit -m "test(l4-critic): update snapshot for [REASON]

Snapshot updated due to:
- [Specific change, e.g., 'Added finding_counts.critical field']
- [Impact, e.g., 'Schema version remains 1.0.0']

Verified:
- Determinism preserved (2 runs → identical bytes)
- All tests pass
- CI gate will validate"
```

### 10.3 Guardrails

**Required Review:**
- All snapshot updates MUST be reviewed by at least one other engineer
- PR description MUST explain WHY snapshot changed
- CI MUST pass with new snapshot

**Rollback Plan:**
- If CI fails post-merge, revert snapshot immediately
- Investigate root cause offline
- Re-apply with fix

---

## 11. Troubleshooting

### Issue: Snapshot Mismatch

**Symptom:**
```
❌ FAILURE: critic_report.json differs from snapshot
```

**Diagnosis:**
```bash
# Compare outputs
diff -u \
  tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/critic_report.json \
  .tmp/l4_critic_out/critic_report.json
```

**Common Causes:**
1. **Non-deterministic timestamp:** Check `meta.created_at` (should be `null`)
2. **Absolute paths:** Check `inputs.evidence_pack_path` (should be repo-relative)
3. **Unsorted findings:** Check findings order (severity desc, then id)
4. **Schema drift:** Check `schema_version` matches snapshot

**Remediation:**
- If intentional change: Update snapshot
- If unintentional: Fix code to restore determinism

### Issue: Tests Fail Locally but Pass in CI

**Symptom:**
```
pytest tests/ai_orchestration/test_l4_critic_determinism.py
# Some tests fail locally
```

**Diagnosis:**
- Check Python version (CI uses 3.11)
- Check dependencies (CI uses `requirements.txt`)
- Check working directory (tests assume repo root)

**Remediation:**
```bash
# Run from repo root
cd /path/to/Peak_Trade

# Use Python 3.11
python3.11 -m pytest tests/ai_orchestration/test_l4_critic_determinism.py -v
```

### Issue: CI Gate Skipped

**Symptom:**
```
CI workflow "L4 Critic Replay Determinism" shows "Skip if no critic changes"
```

**Diagnosis:**
- Path filter excludes changed files
- PR is docs-only

**Remediation:**
- Check path filter in `.github/workflows/l4_critic_replay_determinism.yml`
- If critic code changed, ensure paths match filter

---

## 12. Determinism Contract

### 12.1 Location-Independent Determinism

**Contract:** Output is byte-identical regardless of output directory location.

**Verified:**
```bash
# Run in different locations
--out /tmp/pt_l4_critic_run
--out .tmp/l4_critic_a
--out ~/workspace/l4_reviews

# All produce identical critic_report.json
```

**Implementation:**
- Paths in JSON are repo-relative (not absolute)
- Fixed clock in deterministic mode
- Sorted keys, sorted findings
- No runtime-dependent data

### 12.2 Repo-Relative Path Normalization

**Input paths are normalized:**
```python
# Input: /Users/frnkhrz/Peak_Trade/tests/fixtures/evidence_packs/L1_sample_2026-01-10
# Output JSON: tests/fixtures/evidence_packs/L1_sample_2026-01-10
```

**Rules:**
- Strip user-specific prefixes (`/Users/`, `/home/`, `C:\Users\`)
- Extract repo-relative path (anchor: `Peak_Trade` or `tests`)
- Preserve relative structure

### 12.3 Stable Ordering & Canonicalization

**JSON Keys:**
- Alphabetically sorted (`sort_keys=True`)
- Consistent field ordering in Pydantic models

**Findings:**
- Sorted by severity (HIGH > MEDIUM > LOW > INFO)
- Within same severity, sorted by ID

**Lists:**
- Evidence refs sorted alphabetically
- Metrics keys sorted

### 12.4 No Volatile Fields in Deterministic Mode

**Suppressed in deterministic mode:**
- ❌ Timestamps (`meta.created_at: null`)
- ❌ Random seeds
- ❌ Absolute paths
- ❌ Temp directory paths
- ❌ Process IDs, thread IDs

**Always present:**
- ✅ Schema version
- ✅ Pack ID
- ✅ Mode
- ✅ Verdict, risk level
- ✅ Findings (sorted)

---

## 13. Next Steps

### Phase 4C: Complete ✅

- [x] Standardized output artefakte (JSON + MD)
- [x] Deterministic replay (fixed clock, normalized paths)
- [x] CLI flags (`--pack-id`, `--schema-version`)
- [x] Snapshot fixtures
- [x] Unit tests (determinism)
- [x] CI gate (snapshot-based)
- [x] Control Center docs (this document)

### Future Work

- [ ] Schema evolution (v1.1.0, v2.0.0)
- [ ] Multi-pack batch processing
- [ ] Automated snapshot update workflow
- [ ] Performance benchmarks (replay latency)
- [ ] Cross-platform determinism (Windows, macOS, Linux)

---

## 12. References

- **Phase 4B (L4 Critic Integration):** `docs/governance/ai_autonomy/PHASE4_L1_L4_INTEGRATION.md`
- **Authoritative Matrix:** `docs/governance/ai_autonomy/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md`
- **Model Registry:** `config/model_registry.toml`
- **L4 Capability Scope:** `config/capability_scopes/L4_governance_critic.toml`
- **Control Center Operations:** `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md`

---

**Last Updated:** 2026-01-11  
**Phase:** 4C (Implementation Complete)  
**Status:** ✅ READY FOR PR
