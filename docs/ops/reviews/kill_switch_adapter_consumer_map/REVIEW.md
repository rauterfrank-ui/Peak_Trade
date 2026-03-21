# KILL SWITCH ADAPTER CONSUMER MAP

## Purpose
Map all current kill-switch consumers as one docs-only slice.

## Scope
- exactly one PR
- docs only
- no runtime mutation
- no paper/shadow/testnet mutation

## Consumers To Map
- operator tooling
- risk gate
- risk hook
- ops cockpit
- incident / stop runbooks
- any other runtime-adjacent readers

## For Each Consumer
- what signal is read
- what source is assumed
- whether behavior is implemented, partial, or future work
- what ambiguity remains

## Desired Outcome
- one compact consumer map
- one explicit view of current adapter migration surface
- better basis for any later runtime slice
