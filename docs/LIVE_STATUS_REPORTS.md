# Peak_Trade – Live Status Reports (Phase 57)

> **Daily/Weekly Status als „Snapshot" des Live-/Testnet-Systems**

---

## 1. Zweck

Live-Status-Reports bieten einen **strukturierten Snapshot** des aktuellen Zustands deines Live-/Testnet-Systems. Sie sind nützlich für:

- **Tägliche/Wöchentliche Reviews**: Schneller Überblick über Health, Portfolio & Risk
- **Dokumentation**: Historische Aufzeichnung des Systemzustands
- **Post-Mortems & Reviews**: Referenz für Incident-Analysen
- **Governance**: Nachvollziehbarkeit für Entscheidungen

**Wichtig:** Reports basieren auf dem `live_ops`-CLI und wachsen automatisch mit zukünftigen Erweiterungen mit.

---

## 2. Verwendung

### 2.1 Basic Usage

**Daily-Report (Markdown only):**
```bash
python scripts/generate_live_status_report.py \
  --config config/config.toml \
  --output-dir reports/live_status \
  --format markdown \
  --tag daily
```

**Weekly-Report (Markdown + HTML):**
```bash
python scripts/generate_live_status_report.py \
  --config config/config.toml \
  --output-dir reports/live_status \
  --format both \
  --tag weekly
```

**Report mit Operator-Notizen:**
```bash
python scripts/generate_live_status_report.py \
  --config config/config.toml \
  --output-dir reports/live_status \
  --format markdown \
  --tag daily \
  --notes-file docs/live_status_notes.md
```

### 2.2 CLI-Argumente

| Argument | Beschreibung | Default |
|----------|--------------|---------|
| `--config` | Pfad zur Config-Datei | `config/config.toml` |
| `--output-dir` | Ausgabe-Verzeichnis | `reports/live_status` |
| `--format` | Report-Format (`markdown`, `html`, `both`) | `markdown` |
| `--tag` | Optionaler Tag (z.B. `daily`, `weekly`, `incident`) | `None` |
| `--notes-file` | Pfad zu Operator-Notizen-Datei | `None` |

### 2.3 Output-Dateien

Reports werden benannt als:
- `live_status_YYYY-MM-DD_HHMM_tag.md`
- `live_status_YYYY-MM-DD_HHMM_tag.html`

Beispiele:
- `live_status_2025-12-07_0900_daily.md`
- `live_status_2025-12-07_0900_weekly.html`

---

## 3. Report-Inhalt

Der Report enthält vier Hauptsektionen:

### 3.1 Health Overview

- **Overall Status**: Aggregierter Status (OK/DEGRADED/FAIL)
- **Einzel-Checks**:
  - Config: Config-Datei geladen & konsistent?
  - Exchange: Exchange-Client initialisierbar?
  - Alerts: Alert-System konfiguriert?
  - Live Risk: Risk-Limits geladen & konsistent?

### 3.2 Portfolio Snapshot

- **Mode**: Umgebung (shadow/testnet/live)
- **Aggregate**:
  - Equity (geschätzt)
  - Total Exposure
  - Free Cash
- **Per-Symbol Exposure**: Tabelle mit offenen Positionen (Symbol, Size, Notional, Side, Unrealized PnL)

### 3.3 Risk & Alerts

- **Live-Risk Limits**: Status & Warnungen
- **Letzter Risk-Check**: Health-Check-Ergebnis
- **Alerts**: Hinweis auf Alert-Historie (falls verfügbar)

### 3.4 Notes (Operator)

- Optionaler Freitext für Operator-Notizen
- Kann aus `--notes-file` geladen werden
- Nützlich für TODOs, Follow-Ups, Incident-Referenzen

---

## 4. Integration mit Playbooks & Drills

### 4.1 Research → Live Playbook

Live-Status-Reports können als **Quelle für Portfolio-Beurteilung** im [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) verwendet werden:

- Vergleich Research-PnL vs. Live-PnL
- Portfolio-Exposure-Überwachung
- Risk-Limit-Compliance

### 4.2 Incident-Drills

Reports können an Incident-Drills angehängt werden:

- **Vor Drill**: Baseline-Status dokumentieren
- **Nach Drill**: Vergleich vor/nach Drill
- **In Drill-Log**: Referenz auf Report-Dateien

Siehe auch:
- [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md)
- [`INCIDENT_DRILL_LOG.md`](INCIDENT_DRILL_LOG.md)

### 4.3 Governance & Monitoring

Regelmäßige Status-Reports sind Teil der operativen Governance:

- **Daily**: Schneller Health-Check
- **Weekly**: Detaillierter Review
- **Incident**: Vor/Nach Incident-Dokumentation

---

## 5. Technische Details

### 5.1 Datenquelle

Reports basieren auf:
- `python scripts/live_ops.py health --json`
- `python scripts/live_ops.py portfolio --json`

Die JSON-Ausgaben werden geparst und in Markdown/HTML formatiert.

### 5.2 Erweiterbarkeit

Da Reports auf dem `live_ops`-CLI basieren, wachsen sie automatisch mit zukünftigen Erweiterungen mit:

- Neue Health-Checks → automatisch im Report
- Neue Portfolio-Felder → automatisch im Report
- Neue Risk-Metriken → automatisch im Report

### 5.3 Formatter-Modul

Das Formatter-Modul (`src/reporting/live_status_report.py`) stellt reine Python-Funktionen bereit:

- `build_markdown_report()`: Markdown-Formatierung
- `build_html_report()`: HTML-Formatierung

Keine Subprocess-Aufrufe, keine Abhängigkeiten zu `live_ops`-Internals.

---

## 6. Best Practices

### 6.1 Frequenz

- **Daily**: Täglicher Health-Check (Markdown)
- **Weekly**: Wöchentlicher Review (Markdown + HTML)
- **Incident**: Vor/Nach Incident-Dokumentation

### 6.2 Operator-Notizen

Erstelle eine `docs/live_status_notes.md` für wiederkehrende Notizen:

```markdown
# Live Status Notes

## Wöchentliche TODOs
- [ ] Portfolio-Rebalance prüfen
- [ ] Risk-Limits reviewen

## Incident-Follow-Ups
- [ ] Alert-System-Verbesserung (siehe Incident-Drill 2025-12-07)
```

### 6.3 Archivierung

- Reports in `reports/live_status/` archivieren
- Regelmäßig aufräumen (z.B. älter als 3 Monate)
- Wichtige Reports (z.B. vor Incident) separat markieren

---

## 7. Verwandte Dokumente

- [`CLI_CHEATSHEET.md`](CLI_CHEATSHEET.md) – CLI-Referenz
- [`LIVE_TESTNET_TRACK_STATUS.md`](LIVE_TESTNET_TRACK_STATUS.md) – Live-/Testnet-Status
- [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) – Research → Live Prozess
- [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md) – Incident-Drills
- [`GOVERNANCE_AND_SAFETY_OVERVIEW.md`](GOVERNANCE_AND_SAFETY_OVERVIEW.md) – Governance-Rahmen

---

**Built with ❤️ and safety-first architecture**
