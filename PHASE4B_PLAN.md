# Peak_Trade – Phase 4B Plan
## Evidence Pack: Schema Versioning, Fast Lint, Policy Critic (Gated), Operator Docs & Examples

**Status:** Ready for Implementation  
**Date:** 2026-01-08  
**Owner:** Operator / AI Orchestration  
**Scope:** Evidence Pack Pipeline (CI + scripts + docs + tests)  
**Non-goal:** Keine Änderungen an Trading-/Execution-Logik  
**Prerequisites:** Phase 4A Complete (Evidence Pack CI Gate + Auto-Creation) ✅

---

## 0. Zielbild
Phase 4B liefert die nächste Stufe der Evidence-Pack-Infrastruktur:
1) **Schema Versioning + Migration** (Backward Compatibility)  
2) **Semantics Lint** (sehr schnell, deterministisch)  
3) **Policy Critic** (optional/gated, deterministisch, offline)  
4) **Operator Docs + Examples** (Happy Path + Failure Gallery)

Dabei gilt: **Phase 4A Evidence Pack CI Gate bleibt unverändert und regressionsfrei**.

---

## 1. Success Criteria (Definitionen + Messbarkeit)

### 1.1 Unit Tests
- **40 neue Unit Tests**, alle grün, deterministisch.
- Allokation:
  - **M1 Schema/Migration:** 12 Tests
  - **M2 Lint + Perf:** 10 Tests
  - **M3 Policy Critic + Perf:** 14 Tests
  - **M4 Example Packs:** 4 Tests
- Tests laufen in bestehender CI Matrix (3.9/3.10/3.11), ohne zusätzliche Always-Run Last.

### 1.2 Performance
**Definition:** Messung auf `ubuntu-latest` GitHub Runner, Python 3.11, **cold cache** (keine venv/pycache Vorannahmen), 10 Packs aus `tests/fixtures/evidence_packs/`.

#### Lint
- **Target:** < 5s für 10 Packs (median of 3 runs)
- **CI Guard:**
  - **Warn:** > 5s
  - **Fail:** > 7s
- Output muss Zeiten + Host-Info + Pack Count reporten.

#### Policy Critic
- **Target:** < 30s für 10 Packs (single run)
- **CI Guard:**
  - **Warn:** > 30s
  - **Fail:** > 40s

### 1.3 Regression Freedom
- **Keine Regressionen:** Phase 4A Jobs bleiben grün und **inhaltlich unverändert**:
  - Evidence Pack Validation Gate/changes
  - evidence-pack-smoke-run
  - evidence-pack-validation-gate
- Neue Jobs in Phase 4B sind **path-filtered** und lösen nicht bei irrelevanten Änderungen aus.
- Phase 4A Tests (41 Tests) müssen in jedem Milestone grün bleiben.

### 1.4 Operator Docs & Examples
- Vollständige Operator-Doku inkl.:
  - Tool-Matrix (wann welches Tool)
  - Decision Tree (Debug-Flow)
  - 3–5 Good Examples + 6–10 Bad Examples
  - Lokal reproduzierbare Commands

---

## 2. Constraints / Design Principles
- Deterministische Validierung (stabile Sortierung, stabile Error Codes, keine Zeit-/Netzabhängigkeit).
- Offline-first (Policy Critic ohne Webcalls).
- Minimal invasive CI (keine neuen Always-Run Jobs ohne Path-Filter).
- Error UX: klare, handlungsorientierte Meldungen (one-line summary + actionable hint).

---

## 3. Evidence Pack Schema: Versioning & Compatibility

### 3.1 Schema Header
Jeder Evidence Pack enthält einen Header:

- `schema_id`: `"evidence_pack"`
- `schema_version`: SemVer string, z.B. `"1.0.0"`
- `pack_id`: stable identifier
- `created_at`: ISO-8601 (optional; falls vorhanden: nicht zur Deterministik genutzt)
- `producer`: `{ tool, version, git_sha }` (wo möglich)

**Validation Rule:**  
- Fehlender `schema_id` oder `schema_version` => hard fail (Exit-Code: `EPACK_SCHEMA_MISSING`)
- Unsupported `schema_version` => hard fail (Exit-Code: `EPACK_SCHEMA_UNSUPPORTED`)
- `schema_id` != expected => hard fail

