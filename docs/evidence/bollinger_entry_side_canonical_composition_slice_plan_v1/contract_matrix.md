# Contract Matrix

## Active contract (NOW) — OPTION_D

| Input | Output |
|-------|--------|
| Bollinger raw `+1` | `ENTRY_EVENT` |
| Bollinger raw `-1` | `EXIT_EVENT` |
| Bollinger raw `0` | `FLAT_NO_EVENT` |
| missing&#47;invalid | `UNKNOWN_FAIL_CLOSED` |
| Strategy Direction | `NONE` |
| `entry_side` | `NONE` |
| Executable directional cycle | none |

Authority:

- Bollinger = Strategy Signal &#47; Event producer only
- Master V2 `transition_state` = Direction &#47; SideState
- Composition matrix = system selected_side from assessments
- No Bollinger Long&#47;Short ownership

## Deferred envelope (NOT ACTIVE) — OPTION_B sketch

Only if a **future Operator-GO** explicitly selects OPTION_B (audit currently DEFER):

```text
Strategy Event/Intent
  + Canonical Double-Play Bull/Bear / selected_side
  + Dynamic Scope binding
  -> ENTRY_SIDE(LONG|SHORT|NONE)   # projection only, not new State Authority
```

Mandatory fail-closed rows for that future envelope:

| Condition | ENTRY_SIDE |
|-----------|------------|
| Long-compatible Intent ∧ Bull&#47;Long selected | LONG |
| Short-compatible Intent ∧ Bear&#47;Short selected | SHORT |
| Conflict Intent vs State | NONE |
| Missing binding &#47; CHOP &#47; unknown state | NONE |
| Neutral &#47; flat &#47; exit-only &#47; ambiguous Intent | NONE |
| Bollinger EVENT_ONLY without side ratification | NONE |

Rules that must hold even then:

- Composer is Projection&#47;Composition only — not State Authority
- No strategy→order or strategy→classic-engine path
- Same semantics for Backtest&#47;Replay&#47;Runtime contracts
- Classic `run_realistic` LONG remains non-canonical

## Explicit deviation note

```text
PROMPT_TEMPLATE_OPTION=OPTION_B
AUDIT_RECOMMENDED_CONTRACT=OPTION_D
DEVIATION=PLAN_FOLLOWS_AUDIT_OPTION_D_DEFERS_OPTION_B
```
