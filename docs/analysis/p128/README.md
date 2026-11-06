# P128 — Execution Networked Transport Stub v1

Scope: **networkless, default-deny**. No real HTTP, no secrets, no live/paper execution.

Deliverable:
- `NetworkedTransportStubV1` enforces:
  - Entry Contract guard (mode ∈ {shadow,paper}, dry_run=True, deny env, required args)
  - Transport Gate guard (transport_allow must be "NO")
  - Always returns deterministic deny response (no network I/O).

Tests:
- Stub builds
- Default deny response
- Entry contract blocks invalid mode
- Gate blocks when transport_allow="YES"
