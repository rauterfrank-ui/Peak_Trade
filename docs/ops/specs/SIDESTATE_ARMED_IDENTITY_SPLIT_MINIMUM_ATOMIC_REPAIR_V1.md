# SideState ARMED Identity-Split Minimum Atomic Repair v1

status: ACTIVE
last_updated: 2026-09-05
owner: Peak_Trade
purpose: Bound authority spec for disambiguating Neutral-Start versus pipeline-terminal SideState ARMED identities. Identity split only. Not a new directional authority. Not LastActiveSide. Not LIVE_ARMED.
docs_token: DOCS_TOKEN_SIDESTATE_ARMED_IDENTITY_SPLIT_MINIMUM_ATOMIC_REPAIR_V1

```text
PARALLEL_SSOT_CREATED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
LAST_ACTIVE_SIDE_BINDING_AUTHORIZED=false
HISTORY_RECONSTRUCTED=false
LIVE_ARMED_CHANGED=false
PENDING_SEMANTICS_UNCHANGED=true
ENTRY_EXIT_SEMANTICS_UNCHANGED=true
TRAILING_POLICY_CHANGED=false
MODEL_C_CHANGED=false
FIFTH_CLASS_GRANT_REOPENED=false
SIXTH_CLASS_GRANT_REOPENED=false
```

## 1) Role

This specification is the bound authority for

`OWNER_GO=PEAK_TRADE_OWNER_GO_SIDESTATE_ARMED_IDENTITY_SPLIT_MINIMUM_ATOMIC_REPAIR_V1`

It records the Current-System identity split of overloaded

`SideState.LONG_ARMED` / `SideState.SHORT_ARMED`.

Those persisted tokens previously meant both Neutral-Start and
pipeline-terminal after a side-switch. Productive `transition_state`
edges no longer collapse those meanings into one enum value.

`SideState` remains the directional and lifecycle authority. No parallel
authority is created. Projection parity keeps the previously bound
ScopeDirection destination prefix, ActiveSide freeze, and Entry/Exit
ARMED eligibility. PENDING maps are not part of this repair.

## 2) Identity split

| Old token | Old meanings | New productive state | New semantics |
|---|---|---|---|
| `LONG_ARMED` | Neutral-Start Long **and** Short→Long terminal | `LONG_ARMED_NEUTRAL_START` | Neutral-Start Long |
| `LONG_ARMED` | Neutral-Start Long **and** Short→Long terminal | `LONG_ARMED_SWITCH_TERMINAL` | Pipeline-terminal Long after Short→Long |
| `SHORT_ARMED` | Neutral-Start Short **and** Long→Short terminal | `SHORT_ARMED_NEUTRAL_START` | Neutral-Start Short |
| `SHORT_ARMED` | Neutral-Start Short **and** Long→Short terminal | `SHORT_ARMED_SWITCH_TERMINAL` | Pipeline-terminal Short after Long→Short |
| `LONG_ARMED` | persisted ambiguous | `LONG_ARMED` | Legacy-ambiguous Long ARMED; origin not reconstructed |
| `SHORT_ARMED` | persisted ambiguous | `SHORT_ARMED` | Legacy-ambiguous Short ARMED; origin not reconstructed |

Wire values:

```text
long_armed_neutral_start
long_armed_switch_terminal
short_armed_neutral_start
short_armed_switch_terminal
long_armed
short_armed
```

## 3) Transition matrix (changed destinations only)

No new event types. No extra state-machine edges.

| From | Event | Before | After | Semantics changed? |
|---|---|---|---|---|
| `NEUTRAL_OBSERVE` | `UPSCOPE_CONFIRMED` | `LONG_ARMED` | `LONG_ARMED_NEUTRAL_START` | Identity only; reason remains `NEUTRAL_TO_LONG_ARMED` |
| `NEUTRAL_OBSERVE` | `DOWNSCOPE_CONFIRMED` | `SHORT_ARMED` | `SHORT_ARMED_NEUTRAL_START` | Identity only; reason remains `NEUTRAL_TO_SHORT_ARMED` |
| `SHORT_BLOCKED` | `DOWNSCOPE_CONFIRMED` | `LONG_ARMED` | `LONG_ARMED_SWITCH_TERMINAL` | Identity only; reason `LONG_ARMED_SWITCH_TERMINAL` |
| `LONG_BLOCKED` | `DOWNSCOPE_CONFIRMED` | `SHORT_ARMED` | `SHORT_ARMED_SWITCH_TERMINAL` | Identity only; reason `SHORT_ARMED_SWITCH_TERMINAL` |
| every Long-armed identity | `UPSCOPE_CONFIRMED` | `LONG_ACTIVE` | `LONG_ACTIVE` | No |
| every Short-armed identity | `DOWNSCOPE_CONFIRMED` | `SHORT_ACTIVE` | `SHORT_ACTIVE` | No |

## 4) Projection parity

| New SideState | ScopeDirection | ActiveSide | EntryExit |
|---|---|---|---|
| `LONG_ARMED_NEUTRAL_START` | LONG | NEUTRAL (freeze) | `LONG_ARMED` |
| `LONG_ARMED_SWITCH_TERMINAL` | LONG | NEUTRAL (freeze) | `LONG_ARMED` |
| `SHORT_ARMED_NEUTRAL_START` | SHORT | NEUTRAL (freeze) | `SHORT_ARMED` |
| `SHORT_ARMED_SWITCH_TERMINAL` | SHORT | NEUTRAL (freeze) | `SHORT_ARMED` |
| legacy `LONG_ARMED` | LONG | NEUTRAL (freeze) | `LONG_ARMED` |
| legacy `SHORT_ARMED` | SHORT | NEUTRAL (freeze) | `SHORT_ARMED` |

PENDING maps stay at their previously bound owners. This spec does not
re-adjudicate wallclock-versus-Integrated PENDING divergence.

## 5) Persistence

```text
NEW_TOKEN_FORMAT=snake_case_enum_value
LEGACY_LONG_ARMED_HANDLING=RESTORE_AS_LEGACY_AMBIGUOUS_LONG_ARMED
LEGACY_SHORT_ARMED_HANDLING=RESTORE_AS_LEGACY_AMBIGUOUS_SHORT_ARMED
HISTORY_RECONSTRUCTED=false
RESTORE_FAIL_CLOSED_STATUS=INVALID_VALUE_REMAINS_SIDESTATE_RESTORE_ALPHA_BLOCKED
```

Persisted `long_armed` / `short_armed` restore as the legacy-ambiguous
enum members. Historical Neutral-Start versus terminal origin is not
reconstructed. LastActiveSide is not added for migration.

## 6) Bootstrap

Host defaults that still seed `side_state=LONG_ARMED` remain the
legacy-ambiguous token. Cap 6.2 missing persist already defaults to
`neutral_observe`. This spec does not guess whether a host default meant
Neutral-Start or pipeline-terminal.

```text
GUESSING_USED=false
```

## 7) Out of scope

LIVE_ARMED, LastActiveSide, PENDING generator mapping, PENDING departing-side
policy, Entry/Exit BLOCKED→NEUTRAL, trailing freeze policy, MODEL_C,
ScopeDirection generator fallback, overlay-inert bindings §11.2.1.D/E/F,
29P, Replay Safety, 29Q, Kill Switch, FILEGATE, Live/Testnet/Canary,
Venue/API/Wire, credentials, orders.
