# Phase 4E: Validator Report Normalization

**Status:** Implemented  
**Phase:** 4E  
**Deliverable:** Normalized, versioned validator report schema + CLI + CI integration

---

## Purpose

Standardize validator/determinism reports to enable:
- **Machine-readable** health/trend automation
- **Deterministic** outputs (byte-identical, stable hashing)
- **Schema-versioned** format for forward compatibility
- **CI-ready** artifacts (JSON primary, Markdown derived)

---

## Problem Statement

Phase 4D introduced determinism contract validation, but reports were:
- Semi-structured (Markdown-heavy)
- Inconsistent field names/optionality
- Difficult to parse for automated health checks
- No clear separation of canonical vs volatile data

---

## Solution: Normalized Report Format

### Design Principles

1. **Schema-first**: JSON is canonical, Markdown is derived
2. **Deterministic**: Sorted keys, stable list ordering, no volatile fields in canonical section
3. **Versioned**: `schema_version` field for evolution
4. **Evidence-first**: Clear separation of canonical data vs runtime context
5. **Backward compatible**: Supports legacy Phase 4D reports via adapter

---

## Schema (v1.0.0)

### Top-Level Structure

```json
{
  "schema_version": "1.0.0",
  "tool": {
    "name": "l4_critic_determinism_contract_validator",
    "version": "1.0.0"
  },
  "subject": "l4_critic_determinism_contract_v1.0.0",
  "result": "PASS",
  "checks": [...],
  "summary": {...},
  "evidence": {...},
  "runtime_context": {...}
}
```

### Required Fields (Canonical)

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Schema version (semver) |
| `tool` | object | Tool name + version |
| `subject` | string | Subject being validated |
| `result` | enum | Overall result: PASS/FAIL/ERROR |
| `checks[]` | array | Individual checks (sorted by id) |
| `summary` | object | Summary metrics (passed/failed/total) |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `evidence` | object | Evidence references (baseline/candidate/diff paths) |
| `runtime_context` | object | Volatile runtime data (excluded from canonical hash) |

### Checks Array

Each check has:
- `id` (string): Stable check ID (snake_case)
- `status` (enum): PASS/FAIL/SKIP
- `message` (string): Short message
- `metrics` (object, optional): Deterministic metrics only

**Example:**
```json
{
  "id": "determinism_contract_validation",
  "status": "PASS",
  "message": "Reports are identical (0 diffs)",
  "metrics": {
    "baseline_hash": "abc123...",
    "candidate_hash": "abc123...",
    "first_mismatch_path": null
  }
}
```

### Runtime Context (Volatile)

Isolated section for volatile fields:
- `git_sha`
- `run_id`
- `workflow`
- `job`
- `generated_at_utc`

**Canonicalization Rule:** `runtime_context` is **excluded** from canonical dict and hash computation.

---

## Canonicalization Rules

1. **Sort dict keys** (lexicographic)
2. **Sort checks array** by `id` (stable ordering)
3. **Exclude runtime_context** from canonical representation
4. **Stable JSON formatting**:
   - 2-space indentation
   - UTF-8 encoding
   - Trailing newline
   - `sort_keys=True`

---

## CLI Usage

### Basic Normalization

```bash
# From file
python scripts/aiops/normalize_validator_report.py \
  --input .tmp/validator_report.json \
  --out-dir .tmp/normalized

# From stdin
cat validator_report.json | python scripts/aiops/normalize_validator_report.py \
  --out-dir .tmp/normalized
```

### CI Mode (with runtime context)

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

### Options

| Flag | Description |
|------|-------------|
| `--input PATH` | Input validator report (JSON). If omitted, reads from stdin. |
| `--out-dir PATH` | Output directory (required) |
| `--git-sha SHA` | Git commit SHA (runtime context) |
| `--run-id ID` | CI run ID (runtime context) |
| `--workflow NAME` | CI workflow name (runtime context) |
| `--job NAME` | CI job name (runtime context) |
| `--timestamp` | Add generation timestamp to runtime context |
| `--no-markdown` | Skip Markdown summary generation |
| `--quiet` | Suppress output (exit code only) |

### Exit Codes

- `0`: Success
- `1`: Invalid input / processing error

---

## Outputs

### Primary: `validator_report.normalized.json`

Canonical, deterministic JSON:
- Sorted keys
- Stable list ordering
- No volatile fields (runtime_context excluded in deterministic mode)
- Byte-identical across runs (same input → same output)

### Derived: `validator_report.normalized.md`

