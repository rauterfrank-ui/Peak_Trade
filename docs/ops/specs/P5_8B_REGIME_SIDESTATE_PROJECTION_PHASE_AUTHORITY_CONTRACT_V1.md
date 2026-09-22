---
docs_token: DOCS_TOKEN_P5_8B_REGIME_SIDESTATE_PROJECTION_PHASE_AUTHORITY_CONTRACT_V1
status: active
scope: P5.8B RegimeSideStateProjectionPhaseV1 authority only (no CZ-4 wire; no mapping activation)
---

# P5.8B Regime→SideState Projection Phase Authority Contract v1

```text
PHASE_AUTHORITY_CONTRACT_V1_DEFINED=true
PHASE_AUTHORITY_VARIANT=PERSISTED_STATE_REQUIRED
REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED=false
PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED=false
P5_AUTHORITY_CUTOVER_AUTHORIZED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_SEMANTICS_CHANGED=false
```

## Role

Closes the P5.8A blocker: **who** sets ``RegimeSideStateProjectionPhaseV1`` for P5.7
``project_regime_to_sidestate_v1``. Phase is **SideState lifecycle context only** — never
Regime, L10 switch, or direction decision authority. No SideState→regime backflow.

Does **not** wire CZ-4, productive cycle, or flip ``REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED``.

| Surface | Owner |
| --- | --- |
| Phase authority + lifecycle state | `ops.p5_8b_regime_sidestate_projection_phase_authority_v1` |
| Projection mapping (unchanged) | `ops.p5_7_regime_sidestate_projection_mapping_contract_v1` |

## Adjudication (P5.8B)

**Variant B — persisted state required.**

``(prior_side_state == NEUTRAL_OBSERVE && venue_flat && !switch)`` alone is **not**
sufficient: after a consumed initial orientation seed, restore/resume can present flat
``NEUTRAL_OBSERVE`` again (missing cursor, stale payload, or lineage desync) while
``mechanical_step_count`` on the layered core is already ``> 0``. Without persisted
evidence, a repeat ``INITIAL_SEED`` cannot be distinguished from a legitimate first seed.

## Semantics

### INITIAL_SEED

Exactly **one** initial SideState **orientation** seed for a flat host that is still
**not oriented**: ``prior_side_state == NEUTRAL_OBSERVE``, ``venue_flat == true``,
``existing_position_side == NONE``, no regime switch on the seal, and
``initial_regime_orientation_seed_consumed == false`` in lifecycle state.

Permitted P5.7 effect (no-switch only): ``NEUTRAL_OBSERVE`` → ``*_ARMED_NEUTRAL_START``
for ``regime_post`` orientation — never ``LONG_ACTIVE`` &#47; ``SHORT_ACTIVE`` from regime alone.

### MECHANICAL_STEP

All other resolved cases, including **every** switch path (P5.7 ignores ``phase`` on switch).

After ``INITIAL_SEED`` is consumed, lifecycle sets ``initial_regime_orientation_seed_consumed=true``;
subsequent no-switch projections use ``MECHANICAL_STEP`` (preserve oriented SideState).

### Lifecycle field

| Field | Meaning |
| --- | --- |
| ``initial_regime_orientation_seed_consumed`` | Persisted proof that the one-time flat neutral orientation seed was applied for this lifecycle binding |

Owner DTO: ``RegimeSideStateProjectionLifecycleStateV1`` in the P5.8B contract module.
Future bind may persist alongside host cursor; **not** wired in this WP.

## Fresh start

Caller supplies ``fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=…)`` with
``initial_regime_orientation_seed_consumed=false``. Phase resolution may return ``INITIAL_SEED``
when host SideState is flat ``NEUTRAL_OBSERVE``.

## Restore / resume

Lifecycle JSON must round-trip via ``lifecycle_to_dict_v1`` &#47; ``parse_lifecycle_v1``.
Version or schema mismatch → fail-closed. Instrument binding mismatch → fail-closed.

If ``initial_regime_orientation_seed_consumed == true`` and host presents flat
``NEUTRAL_OBSERVE`` again on a no-switch tick → fail-closed
(``SEED_ALREADY_CONSUMED_NEUTRAL_OBSERVE``) — no silent re-seed.

## Fail-closed

Missing lifecycle object, corrupt payload, schema/version mismatch, instrument mismatch,
or consumed+neutral flat contradiction → phase resolution ``ok=false`` with explicit codes.

## P5.7 input

``phase`` is a **required** P5.7 input; value must come from P5.8B phase resolution
(when bind exists). See updated P5.7 spec authority list.

Code: `src/ops/p5_8b_regime_sidestate_projection_phase_authority_v1/contract_v1.py`
