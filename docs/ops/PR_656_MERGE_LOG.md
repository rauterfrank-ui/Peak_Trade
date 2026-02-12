# PR #656 — Merge Log

## Summary
- **PR:** #656
- **Title:** Phase 4E — Determinism Contract Report Normalization (Validator Report)
- **Scope:** CI / Reporting Infrastructure (no trading logic)
- **Risk:** 🟢 LOW
- **Merge Strategy:** Squash
- **Merged:** true
- **Merged At (UTC):** 2026-01-11T21:50:35Z
- **Merge Commit:** `8574c672507d54a127451f786b2cf12edd917ba3`
- **Head → Base:** `phase4e-report-normalization` → `main`

## Why
Phase 4E standardisiert den Validator-Report als kanonisches, schema-stabiles Artifact (ValidatorReport v1.0.0), damit CI-Artefakte maschinenlesbar in nachgelagerte Health/Trend Checks (Phase 5+) integrierbar sind, ohne Parsing-Drift. Backward Compatibility bleibt über ein Legacy-Artifact erhalten.

## Changes
### 1) CI Artifacts: Normalized + Legacy (Backward Compatibility)
- **Normalized Artifact (canonical):**
  - `validator_report.normalized.json` — schema: `ValidatorReport v1.0.0`
  - `validator_report.normalized.md` — human-readable summary
- **Legacy Artifact (compat):**
  - `validator_report.json` — legacy format for existing consumers

### 2) Root Cause Fix: Dependency Resolution in Workflow
- **Initial failure:** `ModuleNotFoundError: No module named 'pydantic'`
- **Root cause:** workflow invoked `python ...` instead of `python3 ...` → environment/deps not available
- **Fix:** replace python invocations with `python3` across all affected call sites

### 3) Workflow Trigger / Path Correction (v2)
- Adjusted workflow trigger/path to ensure the correct workflow is exercised:
  - from: `.github/workflows/l4_critic_replay_determinism.yml`
  - to: `.github/workflows/l4_critic_replay_determinism_v2.yml`

## Verification
### A) Artifact Proof (Phase 4E Closeout CI)
- **Run ID:** `20902058406`
- **Status:** ✅ SUCCESS
- **Artifacts Produced:** 2
  - Normalized: `validator-report-normalized-20902058406` (Artifact ID `5091683811`)
  - Legacy: `validator-report-legacy-20902058406` (Artifact ID `5091683841`)

### B) Post-Merge Verification on main (fresh download)
- **Run ID:** `20902441555`
- **Workflow:** L4 Critic Replay Determinism v2
- **Downloaded:** `./artifacts_main_latest/`
- **Observed contents:**
  - `validator-report-normalized-20902441555&#47;validator_report.normalized.json`
  - `validator-report-normalized-20902441555&#47;validator_report.normalized.md`
  - `validator-report-legacy-20902441555&#47;validator_report.json`

### Content Verification (reported)
- ✅ JSON schema-konform (`ValidatorReport v1.0.0`)
- ✅ Markdown korrekt formatiert
- ✅ Determinism check PASSED (hash match)
- ✅ Alle erforderlichen Felder vorhanden

### Final CI Status (Required Checks)
- ✅ CI Health Gate (weekly_core)
- ✅ Guard tracked files in reports
- ✅ audit
- ✅ tests (3.11)
- ✅ Policy Critic Gate
- ✅ Lint Gate
- ✅ Docs Diff Guard Policy Gate
- ✅ docs-reference-targets-gate
- (non-required, green) tests 3.9 / 3.10, determinism suites

## Risk
- **Level:** 🟢 LOW
- **No Trading Logic:** Keine Änderungen an Trading-Strategien / Execution-Logic (Scope: CI/Reporting)
- **Compatibility:** Legacy Artifact weiterhin verfügbar
- **Operational Impact:** Verbesserte Debuggability + maschinenlesbare Reports

## Operator How-To
### Merge Evidence (Captured)
```bash
gh pr view 656 --json state,mergedAt,mergeCommit,mergedBy \
  --jq '{state,mergedAt,mergeCommit:.mergeCommit.oid,mergedBy:.mergedBy.login}'
```

**Result:**
```json
{
  "state": "MERGED",
  "mergedAt": "2026-01-11T21:50:35Z",
  "mergeCommit": "8574c672507d54a127451f786b2cf12edd917ba3",
  "mergedBy": "rauterfrank-ui"
}
```

### Verify Future Runs
```bash
# Get latest run ID
RUN_ID="$(gh api repos/rauterfrank-ui/Peak_Trade/actions/workflows/l4_critic_replay_determinism_v2.yml/runs \
  --jq '.workflow_runs[0].id')"
echo "Latest Run ID: $RUN_ID"

# Download artifacts
gh run download "$RUN_ID" -D "./artifacts_check_${RUN_ID}"

# Verify schema version
jq -r '.schema_version' \
  "./artifacts_check_${RUN_ID}/validator-report-normalized-${RUN_ID}/validator_report.normalized.json"
# Expected: 1.0.0

# Verify determinism result
jq -r '.result' \
  "./artifacts_check_${RUN_ID}/validator-report-normalized-${RUN_ID}/validator_report.normalized.json"
# Expected: PASS

# Verify hash match
jq -r '.checks[0].metrics | "\(.baseline_hash == .candidate_hash)"' \
  "./artifacts_check_${RUN_ID}/validator-report-normalized-${RUN_ID}/validator_report.normalized.json"
# Expected: true

# Verify legacy compatibility
jq -r '.result.equal' \
  "./artifacts_check_${RUN_ID}/validator-report-legacy-${RUN_ID}/validator_report.json"
# Expected: true
```

## References
- **PR:** https://github.com/rauterfrank-ui/Peak_Trade/pull/656
- **Merge Commit:** https://github.com/rauterfrank-ui/Peak_Trade/commit/8574c672507d54a127451f786b2cf12edd917ba3
- **Post-Merge CI Run:** https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20902441555
- **Proof Run (Pre-Merge):** https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20902058406
- **Root Cause Commits:**
  - `ebb8f9ec` - Python invocation fix
  - `11b3e934` - Workflow trigger/path correction

## Next Steps
1. **Monitoring:** Watch next 3 CI runs (weekly schedule) to ensure normalized artifacts consistent
2. **AI Tooling:** Begin consuming normalized schema in future orchestration layers (Phase 4F+)
3. **Deprecation Plan:** Evaluate legacy format retirement timeline (not before Q2 2026)
4. **Schema Evolution:** Document v2.0.0 requirements if new governance gates added

---

**Closeout:** Phase 4E complete. Normalized validator reports (schema v1.0.0) operational. ✅
