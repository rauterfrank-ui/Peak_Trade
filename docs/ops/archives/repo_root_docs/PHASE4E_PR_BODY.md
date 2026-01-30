# Phase 4E: Validator Report Normalization

## Summary

Standardizes validator/determinism reports into a **normalized, versioned, machine-readable format** for automated health checks and trend analysis.

**Key Deliverable:** Schema v1.0.0 + Normalizer + CLI + CI integration + 31 tests (100% pass rate)

---

## Why

Phase 4D introduced determinism contract validation, but reports were:
- Semi-structured (Markdown-heavy)
- Inconsistent field names/optionality
- Difficult to parse for automated health checks
- No clear separation of canonical vs volatile data

**Solution:** Normalized JSON schema with deterministic serialization, stable hashing, and CI-ready artifacts.

---

## Changes

### 1. Schema & Models (`validator_report_schema.py`)
- Pydantic models: ValidatorReport, ValidationCheck, SummaryMetrics, Evidence, RuntimeContext
- Schema version: v1.0.0
- Canonical serialization (sorted keys, stable list ordering)
- Legacy adapter for Phase 4D reports

### 2. Normalizer (`validator_report_normalized.py`)
- Convert legacy reports to normalized format
- Deterministic hash computation (excludes runtime_context)
- Validation functions (determinism checks)

### 3. CLI Script (`normalize_validator_report.py`)
- File or stdin input
- Runtime context injection (git SHA, run ID, workflow, job, timestamp)
- Deterministic mode (default)
- Exit codes: 0 (success), 1 (error)

### 4. CI Integration (`.github/workflows/l4_critic_replay_determinism_v2.yml`)
- New step: Normalize validator report (Phase 4E)
- Upload normalized artifacts (JSON + Markdown)
- Upload legacy artifact (backward compatibility)

### 5. Tests (31 tests, 100% pass rate)
- `test_validator_report_normalized.py` (21 tests)
- `test_normalize_validator_report_cli.py` (10 tests)
- Coverage: schema validation, determinism, I/O, CLI integration

### 6. Documentation
- Full spec: `PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md`
- Quickstart: `PHASE4E_QUICKSTART.md`
- Consumer guide (health checks, trend analysis)

---

## Verification

### Tests
```bash
python3 -m pytest tests/ai_orchestration/test_validator_report_normalized.py \
       tests/ai_orchestration/test_normalize_validator_report_cli.py -v
```
**Result:** ✅ 31 tests passed in 1.55s

### Determinism
```bash
# Run normalization twice
python3 scripts/aiops/normalize_validator_report.py \
  --input tests/fixtures/validator_reports/legacy_report_pass.json \
  --out-dir .tmp/run1 --quiet

python3 scripts/aiops/normalize_validator_report.py \
  --input tests/fixtures/validator_reports/legacy_report_pass.json \
  --out-dir .tmp/run2 --quiet

# Compare
diff .tmp/run1/validator_report.normalized.json \
     .tmp/run2/validator_report.normalized.json
```
**Result:** ✅ Outputs are byte-identical

**SHA256 Hashes:**
```
84fb7568af8764b2f1240d3bc76f021ba7f6377193ad09e45cf8d7e18d616743  run1/validator_report.normalized.json
84fb7568af8764b2f1240d3bc76f021ba7f6377193ad09e45cf8d7e18d616743  run2/validator_report.normalized.json
```

---

## Risk Assessment

**Risk Level:** LOW

**Rationale:**
- ✅ Reporting/CI artifacts only (no trading logic)
- ✅ No strategy/config/risk changes
- ✅ Backward compatible (legacy reports still uploaded)
- ✅ Additive changes (new artifacts, no removals)
- ✅ Comprehensive test coverage (31 tests)
- ✅ Determinism verified (byte-identical outputs)

**Scope Verification:**
- ✅ Changed: `src/ai_orchestration/`, `scripts/aiops/`, `tests/`, `.github/workflows/`, `docs/`
- ✅ NOT changed: Trading/execution logic, strategy configs, risk management, portfolio management

