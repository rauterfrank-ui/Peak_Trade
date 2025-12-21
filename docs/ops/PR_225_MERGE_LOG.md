# PR #225 — MERGE LOG

## Summary
PR #225 merged: **fix(quarto): make backtest report template no-exec**

- PR: #225 — fix(quarto): make backtest report template no-exec
- Merged commit (main): `6b01a8d`
- Date: 2025-12-21
- Merge type: Squash merge

## Motivation / Why
- Der CI-Check **Render Quarto Smoke Report** war rot (nicht-blockierend), aber als Signal wichtig
- Ursache: Template enthielt 5 ausführbare Code-Chunks (`{python}`), wodurch der Guard `scripts/ci/check_quarto_no_exec.sh` fehlschlug
- Operator-Nutzen: Stabiler CI, keine falsch-positiven Failures mehr

## Changes
### Added/Updated
- Geändert: `{python}` → `python` (5 Stellen) – non-executable Chunks für Smoke-Kontext
- YAML Frontmatter bereits korrekt: `execute.enabled: false`

### Touched files
- `templates/quarto/backtest_report.qmd` — Alle executable Python chunks zu non-executable konvertiert (+5, -6)

## Verification
- `quarto render templates/quarto/backtest_report.qmd --to html` ✅
- CI: Render Quarto Smoke Report — 21s ✅
- CI: audit — 2m20s ✅
- CI: tests (3.11) — 4m10s ✅
- CI: strategy-smoke — 50s ✅
- CI: CI Health Gate — 42s ✅
- Notes: Template-only change, keine Code-Logik betroffen

## Risk Assessment
🟢 **Low**
- Nur Template-Änderung (non-executable display)
- CI vollständig grün, Quarto Smoke Test jetzt stabil
- Bei Bedarf kann execute.enabled nach Copy wieder aktiviert werden

## Operator How-To
### Do this
1. Template ist bereits gemerged in main
2. Zukünftige Backtest-Reports nutzen automatisch das no-exec Template
3. Falls Code-Execution gewünscht: Nach Copy `execute.enabled: true` setzen

### Quick commands
```bash
# Template lokal testen
quarto render templates/quarto/backtest_report.qmd --to html

# Guard-Check lokal ausführen
bash scripts/ci/check_quarto_no_exec.sh
```

## Follow-Up Tasks
- [x] CI Quarto Smoke Test stabilisiert
- [x] Template-Syntax korrigiert
- [ ] Optional: Weitere Quarto-Templates auf no-exec prüfen (falls vorhanden)

## References
- PR #225 — fix(quarto): make backtest report template no-exec
- Related docs: `templates/quarto/backtest_report.qmd`
- CI Guard: `scripts/ci/check_quarto_no_exec.sh`
- Merged commit: `6b01a8d`
