# Evidence Pack CI Gate (Phase 4A)

**Status:** Implemented  
**Date:** 2026-01-08  
**Phase:** 4A (CI Integration + Auto-Creation)

---

## Overview

Evidence Pack CI Gate ist ein **required CI check** für alle PRs. Er validiert automatisch generierte Evidence Packs und stellt sicher, dass alle Layer Runs strukturierte, auditierbare Artefakte erzeugen.

**Key Features:**
- **CI Gate:** Required check (fail-closed) für PR merges
- **Auto-Creation:** Evidence Packs werden automatisch bei Layer Runs erstellt
- **Validation:** Deterministisch, reproduzierbar, lokal testbar
- **Artifacts:** CI-Artefakte (JSON reports, validation summaries)
- **No Breaking Changes:** Keine Änderungen an Trading/Execution-Logik

---

## How It Works

### 1. Evidence Pack Runtime Helper

**Module:** `src/ai_orchestration/evidence_pack_runtime.py`

Der Runtime Helper stellt Lifecycle-Management für Evidence Packs bereit:

```python
from src.ai_orchestration.evidence_pack_runtime import EvidencePackRuntime
from src.ai_orchestration.models import AutonomyLevel

# Initialize runtime
runtime = EvidencePackRuntime(output_dir=".artifacts/evidence_packs")

# Start run
run_id = "run-001"
pack = runtime.start_run(
    run_id=run_id,
    layer_id="L0",
    autonomy_level=AutonomyLevel.REC,
    description="Example layer run"
)

# Add layer run metadata (optional)
runtime.add_layer_run_metadata(
    run_id=run_id,
    layer_name="Ops/Docs Tooling",
    primary_model_id="gpt-5-2-pro",
    critic_model_id="deepseek-r1",
    capability_scope_id="L0_RO_REC_PROP",
    matrix_version="v1.0"
)

# Add run logs (optional)
runtime.add_run_log(
    run_id=run_id,
    log_run_id="log-001",
    prompt_hash="abc123...",
    artifact_hash="def456...",
    inputs_manifest=["input.txt"],
    outputs_manifest=["output.txt"],
    model_id="gpt-5-2-pro"
)

# Finish run
runtime.finish_run(run_id=run_id, status="success", tests_passed=5, tests_total=5)

# Save pack
pack_path = runtime.save_pack(run_id=run_id)
# Saved to: .artifacts/evidence_packs/<run_id>/evidence_pack.json
```

