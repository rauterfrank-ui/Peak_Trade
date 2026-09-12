"""Constants for Cap 2.2 append-only 15m PIT persistence and collection contracts."""

from __future__ import annotations

from src.ops.cap22_historical_evidence_time_semantics_contract_v1 import (
    ANCHOR_GRID,
    ANCHOR_MINUTE_MODULUS,
    RANKING_CADENCE_ID,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (
    MANIFEST_FILENAME as ECONOMIC_MD_MANIFEST_FILENAME,
    SNAPSHOT_FILENAME as ECONOMIC_MD_SNAPSHOT_FILENAME,
)
from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    MANIFEST_FILENAME as CAP21_MANIFEST_FILENAME,
    SNAPSHOT_FILENAME as CAP21_SNAPSHOT_FILENAME,
)

CONTRACT_ID = "CAP22_APPEND_ONLY_15M_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_V1"
DECISION_ID = "CAP22_APPEND_ONLY_15M_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_V1"
SCHEMA_VERSION = "cap22_append_only_15m_pit_persistence.v1"
OWNER_GO_THIS_SLICE = (
    "PEAK_TRADE_CAP22_WP1_APPEND_ONLY_15M_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_V1"
)
BOUND_ORIGIN_MAIN_SHA = "b31c0398b71a9898ed73cf3bfde9cd3e113caa3b"
AUTHORITY_EFFECT = "OFFLINE_APPEND_ONLY_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_ONLY"
AUTHORITY_SCOPE = "OFFLINE_APPEND_ONLY_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_ONLY"
PRODUCTIVE_SELECTION_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"

COLLECTION_CADENCE_ID = RANKING_CADENCE_ID
COLLECTION_CADENCE_GRID = ANCHOR_GRID
COLLECTION_ANCHOR_MINUTE_MODULUS = ANCHOR_MINUTE_MODULUS
COLLECTION_NETWORK_AUTHORIZED = False
COLLECTION_SCHEDULER_ENABLED = False
PROSPECTIVE_COLLECTION_STARTED = False
CAP22_PROSPECTIVE_COLLECTION_CONTRACTS_IMPLEMENTED = True
CAP22_PROSPECTIVE_COLLECTION_STARTED = False
CAP22_90D_EVIDENCE_CLOCK_STARTED = False

CAP21_APPEND_ONLY_AT_T_PERSISTENCE_IMPLEMENTED = True
ECONOMIC_MD_APPEND_ONLY_AT_T_PERSISTENCE_IMPLEMENTED = True
EXACT_T_BINDING_REQUIRED = True
NO_NEAREST_LATEST_FALLBACK = True
NO_TODAY_UNIVERSE_MEMBERSHIP_RETROACTIVE = True
NO_AS_OF_GUESSING = True
NO_IMPLICIT_FILL = True
APPEND_ONLY = True
CONFLICTING_OVERWRITE_FORBIDDEN = True
IDENTICAL_DUPLICATE_IDEMPOTENT = True

CAP21_UNIVERSE_AT_T_DIRNAME = "cap21_universe_at_t"
ECONOMIC_MD_AT_T_DIRNAME = "economic_md_at_t"

CAP21_EXISTING_PRODUCER_AUTHORITY_PRESERVED = True
CAP21_NEW_MEMBERSHIP_OWNER_CREATED = False
CAP22_MEMBERSHIP_AUTHORITY_ADDED = False
CAP22_SELECTION_AUTHORITY_ADDED = False
ECONOMIC_MD_EXISTING_PRODUCER_AUTHORITY_PRESERVED = True
ECONOMIC_MD_PRODUCER_MAY_RANK = False
ECONOMIC_MD_PRODUCER_MAY_SELECT = False
ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED = False
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED = False
ECONOMIC_RANK_ACTIVATED = False
HISTORICAL_EVIDENCE_GENERATED = False
FORWARD_LABEL_EXECUTION_IMPLEMENTED = False
WALK_FORWARD_EXECUTION_IMPLEMENTED = False
POLICY_RATIFICATION_JUSTIFIED = False
PDF_STEP_5_STATUS = "UNRESOLVED"
ROTATION_POLICY_STATUS = "FAIL_CLOSED_UNTIL_PDF_STEP_5"
PDF_STEP_7_STATUS = "FORBIDDEN"
PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED = False
RUNTIME_AUTHORITY_GRANTED = False
PRODUCTIVE_MF_HOST_JOIN = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK = True
NEXT_CANONICAL_DECISION = "PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION"
NEXT_CAP22_DEPENDENCY = (
    "SEPARATE_OWNER_GO_REQUIRED_FOR_PROSPECTIVE_15M_CAP21_AND_ECONOMIC_MD_COLLECTION"
)

FALSE_REQUIRED_FLAGS: tuple[str, ...] = (
    "cap22_membership_authority_added",
    "cap22_productive_economic_runtime_wired",
    "cap22_prospective_collection_started",
    "cap22_selection_authority_added",
    "cap22_90d_evidence_clock_started",
    "collection_network_authorized",
    "collection_scheduler_enabled",
    "economic_md_producer_may_rank",
    "economic_md_producer_may_select",
    "economic_md_producer_productively_scheduled",
    "economic_rank_activated",
    "forward_label_execution_implemented",
    "historical_evidence_generated",
    "multi_future_runtime_authorized",
    "policy_ratification_justified",
    "productive_mf_host_join",
    "prospective_collection_started",
    "runtime_authority_granted",
    "walk_forward_execution_implemented",
)

TRUE_REQUIRED_FLAGS: tuple[str, ...] = (
    "append_only",
    "cap21_append_only_at_t_persistence_implemented",
    "cap21_existing_producer_authority_preserved",
    "cap22_prospective_collection_contracts_implemented",
    "conflicting_overwrite_forbidden",
    "downstream_execution_must_not_re_rank",
    "economic_md_append_only_at_t_persistence_implemented",
    "economic_md_existing_producer_authority_preserved",
    "exact_t_binding_required",
    "identical_duplicate_idempotent",
    "no_as_of_guessing",
    "no_implicit_fill",
    "no_nearest_latest_fallback",
    "no_today_universe_membership_retroactive",
)
