# EV_TECH_DEBT_D_20260128

PR: `https://github.com/rauterfrank-ui/Peak_Trade/pull/1036`  
Merge Commit: `7394f78cb01555f0888e300c50145140884e957f`  
MergedAt: 2026-01-28T05:58:36Z

## Scope
- Item D: Pandas `.fillna` Downcasting Warnings beheben (Cluster B).
- Ziel: Kein `FutureWarning` mehr durch Pattern wie `cond.shift(1).fillna(False)`; zugleich stabile dtypes (kein `object`) und identische Semantik (kein Lookahead; „fehlender Vorwert => False“).

## Changes (high-signal)
- Cluster-B Fix: Pattern auf `shift(1, fill_value=False)` umgestellt und dtypes stabilisiert (kein `object`).
- Regression: `tests/test_fillna_downcasting_regression.py` erzwingt `FutureWarning` als Fehler und prüft Semantik-Äquivalenz + dtype-Stabilität.
- Cleanup: Downcasting-spezifische und breite pandas-`FutureWarning` Filter entfernt (Filter Removal) – Warning-Signal wird wieder sichtbar, ohne dass der Downcasting-Warn noch auftritt.

## Tests executed
- ```bash
  python3 -m pytest -q tests/test_fillna_downcasting_regression.py tests/test_strategies_smoke.py::test_all_strategies_generate_signals
  python3 -m pytest -q -W default tests/test_fillna_downcasting_regression.py tests/test_strategies_smoke.py::test_all_strategies_generate_signals
  python3 -m ruff format --check src/ tests/ scripts/
  ```

## Verification result
- PASS: Kein pandas-Downcasting `FutureWarning` mehr; `FutureWarning` als Fehler läuft grün.
- PASS: Strategien liefern keine `object` dtypes (dtype stabil).
- PASS: Filter Removal ist sicher (keine Regressions-Warnings im abgedeckten Scope).

## Risk / NO-LIVE
- NO-LIVE bestätigt: Änderungen betreffen Strategien/Tests/Test-Konfiguration; keine Live-Execution/Exchange Writes.