### 3.2 SemVer Policy
- **PATCH:** rein redaktionell/constraints, keine Feldänderungen
- **MINOR:** additive, backward-compatible (neue optionale Felder)
- **MAJOR:** breaking; Migration erforderlich

### 3.3 Backward Compatibility / Migration Strategy
**Policy:** Validator kann ältere Versionen **auto-migrieren** (deterministisch) und dann gegen current schema validieren.

- Migrationen sind **pure functions**: input dict -> output dict
- Migration registry:
  - `migrations[(from_version, to_version)] = fn`
  - `migrate(pack, from_version, to_version)` wendet Chain an
- Jede Migration:
  - darf keine Netz-/Zeitabhängigkeit nutzen
  - darf keine Daten "erfinden"; nur Felder umbenennen/normalisieren/Defaults setzen (transparent dokumentiert)

**Migrations-Output:**
- optional: `migration_info: { migrated_from, migrated_to }` (nur für Debug; nicht für Sorting/Hash)

### 3.4 Canonicalization
Vor Validation:
- stable ordering (keys)
- normalized paths (posix-like, wenn relevant)
- strip trailing whitespace in strings (definiert)

---

## 4. CI Design: Triggers, Path Filtering, Gating

### 4.1 Jobs (existing / unchanged)
**Phase 4A Evidence Pack Validation Gate** bleibt unverändert.

### 4.2 Jobs (new in 4B) + Execution Order

**Job Execution Order:**
```
changes (path filter)
  ↓
evidence-pack-smoke-run (creates pack)
  ↓
evidence-pack-lint ← NEW (fast fail, <5s)
  ↓
evidence-pack-validation-gate (Phase 4A, unchanged)
  ↓
evidence-pack-policy-critic ← NEW (gated, <30s)
```

**Rationale:** Lint läuft VOR validation gate (fail fast für offensichtliche Format-Fehler, 5s vs. 1-2s/pack).

#### Job 1: Evidence Pack Lint (fast)
- Trigger: changes in `src/ai_orchestration/evidence_pack/**`, `scripts/evidence_pack/**`, `tests/**evidence_pack**`, `docs/ai/**evidence_pack**`
- Runtime target: < 5s (median of 3 runs)
- Fail threshold: > 7s

#### Job 2: Evidence Pack Policy Critic (gated)
- Trigger: same as above
- Zusätzlich gated:
  - entweder via Label (z.B. `run-policy-critic`)
  - oder via opt-in path `policy/**` changes
  - oder Push to main/master (always run)
- Default: läuft nicht bei reinen Docs-only Änderungen

### 4.3 Regression Guard für Phase 4A
**CI Job:** `phase4a-regression-guard`  
**Trigger:** All PRs  
**Purpose:** Verhindert unbeabsichtigtes Ändern von Phase 4A Workflow/Scripts

**Implementation:**
```bash
#!/usr/bin/env bash
# Check Phase 4A workflow unchanged (except comments/whitespace)
set -euo pipefail

# Check if exemption label present
if gh pr view --json labels | jq -e '.labels[] | select(.name == "ci/phase4a-regression-allow")' > /dev/null 2>&1; then
    echo "✅ Exemption label present - skipping regression guard"
    exit 0
fi

# Assert workflow unchanged (ignore comment/whitespace changes)
if git diff origin/main -- .github/workflows/evidence_pack_gate.yml | \
   grep -v "^[+\-]#" | grep -v "^[+\-]$" | grep "^[+\-]" > /dev/null; then
    echo "❌ Phase 4A workflow modified without ci/phase4a-regression-allow label"
    echo "If intentional, add label 'ci/phase4a-regression-allow' to PR"
    exit 1
fi

# Assert Phase 4A scripts unchanged
for script in scripts/validate_evidence_pack_ci.py scripts/run_layer_smoke_with_evidence_pack.py; do
    if ! git diff --quiet origin/main -- "$script"; then
        echo "❌ Phase 4A script $script modified without exemption"
        exit 1
    fi
done

echo "✅ Phase 4A regression guard passed"
```

**Exemption:** PR with label `ci/phase4a-regression-allow` skips this check

---

## 5. Performance Specs & Guards

