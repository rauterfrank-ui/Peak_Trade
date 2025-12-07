# Peak_Trade – Performance Notes (Phase 61)

> **Performance-Baseline v1.0** – Reproduzierbare Messungen & Scale-Überlegungen

---

## 1. Einleitung

Peak_Trade v1.0 ist funktional fertig. Dieses Dokument sammelt Performance-Messungen & Scale-Überlegungen.

**Ziel:**

- Reproduzierbare Basiszahlen für typische Research-/Portfolio-Workloads
- Klare Stelle für Optimierungsideen
- Vergleichspunkt für spätere Versionen

**Verwandte Dokumente:**

- [`scripts/profile_research_and_portfolio.py`](../scripts/profile_research_and_portfolio.py) – Profiling-Script
- [`TECH_DEBT_BACKLOG.md`](TECH_DEBT_BACKLOG.md) – Performance-Optimierungen im Backlog

---

## 2. Umgebung

### Hardware

- **CPU**: Apple M2 Pro
- **Architektur**: arm64
- **RAM**: 16 GB (typisch für M2 Pro)
- **Storage**: SSD (NVMe)
- **OS**: macOS 14.x (Sonoma)

### Software

- **Python**: 3.9.6
- **Wichtige Libraries**:
  - pandas: 2.3.3
  - numpy: 2.0.2
  - pyarrow: (optional)

> **Hinweis:** Diese Werte gelten für die oben beschriebene Umgebung. Performance kann auf anderen Systemen abweichen.

---

## 3. Benchmark-Szenarien

### Scenario A – Portfolio-Research `multi_style_moderate`

**Command:**

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset multi_style_moderate \
  --format both
```

**Beschreibung:**

- Portfolio-Backtest & Reporting für ein Multi-Style-Portfolio mit moderatem Risk-Profil
- 4 Strategien (RSI-Reversion BTC/ETH, MA-Trend BTC, Trend-Following ETH)
- Gleichverteilte Gewichte (je 25%)
- Generiert Markdown + HTML Reports

**Erwartete Workload:**

- Backtests für 4 Strategien
- Portfolio-Aggregation
- Report-Generierung

---

### Scenario B – Research-Pipeline v2 (`rsi_reversion_basic`)

**Command:**

```bash
python scripts/research_cli.py pipeline \
  --sweep-name rsi_reversion_basic \
  --config config/config.toml \
  --format both \
  --with-plots \
  --top-n 3
```

**Beschreibung:**

- Research-Pipeline v2 mit Sweep, Top-N-Auswahl, Plots
- Sweep über RSI-Reversion-Parameter
- Top-3 Konfigurationen werden ausgewählt
- Plots werden generiert (kann zeitaufwändig sein)

**Erwartete Workload:**

- Parameter-Sweep
- Top-N-Auswahl
- Plot-Generierung (Matplotlib)
- Report-Generierung

---

### Scenario C – Portfolio-Robustness `multi_style_moderate`

**Command:**

```bash
python scripts/run_portfolio_robustness.py \
  --config config/config.toml \
  --portfolio-preset multi_style_moderate \
  --format both
```

**Beschreibung:**

- Portfolio-Robustness-Analyse für `multi_style_moderate`
- Monte-Carlo-Simulationen (falls aktiviert)
- Stress-Tests (falls aktiviert)
- Portfolio-Level-Metriken

**Erwartete Workload:**

- Portfolio-Backtests
- Monte-Carlo-Runs (falls aktiviert)
- Stress-Test-Szenarien (falls aktiviert)
- Report-Generierung

---

## 4. Messergebnisse (Baseline v1.0)

### Status

> **Stand 2025-12-07:** Die Benchmark-Szenarien erfordern vorbereitete Daten (Sweep-Results, Top-Candidates).
> Die Profiling-Infrastruktur ist vollständig, konkrete Baseline-Messungen werden bei vollständigem Daten-Setup ergänzt.

### Zusammenfassung

**Durchschnitt aus 3 Runs (TBD bei vollständigem Daten-Setup):**

| Scenario                               | Dauer (s) | Notizen                         |
|----------------------------------------|-----------|----------------------------------|
| portfolio_multi_style_moderate         |  (TBD)    | Erfordert Sweep-Results          |
| pipeline_rsi_reversion_basic           |  (TBD)    | inkl. Plots, top-n=3             |
| portfolio_robustness_multi_style_mod  |  (TBD)    | Monte-Carlo + Stress-Tests aktiv |

**Messung durchführen:**

```bash
# Alle Szenarien
python scripts/profile_research_and_portfolio.py

