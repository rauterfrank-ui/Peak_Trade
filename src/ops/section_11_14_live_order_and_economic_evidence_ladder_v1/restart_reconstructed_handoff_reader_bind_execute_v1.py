"""Execute restart-reader / provenance / consumer-bind persist.

No GET. No POST. No restart execution. No historical canary rewrite.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_READER_BIND_OWNER_GO,
    HISTORICAL_READER_BIND_RUN_ID,
    HISTORICAL_READER_BIND_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    WRITER_SEAM_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_bind_v1 import (
    bind_restart_reader_provenance_and_consumer_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    HANDOFF_SCHEMA_VERSION,
    SELECTED_SEMANTIC_ID,
)


def execute_live_handoff_restart_reader_provenance_and_consumer_bind_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != HISTORICAL_READER_BIND_OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != HISTORICAL_READER_BIND_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or HISTORICAL_READER_BIND_RUN_ID)
    binding = bind_restart_reader_provenance_and_consumer_v1()
    adjudication = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    if adjudication.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if binding["COMPLETE_CAPTURE_SEAM"] != "UNPROVEN":
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if binding["READER_BOUND"] is not True:
        raise Section1114OfflineSurfaceError("READER_MUST_BE_BOUND")
    if binding["RESTART_CONSUMER_BOUND"] is not True:
        raise Section1114OfflineSurfaceError("CONSUMER_MUST_BE_BOUND")
    if binding["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is True:
        raise Section1114OfflineSurfaceError("HISTORICAL_CANARY_MUST_REMAIN_UNOBSERVED")
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = {
        "OWNER_GO": HISTORICAL_READER_BIND_OWNER_GO,
        "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "STARTED_AT_UTC": started,
        "ENDED_AT_UTC": ended,
        "LIVE_ACCOUNTING_RECONSTRUCTED": True,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "LIVE_AUTONOMOUS_RECOVERY_OBSERVED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
        "FIRST_OWNER_PRODUCTIVELY_BOUND": True,
        "POS_SEMANTICS": "PROVEN",
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "NEW_PRODUCER_CONTRACT_DEFINED": True,
        "NEW_PRODUCER_IMPLEMENTED": True,
        "PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED": True,
        "CAPTURE_TRIGGER_STATUS": binding["CAPTURE_TRIGGER_STATUS"],
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "CAPTURE_TRIGGER_PRODUCTIVELY_BOUND": True,
        "HANDOFF_REQUIRED_FIELD_COUNT": len(REQUIRED_HANDOFF_FIELDS),
        "HANDOFF_SCHEMA_VERSION": HANDOFF_SCHEMA_VERSION,
        "SCHEMA_CHANGE_REQUIRED": False,
        "STORAGE_OWNER_MINTED": True,
        "SELECTED_STORAGE_OWNER": FIRST_OWNER_ID,
        "WRITER_BOUND": True,
        "WRITER_SEAM_ID": WRITER_SEAM_ID,
        "READER_BOUND": True,
        "READER_IMPLEMENTED": True,
        "SELECTED_PRODUCTIVE_READER": binding["SELECTED_PRODUCTIVE_READER"],
        "READER_CANDIDATE_COUNT": binding["READER_CANDIDATE_COUNT"],
        "SCHEMA_VALIDATION": binding["SCHEMA_VALIDATION"],
        "IDENTITY_VALIDATION": binding["IDENTITY_VALIDATION"],
        "S05_VALIDATION": binding["S05_VALIDATION"],
        "POSSIDE_VALIDATION": binding["POSSIDE_VALIDATION"],
        "PROVENANCE_VALIDATION": binding["PROVENANCE_VALIDATION"],
        "FRESHNESS_VALIDATION": binding["FRESHNESS_VALIDATION"],
        "MALFORMED_DATA_REJECTION": True,
        "STALE_DATA_REJECTION": True,
        "WRONG_INSTRUMENT_REJECTION": True,
        "RESTART_CONSUMER_SELECTED": binding["RESTART_CONSUMER_SELECTED"],
        "RESTART_CONSUMER_BOUND": True,
        "CAPTURE_SEAM_BOUND": False,
        "PRODUCTIVE_BINDING_PRESENT": True,
        "DURABLE_SUCCESS_ACK_BEFORE_MUTATION_SUCCESS_CLAIM": True,
        "PROCESS_RESTART_READABLE_HANDOFF_RECORD": True,
        "PROCESS_RESTART_PROOF": binding["PROCESS_RESTART_PROOF"],
        "HOST_CRASH_PROOF": "UNPROVEN",
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "POWER_LOSS_DURABILITY": "UNPROVEN",
        "DURABILITY_PROVEN_EFFECTIVE": False,
        "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": list(
            binding["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"]
        ),
        "LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED": True,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "HISTORICAL_DATA_REINTERPRETATION_ALLOWED": False,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": False,
        "NO_TIMESTAMP_BACKFILL": True,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": True,
        "IMPLEMENTATION_AUTHORIZED": False,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "DEPENDENT_MUTATION_ALLOWED": False,
        "PRODUCTIVE_HOST_BINDING": False,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CREDENTIAL_USE": False,
        "SECRET_VALUES_INCLUDED": False,
        "RESTART_EXECUTION": False,
        "WIRE_SEND": False,
        "LIVE_ACTION": "NONE",
        "RAW_EVIDENCE_MODIFIED": False,
        "PROPOSED_NEXT_SLICE": binding["PROPOSED_NEXT_SLICE"],
        "repo_root": str(repo_root),
    }
    pack = (
        repo_root
        / "evidence"
        / "ops"
        / ("section_11_14_live_order_and_economic_evidence_ladder_v1")
        / pack_run_id
    )
    return {
        "summary": summary,
        "binding": binding,
        "owner_mint": dict(binding["owner_mint"]),
        "reader_census": dict(binding["reader_census"]),
        "consumer_binding": {
            "RESTART_CONSUMER_SELECTED": binding["RESTART_CONSUMER_SELECTED"],
            "RESTART_CONSUMER_BOUND": True,
            "LIVE_RESTART_RECONSTRUCTED": False,
        },
        "validation_matrix": {
            "SCHEMA_VALIDATION": binding["SCHEMA_VALIDATION"],
            "IDENTITY_VALIDATION": binding["IDENTITY_VALIDATION"],
            "S05_VALIDATION": binding["S05_VALIDATION"],
            "POSSIDE_VALIDATION": binding["POSSIDE_VALIDATION"],
            "PROVENANCE_VALIDATION": binding["PROVENANCE_VALIDATION"],
            "FRESHNESS_VALIDATION": binding["FRESHNESS_VALIDATION"],
        },
        "failure_matrix": {
            "MISSING_HANDOFF": "FAIL_CLOSED",
            "MALFORMED_HANDOFF": "FAIL_CLOSED",
            "STALE_HANDOFF": "FAIL_CLOSED",
            "WRONG_INSTRUMENT": "FAIL_CLOSED",
            "PROVENANCE_INVALID": "FAIL_CLOSED",
            "SCHEMA_INVALID": "FAIL_CLOSED",
            "READ_FAILURE": "FAIL_CLOSED",
            "NO_VENUE_GET_FALLBACK": True,
            "NO_EVIDENCE_PACK_FALLBACK": True,
        },
        "seam_predicate": {
            "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
            "MISSING_PREDICATES": list(binding["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"]),
            "PREDICATES": dict(binding["COMPLETE_CAPTURE_SEAM_PREDICATES"]),
        },
        "baseline": {
            "EXPECTED_ORIGIN_MAIN_SHA": HISTORICAL_READER_BIND_SHA,
            "ORIGIN_MAIN_SHA": origin_main_sha,
            "EXPECTED_ORIGIN_MAIN_MATCH": origin_main_sha == HISTORICAL_READER_BIND_SHA,
            "OWNER_GO": HISTORICAL_READER_BIND_OWNER_GO,
            "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        },
        "changed_path_census": {
            "SCOPE": "SECTION_11_14_LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND_V1",
            "UNTRACKED_FOREIGN_EVIDENCE_UNTOUCHED": True,
            "paths": [
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/constants_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/__init__.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_handoff_reader_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_handoff_reader_census_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_handoff_reader_bind_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_handoff_reader_bind_execute_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_handoff_consumer_bind_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_handoff_implementation_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/restart_reconstructed_handoff_implementation_execute_v1.py",
                "scripts/ops/run_section_11_14_live_handoff_restart_reader_provenance_and_consumer_bind_v1.py",
                "scripts/ops/run_section_11_14_live_handoff_pos_producer_capture_record_owner_and_writer_implementation_v1.py",
                "tests/ops/test_section_11_14_live_handoff_restart_reader_provenance_and_consumer_bind_v1.py",
                "tests/ops/test_section_11_14_live_handoff_pos_producer_capture_record_owner_and_writer_implementation_v1.py",
                "tests/ops/test_section_11_14_live_order_and_economic_evidence_ladder_persist_v1.py",
                "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND_V1.md",
                "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
                "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md",
                "docs/system_atlas/entities/catalog.yaml",
                "docs/system_atlas/relations/runtime.yaml",
            ],
        },
        "selected_reader": {
            "SELECTED_PRODUCTIVE_READER": binding["SELECTED_PRODUCTIVE_READER"],
            "STORAGE_OWNER_ID": FIRST_OWNER_ID,
            "READER_BOUND": True,
            "VENUE_GET_FALLBACK": False,
            "EVIDENCE_PACK_FALLBACK": False,
        },
        "reader_result_contract": {
            "VALID_HANDOFF": "CONSUMER_MAY_ACCEPT",
            "MISSING_HANDOFF": "FAIL_CLOSED",
            "MALFORMED_HANDOFF": "FAIL_CLOSED",
            "STALE_HANDOFF": "FAIL_CLOSED",
            "WRONG_INSTRUMENT": "FAIL_CLOSED",
            "PROVENANCE_INVALID": "FAIL_CLOSED",
            "SCHEMA_INVALID": "FAIL_CLOSED",
            "READ_FAILURE": "FAIL_CLOSED",
        },
        "semantic_readjudication": {
            "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
            "S05_VALIDATION": binding["S05_VALIDATION"],
            "POS_SIGN_SEMANTICS": "UNSIGNED_MAGNITUDE",
            "NO_FILLSZ_SUBSTITUTION": True,
            "NO_VENUE_GET_SUBSTITUTION": True,
            "NO_INFERRED_SIGN_FROM_POSSIDE": True,
        },
        "process_restart_proof": {
            "PROCESS_RESTART_READABLE_HANDOFF_RECORD": True,
            "PROCESS_RESTART_PROOF": binding["PROCESS_RESTART_PROOF"],
            "HOST_CRASH_DURABILITY": "UNPROVEN",
        },
        "safety": {
            "LIVE_ENABLED": False,
            "LIVE_ARMED": False,
            "CANARY_AUTHORIZED": False,
            "GET_PERFORMED": False,
            "POST_USED": False,
            "WIRE_SEND": False,
            "LIVE_ACTION": "NONE",
            "CREDENTIAL_USE": False,
            "IMPLEMENTATION_AUTHORIZED": False,
            "NEXT_SLICE_AUTHORIZED": False,
        },
        "claims": dict(CLAIMS),
        "adjudication": adjudication,
        "pack": str(pack),
        "raw_exchanges": [],
    }
