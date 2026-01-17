# Phase 4D: L4 Critic Determinism Contract

**Status:** Implemented  
**Phase:** 4D  
**Deliverable:** Explicit, versioned determinism contract + canonicalization + validator CLI + CI enforcement

---

## Purpose

Formalize the **L4 Critic Replay Determinism Contract** to ensure:
- **Audit-stable** outputs: byte-identical replays for governance compliance
- **Evidence-first** validation: canonicalized artifacts + stable SHA256 hashing
- **Actionable failures**: explicit contract violations with first-mismatch diagnostics
- **CI enforcement**: automated validation prevents regressions

---

## Contract Schema (v1.0.0)

### Canonicalization Rules

**Applied transformations:**
1. **Remove volatile keys** (substring match, case-insensitive):
   - `timestamp`, `created_at`, `duration`, `elapsed`
   - `run_id`, `pid`, `hostname`
   - `absolute_path`, `_temp`, `_tmp`

2. **Normalize paths**:
   - Convert backslashes to forward slashes
   - Strip absolute path prefixes (repo-relative preferred)

3. **Sort dict keys** (lexicographic)

4. **Preserve list order** (deterministic ordering must be in source data)

5. **Stable JSON formatting**:
   - Sorted keys
   - 2-space indentation
   - UTF-8 encoding
   - Trailing newline

### Required Top-Level Keys

All L4 Critic reports must contain:
- `schema_version`
- `pack_id`
- `mode`
- `critic`
- `inputs`
- `summary`
- `findings`
- `meta`

### Numeric Tolerance

**Default:** No tolerance (exact match required)  
**Configurable:** Per-JSON-path tolerances can be added if needed (not implemented in v1.0.0)

---

## Volatile Fields (Denylist)

These fields are **automatically removed** during canonicalization:

| Pattern | Example | Rationale |
|---------|---------|-----------|
| `timestamp` | `"timestamp": "2026-01-11T12:00:00Z"` | Wall-clock time varies |
| `created_at` | `"created_at": "2026-01-11T12:00:00Z"` | Creation time varies |
| `duration` | `"duration": 1.234` | Execution time varies |
| `elapsed` | `"elapsed_ms": 567` | Timing varies |
| `run_id` | `"run_id": "abc123"` | Unique per run |
| `pid` | `"pid": 12345` | Process ID varies |
| `hostname` | `"hostname": "ci-runner-01"` | Host varies |
| `absolute_path` | `"path": "/Users/test/Peak_Trade"` | Absolute paths vary |
| `_temp`, `_tmp` | `"_tmp_dir": "/tmp/xyz"` | Temp paths vary |

**Note:** The L4 Critic already sets `created_at=None` in deterministic mode, so this field is typically absent.

---

## Local Run Instructions

### Validator CLI

**Location:** `scripts/aiops/validate_l4_critic_determinism_contract.py`

**Basic usage:**
```bash
python3 scripts/aiops/validate_l4_critic_determinism_contract.py \
  --baseline tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/critic_report.json \
  --candidate .tmp/l4_critic_out/critic_report.json
```

**Exit codes:**
- `0`: Reports are equal (deterministic) ✅
- `2`: Reports differ (non-deterministic) ❌
- `3`: Invalid input (missing files, invalid JSON)

**Options:**
- `--out <file>`: Write validator report JSON to file
- `--print-canonical <file>`: Write canonical JSON of baseline (debug)
- `--contract-version <ver>`: Specify contract version (default: 1.0.0)

**Example output (PASS):**
```
✅ PASS: Reports are identical (hash match)
   Baseline hash: a1b2c3d4e5f6...
   Candidate hash: a1b2c3d4e5f6...
```

**Example output (FAIL):**
```
❌ FAIL: Reports differ (first mismatch at $.summary.verdict)
   Baseline hash:  a1b2c3d4e5f6...
   Candidate hash: f6e5d4c3b2a1...
   First mismatch: $.summary.verdict
```

### Reproduce CI Locally

```bash
# 1. Run L4 Critic in deterministic replay mode
python3 scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/l4_critic_out \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic \
  --no-legacy-output

# 2. Validate against snapshot
python3 scripts/aiops/validate_l4_critic_determinism_contract.py \
  --baseline tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/critic_report.json \
  --candidate .tmp/l4_critic_out/critic_report.json

# 3. Run twice and compare (determinism check)
python3 scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/l4_critic_run1 \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic \
  --no-legacy-output

python3 scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/l4_critic_run2 \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic \
  --no-legacy-output

diff .tmp/l4_critic_run1/critic_report.json .tmp/l4_critic_run2/critic_report.json
```

---

## CI Integration

### Workflow

**File:** `.github/workflows/l4_critic_replay_determinism_v2.yml`

**Trigger:** PRs/pushes touching:
- `src/ai_orchestration/**`
- `scripts/aiops/**`
- `tests/**`

