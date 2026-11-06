"""LIVE_RESTART_RECONSTRUCTED producer, census, and fail-closed tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_RESTART_RECONSTRUCTED_OWNER_GO,
    HISTORICAL_RESTART_RECONSTRUCTED_RUN_ID,
    HISTORICAL_RESTART_RECONSTRUCTED_SHA,
    LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    CENSUS_SOURCE_KIND,
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_execute_v1 import (
    census_live_restart_handoff_v1,
    execute_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
    TESTNET_RESTART_PROVEN_INSTID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _restart_evidence(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_kind": CENSUS_SOURCE_KIND,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "RESTART_EXECUTION": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "durable_handoff": None,
        "census": {
            "DURABLE_PRE_RESTART_HANDOFF_PRESENT": False,
            "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH": False,
            "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
        },
    }
    if "census" in overrides and isinstance(overrides["census"], dict):
        census = dict(payload["census"])  # type: ignore[arg-type]
        census.update(overrides.pop("census"))  # type: ignore[arg-type]
        payload["census"] = census
    if "durable_handoff" in overrides and isinstance(overrides["durable_handoff"], dict):
        payload["durable_handoff"] = dict(overrides.pop("durable_handoff"))  # type: ignore[arg-type]
    payload.update(overrides)
    return payload


def test_persisted_census_fails_closed_without_durable_handoff() -> None:
    proof = adjudicate_live_restart_reconstructed_v1(restart_evidence=_restart_evidence())
    assert proof["LIVE_RESTART_RECONSTRUCTED"] is False
    assert proof["LIVE_AUTONOMOUS_RECOVERY_OBSERVED"] is False
    assert proof["SECTION_11_14_COMPLETE"] is False
    assert (
        proof["CASE_ADJUDICATION"]
        == "CASE_LIVE_RESTART_RECONSTRUCTED_FAIL_CLOSED_MISSING_DURABLE_HANDOFF"
    )
    assert proof["UNRESOLVED_REASON"] == "DURABLE_LIVE_PRE_RESTART_HANDOFF_ABSENT"
    assert proof["EARLIEST_MISSING_FACT"] == "DURABLE_LIVE_PRE_RESTART_HANDOFF"
    assert proof["GET_PERFORMED"] is False
    assert proof["POST_USED"] is False
    assert proof["RESTART_EXECUTION"] is False
    assert proof["ACCOUNTING_CLOSURE_IS_NOT_RESTART"] is True
    assert "durable pre-restart handoff" in LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION
    assert "accounting closure" in LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION


def test_accounting_path_is_not_restart_handoff() -> None:
    census = census_live_restart_handoff_v1(repo_root=REPO_ROOT)
    assert census["DURABLE_PRE_RESTART_HANDOFF_PRESENT"] is False
    assert census["durable_handoff_paths"] == []
    assert census["fill_raw_exists"] is True
    assert census["position_raw_exists"] is True
    assert census["accounting_artifacts_are_not_restart_handoff"] is True
    assert census["testnet_restart_instId"] == TESTNET_RESTART_PROVEN_INSTID
    assert census["testnet_restart_instId"] != BOUND_INSTID
    assert census["testnet_restart_is_not_this_field"] is True


def test_injected_true_field_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="RESTART_FIELD_PROMOTED_BY_INJECTED"):
        adjudicate_live_restart_reconstructed_v1(
            restart_evidence=_restart_evidence(LIVE_RESTART_RECONSTRUCTED=True)
        )


def test_recovery_promotion_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="RECOVERY_PROMOTED"):
        adjudicate_live_restart_reconstructed_v1(
            restart_evidence=_restart_evidence(LIVE_AUTONOMOUS_RECOVERY_OBSERVED=True)
        )


def test_post_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="POST_INVOKED"):
        adjudicate_live_restart_reconstructed_v1(restart_evidence=_restart_evidence(POST_USED=True))


def test_private_get_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="PRIVATE_GET_INVOKED"):
        adjudicate_live_restart_reconstructed_v1(
            restart_evidence=_restart_evidence(GET_PERFORMED=True)
        )


def test_restart_execution_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="RESTART_EXECUTION_INVOKED"):
        adjudicate_live_restart_reconstructed_v1(
            restart_evidence=_restart_evidence(RESTART_EXECUTION=True)
        )


def test_fixture_source_refused() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_LIVE_SOURCE"):
        adjudicate_live_restart_reconstructed_v1(
            restart_evidence=_restart_evidence(source_kind="FIXTURE")
        )


def test_synthetic_handoff_on_census_source_cannot_promote() -> None:
    proof = adjudicate_live_restart_reconstructed_v1(
        restart_evidence=_restart_evidence(
            durable_handoff={
                "clOrdId": BOUND_CLORDID,
                "ordId": BOUND_ORDID,
                "instId": BOUND_INSTID,
                "posSide": "net",
                "pos": "1",
            },
            census={
                "DURABLE_PRE_RESTART_HANDOFF_PRESENT": True,
                "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH": True,
                "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
            },
        )
    )
    assert proof["LIVE_RESTART_RECONSTRUCTED"] is False
    assert proof["adjudicated_value"] is False
    assert proof["RESTART_SOURCE_KIND"] == CENSUS_SOURCE_KIND
    assert ADMISSIBLE_SOURCE_KIND != CENSUS_SOURCE_KIND


def test_execute_censuses_persisted_evidence_without_get() -> None:
    result = execute_live_restart_reconstructed_v1(
        owner_go=HISTORICAL_RESTART_RECONSTRUCTED_OWNER_GO,
        origin_main_sha=HISTORICAL_RESTART_RECONSTRUCTED_SHA,
        repo_root=REPO_ROOT,
        run_id=HISTORICAL_RESTART_RECONSTRUCTED_RUN_ID,
    )
    adjudication = result["adjudication"]
    summary = result["summary"]
    census = result["census"]
    assert adjudication["LIVE_RESTART_RECONSTRUCTED"] is False
    assert adjudication["LIVE_AUTONOMOUS_RECOVERY_OBSERVED"] is False
    assert summary["GET_PERFORMED"] is False
    assert summary["CREDENTIAL_USE"] is False
    assert summary["POST_USED"] is False
    assert summary["RESTART_EXECUTION"] is False
    assert summary["RAW_EVIDENCE_MODIFIED"] is False
    assert result["raw_exchanges"] == []
    assert census["DURABLE_PRE_RESTART_HANDOFF_PRESENT"] is False
    assert census["durable_handoff_paths"] == []