---

## How to Use

### Basic Normalization
```bash
python3 scripts/aiops/normalize_validator_report.py \
  --input .tmp/validator_report.json \
  --out-dir .tmp/normalized
```

### CI Mode (with runtime context)
```bash
python3 scripts/aiops/normalize_validator_report.py \
  --input .tmp/validator_report.json \
  --out-dir .tmp/normalized \
  --git-sha "${GITHUB_SHA}" \
  --run-id "${GITHUB_RUN_ID}" \
  --workflow "${GITHUB_WORKFLOW}" \
  --job "${GITHUB_JOB}" \
  --timestamp
```

### Inspect Normalized Report
```bash
# JSON (canonical)
jq . .tmp/normalized/validator_report.normalized.json

# Markdown (human-readable)
cat .tmp/normalized/validator_report.normalized.md
```

---

## Files Changed

**Total:** 14 files (~2350 lines)

**Source Code:** 3 files
- `src/ai_orchestration/validator_report_schema.py` (400 lines)
- `src/ai_orchestration/validator_report_normalized.py` (150 lines)
- `scripts/aiops/normalize_validator_report.py` (250 lines)

**Tests:** 2 files (31 tests)
- `tests/ai_orchestration/test_validator_report_normalized.py` (21 tests)
- `tests/ai_orchestration/test_normalize_validator_report_cli.py` (10 tests)

**Fixtures:** 2 files
- `tests/fixtures/validator_reports/legacy_report_pass.json`
- `tests/fixtures/validator_reports/normalized_report_pass.golden.json`

**CI Integration:** 1 file
- `.github/workflows/l4_critic_replay_determinism_v2.yml` (3 new steps)

**Documentation:** 2 files
- `docs/governance/ai_autonomy/PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md` (600 lines)
- `docs/governance/ai_autonomy/PHASE4E_QUICKSTART.md` (300 lines)

**Summary Reports:** 4 files
- `PHASE4E_IMPLEMENTATION_SUMMARY.md`
- `PHASE4E_CHANGED_FILES.txt`
- `PHASE4E_PR_BODY.md`
- `PHASE4E_MERGE_LOG.md` (to be created post-merge)

See: `PHASE4E_CHANGED_FILES.txt`

---

## References

- **Phase 4D:** [L4 Critic Determinism Contract](docs/governance/ai_autonomy/PHASE4D_L4_CRITIC_DETERMINISM_CONTRACT.md)
- **Phase 4C:** [Critic Hardening](docs/governance/ai_autonomy/PHASE4C_CRITIC_HARDENING.md)
- **Full Spec:** [PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md](docs/governance/ai_autonomy/PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md)
- **Quickstart:** [PHASE4E_QUICKSTART.md](docs/governance/ai_autonomy/PHASE4E_QUICKSTART.md)
- **Implementation Summary:** [PHASE4E_IMPLEMENTATION_SUMMARY.md](PHASE4E_IMPLEMENTATION_SUMMARY.md)

---

## Checklist

- [x] Schema defined and versioned (v1.0.0)
- [x] Normalizer implemented with legacy adapter
- [x] CLI script with full argument support
- [x] 31 tests passing (unit + CLI)
- [x] Determinism verified (byte-identical outputs)
- [x] CI integration (artifacts uploaded)
- [x] Documentation complete (spec + quickstart + consumer guide)
- [x] Golden fixtures created
- [x] Backward compatibility maintained
- [x] No trading/config/risk changes

---

## Next Steps (Post-Merge)

1. Monitor CI artifacts in subsequent runs
2. Verify normalized reports are uploaded correctly
3. Use normalized reports for health checks / trend analysis
4. Consider future enhancements:
   - Multi-validator support (VaR backtest, etc.)
   - Trend dashboard
   - Alert thresholds

---

**Phase 4E Complete** ✅

**Ready for:** Review + Merge
