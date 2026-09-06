"""Execute owner-bind and retroactive-synthesis-refusal persist. No GET. No POST."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
    A1_WAL_REQUIRED_FOR_THIS_FIELD,
    ACCOUNTING_ONLY_IS_NOT_RESTART,
    ACCOUNTING_RECONSTRUCTION_IS_PREDECESSOR_NOT_RESTART,
    CANARY_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY,
    CANONICAL_EVIDENCE_RUN_ID,
    CAN_LIVE_RESTART_BE_RECONSTRUCTED_FROM_FRESH_VENUE_AND_IMMUTABLE_EVIDENCE,
    CENSUS_PHASE_RETAINED,
    CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED,
    DOES_LIVE_RESTART_RECONSTRUCTED_REQUIRE_A1_WAL,
    DOES_LIVE_RESTART_RECONSTRUCTED_REQUIRE_HOST_CRASH_DURABILITY,
    EXPECTED_ORIGIN_MAIN_SHA,
    FRESH_PROCESS_RESTART_REQUIRED_FOR_THIS_FIELD,
    FULL_CORE_29P_REQUIRED_FOR_THIS_FIELD,
    HISTORICAL_LIVE_RESTART_HANDOFF_STATUS,
    HISTORICAL_OWNER_BIND_OWNER_GO,
    HISTORICAL_OWNER_BIND_SHA,
    HOST_CRASH_DURABILITY_REQUIRED_FOR_THIS_FIELD,
    LIVE_RESTART_DEFINITION,
    LIVE_RESTART_GRAPH_COMPLETE,
    LIVE_RESTART_RECONSTRUCTED,
    LIVE_RESTART_RECONSTRUCTED_ACCEPTANCE_REQUIRES,
    NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF,
    NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    NO_TIMESTAMP_BACKFILL,
    OWNER_GO,
    POST_HOC_IDENTITY_MATCH_DOES_NOT_PROVE_PRE_RESTART_CAPTURE,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    RETROACTIVE_PROOF_FROM_POST_SUBMIT_VENUE_STATE_ALLOWED,
    SECTION_11_14_IS_NOT_SECOND_PRODUCTIVE_LIVE_AUTHORITY,
    TRACK_1,
    TRACK_2,
    VENUE_GET_ACCOUNTING_PATH_IS_NOT_RESTART_HANDOFF,
    VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_exhaustive_execute_v1 import (
    execute_live_restart_reconstructed_exhaustive_census_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_historical_unprovability_v1 import (
    bind_historical_live_restart_unprovability_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
    BOUND_FILL_SZ,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_bind_v1 import (
    bind_section_11_14_live_handoff_owner_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_census_matrix_v1 import (
    bind_section_11_14_live_handoff_owner_census_matrix_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    evaluate_handoff_proof_bundle_v1,
    refuse_retroactive_handoff_synthesis_v1,
)

_IDENTITY_HANDOFF = {
    "clOrdId": BOUND_CLORDID,
    "ordId": BOUND_ORDID,
    "instId": BOUND_INSTID,
    "posSide": BOUND_POS_SIDE,
    "pos": BOUND_FILL_SZ,
}


def execute_live_restart_handoff_owner_bind_and_retroactive_synthesis_refusal_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    allowed_owner_gos = {OWNER_GO, HISTORICAL_OWNER_BIND_OWNER_GO}
    allowed_shas = {EXPECTED_ORIGIN_MAIN_SHA, HISTORICAL_OWNER_BIND_SHA}
    if str(owner_go or "").strip() not in allowed_owner_gos:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() not in allowed_shas:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or CANONICAL_EVIDENCE_RUN_ID)
    exhaustive = execute_live_restart_reconstructed_exhaustive_census_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_main_sha,
        repo_root=Path(repo_root),
        run_id=pack_run_id,
    )
    owner_matrix = bind_section_11_14_live_handoff_owner_census_matrix_v1()
    if owner_matrix["LIVE_SCOPED_IDENTITY_BOUND_CONTEMPORANEOUS_HANDOFF_OWNER_FOUND"] is True:
        raise Section1114OfflineSurfaceError(
            "EXISTING_LIVE_HANDOFF_OWNER_FOUND_HARD_STOP_PRIOR_ADJUDICATION_WOULD_CHANGE"
        )
    census = dict(exhaustive["census"])
    if census.get("LIVE_SCOPED_IDENTITY_BOUND_CONTEMPORANEOUS_HANDOFF_OWNER_FOUND") is True:
        raise Section1114OfflineSurfaceError(
            "EXISTING_LIVE_HANDOFF_OWNER_FOUND_HARD_STOP_PRIOR_ADJUDICATION_WOULD_CHANGE"
        )
    if census.get("SECTION_11_14_LIVE_DURABLE_STATE_WRITER_EXISTS") is True:
        raise Section1114OfflineSurfaceError(
            "EXISTING_LIVE_HANDOFF_OWNER_FOUND_HARD_STOP_PRIOR_ADJUDICATION_WOULD_CHANGE"
        )
    owner_bind = bind_section_11_14_live_handoff_owner_contract_v1()
    historical = bind_historical_live_restart_unprovability_v1()
    synthetic_get = refuse_retroactive_handoff_synthesis_v1(
        handoff=_IDENTITY_HANDOFF,
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path=(
            "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "20260904T181817Z/GET_POSITIONS.raw.json"
        ),
        synthetic_from_venue_get=True,
        provenance_class="VENUE_GET_COPY",
    )
    identity_without_provenance = evaluate_handoff_proof_bundle_v1(
        handoff=_IDENTITY_HANDOFF,
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="durable_state/pre_restart.json",
        contemporaneous_capture_proven=False,
    )
    timestamp_backfill = refuse_retroactive_handoff_synthesis_v1(
        handoff={**_IDENTITY_HANDOFF, "captured_at_utc": "2026-09-04T16:00:00Z"},
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="durable_state/pre_restart.json",
        timestamp_backfill=True,
        provenance_class="TIMESTAMP_BACKFILL",
    )
    synthesis_refusal = {
        "DOCUMENT_CLASS": "SECTION_11_14_RETROACTIVE_HANDOFF_SYNTHESIS_REFUSAL_V1",
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "ACCOUNTING_ONLY_IS_NOT_RESTART": ACCOUNTING_ONLY_IS_NOT_RESTART,
        "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF": (
            VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF
        ),
        "POST_HOC_IDENTITY_MATCH_DOES_NOT_PROVE_PRE_RESTART_CAPTURE": (
            POST_HOC_IDENTITY_MATCH_DOES_NOT_PROVE_PRE_RESTART_CAPTURE
        ),
        "NO_TIMESTAMP_BACKFILL": NO_TIMESTAMP_BACKFILL,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
        "NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF": (
            NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF
        ),
        "synthetic_get_positions_rejected": synthetic_get,
        "identity_match_without_contemporaneous_provenance_rejected": (identity_without_provenance),
        "timestamp_backfill_rejected": timestamp_backfill,
    }
    census_persist = {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_ADDITIVE_CENSUS_PERSIST_V1",
        "CENSUS_PHASE_RETAINED": CENSUS_PHASE_RETAINED,
        "CURRENT_PHASE": CENSUS_PHASE_RETAINED,
        "LIVE_RESTART_RECONSTRUCTED_STATUS": LIVE_RESTART_RECONSTRUCTED,
        "LIVE_RESTART_RECONSTRUCTED": LIVE_RESTART_RECONSTRUCTED,
        "LIVE_RESTART_DEFINITION": LIVE_RESTART_DEFINITION,
        "LIVE_RESTART_RECONSTRUCTED_ACCEPTANCE_REQUIRES": (
            LIVE_RESTART_RECONSTRUCTED_ACCEPTANCE_REQUIRES
        ),
        "ACCOUNTING_RECONSTRUCTION_IS_PREDECESSOR_NOT_RESTART": (
            ACCOUNTING_RECONSTRUCTION_IS_PREDECESSOR_NOT_RESTART
        ),
        "VENUE_GET_ACCOUNTING_PATH_IS_NOT_RESTART_HANDOFF": (
            VENUE_GET_ACCOUNTING_PATH_IS_NOT_RESTART_HANDOFF
        ),
        "FRESH_PROCESS_RESTART_REQUIRED_FOR_THIS_FIELD": (
            FRESH_PROCESS_RESTART_REQUIRED_FOR_THIS_FIELD
        ),
        "HOST_CRASH_DURABILITY_REQUIRED_FOR_THIS_FIELD": (
            HOST_CRASH_DURABILITY_REQUIRED_FOR_THIS_FIELD
        ),
        "A1_WAL_REQUIRED_FOR_THIS_FIELD": A1_WAL_REQUIRED_FOR_THIS_FIELD,
        "FULL_CORE_29P_REQUIRED_FOR_THIS_FIELD": FULL_CORE_29P_REQUIRED_FOR_THIS_FIELD,
        "CANARY_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY": (
            CANARY_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY
        ),
        "LIVE_RESTART_GRAPH_COMPLETE": LIVE_RESTART_GRAPH_COMPLETE,
        "DOES_LIVE_RESTART_RECONSTRUCTED_REQUIRE_A1_WAL": (
            DOES_LIVE_RESTART_RECONSTRUCTED_REQUIRE_A1_WAL
        ),
        "DOES_LIVE_RESTART_RECONSTRUCTED_REQUIRE_HOST_CRASH_DURABILITY": (
            DOES_LIVE_RESTART_RECONSTRUCTED_REQUIRE_HOST_CRASH_DURABILITY
        ),
        "CAN_LIVE_RESTART_BE_RECONSTRUCTED_FROM_FRESH_VENUE_AND_IMMUTABLE_EVIDENCE": (
            CAN_LIVE_RESTART_BE_RECONSTRUCTED_FROM_FRESH_VENUE_AND_IMMUTABLE_EVIDENCE
        ),
        "A1_WAL_AS_LIVE_HANDOFF_ALLOWED": A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
        "TRACK_1": TRACK_1,
        "TRACK_2": TRACK_2,
        "SECTION_11_14_IS_NOT_SECOND_PRODUCTIVE_LIVE_AUTHORITY": (
            SECTION_11_14_IS_NOT_SECOND_PRODUCTIVE_LIVE_AUTHORITY
        ),
        "exhaustive_census": census,
    }
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = {
        "OWNER_GO": OWNER_GO,
        "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "STARTED_AT_UTC": started,
        "ENDED_AT_UTC": ended,
        "LIVE_ACCOUNTING_RECONSTRUCTED": True,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "LIVE_AUTONOMOUS_RECOVERY_OBSERVED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": owner_bind[
            "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT"
        ],
        "SECTION_11_14_LIVE_HANDOFF_OWNER_BOUND": owner_bind[
            "SECTION_11_14_LIVE_HANDOFF_OWNER_BOUND"
        ],
        "SECTION_11_14_LIVE_HANDOFF_WRITER_PRESENT": owner_bind[
            "SECTION_11_14_LIVE_HANDOFF_WRITER_PRESENT"
        ],
        "SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_BINDING": owner_bind[
            "SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_BINDING"
        ],
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "ACCOUNTING_ONLY_IS_NOT_RESTART": ACCOUNTING_ONLY_IS_NOT_RESTART,
        "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF": (
            VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF
        ),
        "POST_HOC_IDENTITY_MATCH_DOES_NOT_PROVE_PRE_RESTART_CAPTURE": (
            POST_HOC_IDENTITY_MATCH_DOES_NOT_PROVE_PRE_RESTART_CAPTURE
        ),
        "HISTORICAL_LIVE_RESTART_HANDOFF_STATUS": HISTORICAL_LIVE_RESTART_HANDOFF_STATUS,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": (
            CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED
        ),
        "RETROACTIVE_PROOF_FROM_POST_SUBMIT_VENUE_STATE_ALLOWED": (
            RETROACTIVE_PROOF_FROM_POST_SUBMIT_VENUE_STATE_ALLOWED
        ),
        "A1_WAL_AS_LIVE_HANDOFF_ALLOWED": A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
        "NEW_STORAGE_OWNER_CREATED": False,
        "NEW_RECONCILIATION_ENGINE_CREATED": False,
        "NEW_EXECUTION_STATE_MACHINE_CREATED": False,
        "SECOND_RESTART_STATE_OWNER_CREATED": False,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CREDENTIAL_USE": False,
        "RESTART_EXECUTION": False,
        "RAW_EVIDENCE_MODIFIED": False,
        "SECRET_VALUES_INCLUDED": False,
    }
    pack = (
        Path(repo_root)
        / "evidence"
        / "ops"
        / ("section_11_14_live_order_and_economic_evidence_ladder_v1")
        / pack_run_id
    )
    return {
        "pack": str(pack),
        "summary": summary,
        "adjudication": exhaustive["adjudication"],
        "census": census,
        "census_persist": census_persist,
        "owner_bind": owner_bind,
        "owner_matrix": owner_matrix,
        "synthesis_refusal": synthesis_refusal,
        "historical_unprovability": historical,
        "code_path_census": exhaustive["code_path_census"],
        "future_owner_go_contract": exhaustive["future_owner_go_contract"],
        "validator_matrix": exhaustive["validator_matrix"],
        "raw_exchanges": [],
    }
