---
docs_token: DOCS_TOKEN_P5_7_REGIME_SIDESTATE_PROJECTION_MAPPING_CONTRACT_V1
status: active
scope: P5.7 regime→SideState projection mapping contract only (no cutover; no productive bind)
---

# P5.7 Regime↔SideState Projection Mapping Contract v1

```text
MAPPING_CONTRACT_V1_DEFINED=true
REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED=false
PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED=false
P5_AUTHORITY_CUTOVER_AUTHORIZED=false
AUTHORITY_CUTOVER_OCCURRED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Closes O-R2 **R-01** at the **contract** layer: explicit projection from layered-core
``regime_pre`` and ``regime_post`` (seal and L10 output) onto downstream ``SideState``.

Does **not** set ``REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED=true`` (P5.2 remains fail-closed
for CZ-4 switch until a separate activation WP). Does **not** wire replay, cycle, or CZ-4.

| Surface | Owner |
| --- | --- |
| Mapping + validator | `ops.p5_7_regime_sidestate_projection_mapping_contract_v1` |
| Phase authority (INITIAL_SEED vs MECHANICAL_STEP) | `ops.p5_8b_regime_sidestate_projection_phase_authority_v1` |
| Regime domain | `trading.master_v2.naked_mv2_dp_regime_v1.NakedRegimeV1` |
| SideState domain | `trading.master_v2.double_play_state.SideState` |
| Orientation rule (aligned with L9) | BULL→LONG, BEAR→SHORT scope direction |
| Legacy SideState SM (unchanged) | `trading.master_v2.double_play_state.transition_state` |

## Authority

- **Inputs:** valid ``NakedRegimeV1`` pair, ``switch_condition_met`` consistent with
  ``regime_pre != regime_post``, occupancy (`venue_flat`, ``ExistingPositionSide``),
  ``prior_side_state`` (cursor/occupancy seed — never core regime writer),
  ``phase`` (``RegimeSideStateProjectionPhaseV1`` — from P5.8B phase authority only;
  SideState lifecycle context, not regime writer).
- **Output:** projected ``SideState`` for downstream lifecycle / CZ-4 prep only.
- **Sole trading-decision regime source:** core seal ``regime_pre`` and ``regime_post``.
- **Forbidden:** SideState→regime backflow; ACTIVE from regime alone when flat;
  implicit BULL→LONG_ACTIVE / BEAR→SHORT_ACTIVE; ``transition_state`` authority in layered mode.

## Projection rules (summary)

1. **No switch:** return ``prior_side_state``; initial flat seed may move
   ``NEUTRAL_OBSERVE`` → ``*_ARMED_NEUTRAL_START`` for ``regime_post`` orientation only.
2. **Switch:** flat/neutral → ``*_ARMED_NEUTRAL_START`` for ``regime_post``;
   ``LONG_ACTIVE`` + flip to BEAR → ``SWITCH_LONG_TO_SHORT_PENDING`` (mirrors
   ``transition_state`` long-active reversal entry);
   ``SHORT_ACTIVE`` + flip to BULL → ``SWITCH_SHORT_TO_LONG_PENDING``.
3. **Invalid:** seal flag inconsistency, occupancy contradictions, KILL_ALL/CHOP unresolved.

Code: `src/ops/p5_7_regime_sidestate_projection_mapping_contract_v1/contract_v1.py`
