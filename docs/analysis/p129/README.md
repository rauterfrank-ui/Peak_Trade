# P129 — Execution Networked Onramp CLI v1

Scope: **networkless, default-deny**. End-to-end wiring proof.

Flow: EntryContract -> TransportGate -> Transport(Stub) -> ProviderAdapter(Stub) -> Report.

- mode ∈ {shadow, paper} only
- dry_run=True only
- transport_allow default "NO"; "YES" => exit 3 (blocked)
- JSON report to stdout: meta, guards, transport, adapter
- No real HTTP, no secrets, no live modes
