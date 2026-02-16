# P107 — Coinbase Adapter v1 (Mocks Only)

Goal: Add a **provider-specific** adapter stub that implements `ExecutionAdapterV1` without any network calls.

Constraints:

- **No secrets**
- **No HTTP/WS**
- **Deterministic**
- Upgrade to real integration requires explicit governance + tests.