Human-readable Markdown summary:
- Generated from JSON (not a source of truth)
- Includes all sections (summary, checks, evidence, runtime context)
- Emoji indicators (✅ PASS, ❌ FAIL)

---

## CI Integration

### Workflow: `.github/workflows/l4_critic_replay_determinism_v2.yml`

**New Steps (Phase 4E):**

1. **Normalize validator report**
   - Runs after determinism contract validation
   - Adds runtime context (git SHA, run ID, workflow, job, timestamp)
   - Produces normalized JSON + Markdown

2. **Upload normalized artifacts**
   - Artifact name: `validator-report-normalized-<run_id>`
   - Contents: `validator_report.normalized.json` + `.md`
   - Retention: 14 days

3. **Upload legacy artifact** (backward compatibility)
   - Artifact name: `validator-report-legacy-<run_id>`
   - Contents: `validator_report.json` (Phase 4D format)
   - Retention: 14 days

**Trigger:** Same as existing workflow (PRs/pushes touching AI orchestration code)

---

## Determinism Verification

### Local Test

```bash
# Run normalization twice
python scripts/aiops/normalize_validator_report.py \
  --input report.json --out-dir .tmp/run1
python scripts/aiops/normalize_validator_report.py \
  --input report.json --out-dir .tmp/run2

# Compare (should be byte-identical)
diff .tmp/run1/validator_report.normalized.json \
     .tmp/run2/validator_report.normalized.json

# Verify hash stability
sha256sum .tmp/run1/validator_report.normalized.json
sha256sum .tmp/run2/validator_report.normalized.json
```

### Programmatic Check

```python
from src.ai_orchestration.validator_report_normalized import (
    normalize_validator_report,
    hash_normalized_report,
    validate_determinism,
)

# Normalize twice
report1 = normalize_validator_report(raw_report)
report2 = normalize_validator_report(raw_report)

# Verify determinism
assert validate_determinism(report1, report2) is True

# Verify hash stability
hash1 = hash_normalized_report(report1)
hash2 = hash_normalized_report(report2)
assert hash1 == hash2
```

---

## Backward Compatibility

### Legacy Report Adapter

The normalizer includes a built-in adapter for Phase 4D reports:

```python
from src.ai_orchestration.validator_report_schema import ValidatorReport

# Automatic conversion from legacy format
normalized = ValidatorReport.from_legacy_validator_report(
    legacy_report=phase4d_report_dict,
    runtime_context={"git_sha": "abc123"},
)
```

**Supported Legacy Format:**
- Phase 4D validator reports (from `validate_l4_critic_determinism_contract.py`)
- Fields: `validator`, `contract_version`, `inputs`, `result`

---

## Testing

### Test Coverage

**Unit Tests:** `tests/ai_orchestration/test_validator_report_normalized.py` (21 tests)
- Schema validation
- Legacy report conversion
- Deterministic serialization
- Hash stability
- I/O operations

**CLI Tests:** `tests/ai_orchestration/test_normalize_validator_report_cli.py` (10 tests)
- CLI argument parsing
- File/stdin input
- Runtime context handling
- Error handling
- Determinism verification

**Total:** 31 tests, all passing

### Run Tests

```bash
# Unit tests
pytest tests/ai_orchestration/test_validator_report_normalized.py -v

# CLI tests
pytest tests/ai_orchestration/test_normalize_validator_report_cli.py -v

# All tests
pytest tests/ai_orchestration/test_validator_report_normalized.py \
       tests/ai_orchestration/test_normalize_validator_report_cli.py -v
```

---

## Consumer Guide

### Use Case 1: Automated Health Checks

```python
import json
from pathlib import Path

# Load normalized report
report_path = Path(".tmp/validator_report_normalized/validator_report.normalized.json")
data = json.loads(report_path.read_text())

# Check overall result
if data["result"] == "PASS":
    print("✅ All checks passed")
else:
    print(f"❌ Validation failed: {data['summary']['failed']} checks failed")

# Inspect individual checks
for check in data["checks"]:
    print(f"  {check['id']}: {check['status']} - {check['message']}")
```

### Use Case 2: Trend Analysis

```python
import json
from pathlib import Path
from collections import defaultdict

# Collect reports from multiple runs
reports = []
for report_file in Path("artifacts/").glob("**/validator_report.normalized.json"):
    reports.append(json.loads(report_file.read_text()))

# Analyze trends
pass_rate = sum(1 for r in reports if r["result"] == "PASS") / len(reports)
print(f"Pass rate: {pass_rate:.1%}")

# Check-level trends
check_stats = defaultdict(lambda: {"pass": 0, "fail": 0})
for report in reports:
    for check in report["checks"]:
        check_stats[check["id"]][check["status"].lower()] += 1

for check_id, stats in check_stats.items():
    total = stats["pass"] + stats["fail"]
    pass_rate = stats["pass"] / total if total > 0 else 0
    print(f"{check_id}: {pass_rate:.1%} pass rate ({stats['pass']}/{total})")
```

