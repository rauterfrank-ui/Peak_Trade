"""Complete capture-seam provenance and no-backfill-contract tests.

All inputs are TEST_FIXTURE. These tests do not execute productive Live
capture, submit, wire send, or restart.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_caller_v1 import (
    PRODUCTIVE_HOOK_CALLER,
    call_pre_restart_handoff_capture_after_bound_fill_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_hook_v1 import (
    run_capture_hook_after_bound_fill_before_restart_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.runner_v1 import (
    run_live_order_pre_restart_handoff_capture_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    OWNER_GO,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
    THIS_SLICE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_capture_seam_required_field_provenance_and_no_backfill_contract_execute_v1 import (
    execute_live_handoff_complete_capture_seam_required_field_provenance_and_no_backfill_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_capture_seam_required_field_provenance_and_no_backfill_contract_v1 import (
    AUTHORITATIVE_CAPTURE_PRODUCER,
    CAPTURE_HOOK,
    CAPTURE_OWNER,
    CASE_ADJUDICATION,
    COMPLETE_CAPTURE_SEAM,
    NO_BACKFILL_CONTRACT_PROVEN,
    PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL,
    REQUIRED_FIELD_PROVENANCE_COMPLETE,
    bind_complete_capture_seam_field_table_v1,
    bind_complete_capture_seam_required_field_provenance_and_no_backfill_contract_v1,
    classify_legacy_codec_document_class_synthesis_v1,
    prove_offline_capture_roundtrip_v1,
    prove_writer_rejects_wall_clock_substitution_v1,
    read_contemporaneous_valid_handoff_v1,
    refuse_incomplete_record_plus_later_runtime_state_v1,
    validate_contemporaneous_no_backfill_persisted_record_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_v1 import (
    INPUT_CLASS_TEST_FIXTURE,
    accept_complete_contemporaneous_capture_inputs_v1,
    build_test_fixture_field_provenance_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    CANONICAL_BOUND_FILL_KIND,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    durable_handoff_path_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
    HANDOFF_DOCUMENT_CLASS,
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    HANDOFF_SCHEMA_VERSION,
    POS_UNIT,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_FIXTURE_IDENTITY = {
    "clOrdId": "pttestfixtureclordid000000001",
    "ordId": "1110002223334445556",
    "instId": "ETH-USD_UM_XPERP-FIXTURE",
    "posSide": "net",
    "fillSz": "3",
}
LIFECYCLE_ID = "test-fixture-complete-capture-seam-no-backfill-lifecycle-v1"
ATTEMPT_IDENTITY = "test-fixture-attempt-no-backfill-v1"
BOUND_FILL_PROVEN_AT = "2026-09-07T14:00:00Z"
CAPTURE_STARTED_AT = "2026-09-07T14:00:01Z"


def _provenance() -> dict[str, object]:
    return build_test_fixture_field_provenance_v1(
        bound_fill_identity=TEST_FIXTURE_IDENTITY,
        lifecycle_id=LIFECYCLE_ID,
    )


def _accept_kwargs(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "input_class": INPUT_CLASS_TEST_FIXTURE,
        "bound_fill_proven": True,
        "bound_fill_kind": CANONICAL_BOUND_FILL_KIND,
        "bound_fill_identity": dict(TEST_FIXTURE_IDENTITY),
        "peak_trade_owned_resulting_current_position_qty": "3",
        "source_kind": ADMISSIBLE_POS_SOURCE_KIND,
        "unit": POS_UNIT,
        "restart_already_occurred": False,
        "restart_not_yet_occurred_proven": True,
        "bound_fill_proven_at": BOUND_FILL_PROVEN_AT,
        "capture_started_at": CAPTURE_STARTED_AT,
        "attempt_identity": ATTEMPT_IDENTITY,
        "lifecycle_id": LIFECYCLE_ID,
        "field_provenance": _provenance(),
    }
    payload.update(overrides)
    return payload


def _caller_kwargs(tmp_path: Path, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "storage_root": tmp_path,
        "bound_fill_proven": True,
        "bound_fill_kind": CANONICAL_BOUND_FILL_KIND,
        "bound_fill_identity": dict(TEST_FIXTURE_IDENTITY),
        "peak_trade_owned_resulting_current_position_qty": "3",
        "source_kind": ADMISSIBLE_POS_SOURCE_KIND,
        "unit": POS_UNIT,
        "restart_already_occurred": False,
        "restart_not_yet_occurred_proven": True,
        "bound_fill_proven_at": BOUND_FILL_PROVEN_AT,
        "capture_started_at": CAPTURE_STARTED_AT,
        "attempt_identity": ATTEMPT_IDENTITY,
        "input_class": INPUT_CLASS_TEST_FIXTURE,
        "lifecycle_id": LIFECYCLE_ID,
        "lifecycle_event": REQUIRED_CAPTURE_TRIGGER,
        "field_provenance": _provenance(),
    }
    payload.update(overrides)
    return payload


def test_current_slice_and_owner_go_match_this_workpackage() -> None:
    assert THIS_SLICE == (
        "11.14.LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_REQUIRED_FIELD_PROVENANCE_AND_NO_BACKFILL_CONTRACT"
    )
    assert OWNER_GO.endswith(
        "COMPLETE_CAPTURE_SEAM_REQUIRED_FIELD_PROVENANCE_AND_NO_BACKFILL_CONTRACT_V1"
    )
    assert EXPECTED_ORIGIN_MAIN_SHA == "eafb5f29e36e69f6af996d7eb9f276d0cec195f0"
    assert COMPLETE_CAPTURE_SEAM == "PROVEN"
    assert PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL is True
    assert REQUIRED_FIELD_PROVENANCE_COMPLETE is True
    assert NO_BACKFILL_CONTRACT_PROVEN is True
    assert LIVE_ENABLED is False
    assert POST_ALLOWED is False
    assert SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is False
    assert LIVE_RESTART_RECONSTRUCTED is False


def test_required_field_table_covers_all_five_fields_with_no_backfill() -> None:
    table = bind_complete_capture_seam_field_table_v1()
    assert table["HANDOFF_REQUIRED_FIELD_COUNT"] == 5
    assert table["REQUIRED_FIELD_PROVENANCE_COMPLETE"] is True
    assert table["NO_BACKFILL_CONTRACT_PROVEN"] is True
    names = [row["FIELD"] for row in table["rows"]]
    assert names == list(REQUIRED_HANDOFF_FIELDS)
    for row in table["rows"]:
        assert row["BACKFILL_ALLOWED"] is False
        assert row["MISSING_BEHAVIOR"] == "HARD_FAIL"
        assert row["NULL_ALLOWED"] is False
        assert row["DEFAULT_EXISTS"] is False
        assert row["DEFAULT_SEMANTICALLY_ALLOWED"] is False
        assert row["READER_REQUIRES_FIELD"] is True
        assert row["READER_WRITER_SEMANTICS_IDENTICAL"] is True
        assert row["NAMING_SIMILARITY_IS_NOT_IDENTITY"] is True
        assert row["PROVENANCE_STATUS"] == "PROVEN_CONTEMPORANEOUS_NO_BACKFILL_OFFLINE"


def test_complete_authoritative_bound_fill_constructs_in_memory_record() -> None:
    accepted = accept_complete_contemporaneous_capture_inputs_v1(**_accept_kwargs())
    assert accepted["ALLOWED"] is True
    assert accepted["TEST_FIXTURE"] is True
    assert accepted["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    for name in REQUIRED_HANDOFF_FIELDS:
        assert str(accepted["record"][name]).strip() != ""
    assert accepted["record"]["pos"] == "3"
    assert accepted["record"]["BACKFILL_ALLOWED"] is False
    assert accepted["record"]["lifecycle_id"] == LIFECYCLE_ID
    assert "field_provenance" in accepted["record"]


def test_productive_caller_hook_owner_and_persist_roundtrip(tmp_path: Path) -> None:
    proof = prove_offline_capture_roundtrip_v1(
        storage_root=tmp_path,
        bound_fill_identity=dict(TEST_FIXTURE_IDENTITY),
        peak_trade_owned_resulting_current_position_qty="3",
        bound_fill_proven_at=BOUND_FILL_PROVEN_AT,
        capture_started_at=CAPTURE_STARTED_AT,
        attempt_identity=ATTEMPT_IDENTITY,
        lifecycle_id=LIFECYCLE_ID,
        field_provenance=_provenance(),
    )
    assert proof["PASS"] is True
    assert proof["SNAPSHOT_IMMUTABLE_AFTER_BOUND_FILL_COPY"] is True
    assert proof["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    persisted = proof["persisted"]
    for name in REQUIRED_HANDOFF_FIELDS:
        assert persisted[name] == (TEST_FIXTURE_IDENTITY[name] if name != "pos" else "3")
    assert persisted["captured_at_utc"] == CAPTURE_STARTED_AT
    assert persisted["schema_version"] == HANDOFF_SCHEMA_VERSION
    caller = proof["caller_result"]
    assert caller["PRODUCTIVE_HOOK_CALLER"] == PRODUCTIVE_HOOK_CALLER
    assert caller["hook_result"]["PRODUCTIVE_CAPTURE_OWNER"] == PRODUCTIVE_CAPTURE_OWNER
    assert caller["hook_result"]["PRODUCTIVE_LIFECYCLE_HOOK"] == PRODUCTIVE_LIFECYCLE_HOOK


def test_each_required_field_missing_or_null_hard_fails() -> None:
    for name in REQUIRED_HANDOFF_FIELDS:
        provenance = _provenance()
        fields = dict(provenance["fields"])
        del fields[name]
        provenance["fields"] = fields
        with pytest.raises(
            Section1114OfflineSurfaceError, match="REQUIRED_FIELD_PROVENANCE_MISSING"
        ):
            accept_complete_contemporaneous_capture_inputs_v1(
                **_accept_kwargs(field_provenance=provenance)
            )
        provenance = _provenance()
        fields = dict(provenance["fields"])
        fields[name] = dict(fields[name])
        fields[name]["VALUE"] = None
        provenance["fields"] = fields
        with pytest.raises(Section1114OfflineSurfaceError, match="REQUIRED_FIELD_MISSING"):
            accept_complete_contemporaneous_capture_inputs_v1(
                **_accept_kwargs(field_provenance=provenance)
            )


def test_wrong_type_and_wrong_unit_hard_fail() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="POS_MALFORMED"):
        accept_complete_contemporaneous_capture_inputs_v1(
            **_accept_kwargs(peak_trade_owned_resulting_current_position_qty="not-a-decimal")
        )
    with pytest.raises(Section1114OfflineSurfaceError, match="WRONG_UNIT"):
        accept_complete_contemporaneous_capture_inputs_v1(**_accept_kwargs(unit="contracts"))
    with pytest.raises(Section1114OfflineSurfaceError, match="BOUND_FILL_KIND_REJECTED"):
        accept_complete_contemporaneous_capture_inputs_v1(
            **_accept_kwargs(bound_fill_kind="SIMULATED_FILL")
        )


def test_malformed_partial_and_unknown_schema_fail_closed(tmp_path: Path) -> None:
    prove_offline_capture_roundtrip_v1(
        storage_root=tmp_path,
        bound_fill_identity=dict(TEST_FIXTURE_IDENTITY),
        peak_trade_owned_resulting_current_position_qty="3",
        bound_fill_proven_at=BOUND_FILL_PROVEN_AT,
        capture_started_at=CAPTURE_STARTED_AT,
        attempt_identity=ATTEMPT_IDENTITY,
        lifecycle_id=LIFECYCLE_ID,
        field_provenance=_provenance(),
    )
    path = durable_handoff_path_v1(storage_root=tmp_path)
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(Section1114OfflineSurfaceError):
        read_contemporaneous_valid_handoff_v1(
            storage_root=tmp_path,
            expected_identity=TEST_FIXTURE_IDENTITY,
            expected_lifecycle=LIFECYCLE_ID,
            expected_captured_at_utc=CAPTURE_STARTED_AT,
            expected_attempt_identity=ATTEMPT_IDENTITY,
        )
    path.write_text('{"clOrdId":"x"', encoding="utf-8")
    with pytest.raises(Section1114OfflineSurfaceError):
        read_contemporaneous_valid_handoff_v1(
            storage_root=tmp_path,
            expected_identity=TEST_FIXTURE_IDENTITY,
            expected_lifecycle=LIFECYCLE_ID,
            expected_captured_at_utc=CAPTURE_STARTED_AT,
            expected_attempt_identity=ATTEMPT_IDENTITY,
        )
    prove_offline_capture_roundtrip_v1(
        storage_root=tmp_path / "schema",
        bound_fill_identity=dict(TEST_FIXTURE_IDENTITY),
        peak_trade_owned_resulting_current_position_qty="3",
        bound_fill_proven_at=BOUND_FILL_PROVEN_AT,
        capture_started_at=CAPTURE_STARTED_AT,
        attempt_identity=ATTEMPT_IDENTITY,
        lifecycle_id=LIFECYCLE_ID,
        field_provenance=_provenance(),
    )
    schema_path = durable_handoff_path_v1(storage_root=tmp_path / "schema")
    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    payload["schema_version"] = "section_11_14_live_durable_pre_restart_handoff.v2"
    schema_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(Section1114OfflineSurfaceError, match="SCHEMA_OR_VERSION_MISMATCH"):
        read_contemporaneous_valid_handoff_v1(
            storage_root=tmp_path / "schema",
            expected_identity=TEST_FIXTURE_IDENTITY,
            expected_lifecycle=LIFECYCLE_ID,
            expected_captured_at_utc=CAPTURE_STARTED_AT,
            expected_attempt_identity=ATTEMPT_IDENTITY,
        )


def test_illegal_backfill_stale_and_conflicting_identity_hard_fail(tmp_path: Path) -> None:
    provenance = _provenance()
    fields = dict(provenance["fields"])
    fields["pos"] = dict(fields["pos"])
    fields["pos"]["SOURCE_KIND"] = "RETROACTIVE_SYNTHESIS"
    provenance["fields"] = fields
    with pytest.raises(Section1114OfflineSurfaceError, match="FIELD_SOURCE_KIND_REJECTED"):
        run_live_order_pre_restart_handoff_capture_v1(
            **_caller_kwargs(tmp_path, field_provenance=provenance)
        )
    provenance = _provenance()
    fields = dict(provenance["fields"])
    fields["clOrdId"] = dict(fields["clOrdId"])
    fields["clOrdId"]["FRESHNESS"] = "BACKFILLED"
    provenance["fields"] = fields
    with pytest.raises(Section1114OfflineSurfaceError, match="STALE_OR_INVALID_PROVENANCE"):
        call_pre_restart_handoff_capture_after_bound_fill_v1(
            **_caller_kwargs(tmp_path, field_provenance=provenance)
        )
    with pytest.raises(Section1114OfflineSurfaceError, match="AMBIGUOUS_DUPLICATE_IDENTITY"):
        hook_kwargs = _caller_kwargs(tmp_path, extra_fields={"ordId": "9999999999999999999"})
        hook_kwargs.pop("lifecycle_event")
        run_capture_hook_after_bound_fill_before_restart_v1(**hook_kwargs)


def test_source_timestamp_missing_or_replaced_fail_closed(tmp_path: Path) -> None:
    prove_writer_rejects_wall_clock_substitution_v1(
        storage_root=tmp_path,
        bound_fill_identity=TEST_FIXTURE_IDENTITY,
        peak_trade_owned_resulting_current_position_qty="3",
        attempt_identity=ATTEMPT_IDENTITY,
    )
    with pytest.raises(Section1114OfflineSurfaceError, match="CAPTURE_WINDOW_TIMESTAMP_MISSING"):
        run_live_order_pre_restart_handoff_capture_v1(
            **_caller_kwargs(tmp_path, capture_started_at="")
        )
    proof = prove_offline_capture_roundtrip_v1(
        storage_root=tmp_path / "ts",
        bound_fill_identity=dict(TEST_FIXTURE_IDENTITY),
        peak_trade_owned_resulting_current_position_qty="3",
        bound_fill_proven_at=BOUND_FILL_PROVEN_AT,
        capture_started_at=CAPTURE_STARTED_AT,
        attempt_identity=ATTEMPT_IDENTITY,
        lifecycle_id=LIFECYCLE_ID,
        field_provenance=_provenance(),
    )
    with pytest.raises(Section1114OfflineSurfaceError, match="SOURCE_TIMESTAMP_REPLACED"):
        validate_contemporaneous_no_backfill_persisted_record_v1(
            record=proof["persisted"],
            expected_identity=TEST_FIXTURE_IDENTITY,
            expected_lifecycle=LIFECYCLE_ID,
            expected_captured_at_utc="2026-09-07T23:59:59Z",
        )


def test_no_backfill_incomplete_plus_later_runtime_is_not_valid(tmp_path: Path) -> None:
    historical = {
        "DOCUMENT_CLASS": HANDOFF_DOCUMENT_CLASS,
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "provenance_class": CONTEMPORANEOUS_PROVENANCE_CLASS,
        "clOrdId": TEST_FIXTURE_IDENTITY["clOrdId"],
        "ordId": TEST_FIXTURE_IDENTITY["ordId"],
        "instId": "",
        "posSide": TEST_FIXTURE_IDENTITY["posSide"],
        "pos": "",
        "captured_at_utc": "",
        "lifecycle_id": "",
    }
    later_runtime = {
        "instId": TEST_FIXTURE_IDENTITY["instId"],
        "pos": "3",
        "peak_trade_owned_resulting_current_position_qty": "3",
        "bound_fill_identity": dict(TEST_FIXTURE_IDENTITY),
        "lifecycle_id": LIFECYCLE_ID,
        "now_utc": CAPTURE_STARTED_AT,
        "field_provenance": _provenance(),
    }
    refused = refuse_incomplete_record_plus_later_runtime_state_v1(
        historical_record=historical,
        later_runtime_state=later_runtime,
        expected_identity=TEST_FIXTURE_IDENTITY,
        expected_lifecycle=LIFECYCLE_ID,
        expected_captured_at_utc=CAPTURE_STARTED_AT,
    )
    assert refused["VALID_CONTEMPORANEOUS_CAPTURE_RECORD"] is False
    assert refused["FAIL_CLOSED"] is True
    assert refused["HISTORICAL_INCOMPLETE_PLUS_LATER_RUNTIME_IS_NOT_CONTEMPORANEOUS_VALID"] is True
    with pytest.raises(
        Section1114OfflineSurfaceError, match="LATER_RUNTIME_STATE_MUST_NOT_COMPLETE_CAPTURE"
    ):
        validate_contemporaneous_no_backfill_persisted_record_v1(
            record={
                **historical,
                "instId": TEST_FIXTURE_IDENTITY["instId"],
                "pos": "3",
                "captured_at_utc": CAPTURE_STARTED_AT,
                "lifecycle_id": LIFECYCLE_ID,
                "field_provenance": _provenance()["fields"],
            },
            expected_identity=TEST_FIXTURE_IDENTITY,
            expected_lifecycle=LIFECYCLE_ID,
            expected_captured_at_utc=CAPTURE_STARTED_AT,
            later_runtime_state=later_runtime,
        )


def test_legacy_codec_document_class_stamp_is_not_contemporaneous_valid() -> None:
    payload = {
        "clOrdId": TEST_FIXTURE_IDENTITY["clOrdId"],
        "ordId": TEST_FIXTURE_IDENTITY["ordId"],
        "instId": TEST_FIXTURE_IDENTITY["instId"],
        "posSide": TEST_FIXTURE_IDENTITY["posSide"],
        "pos": "3",
        "provenance_class": CONTEMPORANEOUS_PROVENANCE_CLASS,
        "claimed_owner": "NONE",
    }
    split = classify_legacy_codec_document_class_synthesis_v1(payload=payload)
    assert split["LEGACY_READABLE"] is True
    assert split["CONTEMPORANEOUS_VALID"] is False
    assert split["LEGACY_READABLE_IS_NOT_CONTEMPORANEOUS_VALID"] is True
    assert split["CODEC_STAMP_IS_NOT_CONTEMPORANEOUS_CAPTURE"] is True


def test_adjudication_proves_complete_seam_offline_without_live_claims() -> None:
    adjudication = bind_complete_capture_seam_required_field_provenance_and_no_backfill_contract_v1(
        repo_root=REPO_ROOT
    )
    assert adjudication["COMPLETE_CAPTURE_SEAM"] == "PROVEN"
    assert adjudication["AUTHORITATIVE_CAPTURE_PRODUCER"] == AUTHORITATIVE_CAPTURE_PRODUCER
    assert adjudication["CAPTURE_HOOK"] == CAPTURE_HOOK
    assert adjudication["CAPTURE_OWNER"] == CAPTURE_OWNER
    assert adjudication["PRODUCTIVE_HOOK_CALLER"] == PRODUCTIVE_HOOK_CALLER
    assert adjudication["REQUIRED_FIELD_PROVENANCE_COMPLETE"] is True
    assert adjudication["NO_BACKFILL_CONTRACT_PROVEN"] is True
    assert adjudication["PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"] is True
    assert adjudication["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert adjudication["CURRENT_RUNTIME_EXECUTION_AUTHORIZED"] is False
    assert adjudication["AUTHORIZED_RUNTIME_SURFACE"] == "NONE"
    assert adjudication["LIVE_RESTART_RECONSTRUCTED"] is False
    assert adjudication["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    assert adjudication["LIVE_SUBMIT_EXECUTED"] is False
    assert adjudication["WIRE_SEND_EXECUTED"] is False
    assert adjudication["RESTART_EXECUTED"] is False
    assert adjudication["HISTORICAL_READER_BIND_COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert (
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"
        in adjudication["HISTORICAL_COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"]
    )


def test_execute_is_offline_and_does_not_claim_productive_capture() -> None:
    result = execute_live_handoff_complete_capture_seam_required_field_provenance_and_no_backfill_contract_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        run_id="20260907T140000Z-test",
    )
    summary = result["summary"]
    assert summary["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert summary["COMPLETE_CAPTURE_SEAM"] == "PROVEN"
    assert summary["PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"] is True
    assert summary["REQUIRED_FIELD_PROVENANCE_COMPLETE"] is True
    assert summary["NO_BACKFILL_CONTRACT_PROVEN"] is True
    assert summary["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert summary["PRODUCTIVE_CAPTURE_WRITE_EXECUTED"] is False
    assert summary["HANDOFF_WRITTEN"] is False
    assert summary["RESTART_EXECUTED"] is False
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["WIRE_SEND"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["CURRENT_RUNTIME_EXECUTION_AUTHORIZED"] is False
    assert result["raw_exchanges"] == []
    assert result["safety"]["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert result["safety"]["COMPLETE_CAPTURE_SEAM"] == "PROVEN"
