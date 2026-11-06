# EV_TECH_DEBT_D_20260128 — Item D Evidence Pack

## Reference
- Code PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1036
- Merge commit: 7394f78cb01555f0888e300c50145140884e957f
- MergedAt: 2026-01-28T05:58:36Z

## Scope
- Item D: Pandas `.fillna` Downcasting Warnings beheben (Cluster B).
- Ziel: Kein `FutureWarning` mehr durch Pattern wie `cond.shift(1).fillna(False)`; zugleich stabile dtypes (kein `object`) und identische Semantik (kein Lookahead; „fehlender Vorwert => False“).

## Changes (high-signal)
- Cluster-B Fix: Pattern auf `.shift(1, fill_value=False)` umgestellt (vermeidet NaN und verhindert object-downcast Pfade).
- Regression: `tests&#47;test_fillna_downcasting_regression.py` erzwingt `FutureWarning` als Fehler und prüft Semantik-Äquivalenz + dtype-Stabilität.
- Cleanup: Downcasting-spezifische und breite pandas-`FutureWarning` Filter entfernt (z.B. in `tests&#47;conftest.py`/pytest config).

## Tests executed
```bash
python3 -m pytest -q tests/test_fillna_downcasting_regression.py tests/test_strategies_smoke.py::test_all_strategies_generate_signals
python3 -m pytest -q -W default tests/test_fillna_downcasting_regression.py tests/test_strategies_smoke.py::test_all_strategies_generate_signals
python3 -m ruff format --check src/ tests/ scripts/
```

## Verification result
- PASS: Kein pandas-Downcasting `FutureWarning` mehr; `FutureWarning` als Fehler läuft grün.
- PASS: Strategien liefern keine `object` dtypes (dtype stabil).
- PASS: Filter Removal ist sicher (keine Regressions-Warnings im abgedeckten Scope).

## Risk / NO-LIVE
- NO-LIVE: Strategy signal generation + tests/warnings policy only. No live execution paths.
