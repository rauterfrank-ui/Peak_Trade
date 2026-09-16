---
title: "Bounded Post-Disentanglement Double Play Clean Core Repair v2"
status: "WP_CONTRACT_PERSISTED_BOUNDED_IMPLEMENTATION"
owner: "ops"
last_updated: "2026-09-16"
docs_token: "DOCS_TOKEN_BOUNDED_POST_DISENTANGLEMENT_DOUBLE_PLAY_CLEAN_CORE_REPAIR_V2"
---

# Bounded Post-Disentanglement Double Play Clean Core Repair v2

Canonical persist of workpackage
`BOUNDED_POST_DISENTANGLEMENT_DOUBLE_PLAY_CLEAN_CORE_REPAIR_V2`
under `OWNER_GO_BOUNDED_POST_DISENTANGLEMENT_DOUBLE_PLAY_CLEAN_CORE_REPAIR_V2`.

Semantic authority for this persist lives in Master Runbook §9.2.7.
This file is the WP contract record and navigation twin. It is **not**
MODEL_C runtime bind, **not** Cross-Instrument validation, **not**
Live/Testnet/Canary/POST/Funding/Execute authority, and **not** a
venue-to-SideState mutation decision.

```text
DOCUMENT_CLASS=BOUNDED_CLEAN_CORE_REPAIR_WP_CONTRACT
OWNER_GO=OWNER_GO_BOUNDED_POST_DISENTANGLEMENT_DOUBLE_PLAY_CLEAN_CORE_REPAIR_V2
OWNER_GO_STATUS=CONSUMED
AUTHORITY_CLASS=R1_OFFLINE_BOUNDED_CORE_REPAIR
EXPECTED_ORIGIN_MAIN=69164b604f42b4ba40fdecdb0e8f97bfdb16b7fd
PARENT_MODEL_C_UNBOUND=docs/ops/specs/CAP63_DYNAMIC_DERIVATION_PURE_FUNCTION_AND_GOLDEN_VECTORS_V1.md
PARENT_PROFIT_PROTECTION_SPLIT=docs/ops/specs/MODEL_C_UP_DISTANCE_SWITCH_VS_PROFIT_PROTECTION_AUTHORITY_SPLIT_V1.md
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 1. Epistemic class separation

```text
CANONICAL_AUTHORITY=MASTER_RUNBOOK_§9.2.7_PLUS_THIS_CONTRACT
FORENSIC_RAW_EVIDENCE=CLAMP_50_50_AND_HOST_SKEW_CENSUS
ADJUDICATED_CONCLUSION=SECTION_3_SLICE_DAG_AND_PARK_MARKERS
HISTORICAL_SUPERSEDED=CANDIDATE_WP_V1_S1_S8
NAVIGATION_ONLY=MAP_OF_TRUTH
INTERPRETATION=NONE_USED_AS_AUTHORITY
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN_OR_CONTRADICTORY=VENUE_SIDESTATE_SEED_CLASS
```

## 2. Frozen invariants (CC-A)

```text
WP_NAME=BOUNDED_POST_DISENTANGLEMENT_DOUBLE_PLAY_CLEAN_CORE_REPAIR_V2
AUTHORIZED_WP_SLICES=CC-A,CC-B,CC-C,CC-D,CC-E,CC-F,CC-G,CC-H
MAX_POSITIONS_EFFECTIVE=1
SINGLE_SELECTED_FUTURE=true
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
confirmation_epochs=2
CURRENT_MODEL=MODEL_B
MODEL_A_REACHABLE=false
MODEL_C_BOUND=false
ATOMIC_RETIRE_BIND_AUTHORIZED=false
DERIVE_FN_PRODUCTIVE_CONSUMER_COUNT=0
CAP65_PROFIT_PROTECTION_JOINED=false
FROZEN_PROFIT_PROTECTION_DISTANCE=200.0
FROZEN_CAP63_GENERATOR_DISTANCES=200.0/80.0/120.0
SNAPSHOT_WINDOW_IDENTITY=50.0/500.0
NEW_NUMERIC_SCOPE_LIMIT_INVENTED=false
NEW_PERSISTENCE_DOMAIN_CREATED=false
TRANSITION_STATE_SEMANTICS_CHANGED=false
CHOP_SIDESTATE_AUTHORITY=false
POSITION_FLIP_ALLOWED=false
KILL_SWITCH_ROLE=SAFETY_VETO_ONLY
LIVE_OR_EXECUTION_AUTHORITY_TOUCHED=false
BLOCKED_CROSS_GO=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1
BLOCKED_CROSS_GO_CONSUMED=false
CROSS_INSTRUMENT_VALIDATION_IN_WP=false
```

## 3. Mini-slice DAG

```text
CC-A  invariants plus MUST_NOT_TOUCH freeze (this contract)
CC-E  venue seed classify only (no SideState mutation)
CC-F  hardening_v2 PARKED_WITH_REASON
CC-G  MODEL_C bind boundary persisted; function remains unbound
CC-B  clamp non-collapse inside snapshot 50/500 (no new ceiling)
CC-C  typed CMC vol → DynamicScopeRules.volatility_estimate
CC-D  cursor-owned temporal pass-through only
CC-H  regression/parity/authority closure of implemented V2 scope
```

Required order: CC-A first; CC-E/CC-F/CC-G persist after CC-A; CC-B before
CC-C; CC-D after CC-A; CC-H only after CC-B+CC-C+CC-D.

## 4. MUST_NOT_TOUCH

Forbidden in this WP:

- Cap 2.3 / 2.4 or Multi-Future mutation
- `transition_state` semantic/table modification
- MODEL_A
- MODEL_C `derive_scope_event_distances_v1` productive bind
- ATOMIC_RETIRE_BIND
- Cross-Instrument validation or consumption of its blocked GO
- Kill Switch / FILEGATE redesign
- CHOP as SideState authority or invented CHOP market emission
- DDO / dashboard / readmodel
- mapper / execution / live / testnet / canary / POST / funding / execute
- position flip
- Cap 6.5 profit-protection join with switch distances
- ScopeCooldownState persistence invention
- previous_composition_direction_state persistence invention
- hardening_v2 runtime modification
- venue ExistingPositionSide → SideState mutation
- deciding VENUE_SIDESTATE_SEED_CLASS on Owner's behalf
- new numeric scope limits not already canonically authorized

## 5. CC-B clamp non-collapse

Class: `ADJUDICATED_CONCLUSION`.

`DynamicScopeRules` min/max must follow CanonicalScopeSnapshot identity
(`min_scope_band` / `max_scope_band`). Unratified Replay literals
`rules.max=50` and `static.max=100` must not clip Host-INIT 50/500 to 50/50.

`StaticHardLimits` must envelope-contain the snapshot window. No new Owner
ceiling is invented. Replay default 0.02 remains the quarantined offline
volatility default only.

## 6. CC-C typed volatility bind

Class: `ADJUDICATED_CONCLUSION`.

Per-cycle `DynamicScopeRules.volatility_estimate` consumes the canonical
admitted typed CMC float when present. No second estimator. Floor policy
remains NONE. Productive typed-missing remains fail-closed on the existing
presence-gate path. Replay 0.02 remains quarantined offline default only.

G17 producer caller owner remains hardening_v2, which this WP parks (CC-F).
This WP does not add mark-history persistence to current_productive.

## 7. CC-D temporal continuity

Class: `ADJUDICATED_CONCLUSION`.

In-scope hosts (current_productive + Cap 6.2 wallclock v1) pass through
already cursor-owned fields only:

- `RuntimeScopeState`
- existing `CanonicalScopeSnapshotV1`
- `scope_confirmation` / Cap 6.1 carrier

No new persistence domain. Generator `ScopeCooldownState` and
`previous_composition_direction_state` are not invented as cursor fields.

## 8. CC-E venue SideState seed (classification only)

Class: `OPEN_OR_CONTRADICTORY` plus `OWNER_DECISION_REQUIRED`.

```text
VENUE_SIDESTATE_SEED_ADJUDICATION=OWNER_DECISION_REQUIRED
VENUE_SIDESTATE_MUTATION_AUTHORIZED=false
VENUE_SIDESTATE_MUTATION_PERFORMED=false
```

Not decided in this WP:

1. `LEGITIMATE_RECON_RESTORE`
2. `COMPETING_SIDESTATE_WRITER`
3. `POSITION_CONTEXT_ONLY`

Default V2 path performs **no** venue → SideState mutation.

## 9. CC-F hardening_v2 park

```text
HARDENING_V2_DISPOSITION=PARKED_WITH_REASON
HARDENING_V2_RUNTIME_MUTATION_AUTHORIZED=false
HARDENING_V2_RESTART_PARITY_NOT_CLAIMED=true
```

Reason: not Cap-6.2 `PRODUCTIVE_HOST`; abbreviated public-MD bridge;
`existing_scope=None` every cycle and missing `runtime_scope_state` are
drift outside this WP host set.

## 10. CC-G MODEL_C bind boundary

```text
MODEL_C_BIND_BOUNDARY_PERSISTED=true
MODEL_C_PRODUCTIVE_BIND_PERFORMED=false
DERIVE_FN_PRODUCTIVE_CONSUMER_COUNT=0
ATOMIC_RETIRE_BIND_AUTHORIZED=false
CROSS_INSTRUMENT_VALIDATION_STATUS=NOT_RATIFIED_PENDING_SEPARATE_VALIDATION
```

`derive_scope_event_distances_v1` remains IMPLEMENTED_UNBOUND. Replay must
not import or call it. Cap 6.3 frozen generator inputs remain
`200.0` / `80.0` / `120.0`. Cap 6.5 profit-protection `200.0` remains unjoined.

## 11. Residual next Owner decisions

```text
OPEN_OWNER_DECISIONS=
  VENUE_SIDESTATE_SEED_CLASS
  ATOMIC_RETIRE_BIND (separate GO; not this WP)
  OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1
    (VALIDATION_PRECONDITION; not a V2 slice; unconsumed)
```
