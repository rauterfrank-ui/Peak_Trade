# First Blocking Boundary

## Verdict

`FIRST_BLOCKING_BOUNDARY=NONE` for productive Scope/Direction/Entry/Exit value-loss.

## Probe artifact (not a blocker)

The observational probe initially records `intermediate_missing` on early warmup bars before
integrated replay intermediate exists. That is expected warmup plumbing, not a canonical
chain value-loss: subsequent hooked bars carry full intermediate
(scope_event → state_switch → composition → entry_exit).

## Reachability evidence against a frozen chain

On 1INCH after #5338/#5340:

| Layer | Observation |
|-------|-------------|
| Distances | mark-relative; legacy 120 abs not seen |
| ScopeEvent | downscope_confirmed=2439, upscope_confirmed=277 |
| SideState | short_active=2543 (not frozen LONG_ARMED) |
| Policy | adverse triggered=2491; enter_short=8; enter_long=1 |
| Execution | total_trades=1 offline |

## Pre-fix blockers (closed)

| Historical blocker | Status |
|--------------------|--------|
| Absolute distance unit mismatch (#5338) | closed |
| ADVERSE shadowing DOWNSCOPE → SCOPE_UNKNOWN (#5340) | closed for nested case |

## Residual sparse-trade note

BONK/AVAX/SOL show enter_* intents but 0 closed trades in this sample. Classification for
that residual is economic/execution conversion density (class K/H discussion), **not** a
first ScopeEvent/transition_state value-loss boundary. Primary instrument proves trade path.
