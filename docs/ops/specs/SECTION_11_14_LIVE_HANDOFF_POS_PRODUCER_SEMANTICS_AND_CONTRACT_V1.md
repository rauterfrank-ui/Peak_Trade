---
docs_token: DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT_V1
status: active
scope: §11.14 Live handoff pos producer semantics and contract; unique meaning/unit/sign Owner-bound; new contemporaneous Peak_Trade-owned producer contract-only; no writer/reader/storage mint; capture seam remains UNPROVEN but can now be adjudicated; restart remains false; section 11.14 incomplete
capability: SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-07
---

# Section 11.14 Live Handoff Pos Producer Semantics And Contract V1

## Goal

Make the previously missing Owner-level `pos` semantic choice explicit and
auditable. Bind unique meaning, unit, and sign if and only if a single
coherent contract is proveable. Define a new Peak_Trade-owned
contemporaneous producer at contract level only. Do not implement a writer.
Do not mint an owner. Do not GET. Do not POST. Do not execute a restart.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=none
SECTION_11_14_AUTHORIZED=false
SECTION_11_14_COMPLETE=false
LIVE_ACCOUNTING_RECONSTRUCTED=true
LIVE_RESTART_RECONSTRUCTED=false
LIVE_AUTONOMOUS_RECOVERY_OBSERVED=false
CURRENT_PHASE=11.14.LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT
SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=NONE
FIRST_OWNER_PRODUCTIVELY_BOUND=false
POS_SEMANTICS=PROVEN
POS_SEMANTICS_STATUS=PROVEN
POS_SEMANTICS_CANONICALLY_BOUND=true
POS_CANONICAL_MEANING=Peak_Trade-owned contemporaneous resulting/current position quantity for BOUND_INSTID as of handoff-commit immediately before restart
POS_UNIT=VENUE_CONTRACT_COUNT_NUMBER_OF_CONTRACTS
POS_SIGN_SEMANTICS=UNSIGNED_MAGNITUDE
POS_POS_SIDE_RELATION=MANDATORY_IDENTITY_FIELD_NET_MODE_TOKEN_NOT_DIRECTION
POS_POSITION_MODE_BINDING=ACCOUNT_CONFIG_POSMODE_RAW_net_mode
POS_ACCOUNT_MODE_BINDING=IRRELEVANT_FOR_HANDOFF_POS_QUANTITY
POS_TEMPORAL_MEANING=HANDOFF_COMMIT_IMMEDIATELY_BEFORE_RESTART_DESCRIBING_RESULTING_POSITION_AFTER_BOUND_FILL_AND_BEFORE_RESTART
SELECTED_SEMANTIC_ID=S05_PEAK_TRADE_OWNED_RESULTING_CURRENT_POSITION_QTY_VENUE_CONTRACT_COUNT_UNSIGNED
SELECTED_SEMANTIC_UNIQUE=true
NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED=true
NEW_PRODUCER_CONTRACT_DEFINED=true
NEW_PRODUCER_IMPLEMENTED=false
PRODUCER_ID=SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_V1
PRODUCER_CONTRACT_COMPLETE=true
HANDOFF_SCHEMA_VERSION=section_11_14_live_durable_pre_restart_handoff.v1
SCHEMA_CHANGE_REQUIRED=false
HISTORICAL_DATA_REINTERPRETATION_ALLOWED=false
COMPLETE_CAPTURE_SEAM=UNPROVEN
COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED=true
OWNER_MINT_CAN_NOW_BE_ADJUDICATED=false
WRITER_BIND_CAN_NOW_BE_ADJUDICATED=false
READER_BIND_CAN_NOW_BE_ADJUDICATED=false
LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED=false
HOST_CRASH_DURABILITY=UNPROVEN
POWER_LOSS_DURABILITY=UNPROVEN
DURABILITY_PROVEN_EFFECTIVE=false
STORAGE_OWNER_MINTED=false
WRITER_BOUND=false
READER_BOUND=false
CAPTURE_SEAM_BOUND=false
PRODUCTIVE_BINDING_PRESENT=false
ADMISSION_TRUE=false
SUPERVISOR_ACTIVATED=false
IMPLEMENTATION_AUTHORIZED=false
TOKEN_NAME_IDENTITY_IS_NOT_SEMANTIC_IDENTITY=true
RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false
NO_TIMESTAMP_BACKFILL=true
NO_SYNTHETIC_PRE_RESTART_PROVENANCE=true
WIRE_SEND=false
LIVE_ACTION=NONE
```

## Decision

§11.14 restart reconstruction reconstructs Peak_Trade durable pre-restart
control-state identity, not venue accounting. Owner binds handoff `pos` to
Peak_Trade-owned contemporaneous resulting/current position quantity in
venue contract count as unsigned magnitude. `posSide=net` is a mandatory
net-mode identity token and does not encode long/short. Account mode
`tdMode=cross` is irrelevant to this quantity. A new Peak_Trade-owned
contemporaneous producer is contracted and not implemented. Capture seam,
owner mint, writer/reader bind, and restart reconstruction remain
fail-closed. Historical `POS_SEMANTICS=UNPROVEN` records are not
reinterpreted.
