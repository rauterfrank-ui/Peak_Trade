# Allowed Files

## This preparation PR (only)

```text
docs/evidence/bollinger_entry_side_canonical_composition_slice_plan_v1/**
```

## Deferred future productive slice (NOT authorized now)

Only after a **separate Operator-GO** that explicitly selects OPTION_B (or another ratified option):

| Candidate surface | Role |
|-------------------|------|
| New Master-V2-scoped composer module (TBD name under `src&#47;trading&#47;master_v2&#47;`) | Projection&#47;composition only |
| `src&#47;backtest&#47;strategy_signal_suitability_agreement_adapter_v1.py` | Consume events; still no Bollinger side invent |
| Focused contract tests under `tests&#47;trading&#47;master_v2&#47;` &#47; `tests&#47;backtest&#47;` | Fail-closed locks |
| Governance SSOT JSON under `config&#47;governance&#47;` | Ratify OPTION_B if chosen |

Bollinger producer (`src&#47;strategies&#47;bollinger.py`) should remain event-geometry only unless a later GO says otherwise.
