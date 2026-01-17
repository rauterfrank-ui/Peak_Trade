# Phase 4E Quickstart: Validator Report Normalization

**Target Audience:** Operators, CI maintainers  
**Time to Complete:** 5 minutes  
**Prerequisites:** Phase 4D determinism contract validator

---

## What is This?

Phase 4E standardizes validator reports into a **machine-readable, deterministic format** for:
- ✅ Automated health checks
- ✅ Trend analysis
- ✅ CI artifact consistency
- ✅ Forward compatibility

---

## Quick Start

### 1. Normalize a Report

```bash
# From file
python scripts/aiops/normalize_validator_report.py \
  --input .tmp/validator_report.json \
  --out-dir .tmp/normalized

# From stdin
cat validator_report.json | python scripts/aiops/normalize_validator_report.py \
  --out-dir .tmp/normalized
```

**Outputs:**
- `validator_report.normalized.json` (canonical, deterministic)
- `validator_report.normalized.md` (human-readable summary)

---

### 2. CI Mode (with runtime context)

```bash
python scripts/aiops/normalize_validator_report.py \
  --input .tmp/validator_report.json \
  --out-dir .tmp/normalized \
  --git-sha "${GITHUB_SHA}" \
  --run-id "${GITHUB_RUN_ID}" \
  --workflow "${GITHUB_WORKFLOW}" \
  --job "${GITHUB_JOB}" \
  --timestamp
```

**Note:** Runtime context is **excluded** from canonical JSON (deterministic mode).

---

### 3. Verify Determinism

```bash
# Run twice
python scripts/aiops/normalize_validator_report.py \
  --input report.json --out-dir .tmp/run1
python scripts/aiops/normalize_validator_report.py \
  --input report.json --out-dir .tmp/run2

# Compare (should be identical)
diff .tmp/run1/validator_report.normalized.json \
     .tmp/run2/validator_report.normalized.json

# Expected: no differences
```

---

## Common Use Cases

### Inspect a Normalized Report

```bash
# JSON (canonical)
jq . .tmp/normalized/validator_report.normalized.json

# Markdown (human-readable)
cat .tmp/normalized/validator_report.normalized.md
```

### Extract Key Metrics

```bash
# Overall result
jq -r '.result' validator_report.normalized.json
# Output: PASS or FAIL

# Summary
jq '.summary' validator_report.normalized.json
# Output: {"passed": 1, "failed": 0, "total": 1}

# Check details
jq '.checks[] | "\(.id): \(.status)"' validator_report.normalized.json
# Output: determinism_contract_validation: PASS
```

### Download from CI

```bash
# List artifacts
gh run view <run-id>

# Download normalized report
gh run download <run-id> -n validator-report-normalized-<run-id>

# Inspect
jq . validator_report.normalized.json
cat validator_report.normalized.md
```

---

## Schema Overview

### Top-Level Structure

```json
{
  "schema_version": "1.0.0",
  "tool": {"name": "...", "version": "..."},
  "subject": "l4_critic_determinism_contract_v1.0.0",
  "result": "PASS",
  "checks": [...],
  "summary": {"passed": 1, "failed": 0, "total": 1},
  "evidence": {...},
  "runtime_context": {...}  // Excluded in deterministic mode
}
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Schema version (v1.0.0) |
| `result` | enum | PASS/FAIL/ERROR |
| `checks[]` | array | Individual checks (sorted by id) |
| `summary` | object | Metrics (passed/failed/total) |
| `evidence` | object | Baseline/candidate paths |
| `runtime_context` | object | Volatile (git SHA, run ID, etc.) |

---

## CLI Options

| Flag | Description |
|------|-------------|
| `--input PATH` | Input validator report (JSON). Omit for stdin. |
| `--out-dir PATH` | Output directory (required) |
| `--git-sha SHA` | Git commit SHA (runtime context) |
| `--run-id ID` | CI run ID (runtime context) |
| `--workflow NAME` | CI workflow name (runtime context) |
| `--job NAME` | CI job name (runtime context) |
| `--timestamp` | Add generation timestamp |
| `--no-markdown` | Skip Markdown summary |
| `--quiet` | Suppress output |

---

## Troubleshooting

### Error: "Invalid JSON input"

**Cause:** Input file is not valid JSON.

**Fix:**
```bash
# Validate JSON
jq . input.json