### Use Case 3: CI Artifact Download

```bash
# Download normalized report from CI
gh run download <run-id> -n validator-report-normalized-<run-id>

# Inspect JSON
jq . validator_report.normalized.json

# Read Markdown
cat validator_report.normalized.md
```

---

## Files Delivered

### Source Code

1. **Schema:** `src/ai_orchestration/validator_report_schema.py` (400 lines)
   - Pydantic models (ValidatorReport, ValidationCheck, etc.)
   - Canonical serialization methods
   - Legacy adapter

2. **Normalizer:** `src/ai_orchestration/validator_report_normalized.py` (150 lines)
   - Normalization functions
   - Hash computation
   - Determinism validation

3. **CLI:** `scripts/aiops/normalize_validator_report.py` (250 lines)
   - Command-line interface
   - Runtime context handling
   - Input/output management

### Tests

4. **Unit Tests:** `tests/ai_orchestration/test_validator_report_normalized.py` (400 lines, 21 tests)
5. **CLI Tests:** `tests/ai_orchestration/test_normalize_validator_report_cli.py` (250 lines, 10 tests)

### Fixtures

6. **Legacy Report:** `tests/fixtures/validator_reports/legacy_report_pass.json`
7. **Golden Normalized:** `tests/fixtures/validator_reports/normalized_report_pass.golden.json`

### CI Integration

8. **Workflow Update:** `.github/workflows/l4_critic_replay_determinism_v2.yml` (3 new steps)

### Documentation

9. **Specification:** `docs/governance/ai_autonomy/PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md` (this file)

---

## Risk Assessment

### Risk Level: **LOW**

**Rationale:**
- Reporting/CI artifacts only (no trading logic)
- No strategy/config/risk changes
- Backward compatible (legacy reports still uploaded)
- Additive changes (new artifacts, no removals)

### Rollback Strategy

If issues arise:
1. Revert CI workflow changes (remove normalization step)
2. Legacy artifacts remain available
3. No impact on existing determinism validation

---

## Verification Checklist

- [x] Schema defined and versioned (v1.0.0)
- [x] Normalizer implemented with legacy adapter
- [x] CLI script with full argument support
- [x] 31 tests passing (unit + CLI)
- [x] Determinism verified (byte-identical outputs)
- [x] CI integration (artifacts uploaded)
- [x] Documentation complete (spec + consumer guide)
- [x] Golden fixtures created
- [x] Backward compatibility maintained

---

## Future Enhancements (Out of Scope for Phase 4E)

1. **Multi-validator support**: Normalize reports from other validators (not just L4 critic)
2. **Trend dashboard**: Automated visualization of validator health over time
3. **Alert thresholds**: Configurable alerts for pass rate degradation
4. **Schema evolution**: v1.1.0+ with additional fields (e.g., performance metrics)

---

## References

- **Phase 4D:** [L4 Critic Determinism Contract](PHASE4D_L4_CRITIC_DETERMINISM_CONTRACT.md)
- **Phase 4C:** [Critic Hardening](PHASE4C_CRITIC_HARDENING.md)
- **Validator CLI:** `scripts/aiops/validate_l4_critic_determinism_contract.py`
- **CI Workflow:** `.github/workflows/l4_critic_replay_determinism_v2.yml`

---

## Operator Quick Reference

### Normalize a Report

```bash
python scripts/aiops/normalize_validator_report.py \
  --input .tmp/validator_report.json \
  --out-dir .tmp/normalized
```

### Verify Determinism

```bash
# Run twice
for i in 1 2; do
  python scripts/aiops/normalize_validator_report.py \
    --input report.json --out-dir .tmp/run$i
done

# Compare
diff .tmp/run1/validator_report.normalized.json \
     .tmp/run2/validator_report.normalized.json
```

### Inspect Normalized Report

```bash
# JSON (canonical)
jq . .tmp/normalized/validator_report.normalized.json

# Markdown (human-readable)
cat .tmp/normalized/validator_report.normalized.md
```

### Run Tests

```bash
pytest tests/ai_orchestration/test_validator_report_normalized.py \
       tests/ai_orchestration/test_normalize_validator_report_cli.py -v
```

---

**Phase 4E Complete** ✅
