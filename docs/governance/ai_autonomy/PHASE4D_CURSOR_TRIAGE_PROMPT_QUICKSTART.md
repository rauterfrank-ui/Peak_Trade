# PHASE4D – Cursor Triage Prompt Quickstart (L4 Critic Determinism)

## Ziel
Schnellreferenz für CI-Failures im Job **"L4 Critic Replay Determinism"**.  
Diese Quickstart-Seite beschreibt **Workflow**, **Operator-Handgriffe** und **Expected Output** – ohne den vollständigen Prompt zu duplizieren.

## Vollständiger Prompt
Der vollständige All-in-one Prompt (Copy/Paste in Cursor Chat):

- **Prompt:** [PHASE4D_CURSOR_TRIAGE_PROMPT.md](PHASE4D_CURSOR_TRIAGE_PROMPT.md)

---

## Workflow-Konsistenz (Peak_Trade Standard)

Dieser Triage-Prozess folgt dem etablierten Peak_Trade-Workflow:

1. **All-in-one Prompt**  
   Operator füllt INPUT aus, Agent hat vollständigen Kontext.

2. **Tool ausführen (read-only safe)**  
   Agent führt Validator-Kommandos aus (fixtures-only, no network).

3. **Evidence**  
   Strukturierter Report mit Commands + Outputs + Diff (auditfähig).

4. **Merge-ready**  
   Konkreter Code-Patch + Tests + Commit-Message-Vorschlag.

**Referenz:** Konsistent mit Peak_Trade workflow documentation (governance-first, evidence-first, no-live policy).

---

## Wann verwenden?

Wenn in GitHub Actions der Job **"L4 Critic Replay Determinism"** fehlschlägt, insbesondere bei Steps wie:
- "Validate Determinism Contract"
- "Compare outputs with snapshot (JSON)"
- "Compare outputs with snapshot (Markdown)"
- "Verify determinism (run twice, compare)"

**Beispiel-Fehlerklassen:**
- `❌ Contract violation: Absolute path detected: &#47;Users&#47;...`
- `❌ Timestamp found in deterministic mode: created_at`
- `❌ Findings order differs between runs`
- `❌ critic_report.json differs from snapshot`

---

## Operator: Minimal Steps (Copy/Paste Workflow)

### 1) Öffne den vollständigen Prompt
Kopiere den **gesamten** Inhalt aus:  
`docs/governance/ai_autonomy/PHASE4D_CURSOR_TRIAGE_PROMPT.md`

Füge ihn in **Cursor Chat** ein.

### 2) Fülle INPUT-Sektion aus
Ersetze die Platzhalter im Prompt:

```yaml
Failing job: L4 Critic Replay Determinism
Failing step: <step name>
Report path: <path to report, e.g. .tmp/l4_critic_out/critic_report.json>
CI run: <GitHub Actions URL>
Error: <exact error message from CI logs>
```

**Optional:** Artifact snippet (10–30 Zeilen JSON oder Diff-Output)

### 3) Lass den Multi-Agent laufen
Der Agent führt **nur read-only** Diagnostics aus und liefert am Ende das **Strukturierte Evidence Template**.

---

## Expected Output (Strict Format)

Der Agent **muss** dieses Format liefern:

```markdown
## Triage Evidence Report

### Failure Classification
- [x] <Selected failure type>

### Commands Executed
<Commands + captured outputs>

### Root Cause
**Classification:** <A/B/C/D>  
**Description:** <explanation>

### Proposed Fix
**File:** <path/to/file.py>  
**Function/Method:** <function_name>()  
**Code patch:** <snippet>

### Tests Added/Modified
**Test file:** <path>  
**Test function:** <name>  
**Code:** <snippet>

### Snapshot Update Required
- [ ] Yes / [ ] No
**Justification:** <if Yes>

### Next Steps
1. [ ] Review proposed fix
2. [ ] Apply patch
3. [ ] Run local tests
4. [ ] Verify CI passes
5. [ ] Open PR
```

---

## Root Cause Quick Reference (A/B/C/D)

### A) Volatile Field Introduced
**Symptoms:**
- `Absolute path detected: &#47;Users&#47;...`
- `Timestamp found: created_at`
- `UUID&#47;session ID in output`

**Typical Fix Location:**  
L4 critic determinism contract module (planned) → `canonicalize_report()`

**Fix Pattern:**
```python
# Remove or normalize volatile field
canonical.pop("run_id", None)
canonical["meta"]["created_at"] = None
canonical["inputs"]["evidence_pack_path"] = _normalize_path(path)
```

---

