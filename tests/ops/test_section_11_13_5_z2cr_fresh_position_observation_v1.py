"""Offline §11.13.5.Z2CR observation helpers. No network."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.execution_prerequisite_08_cluster_contract_v1 import (
    REASON_DEPENDENT_BLOCKED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    OWNER_GO,
    LiveCanaryPrerequisite08FreshObservationError,
    adjudicate_prerequisite_08_window_v1,
    evaluate_freshness_at_adjudication_v1,
    run_authorized_fresh_position_observation_v1,
    sanitize_position_row_v1,
    sanitize_positions_payload_v1,
)

CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _deny(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("network must not be used")

    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1.urlopen",
        _deny,
    )


def test_sanitize_redacts_uid_and_keeps_pos() -> None:
    row = sanitize_position_row_v1(
        {"instId": CURRENT_SUI, "pos": "1", "uid": "secret-uid", "unexpected": "drop"}
    )
    assert row["instId"] == CURRENT_SUI
    assert row["pos"] == "1"
    assert row["uid"] == "<REDACTED>"
    assert "unexpected" not in row


def test_empty_payload_does_not_prove_zero_or_08() -> None:
    result = adjudicate_prerequisite_08_window_v1(
        positions_payload={"code": "0", "data": [], "msg": ""}
    )
    assert result["TARGET_ROW_OBSERVED"] is False
    assert result["TARGET_POSITION_STATE"] == "NOT_OBSERVED"
    assert result["EXECUTION_PREREQUISITE_08_STATUS"] == (
        "UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW"
    )
    assert result["EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN"] is False
    assert result["EXECUTION_PREREQUISITE_09_STATUS"] == REASON_DEPENDENT_BLOCKED
    assert result["TARGET_POSITION_QTY_NUMERIC"] == "UNRESOLVED"
    assert result["TARGET_POSITION_QTY_UNIT"] == "UNPROVEN"
    assert result["CLASS_D_CONSUMED"] is False
    assert result["cluster_offline_08_proven_token"] is False


def test_zero_row_is_zero_not_nonzero() -> None:
    result = adjudicate_prerequisite_08_window_v1(
        positions_payload={"code": "0", "data": [{"instId": CURRENT_SUI, "pos": "0"}]}
    )
    assert result["TARGET_ROW_OBSERVED"] is True
    assert result["TARGET_POSITION_STATE"] == "ZERO"
    assert result["EXECUTION_PREREQUISITE_08_STATUS"] == "UNRESOLVED_TARGET_ZERO_THIS_PAYLOAD"
    assert result["EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN"] is False
    assert result["TARGET_POSITION_QTY_NUMERIC"] == "PASS"


def test_nonzero_fixture_is_not_productive_08_proof_token() -> None:
    result = adjudicate_prerequisite_08_window_v1(
        positions_payload={"code": "0", "data": [{"instId": CURRENT_SUI, "pos": "1"}]}
    )
    assert result["TARGET_POSITION_STATE"] == "NONZERO"
    assert result["EXECUTION_PREREQUISITE_08_STATUS"] == (
        "PASS_TARGET_POSITION_NONZERO_OBSERVED_THIS_WINDOW"
    )
    assert result["cluster_offline_08_proven_token"] is False
    assert result["OFFLINE_CLUSTER_PROVEN_TOKEN_IS_NOT_PRODUCTIVE_08_PROOF"] is True
    assert result["CLASS_D_CONSUMED"] is False
    assert result["EXECUTION_READY"] is False


def test_freshness_missing_is_not_evaluable() -> None:
    verdict = evaluate_freshness_at_adjudication_v1(
        response_received_monotonic_ms=None,
        adjudication_monotonic_ms=1,
    )
    assert verdict["FRESHNESS_STATUS"] == "NOT_EVALUABLE"


def test_freshness_equal_5000_is_pass() -> None:
    verdict = evaluate_freshness_at_adjudication_v1(
        response_received_monotonic_ms=10,
        adjudication_monotonic_ms=5010,
    )
    assert verdict["FRESHNESS_STATUS"] == "PASS"
    assert verdict["OBSERVATION_AGE_AT_ADJUDICATION_MS"] == 5000


def test_freshness_above_5000_is_fail() -> None:
    verdict = evaluate_freshness_at_adjudication_v1(
        response_received_monotonic_ms=10,
        adjudication_monotonic_ms=5011,
    )
    assert verdict["FRESHNESS_STATUS"] == "FAIL"


def test_wrong_owner_go_fails_closed_without_network(tmp_path: Path) -> None:
    with pytest.raises(LiveCanaryPrerequisite08FreshObservationError, match="OWNER_GO_MISMATCH"):
        run_authorized_fresh_position_observation_v1(
            owner_go="WRONG",
            origin_main_sha="abc",
            vault_file=tmp_path / "missing.json",
            evidence_root=tmp_path,
        )


def test_sanitize_payload_empty_envelope() -> None:
    sanitized = sanitize_positions_payload_v1({"code": "0", "data": [], "msg": ""})
    assert sanitized == {"code": "0", "data": [], "msg": ""}


def test_owner_go_token_is_exact() -> None:
    assert OWNER_GO == (
        "PEAK_TRADE_OWNER_GO_SECTION_11_13_5_PREREQUISITE_08_FRESH_POSITION_OBSERVATION_CLUSTER_V1"
    )