### 5.1 Lint Perf Guard Script
**File:** `scripts/perf_guard_lint.sh` (NEW)

**Purpose:** Measures lint performance over 10 fixture packs

**Implementation:**
```bash
#!/usr/bin/env bash
# Performance Guard: Evidence Pack Lint (<5s for 10 packs)
set -euo pipefail

FIXTURE_DIR="${1:-tests/fixtures/evidence_packs}"
WARN_THRESHOLD=5
FAIL_THRESHOLD=7
NUM_RUNS=3

echo "🔍 Perf Guard: Lint Performance Test"
echo "Target: <${WARN_THRESHOLD}s (median of ${NUM_RUNS} runs)"
echo "Fixture Dir: $FIXTURE_DIR"
echo ""

# Count packs
PACK_COUNT=$(find "$FIXTURE_DIR" -name "evidence_pack.json" | wc -l | tr -d ' ')
echo "Found $PACK_COUNT packs"

if [ "$PACK_COUNT" -lt 10 ]; then
    echo "⚠️ WARNING: Need 10+ packs for performance test (found $PACK_COUNT)"
fi

# Environment info
echo "Python: $(python --version)"
echo "OS: $(uname -s)"
echo ""

# Run multiple times and collect durations
DURATIONS=()
for i in $(seq 1 $NUM_RUNS); do
    START=$(date +%s.%N)
    python scripts/lint_evidence_pack.py --root "$FIXTURE_DIR" --json > /dev/null 2>&1
    END=$(date +%s.%N)
    DURATION=$(echo "$END - $START" | bc)
    DURATIONS+=($DURATION)
    echo "Run $i: ${DURATION}s"
done

# Calculate median
MEDIAN=$(printf '%s\n' "${DURATIONS[@]}" | sort -n | awk '{a[NR]=$1} END {print (NR%2==1)?a[(NR+1)/2]:(a[NR/2]+a[NR/2+1])/2}')

echo ""
echo "⏱️ Median Duration: ${MEDIAN}s"
echo "Warn Threshold: ${WARN_THRESHOLD}s"
echo "Fail Threshold: ${FAIL_THRESHOLD}s"

# Check thresholds
if (( $(echo "$MEDIAN > $FAIL_THRESHOLD" | bc -l) )); then
    echo "❌ PERFORMANCE FAIL: ${MEDIAN}s exceeds ${FAIL_THRESHOLD}s"
    exit 1
elif (( $(echo "$MEDIAN > $WARN_THRESHOLD" | bc -l) )); then
    echo "⚠️ PERFORMANCE WARN: ${MEDIAN}s exceeds ${WARN_THRESHOLD}s (not failing)"
    exit 0
else
    echo "✅ PERFORMANCE OK: ${MEDIAN}s within threshold"
    exit 0
fi
```

### 5.2 Policy Critic Perf Guard Script
**File:** `scripts/perf_guard_policy_critic.sh` (NEW)

**Purpose:** Measures policy critic performance over 10 fixture packs

**Implementation:**
```bash
#!/usr/bin/env bash
# Performance Guard: Evidence Pack Policy Critic (<30s for 10 packs)
set -euo pipefail

FIXTURE_DIR="${1:-tests/fixtures/evidence_packs}"
WARN_THRESHOLD=30
FAIL_THRESHOLD=40

echo "🔍 Perf Guard: Policy Critic Performance Test"
echo "Target: <${WARN_THRESHOLD}s"
echo "Fixture Dir: $FIXTURE_DIR"
echo ""

# Count packs
PACK_COUNT=$(find "$FIXTURE_DIR" -name "evidence_pack.json" | wc -l | tr -d ' ')
echo "Found $PACK_COUNT packs"

if [ "$PACK_COUNT" -lt 10 ]; then
    echo "⚠️ WARNING: Need 10+ packs for performance test (found $PACK_COUNT)"
fi

# Environment info
echo "Python: $(python --version)"
echo "OS: $(uname -s)"
echo ""

# Single run measurement
START=$(date +%s.%N)
python scripts/policy_critic_evidence_pack.py --root "$FIXTURE_DIR" --json > /dev/null 2>&1
END=$(date +%s.%N)

DURATION=$(echo "$END - $START" | bc)

echo "⏱️ Duration: ${DURATION}s"
echo "Warn Threshold: ${WARN_THRESHOLD}s"
echo "Fail Threshold: ${FAIL_THRESHOLD}s"

# Check thresholds (soft limits for policy critic)
if (( $(echo "$DURATION > $FAIL_THRESHOLD" | bc -l) )); then
    echo "❌ PERFORMANCE FAIL: ${DURATION}s exceeds ${FAIL_THRESHOLD}s"
    exit 1
elif (( $(echo "$DURATION > $WARN_THRESHOLD" | bc -l) )); then
    echo "⚠️ PERFORMANCE WARN: ${DURATION}s exceeds ${WARN_THRESHOLD}s (not failing)"
    exit 0
else
    echo "✅ PERFORMANCE OK: ${DURATION}s within threshold"
    exit 0
fi
```

