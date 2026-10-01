# WP N5 Instrument Runtime Identity Closure — Implementation Evidence V1

```text
CURRENT_BASELINE_SHA=881efd47285ebccd83c0e57691e5832730c017a9
TRANSPLANT_SOURCE_SHA=89bda2857035ae104e6758eb582c8c892f3237d5
TRANSPLANT_PROOF=22/22 content preserved, no conflicts
BRANCH=feat/n5-instrument-runtime-identity-closure-current-v1
WORKTREE=/Users/frnkhrz/Peak_Trade/.wt_n5_instrument_runtime_identity_closure_current_v1
WP=N5_INSTRUMENT_RUNTIME_IDENTITY_CLOSURE
WP_SCOPE_CLOSURE_STATUS=COMPLETE_ON_CURRENT_BASELINE
```

Historical note: implementation was first developed on `TRANSPLANT_SOURCE_SHA` and
transplanted onto `CURRENT_BASELINE_SHA` (includes #6988 realm outcome provenance and
#6989 DDO meta-evidence CI debt on `origin/main`). Closure evidence below reflects
CURRENT truth after transplant, not a claim that original edits occurred on
`881efd472`.

## Contract derivation

- Reused `BoundInstrumentLaneIdentityV1` / `adjudicate_instrument_sensitive_state_v1` (hard-facts closure) for D4.
- Reused `extract_position_truth_v1` for D2 (no parallel position authority).
- Reused `evaluate_position_aware_rotation_v1` for D5 rotation semantics.
- N1 consumer remains sole governed-cycle invoke owner; closure composes ingress only.

## Wiring

- `invoke_occupied_lane_governed_cycle_n1_consumer_v1`: `candles_payload_by_lane`, `observed_portfolio`, per-lane C1/position/generation/reconciliation admission.
- `consume_recovered_isolated_lane_topology_v1` / `apply_isolated_lane_topology_v1`: open-position custody portfolio pin.
- `run_productive_full_autonomy_n5_runtime_orchestrator_v1`: membership pin + Cap24 per-lane candles fan-out (`cap24_lane_mv2_candles_payload_compose_v1`).

## Tests (CURRENT baseline validation)

| Suite | Role |
|-------|------|
| `tests/ops/test_current_mf_n5_instrument_runtime_identity_closure_v1.py` | D1–D3, generation, compose, authority pins |
| `tests/ops/test_current_mf_n5_instrument_runtime_identity_closure_scope_v1.py` | D4–D6, I11–I13, five-lane isolation |
| `tests/ops/test_current_mf_n5_recovered_topology_consumer_join_v1.py` | Topology consumer + portfolio |
| `tests/ops/test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.py` | N1 consumer regression |
| `tests/ops/test_current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.py` | FA orchestrator multi-lane |

Run on `CURRENT_BASELINE_SHA` with transplanted WIP:

- `./scripts/pt -m pytest -q` on all five suites in the table above → **57 passed** (2026-10-01 local).
- `./scripts/pt scripts/ops/ci_test_selection_v1.py --files-file <n5_final_files> --diff-base-ref origin/main` → **PR_BOUNDED_FULL**.
- `ruff format --check` + `ruff check` on 20 N5-bounded Python paths → **PASS**.

## Explicit non-claims

- `N_GT_1_ENABLED=false`, `MULTI_FUTURE_RUNTIME_AUTHORIZED=false`, `MAX_POSITIONS=1`, `POST_ALLOWED=false` unchanged.
- Productive live per-lane C1 ingress not proven by this WP.
- `JOIN_CAP23_SELECTION_AUTHORITY=false`, `JOIN_CAP24_BINDING_AUTHORITY=false`, `JOIN_TRADING_AUTHORITY=false` in closure constants.

## Scope boundary (operator)

Do not stage/commit untracked `runtime&#47;governance/**` if present in the worktree; it is
outside N5_INSTRUMENT_RUNTIME_IDENTITY_CLOSURE_V1.
