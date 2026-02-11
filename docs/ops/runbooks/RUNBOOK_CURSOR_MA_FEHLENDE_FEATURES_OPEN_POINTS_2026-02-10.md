# Cursor Multi-Agent Runbook — Offene Features in Peak_Trade (Einstieg → Endpunkt)

**Quelle:** [docs/FEHLENDE_FEATURES_PEAK_TRADE.md](../../FEHLENDE_FEATURES_PEAK_TRADE.md) (Stand 2026-02-10, letzter Repo-Abgleich 2026-02-10)  
**Runbook-Version:** 2026-02-10T12:00:00+01:00 (Europe/Berlin)  
**Ziel:** Für die **noch offenen** Punkte ein **logisches, sequentielles** Abarbeitungs-Runbook, das in **Cursor Multi-Agent Chats** (bash-only) ausführbar ist, mit klaren **Einstiegs-/Endpunkten**, Artefakt-Pfaden und Evidence.

### Stand / Fortschritt (wird bei Abarbeitung aktualisiert)

| Block | Slug | Status | Anmerkung |
|-------|------|--------|-----------|
| A | sweep-pipeline-cli | ✅ erledigt | `scripts/run_sweep_pipeline.py` mit --run/--report/--promote, Artefakte unter `out/research/<sweep_id>/` (2026-02-11) |
| B | heatmap-template-2x2 | ✅ erledigt | `create_standard_2x2_heatmap()` in `src/reporting/sweep_visualization.py`, 2 params × 2 metrics, Tests (2026-02-11) |
| C | vol-regime-universal-wrapper | offen | |
| D | corr-matrix-param-metric | offen | |
| E | rolling-window-stability | offen | |
| F | sweep-comparison-tool | offen | |
| G | metrics-ulcer-recovery | ✅ erledigt | Ulcer Index + Recovery Factor in `src/backtest/stats.py`, Engine + `compute_backtest_stats`, Sweep-Defaults, Tests (2026-02-11) |
| H | nightly-sweep-automation | offen | |
| I | feature-importance-wrapper | offen | |
| J | feature-engine-skeleton | offen | |

**Nächster logischer Schritt:** Block C (Vol-Regime Universal Wrapper).

---

## 0) Konventionen (wichtig für Reproduzierbarkeit)

**Arbeitsweise pro Feature-Block:**
- Neuer Branch pro Block: `feat&#47;<slug>`
- Jede MA-Session schreibt:
  - `out&#47;ops&#47;cursor_ma&#47;<slug>&#47;MANIFEST.json`
  - `out&#47;ops&#47;cursor_ma&#47;<slug>&#47;JOURNAL.ndjson`
  - `out&#47;ops&#47;cursor_ma&#47;<slug>&#47;EVIDENCE.md`
- Finaler Abschluss pro Block:
  - Tests/Lint: mindestens `ruff format --check` + relevante `pytest -q`
  - Commit mit eindeutigem Scope
  - PR optional (wenn du die Repo-Policy so fährst)

**Bash-only:** Alle Schritte unten sind als copy/paste Befehlsfolgen geschrieben.

---

## 1) Einstiegspunkt (einmal pro Arbeitssession)

```bash
set -euo pipefail

# Repo-Root (anpassen falls nötig)
cd "$(git rev-parse --show-toplevel)"

git status -sb
git fetch origin --prune
git checkout main
git pull --ff-only origin main

# Arbeitsordner für diese Session
export MA_TS="2026-02-10T12:00:00+01:00"
export MA_ROOT="out/ops/cursor_ma/session_${MA_TS//:/-}"
mkdir -p "$MA_ROOT"

# Snapshot
git rev-parse HEAD | tee "$MA_ROOT/HEAD.txt"
git status -sb | tee "$MA_ROOT/STATUS.txt"
```

**Endpunkt dieses Abschnitts:** `main` ist sauber und synchron; Session-Ordner mit HEAD/STATUS existiert.

---

## 2) Offene Punkte → Logische Abarbeitungsreihenfolge

