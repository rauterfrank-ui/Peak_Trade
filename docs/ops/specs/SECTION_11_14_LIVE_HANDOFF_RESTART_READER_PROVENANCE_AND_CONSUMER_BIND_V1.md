---
docs_token: DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND_V1
status: active
scope: §11.14 Live restart reader bound to minted SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1; schema-v1 five-field and S05 validation; envelope provenance contract-proven; freshness partial; restart reconstruction consumer bound; COMPLETE_CAPTURE_SEAM remains UNPROVEN; LIVE_RESTART_RECONSTRUCTED remains false; contemporaneous Live pre-restart observation remains false; host-crash durability unproven; no GET; no POST; no schema v2
capability: SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-07
---

# Section 11.14 Live Handoff Restart Reader Provenance And Consumer Bind V1

## Goal

Implement the productive restart reader, bind it exclusively to the minted
Live durable pre-restart handoff owner, validate schema v1, identity, S05,
posSide, envelope provenance, and applicable freshness, and bind the
restart-reconstruction consumer to a validated reader result only.
Do not GET. Do not POST. Do not invent schema v2. Do not claim host-crash
durability. Do not promote LIVE_RESTART_RECONSTRUCTED. Do not rewrite
historical canary provenance. Do not synthesize a contemporaneous Live
pre-restart observation from tests.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=none
SECTION_11_14_AUTHORIZED=false
SECTION_11_14_COMPLETE=false
LIVE_ACCOUNTING_RECONSTRUCTED=true
LIVE_RESTART_RECONSTRUCTED=false
LIVE_AUTONOMOUS_RECOVERY_OBSERVED=false
CURRENT_PHASE=11.14.LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND
SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1
FIRST_OWNER_PRODUCTIVELY_BOUND=true
POS_SEMANTICS=PROVEN
SELECTED_SEMANTIC_ID=S05_PEAK_TRADE_OWNED_RESULTING_CURRENT_POSITION_QTY_VENUE_CONTRACT_COUNT_UNSIGNED
NEW_PRODUCER_IMPLEMENTED=true
PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED=true
STORAGE_OWNER_MINTED=true
SELECTED_STORAGE_OWNER=SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1
WRITER_BOUND=true
READER_BOUND=true
SELECTED_PRODUCTIVE_READER=read_validated_durable_pre_restart_handoff_v1
HANDOFF_SCHEMA_VERSION=section_11_14_live_durable_pre_restart_handoff.v1
HANDOFF_REQUIRED_FIELD_COUNT=5
SCHEMA_CHANGE_REQUIRED=false
SCHEMA_VALIDATION=PASS
IDENTITY_VALIDATION=PASS
S05_VALIDATION=PASS
POSSIDE_VALIDATION=PASS
PROVENANCE_VALIDATION=CONTRACT_PROVEN
FRESHNESS_VALIDATION=PARTIAL
MALFORMED_DATA_REJECTION=true
STALE_DATA_REJECTION=true
WRONG_INSTRUMENT_REJECTION=true
RESTART_CONSUMER_BOUND=true
CAPTURE_SEAM_BOUND=false
PRODUCTIVE_BINDING_PRESENT=true
PROCESS_RESTART_READABLE_HANDOFF_RECORD=true
HOST_CRASH_DURABILITY=UNPROVEN
COMPLETE_CAPTURE_SEAM=UNPROVEN
COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES=PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL
LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED=true
CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false
HISTORICAL_DATA_REINTERPRETATION_ALLOWED=false
RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false
NO_TIMESTAMP_BACKFILL=true
NO_SYNTHETIC_PRE_RESTART_PROVENANCE=true
IMPLEMENTATION_AUTHORIZED=false
ADMISSION_TRUE=false
SUPERVISOR_ACTIVATED=false
WIRE_SEND=false
LIVE_ACTION=NONE
PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_CONTEMPORANEOUS_PRE_RESTART_OBSERVATION_V1
```

## Bound outcome

The productive restart reader `read_validated_durable_pre_restart_handoff_v1`
reads only `SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1`. Schema
remains `section_11_14_live_durable_pre_restart_handoff.v1`. Required fields
remain exactly `{clOrdId, ordId, instId, posSide, pos}`. `pos` retains S05
unsigned venue-contract-count semantics and must Decimal-equal the bound Live
identity. `posSide` remains the net-mode token `net`. Envelope provenance
(`owner_id`, `claimed_owner`, `provenance_class`) is contract-validated and
is not an empirical contemporaneous Live observation. Freshness is partial:
attempt identity, bound identity, schema, completeness, and optional temporal
order when a restart timestamp is supplied. No TTL is invented. The consumer
`consume_validated_handoff_for_restart_reconstruction_v1` accepts only
`VALID_HANDOFF` and rejects every other typed result without fallback.
`COMPLETE_CAPTURE_SEAM` remains `UNPROVEN` because
`PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL` is not empirically proven.
`LIVE_RESTART_RECONSTRUCTED` remains false.
`CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED` remains false.
Host-crash durability remains `UNPROVEN`. No GET. No POST. No restart
execution.
