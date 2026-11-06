# Authority Boundary — Bollinger EVENT_ONLY

## Allowed

| Action | Authority |
|--------|-----------|
| Classify Bollinger raw `{-1,0,+1}` as events | `classify_bollinger_raw_signal_event_v1` |
| Emit adapter `event_kind` ENTRY&#47;EXIT&#47;NONE | adapter `_bollinger_event_only_side_agreement_and_aux` |
| Keep `entry_side=NONE` | `_resolve_entry_side_carrier_v1` (Bollinger branch) |
| Diagnostic visibility of Entry&#47;Exit events | Agreement material `event_kind` |

## Forbidden (held)

| Action | Status |
|--------|--------|
| Read&#47;mutate Bull&#47;Bear state | forbidden |
| Use Dynamic Scope &#47; Switch as direction | forbidden |
| Evaluate Cycle State for direction | forbidden |
| Use Position State for direction | forbidden |
| Emit LONG or SHORT | forbidden |
| Set `entry_side` ≠ `NONE` | forbidden |
| Create orders &#47; execution intent | forbidden |
| Adopt Classic Engine as direction authority | forbidden |

## System state

Master V2 &#47; Double Play remain the only system-state authority.
Bollinger produces Strategy Events only — never system direction.