# Check for syntax errors
python -m json.tool input.json
```

### Error: "Input file not found"

**Cause:** File path is incorrect.

**Fix:**
```bash
# Check file exists
ls -lh .tmp/validator_report.json

# Use absolute path
python scripts/aiops/normalize_validator_report.py \
  --input "$(pwd)/.tmp/validator_report.json" \
  --out-dir .tmp/normalized
```

### Non-deterministic Outputs

**Symptom:** Two runs produce different JSON.

**Cause:** Runtime context included in canonical mode (bug).

**Fix:**
```bash
# Verify runtime_context is excluded
jq 'has("runtime_context")' .tmp/normalized/validator_report.normalized.json
# Expected: false (in deterministic mode)

# If true, file a bug report
```

---

## Testing

### Run All Tests

```bash
pytest tests/ai_orchestration/test_validator_report_normalized.py \
       tests/ai_orchestration/test_normalize_validator_report_cli.py -v
```

**Expected:** 31 tests passed

### Run Specific Test

```bash
# Schema validation
pytest tests/ai_orchestration/test_validator_report_normalized.py::test_validator_report_schema_valid -v

# Determinism check
pytest tests/ai_orchestration/test_validator_report_normalized.py::test_determinism_golden_fixture -v

# CLI integration
pytest tests/ai_orchestration/test_normalize_validator_report_cli.py::test_cli_full_pipeline -v
```

---

## CI Integration

### Workflow: `l4_critic_replay_determinism_v2.yml`

**New Steps:**
1. **Normalize validator report** (Phase 4E)
2. **Upload normalized artifacts** (JSON + Markdown)
3. **Upload legacy artifact** (backward compatibility)

**Artifacts:**
- `validator-report-normalized-<run_id>` (JSON + Markdown)
- `validator-report-legacy-<run_id>` (Phase 4D format)

**Retention:** 14 days

---

## References

- **Full Spec:** [PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md](PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md)
- **Phase 4D:** [L4 Critic Determinism Contract](PHASE4D_L4_CRITIC_DETERMINISM_CONTRACT.md)
- **CLI Help:** `python scripts/aiops/normalize_validator_report.py --help`

---

## Examples

### Example 1: Basic Normalization

```bash
# Input: Phase 4D validator report
cat .tmp/validator_report.json
# {
#   "validator": {"name": "...", "version": "1.0.0"},
#   "contract_version": "1.0.0",
#   "result": {"equal": true, ...}
# }

# Normalize
python scripts/aiops/normalize_validator_report.py \
  --input .tmp/validator_report.json \
  --out-dir .tmp/normalized

# Output: Normalized report
cat .tmp/normalized/validator_report.normalized.json
# {
#   "schema_version": "1.0.0",
#   "result": "PASS",
#   "checks": [...],
#   "summary": {"passed": 1, "failed": 0, "total": 1}
# }
```

### Example 2: CI Integration

```yaml
# .github/workflows/example.yml
- name: Normalize validator report
  run: |
    python scripts/aiops/normalize_validator_report.py \
      --input .tmp/validator_report.json \
      --out-dir .tmp/normalized \
      --git-sha "${{ github.sha }}" \
      --run-id "${{ github.run_id }}" \
      --workflow "${{ github.workflow }}" \
      --job "${{ github.job }}" \
      --timestamp

- name: Upload normalized report
  uses: actions/upload-artifact@v4
  with:
    name: validator-report-normalized-${{ github.run_id }}
    path: |
      .tmp/normalized/validator_report.normalized.json
      .tmp/normalized/validator_report.normalized.md
```

### Example 3: Automated Health Check

```python
import json
from pathlib import Path

# Load normalized report
data = json.loads(Path(".tmp/normalized/validator_report.normalized.json").read_text())

# Check result
if data["result"] == "PASS":
    print("✅ All checks passed")
    exit(0)
else:
    print(f"❌ {data['summary']['failed']} checks failed")
    for check in data["checks"]:
        if check["status"] == "FAIL":
            print(f"  - {check['id']}: {check['message']}")
    exit(1)
```

---

**Phase 4E Quickstart Complete** ✅

For detailed information, see [PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md](PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md).
