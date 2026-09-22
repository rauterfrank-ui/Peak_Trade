---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_29P_CAP24_BOUND_INSTRUMENT_PROVENANCE_HANDOFF_V1
status: active
scope: CURRENT_PRODUCTIVE 29P Cap-2.4 bound-instrument provenance handoff; persisted Cap-2.1–2.3 runtime state; Cap-2.4 gate only; common-epoch consumer seam; no venue I/O; no reselection
capability: FULL_CORE_CURRENT_PRODUCTIVE_29P_CAP24_BOUND_INSTRUMENT_PROVENANCE_HANDOFF_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-22
---

# Full Core Current Productive 29P Cap-2.4 Bound Instrument Provenance Handoff V1

Derived spec. Non-SSOT. Closes runtime dependency
`CURRENT_PRODUCTIVE_CAP24_BOUND_INSTRUMENT_INSTANCE_MISSING` for
`compose_current_productive_29p_common_epoch_handoff_v1` /
`execute_current_productive_29p_common_epoch_handoff_to_first_blocker_v1`.

Cap-2.3 remains selection authority. Cap-2.4
(`run_single_selected_future_runtime_binding_gate_v1`) remains binding
authority. This slice loads persisted runtime state and invokes Cap-2.4
only. No ranking, no Cap-2.3 policy re-run, no manual instrument id,
no historical evidence as runtime input.

```text
THIS_SLICE=11.2.1.EJ.FULL_CORE_CURRENT_PRODUCTIVE_29P_CAP24_BOUND_INSTRUMENT_PROVENANCE_HANDOFF
EXECUTION_IDENTITY=consumer passes repository_sha; persisted provenance via resolve_cap24_persisted_repository_sha_v1
CHAIN_BASELINE_CONTRACT=FULL_CORE_CURRENT_PRODUCTIVE_29P_CHAIN_BASELINE_CONTRACT_V1
DEFAULT_RUNTIME_ROOT=runtime/current_productive/cap24_selection_state
MARK_PRICES_SIDEcar=mark_prices_by_native_id_v1.json
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
MAX_POSITIONS_EFFECTIVE=1
RESELECTION_PERFORMED=false
HISTORICAL_EVIDENCE_RUNTIME_INPUT=false
VENUE_GET_COUNT=0
VENUE_POST_COUNT=0
CONSUMER=execute_current_productive_29p_common_epoch_handoff_to_first_blocker_v1
PRODUCER=acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1
ATLAS_AUTHORITY=NONE
```

Authority chain: persisted Cap-2.1 universe → Cap-2.2 ranking → Cap-2.3
selection → Cap-2.4 bound instrument → 29P common-epoch compose (Cap-2.4
consumer only).
