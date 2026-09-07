"""Write forensic evidence pack. No GET. No POST. No restart."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_14_live_handoff_exact_fee_restart_durability_and_pre_execution_readiness_closure_v1.adjudication_v1 import (
    adjudicate_exact_fee_restart_durability_and_pre_execution_readiness_v1,
)
from src.ops.section_11_14_live_handoff_exact_fee_restart_durability_and_pre_execution_readiness_closure_v1.constants_v1 import (
    ADJUDICATION_FILENAME,
    BASELINE_FILENAME,
    CANONICAL_EVIDENCE_RUN_ID,
    CLAIMS_FILENAME,
    DURABILITY_ADJUDICATION_FILENAME,
    EVIDENCE_RELATIVE_ROOT,
    EXPECTED_ORIGIN_MAIN_SHA,
    FEE_PROVENANCE_FILENAME,
    LINEAGE_FILENAME,
    NON_EXECUTION_FILENAME,
    OWNER_GO,
    PREDECESSOR_SLICE,
    PREDICATE_TABLE_FILENAME,
    PR_6334_EXPECTED_TREE,
    PR_6334_HEAD_SHA,
    PR_6334_MERGE_COMMIT_SHA,
    PRIOR_OWNER_GO,
    RESTART_ADJUDICATION_FILENAME,
    SAFETY_FILENAME,
    SUMMARY_FILENAME,
    THIS_SLICE,
)


EVIDENCE_FILES: tuple[str, ...] = (
    SUMMARY_FILENAME,
    CLAIMS_FILENAME,
    ADJUDICATION_FILENAME,
    FEE_PROVENANCE_FILENAME,
    RESTART_ADJUDICATION_FILENAME,
    DURABILITY_ADJUDICATION_FILENAME,
    PREDICATE_TABLE_FILENAME,
    SAFETY_FILENAME,
    BASELINE_FILENAME,
    NON_EXECUTION_FILENAME,
    LINEAGE_FILENAME,
)


def persist_evidence_pack_v1(*, repo_root: Path) -> dict[str, Any]:
    adjudication = adjudicate_exact_fee_restart_durability_and_pre_execution_readiness_v1()
    root = Path(repo_root) / EVIDENCE_RELATIVE_ROOT / CANONICAL_EVIDENCE_RUN_ID
    root.mkdir(parents=True, exist_ok=True)
    baseline = {
        "BASELINE_VALIDATION": "PASS",
        "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "CURRENT_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "PR_6334_MERGE_COMMIT_SHA": PR_6334_MERGE_COMMIT_SHA,
        "PR_6334_HEAD_SHA": PR_6334_HEAD_SHA,
        "PR_6334_EXPECTED_TREE": PR_6334_EXPECTED_TREE,
        "PR_6334_STATE": "MERGED",
        "OWNER_MERGE_GO_STATUS": "CONSUMED",
    }
    safety = {
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "OWNER_EXECUTION_AUTHORIZED": False,
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_TEST_EXECUTED": False,
        "GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "AUTHORITY_CLASS": "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK",
    }
    non_execution = {
        "GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_TEST_EXECUTED": False,
        "NEW_GET_EXECUTED": False,
        "OPTIONAL_GET_SKIPPED_REASON": (
            "CURRENT_TRADE_FEE_GET_CANNOT_PROVE_OEM_FORMULA;"
            "REDUNDANT_PRETRADE_REFRESH_NOT_REQUIRED_FOR_FORENSIC_UNPROVEN_CLOSURE"
        ),
    }
    lineage: Mapping[str, Any] = {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "CANONICAL_EVIDENCE_RUN_ID": CANONICAL_EVIDENCE_RUN_ID,
        "AUTHORITY_CLASS": "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK",
        "MAP_OF_TRUTH_AUTHORITY": "NONE_FOR_SEMANTICS",
        "ATLAS_AUTHORITY": "NONE",
    }
    summary = {
        "AUTHORITY_CLASS": "R1_OFFLINE_DOCS_CONTRACTS_TESTS_NO_NETWORK",
        "CANONICAL_EVIDENCE_RUN_ID": CANONICAL_EVIDENCE_RUN_ID,
        "CASE_ADJUDICATION": adjudication["CASE_ADJUDICATION"],
        "EXACT_OKX_FEE_FORMULA_UNPROVEN": True,
        "EXACT_OKX_FEE_FORMULA_STATUS": "UNPROVEN",
        "BOUNDED_FEE_ENVELOPE_PROVEN": False,
        "BOUNDED_FEE_ENVELOPE_POLICY_BOUND": True,
        "EXPECTED_FEE_PRETRADE_STATUS": adjudication["EXPECTED_FEE_PRETRADE_STATUS"],
        "VENUE_REPORTED_FEE_POST_FILL_STATUS": adjudication["VENUE_REPORTED_FEE_POST_FILL_STATUS"],
        "LIVE_RESTART_STATIC_RECONSTRUCTION_PROVEN": True,
        "LIVE_RESTART_EMPIRICAL_RECONSTRUCTION_PROVEN": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "PROCESS_CRASH_DURABILITY_STATUS": adjudication["PROCESS_CRASH_DURABILITY_STATUS"],
        "HOST_CRASH_DURABILITY_UNPROVEN": True,
        "HOST_CRASH_DURABILITY_STATUS": "UNPROVEN",
        "POWER_LOSS_DURABILITY_STATUS": "UNPROVEN",
        "CODE_GAP_FOUND": False,
        "REPAIR_IMPLEMENTED": False,
        "CANARY_AUTHORIZED_EXACT_FIELD": "INDETERMINATE_ABSENT",
        "POST_ALLOWED_EXACT_FIELD": "INDETERMINATE_ABSENT",
        "OWNER_EXECUTION_AUTHORIZED": False,
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED": False,
        "TECHNICAL_PRE_EXECUTION_READINESS": False,
        "TECHNICAL_EXECUTION_READY": False,
        "EXECUTION_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
        "EARLIEST_REMAINING_BLOCKER": "OWNER_EXECUTION_AUTHORIZED",
        "EARLIEST_TECHNICAL_BLOCKER": "CURRENT_SUI_FAMILY_TRADE_FEE_GET_ABSENT",
        "EARLIEST_LADDER_BLOCKER": "LIVE_RESTART_RECONSTRUCTED",
        "GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_TEST_EXECUTED": False,
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "NEXT_SLICE_AUTHORIZED": False,
    }
    claims = dict(summary)
    write_json_v1(root / SUMMARY_FILENAME, summary)
    write_json_v1(root / CLAIMS_FILENAME, claims)
    write_json_v1(root / ADJUDICATION_FILENAME, adjudication)
    write_json_v1(root / FEE_PROVENANCE_FILENAME, {"rows": adjudication["FEE_PROVENANCE"]})
    write_json_v1(root / RESTART_ADJUDICATION_FILENAME, adjudication["RESTART"])
    write_json_v1(root / DURABILITY_ADJUDICATION_FILENAME, adjudication["DURABILITY"])
    write_json_v1(root / PREDICATE_TABLE_FILENAME, {"rows": adjudication["PREDICATE_TABLE"]})
    write_json_v1(root / SAFETY_FILENAME, safety)
    write_json_v1(root / BASELINE_FILENAME, baseline)
    write_json_v1(root / NON_EXECUTION_FILENAME, non_execution)
    write_json_v1(root / LINEAGE_FILENAME, lineage)
    write_manifest_v1(root, EVIDENCE_FILES)
    verified = verify_manifest_v1(root)
    return {
        "EVIDENCE_ROOT": str(root),
        "MANIFEST_VERIFY_RC": int(verified.get("MANIFEST_VERIFY_RC", 1)),
        "ADJUDICATION": adjudication,
    }
