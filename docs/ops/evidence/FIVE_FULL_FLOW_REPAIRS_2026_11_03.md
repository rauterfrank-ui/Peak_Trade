---
docs_token: DOCS_TOKEN_FIVE_FULL_FLOW_REPAIRS_2026_11_03
status: scoped-local-proof
scope: Offline injected full-flow repairs; no activation
---

# Five full-flow repairs — 2026-11-03

Base revision: 9afa1f651c74a2b9b51d414b9a900eb63f7a5baa. This closes the five baseline failures recorded in [the startup-port report](LEGACY_STARTUP_OBSERVATION_PORTS_2026_11_03.md), within the injected test configuration only.

## Causes and implementation

1. The bootstrap fixture supplied a non-futures native identifier. It now uses the existing typed 0G futures binding. The natural long/short seed helpers anchored G17 history later than their first observation; history now starts at that first observation, and replay/cursor assertions prevent silently proceeding after rejection. Future-estimate rejection remains enforced.
2. The one-shot prepare API omitted the shared portfolio reservation owner already required by the downstream closure. It now accepts and forwards the exact supplied object. There is no automatic owner creation or substitute. Omitting it still denies a natural ENTER.
3. The closure reported MARKET_STATE_HOLD_NOT_ENTER even when MV2 had produced enter_long and the capital gate blocked it. It now reports the actual first blocker for ENTER decisions; HOLD disposition and all gates remain unchanged.

Only two production files change. Neighboring order-independence and offline capital-guard test callers now explicitly supply temporary owners too. Capital formulas, U04/P01, GGE/Double Play logic, protected trading sources and learning/promotion behavior are unchanged.

## Evidence and proof limits

[Final JUnit](five_full_flow_repairs_v1_2026_11_03/integration_final_tests.xml): **68 passed**, including all five original failures, long/short offline capital guards, same-process/repeated preparation, process isolation, G17 binding and closure composition. The new negative case proves that a natural ENTER without the shared owner still fails with ENTRY_BUDGET_REQUIRES_SHARED_RESERVATION_OWNER.

The persistent test previously checked only that no POST occurred. It now composes the existing S8/S6/S5 path with injected account transport, an isolated budget host and durable armed seed, and requires an actual PRE_EXTERNAL terminal in one cycle, a positive reservation bounded by 25, and no POST, permit or external effect. The offline convenience wrapper still has no private-account or budget acquisition ports.

The initial broadened diagnostic had 60 passes and eight neighboring fixture failures, all caused by absent required owners. Its losslessly compressed JUnit is retained beside the final result. These overlapping runs are not summed. [Verification manifest](five_full_flow_repairs_v1_2026_11_03/verification_manifest.json) binds source hashes, U04/learning preservation and the scoped result.

No real private GET, credential acquisition, service start, order or capital transfer was performed. Fixtures and transports are injected; offline subprocess guard proofs are not live-host restart proofs. Actual startup source provisioning, persistent service configuration, U04 original-intent questions and repository-wide/remote CI completion remain open. The CLI does not acquire an owner automatically through this change. PRE_EXTERNAL evidence does not authorize activation.
