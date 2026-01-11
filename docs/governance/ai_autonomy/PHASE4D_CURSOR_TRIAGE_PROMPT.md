# PHASE4D – Cursor Multi-Agent CI Triage Prompt (L4 Critic Determinism)

## Quickstart
Für die schnelle Anwendung im Incident-/CI-Failure-Fall:

- **Quickstart:** [PHASE4D_CURSOR_TRIAGE_PROMPT_QUICKSTART.md](PHASE4D_CURSOR_TRIAGE_PROMPT_QUICKSTART.md)

Diese Seite bleibt der **vollständige All-in-one Prompt** (Copy/Paste in Cursor Chat).

---

## Zweck
Diese Vorlage dient als **governance-konforme, evidence-first** Triage-Anweisung für CI-Failures rund um den L4 Critic Determinism Contract.
Sie ist so gestaltet, dass ein Cursor Multi-Agent Chat:
- schrittweise diagnostiziert (read-only),
- Root Cause klassifiziert,
- konkrete Patch-Locations vorschlägt,
- Tests benennt/ergänzt,
- und einen auditierbaren Evidence-Report strukturiert ausgibt.

---

## Context (für Agent)

You are operating in Peak_Trade under strict governance constraints:
- **No-live policy:** No trading execution, no live API calls, no external services
- **Read-only safe:** Only read operations and writes to `.tmp/` directories
- **Evidence-first:** All diagnostics must be reproducible and documented

**Task:** Triage a failing CI gate "Validate Determinism Contract" for L4 Critic replay determinism (Phase 4D).

---

## INPUT (Operator füllt aus)

```yaml
Failing job: <job name>
Failing step: <step name>
Report path: <path to report, e.g. .tmp/l4_critic_out/critic_report.json>
CI run: <url>
Error: <exact error message>
```

**Optional:** Failing artifact snippet (10–30 Zeilen):
```text
<paste relevant JSON or error output>
```

---

## DELIVERABLES (Agent produces structured output)

### 1. Failure Classification

Identify which CI step failed:
- [ ] **Contract validation** (validator detected contract violation)
- [ ] **JSON snapshot comparison** (critic_report.json differs from fixture)
- [ ] **Markdown snapshot comparison** (critic_summary.md differs from fixture)
- [ ] **Run-twice determinism** (two consecutive runs produced different outputs)

**Agent action:** Check error message and CI logs to determine failure type.

---

### 2. Local Reproduction

Execute the following commands in sequence and capture outputs:

#### Step A: Validate contract + print hash
```bash
python scripts/aiops/validate_l4_critic_determinism_contract.py \
  --report <REPORT_PATH> \
  --print-hash
```

**Expected (success):**
```
✅ Contract validation passed
Hash: <SHA256>
```

**Expected (failure):**
```
❌ Contract violations detected:
  - Absolute path found: /Users/...
  - Timestamp found in deterministic mode: created_at
```

#### Step B: Emit canonical JSON
```bash
python scripts/aiops/validate_l4_critic_determinism_contract.py \
  --report <REPORT_PATH> \
  --write-canonical .tmp/canonical.json
```

#### Step C: Diff against known-good baseline
```bash
diff -u tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/critic_report.json \
  .tmp/canonical.json || true
```

**Agent action:** Execute commands (read-only safe), capture all outputs, include in evidence section.

---

### 3. Root Cause Classification

Analyze diff output and classify root cause:

#### A) Volatile Field Introduced
**Symptoms:** New field contains timestamp, absolute path, UUID, session ID

**Examples:**
- `"created_at": "2026-01-11T12:00:00Z"` (should be `null` in deterministic mode)
- `"evidence_pack_path": "/Users/operator/Peak_Trade/tests/..."` (should be repo-relative)
- `"run_id": "abc-123-def-456"` (should be excluded)
- `"session_id": "..."` (should be excluded)

**Impact:** Report is non-deterministic across machines/runs

#### B) Unstable Ordering
**Symptoms:** Items in lists appear in different order between runs

**Examples:**
- `findings` array not sorted by severity (HIGH > MEDIUM > LOW > INFO)
- Within same severity, findings not sorted by stable key (ID, title)
- JSON keys not alphabetically sorted

**Impact:** Byte-identical comparison fails despite semantic equivalence

#### C) Non-Canonical Emission
**Symptoms:** JSON structure/formatting differs despite semantic equivalence