# Oder einzeln
python scripts/profile_research_and_portfolio.py --scenario portfolio_multi_style_moderate
```

**Erwartete Regression-Schwelle:**

- Wenn sich Laufzeiten um >50% verschlechtern, sollte geprüft werden:
  - Recent Changes / Profiling-Output
  - Ggf. Optimierungs-Ideen aus Abschnitt 5 aufgreifen

---

## 5. Bekannte Bottlenecks & Optimierungsideen

> **Hinweis:** Diese Beobachtungen werden nach dem ersten Durchlauf ergänzt. Ziel ist es, Ideen zu sammeln, **ohne sie alle sofort umzusetzen**.

### Data Loading

**Beobachtung:** (TBD – nach ersten Runs ergänzen)

- Ein Großteil der Laufzeit in Scenario B steckt möglicherweise im Einlesen & Aufbereiten historischer Daten.

**Idee:**

- Caching-Layer weiter ausbauen / mehr Reuse zwischen Runs
- Parquet-Format für persistierte Daten nutzen (falls noch nicht geschehen)

---

### pandas-Operationen

**Beobachtung:** (TBD – nach ersten Runs ergänzen)

- Viele `groupby` / `resample`-Operationen im Backtest können teuer sein.

**Idee:**

- Vektorization & Reduzierung von Zwischenkopien prüfen
- Nutzung von `numba` oder `cython` für kritische Loops (später)

---

### Plot-Generation

**Beobachtung:** (TBD – nach ersten Runs ergänzen)

- Plots (Matplotlib) können bei großen Sweeps spürbar Zeit kosten.

**Idee:**

- Optional Plots deaktivieren für reine Performance-Benchmarks (`--no-plots` o.ä., später)
- Asynchrone Plot-Generierung (später)

---

### Logging

**Beobachtung:** (TBD – nach ersten Runs ergänzen)

- In sehr großen Runs erzeugen Logs spürbar I/O.

**Idee:**

- „Benchmark-/Silent"-Mode für Logs, später
- Batch-weiser Output statt einzelner Log-Zeilen

---

### Weitere Beobachtungen

- (Nach ersten Runs ergänzen)

---

## 6. How-To: Benchmarks wiederholen

### Voraussetzungen

1. Sicherstellen, dass Environment & Datenlage vergleichbar sind:
   - Gleiche Python-Version
   - Gleiche Library-Versionen
   - Gleiche Daten (falls möglich)

### Durchführung

**Alle Szenarien ausführen:**

```bash
python scripts/profile_research_and_portfolio.py
```

**Nur bestimmte Szenarien:**

```bash
python scripts/profile_research_and_portfolio.py \
  --scenario portfolio_multi_style_moderate
```

**Mit Markdown-Output:**

```bash
python scripts/profile_research_and_portfolio.py --markdown
```

**Szenarien auflisten:**

```bash
python scripts/profile_research_and_portfolio.py --list
```

### Auswertung

1. Laufzeiten notieren und mit der Baseline vergleichen
2. Bei größeren Abweichungen:
   - Recent Changes / Profiling-Output prüfen
   - Ggf. Optimierungs-Ideen aus Abschnitt 5 aufgreifen
   - In diesem Dokument aktualisieren

---

## 7. Tech-Debt/Backlog-Hinweise

Siehe auch [`TECH_DEBT_BACKLOG.md`](TECH_DEBT_BACKLOG.md), Abschnitt "Performance & Scale" für konkrete geplante Optimierungen.

Siehe auch [`docs/OBSERVABILITY_AND_MONITORING_PLAN.md`](OBSERVABILITY_AND_MONITORING_PLAN.md) für den übergeordneten Kontext von Performance-Messungen im Rahmen von Observability & Monitoring.

---

## 8. Änderungshistorie

| Datum      | Änderung                                                     |
|------------|--------------------------------------------------------------|
| 2025-12-07 | Phase 61 – Initiale Performance-Baseline & Umgebungsinfos   |

---

**Built with ❤️ and safety-first architecture**

