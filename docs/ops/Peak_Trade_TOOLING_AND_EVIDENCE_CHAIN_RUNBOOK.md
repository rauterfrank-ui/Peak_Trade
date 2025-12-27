# Peak_Trade – Tooling & Evidence Chain Runbook (Ops-Style)

Stand: 2025-12-18 • Scope: **P0 → P1 → P2**  
Ziel: **kein Rewrite**, sondern **inkrementelle Upgrades** (PR-weise, optional via Extras, mit Tests/CI abgesichert).

---

## TL;DR – Operator Quick Start

### P0 (Dev-Speed): uv + ruff + minimal CI Gate
```bash
git checkout main && git pull --ff-only
git checkout -b chore/tooling-uv-ruff
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
ruff check src tests scripts
ruff format --check src tests scripts
pre-commit run --all-files
uv run pytest -q
# commit + PR
```

### P1 (Evidence Chain): MLflow + Quarto
```bash
git checkout main && git pull --ff-only
git checkout -b feat/experiments-mlflow-quarto
uv pip install -e ".[experiments]"
# run runner => results/<run_id>/*
mlflow ui  # optional
quarto render reports/quarto/backtest_report.qmd
```

### P2 (Boss Mode): DuckDB/Lake + Observability
```bash
git checkout main && git pull --ff-only
git checkout -b feat/lake-duckdb-otel
uv pip install -e ".[lake,observability]"
python scripts/query_lake.py --sql "SELECT COUNT(*) FROM ohlcv"
docker compose -f ops/observability/docker-compose.yml up
```

---

## 0) Grundprinzipien & Guardrails

- **No Rewrite / No Semantic Drift:** Backtest-/Strategy-Semantik bleibt unverändert.
- **Optional Dependencies via Extras:** Default bleibt lean. Feature-Flags/Extras schalten Add-ons an.
- **Graceful Degradation:** Fehlende deps → **WARN + Skip**, Runner läuft weiter.
- **Evidence Chain Standard:** `run_id` ist die Klammer für Artefakte, Tracking, Telemetrie.
- **PR-weise:** P0/P1/P2 sind getrennte PRs, damit Rollback/Review sauber ist.

---

## 1) Repository-Konventionen (Empfohlen)

### 1.1 Ordnerstruktur (Add-ons)
- Tooling/Doku:
  - `docs/dev/` (uv, pre-commit, tooling)
- Evidence/Reports:
  - `results/<run_id>/...` (Artefakte pro Run)
  - `reports/quarto/` (Templates)
  - `docs/reports/` (How-to)
- Data Lake:
  - `data/lake/` (Parquet)
  - `src/data/lake/` (writer + query)
- Observability:
  - `src/obs/` (OTel init + helpers)
  - `ops/observability/` (docker-compose + README)

### 1.2 Naming & IDs
- `run_id`: UUID4 (string)
- `results/<run_id>/` ist **single source of truth** für Artefakte.
- `run_id` soll in Logs/Traces/Tracking überall als Tag auftauchen.

---

## 2) P0 Runbook – uv + ruff + minimal CI Gate

### 2.1 Ziel / Exit Criteria (P0)
✅ Lokal:
- `ruff check src tests scripts`  
- `ruff format --check src tests scripts`  
- `pre-commit run --all-files`  
- `pytest` grün

✅ CI:
- Workflow `lint.yml` grün (ruff check, optional format check)

### 2.2 Umsetzung (Operator Steps)

#### Step A: Branch & Baseline
```bash
git checkout main
git pull --ff-only
git checkout -b chore/tooling-uv-ruff
```

#### Step B: Env & Deps
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
pre-commit install
```

#### Step C: Lint/Format
> **Empfehlung:** CI startet konservativ (nur sinnvolle Bug-Klassen blocken).  
> Format-Gate kann später „hart“ gemacht werden, wenn die Codebase aufgeräumt ist.

```bash
ruff check src tests scripts
ruff format --check src tests scripts
```

#### Step D: Pre-commit & Tests
```bash
pre-commit run --all-files
uv run pytest -q
```

#### Step E: Commit & PR
```bash
git add -A
git commit -m "chore(tooling): add uv + ruff lint gate"

