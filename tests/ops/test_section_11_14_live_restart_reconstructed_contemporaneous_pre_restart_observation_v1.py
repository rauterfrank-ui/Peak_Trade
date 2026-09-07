"""Contemporaneous pre-restart observability prove-or-refute tests."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_CONTEMPORANEOUS_OBSERVATION_OWNER_GO,
    HISTORICAL_CONTEMPORANEOUS_OBSERVATION_SHA,
    LIVE_RESTART_RECONSTRUCTED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_contemporaneous_pre_restart_observation_execute_v1 import (
    execute_live_restart_reconstructed_contemporaneous_pre_restart_observation_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_contemporaneous_pre_restart_observation_v1 import (
    COMPLETE_CAPTURE_SEAM,
    MINIMUM_SAFE_OBSERVATION_CLASS,
    OBSERVATION_CASE,
    OBSERVATION_STATUS,
    bind_contemporaneous_pre_restart_observability_adjudication_v1,
    bind_non_synthetic_observation_protocol_v1,
    bind_restart_boundary_for_contemporaneous_classification_v1,
    execute_minimum_safe_read_back_observation_v1,
    inventory_durable_write_point_and_provenance_v1,
    inventory_productive_pre_restart_capture_trigger_and_producer_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_consumer_bind_v1 import (
    consume_validated_handoff_for_restart_reconstruction_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_v1 import (
    RESULT_MISSING_HANDOFF,
    read_validated_durable_pre_restart_handoff_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_capture_trigger_and_producer_are_bound_but_not_runtime_joined() -> None:
    trigger = inventory_productive_pre_restart_capture_trigger_and_producer_v1()
    assert trigger["SELECTED_CAPTURE_TRIGGER"] == REQUIRED_CAPTURE_TRIGGER
    assert trigger["CAPTURE_TRIGGER_PRODUCTIVELY_BOUND"] is True
    assert trigger["CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME"] is False
    assert trigger["PRODUCTIVE_RUNTIME_CALLER_COUNT"] == 0
    assert trigger["AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT"] is False
    assert trigger["TEST_TMP_PATH_MAY_SATISFY_LIVE_FIELD"] is False


def test_durable_write_point_and_provenance_fields_are_named() -> None:
    write_point = inventory_durable_write_point_and_provenance_v1()
    assert write_point["RELATIVE_DURABLE_DIR"].endswith("pre_restart")
    assert write_point["HANDOFF_FILENAME"] == "restart_with_open_position_pre_restart_v1.json"
    assert "owner_id" in write_point["PROVENANCE_RECORD_FIELDS"]
    assert "provenance_class" in write_point["PROVENANCE_RECORD_FIELDS"]
    assert "captured_at_utc" in write_point["PROVENANCE_RECORD_FIELDS"]
    assert write_point["PRODUCTIVE_DURABLE_RECORD_PRESENT_IN_REPO"] is False
    assert write_point["ENVELOPE_PROVENANCE_IS_CONTRACT_NOT_EMPIRICAL_OBSERVATION"] is True


def test_restart_boundary_is_consumption_not_capture() -> None:
    boundary = bind_restart_boundary_for_contemporaneous_classification_v1()
    assert boundary["CAPTURE_MUST_PRECEDE_RESTART"] is True
    assert boundary["RESTART_IS_CONSUMPTION_NOT_CAPTURE"] is True
    assert boundary["RESTART_ALREADY_OCCURRED_IS_RETROACTIVE_SYNTHESIS"] is True
    assert boundary["POST_HOC_ASSEMBLY_ACROSS_MOMENTS_IS_RETROACTIVE_SYNTHESIS"] is True


def test_protocol_forbids_synthetic_or_retroactive_observation() -> None:
    protocol = bind_non_synthetic_observation_protocol_v1()
    assert protocol["RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED"] is False
    assert protocol["TIMESTAMP_BACKFILL_ALLOWED"] is False
    assert protocol["SYNTHETIC_PRE_RESTART_PROVENANCE_ALLOWED"] is False
    assert protocol["PRODUCTIVE_WRITE_AUTHORIZED"] is False
    assert protocol["MINIMUM_SAFE_OBSERVATION_CLASS"] == MINIMUM_SAFE_OBSERVATION_CLASS
    assert protocol["TEST_ROUNDTRIP_IS_NOT_CONTEMPORANEOUS_OBSERVATION"] is True


def test_repo_root_read_back_is_missing_handoff_and_consumer_rejects() -> None:
    read_back = execute_minimum_safe_read_back_observation_v1(storage_root=REPO_ROOT)
    assert read_back["PRODUCTIVE_CAPTURE_WRITE_EXECUTED"] is False
    assert read_back["READ_BACK_EXECUTED"] is True
    assert read_back["READER_RESULT"] == RESULT_MISSING_HANDOFF
    assert read_back["CONSUMER_ACCEPTED"] is False
    reader = read_validated_durable_pre_restart_handoff_v1(storage_root=REPO_ROOT)
    consumed = consume_validated_handoff_for_restart_reconstruction_v1(reader_result=reader)
    assert reader["RESULT"] == RESULT_MISSING_HANDOFF
    assert consumed["LIVE_RESTART_RECONSTRUCTED"] is False
    assert consumed["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is False


def test_observability_adjudication_refutes_without_promoting_restart() -> None:
    read_back = execute_minimum_safe_read_back_observation_v1(storage_root=REPO_ROOT)
    adjudication = bind_contemporaneous_pre_restart_observability_adjudication_v1(
        read_back=read_back
    )
    assert adjudication["OBSERVATION_STATUS"] == OBSERVATION_STATUS
    assert adjudication["CASE_ADJUDICATION"] == OBSERVATION_CASE
    assert adjudication["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is False
    assert adjudication["COMPLETE_CAPTURE_SEAM"] == COMPLETE_CAPTURE_SEAM
    assert (
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"
        in adjudication["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"]
    )
    assert adjudication["LIVE_RESTART_RECONSTRUCTED"] is False
    assert LIVE_RESTART_RECONSTRUCTED is False
    assert adjudication["restart_adjudication"]["LIVE_RESTART_RECONSTRUCTED"] is False


def test_execute_is_offline_and_closes_as_refuted() -> None:
    result = execute_live_restart_reconstructed_contemporaneous_pre_restart_observation_v1(
        owner_go=HISTORICAL_CONTEMPORANEOUS_OBSERVATION_OWNER_GO,
        origin_main_sha=HISTORICAL_CONTEMPORANEOUS_OBSERVATION_SHA,
        repo_root=REPO_ROOT,
        run_id="20260907T054500Z-test",
    )
    summary = result["summary"]
    assert summary["OBSERVATION_STATUS"] == "CLOSED_REFUTED"
    assert summary["READ_BACK_RESULT"] == RESULT_MISSING_HANDOFF
    assert summary["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert summary["LIVE_RESTART_RECONSTRUCTED"] is False
    assert summary["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is False
    assert summary["AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT"] is False
    assert summary["PRODUCTIVE_CAPTURE_WRITE_EXECUTED"] is False
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["WIRE_SEND"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["IMPLEMENTATION_AUTHORIZED"] is False
    assert result["raw_exchanges"] == []
    assert result["adjudication"]["LIVE_RESTART_RECONSTRUCTED"] is False
    assert result["read_back"]["VENUE_GET_FALLBACK"] is False
    assert result["read_back"]["EVIDENCE_PACK_FALLBACK"] is False