Aus [docs/FEHLENDE_FEATURES_PEAK_TRADE.md](../../FEHLENDE_FEATURES_PEAK_TRADE.md) sind offen (Schwerpunkte):
- Research/Strategy (5.1): Pipeline-CLI, Heatmap-Template, Vol-Regime Wrapper, Corr-Matrix, Rolling Stability, Sweep-Comparison, zusätzliche Metriken, Regime-adaptive Strategien, Nightly Sweeps, interaktive Dashboards, Feature-Importance Wrapper
- Feature-Engine/Meta-Labeling: `src/features/` Placeholder, Triple-Barrier Labels / Feature Extraction TODO
- Real-Time/Streaming, Live-Execution, Multi-Exchange, Web-Dashboard (Auth/WebSocket), Risk Auto-Liquidation, API-Doku, Skalierung, etc.
- Tech-Debt / Stubs: Kill-Switch, PagerDuty, Adapter Protocol Placeholder, R&D Strategien TODO

**Pragmatische Reihenfolge (Dependency-first):**
1. **Research Tooling Core** (unified sweep pipeline + standard heatmap template + metrics add-ons)  
2. **Strategy Wrappers** (vol-regime universal wrapper + regime-adaptive switching)  
3. **Comparisons & Robustness** (rolling stability + sweep comparison + correlation plots)  
4. **Automation** (nightly sweeps + alerts, ohne Live-Trading)  
5. **Feature-Importance Wrapper** (SHAP/Permutation: vereinheitlichen, reports)  
6. **Feature-Engine Skeleton** (`src/features/` echte Pipeline + meta-labeling TODOs)  
7. Danach: Streaming/Live/Multi-Exchange/Web-Auth (größerer Scope, separate Runbooks sinnvoll)

Die folgenden Abschnitte liefern **konkrete Cursor-MA Blöcke** für 1–6.

---

## 3) Block A — Unified Pipeline CLI (`run_sweep_pipeline.py`)

### Einstieg
- Ziel: Ein einziges CLI, das `--run&#47;--report&#47;--promote` orchestriert und Artefakte standardisiert ablegt.
- Endzustand: CLI vorhanden + Tests/Smoke + Doku-Update.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="sweep-pipeline-cli"
git checkout -b "feat/${SLUG}"

mkdir -p "out/ops/cursor_ma/${SLUG}"

