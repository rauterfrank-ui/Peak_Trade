# PR #506 — Merge Log

## Summary
PR **#506** wurde per **Squash-Merge** nach `main` integriert und verdrahtet den **Tracking-Hook** in der `BacktestEngine` (optional, Default `None`). Zusätzlich wurden Tracking-Imports konsolidiert und begleitende Tests/Dokumente aktualisiert.

## Why
- **Backtest-Tracking** (Noop/optional MLflow) soll ohne harte Abhängigkeiten funktionieren.
- Tests und Integrationspfade sollten konsistent auf `core.tracking` zeigen.
- Additive Änderung: keine Verhaltensänderung ohne explizit übergebenen Tracker.

## Changescktest/engine.py`
  - `BacktestEngine.__init__` akzeptiert jetzt `tracker=...` (optional) und speichert ihn auf der Instanz.
- `src/core/tracking.py`
  - Kanonischer Tracking-Entry-Point (`core.tracking`) inkl. Tracker/Factory/Helper (Noop-safe; MLflow optional/lazy).
- Tests/Imports normalisiert:
  - `tests/test_tracking_noop.py`
  - `tests/test_tracking_mlflow_integration.py`
  - `tests/test_optuna_integration.py`
- Format/Lint-Fix:
  - `src/strategies/parameters.py` via `ruff format`
- Doku/Tools (additiv):
  - `docs/risk/RISK_LAYER_ROADMAP.md`
  - `scripts/rescue/pin_unreferenced_commits.sh`

## Verification
- Lokal (Operator):
  - `python -m pytest -q tests/test_tracking_noop.py tests/test_tracking_mlflow_integration.py`
  - `ruff check ...` / `ruff format --check ...`
- CI: Lint Gate war initial wegen `ruff format`-Diff rot; wurde durch Reformat-Fix behoben.

## Risk
- **Low**: Additiver optionaler Parameter (`tracker=None` Default).
- Tracking bleibt **optional** (keine harte MLflow-Abhängigkeit bei Import).
- Änderungen sind überwiegend Import-/Verdrahtungs- und Doku-/Tool-Erweiterungen.

## Operator How-To
- Minimal (Noop):
  - `engine = BacktestEngine(..., tracker=NoopTracker())`
- Optional MLflow (nur wenn installiert):
  - `engine = BacktestEngine(..., tracker=MLflowTracker(...))`
- Config-basiert:
  - `tracker = build_tracker_from_config(get_config())`
  - `engine = BacktestEngine(..., tracker=tracker)`

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/506
- Merge-Commit (squash): `56a0502` (HEAD nach Merge)
