#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Peak_Trade – Post-Merge Ops Doku für PR #203
# Ziel:
# - docs/ops/PR_203_MERGE_LOG.md anlegen
# - docs/ops/README.md Index erweitern
# - docs/PEAK_TRADE_STATUS_OVERVIEW.md aktualisieren (Changelog-Eintrag)
# - Commit + Push + PR + Merge + main fast-forward
# =============================================================================

cd ~/Peak_Trade

echo "==> Update main"
git checkout main
git pull --ff-only

BR="docs/ops-pr203-merge-log"
echo "==> Create branch: $BR"
git checkout -b "$BR"

echo "==> Ensure docs folders"
mkdir -p docs/ops

echo "==> Write merge log: docs/ops/PR_203_MERGE_LOG.md"
cat > docs/ops/PR_203_MERGE_LOG.md <<'MD'
# PR #203 – test(viz): skip matplotlib-based report/plot tests when matplotlib missing

**Status:** ✅ MERGED (squash)
**Merge Commit:** `85c3c3e`
**Branch:** `test/viz-tests-optional-matplotlib` (deleted)
**Intent:** Optionalisierung der Matplotlib-basierten Report/Plot-Tests, sodass Core-Installationen ohne `matplotlib` sauber durchlaufen.

---

## 1) Problem / Motivation

In einer minimalen Core-Umgebung (ohne Visualisierung-Dependencies) führten Matplotlib-basierte Tests zu ImportErrors und damit zu **Test-Failures**.

**Ziel:** Wenn `matplotlib` nicht installiert ist → relevante Tests **skippen** statt failen.

---

## 2) Änderungen (High-Level)

- ✅ **Tests**: Matplotlib-abhängige Tests verwenden `importorskip`/Skip-Mechanismus, wenn `matplotlib` fehlt.
- ✅ **Packaging**: Neues optionales Extra **`viz`** für Visualisierungen (inkl. `matplotlib`).
- ✅ **Ops/Workflow**: `scripts/post_merge_workflow.sh` mit Hinweisen/Checks ergänzt bzw. aktualisiert.
- ✅ **CI**: Vollständig grün ohne Matplotlib-Installation (Core bleibt schlank).

---

## 3) Qualität / CI Ergebnisse

Alle Checks grün ✅:
- `lint`: pass (13s)
- `audit`: pass (2m11s)
- `tests (3.11)`: pass (3m54s)
- `strategy-smoke`: pass (44s)
- `CI Health Gate`: pass (39s)

---

## 4) Nutzung (Operator / Dev)

### Standard (ohne Matplotlib)
```bash
uv run pytest -q
# → Viz-Tests werden geskippt, Core-Tests laufen durch
```

### Mit Visualisierung
```bash
uv sync --extra viz
uv run pytest -q
# → Alle Tests inkl. Matplotlib-basierte Viz-Tests laufen
```

---

## 5) Betroffene Dateien

**Tests:**
- `tests/test_backtest_report.py`
- `tests/test_experiment_report.py`
- `tests/test_plots.py`
- `tests/test_portfolio_robustness_report.py`
- weitere Report/Plot-Tests mit Matplotlib-Abhängigkeit

**Packaging:**
- `pyproject.toml` – neues Extra `viz = ["matplotlib>=3.5.0"]`

**Workflow:**
- `scripts/post_merge_workflow.sh` – Hinweise für optionale Viz-Installation

---

## 6) Breaking Change Policy

- ✅ **Additiv & safe**: Core bleibt ohne Viz-Extras lauffähig
- ✅ **Viz-only Tests** werden sauber **geskippt** statt zu crashen
- ✅ **Keine Änderungen** an Live-Trading kritischen Pfaden
- ✅ **Backward-kompatibel**: Bestehende Workflows mit vollem Extra-Set unverändert

---

## 7) Follow-ups