---

## 6. Policy Critic Rules

### 6.1 Severity Levels
- `INFO`, `WARN`, `ERROR`
- CI behavior:
  - default: `ERROR` fails job
  - `WARN`: logged but doesn't fail
  - `INFO`: informational only
  - allowlist/exemptions must be explicit and scoped (pack_id/rule_id)

### 6.2 Exemptions
- `policy_exemptions` block in pack metadata or a repo allowlist file (`config/evidence_pack_policy_exemptions.toml`)
- Must include:
  - `rule_id`: string identifier
  - `justification`: human-readable reason
  - `expiration_date`: ISO-8601 (optional but recommended)
  - `approved_by`: operator/reviewer name

**Example exemption:**
```toml
[[exemptions]]
pack_id = "EVP-L0-20260108-001"
rule_id = "sod_check_missing"
justification = "L0-RO layer does not require critic (read-only)"
approved_by = "ops-team"
expiration_date = "2026-06-01"
```

### 6.3 Example Rules (initial set)
**Rule 1: SoD Enforcement**
- Check: `primary_model_id != critic_model_id` (if both present)
- Severity: ERROR
- Exemption: L0-RO layers (read-only, no critic required)

**Rule 2: Autonomy Level Restrictions**
- Check: `autonomy_level != AutonomyLevel.EXEC`
- Severity: ERROR (always blocks)
- Message: "EXEC forbidden: Evidence Packs require explicit CodeGate + Go/NoGo"

