---
title: "RUNBOOK D2 — Reporting + Compare Runs"
version: "v1.0"
date: "2026-01"
scope: "docs-only / NO-LIVE"
---

# RUNBOOK D2 — Reporting + Compare Runs (v1.0)

Dieses Runbook beschreibt einen **docs-/artefakt-basierten** Workflow, um:

- **Ad-hoc Reports** aus Run-Artefakten zu erzeugen
- optional **Compare-Reports** (mehrere Runs) zu erstellen

**Wichtig:** D2 ist **NO‑LIVE**. Es geht ausschließlich um Auswertung/Reporting (Evidence Chain) und hat keine Auswirkung auf Live-Execution.

---

## Voraussetzungen

- Du hast eine Run-ID (oder mehrere Run-IDs) und Zugriff auf die **Run-Artefakte** (lokal oder als exportiertes Evidence-Pack).
- Du kennst den Reporting-Einstieg:
  - `docs/reporting/REPORTING_QUICKSTART.md`

---

## A. Single-Run Report (Ad-hoc)

1) **Artefakte lokalisieren**

- Stelle sicher, dass du die Run-Artefakte (Logs/Configs/Reports) für den Run verfügbar hast.
- Falls du unsicher bist, nutze den Quickstart:
  - `docs/reporting/REPORTING_QUICKSTART.md`

2) **Report rendern**

- Folge dem in `docs/reporting/REPORTING_QUICKSTART.md` beschriebenen Render-/Build-Flow.
- Ziel: ein reproduzierbarer Output (HTML/PDF/Markdown, je nach Pipeline), der in der Evidence Chain abgelegt werden kann.

3) **Sanity Checks**

- Prüfe, ob im Report die erwarteten Run-Metadaten enthalten sind (Run-ID, Datum, Konfiguration/Snapshot).
- Prüfe, ob der Report ohne fehlende Referenzen/Assets auskommt.

---

## B. Compare Runs (mehrere Runs)

1) **Run-IDs definieren**

- Lege die zu vergleichenden Runs fest (z.B. Baseline vs. Candidate).

2) **Compare-Tooling**

- Compare-Logik ist (mindestens) als Entwickler-Tooling vorhanden:
  - `scripts/dev/compare_runs.py`

> Hinweis: Die genaue CLI/Flags können sich ändern; orientiere dich an der Header-Dokumentation im Script und am Reporting-Quickstart.

3) **Compare-Report erzeugen**

- Erzeuge einen konsolidierten Compare-Output (Tabellen/Plots/Delta-Ansicht).
- Lege den Compare-Report als Evidence-Artefakt ab (inkl. Referenz auf die verglichenen Run-IDs).

---

## Troubleshooting (kurz)

- **Missing artifacts / paths**: erst Evidence-Pack / Artefaktstruktur verifizieren (`docs/reporting/REPORTING_QUICKSTART.md`).
- **Inconsistent metadata**: sicherstellen, dass alle Runs die gleiche Schema-/Report-Version nutzen.
- **Output nicht reproduzierbar**: Run-Config-Snapshots und Seeds/Regime-Inputs prüfen (siehe Reporting-Quickstart).

---

## Links

- Reporting Quickstart: `docs/reporting/REPORTING_QUICKSTART.md`
- Backtest/Registry CLI Kontext (optional): `docs/REGISTRY_BACKTEST_CLI.md`
- Compare Script: `scripts/dev/compare_runs.py`
