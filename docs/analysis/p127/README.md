# P127 — Networked Provider Adapter Stub v1

Scope: **shadow/paper only**, **dry_run=True**, **default-deny transport**.

What this adds:
- `NetworkedProviderAdapterV1` protocol + stub implementation that:
  - enforces `entry_contract_v1` guards
  - enforces `transport_gate_v1` default-deny (transport_allow must be `NO`)
  - never performs network I/O (`send_request()` always denies)

Safety:
- no secrets required
- no HTTP client usage
- no live execution path