gh pr create \
  --base main \
  --title "chore(tooling): add uv + ruff lint gate" \
  --body "## Summary
- Adds minimal CI lint workflow with ruff (path-filtered)
- Adds pre-commit config with ruff linter + formatter hooks
- Adds uv + pre-commit docs in docs/dev/
- Extends ruff configuration in pyproject.toml (conservative gate)

## Notes
- Conservative lint gate to avoid legacy churn
- Formatter enforced via pre-commit; repo-wide format CI can follow later
- No breaking changes

## Test plan
- \`ruff check src tests scripts\`
- \`pre-commit run --all-files\`
- \`uv run pytest -q\`"
```

### 2.3 Troubleshooting (P0)

**Problem:** `ruff format --check` schlägt überall fehl  
**Fix:**  
- Format nicht in CI erzwingen, nur pre-commit.  
- Repo-cleanup später: „format roll-out“ PR.

**Problem:** `pre-commit` nicht gefunden  
**Fix:**
```bash
uv pip install pre-commit
pre-commit install
```

**Problem:** CI Lint läuft nicht auf PR  
**Fix:** workflow trigger checken (`on: pull_request`) und path-filter nicht zu eng.

---

## 3) P1 Runbook – Evidence Chain (MLflow + Quarto)

### 3.1 Ziel / Exit Criteria (P1)
✅ Jeder Runner-Run erzeugt:
- `results/<run_id>/config_snapshot.*`
- `results/<run_id>/stats.json`
- `results/<run_id>/equity.csv`
- optional: `trades.parquet` / `trades.csv`

✅ Optional (wenn installiert):
- MLflow UI zeigt Run mit params/metrics/artifacts

✅ Quarto:
- Report rendert aus `results/<run_id>/...` zu HTML (1 Command)

### 3.2 Umsetzung (Operator Steps)

#### Step A: Branch
```bash
git checkout main
git pull --ff-only
git checkout -b feat/experiments-mlflow-quarto
```

#### Step B: Extras installieren
```bash
uv venv || true
source .venv/bin/activate
uv pip install -e ".[experiments]"
```

#### Step C: Run ausführen (Beispiel)
> Passe den Runner-Command an eure tatsächlichen Scripts/Configs an.
```bash
python scripts/run_strategy_from_config.py --config config/my_strategy.toml
# Erwartung: Output in results/<run_id>/
```

#### Step D: MLflow UI (optional)
```bash
mlflow ui
# typischerweise http://127.0.0.1:5000
```

#### Step E: Quarto Report (optional)
> Quarto ist ein externes Binary. Wenn installiert:
```bash
quarto --version
quarto render reports/quarto/backtest_report.qmd
```

#### Step F: „Last run report“ Convenience
> Empfohlen: Script, das den neuesten `results/<run_id>` findet und report rendert.
```bash
bash scripts/utils/render_last_report.sh
```

### 3.3 Standardisierte Artefakte (P1)

**Pflicht**
- `config_snapshot.toml` (raw)
- `config_snapshot.json` (parsed/normalized, falls möglich)
- `stats.json` (Kennzahlen)
- `equity.csv` (Zeitreihe)

**Optional**
- `trades.parquet` / `trades.csv`
- `debug/*.json`
- `plots/*.png` (wenn gewünscht)

### 3.4 Troubleshooting (P1)

**Problem:** MLflow nicht installiert / import error  
**Fix:**
```bash
uv pip install -e ".[experiments]"
python -c "import mlflow; print(mlflow.__version__)"
```

**Problem:** Quarto nicht installiert  
**Fix:** Installiere Quarto (OS-spezifisch), dann:
```bash
quarto --version
```

**Problem:** Tracking killt Runner  
**Fix (Design-Guard):**
- Tracker muss warn-only sein.
- `NullTracker` als default.
- Optional: `--tracking strict` erst später.

---

## 4) P2 Runbook – Data Lake + Observability

### 4.1 Ziel / Exit Criteria (P2)
✅ Lake:
- Parquet partitioned vorhanden
- DuckDB Query via CLI funktioniert (3 Beispielqueries)

