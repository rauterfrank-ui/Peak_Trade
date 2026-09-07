"""Restart-reader, provenance, freshness, and consumer-bind tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    OWNER_GO,
    SECTION_11_14_LIVE_HANDOFF_READER_PRESENT,
    THIS_SLICE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_consumer_bind_v1 import (
    consume_validated_handoff_for_restart_reconstruction_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    commit_handoff_after_bound_fill_before_restart_v1,
    durable_handoff_path_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_bind_execute_v1 import (
    execute_live_handoff_restart_reader_provenance_and_consumer_bind_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_bind_v1 import (
    COMPLETE_CAPTURE_SEAM,
    bind_restart_reader_provenance_and_consumer_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_v1 import (
    RESULT_MALFORMED_HANDOFF,
    RESULT_MISSING_HANDOFF,
    RESULT_PROVENANCE_INVALID,
    RESULT_READ_FAILURE,
    RESULT_SCHEMA_INVALID,
    RESULT_STALE_HANDOFF,
    RESULT_VALID_HANDOFF,
    RESULT_WRONG_INSTRUMENT,
    read_validated_durable_pre_restart_handoff_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
    HANDOFF_DOCUMENT_CLASS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    HANDOFF_SCHEMA_VERSION,
    POS_UNIT,
    SELECTED_SEMANTIC_ID,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_ATTEMPT = "test-attempt-reader-bind-v1"
TEST_CAPTURED_AT = "2026-09-07T02:55:00Z"


def _commit(storage_root: Path, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "storage_root": storage_root,
        "resulting_current_position_qty": BOUND_FILL_SZ,
        "unit": POS_UNIT,
        "source_kind": ADMISSIBLE_POS_SOURCE_KIND,
        "inst_id": BOUND_INSTID,
        "clordid": BOUND_CLORDID,
        "ord_id": BOUND_ORDID,
        "pos_side": BOUND_POS_SIDE,
        "bound_fill_identity_exists": True,
        "capture_trigger": REQUIRED_CAPTURE_TRIGGER,
        "provenance_class": CONTEMPORANEOUS_PROVENANCE_CLASS,
        "attempt_identity": TEST_ATTEMPT,
        "now_utc": TEST_CAPTURED_AT,
    }
    payload.update(overrides)
    return commit_handoff_after_bound_fill_before_restart_v1(**payload)


def _write_raw(storage_root: Path, payload: dict[str, object]) -> Path:
    path = durable_handoff_path_v1(storage_root=storage_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def _valid_envelope(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "DOCUMENT_CLASS": HANDOFF_DOCUMENT_CLASS,
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "owner_id": FIRST_OWNER_ID,
        "claimed_owner": FIRST_OWNER_ID,
        "clOrdId": BOUND_CLORDID,
        "ordId": BOUND_ORDID,
        "instId": BOUND_INSTID,
        "posSide": BOUND_POS_SIDE,
        "pos": str(BOUND_FILL_SZ),
        "provenance_class": CONTEMPORANEOUS_PROVENANCE_CLASS,
        "attempt_identity": TEST_ATTEMPT,
        "captured_at_utc": TEST_CAPTURED_AT,
        "written_at_utc": TEST_CAPTURED_AT,
    }
    payload.update(overrides)
    return payload


def test_writer_reader_roundtrip_valid_record(tmp_path: Path) -> None:
    ack = _commit(tmp_path)
    result = read_validated_durable_pre_restart_handoff_v1(
        storage_root=tmp_path,
        expected_attempt_identity=TEST_ATTEMPT,
    )
    assert result["RESULT"] == RESULT_VALID_HANDOFF
    assert result["GET_PERFORMED"] is False
    assert result["VENUE_GET_FALLBACK"] is False
    assert result["validated_handoff"]["pos"] == ack["record"]["pos"]
    assert result["validated_handoff"]["SELECTED_SEMANTIC_ID"] == SELECTED_SEMANTIC_ID
    consumed = consume_validated_handoff_for_restart_reconstruction_v1(reader_result=result)
    assert consumed["CONSUMER_ACCEPTED"] is True
    assert consumed["LIVE_RESTART_RECONSTRUCTED"] is False
    assert consumed["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is False


def test_missing_record_fail_closed(tmp_path: Path) -> None:
    result = read_validated_durable_pre_restart_handoff_v1(storage_root=tmp_path)
    assert result["RESULT"] == RESULT_MISSING_HANDOFF
    consumed = consume_validated_handoff_for_restart_reconstruction_v1(reader_result=result)
    assert consumed["CONSUMER_ACCEPTED"] is False
    assert consumed["LIVE_RESTART_RECONSTRUCTED"] is False


def test_malformed_serialization_fail_closed(tmp_path: Path) -> None:
    path = durable_handoff_path_v1(storage_root=tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not-json", encoding="utf-8")
    result = read_validated_durable_pre_restart_handoff_v1(storage_root=tmp_path)
    assert result["RESULT"] == RESULT_MALFORMED_HANDOFF


def test_missing_required_field_fail_closed(tmp_path: Path) -> None:
    payload = _valid_envelope()
    payload["pos"] = ""
    _write_raw(tmp_path, payload)
    result = read_validated_durable_pre_restart_handoff_v1(storage_root=tmp_path)
    assert result["RESULT"] == RESULT_MALFORMED_HANDOFF
    assert result["REASON"] == "MISSING_REQUIRED_HANDOFF_FIELDS"


def test_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    _write_raw(
        tmp_path,
        _valid_envelope(schema_version="section_11_14_live_durable_pre_restart_handoff.v2"),
    )
    result = read_validated_durable_pre_restart_handoff_v1(storage_root=tmp_path)
    assert result["RESULT"] == RESULT_SCHEMA_INVALID


def test_wrong_instrument_fail_closed(tmp_path: Path) -> None:
    _write_raw(tmp_path, _valid_envelope(instId="BTC-USDT-SWAP"))
    result = read_validated_durable_pre_restart_handoff_v1(storage_root=tmp_path)
    assert result["RESULT"] == RESULT_WRONG_INSTRUMENT
    consumed = consume_validated_handoff_for_restart_reconstruction_v1(reader_result=result)
    assert consumed["CONSUMER_ACCEPTED"] is False


def test_invalid_pos_and_posside_fail_closed(tmp_path: Path) -> None:
    _write_raw(tmp_path, _valid_envelope(pos="-1"))
    negative = read_validated_durable_pre_restart_handoff_v1(storage_root=tmp_path)
    assert negative["RESULT"] == RESULT_MALFORMED_HANDOFF
    assert negative["REASON"] == "INVALID_POS"
    _write_raw(tmp_path, _valid_envelope(pos="not-a-qty"))
    malformed = read_validated_durable_pre_restart_handoff_v1(storage_root=tmp_path)
    assert malformed["REASON"] == "INVALID_POS"
    _write_raw(tmp_path, _valid_envelope(posSide="long"))
    side = read_validated_durable_pre_restart_handoff_v1(storage_root=tmp_path)
    assert side["REASON"] == "INVALID_POSSIDE"


def test_stale_attempt_and_temporal_inversion_fail_closed(tmp_path: Path) -> None:
    _commit(tmp_path)
    stale = read_validated_durable_pre_restart_handoff_v1(
        storage_root=tmp_path,
        expected_attempt_identity="other-attempt",
    )
    assert stale["RESULT"] == RESULT_STALE_HANDOFF
    inverted = read_validated_durable_pre_restart_handoff_v1(
        storage_root=tmp_path,
        expected_attempt_identity=TEST_ATTEMPT,
        restart_at_utc="2026-09-07T02:00:00Z",
    )
    assert inverted["RESULT"] == RESULT_STALE_HANDOFF


def test_provenance_mismatch_and_forbidden_sources_fail_closed(tmp_path: Path) -> None:
    _write_raw(tmp_path, _valid_envelope(provenance_class="VENUE_GET_COPY"))
    venue = read_validated_durable_pre_restart_handoff_v1(storage_root=tmp_path)
    assert venue["RESULT"] == RESULT_PROVENANCE_INVALID
    _write_raw(tmp_path, _valid_envelope(owner_id="DDO_DURABLE_EVIDENCE_STORAGE_OWNER"))
    owner = read_validated_durable_pre_restart_handoff_v1(storage_root=tmp_path)
    assert owner["RESULT"] == RESULT_PROVENANCE_INVALID
    pack = read_validated_durable_pre_restart_handoff_v1(
        storage_root=tmp_path,
        source_path=(
            "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "20260907T014000Z/SUMMARY.json"
        ),
    )
    assert pack["RESULT"] == RESULT_PROVENANCE_INVALID
    get_source = read_validated_durable_pre_restart_handoff_v1(
        storage_root=tmp_path,
        source_path="GET_POSITIONS.raw.json",
    )
    assert get_source["RESULT"] == RESULT_PROVENANCE_INVALID


def test_owner_read_failure_and_no_fillsz_substitution(tmp_path: Path) -> None:
    path = durable_handoff_path_v1(storage_root=tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir()
    result = read_validated_durable_pre_restart_handoff_v1(storage_root=tmp_path)
    assert result["RESULT"] == RESULT_READ_FAILURE
    file_root = tmp_path / "file-root"
    file_root.mkdir()
    payload = _valid_envelope()
    payload["fillSz"] = str(BOUND_FILL_SZ)
    _write_raw(file_root, payload)
    substituted = read_validated_durable_pre_restart_handoff_v1(storage_root=file_root)
    assert substituted["REASON"] == "POS_SUBSTITUTION_FORBIDDEN"


def test_identity_mismatch_is_non_applicable(tmp_path: Path) -> None:
    _write_raw(tmp_path, _valid_envelope(clOrdId="alien-clordid"))
    result = read_validated_durable_pre_restart_handoff_v1(storage_root=tmp_path)
    assert result["RESULT"] == RESULT_STALE_HANDOFF
    assert result["REASON"] == "IDENTITY_MISMATCH"


def test_s05_semantic_preservation_and_no_backfill(tmp_path: Path) -> None:
    _commit(tmp_path)
    result = read_validated_durable_pre_restart_handoff_v1(
        storage_root=tmp_path,
        expected_attempt_identity=TEST_ATTEMPT,
    )
    validated = result["validated_handoff"]
    assert validated["posSide"] == "net"
    assert validated["POS_SIGN_SEMANTICS"] == "UNSIGNED_MAGNITUDE"
    assert validated["POS_UNIT"] == POS_UNIT
    assert result["TIMESTAMP_BACKFILL"] is False
    assert result["SYNTHETIC_PRE_RESTART_PROVENANCE"] is False
    assert result["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is False


def test_process_restart_writer_reader_idempotent_roundtrip(tmp_path: Path) -> None:
    first = _commit(tmp_path)
    second = _commit(tmp_path)
    assert second["IDEMPOTENT_REPLAY"] is True
    result = read_validated_durable_pre_restart_handoff_v1(
        storage_root=tmp_path,
        expected_attempt_identity=TEST_ATTEMPT,
    )
    assert result["RESULT"] == RESULT_VALID_HANDOFF
    assert result["validated_handoff"]["pos"] == first["record"]["pos"]


def test_consumer_rejects_every_invalid_reader_result() -> None:
    for result_class in (
        RESULT_MISSING_HANDOFF,
        RESULT_MALFORMED_HANDOFF,
        RESULT_STALE_HANDOFF,
        RESULT_WRONG_INSTRUMENT,
        RESULT_PROVENANCE_INVALID,
        RESULT_SCHEMA_INVALID,
        RESULT_READ_FAILURE,
    ):
        consumed = consume_validated_handoff_for_restart_reconstruction_v1(
            reader_result={"RESULT": result_class}
        )
        assert consumed["CONSUMER_ACCEPTED"] is False
        assert consumed["LIVE_RESTART_RECONSTRUCTED"] is False
        assert consumed["FALLBACK_USED"] is False


def test_binding_keeps_restart_and_seam_unproven() -> None:
    binding = bind_restart_reader_provenance_and_consumer_v1()
    assert THIS_SLICE == "11.14.LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND"
    assert SECTION_11_14_LIVE_HANDOFF_READER_PRESENT is True
    assert binding["READER_BOUND"] is True
    assert binding["RESTART_CONSUMER_BOUND"] is True
    assert binding["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert COMPLETE_CAPTURE_SEAM == "UNPROVEN"
    assert (
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"
        in binding["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"]
    )
    assert binding["LIVE_RESTART_RECONSTRUCTED"] is False
    assert binding["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    assert LIVE_RESTART_RECONSTRUCTED is False


def test_execute_is_offline_and_does_not_observe_contemporaneous_handoff() -> None:
    result = execute_live_handoff_restart_reader_provenance_and_consumer_bind_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        run_id="20260907T025500Z-test",
    )
    summary = result["summary"]
    assert summary["READER_BOUND"] is True
    assert summary["RESTART_CONSUMER_BOUND"] is True
    assert summary["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert summary["LIVE_RESTART_RECONSTRUCTED"] is False
    assert summary["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is False
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["WIRE_SEND"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    assert summary["IMPLEMENTATION_AUTHORIZED"] is False
    assert result["raw_exchanges"] == []
    assert result["adjudication"]["LIVE_RESTART_RECONSTRUCTED"] is False
