# ADR 0001 — Peak_Trade Tool-Stack: Dev-Speed + Evidence Chain + Lake + Observability

**Datum:** 2025-12-18  
**Status:** PROPOSED (wird „ACCEPTED“, sobald gemerged)  
**Entscheidungs-Owner:** Peak_Trade Maintainers / Operator

---

## 1) Kontext

Peak_Trade ist ein modularer Trading-/Backtest-/Ops-Stack mit hoher Test- und Governance-Disziplin.  
Die nächsten Skalierungsschritte (mehr Runs, mehr Daten, mehr Experimente, mehr Live-Nähe) erfordern:

- **weniger Tooling-Reibung** (Setup/CI/Dev-Speed)
- **reproduzierbare Evidence** (Run-ID → Config → Artefakte → Metrics)
- **Query-fähige Datenhaltung** (lokaler Research-Lake)
- **Observability/Forensik** (Traces/Logs/Latency, korreliert auf run_id)

Wichtig: **kein Rewrite** und **keine Breaking Changes** der Kernsemantik (Backtest/Runner/Strategien).

---

## 2) Problem / Ziele

### Ziele (Goals)
1. **Dev-Speed & Hygiene**: schnelleres Setup, schnellere CI, konsistentes Lint/Format.
2. **Evidence Chain**: jeder Run liefert deterministic artifacts + optional Tracking.
3. **Research Lake**: Parquet + DuckDB für lokale Analytics/Screening.
4. **Observability**: optionale Telemetrie (Tracing/Logs) für Debugging/Latency.

### Nicht-Ziele (Non-Goals)
- Kein Umbau der Core-Architektur.
- Kein Zwang zu neuen Dependencies im Default-Install.
- Keine „Mass-Reformat PRs“ ohne expliziten Cleanup-Plan.
- Kein Live-Autotrading-Enablement durch diese ADR.

---

## 3) Entscheidung (Decision)

Wir führen einen **inkrementellen Tool-Stack** ein, in 3 PR-Stufen:

### P0 (sofort): **uv + ruff + minimal CI Gate**
- `uv` als schneller Env/Dependency Runner für Dev/CI (optional, aber empfohlen).
- `ruff` als Lint + Formatter.
- Minimaler CI Gate: `ruff check` + optional `ruff format --check` (konservativ starten).
- pre-commit Hooks: ruff + ruff-format.

### P1 (riesiger Hebel): **MLflow Tracking + Quarto Report Template**
- Standardisierte Run-Struktur: `results/<run_id>/...`
- Optionales MLflow Tracking (extras) für params/metrics/artifacts.
- Quarto Template für reproduzierbare HTML-Reports aus `results/<run_id>`.

### P2 (Boss-Mode): **DuckDB+Parquet Lake + OpenTelemetry + Grafana/Loki**
- Local Data Lake (Parquet partitioned) + DuckDB Query Layer + CLI.
- Optional Observability via OpenTelemetry, lokales docker-compose für Grafana/Loki/OTel Collector.

---

## 4) Leitprinzipien (Implementation Principles)

1. **Optional Dependencies via Extras**
   - Beispiele: `.[dev]`, `.[experiments]`, `.[lake]`, `.[observability]`
   - Default bleibt lean; Features schalten sich per Install/Env-Flag zu.

2. **Graceful Degradation**
   - Wenn Dependencies fehlen: **WARN + skip**, keine Run-Abbrüche.
   - Optionaler `--strict` Modus kann später eingeführt werden.

3. **No Semantic Drift**
   - Backtest-/Strategy-Semantik bleibt unverändert.
   - Tooling/Tracking darf nur beobachten & dokumentieren, nicht „optimieren“.

4. **Evidence Chain Standard**
   - `run_id` ist zentral und wird überall mitgeführt (Artefakte, Tracking, Telemetrie).

---

## 5) Konkrete Scope-Definition (Was gehört dazu?)

### P0 Scope
- `pyproject.toml`: ruff config (konservativ)
- `.github/workflows/lint.yml`: ruff CI job (minimal)
- `.pre-commit-config.yaml`: ruff hooks
- `docs/dev/UV_QUICKSTART.md`, `docs/dev/PRECOMMIT.md`

