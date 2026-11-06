---
docs_token: DOCS_TOKEN_SELECTED_FUTURE_PERSISTENT_SCOPE_CONFIRMATION_AUTHORITY_V1
status: ACTIVE
owner: Peak_Trade
last_updated: 2026-09-28
purpose: Canonical Owner policy for persistent Selected-Future Bull/Bear confirmation lifecycle vs OD1 single-lane carrier routing.
---

# Selected Future Persistent Scope Confirmation Authority V1

Machine record: [`config/governance/selected_future_persistent_scope_confirmation_authority_v1.json`](../../../config/governance/selected_future_persistent_scope_confirmation_authority_v1.json)

```text
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=SEMANTIC_CONTRACT_AND_PRODUCTIVE_BINDING
LIVE_AUTHORIZED=false
ORDERS_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Owner decision (canonical)

```text
SELECTED_FUTURE_PERSISTENCE=true
ELEMENTARY_DIRECTION_CHANGE_RESELECTS_FUTURE=false
ELEMENTARY_DIRECTION_CHANGE_INVALIDATES_OPPOSITE_CANDIDATE=false
OD1_SINGLE_LANE_ACTIVATION_IS_CARRIER_ROUTING_NOT_CANDIDATE_INVALIDATION_AUTHORITY=true
DUAL_CARRIER_PADDING_MUST_NOT_DESTROY_PERSISTENT_CANDIDATE=true
CANDIDATE_LIFECYCLE_IS_SCOPED_TO_SELECTED_FUTURE=true
BULL_BEAR_SWITCH_SCOPE_STATE_PERSISTS_ACROSS_ELEMENTARY_DIRECTION_CHANGES=true
```

Selection remains sole Future owner. Execution, MV2, Cap 6.1, and L10 MUST NOT
reselect the productive Future on elementary direction change.

Elementary BULL/BEAR observations are observations inside the persistent
Bull/Bear/Scope/Switch lifecycle on the bound Future. They are not authority to
destroy opposite-side confirmation cursor state merely because OD1 routes the
current DISTINCT observation to the opposite evaluation lane.

## Topology owners

| Role | Owner |
| --- | --- |
| Selected Future | `CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1` |
| Selected Future persistence | `CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1` |
| Scope events | `deterministic_scope_event_generator_v1` |
| Regime (L10) | `naked_mv2_dp_explicit_layered_core_v1` L10 |
| Switch / Stay | `double_play_state` |
| Candidate state (C2) | `directional_confirmation_progress_v1` |
| Candidate persistence schema | `DirectionalConfirmationSideStateCarrierV1` (Cap 6.1) |
| Candidate invalidation evaluator | `directional_confirmation_progress_v1` (C2 reset rules) |
| OD1 | `single_lane_confirmation_activation_v1` — **active evaluation lane only** |

## OD1 authority boundary

OD1 selects **ACTIVE_EVALUATION_LANE** from `ElementaryDirectionV1` for the
current cycle. OD1 MUST NOT erase `ConfirmationProgressStateV1` on the inactive
side when persisting into the dual carrier.

Cap 6.1 / C3 `DirectionalConfirmationSideStateCarrierV1` holds
**PERSISTENT_CONFIRMATION_STATE_PER_SIDE**. Inactive-side padding is absence
only for never-initialized slots; authoritative opposite-side state MUST
survive lane switches.

## Candidate invalidation (Phase 3 adjudication)

| Event | CURRENT authority | CAN_INVALIDATE_CANDIDATE |
| --- | --- | --- |
| L10 regime switch | L10 layered core | NOT_PROVEN (no productive C3 bind) |
| Scope exit / `*_CONFIRMED` switch | DSE + State-Switch contract | NOT_PROVEN (separate scope clock; S05) |
| Switch/Stay transition | `double_play_state` | NOT_PROVEN (side-state ≠ C2 cursor) |
| C2 OBSERVE assessment on evaluated side | C2 reset rule | true (per-side, when C3 evaluates that side) |
| Session / instrument rebind | Cap 6.1 / C2 mismatch | true (fail-closed) |
| Future unbind / rebind | Selection + binding owners | NOT_PROVEN in this slice |
| Episode invalidation | L1–L10 durable episode | NOT_PROVEN in this slice |

```text
CANDIDATE_INVALIDATION_EVENT=UNRESOLVED_SCOPE_SWITCH_L8_L10_MECHANICAL_BIND
CANDIDATE_INVALIDATION_AUTHORITY_PROVEN=false
AUTHORITY_BLOCKER=true
```

Implementation MUST stop at inventing scope/L10-driven candidate reset until an
explicit mechanical bind exists. Safe closure: prevent OD1 lane switch and
padding from erasing persistent opposite-side candidate state.

## Confirmation count (Phase 6)

Under persistent per-side cursors, consecutive confirmation count advances only
when that side receives C3 evaluation with qualifying C2 input on DISTINCT
observations. Opposite elementary observations leave the inactive side's count
unchanged because C3 does not evaluate the inactive lane.

```text
CONFIRMATION_COUNT_SEMANTICS=PER_SIDE_C2_DISTINCT_QUALIFYING_SIGNAL_ONLY_INACTIVE_SIDE_UNEVALUATED
CONFIRMATION_COUNT_SEMANTICS_AUTHORITY_BLOCKER=false
```

## Related contracts

- [`MV2_C3_DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_V1.md`](MV2_C3_DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_V1.md) — Bull/Bear isolation
- [`CAPABILITY_6_1_STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1.md`](CAPABILITY_6_1_STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1.md) — persistence schema
- [`EXPLICIT_OWNER_ADJUDICATED_OD1_PRODUCTIVE_SINGLE_LANE_CONFIRMATION_AUTHORIZATION_V1.md`](EXPLICIT_OWNER_ADJUDICATED_OD1_PRODUCTIVE_SINGLE_LANE_CONFIRMATION_AUTHORIZATION_V1.md) — Economic Guard class (grant inactive)