### B) Unstable Ordering
**Symptoms:**
- `Findings order differs between runs`
- `JSON keys not consistently ordered`
- List items appear in random order

**Typical Fix Location:**  
`src/ai_orchestration/critic_report_schema.py` → `to_canonical_dict()`

**Fix Pattern:**
```python
# Sort findings by stable key(s)
data["findings"] = sorted(
    data["findings"],
    key=lambda f: (severity_order[f["severity"]], f["id"])
)
```

---

### C) Non-Canonical Emission
**Symptoms:**
- JSON formatting inconsistent
- Keys not alphabetically sorted
- Whitespace/indentation differs

**Typical Fix Location:**  
`src/ai_orchestration/critic_report_schema.py` → `write_json()`

**Fix Pattern:**
```python
json.dump(
    data,
    f,
    ensure_ascii=False,
    indent=2,
    sort_keys=True  # ← Must be True
)
```

---

### D) Intentional Schema Change
**Symptoms:**
- Snapshot differs due to legitimate schema evolution
- New field added intentionally
- Existing field structure changed by design

**Typical Fix Location:**  
Snapshot update (operator-approved only)

**Procedure:**
```bash
# 1. Verify change is intentional (review PR/commit)
# 2. Regenerate snapshot
python3 scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0 \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic \
  --no-legacy-output

# 3. Validate new snapshot
python3 scripts/aiops/validate_l4_critic_determinism_contract.py \
  --report tests/fixtures/l4_critic_determinism/.../critic_report.json \
  --print-hash

# 4. Commit with justification
git commit -m "chore(aiops): update L4 critic determinism snapshot (schema change: <REASON>)"
```

---

## Governance Guardrails (Nicht verhandelbar)

- ✅ **Read-only:** Diagnostics lesen nur bestehende Files oder schreiben nach `.tmp/`
- ✅ **No live calls:** Fixtures only, keine Network Requests
- ✅ **Evidence-first:** Commands + Outputs immer dokumentieren
- ❌ **No automatic snapshot updates:** Nur nach Operator-Approval (Root Cause D)
- ❌ **No trading logic:** Scope strikt AI-Ops tooling

---

## Operator: Nach dem Triage (Merge-ready Hand-off)

Wenn der Agent einen Fix vorschlägt:

**1. Review**
```bash
# Patch lokal reviewen
cat <proposed_file>.py  # Review code changes
```

**2. Test**
```bash
# Tests lokal ausführen
python3 -m pytest tests/ai_orchestration/test_l4_critic_determinism_contract.py -v

# Validator ausführen
python3 scripts/aiops/validate_l4_critic_determinism_contract.py \
  --report tests/fixtures/l4_critic_determinism/.../critic_report.json \
  --print-hash
```

**3. Commit**
```bash
# Fix-PR erstellen (separater Branch)
git checkout -b fix/l4-critic-determinism-<issue>
git add <modified_files>
git commit -m "fix(aiops): <description from agent>"
git push origin fix/l4-critic-determinism-<issue>
```

**4. Merge-Log** (falls im Prozess vorgesehen)
```bash
# Ergänze Merge-Log nach PR-Merge
# docs/ops/PR_<NUM>_MERGE_LOG.md
```

---

## Quick Diagnostic Commands (Manual Verification)

```bash
# Validate contract compliance
python3 scripts/aiops/validate_l4_critic_determinism_contract.py \
  --report <path/to/report.json> \
  --print-hash

# Emit canonical JSON + diff
python3 scripts/aiops/validate_l4_critic_determinism_contract.py \
  --report <path/to/report.json> \
  --write-canonical .tmp/canonical.json

diff -u tests/fixtures/l4_critic_determinism/.../critic_report.json \
  .tmp/canonical.json || true

# Run determinism tests
python3 -m pytest tests/ai_orchestration/test_l4_critic_determinism_contract.py -v
```

---

## Status

✅ **FINAL DELIVERABLE: READY TO USE**

**Status:** Production-ready  
**Verwendung:** Copy/Paste Workflow bei CI-Failure  
**Output:** Strukturierter Evidence Report + konkreter Fix  
**Governance:** Read-only, evidence-first, no-live compliant

**Dateien:**
- Quickstart (diese Datei): `docs/governance/ai_autonomy/PHASE4D_CURSOR_TRIAGE_PROMPT_QUICKSTART.md`
- Vollständiger Prompt: `docs/governance/ai_autonomy/PHASE4D_CURSOR_TRIAGE_PROMPT.md`
- Contract Doc: PHASE4D L4 Critic Determinism Contract (planned)