# Cursor Multi-Agent: Planner → Implementer → Critic
# (Command Palette in Cursor): "Cursor: Multi Agent Orchestration"
# Input: Ziel + Constraints (bash-only, safety-first, reproducible)
```

**MA Prompt (copy/paste in Cursor MA):**
```text
[GOAL]
Implement a unified sweep pipeline CLI: scripts/run_sweep_pipeline.py (or src/cli/run_sweep_pipeline.py if that's the convention)
with subcommands or flags:
  --run (execute sweep), --report (generate plots/reports), --promote (move "best" configs into registry/presets)
Write artifacts to out/research/<sweep_id>/...
Ensure idempotency: rerun does not corrupt outputs; new run_id each time unless explicitly provided.

[CONSTRAINTS]
- No live trading; research-only
- Must integrate with existing sweep runners + reporting modules (stats, sweep_visualization, portfolio_builder)
- Provide at least one smoke test + minimal unit tests
- Add logging + clear exit codes
- Update docs where appropriate

[OUTPUTS]
- new CLI file
- tests
- docs snippet
- evidence: paths and sample run
```

### Lokal: Smoke + Evidence + Commit
```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Lint/Test (anpassen je nach Repo-Targets)
ruff format --check src tests scripts || true
pytest -q || true

# Minimal Smoke (CLI vorhanden):
python3 scripts/run_sweep_pipeline.py --help 2>&1 | tee "out/ops/cursor_ma/${SLUG}/smoke_help.txt" || true

# Evidence
git diff | tee "out/ops/cursor_ma/${SLUG}/DIFF.patch"

# Commit
git add -A
git commit -m "research: add unified sweep pipeline CLI" || true
```

### Endpunkt
- Branch enthält CLI + Tests/Doku.
- Evidence liegt unter `out&#47;ops&#47;cursor_ma&#47;sweep-pipeline-cli&#47;`.

---

## 4) Block B — Standard Heatmap Template (2 params × 2 metrics)

### Einstieg
- Ziel: Generisches Template, nicht nur Drawdown; mindestens zwei Metriken (z.B. Sharpe + MaxDD) und zwei Parameter-Achsen.
- Endzustand: API in `src/reporting/sweep_visualization.py` (oder passender Ort) + Tests + example output.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="heatmap-template-2x2"
git checkout -b "feat/${SLUG}"
mkdir -p "out/ops/cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Add a standard heatmap template that supports:
- x_param, y_param
- metric_a, metric_b
- output: two heatmaps (metric_a and metric_b) with consistent labeling
- handles missing grid points gracefully

[CONSTRAINTS]
- Reuse existing drawdown heatmap utilities if present
- Deterministic output file names
- Add a small test that builds a tiny synthetic sweep dataframe

[OUTPUTS]
- API function + docstring
- test
- example call in research CLI or docs
```

**Lokal:**
```bash
ruff format --check src tests scripts || true
pytest -q || true
git add -A
git commit -m "reporting: add standard 2x2 heatmap template" || true
```

**Endpunkt:** 2×Heatmap Template ist verfügbar, tests grün.

**Beispiel (nach Implementierung):**
```python
from pathlib import Path
from src.reporting.sweep_visualization import create_standard_2x2_heatmap

paths = create_standard_2x2_heatmap(
    df=sweep_df,
    x_param="fast_period",
    y_param="slow_period",
    metric_a="sharpe_ratio",
    metric_b="max_drawdown",
    sweep_name="ma_sweep",
    output_dir=Path("out/research/run_01/report"),
)
# -> paths["metric_a"], paths["metric_b"] (PNG-Pfade)
```

---

## 5) Block C — Vol-Regime Universal Wrapper (für alle Strategien)

### Einstieg
- Ziel: Eine dekorator-/wrapper-basierte Lösung, die jede Strategie optional mit Regime-Filter (z.B. only trade in specific vol regimes) versieht.
- Endzustand: Wrapper im `src/strategies/` oder `src&#47;core&#47;strategy_wrappers.py` + tests.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="vol-regime-universal-wrapper"
git checkout -b "feat/${SLUG}"
mkdir -p "out/ops/cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Implement a universal vol-regime wrapper that can wrap any Strategy instance:
- takes regime labels series + allowed regimes
- masks signals/positions outside allowed regimes
- works in backtest and sweeps
- minimal config surface (yaml/json friendly)

[CONSTRAINTS]
- Do not break existing Strategy interface
- Add unit tests for signal masking + edge cases (NaN regimes)
- Ensure audit/logging indicates regime gating was applied

[OUTPUTS]
- wrapper module
- tests
- docs snippet in strategy docs
```

**Endpunkt:** Wrapper existiert, ist per Config nutzbar.

---

## 6) Block D — Correlation Matrix Plot (Parameter–Metrik)

### Einstieg
- Ziel: Plot/Report, der Korrelationen zwischen Parametern (numeric) und Zielmetriken zeigt (Spearman/Pearson).
- Endzustand: Funktion + CLI hook + Test.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="corr-matrix-param-metric"
git checkout -b "feat/${SLUG}"
mkdir -p "out/ops/cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Add a correlation matrix report:
- inputs: sweep results dataframe with params + metrics
- computes correlation (Spearman default) between numeric params and selected metrics
- outputs: heatmap plot + csv table
- integrates into report step of unified sweep pipeline

[CONSTRAINTS]
- Deterministic ordering of columns
- Gracefully skip non-numeric params
- Unit test for correlation computation on synthetic data
```

**Endpunkt:** Report ist Bestandteil des `--report`-Steps.

---

## 7) Block E — Rolling-Window Stability (Top-Params über 6-Monats Fenster)

### Einstieg
- Ziel: Stability-Analyse: Parameter-Rankings je Window; z.B. top-k Frequenz oder Kendall tau zwischen Fenstern.
- Endzustand: Funktion + Report + Test.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="rolling-window-stability"
git checkout -b "feat/${SLUG}"
mkdir -p "out/ops/cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Implement rolling-window stability analysis for sweeps:
- windows: e.g. 6 months (configurable)
- for each window: run same sweep or evaluate same param grid on that window
- compute stability metrics: top-k overlap, kendall tau, rank volatility
- output: table + plot

[CONSTRAINTS]
- Must be runnable offline; deterministic
- If full recomputation is too heavy, allow "evaluate existing trade logs" if available
- Provide at least one fast unit test and one smoke example
```

**Endpunkt:** Stability report exists and is callable via pipeline `--report`.

---

## 8) Block F — Sweep Comparison Tool

### Einstieg
- Ziel: Zwei Sweeps vergleichen: best configs, distribution shifts, winner/loser per metric.
- Endzustand: CLI subcommand + report.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="sweep-comparison-tool"
git checkout -b "feat/${SLUG}"
mkdir -p "out/ops/cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Add a sweep comparison tool:
- compare two sweep runs by run_id/path
- outputs: side-by-side summary, deltas for top-N configs, histogram/ECDF for key metrics
- writes a single markdown report and plots

[CONSTRAINTS]
- pure research tooling; no live execution hooks
- deterministic output path structure
- add a unit test for summary/delta logic
```

**Endpunkt:** Comparison tool can be called from CLI.

---

## 9) Block G — Additional Metrics (Ulcer Index, Recovery Factor)

### Einstieg
- Ziel: Ergänzung der Stats-Engine + Sweep outputs.
- Endzustand: `src/backtest/stats.py` erweitert + tests.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="metrics-ulcer-recovery"
git checkout -b "feat/${SLUG}"
mkdir -p "out/ops/cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Add Ulcer Index and Recovery Factor metrics:
- integrate into backtest stats and sweep reporting
- ensure they appear in CSV/JSON outputs

[CONSTRAINTS]
- definitions documented in docstring (no external links required)
- test metrics on small synthetic equity curves
```

**Endpunkt:** Metrics appear in reports and are unit-tested.

---

## 10) Block H — Nightly Sweep Automation (Cron/Scheduler + Alerts)

### Einstieg
- Ziel: Offline/CI automation, die nightly sweeps ausführt und Ergebnisse ablegt + optional notify (stub ok).
- Endzustand: GitHub Actions workflow oder lokaler scheduler wrapper (abhängig von Policy).

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="nightly-sweep-automation"
git checkout -b "feat/${SLUG}"
mkdir -p "out/ops/cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Add nightly sweep automation:
- a workflow (GitHub Actions) or local cron-friendly script
- runs unified sweep pipeline with a configured set
- uploads/stores artifacts
- emits a compact summary (markdown)

[CONSTRAINTS]
- no secrets required
- notifications can be stubbed (print summary); avoid PagerDuty unless already implemented
- respect existing CI gates and repo conventions
```

**Endpunkt:** automation definition exists and is documented.

---

## 11) Block I — Feature-Importance Wrapper (SHAP/Permutation)

### Einstieg
- Ziel: „Universal“ wrapper/report, der vorhandene SHAP/Permutation-Logik standardisiert abrufbar macht.
- Endzustand: CLI `--feature-importance` + report artifacts.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="feature-importance-wrapper"
git checkout -b "feat/${SLUG}"
mkdir -p "out/ops/cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Implement a standard feature-importance report wrapper:
- supports permutation importance as baseline
- optional SHAP if dependency available (guarded import)
- outputs: csv table + plot + markdown summary
- integrates with research pipeline report step

[CONSTRAINTS]
- no hard dependency on heavy libs; SHAP optional
- deterministic output
- unit tests for permutation importance on synthetic model
```

**Endpunkt:** Unified feature importance report exists.

---

## 12) Block J — Feature-Engine Skeleton + Meta-Labeling TODOs (`src/features/`)

### Einstieg
- Ziel: `src/features/` wird echte Pipeline (compute features, store feature matrix, versioned schema).
- Zudem: `compute_triple_barrier_labels` + `_extract_features` nicht mehr Placeholder.
- Endzustand: Minimal viable feature-engine that plugs into research.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

export SLUG="feature-engine-skeleton"
git checkout -b "feat/${SLUG}"
mkdir -p "out/ops/cursor_ma/${SLUG}"
```

**MA Prompt:**
```text
[GOAL]
Turn src/features/ from placeholder into a minimal feature engine:
- feature schema/versioning (simple: dataclass + version string)
- compute feature matrix from OHLCV (returns, vol, rolling stats, regime features)
- store outputs deterministically (parquet/csv) under out/features/<run_id>/
- implement compute_triple_barrier_labels (no placeholders)
- implement _extract_features with a minimal meaningful set

[CONSTRAINTS]
- do not require exotic deps; use pandas/numpy
- keep interfaces narrow; testable functions
- add unit tests for label generation and feature extraction
- no live execution hooks
```

**Endpunkt:** Placeholder removed; features + labels are real, tested, and documented.

---

## 13) Global Endpunkt (für jeden Block)

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Final sanity
git status -sb
ruff format --check src tests scripts || true
pytest -q || true

# Evidence snapshot (always)
export SLUG="<set_this>"
mkdir -p "out/ops/cursor_ma/${SLUG}"
git rev-parse HEAD | tee "out/ops/cursor_ma/${SLUG}/HEAD.txt"
git log -1 --oneline | tee "out/ops/cursor_ma/${SLUG}/LOG1.txt"
```

Optional PR:
```bash
# If gh works in your environment:
# gh pr create --fill
# gh pr view --web
```

---

## 14) Quick Index — Welche Blöcke sind „must-have“ vs. „nice-to-have“

**Must-have (macht den Research-Track „rund“):**
- Block A (Pipeline CLI)
- Block B (Heatmap Template)
- Block C (Vol-Regime Wrapper)
- Block D (Corr Matrix)
- Block G (Ulcer/Recovery metrics)

**Nice-to-have / Iterativ:**
- Block E/F (Stability/Comparison)
- Block H (Nightly)
- Block I (Feature-Importance Wrapper)
- Block J (Feature-Engine + Meta-Labeling)

---

## 15) Datei-Output / Crawler-Hinweis

Diese Datei ist **crawler-eindeutig** benannt und enthält im Titel die Scope-Keywords:
- `CURSOR_MA_RUNBOOK`
- `FEHLENDE_FEATURES`
- `OPEN_POINTS`
- Datum

---

## Closeout — Block G Evidence (metrics-ulcer-recovery)

**Date:** 2026-02-10

### Evidence files
- Present: DIFF.patch, STATUS.txt, HEAD.txt, LOG1.txt
- DIFF.patch: 0 bytes (working tree clean)

### Verify commands actually executed
- ruff format --check: **NOT executed** (ruff not in PATH; use `python3 -m ruff` on macOS)
- pytest: executed as `python3 -m pytest tests/backtest/test_stats_ulcer_recovery.py -q` → **8 passed**

### Cross-check
- LOG1 = `5e279236 reporting: add standard 2x2 heatmap template`
- Ulcer/Recovery changes are also in commit `5e279236` (git log -S ulcer / -S recovery_factor → same commit)
- Interpretation: Branch `feat/metrics-ulcer-recovery` forked after Block-G changes already existed → no additional diff/commit on this branch.

### New evidence artifacts
- `out/ops/cursor_ma/metrics-ulcer-recovery/EVIDENCE_SUMMARY.md`
- `out/ops/cursor_ma/metrics-ulcer-recovery/EVIDENCE_SHA256.txt` (macOS `shasum -a 256`)

### If a dedicated Block-G commit is required
- Option A: branch from parent commit before `5e279236`, stage only Block-G files/hunks, commit.
- Option B: keep as-is (no-op branch), confirm main contains Block-G, then delete branch.

### Portable verify helper — hash flags fix

- Problem: `portable_verify.sh` hashed every pytest arg; flags like `-q` caused hash failures.
- Fix: hash only existing file paths; ignore args starting with `-` and non-existent paths.
- Behavior:
  - If no files are passed (or only flags): prints `[hash] no files to hash (pass file paths as args; flags are ignored)` and exits 0.
  - If files are passed: hashes via `sha256sum` when available, else `shasum -a 256` per file (macOS).
- Commit: 50a2dd4a ops: make portable_verify hash only existing files (ignore flags)

Evidence: `out/ops/cursor_ma/metrics-ulcer-recovery/closeout_meta2/` (STATUS.txt, LOG1.txt, DIFF_CACHED.patch, SHA256.txt)

### Closeout — normalize_validator_report_cli (PYTHONPATH-free) green
- Fix commit: 604a53fb (scripts/aiops/normalize_validator_report.py)
- Evidence: out/ops/portable_verify_failures/fix_normalize_validator_report_cli/
