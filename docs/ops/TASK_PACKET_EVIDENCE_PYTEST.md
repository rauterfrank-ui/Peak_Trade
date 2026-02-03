# Task Packet: Evidence-Stamps (pytest) + Exitcode korrekt + Cleanup

**Für Cursor/Agent: genau drei Blöcke — 1) Repro/Setup, 2) Commands, 3) Expected output / success criteria.**

---

## 1) Repro/Setup

**Context**
- Repo: Peak_Trade  
- Ziel: Reproduzierbarer lokaler Evidence-Stamp für `python -m pytest -q` mit korrektem Exitcode (tee-sicher) und kuratierte Evidence-Dateien (nicht-null Läufe nach `.tmp&#47;evidence&#47;failed&#47;`).

**Preconditions**
- In normalem Terminal-Kontext ausführen (nicht Sandbox/Agent).
- venv aktiv: `source .venv&#47;bin&#47;activate`
- Working tree sauber; `docs&#47;ops` muss zu `origin&#47;main` passen:
  - `docs/ops/README.md` = vollständiges Ops-README (enthält "PR Inventory" / "pr_inventory")
  - `docs/ops/MERGE_LOG_WORKFLOW.md` und `docs/ops/PR_999_MERGE_LOG.md` dürfen **nicht** die kurzen Test-Fixtures sein.

---

## 2) Commands

### A) docs/ops auf origin/main bringen (typischen Drift beheben)
```bash
git fetch origin --prune
git checkout origin/main -- docs/ops/README.md docs/ops/MERGE_LOG_WORKFLOW.md docs/ops/PR_999_MERGE_LOG.md
git status
```

### B) pytest Evidence-Stamp ausführen (tee-sicherer Exitcode)
```bash
mkdir -p .tmp/evidence
TS="$(date +%Y%m%d_%H%M%S)"
set -o pipefail
python -m pytest -q 2>&1 | tee ".tmp/evidence/pytest_main_pass_${TS}.txt"
echo "${PIPESTATUS[0]}" > ".tmp/evidence/pytest_main_pass_${TS}.exitcode"
tail -n 3 ".tmp/evidence/pytest_main_pass_${TS}.txt"
cat ".tmp/evidence/pytest_main_pass_${TS}.exitcode"
```

### C) Evidence kuratieren: nicht-null Läufe nach failed/
```bash
mkdir -p .tmp/evidence/failed
for f in .tmp/evidence/*.exitcode; do
  [ -f "$f" ] || continue
  code="$(cat "$f" | tr -d '[:space:]')"
  base="${f%.exitcode}"
  if [ "$code" != "0" ]; then
    mv -f "$f" ".tmp/evidence/failed/$(basename "$f")"
    [ -f "${base}.txt" ] && mv -f "${base}.txt" ".tmp/evidence/failed/$(basename "${base}.txt")" || true
  fi
done
```

### Optional: One-liner (bash, tee-sicher + gleicher Timestamp)
```bash
mkdir -p .tmp/evidence; TS="$(date +%Y%m%d_%H%M%S)"; set -o pipefail; python -m pytest -q 2>&1 | tee ".tmp/evidence/pytest_main_pass_${TS}.txt"; echo "${PIPESTATUS[0]}" > ".tmp/evidence/pytest_main_pass_${TS}.exitcode"
```
(Danach ggf. Cleanup wie in C ausführen.)

---

## 3) Expected output / success criteria

- **pytest:** `python -m pytest -q` meldet `6587 passed, ...` und die Exitcode-Datei enthält `0`.
- **Evidence:** `.tmp&#47;evidence&#47;failed&#47;` enthält alle Läufe mit Exitcode ≠ 0.
- **Repo:** Bleibt sauber (`git status` clean); Evidence-Dateien sind untracked.