✅ Observability:
- docker-compose stack läuft lokal
- run_id taucht als attribute/tag in traces/logs auf (wenn enabled)

### 4.2 Data Lake – Operator Steps

#### Step A: Branch
```bash
git checkout main
git pull --ff-only
git checkout -b feat/lake-duckdb-otel
```

#### Step B: Extras installieren
```bash
source .venv/bin/activate
uv pip install -e ".[lake]"
```

#### Step C: Lake befüllen (Beispiel)
> Je nach Integration: nach Normalizer/Cache oder nach Runner.
```bash
python scripts/build_lake_from_results.py  # falls vorhanden
# oder: Writer wird direkt beim Run aufgerufen
```

#### Step D: Queries
```bash
python scripts/query_lake.py --sql "SELECT COUNT(*) AS n FROM ohlcv"
python scripts/query_lake.py --sql "SELECT symbol, COUNT(*) FROM ohlcv GROUP BY 1 ORDER BY 2 DESC"
python scripts/query_lake.py --sql "SELECT * FROM ohlcv WHERE symbol='BTCUSDT' LIMIT 5"
```

### 4.3 Observability – Operator Steps

#### Step A: Extras installieren
```bash
uv pip install -e ".[observability]"
```

#### Step B: Lokalen Stack starten
```bash
docker compose -f ops/observability/docker-compose.yml up
```

#### Step C: Telemetry einschalten (Beispiel)
> Env vars exemplarisch – eure Implementierung kann anders heißen.
```bash
export PEAK_OTEL_ENABLED=1
export PEAK_OTEL_SERVICE_NAME="peak-trade"
export PEAK_OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

python scripts/run_strategy_from_config.py --config config/my_strategy.toml
```

### 4.4 Troubleshooting (P2)

**Problem:** DuckDB findet Tabellen nicht  
**Fix:** Parquet-Glob/Registration prüfen, Pfade stimmen?

**Problem:** docker compose ports belegt  
**Fix:** andere Ports mappen oder bestehende Services stoppen.

**Problem:** Telemetry spam / zu noisy  
**Fix:** nur „edges“ instrumentieren, sampling nutzen, debug-level reduzieren.

---

## 5) PR Workflow (Peak-Style, kurz & hart)

### 5.1 Pre-PR Checklist
- [ ] `git status` clean
- [ ] `pytest -q` grün
- [ ] ruff check/format-check grün
- [ ] docs aktualisiert (Quickstart/Runbook)
- [ ] optional deps via extras, graceful degradation

### 5.2 PR Merge (Empfohlen)
- Squash merge
- Branch löschen
- Post-merge checks:
  - `scripts/ci/validate_git_state.sh` (falls vorhanden)
  - `scripts/automation/post_merge_verify.sh` (falls vorhanden)
  - `pytest -q`

### 5.3 Traceability (Optional / euer Ops-Standard)
- Merge Log unter `docs/ops/PR_<N>_MERGE_LOG.md`
- Index `docs/ops/README.md` aktualisieren

---

## 6) „Was kommt danach?“ (Empfohlen)

1. **ADR 0001 mergen** (Entscheidung fixieren)
2. **P0 PR mergen** (Tooling speed)
3. **P1 PR bauen** (Evidence Chain)
4. **P2 PR bauen** (Lake + Observability)
5. Danach: **Retention Policy** + **Data Contracts** (OHLCV + Trades)

---

## Appendix A – Beispiel “Retention Policy” (später)
- `results/`: behalte letzte N runs (z.B. 200) oder max age (z.B. 30 Tage)
- `data/lake/`: nur gold dataset + curated partitions
- optional: `scripts&sol;cleanup_artifacts.py` (noch nicht implementiert) + CI/cron (nur wenn ihr wollt)

---

## Appendix B – Standard-Commands (Copy/Paste)

### Create + update venv
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Full local validation
```bash
ruff check src tests scripts
ruff format --check src tests scripts
pre-commit run --all-files
uv run pytest -q
```

---

_Ende Runbook._
