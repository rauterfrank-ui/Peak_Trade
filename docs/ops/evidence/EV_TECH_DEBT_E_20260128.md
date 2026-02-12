# EV_TECH_DEBT_E_20260128

PR: `https://github.com/rauterfrank-ui/Peak_Trade/pull/1025`  
Merge Commit: `1cf7c45c963066f57c26e693d9fafab815e15b78`

## Scope
Item E: Plot generation optional via `--no-plots` (central runners)
- Adds `--no-plots` to key CLIs and propagates it to backtest reporting.
- Ensures HTML reports do not reference missing PNGs when plots are disabled (no broken/partial plots).

## Changes (main)
Target runners:
- `scripts&#47;run_strategy_from_config.py`
  - New: `--no-plots`
  - Wiring: `save_full_report(..., save_plots_flag=not args.no_plots)`
- `scripts&#47;run_portfolio_backtest.py` (only for `--save-individual`)
  - New: `--no-plots`
  - Wiring: `save_full_report(..., save_plots_flag=not args.no_plots)`

Core:
- `src&#47;backtest&#47;reporting.py`
  - `generate_html_report(..., include_plots=...)`
  - HTML references `*_equity.png` / `*_drawdown.png` only when `include_plots=True`

Artifacts / Behavior
- With `--no-plots`:
  - No PNG charts: `{run_name}_equity.png`, `{run_name}_drawdown.png`
  - HTML may still be generated, but contains no references to the missing PNGs.

## Tests executed
- CI required checks: PASS (Lint Gate, docs-reference-targets-gate, tests (3.11), etc.)
- Local (pre-PR):
  - `python3 -m pytest -q tests&#47;backtest&#47;test_reporting_no_plots.py tests&#47;scripts&#47;test_no_plots_cli_wiring.py`

## Verification result
- PASS: `save_full_report(..., save_plots_flag=False, save_html_flag=True)` writes no PNGs and the HTML contains no PNG references.
- PASS: CLIs expose and wire `--no-plots` correctly.

## Risk / NO-LIVE
LOW. Affects report artifacts only; does not change backtest results. No live exchange writes.
