---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITER_V1
status: active
scope: CURRENT_PRODUCTIVE canonical Cap-2.1–2.3 productivity-root writer for Cap-2.4 handoff; no Cap-2.4 execution; no network in module; separate Owner-GO for productive run
capability: FULL_CORE_CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-22
---

# Full Core Current Productive Cap-24 Selection State Canonical Writer V1

Derived spec. Non-SSOT. Closes orchestration gap
`runtime&#47;current_productive&#47;cap24_selection_state` for
`acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1`.

Cap-2.1 / Cap-2.2 / Cap-2.3 remain sole selection/ranking authorities.
This slice persists their outputs only via existing producers
(`run_cap21_to_cap23_persist_productive_v1`). Cap-2.4 handoff remains
consumer-only.

```text
THIS_SLICE=11.2.1.EK.FULL_CORE_CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITER
OWNER_GO=CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITE_V1
EXPECTED_ORIGIN_MAIN_SHA=8379a278517b23240ca1cdad02fe041b7d618874
REPOSITORY_BASELINE_CONTRACT=FULL_CORE_CURRENT_PRODUCTIVE_29P_CHAIN_BASELINE_CONTRACT_V1
PRODUCTIVITY_ROOT=runtime/current_productive/cap24_selection_state
PRODUCER=execute_current_productive_cap24_selection_state_canonical_write_v1
HANDOFF_CONSUMER=acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1
MARK_PRICE_SOURCE=EEA_acquisition_mark_price_payload
MARK_PRICE_TRANSFORM=instId→markPx map filtered to Cap-2.3 selected venue_native_id
REPOSITORY_SHA=explicit baseline bind (same value on Cap-2.1/2.2/2.3 snapshots)
ATOMIC_PUBLISH=staging_root then replace runtime_state and mark sidecar
NETWORK_IO=0 in module; productive input via separate authorized acquisition
SELECTION_AUTHORITY_ADDED=false
RANKING_AUTHORITY_ADDED=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
MAX_POSITIONS_EFFECTIVE=1
```