- ✅ Gleicher Mechanismus für Web-UI-Tests (siehe PR #201)
- ⏳ Optional: Weitere Extras für andere Tool-Gruppen (z.B. `dev`, `ml`, `quarto`)

---

## 8) Ops / Merge Metadata

**Author:** rauterfrank-ui
**Date:** 2025-12-21 (Europe/Berlin)
**Merge Method:** Squash
**Branch Cleanup:** ✅ Branch deleted after merge

---

**Fazit:**
PR #203 macht Matplotlib-basierte Viz-Tests optional via `viz` Extra. Core-Installationen bleiben schlank und lauffähig, Viz-Workflows funktionieren mit explizitem Extra-Install.
MD

echo "==> Update docs/ops/README.md (add PR #203)"
# Füge PR #203 zur Merge Logs Sektion in docs/ops/README.md hinzu
# Zeile nach PR #201 einfügen
if grep -q "PR #201.*MERGE_LOG" docs/ops/README.md; then
  # Füge nach der Zeile mit PR #201 ein
  sed -i '' '/PR #201.*MERGE_LOG/a\
- PR #203 – test(viz): skip matplotlib-based report/plot tests when matplotlib missing – `docs/ops/PR_203_MERGE_LOG.md`
' docs/ops/README.md
else
  # Falls PR #201 nicht gefunden, füge am Ende der Merge Logs Sektion hinzu
  sed -i '' '/## Merge Logs/a\
- PR #203 – test(viz): skip matplotlib-based report/plot tests when matplotlib missing – `docs/ops/PR_203_MERGE_LOG.md`
' docs/ops/README.md
fi

echo "==> Update docs/PEAK_TRADE_STATUS_OVERVIEW.md (Changelog)"
# Füge Changelog-Eintrag am Ende hinzu
cat >> docs/PEAK_TRADE_STATUS_OVERVIEW.md <<'CHANGELOG'
- 2025-12-21: PR #203 – Matplotlib-basierte Viz-Tests optional via extras (Core ohne Matplotlib lauffähig)
CHANGELOG

echo "==> Git status"
git status

echo "==> Stage changes"
git add docs/ops/PR_203_MERGE_LOG.md
git add docs/ops/README.md
git add docs/PEAK_TRADE_STATUS_OVERVIEW.md

echo "==> Commit"
git commit -m "docs(ops): add PR #203 merge log + update index

- docs/ops/PR_203_MERGE_LOG.md: comprehensive merge log for viz tests optionalization
- docs/ops/README.md: add PR #203 to merge logs index
- docs/PEAK_TRADE_STATUS_OVERVIEW.md: changelog entry for PR #203

Related: PR #203 (test/viz-tests-optional-matplotlib)
Merge commit: 85c3c3e"

echo "==> Push branch"
git push -u origin "$BR"

echo ""
echo "=== AUTOMATED PR WORKFLOW ==="

# 0) Safety: sauberer Status + richtiger Branch
echo "==> Safety checks"
git status -sb
CURRENT_BRANCH="$(git branch --show-current)"
echo "Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "$BR" ]; then
  echo "ERROR: Not on expected branch $BR"
  exit 1
fi

# 1) PR erstellen (Branch wird automatisch erkannt)
echo ""
echo "==> Creating PR"
gh pr create \
  --title "docs(ops): PR #203 merge log + index update" \
  --body "Adds merge log for PR #203 (matplotlib/viz tests optionalization) + updates ops README and changelog.

## Changes
- docs/ops/PR_203_MERGE_LOG.md: comprehensive merge log
- docs/ops/README.md: add PR #203 to merge logs index
- docs/PEAK_TRADE_STATUS_OVERVIEW.md: changelog entry

## Related
- PR #203 (test/viz-tests-optional-matplotlib)
- Merge commit: 85c3c3e" \
  --base main

# 2) Checks live verfolgen
echo ""
echo "==> Watching PR checks (Ctrl+C to skip, continues after checks pass)"
gh pr checks --watch || true

# Optional: Warten auf Benutzer-Bestätigung vor Merge
echo ""
read -p "Press ENTER to merge PR (or Ctrl+C to abort)..." DUMMY

# 3) Merge (squash + branch löschen)
echo ""
echo "==> Merging PR (squash + delete branch)"
gh pr merge --squash --delete-branch

# 4) main aktualisieren
echo ""
echo "==> Updating main"
git checkout main
git pull --ff-only

echo ""
echo "=== ✅ DONE ==="
echo "PR docs merged + main up-to-date"
git log -1 --oneline
