# WORKBOOK — Execution Networked On-Ramp (A2Z) v1

Scope: shadow/paper only. DRY_RUN=YES always. No secrets in repo. Network calls only behind explicit operator action.

A) Preconditions

- main clean; P122 checkpoint reached.
- P93/P95 green if ops-loop needed; otherwise independent.

B) Secrets / Config (Operator-only)

- Keys stored in OS keychain / env at runtime only.
- Explicit allowlist: COINBASE / OKX / BYBIT (as chosen).
- Deny: LIVE, TRADING_ENABLE, PT_ARMED, etc.

C) Transport Gate

- One module for HTTP client with hard timeout + retries.
- Single toggle: EXEC_NET_ENABLE=YES required or exit 3.

D) Adapter v2 (Network Stub)

- Keep existing Mock adapters.
- Add network "stub" methods returning NotImplemented unless EXEC_NET_ENABLE=YES.

E) Rate limits & backoff

- Global limiter + per-exchange buckets.
- Deterministic sleep disabled in tests via injected clock.

F) Paper/Shadow integration

- Paper: send to exchange test endpoint if supported OR simulate with recorded fixtures.
- Shadow: fetch markets/orderbook only (read-only), no order placement.

G) Evidence

- Every networked run writes EVI + SHA256SUMS + bundle + DONE pin.
- Include request metadata without secrets (host, path, status, latency).

H) Failure Modes

- TLS / 429 / 5xx / clock skew / auth fail / schema drift.

I) CI Strategy

- Networkless CI only: use VCR-style fixtures or local http mock server.
- No real network in CI.

J) Finish Criteria

- Networkless suite still green.
- One operator-run "shadow read-only" evidence pack created and verified.
