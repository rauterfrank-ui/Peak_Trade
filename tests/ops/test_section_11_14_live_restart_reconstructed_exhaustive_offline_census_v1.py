"""Exhaustive offline LIVE_RESTART_RECONSTRUCTED census and validator tests."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_exhaustive_census_v1 import (
    census_exhaustive_live_restart_handoff_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_exhaustive_execute_v1 import (
    execute_live_restart_reconstructed_exhaustive_census_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_future_go_contract_v1 import (
    bind_future_live_restart_owner_go_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    evaluate_handoff_proof_bundle_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _complete_handoff() -> dict[str, str]:
    return {
        "clOrdId": BOUND_CLORDID,
        "ordId": BOUND_ORDID,
        "instId": BOUND_INSTID,
        "posSide": "net",
        "pos": "1",
        "captured_at_utc": "2026-09-04T16:00:00Z",
    }


def test_exhaustive_census_finds_no_bound_live_durable_handoff() -> None:
    census = census_exhaustive_live_restart_handoff_v1(repo_root=REPO_ROOT)
    assert census["DURABLE_PRE_RESTART_HANDOFF_PRESENT"] is False
    assert census["BOUND_IDENTITY_HITS_IN_DURABLE_STATE"] == []
    assert census["LIVE_LADDER_DURABLE_STATE_PRESENT"] is False
    assert census["SECTION_11_14_LIVE_DURABLE_STATE_WRITER_EXISTS"] is False
    assert census["LIVE_CANARY_DURABLE_STATE_WRITER_EXISTS"] is False
    assert census["LIVE_LADDER_PACK_COUNT"] >= 13
    assert census["TESTNET_OR_FIXTURE_DURABLE_STATE_EXISTS"] is True
    assert census["EARLIEST_MISSING_FACT"] == "DURABLE_LIVE_PRE_RESTART_HANDOFF"


def test_happy_path_complete_handoff_promotes_only_on_admissible_source() -> None:
    proof = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={
            "source_kind": ADMISSIBLE_SOURCE_KIND,
            "POST_USED": False,
            "GET_PERFORMED": False,
            "PRIVATE_GET_USED": False,
            "CANCEL_USED": False,
            "AMEND_USED": False,
            "FLATTEN_EXECUTE_USED": False,
            "RESTART_EXECUTION": False,
            "LIVE_RESTART_RECONSTRUCTED": False,
            "durable_handoff": _complete_handoff(),
            "census": {
                "DURABLE_PRE_RESTART_HANDOFF_PRESENT": True,
                "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH": True,
                "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
            },
        }
    )
    assert proof["LIVE_RESTART_RECONSTRUCTED"] is True
    assert proof["LIVE_AUTONOMOUS_RECOVERY_OBSERVED"] is False
    assert proof["SECTION_11_14_COMPLETE"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_RESTART_RECONSTRUCTED_RECOVERY_INELIGIBLE"


def test_identity_mismatch_fails_closed() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff={**_complete_handoff(), "clOrdId": "wrong-id"},
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="durable_state/pre_restart.json",
    )
    assert result["claim_value"] is False
    assert result["REASON"] == "IDENTITY_MISMATCH_OR_STALE"


def test_wrong_run_identity_fails_closed() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff={**_complete_handoff(), "ordId": "0000000000000000000"},
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="durable_state/pre_restart.json",
    )
    assert result["claim_value"] is False
    assert result["identity"]["STALE_OR_IDENTITY_MISMATCH"] is True


def test_missing_durable_state_fails_closed() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff=None,
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="durable_state/pre_restart.json",
    )
    assert result["claim_value"] is False
    assert result["REASON"] == "MISSING_DURABLE_STATE"


def test_corrupt_pos_fails_closed() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff={**_complete_handoff(), "pos": "not-a-decimal"},
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="durable_state/pre_restart.json",
    )
    assert result["claim_value"] is False
    assert result["REASON"] == "CORRUPT_HANDOFF_POS"


def test_stale_zero_pos_is_silent_reinitialization() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff={**_complete_handoff(), "pos": "0.0"},
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="durable_state/pre_restart.json",
    )
    assert result["claim_value"] is False
    assert result["REASON"] == "SILENT_REINITIALIZATION"


def test_temporal_inversion_post_restart_only_fails_closed() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff={**_complete_handoff(), "captured_at_utc": "2026-09-04T18:00:00Z"},
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="durable_state/pre_restart.json",
        restart_at_utc="2026-09-04T17:00:00Z",
    )
    assert result["claim_value"] is False
    assert result["REASON"] == "TEMPORAL_INVERSION_POST_RESTART_ONLY"


def test_accounting_only_evidence_fails_closed() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_complete_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path=(
            "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "20260904T181817Z/GET_POSITIONS.raw.json"
        ),
        accounting_only=True,
    )
    assert result["claim_value"] is False
    assert result["REASON"] == "ACCOUNTING_ONLY_IS_NOT_RESTART"


def test_future_owner_go_contract_requires_persist_first_not_restart() -> None:
    contract = bind_future_live_restart_owner_go_contract_v1()
    assert contract["FRESH_PROCESS_RESTART_REQUIRED_FOR_THIS_FIELD"] is False
    assert contract["FRESH_PROCESS_RESTART_INSUFFICIENT_WITHOUT_HANDOFF"] is True
    assert contract["RUNTIME_CHANGE_REQUIRES_SEPARATE_OWNER_SCOPE"] is True
    assert contract["EARLIEST_MISSING_FACT"] == "DURABLE_LIVE_PRE_RESTART_HANDOFF"
    assert contract["FUTURE_MINIMUM_OPERATION"] == (
        "PERSIST_IDENTITY_BOUND_PEAK_TRADE_DURABLE_PRE_RESTART_HANDOFF"
    )


def test_exhaustive_execute_fails_closed_without_get_or_restart() -> None:
    result = execute_live_restart_reconstructed_exhaustive_census_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        run_id="20260904T195000Z",
    )
    summary = result["summary"]
    adjudication = result["adjudication"]
    census = result["census"]
    assert adjudication["LIVE_RESTART_RECONSTRUCTED"] is False
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["RESTART_EXECUTION"] is False
    assert summary["ACCOUNTING_EVIDENCE_USED_AS_RESTART_SUBSTITUTE"] is False
    assert summary["RUNTIME_CHANGE_REQUIRES_SEPARATE_OWNER_SCOPE"] is True
    assert census["BOUND_IDENTITY_HITS_IN_DURABLE_STATE"] == []
    assert result["raw_exchanges"] == []
