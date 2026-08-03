# O7 Remaining Network Gaps — Productive Wiring (Offline)

**Capability:** `CAPABILITY_O7_GOVERNED_END_TO_END_RUNTIME_AND_DASHBOARD_EVIDENCE_V1`  
**Authority effect:** Implementation wiring only. No runtime network authorization.  
**O7_FULL_CAPABILITY_CLOSED:** `false`

## What this change closes (offline / local)

- O2 `dashboard-only` now supervises a loopback-only FastAPI host serving:
  - `GET &#47;market`
  - `GET &#47;api&#47;market&#47;landscape&#47;ohlcv`
  - `GET &#47;health`
- Productive PSO normalized MD can feed `CanonicalPublicMdBarProducerV1` (PT1H) via
  `PsoToO4O5LiveBridgeV1` into the durable O5 read model.
- Joined timestamp provenance is stamped without fabrication.
- Dashboard restart reloads durable read model without restarting PSO.

## What remains for a separate Owner-GO network session

Attempt 2 (`o7_network_bound_ddf3955af9f7_2bd450c5`) already proves long-running public-MD.
After merge, a separate network evidence session must still prove:

- live OHLCV matrix continuity
- dashboard HTTP poll continuity against live MD
- full end-to-end latency chain under live conditions
- network failure / recovery evidence (no fabrication)

## Safety

- No orders, credentials, testnet, or live trading paths.
- Dashboard authority remains read-only (`NONE`).
- No parallel bar producer or parallel read-model authority.