### P1 Scope
- `src/experiments/tracking/`:
  - `base.py` (Interface), `null.py` (No-op), `mlflow_tracker.py`
- Runner Integration:
  - `run_id` generieren
  - `results/<run_id>/config_snapshot.*`
  - `results/<run_id>/stats.json`, `equity.csv` (optional trades.*)
- `reports/quarto/backtest_report.qmd`
- `docs/reports/REPORTING_QUICKSTART.md`
- Convenience Script: `scripts/utils/render_last_report.sh` (oder python)
- Minimal Tests: NullTracker + results-writer smoke

### P2 Scope
- `src/data/lake/`:
  - `lake_writer.py`, `duckdb_client.py`
- `scripts/query_lake.py`
- `docs/data/LAKE_GUIDE.md`
- `src/obs/otel.py` + edge instrumentation
- `ops/observability/docker-compose.yml` + `README.md`

---

## 6) Konsequenzen (Consequences)

### Positive
- Deutlich schnellerer Dev/CI Loop (P0).
- Reproducibility + Auditability via Evidence Chain (P1).
- Schnellere Research-Iteration & Screening via DuckDB/Parquet (P2).
- Debugging/Latency-Forensik via Observability (P2).

### Trade-offs / Costs
- Mehr Tooling-Komplexität (aber optional).
- Einmalige Integrationskosten pro PR.
- Disziplin nötig: artifacts/retention, Logging-Standards, Naming.

---

## 7) Risiken & Mitigations

1. **Zu großer Format-Diff (P0)**
   - Mitigation: konservativer Start, Format in pre-commit, repo-weites Reformat später geplant.

2. **Tracking/Telemetry verursacht Instabilität (P1/P2)**
   - Mitigation: try/except, warn-only, strict nur optional, tests für NullTracker/Writer.

3. **Artefakt-Sprawl / Storage-Wachstum (P1/P2)**
   - Mitigation: retention policy (später), Kompression (Parquet), klarer results/ Lake Ordner.

4. **Schema Drift im Lake**
   - Mitigation: Data Contracts (Pandera/GE) + dtype enforcement im Writer.

---

## 8) Verifikation / Exit Criteria

### P0 Exit Criteria
- `ruff check src tests scripts` grün
- `ruff format --check ...` grün (oder bewusst erst später aktiv)
- CI lint workflow grün
- pre-commit läuft lokal

### P1 Exit Criteria
- Jeder Runner Run erzeugt `results/<run_id>/...` deterministisch
- MLflow optional: Run erscheint in MLflow UI, artifacts/metrics vorhanden
- Quarto Report rendert aus einem run_id (1 command)

### P2 Exit Criteria
- Lake befüllbar + querybar (DuckDB) mit 3 Beispielqueries
- Observability optional: Traces/Logs korrelierbar (run_id), local stack lauffähig

---

## 9) Alternativen (erwogen, nicht gewählt)

- Poetry/PDM statt uv: möglich, aber uv bietet Speed/Ergonomie (lokal & CI) bei geringer Reibung.
- Black + isort + flake8 statt ruff: funktioniert, aber ruff reduziert Tool-Sprawl und ist schneller.
- W&B statt MLflow: stärkeres SaaS, aber MLflow passt „local-first“ besser.
- Vollständige Observability Plattform (Tempo/Prometheus) sofort: zu schwergewichtig; wir starten minimal.

---

## 10) Follow-ups (separat zu tracken)

1. **Master-Runbook**: `docs/ops/TOOLING_AND_EVIDENCE_CHAIN.md` (1-command flows + troubleshooting)
2. **Retention Policy**: results/ & lake cleanup schedule (optional automation)
3. **Data Contracts**: OHLCV + Trades Schema (Pandera first)
4. **Correlation IDs**: run_id in logs/traces konsequent überall

---

## 11) PR-Plan (empfohlen)

1. PR #1: `chore(tooling): add uv + ruff lint gate`
2. PR #2: `feat(experiments): add MLflow tracking + Quarto report template`
3. PR #3: `feat(lake+obs): add duckdb/parquet lake and otel stack`

---

**Ende ADR 0001**
