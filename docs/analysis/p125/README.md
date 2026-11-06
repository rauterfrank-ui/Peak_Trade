# P125 — Execution Networked Transport Gate v1 (networkless)

## Goal
Add a **hard transport choke-point** that is *networkless by design* in v1.

## Behavior
- Reuses P124 entry contract guards (mode, dry_run, deny env, secret env).
- Enforces `transport_allow == "NO"` (default). Any other value denies.
- Returns `TransportDecisionV1(ok=true, reason="NETWORKLESS_V1")` on allowed path.
- Raises `TransportGateError` on `transport_allow != "NO"`.

## Safety
- No sockets / no HTTP clients.
- No secrets accepted.
- `mode ∈ {shadow, paper}` and `dry_run=True` only.
