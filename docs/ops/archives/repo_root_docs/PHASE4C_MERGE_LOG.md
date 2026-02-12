# Phase 4C: L4 Governance Critic → Evidence Pack Integration Hardening

**Date:** 2026-01-11  
**Type:** Enhancement (AI-Ops Tooling)  
**Scope:** Governance / Deterministic Replay  
**Risk:** 🟢 LOW (replay-only, no trading logic)

---

## Summary

Phase 4C hardening: standardized critic artifacts + deterministic replay snapshot gate.

Ensures governance-critic outputs are stable, comparable, and CI-enforceable through snapshot determinism and operator-friendly artifacts.

---

## Why

**Problem:**
- L4 Critic outputs were not schema-versioned (Phase 4B: ad-hoc markdown/JSON)
- No CI enforcement for deterministic replay (outputs could drift)
- Legacy artifacts created clutter in CI outputs (6 files vs. 2 essential)
- No standardized snapshot-based regression detection

**Solution:**
- Standardized, schema-versioned outputs (`critic_report.json` v1.0.0)
- Deterministic replay with snapshot-based CI gate
- Clean CI mode (`--no-legacy-output`) for minimal output
- Operator-friendly one-liners and documentation

---

## Changes

### 1. Standardized Output Artifacts
- **Added:** `critic_report.json` (schema v1.0.0, Pydantic-based, authoritative)
- **Added:** `critic_summary.md` (derived from JSON, human-readable)
- **Schema features:** Deterministic (no timestamps), repo-relative paths, sorted keys/findings

### 2. Legacy Output Policy
- **Added:** `--no-legacy-output` flag (suppresses 4 legacy files)
- **Default:** Legacy ON (backward compatibility for one deprecation window)
- **CI mode:** Uses `--no-legacy-output` for clean 2-file output

### 3. Snapshot-Based CI Gate
- **Added:** `.github/workflows/l4_critic_replay_determinism.yml` (2 jobs)
  - Job 1: CLI-based snapshot validation (diff-based, fails on drift)
  - Job 2: Pytest-based determinism tests (10 tests)
- **Snapshots:** `tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/`
- **Behavior:** Fails CI with unified diff on any output change

### 4. Tests
- **Added:** `tests/ai_orchestration/test_l4_critic_determinism.py` (10 tests)
  - 5 tests: determinism (byte-identical, snapshot match, sorted findings)
  - 3 tests: legacy policy (default ON, suppressed, standardized always present)
  - 2 tests: schema validation
- **Result:** 10/10 pass in 0.09s

### 5. Documentation
- **Added:** `docs/governance/ai_autonomy/PHASE4C_CRITIC_HARDENING.md`
  - Section 6: Legacy Output Policy
  - Section 10: Snapshot Update Procedure
  - Section 12: Determinism Contract
- **Operator one-liners:** Minimal, clean, custom location examples

### 6. Implementation
- **Modified:** `src/ai_orchestration/l4_critic.py` (+legacy_output parameter)
- **Modified:** `scripts/aiops/run_l4_governance_critic.py` (+--no-legacy-output flag)
- **Added:** `src/ai_orchestration/critic_report_schema.py` (Pydantic models)

---

## Verification

### Manual Verification
```bash
# CI-clean replay (standard artifacts only)
python3 scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/l4_critic_ci_run \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic \
  --no-legacy-output

# Output: Exactly 2 files (critic_report.json + critic_summary.md)
ls -1 .tmp/l4_critic_ci_run/ | wc -l  # Expected: 2

# Snapshot comparison
SNAP_DIR="tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0"
diff -u "$SNAP_DIR/critic_report.json" .tmp/l4_critic_ci_run/critic_report.json
# Expected: no output (files identical)
```

**Results:**
- ✅ Produces exactly 2 files (clean output)
- ✅ Matches snapshots (no diff)
- ✅ Deterministic run ID stable on repeat (L4-4e04ea4c65509433)
- ✅ Output location does not influence determinism (verified: /tmp, .tmp, out/)

### Automated Verification
```bash
# All tests pass
python3 -m pytest tests/ai_orchestration/test_l4_critic_determinism.py -v
# Result: 10 passed in 0.09s

# Determinism check (2 runs → identical)
python3 scripts/aiops/run_l4_governance_critic.py ... --out .tmp/run1
python3 scripts/aiops/run_l4_governance_critic.py ... --out .tmp/run2
diff .tmp/run1/critic_report.json .tmp/run2/critic_report.json
# Expected: no output (byte-identical)
```

### CI Gate Verification
- **Workflow:** `.github/workflows/l4_critic_replay_determinism.yml`
- **Expected:** CI passes on main, fails on output drift
- **Failure behavior:** Uploads artifacts + prints unified diff

---

## Risk

**Level:** 🟢 **LOW**

**Why Low:**
- AI-Ops tooling only (no trading/execution logic changes)
- Replay-only mode (no live model calls)
- Schema-versioned (explicit evolution)
- Backward compatible (legacy outputs default ON)
- 10/10 tests pass
- Determinism verified (location-independent, byte-identical)

