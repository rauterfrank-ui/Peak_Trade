# EV_TECH_DEBT_B_20260128

PR: `https://github.com/rauterfrank-ui/Peak_Trade/pull/1021`  
Merge Commit: `3d6aee01aee77373a190a509e93a38c7d5298ffc`  
MergedAt: 2026-01-28T01:35:56Z

## Scope
- Item B: Timeframe in `run_shadow_execution` nicht hardcoden, sondern aus dem OHLCV-DatetimeIndex ableiten.
- CLI Override bleibt möglich (`--timeframe`), kein stiller Fallback bei irregulärem Index.

## Changes (high-signal)
- Added: `infer_timeframe_from_index()` (median-delta bucket mapping, 5% tolerance, strict irregularity check).
- Added: CLI `--timeframe` (override wins).
- Removed: hardcoded `"1h"` im Registry-Logging.
- Added: Unit tests für Buckets + irregular/too-short failures.

## Tests executed
- ```bash
  uv run pytest -q tests/test_timeframe_infer.py
  ```

## Verification result
- PASS: Unit tests grün, Inferenz liefert erwartete Buckets; irreguläre Indizes führen zu klarem Fehler (kein stilles Default).

## Risk / NO-LIVE
- NO-LIVE bestätigt: Änderung betrifft nur Shadow-Run Metadata (`timeframe`) und Test-Code.
- Failure-mode ist explizit (ValueError) bei nicht-inferierbarem/irregulärem Index, außer Operator setzt `--timeframe`.
