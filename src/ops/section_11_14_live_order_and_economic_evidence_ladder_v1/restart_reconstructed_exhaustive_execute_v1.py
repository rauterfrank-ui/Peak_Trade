"""Execute the exhaustive offline LIVE_RESTART_RECONSTRUCTED census. No GET. No POST."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_v1 import (
    assert_no_secrets_in_payload_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_execute_v1 import (
    bind_restart_evidence_from_persisted_census_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_exhaustive_census_v1 import (
    census_exhaustive_live_restart_handoff_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_future_go_contract_v1 import (
    bind_future_live_restart_owner_go_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    LIVE_EVIDENCE_DIRNAME,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    evaluate_handoff_proof_bundle_v1,
)

EVIDENCE_DIRNAME = LIVE_EVIDENCE_DIRNAME


def _utc_now_compact_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def execute_live_restart_reconstructed_exhaustive_census_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or CANONICAL_EVIDENCE_RUN_ID or _utc_now_compact_v1())
    exhaustive = census_exhaustive_live_restart_handoff_v1(repo_root=Path(repo_root))
    assert_no_secrets_in_payload_v1(exhaustive)
    bound_evidence = bind_restart_evidence_from_persisted_census_v1(repo_root=Path(repo_root))
    adjudication = adjudicate_live_restart_reconstructed_v1(restart_evidence=bound_evidence)
    assert_no_secrets_in_payload_v1(adjudication)
    future_go = bind_future_live_restart_owner_go_contract_v1()
    validator_matrix = {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_RESTART_VALIDATOR_MATRIX_V1",
        "happy_path_not_persisted_as_live_claim": True,
        "missing_durable_state": evaluate_handoff_proof_bundle_v1(
            handoff=None,
            source_kind="GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS",
        ),
        "accounting_only": evaluate_handoff_proof_bundle_v1(
            handoff={"clOrdId": exhaustive["BOUND_CLORDID"], "pos": "1"},
            source_kind="GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS",
            source_path="evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "20260904T181817Z/GET_POSITIONS.raw.json",
            accounting_only=True,
        ),
    }
    assert_no_secrets_in_payload_v1(validator_matrix)
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    code_path = {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_RESTART_CODE_PATH_CENSUS_V1",
        "SECTION_11_14_LIVE_DURABLE_STATE_WRITER_EXISTS": exhaustive[
            "SECTION_11_14_LIVE_DURABLE_STATE_WRITER_EXISTS"
        ],
        "LIVE_CANARY_DURABLE_STATE_WRITER_EXISTS": exhaustive[
            "LIVE_CANARY_DURABLE_STATE_WRITER_EXISTS"
        ],
        "SECTION_11_14_DURABLE_STATE_WRITER_HITS": exhaustive[
            "SECTION_11_14_DURABLE_STATE_WRITER_HITS"
        ],
        "LIVE_CANARY_DURABLE_STATE_WRITER_HITS": exhaustive[
            "LIVE_CANARY_DURABLE_STATE_WRITER_HITS"
        ],
        "CODE_PATH_EXISTS": bool(
            exhaustive["SECTION_11_14_LIVE_DURABLE_STATE_WRITER_EXISTS"]
            or exhaustive["LIVE_CANARY_DURABLE_STATE_WRITER_EXISTS"]
        ),
        "HISTORICAL_LIVE_EXECUTION_PROVEN": False,
        "PRE_RESTART_HANDOFF_PROVEN": False,
        "RUNTIME_CHANGE_REQUIRES_SEPARATE_OWNER_SCOPE": True,
    }
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
        "CASE_ADJUDICATION": adjudication.get("CASE_ADJUDICATION"),
        "CASE_B_NOT_PROVEN_CONTRACT_CLOSED": True,
        "RESTART_PROOF_CONTRACT_STATUS": "BOUND_AND_EXHAUSTIVELY_CENSUSED",
        "RESTART_SEMANTICS_STATUS": adjudication.get("RESTART_SEMANTICS_STATUS"),
        "EARLIEST_MISSING_FACT": "DURABLE_LIVE_PRE_RESTART_HANDOFF",
        "DURABLE_STATE_CODE_PATH_EXISTS": code_path["CODE_PATH_EXISTS"],
        "DURABLE_STATE_HISTORICAL_EXECUTION_PROVEN": False,
        "PRE_RESTART_HANDOFF_REQUIRED": True,
        "PRE_RESTART_HANDOFF_PROVEN": False,
        "POST_RESTART_RECONSTRUCTION_PROVEN": False,
        "ACCOUNTING_EVIDENCE_USED_AS_RESTART_SUBSTITUTE": False,
        "RUNTIME_CHANGE_REQUIRES_SEPARATE_OWNER_SCOPE": True,
        "BOUND_ORDID": exhaustive["BOUND_ORDID"],
        "BOUND_CLORDID": exhaustive["BOUND_CLORDID"],
        "BOUND_INSTID": exhaustive["BOUND_INSTID"],
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "PUBLIC_GET_USED": False,
        "CREDENTIAL_USE": False,
        "RETRY_USED": False,
        "SECOND_SUBMIT_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "FUNDING_USED": False,
        "RESTART_EXECUTION": False,
        "RAW_EVIDENCE_MODIFIED": False,
        "SECRET_VALUES_INCLUDED": False,
        "LIVE_LADDER_PACK_COUNT": exhaustive["LIVE_LADDER_PACK_COUNT"],
        "DURABLE_STATE_TREE_COUNT": exhaustive["DURABLE_STATE_TREE_COUNT"],
        "BOUND_IDENTITY_HITS_IN_DURABLE_STATE": exhaustive["BOUND_IDENTITY_HITS_IN_DURABLE_STATE"],
        "FUTURE_OWNER_GO_REQUIRED": future_go["FUTURE_OWNER_GO_REQUIRED"],
        "FUTURE_MINIMUM_OPERATION": future_go["FUTURE_MINIMUM_OPERATION"],
        "restart_adjudication": adjudication,
        "exhaustive_census": exhaustive,
        "code_path_census": code_path,
        "future_owner_go_contract": future_go,
        "validator_matrix": validator_matrix,
    }
    assert_no_secrets_in_payload_v1(summary)
    pack = Path(repo_root) / "evidence" / "ops" / EVIDENCE_DIRNAME / pack_run_id
    return {
        "pack": str(pack),
        "summary": summary,
        "adjudication": adjudication,
        "census": exhaustive,
        "code_path_census": code_path,
        "future_owner_go_contract": future_go,
        "validator_matrix": validator_matrix,
        "raw_exchanges": [],
    }