**No Impact On:**
- Trading strategies
- Risk management
- Portfolio execution
- Live market data
- Production systems

**Scope:** Governance tooling hardening for AI Autonomy framework.

---

## Operator How-To

### Quick Start (CI-Clean Mode)

**Command:**
```bash
python3 scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/l4_critic_ci_run \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic \
  --no-legacy-output
```

**Output:**
```
✅ L4 GOVERNANCE CRITIC COMPLETE
Artifacts: 2 files
  - critic_report_json: .tmp/l4_critic_ci_run/critic_report.json
  - critic_summary_md: .tmp/l4_critic_ci_run/critic_summary.md
```

**Files Generated:**
- `critic_report.json` (1.6K, schema v1.0.0, authoritative)
- `critic_summary.md` (1.1K, derived, human-readable)

### Use Cases

**1. CI/CD Pipeline (Clean):**
```bash
--out .tmp/l4_critic_ci_run --deterministic --no-legacy-output
```

**2. Operator Analysis (With Legacy):**
```bash
--out evidence_packs/L4_review_$(date +%Y%m%d)
# Generates: 2 standard + 4 legacy files (6 total)
```

**3. Custom Location:**
```bash
--out /tmp/pt_l4_critic_run
# Location-independent determinism preserved
```

### Snapshot Update Procedure

**When to update snapshots:**
- ✅ Intentional schema changes
- ✅ Bug fixes affecting output
- ✅ Schema version bump (e.g., 1.0.0 → 1.1.0)

**Procedure:**
```bash
# 1) Generate fresh outputs
python3 scripts/aiops/run_l4_governance_critic.py ... --out .tmp/new_output

# 2) Review diff
SNAP_DIR="tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0"
diff -u "$SNAP_DIR/critic_report.json" .tmp/new_output/critic_report.json

# 3) If intentional, update
cp .tmp/new_output/critic_report.json "$SNAP_DIR/critic_report.json"
cp .tmp/new_output/critic_summary.md "$SNAP_DIR/critic_summary.md"

# 4) Commit with justification
git add tests/fixtures/l4_critic_determinism/
git commit -m "test(l4-critic): update snapshot for [REASON]"
```

**Guardrails:**
- Mandatory: Review diff before commit
- Mandatory: Explain WHY in commit message
- Mandatory: Verify determinism (2 runs → identical)
- Review: Snapshot updates require code review

---

## References

### Code
- `src/ai_orchestration/critic_report_schema.py` (new: Pydantic models)
- `src/ai_orchestration/l4_critic.py` (modified: +legacy_output)
- `scripts/aiops/run_l4_governance_critic.py` (modified: +--no-legacy-output)

### Tests
- `tests/ai_orchestration/test_l4_critic_determinism.py` (new: 10 tests)
- `tests/fixtures/l4_critic_determinism/` (new: snapshot fixtures)

### CI
- `.github/workflows/l4_critic_replay_determinism.yml` (new: CI gate)
- `.github/workflows/l4_critic_replay_determinism_v2.yml` (new: enhanced version)

### Documentation
- `docs/governance/ai_autonomy/PHASE4C_CRITIC_HARDENING.md` (new: complete spec)
- `PHASE4C_IMPLEMENTATION_REPORT.md` (new: implementation details)
- `PHASE4C_FINAL_REPORT.md` (new: final verification)

### Related
- `docs/governance/ai_autonomy/PHASE4_L1_L4_INTEGRATION.md` (Phase 4B)
- `config/capability_scopes/L4_governance_critic.toml` (capability scope)
- `config/model_registry.toml` (model registry)

---

## Files Changed

**Modified (2):**
- `src/ai_orchestration/l4_critic.py`
- `scripts/aiops/run_l4_governance_critic.py`

**Added (7):**
- `src/ai_orchestration/critic_report_schema.py`
- `tests/ai_orchestration/test_l4_critic_determinism.py`
- `tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/critic_report.json`
- `tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/critic_summary.md`
- `.github/workflows/l4_critic_replay_determinism.yml`
- `.github/workflows/l4_critic_replay_determinism_v2.yml`
- `docs/governance/ai_autonomy/PHASE4C_CRITIC_HARDENING.md`

**Reports (3):**
- `PHASE4C_IMPLEMENTATION_REPORT.md`
- `PHASE4C_FINAL_REPORT.md`
- `PHASE4C_MERGE_LOG.md` (this file)

---

## Next Steps

**Immediate (Post-Merge):**
1. Monitor CI gate on main (ensure passes)
2. Watch for snapshot mismatches (indicates drift)
3. Operator training: share one-liners + use cases

**Future Phases:**
- Phase 4D: L4 Critic → L2 Market Outlook integration
- Phase 5: Multi-layer Evidence Pack chaining
- Phase 6: Live model calls with budget controls
- Deprecate legacy outputs (make --legacy-output required flag)

---

**Implementation Date:** 2026-01-11  
**Status:** ✅ Complete & Verified  
**Quality:** 🟢 Production-Ready  
**Test Coverage:** 10/10 tests pass  
**CI:** Gate implemented & tested
