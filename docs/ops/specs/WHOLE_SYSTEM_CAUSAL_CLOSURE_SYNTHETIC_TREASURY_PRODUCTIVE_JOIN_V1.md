# WHOLE_SYSTEM_CAUSAL_CLOSURE_SYNTHETIC_TREASURY_PRODUCTIVE_JOIN_V1

docs_token: DOCS_TOKEN_WHOLE_SYSTEM_CAUSAL_CLOSURE_SYNTHETIC_TREASURY_PRODUCTIVE_JOIN_V1

RUNTIME_AUTHORIZATION_EFFECT=NONE

## Purpose

Machine-checkable productive joins closing:

1. STEP-29P admitted capital lineage → EEA universe acquisition (lineage on provenance).
2. Same Treasury/29P handoff producer output → `PortfolioCapitalReservationBudgetOwnerV1`.

Synthetic treasury test values (`SIMULATED_OKX_EEA_DEPOSIT_10000_EUR`) are **fixtures only**;
they do not grant productive authority or external-effect rights.

## Owners

| Join | Module |
|------|--------|
| 29P → EEA acquisition | `src/ops/full_core_live_path_composition_root_v1/current_productive_step_29p_to_eea_acquisition_productive_join_v1.py` |
| 29P → portfolio budget | `src/ops/full_core_live_path_composition_root_v1/current_productive_step_29p_to_portfolio_budget_productive_join_v1.py` |
| Whole-system E2E runner | `scripts/ops/run_whole_system_causal_closure_from_synthetic_treasury_zero_e2e_v1.py` |

## Tests

- `tests/ops/test_current_productive_step_29p_productive_causal_join_v1.py`