**Auto-Tracked Metadata:**
- `run_id`: Unique run ID
- `layer_id`: Layer ID (L0-L6)
- `git_sha`: Git commit SHA (from `GITHUB_SHA` env var or `git rev-parse HEAD`)
- `started_at`: ISO8601 timestamp
- `finished_at`: ISO8601 timestamp
- `status`: Run status (success, failure, error)
- `config_fingerprint`: SHA256 of all config/*.toml files
- `artifacts`: List of artifact paths
- `validator_version`: Model registry version

---

### 2. CI Validation Script

**Script:** `scripts/validate_evidence_pack_ci.py`

Validiert alle Evidence Packs in einem Verzeichnis (default: `.artifacts/evidence_packs`).

**Usage:**

```bash
# Validate all packs (strict mode)
python scripts/validate_evidence_pack_ci.py --root .artifacts/evidence_packs

# Verbose output
python scripts/validate_evidence_pack_ci.py --root .artifacts/evidence_packs --verbose

# Generate JSON report
python scripts/validate_evidence_pack_ci.py \
  --root .artifacts/evidence_packs \
  --output validation_report.json
```

**Exit Codes:**
- `0`: All packs valid
- `1`: One or more packs invalid
- `2`: No packs found or invalid arguments

**Output:**

```
🔍 Discovering Evidence Packs in: .artifacts/evidence_packs
   Found 3 Evidence Pack(s)

📦 Validating Evidence Packs...
   Mode: STRICT

================================================================================
Evidence Pack CI Validation Report
================================================================================
Timestamp: 2026-01-08T12:00:00Z
Total Packs: 3
Valid Packs: 3
Invalid Packs: 0
Success Rate: 100.0%
================================================================================

✅ ALL PACKS VALID
================================================================================
```

---

### 3. Smoke Run Script

**Script:** `scripts/run_layer_smoke_with_evidence_pack.py`

Erstellt einen minimalen Evidence Pack als Smoke Test.

**Usage:**

```bash
# Default: L0, REC
python scripts/run_layer_smoke_with_evidence_pack.py

# Specify layer and autonomy
python scripts/run_layer_smoke_with_evidence_pack.py --layer L1 --autonomy PROP

# Verbose output
python scripts/run_layer_smoke_with_evidence_pack.py --verbose
```

**Exit Codes:**
- `0`: Smoke run successful, pack valid
- `1`: Smoke run failed or pack invalid

---

### 4. CI Workflow

**Workflow:** `.github/workflows/evidence_pack_gate.yml`

**Jobs:**

1. **`changes`** (Path Detection):
   - Detects Evidence Pack code changes
   - Allows graceful skipping on unrelated PRs
   - Paths monitored:
     - `src/ai_orchestration/**`
     - `scripts/validate_evidence_pack_ci.py`
     - `scripts/run_layer_smoke_with_evidence_pack.py`
     - `tests/ai_orchestration/test_evidence_pack*.py`
     - `.github/workflows/evidence_pack_gate.yml`
     - `requirements.txt`

2. **`evidence-pack-smoke-run`**:
   - Erstellt minimalen Evidence Pack via smoke test
   - Uploaded pack als CI artifact
   - Timeout: 5 minutes
   - **Path-Aware:** Skips gracefully if Evidence Pack code unchanged (on PRs)

3. **`evidence-pack-validation-gate`** (REQUIRED CHECK):
   - Validiert alle Evidence Packs
   - Generiert GitHub Actions Summary (visible in PR UI)
   - Uploaded validation reports + Evidence Packs als CI artifacts
   - Failt bei invaliden Packs
   - Timeout: 10 minutes
   - **Path-Aware:** Skips gracefully if Evidence Pack code unchanged (on PRs)
   - **Always Created:** Job runs even if skipped (satisfies required check contract)

**Trigger:**
- Push to `main`/`master`
- Pull requests
- Merge groups
- Manual dispatch

**Artifacts:**
- `evidence-packs`: Generated Evidence Packs (from smoke run)
- `evidence-pack-validation-report`: JSON validation report (full details)
- `evidence-pack-validation-summary`: Text summary (console output)
- `evidence-packs-validated`: Evidence Packs after validation
- Retention: 30 days

**GitHub Actions Summary:**
- Visible in PR UI (Actions tab → Workflow run → Summary)
- Shows: Total packs, valid packs, invalid packs, success rate
- Lists invalid packs with errors (if any)

---

## How to Run Locally

### 1. Create Evidence Pack (Minimal)

```bash
python scripts/run_layer_smoke_with_evidence_pack.py --verbose
```

### 2. Validate Evidence Packs

```bash
python scripts/validate_evidence_pack_ci.py \
  --root .artifacts/evidence_packs \
  --verbose
```

### 3. Run Tests

```bash
# Run CI gate tests only
python -m pytest -q tests/ai_orchestration/test_evidence_pack_ci_gate.py

# Run all Evidence Pack tests
python -m pytest -q tests/ai_orchestration/test_evidence_pack*.py
```

---

## Failure Modes & Troubleshooting

### 1. No Evidence Packs Found

**Symptom:** CI validation fails with "No Evidence Packs found"

**Cause:** Smoke run didn't create pack, or pack was not uploaded as artifact

**Fix:**
1. Check smoke run output: Did it create `.artifacts/evidence_packs/<run_id>/evidence_pack.json`?
2. Check CI artifacts: Was `evidence-packs` artifact uploaded?
3. Check `.gitignore`: `.artifacts/` should be ignored (not committed)
4. Check path-filtering: Did Evidence Pack code actually change? (if not, job gracefully skips)

**Where to Look:**
- GitHub Actions → Workflow run → `evidence-pack-smoke-run` job → Logs
- GitHub Actions → Workflow run → Artifacts → `evidence-packs`

### 2. Invalid Evidence Pack

**Symptom:** Validation fails with specific errors (e.g., "missing field", "SoD violation")

**Cause:** Pack missing mandatory fields or violates validation rules

**Fix:**
1. Check GitHub Actions Summary (visible in PR UI):
   - Lists invalid packs with errors
2. Download `evidence-pack-validation-report` artifact (JSON) for full details:
   - GitHub Actions → Workflow run → Artifacts → `evidence-pack-validation-report`
3. Run validation locally to reproduce:
   ```bash
   python scripts/validate_evidence_pack_ci.py \
     --root .artifacts/evidence_packs \
     --verbose
   ```
4. Fix pack creation logic in runtime helper or caller code

**Where to Look:**
- GitHub Actions → Workflow run → Summary (top of page)
- GitHub Actions → Workflow run → Artifacts → `evidence-pack-validation-report`

### 3. Git SHA Missing/Invalid

**Symptom:** Pack has `git_sha: "local-dev"` or invalid SHA

**Cause:** Not in git repo, or `GITHUB_SHA` env var not set (CI)

**Fix:**
- CI: Check that `GITHUB_SHA` is available (should be auto-set by GitHub Actions)
- Local: Ensure you're in a git repo, or accept `"local-dev"` as fallback

### 4. Config Fingerprint Mismatch

**Symptom:** Config fingerprint changes unexpectedly

**Cause:** Config files (`config/*.toml`) were modified

**Fix:**
- This is expected if config changed
- Review config changes in PR
- If unintentional, revert config changes

### 5. CI Check "Pending" or "Expected" (Missing)

**Symptom:** PR shows "evidence-pack-validation-gate" as "Expected" but never completes

**Cause:** Job has job-level `if:` condition, preventing job creation

**Fix:**
- This should NOT happen (workflow uses step-level `if:` only)
- If it does: Check workflow file for job-level `if:` conditions
- Workflow must always create jobs (even if they skip) for required check compatibility

**Where to Look:**
- PR → Checks tab → Look for `evidence-pack-validation-gate` status
- `.github/workflows/evidence_pack_gate.yml` → Verify no job-level `if:` conditions

### 6. Path-Filtering False Negative

**Symptom:** Evidence Pack code changed, but CI job skipped anyway

**Cause:** Path-filter doesn't match actual changed files

**Fix:**
1. Check which files changed in PR
2. Verify path-filter in `.github/workflows/evidence_pack_gate.yml`:
   ```yaml
   filters: |
     evidence_pack:
       - 'src/ai_orchestration/**'
       - 'scripts/validate_evidence_pack_ci.py'
       - 'scripts/run_layer_smoke_with_evidence_pack.py'
       - 'tests/ai_orchestration/test_evidence_pack*.py'
       - '.github/workflows/evidence_pack_gate.yml'
       - 'requirements.txt'
   ```
3. Add missing paths to filter if needed
4. Or: Manually trigger workflow with "workflow_dispatch"

**Where to Look:**
- GitHub Actions → Workflow run → `changes` job → Logs

---

## Integration with Layer Runs

### Minimal Integration (Thin Slice)

Phase 4A fokussiert auf **thin slice**: Keine DB, keine Query API (kommt in Phase 4B).

**Empfohlener Hook:**

```python
from src.ai_orchestration.evidence_pack_runtime import EvidencePackRuntime
from src.ai_orchestration.models import AutonomyLevel

def run_layer_with_evidence_pack(layer_id, autonomy_level, **kwargs):
    """
    Example: Wrapper für Layer Run mit Evidence Pack Auto-Creation.
    """
    runtime = EvidencePackRuntime()
    run_id = f"run-{uuid.uuid4().hex[:8]}"

    try:
        # Start run
        runtime.start_run(
            run_id=run_id,
            layer_id=layer_id,
            autonomy_level=autonomy_level,
            description=kwargs.get("description", ""),
        )

        # YOUR LAYER RUN LOGIC HERE
        # (model selection, execution, validation, etc.)

        # Optional: Add layer run metadata
        if "primary_model_id" in kwargs:
            runtime.add_layer_run_metadata(
                run_id=run_id,
                layer_name=kwargs["layer_name"],
                primary_model_id=kwargs["primary_model_id"],
                critic_model_id=kwargs["critic_model_id"],
                capability_scope_id=kwargs["capability_scope_id"],
                matrix_version=kwargs["matrix_version"],
            )

        # Finish run
        runtime.finish_run(
            run_id=run_id,
            status="success",
            tests_passed=kwargs.get("tests_passed", 0),
            tests_total=kwargs.get("tests_total", 0),
        )

        # Save pack
        pack_path = runtime.save_pack(run_id=run_id)
        print(f"Evidence Pack saved: {pack_path}")

    except Exception as e:
        runtime.finish_run(run_id=run_id, status="error")
        runtime.save_pack(run_id=run_id)
        raise
```

**Alternatively: Convenience Function**

```python
from src.ai_orchestration.evidence_pack_runtime import create_minimal_evidence_pack_for_run

# Quick one-liner for simple cases
pack_path = create_minimal_evidence_pack_for_run(
    run_id="run-001",
    layer_id="L0",
    autonomy_level=AutonomyLevel.REC,
    description="Quick test run",
)
```

---

## Paths & Conventions

### Evidence Pack Root

**Default:** `.artifacts/evidence_packs/`

**Structure:**

```
.artifacts/evidence_packs/
├── <run_id>/
│   ├── evidence_pack.json       # Evidence Pack (validated)
│   └── run_metadata.json        # Runtime metadata (git_sha, config fingerprint, etc.)
├── <run_id>/
│   ├── evidence_pack.json
│   └── run_metadata.json
└── ...
```

### Git SHA Tracking

**Sources (priority order):**
1. `GITHUB_SHA` environment variable (CI)
2. `git rev-parse HEAD` (local, if in git repo)
3. `"local-dev"` (fallback if not in git repo)

### Config Fingerprint

**Algorithm:**
1. Collect all `config/*.toml` files (sorted)
2. Concatenate file contents (sorted by path)
3. Compute SHA256 hex digest

**Purpose:**
- Detect config changes across runs
- Enable reproducibility checks
- Audit config drift

---

## Testing Strategy

### Unit Tests

**File:** `tests/ai_orchestration/test_evidence_pack_ci_gate.py`

**Coverage:**
- Runtime helper initialization
- Pack creation/validation
- Git SHA tracking
- Config fingerprinting
- Artifact tracking
- End-to-end CI gate flow

**Run:**

```bash
python -m pytest -q tests/ai_orchestration/test_evidence_pack_ci_gate.py
```

### Integration Tests

**Smoke Run (CI):**

```bash
python scripts/run_layer_smoke_with_evidence_pack.py --verbose
```

**CI Validation (Local):**

```bash
python scripts/validate_evidence_pack_ci.py \
  --root .artifacts/evidence_packs \
  --verbose
```

---

## CI Check Configuration (GitHub)

### Required Check Name

**Exact Check Name:** `evidence-pack-validation-gate`

**Format:** `workflow-name / job-name`

**Where to Configure:**
1. GitHub → Repository → Settings
2. Branches → Branch protection rules → `main` (or target branch)
3. "Require status checks to pass before merging" → Enable
4. Search for: `evidence-pack-validation-gate`
5. Select checkbox → Save

**Important:**
- Check name MUST match job name in workflow (line 78 in `.github/workflows/evidence_pack_gate.yml`)
- No matrix suffix (job is not a matrix job)
- Name is stable (no dynamic components)

---

## Rollback Plan

Falls CI Gate Probleme verursacht:

### Option A: Emergency Disable (No Code Change)

**GitHub UI (fastest):**
1. GitHub → Repository → Settings
2. Branches → Branch protection rules → `main`
3. Find `evidence-pack-validation-gate` in required checks
4. Uncheck checkbox
5. Save

**Duration:** 30 seconds  
**Risk:** None (reversible)

### Option B: Disable via Workflow (Code Change)

**Edit Workflow:**
1. Edit `.github/workflows/evidence_pack_gate.yml`
2. Add job-level `if: false` to `evidence-pack-validation-gate` job:
   ```yaml
   evidence-pack-validation-gate:
     name: evidence-pack-validation-gate
     if: false  # TEMPORARY DISABLE
     runs-on: ubuntu-latest
     ...
   ```
3. Commit and push

**Duration:** 2 minutes  
**Risk:** Low (reversible, but requires commit)

### Option C: Disable Entire Workflow

**Rename Workflow:**
1. Rename `.github/workflows/evidence_pack_gate.yml` to `.github/workflows/evidence_pack_gate.yml.disabled`
2. Commit and push

**Duration:** 2 minutes  
**Risk:** Low (reversible, but requires commit)

### Investigate & Fix

1. **Check CI Artifacts:**
   - Download `evidence-pack-validation-report` (JSON)
   - Download `evidence-pack-validation-summary` (text)
   - Review GitHub Actions Summary

2. **Reproduce Locally:**
   ```bash
   python scripts/run_layer_smoke_with_evidence_pack.py --verbose
   python scripts/validate_evidence_pack_ci.py --root .artifacts/evidence_packs --verbose
   ```

3. **Fix Root Cause:**
   - Fix runtime helper (`src/ai_orchestration/evidence_pack_runtime.py`)
   - Fix validation logic (`src/ai_orchestration/evidence_pack.py`)
   - Fix validation script (`scripts/validate_evidence_pack_ci.py`)
   - Test locally (17 unit tests + smoke run)

4. **Re-Enable:**
   - Option A: Re-check required check in GitHub UI
   - Option B: Remove `if: false` from workflow
   - Option C: Rename workflow back to `.yml`

---

## Risks & Mitigations

### Risk: CI Gate False Positives

**Mitigation:**
- Strict validation mode (fail-closed)
- Local reproducibility (scripts)
- Detailed validation reports (JSON artifacts)

### Risk: Performance Impact

**Mitigation:**
- Smoke run timeout: 5 minutes
- Validation timeout: 10 minutes
- Minimal pack creation (no heavy I/O)

### Risk: Breaking Changes

**Mitigation:**
- No changes to trading/execution logic
- Evidence Pack creation is **opt-in** via runtime helper
- Existing code paths unchanged

---

## Next Steps (Phase 4B)

Phase 4B wird folgende Features hinzufügen:

1. **Evidence Pack Query API:**
   - Search by run_id, layer_id, git_sha, etc.
   - Temporal queries (last N days, etc.)

2. **Evidence Pack Index:**
   - SQLite index for fast queries
   - Incremental indexing

3. **Dashboard Integration:**
   - Ops Doctor dashboard integration
   - Evidence Pack timeline view

4. **Advanced Validation:**
   - Cross-pack validation (SoD checks across runs)
   - Drift detection (config, models, etc.)

---

## References

- **Phase 3B:** Evidence Pack Validator (`docs/ops/PHASE3B_EVIDENCE_PACK_QUICKSTART.md`)
- **AI Autonomy Layer Map:** `docs/architecture/ai_autonomy_layer_map_v1.md`
- **Model Registry:** `config/model_registry.toml`
- **Capability Scopes:** `config/capability_scopes/*.toml`

---

## Contact

Bei Fragen oder Problemen:
- Check CI artifacts: `evidence-pack-validation-report` (JSON)
- Run locally: `scripts/validate_evidence_pack_ci.py --verbose`
- Review docs: `docs/ai/EVIDENCE_PACK_CI_GATE.md` (dieses Dokument)
