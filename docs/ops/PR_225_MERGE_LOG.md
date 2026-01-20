# MERGE LOG — PR #225 — fix(quarto): make backtest report template no-exec

**PR:** https://github.com/rauterfrank-ui/Peak_Trade/pull/225  
**Merged:** 2025-12-21  
**Merge Commit:** 6b01a8d  
**Branch:** fix/quarto-backtest-report-noexec (deleted)

---

## Zusammenfassung
- Quarto-Backtest-Report-Template ist jetzt **wirklich "no-exec"** und triggert keine ausführbaren Chunks mehr.
- Der **Quarto Smoke Report** in CI läuft dadurch stabil durch.

## Warum
- CI/Quarto-Smoke hat executable chunks im Template erkannt und dadurch den Smoke-Check gebrochen.
- Ziel war: Template bleibt als Beispiel/Report-Layout nutzbar, aber **ohne Code-Ausführung**.

## Änderungen
**Geändert**
- `templates/quarto/backtest_report.qmd` — 5 Code-Chunks von `{python}` → `python` umgestellt (nicht-executable), YAML `execute.enabled: false` bleibt gesetzt.

## Verifikation
**CI**
- CI Health Gate — ✅ PASS (42s)
- Render Quarto Smoke Report — ✅ PASS (21s)
- audit — ✅ PASS (2m20s)
- strategy-smoke — ✅ PASS (50s)
- tests (3.11) — ✅ PASS (4m10s)

**Lokal**
- `quarto render templates&#47;quarto&#47;backtest_report.qmd --to html`
- ✅ Output erstellt: `backtest_report.html`
- ⚠️ Hinweis: *Unknown meta key "date"* (nicht kritisch)

## Risiko
**Risk:** 🟢 Minimal  
**Begründung**
- Nur Template-Anpassung; kein Einfluss auf Core-Logic oder Trading-Pfade.
- Änderung reduziert CI-Flakiness / Smoke-Failures statt neue Risiken einzuführen.

## Operator How-To
- Wenn du im Quarto-Template Beispiele ergänzt:
  - Nutze `python` (plain) statt `{python}`, damit keine ausführbaren Chunks "detektiert" werden.
  - Lass `execute.enabled: false` im YAML aktiv.
- Sanity lokal:
  - `quarto render templates&#47;quarto&#47;backtest_report.qmd --to html`
- Wenn die Warnung "Unknown meta key date" nervt:
  - Prüfe YAML-Metadaten oder entferne/normalisiere `date:` (optional, kein Muss).

## Referenzen
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/225
- Template: `templates/quarto/backtest_report.qmd`
- Ops-Docs Standard: `docs/ops/MERGE_LOG_TEMPLATE_COMPACT.md`
