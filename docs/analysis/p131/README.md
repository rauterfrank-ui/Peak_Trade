# P131 — Networked Allowlist Wire v1

Scope: **networkless, default-deny**. Allowlist is an additional guard layer.

## Invariants
- transport_allow must remain "NO" (Transport Gate unchanged)
- allowlist_allow default "NO" -> deny before transport
- allowlist_allow="YES" with empty allowlist -> deny
- allowlist_allow="YES" with adapter+market in allowlist -> proceeds to transport stub, then adapter (still denies send)

## Flow
EntryContract -> Allowlist -> TransportGate -> Transport(Stub) -> ProviderAdapter(Stub)
