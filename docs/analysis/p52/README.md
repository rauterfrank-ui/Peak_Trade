# P52 — AI Switch-Layer v1

## Goal
Introduce a deterministic "switch-layer" that classifies market regime into:
- `bull`
- `bear`
- `neutral`

The output is intended to **mount onto** strategy/portfolio selection and risk posture later (deny-by-default for live).

## Scope
IN:
- Pure deterministic classifier `decide_regime_v1(returns, cfg)`
- Typed output `{regime, confidence, evidence}`
- Orchestration-safe wrapper `compute_market_regime_v1(...)`
- Unit tests + determinism test

OUT:
- No live execution changes
- No AI/model calls
- No data ingestion changes
- No portfolio switching logic yet

## Design
### Inputs
- `returns`: sequence of per-step returns (pct returns)

### Signals
- Mean return over `slow_window` (thresholded)
- EMA separation on cumulative return proxy (`fast_window` vs `slow_window`)

### Output
- `regime`: bull/bear/neutral
- `confidence`: bounded `[min_confidence, max_confidence]`
- `evidence`: computed stats + config snapshot

## Enable / Verify (local)
```bash
python3 -c "from src.ai.switch_layer import decide_regime_v1; print(decide_regime_v1([0.002]*80))"
pytest -q tests/p52/test_ai_switch_layer_v1.py
```
