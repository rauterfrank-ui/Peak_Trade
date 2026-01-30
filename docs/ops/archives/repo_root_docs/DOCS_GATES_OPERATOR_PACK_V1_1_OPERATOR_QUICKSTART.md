# Docs Gates Operator Pack v1.1 — Operator Quick Start

**Zielgruppe:** Operators, die Docs-Änderungen validieren wollen  
**Zeit:** 60 Sekunden  
**Status:** READY TO USE

---

## 🚀 Quick Start (3 Schritte)

### 1. Snapshot Helper ausführen

```bash
# Von Repo-Root aus
./scripts/ops/pt_docs_gates_snapshot.sh --changed
```

**Was passiert:**
- Alle 3 Docs Gates werden lokal ausgeführt
- Klare PASS/FAIL Ausgabe
- Bei Failures: Actionable "Next Actions"

### 2. Bei Failures: Quick Fixes

**Token Policy Gate (Illustrative Pfade):**
```markdown
Vorher: `scripts/example.py` <!-- pt:ref-target-ignore -->
Nachher: `scripts&#47;example.py`
```

**Reference Targets Gate (Fehlende Dateien):**
```bash
# Pfad aktualisieren
sed -i 's|alter_pfad|neuer_pfad|g' docs/datei.md
```

**Diff Guard Policy Gate (Policy Marker fehlt):**
```bash
# Marker einfügen
python3 scripts/ops/insert_docs_diff_guard_section.py --files docs/ops/datei.md
```

### 3. Re-run zur Verifikation

```bash
./scripts/ops/pt_docs_gates_snapshot.sh --changed
```

**Erwartetes Ergebnis:**
```
✅ Docs Token Policy Gate
✅ Docs Reference Targets Gate
✅ Docs Diff Guard Policy Gate

🎉 All gates passed! Docs changes are merge-ready.
```

---

## 📚 Dokumentation

**Quickstart Runbook (START HERE):**
- `docs&#47;ops&#47;runbooks&#47;RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md`
- Single-Page Quick Reference für alle 3 Gates
- Troubleshooting, Decision Trees, Workflows

**Detaillierte Runbooks (400+ Zeilen):**
1. `docs&#47;ops&#47;runbooks&#47;RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md`
2. `docs&#47;ops&#47;runbooks&#47;RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md`
3. `docs&#47;ops&#47;runbooks&#47;RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md`

**Frontdoor:**
- `docs&#47;ops&#47;README.md` (Section: "Docs Gates — Operator Pack")

---

## 🔔 Neues Feature: PR Merge State Signal (v1.1)

**Was ist das?**
- Optionaler CI-Workflow (informational-only)
- Zeigt BEHIND-Status früh in PR-Checks
- **NIEMALS required, IMMER SUCCESS**

**Wo finde ich es?**
- In PR-Checks: "PR Merge State Signal (Informational)"
- Job Summary enthält:
  - Merge State (behind/ahead/clean)
  - Commits behind/ahead
  - Sync-Anweisungen (copy-paste ready)

**Was tun bei BEHIND?**
```bash
# Option A: Merge main
git fetch origin main
git merge origin/main

# Option B: Rebase auf main
git fetch origin main
git rebase origin/main

# Re-validate
./scripts/ops/pt_docs_gates_snapshot.sh --changed

# Push
git push --force-with-lease
```

---

## ⚙️ Häufige Kommandos

**Standard PR-Workflow:**
```bash
./scripts/ops/pt_docs_gates_snapshot.sh --changed
```

**Full Repo Audit:**
```bash
./scripts/ops/pt_docs_gates_snapshot.sh --all
```

**Gegen spezifischen Branch:**
```bash
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/develop
```

**Einzelne Gates (falls nötig):**
```bash
# Token Policy
python3 scripts/ops/validate_docs_token_policy.py --changed

# Reference Targets
bash scripts/ops/verify_docs_reference_targets.sh --changed

# Diff Guard Policy
python3 scripts/ci/check_docs_diff_guard_section.py
```

---

## 🛡️ Wichtige Prinzipien

**Snapshot-Only (kein Watch-Mode):**
- ✅ Einmal ausführen, Ergebnis erhalten, beenden
- ✅ Keine Background-Prozesse
- ✅ Keine Polling/Watching
- ✅ Deterministisch und reproduzierbar

**Gate-Safe Docs:**
- Illustrative Pfade: `&#47;` encoding verwenden
- Echte Pfade: Unverändert lassen
- Links: Immer auf existierende Dateien zeigen

**Operator-First:**
- Klare PASS/FAIL Ausgabe
- Actionable "Next Actions"
- Cross-Links zu Runbooks
- Copy-paste ready Kommandos

---

## 🆘 Troubleshooting

**Script hängt bei Prompt (> oder dquote>):**
```bash
# Ctrl-C drücken
# Unclosed quotes im Kommando prüfen
```

**"uv: command not found":**
```bash
pip install uv
```

**"Permission denied":**
```bash
chmod +x scripts/ops/pt_docs_gates_snapshot.sh
```

**Gate passed lokal, failed in CI:**
```bash
# Match CI behavior
git fetch origin main
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
```

---

## 📊 Was ist neu in v1.1?

**v1.0 (PR #702, merged 2026-01-13):**
- 3 Operator Runbooks
- Snapshot Helper Script
- Frontdoor Integration

**v1.1 (dieses Update):**
- ✨ **Quickstart Runbook** (Single-Page Quick Reference)
- ✨ **PR Merge State Signal** (Optional CI workflow für BEHIND visibility)
- ✨ **Enhanced Frontdoor** (Klare Navigation, "START HERE" signposting)

---

## 🎯 Operator Checklist

**Vor Commit:**
- [ ] Snapshot helper ausführen: `./scripts/ops/pt_docs_gates_snapshot.sh --changed`
- [ ] Bei Failures: Quick Fixes anwenden
- [ ] Re-run bis alle Gates passen
- [ ] Commit: `git add . && git commit`

**Vor Push:**
- [ ] Quick recheck: `./scripts/ops/pt_docs_gates_snapshot.sh --changed`
- [ ] Push: `git push -u origin <branch>`

**Nach PR erstellt:**
- [ ] CI-Checks beobachten (alle 3 Gates + optional Merge State Signal)
- [ ] Bei BEHIND: Sync-Anweisungen aus Job Summary folgen

**Vor Merge:**
- [ ] Alle required Checks grün
- [ ] Optional: Merge State Signal prüfen (informational-only)

---

**Version:** 1.1  
**Maintainer:** Peak_Trade Operator Team  
**Support:** Siehe Quickstart Runbook für Details