**Rule 3: Model Registry Compliance**
- Check: All model IDs exist in `config/model_registry.toml`
- Severity: WARN (informational, doesn't block)
- Fallback: Graceful skip if registry not found

**Rule 4: Evidence Chain Completeness**
- Check: If `autonomy_level >= PROP`, require non-empty `sod_checks` and `run_logs`
- Severity: WARN (metrics only, doesn't block)

**Rule 5: Suspicious External References**
- Check: No external URLs in evidence fields (offline constraint)
- Severity: WARN
- Rationale: Policy critic must be offline/deterministic

---

## 7. Tests

### 7.1 Test Allocation (40 total)

**M1: Schema Versioning & Migration (12 tests)**
- `test_schema_header_present()`
- `test_schema_version_valid_format()`
- `test_schema_version_unsupported_fails()`
- `test_migration_registry_lookup()`
- `test_migration_chain_v1_to_v2()`
- `test_migration_determinism()`
- `test_backward_compat_missing_version_defaults()`
- `test_canonicalization_key_order()`
- `test_canonicalization_path_normalization()`
- `test_timestamp_chronology_valid()`
- `test_git_sha_format_valid()`
- `test_config_fingerprint_format_valid()`

**M2: Lint + Performance (10 tests)**
- `test_lint_single_pack_valid()`
- `test_lint_single_pack_invalid()`
- `test_lint_multiple_packs()`
- `test_lint_json_output_format()`
- `test_lint_missing_mandatory_fields()`
- `test_lint_invalid_timestamp_format()`
- `test_lint_chronology_violation()`
- `test_lint_duplicate_run_ids()`
- `test_lint_empty_directory()`
- `test_lint_performance_benchmark()` ← Performance harness

**M3: Policy Critic + Performance (14 tests)**
- `test_policy_critic_sod_valid()`
- `test_policy_critic_sod_violation()`
- `test_policy_critic_autonomy_exec_forbidden()`
- `test_policy_critic_autonomy_rec_allowed()`
- `test_policy_critic_model_registry_valid()`
- `test_policy_critic_model_registry_invalid()`
- `test_policy_critic_evidence_chain_complete()`
- `test_policy_critic_evidence_chain_incomplete()`
- `test_policy_critic_run_log_complete()`
- `test_policy_critic_exemption_valid()`
- `test_policy_critic_exemption_expired()`
- `test_policy_critic_strict_mode()`
- `test_policy_critic_json_output()`
- `test_policy_critic_performance_benchmark()` ← Performance harness

**M4: Example Pack Validation (4 tests)**
File: `tests/test_example_packs_validation.py` (NEW)
- `test_good_pack_passes_all_gates()`
- `test_bad_pack_missing_fields_fails_validation()`
- `test_bad_pack_sod_violation_fails_policy_critic()`
- `test_bad_pack_invalid_format_fails_lint()`

**Total:** 40 Tests (12+10+14+4)

---

## 8. Documentation

### 8.1 Operator Docs: Decision Tree + Tool Matrix

**File:** `docs/ai/EVIDENCE_PACK_OPERATOR_GUIDE.md` (NEW)

**Content:**

#### Tool Comparison Matrix
| Tool | Speed | Depth | Use Case | Required? |
|------|-------|-------|----------|-----------|
| **Lint** | <5s/10 packs | Field formats, chronology | Pre-commit, CI fast fail | No (recommended) |
| **Validate** | ~1s/pack | Schema + mandatory fields | CI gate, manual review | **YES (Phase 4A)** |
| **Policy Critic** | <30s/10 packs | SoD, autonomy, model registry | Main branch, security review | No (gated) |

#### Decision Tree
```
CI Job Failed
│
├─ evidence-pack-lint?
│  ├─ Perf issue (>5s)?
│  │  └─ Check pack count, run perf_guard locally:
│  │     bash scripts/perf_guard_lint.sh tests/fixtures/evidence_packs
│  └─ Lint rule failed?
│     └─ See error code in output, fix pack, re-validate locally:
│        python scripts/lint_evidence_pack.py --pack <path> --verbose
│
├─ evidence-pack-validation-gate?
│  ├─ Missing field?
│  │  └─ See docs/ai/EVIDENCE_PACK_SCHEMA_V1.md, add field, re-run
│  └─ Invalid format?
│     └─ Download validation report JSON artifact from CI:
│        gh run download <run-id> --name evidence-pack-validation-report
│        cat evidence-pack-validation-report/validation_report.json | jq
│
└─ evidence-pack-policy-critic?
   ├─ SoD violation?
   │  └─ Check primary_model_id != critic_model_id in pack
   ├─ Autonomy violation?
   │  └─ Remove EXEC level, use REC/PROP instead
   └─ Exemption needed?
      └─ Add exemption to config/evidence_pack_policy_exemptions.toml
```

#### Reproduce Locally
```bash
# Download CI artifacts
gh run download <run-id> --name evidence-packs

# Run lint
python scripts/lint_evidence_pack.py --root evidence-packs --verbose

# Run validation
python scripts/validate_evidence_pack_ci.py --root evidence-packs --verbose

# Run policy critic
python scripts/policy_critic_evidence_pack.py --root evidence-packs --strict
```

### 8.2 Schema Docs
**File:** `docs/ai/EVIDENCE_PACK_SCHEMA_V1.md` (NEW)

**Content:**
- Schema header fields (required/optional)
- Field format specifications
- Migration notes (v1.0 -> v1.1 example)
- Error codes reference (EPACK_SCHEMA_MISSING, etc.)
- Backward compatibility policy

### 8.3 Troubleshooting Guide
**File:** `docs/ai/EVIDENCE_PACK_TROUBLESHOOTING.md` (NEW)

**Content:**
- Common error codes + fixes
- Performance troubleshooting (pack count, system load)
- CI artifacts download guide
- Local reproduction commands

---

## 9. Milestones & Deliverables

### Milestone 1: Schema Versioning & Migration (Week 1)
**Deliverables**
- schema header enforcement
- migration registry + v1.0 baseline
- canonicalization
- 12 unit tests
- docs: `EVIDENCE_PACK_SCHEMA_V1.md`

**Files (4 new, 1 modified):**
- `src/ai_orchestration/evidence_pack_schema.py` (NEW, ~300 lines)
- `tests/ai_orchestration/test_evidence_pack_schema.py` (NEW, ~250 lines)
- `docs/ai/EVIDENCE_PACK_SCHEMA_V1.md` (NEW, ~200 lines)
- `scripts/migrate_evidence_pack_schema.py` (NEW, ~150 lines, optional)
- `src/ai_orchestration/evidence_pack.py` (UPDATE, +50 lines)

**Acceptance**
- [ ] validator supports schema_version "1.0.0"
- [ ] deterministically migrates older packs (when applicable)
- [ ] all 12 tests green
- [ ] Phase 4A tests (41) remain green

### Milestone 2: Semantics Lint (Week 2)
**Deliverables**
- lint rules + CLI entry
- perf guard lint script
- 10 unit tests
- CI integration (new job before validation gate)

**Files (4 new, 2 modified):**
- `scripts/lint_evidence_pack.py` (NEW, ~250 lines)
- `scripts/perf_guard_lint.sh` (NEW, ~80 lines)
- `tests/test_evidence_pack_lint.py` (NEW, ~200 lines)
- `tests/fixtures/evidence_packs/` (NEW, 10+ fixture packs)
- `.github/workflows/evidence_pack_gate.yml` (UPDATE, +50 lines)
- `docs/ai/EVIDENCE_PACK_CI_GATE.md` (UPDATE, +100 lines)

**Acceptance**
- [ ] 10 packs median <5s (warn>5, fail>7)
- [ ] stable output/reporting
- [ ] CI job runs before validation gate (fail fast)
- [ ] Phase 4A tests (41) remain green

### Milestone 3: Policy Critic (Gated) (Week 3)
**Deliverables**
- rule engine + 5 base rules + exemptions
- perf guard policy critic script
- 14 unit tests
- CI job gated (label/opt-in)

**Files (5 new, 2 modified):**
- `src/ai_orchestration/evidence_pack_policy_critic.py` (NEW, ~400 lines)
- `scripts/policy_critic_evidence_pack.py` (NEW, ~250 lines)
- `scripts/perf_guard_policy_critic.sh` (NEW, ~70 lines)
- `tests/test_evidence_pack_policy_critic.py` (NEW, ~300 lines)
- `config/evidence_pack_policy_exemptions.toml` (NEW, ~50 lines)
- `.github/workflows/evidence_pack_gate.yml` (UPDATE, +60 lines)
- `docs/ai/EVIDENCE_PACK_POLICY_RULES.md` (NEW, ~300 lines)

**Acceptance**
- [ ] <30s target (warn>30, fail>40)
- [ ] deterministic, offline
- [ ] does not run unless opted-in (label OR policy file change OR main push)
- [ ] Phase 4A tests (41) remain green

### Milestone 4: Operator Docs + Examples (Week 4)
**Deliverables**
- operator guide, decision tree, tool matrix
- fixtures: good/bad packs
- 4 tests for example packs
- finalize plan outcomes

**Files (8 new):**
- `docs/ai/EVIDENCE_PACK_OPERATOR_GUIDE.md` (NEW, ~400 lines)
- `docs/ai/EVIDENCE_PACK_TROUBLESHOOTING.md` (NEW, ~300 lines)
- `examples/evidence_packs/README.md` (NEW, ~100 lines)
- `examples/evidence_packs/good_pack_l0_rec.json` (NEW)
- `examples/evidence_packs/good_pack_l1_prop.json` (NEW)
- `examples/evidence_packs/bad_pack_missing_fields.json` (NEW)
- `examples/evidence_packs/bad_pack_sod_violation.json` (NEW)
- `examples/evidence_packs/bad_pack_invalid_format.json` (NEW)
- `tests/test_example_packs_validation.py` (NEW, ~100 lines)

**Acceptance**
- [ ] examples cover common failures
- [ ] new operator can debug within 10 minutes
- [ ] all 4 example tests green (1 good pass, 3 bad fail expected gates)
- [ ] Phase 4A tests (41) remain green

---

## 10. File Plan (Summary)

### New Files (24)
**M1 (4):**
1. `src/ai_orchestration/evidence_pack_schema.py`
2. `tests/ai_orchestration/test_evidence_pack_schema.py`
3. `docs/ai/EVIDENCE_PACK_SCHEMA_V1.md`
4. `scripts/migrate_evidence_pack_schema.py` (optional)

**M2 (4):**
5. `scripts/lint_evidence_pack.py`
6. `scripts/perf_guard_lint.sh`
7. `tests/test_evidence_pack_lint.py`
8. `tests/fixtures/evidence_packs/` (directory + 10 packs)

**M3 (6):**
9. `src/ai_orchestration/evidence_pack_policy_critic.py`
10. `scripts/policy_critic_evidence_pack.py`
11. `scripts/perf_guard_policy_critic.sh`
12. `tests/test_evidence_pack_policy_critic.py`
13. `config/evidence_pack_policy_exemptions.toml`
14. `docs/ai/EVIDENCE_PACK_POLICY_RULES.md`

**M4 (9):**
15. `docs/ai/EVIDENCE_PACK_OPERATOR_GUIDE.md`
16. `docs/ai/EVIDENCE_PACK_TROUBLESHOOTING.md`
17. `examples/evidence_packs/README.md`
18. `examples/evidence_packs/good_pack_l0_rec.json`
19. `examples/evidence_packs/good_pack_l1_prop.json`
20. `examples/evidence_packs/bad_pack_missing_fields.json`
21. `examples/evidence_packs/bad_pack_sod_violation.json`
22. `examples/evidence_packs/bad_pack_invalid_format.json`
23. `tests/test_example_packs_validation.py`

**CI/Regression Guard (1):**
24. `.github/workflows/phase4a_regression_guard.yml` (NEW, optional - kann in existing workflow integriert werden)

### Modified Files (3)
1. `src/ai_orchestration/evidence_pack.py` (M1: Schema Integration, +50 lines)
2. `.github/workflows/evidence_pack_gate.yml` (M2: +50 lines Lint, M3: +60 lines Policy Critic, Total: +110 lines)
3. `docs/ai/EVIDENCE_PACK_CI_GATE.md` (M2: +100 lines Lint Docs)

**Total: 24 new + 3 modified = 27 files**

---

## 11. Rollback
**Emergency Rollback Options:**

**Option A: Disable CI Jobs (fastest, 2 minutes)**
```bash
# Edit .github/workflows/evidence_pack_gate.yml
# Comment out new jobs:
# jobs:
#   evidence-pack-lint:    # <-- Comment out
#   evidence-pack-policy-critic:  # <-- Comment out

git add .github/workflows/evidence_pack_gate.yml
git commit -m "chore: Disable Phase 4B CI jobs (emergency)"
git push origin main
```

**Option B: Revert PR (safe, 5 minutes)**
```bash
# Find PR commit SHA
git log --oneline | grep "feat: phase4b"

# Revert commit
git revert <commit-sha>
git push origin main
```

**Option C: GitHub Branch Protection (instant)**
- GitHub UI: Settings → Branches → main protection
- Uncheck: evidence-pack-lint (if required)
- Uncheck: evidence-pack-policy-critic (if required)
- Save (instant, no code change)

---

## 12. Implementation Start Checklist

- [ ] Plan reviewed and accepted
- [ ] Create branch `feat/phase4b-schema-versioning`
- [ ] Implement Milestone 1
  - [ ] Schema header + validation
  - [ ] Migration registry
  - [ ] 12 unit tests
  - [ ] Phase 4A regression guard passes
- [ ] CI green (incl. Phase 4A regression guard)
- [ ] Proceed milestone-by-milestone

---

## 13. Success Metrics (Post-Implementation)

**Coverage:**
- 40 new tests (100% passing)
- Phase 4A tests (41) remain green (0 regressions)

**Performance:**
- Lint: < 5s median (10 packs)
- Policy Critic: < 30s (10 packs)

**CI Impact:**
- No new always-run jobs (path-filtered)
- Lint job adds ~5-7s to Evidence Pack PRs
- Policy Critic is opt-in (no default overhead)

**Operator Readiness:**
- Docs complete (operator guide + troubleshooting + schema)
- Examples cover 3+ good + 3+ bad scenarios
- Debug flow reproducible locally (< 10 minutes)

---

**Status:** ✅ READY FOR IMPLEMENTATION START
