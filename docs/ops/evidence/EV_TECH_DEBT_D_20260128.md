# EV_TECH_DEBT_D_20260128 — Item D Evidence Pack

## Reference
- Code PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1036
- Merge commit: 7394f78cb01555f0888e300c50145140884e957f
- MergedAt: 2026-01-28T05:58:36Z

## Scope / Changes
- Fix pandas FutureWarning: "Downcasting object dtype arrays on .fillna/.ffill/.bfill is deprecated..."
- Root cause (Cluster B): bool-ish series patterns using `.shift(1).fillna(False)` causing object dtype + silent downcast path.
- Remediation:
  - Replace with `.shift(1, fill_value=False)` to avoid NaN and prevent object downcast paths.
  - Remove downcasting-specific warning ignore filters (pytest.ini + tests/conftest.py), including the broad `ignore::FutureWarning:pandas.*`.

## Tests executed
- `python3 -m pytest -q tests&#47;test_fillna_downcasting_regression.py tests&#47;test_strategies_smoke.py::test_all_strategies_generate_signals`
- `python3 -m pytest -q -W default tests&#47;test_fillna_downcasting_regression.py tests&#47;test_strategies_smoke.py::test_all_strategies_generate_signals`
- `python3 -m ruff format --check src&#47; tests&#47; scripts&#47;`

## Verification result
- PASS: Regression test enforces that strategy signal paths do not emit the downcasting FutureWarning.
- PASS: Downcasting/Fillna FutureWarning filters removed; warnings-probe run is clean for the targeted suite.

## Risk / NO-LIVE
- NO-LIVE: Strategy signal generation + tests/warnings policy only. No live execution paths.
