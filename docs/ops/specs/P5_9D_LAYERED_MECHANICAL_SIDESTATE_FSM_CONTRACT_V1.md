---
docs_token: DOCS_TOKEN_P5_9D_LAYERED_MECHANICAL_SIDESTATE_FSM_CONTRACT_V1
status: active
scope: P5.9D layered post-projection mechanical SideState FSM contract only (no bind)
---

# P5.9D Layered Mechanical SideState FSM Contract v1

```text
LAYERED_MECHANICAL_FSM_CONTRACT_V1_DEFINED=true
REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED=false
PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED=false
FINAL_D_T_FORMULA_SELECTED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_SEMANTICS_CHANGED=false
```

Closes P5.9C: explicit **regime-bound** vs **mechanical** SideState authority split for future
``LAYERED_CORE_SEAL_DELEGATED`` bind. Validators only — no productive replay/cycle/CZ-4 wiring.

| Surface | Owner |
| --- | --- |
| FSM contract + validators | `ops.p5_9d_layered_mechanical_sidestate_fsm_contract_v1` |
| Regime-bound projection (future) | `ops.p5_7_regime_sidestate_projection_mapping_contract_v1` |
| Legacy SM reference | `trading.master_v2.double_play_state.transition_state` |

## Regime-bound authority (future P5.7)

- INITIAL_SEED → regime-oriented ``*_ARMED_NEUTRAL_START``
- L10 regime flip → ``SWITCH_*_PENDING``
- Must not duplicate forbidden legacy ``transition_state`` rows (see below).

## Mechanical authority (allowlist)

Repo-belegbare rows from ``transition_state`` (P5.9C), excluding UNKNOWN (e.g.
``CHOP_GUARD_BLOCK`` clear) and regime-bound legacy rows:

| Row ID | Semantics (reference) |
| --- | --- |
| MECH_T1 | ``KILL_ALL_REQUIRED`` → ``KILL_ALL`` |
| MECH_T3 | ``SCOPE_UNKNOWN`` hold |
| MECH_T4 | ``CHOP_DETECTED`` scope-only hold |
| MECH_T6 | CHOP policy block hold (requires ``chop_scope_policy_blocked_transition``) |
| MECH_T8–T14 | Pending completion + ``*_ARMED_*`` → ``*_ACTIVE`` |
| MECH_T17 | Candidate ack (side unchanged) |
| MECH_T18 | ``NOOP`` hold |

## Forbidden legacy rows (layered mode)

| ID | Prior + Event → Next |
| --- | --- |
| T15 | ``NEUTRAL_OBSERVE`` + ``UPSCOPE_CONFIRMED`` → ``LONG_ARMED_NEUTRAL_START`` |
| T16 | ``NEUTRAL_OBSERVE`` + ``DOWNSCOPE_CONFIRMED`` → ``SHORT_ARMED_NEUTRAL_START`` |
| T7 | ``LONG_ACTIVE`` + ``DOWNSCOPE_CONFIRMED`` → ``SWITCH_LONG_TO_SHORT_PENDING`` |
| T11 | ``SHORT_ACTIVE`` + ``DOWNSCOPE_CONFIRMED`` → ``SWITCH_SHORT_TO_LONG_PENDING`` |

## Scope-event provenance

Mechanical **side-changing** transitions require explicit provenance. Completion rows
(MECH_T8–T14) require ``LEGACY_DETERMINISTIC_SCOPE_EVENT_GENERATOR``. ``CZ4_SYNTHETIC_NOOP``
(marked via ``p5_cz4_delegated_noop``) cannot authorize completion or any side change.

## Single writer

Per ``trading_epoch``: at most one of regime-bound or mechanical SideState write authority
may assert a mutation.

Code: `src/ops/p5_9d_layered_mechanical_sidestate_fsm_contract_v1/contract_v1.py`