**Jobs:**
1. **`l4_critic_replay_determinism`** (existing)
   - Runs L4 Critic in deterministic replay mode
   - Compares output with snapshot (JSON + Markdown)
   - Verifies determinism (run twice, compare)

2. **`validate_determinism_contract`** (new in Phase 4D)
   - Runs validator CLI against snapshot
   - Uploads validator report as artifact
   - Fails if contract violations detected

**Required context:** `L4 Critic Replay Determinism`

**Artifacts:**
- `l4-critic-outputs-failed-<run_id>` (on failure)
- `validator-report-<run_id>.json` (always)

### CI Behavior

**On contract violation:**
1. Validator exits with code 2
2. CI step fails
3. First mismatch path printed to logs
4. Validator report artifact uploaded
5. Operator uses triage prompt (see below)

**Expected checks:**
- ✅ Lint Gate (Always Run)
- ✅ Audit
- ✅ CI/tests (Python 3.9, 3.10, 3.11)
- ✅ L4 Critic Replay Determinism (all jobs)
- ✅ Policy Critic Gate (Always Run)

---

## Operator Triage Workflow

**If determinism CI fails:**

1. **Download validator report artifact** from CI run
2. **Inspect first mismatch path** in validator report JSON
3. **Reproduce locally** (see commands above)
4. **Classify root cause:**
   - **A) Volatile field leak:** New field added without canonicalization
   - **B) Unstable ordering:** List ordering not deterministic
   - **C) Intentional change:** Schema evolution or bug fix

5. **Fix:**
   - **A:** Add field pattern to `DEFAULT_VOLATILE_KEY_PATTERNS` in contract module
   - **B:** Ensure source data sorts lists by stable key (e.g., finding ID)
   - **C:** Update snapshot if intentional (follow Phase 4C procedure)

6. **Verify fix:**
   ```bash
   pytest tests/ai_orchestration/test_l4_critic_determinism_contract.py -v
   ```

**Triage prompt:** See `PHASE4D_CURSOR_TRIAGE_PROMPT.md` for full AI-assisted triage workflow.

---

## Design Decisions

### 1. Volatile Key Handling

**Decision:** Simple substring matching (case-insensitive)  
**Rationale:**
- Fast and deterministic
- Easy to reason about
- Covers 99% of cases
- Can be extended to regex if needed

**Alternative considered:** JSON path patterns (e.g., `$.meta.created_at`)  
**Rejected:** More complex, harder to maintain, overkill for current needs

### 2. Numeric Tolerance

**Decision:** No tolerance in v1.0.0 (exact match required)  
**Rationale:**
- L4 Critic outputs are deterministic (no floating-point computation)
- Exact match is stronger guarantee
- Can be added later if needed (per-path tolerance dict)

**Alternative considered:** Global epsilon tolerance (e.g., 1e-9)  
**Rejected:** Not needed for current use case, can introduce false positives

### 3. List Ordering

**Decision:** Preserve list order (do not auto-sort)  
**Rationale:**
- Deterministic ordering should be in source data (e.g., findings sorted by severity + ID)
- Auto-sorting lists could mask bugs
- Explicit is better than implicit

**Alternative considered:** Auto-sort all lists by first stable key  
**Rejected:** Too magical, could hide real issues

### 4. Path Normalization

**Decision:** Normalize paths (backslash → slash, strip absolute prefixes)  
**Rationale:**
- Cross-platform compatibility (Windows vs Unix)
- Repo-relative paths are more stable
- Heuristic-based (best-effort)

**Alternative considered:** Require all paths to be repo-relative in source  
**Rejected:** Too strict, would break existing code

---

## References

- **Contract module:** `src/ai_orchestration/l4_critic_determinism_contract.py`
- **Validator CLI:** `scripts/aiops/validate_l4_critic_determinism_contract.py`
- **Unit tests:** `tests/ai_orchestration/test_l4_critic_determinism_contract.py`
- **CI workflow:** `.github/workflows/l4_critic_replay_determinism_v2.yml`
- **Triage prompt:** `PHASE4D_CURSOR_TRIAGE_PROMPT.md`
- **Phase 4C (predecessor):** `PHASE4C_CRITIC_HARDENING.md`

---

## Backwards Compatibility

**Guaranteed:**
- Existing L4 Critic reports (schema v1.0.0) are compatible
- Existing CI workflow (`l4_critic_replay_determinism_v2.yml`) unchanged
- Existing fixtures and snapshots work without modification
- No changes to L4 Critic runtime behavior

**Migration:** None required (additive change)

---

## Future Work

**Potential enhancements (not in scope for Phase 4D):**
1. **Numeric tolerance:** Add per-path float tolerance if needed
2. **Regex patterns:** Support regex for volatile key matching
3. **Custom canonicalization:** Per-field custom transformations
4. **Snapshot management:** CLI tool to update snapshots (Phase 4E?)
5. **Diff visualization:** HTML diff report for easier debugging

---

**Status:** ✅ Implemented (Phase 4D complete)