**Examples:**
- Keys not sorted alphabetically (`sort_keys=True` missing in `json.dump()`)
- Inconsistent indentation or whitespace
- Float precision differences (e.g., `0.1` vs `0.10`)

**Impact:** Text-based diff shows differences, but semantic content is identical

#### D) Intentional Schema Change
**Symptoms:** New field added or existing field structure changed (legitimate evolution)

**Valid scenario:** Schema evolution requires snapshot update

**Impact:** Snapshot is stale, needs operator-approved refresh

**Agent action:** Determine which category (A/B/C/D) best matches the observed diff.

---

### 4. Minimal Patch Suggestion

Based on root cause, suggest fix location and code changes:

#### For Volatile Field (Root Cause A)

**File:** `src/ai_orchestration/l4_critic_determinism_contract.py`  
**Function:** `canonicalize_report()`

```python
def canonicalize_report(report: dict) -> dict:
    """Canonicalize report by removing/normalizing volatile fields."""
    canonical = report.copy()

    # Suppress timestamps in deterministic mode
    if canonical.get("meta", {}).get("deterministic"):
        canonical["meta"]["created_at"] = None

    # Normalize paths (strip absolute prefixes)
    if "inputs" in canonical:
        path = canonical["inputs"].get("evidence_pack_path", "")
        canonical["inputs"]["evidence_pack_path"] = _normalize_path(path)

    # Remove volatile fields (ADD NEW VOLATILE FIELDS HERE)
    canonical.pop("run_id", None)
    canonical.pop("session_id", None)
    canonical.pop("debug", None)  # Often contains machine-specific info

    return canonical
```

**Test to add:**
```python
# tests/ai_orchestration/test_l4_critic_determinism_contract.py

def test_canonicalize_removes_volatile_field_X():
    """Test that canonicalize_report removes volatile field X."""
    report = {
        "schema_version": "1.0.0",
        "pack_id": "TEST",
        "volatile_field_X": "machine-specific-value",
        # ...
    }

    canonical = canonicalize_report(report)
    assert "volatile_field_X" not in canonical
```

#### For Unstable Ordering (Root Cause B)

**File:** `src/ai_orchestration/critic_report_schema.py`  
**Method:** `to_canonical_dict()`

```python
def to_canonical_dict(self) -> dict:
    """Convert to canonical dict with stable ordering."""
    data = self.model_dump()

    # Sort findings by severity (HIGH > MED > LOW > INFO), then by ID
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    data["findings"] = sorted(
        data["findings"],
        key=lambda f: (
            severity_order.get(f["severity"], 99),
            f.get("id", ""),
            f.get("title", "")  # Secondary sort key for stability
        )
    )

    return data
```

**Test to add:**
```python
# tests/ai_orchestration/test_l4_critic_determinism_contract.py

def test_findings_sorted_by_severity_then_id():
    """Test that findings are sorted by severity, then ID."""
    report = CriticReport(
        # ... fields ...
        findings=[
            Finding(id="B", severity="HIGH", ...),
            Finding(id="A", severity="HIGH", ...),
            Finding(id="C", severity="LOW", ...),
        ]
    )

    canonical = report.to_canonical_dict()
    findings = canonical["findings"]

    # Check severity grouping
    assert findings[0]["severity"] == "HIGH"
    assert findings[1]["severity"] == "HIGH"
    assert findings[2]["severity"] == "LOW"

    # Check ID sorting within HIGH severity
    assert findings[0]["id"] == "A"
    assert findings[1]["id"] == "B"
```

#### For Non-Canonical Emission (Root Cause C)

**File:** `src/ai_orchestration/critic_report_schema.py`  
**Method:** `write_json()`

```python
def write_json(self, path: Path, deterministic: bool = False):
    """Write report to JSON with canonical formatting."""
    data = self.to_canonical_dict() if deterministic else self.model_dump()

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
            sort_keys=True  # CRITICAL: Always True for canonical emission
        )
```

**Verification command:**
```bash
# Verify keys are sorted in output
python -c "import json; d=json.load(open('.tmp/canonical.json')); print(list(d.keys()))"
# Expected: ['critic', 'findings', 'inputs', 'meta', 'mode', 'pack_id', 'schema_version', 'summary']
```

#### For Intentional Schema Change (Root Cause D)

**Procedure:** Operator-approved snapshot update

```bash
# Step 1: Verify change is intentional (review PR/commit that introduced field)

# Step 2: Regenerate snapshot with new schema
python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0 \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic \
  --no-legacy-output

# Step 3: Validate new snapshot passes contract validation
python scripts/aiops/validate_l4_critic_determinism_contract.py \
  --report tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/critic_report.json \
  --print-hash

# Step 4: Commit with clear message
git add tests/fixtures/l4_critic_determinism/
git commit -m "chore(aiops): update L4 critic determinism snapshot (schema v1.0.0 field addition: <FIELD_NAME>)"
```

**Documentation update required:**
- Update `docs/governance/ai_autonomy/PHASE4D_L4_CRITIC_DETERMINISM_CONTRACT.md`
- Document new field in canonicalization matrix
- Update schema version if breaking change

---

### 5. Evidence Report

**Agent action:** Structure all findings in this template:

```markdown
## Triage Evidence Report

**Date:** YYYY-MM-DD HH:MM UTC
**CI Run:** <GITHUB_RUN_URL>
**Local Repo State:** `git rev-parse HEAD` → <COMMIT_SHA>
**Operator:** <USERNAME>

---

### Failure Classification
- [x] <Selected failure type from Step 1>

### Commands Executed

**1. Contract validation:**
```bash
python scripts/aiops/validate_l4_critic_determinism_contract.py \
  --report <REPORT_PATH> \
  --print-hash
```
**Output:**
```
<paste output>
```

**2. Canonical emission:**
```bash
python scripts/aiops/validate_l4_critic_determinism_contract.py \
  --report <REPORT_PATH> \
  --write-canonical .tmp/canonical.json
```
**Output:** Canonical JSON written to .tmp/canonical.json

**3. Diff against baseline:**
```bash
diff -u tests/fixtures/l4_critic_determinism/.../critic_report.json .tmp/canonical.json
```
**Output (first 50 lines or key section):**
```diff
<paste diff>
```

---

### Root Cause
**Classification:** <A/B/C/D>  
**Description:** <concise explanation>

**Key diff indicators:**
- <list specific diff lines that reveal root cause>

---

### Proposed Fix

**File:** `<path/to/file.py>`  
**Function/Method:** `<function_name>()`  
**Change:** <brief description>

**Code patch:**
```python
<paste suggested code snippet>
```

---

### Tests Added/Modified

**Test file:** `tests/ai_orchestration/test_l4_critic_determinism_contract.py`  
**Test function:** `test_<descriptive_name>()`

**Test purpose:** <one sentence>

**Code:**
```python
<paste test code>
```

---

### Snapshot Update Required
- [ ] Yes (Root Cause D: intentional schema change)
- [ ] No (Root Cause A/B/C: code fix required)

**If Yes, justification:**
- PR/commit that introduced schema change: <link>
- New field/structure: <description>
- Operator approval: <username>

---

### Governance Compliance
- [x] Read-only operations (no live calls, no writes outside .tmp/)
- [x] Evidence-first (all commands + outputs captured)
- [x] No trading logic modified
- [x] Reproducible (commands can be re-run by operator)

---

### Next Steps
1. [ ] Review proposed fix with team
2. [ ] Apply patch to codebase
3. [ ] Run local tests: `pytest tests/ai_orchestration/test_l4_critic_determinism_contract.py -v`
4. [ ] Verify CI passes on fix branch
5. [ ] Open PR with fix (reference this triage report)

---

**Report generated by:** Cursor Multi-Agent  
**Status:** ✅ COMPLETE
```

---

## References

- **Contract Doc:** `docs/governance/ai_autonomy/PHASE4D_L4_CRITIC_DETERMINISM_CONTRACT.md`
- **Validator CLI:** `scripts/aiops/validate_l4_critic_determinism_contract.py`
- **Contract Utilities:** `src/ai_orchestration/l4_critic_determinism_contract.py`
- **CI Workflow:** `.github/workflows/l4_critic_replay_determinism_v2.yml`
- **Merge Log:** `docs/ops/PR_<NUM>_MERGE_LOG.md` (Phase 4D)

---

## Governance Guardrails (Reminder for Agent)

✅ **Allowed:**
- Read operations on all files
- Writes to `.tmp/` directory
- Command execution (read-only validators, tests)
- Evidence capture and documentation

❌ **Forbidden:**
- Live trading operations
- External API calls (network requests)
- Writes outside `.tmp/` (except with explicit operator approval for snapshot updates)
- Automatic commits/pushes

---

**End of Triage Prompt Template**
