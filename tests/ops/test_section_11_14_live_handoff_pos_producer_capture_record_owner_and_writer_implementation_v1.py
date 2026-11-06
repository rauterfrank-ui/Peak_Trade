"""Implementation tests for §11.14 Live S05 producer, owner mint, and writer."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_IMPLEMENTATION_OWNER_GO,
    HISTORICAL_IMPLEMENTATION_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
    SECTION_11_14_LIVE_HANDOFF_READER_PRESENT,
    SECTION_11_14_LIVE_HANDOFF_WRITER_PRESENT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_implementation_execute_v1 import (
    execute_live_handoff_pos_producer_capture_record_owner_and_writer_implementation_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_implementation_v1 import (
    COMPLETE_CAPTURE_SEAM,
    PROPOSED_NEXT_SLICE,
    bind_pos_producer_capture_record_owner_and_writer_implementation_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    HANDOFF_FILENAME,
    READER_BOUND,
    RELATIVE_DURABLE_DIR,
    WRITER_SEAM_ID,
    claim_handoff_mutation_success_v1,
    commit_handoff_after_bound_fill_before_restart_v1,
    construct_five_field_handoff_record_v1,
    durable_handoff_path_v1,
    load_durable_handoff_record_v1,
    mint_section_11_14_live_durable_pre_restart_handoff_owner_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
    NEW_PRODUCER_IMPLEMENTED,
    PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED,
    REQUIRED_CAPTURE_TRIGGER,
    emit_s05_handoff_pos_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
    REQUIRED_HANDOFF_FIELDS,
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
    POS_SEMANTICS,
    POS_SIGN_SEMANTICS,
    POS_UNIT,
    PRODUCER_ID,
    SELECTED_SEMANTIC_ID,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_ATTEMPT_IDENTITY = "test-attempt-s05-implementation-v1"
TEST_CAPTURED_AT = "2026-09-07T01:40:00Z"


def _producer_kwargs(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
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
    }
    payload.update(overrides)
    return payload


def _commit_kwargs(storage_root: Path, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "storage_root": storage_root,
        "attempt_identity": TEST_ATTEMPT_IDENTITY,
        "now_utc": TEST_CAPTURED_AT,
        **_producer_kwargs(),
    }
    payload.update(overrides)
    return payload


def test_s05_producer_emits_exact_five_required_fields() -> None:
    produced = emit_s05_handoff_pos_v1(**_producer_kwargs())
    assert produced["PRODUCER_ID"] == PRODUCER_ID
    assert produced["SELECTED_SEMANTIC_ID"] == SELECTED_SEMANTIC_ID
    assert produced["NEW_PRODUCER_IMPLEMENTED"] is True
    assert produced["PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED"] is True
    assert produced["source_kind"] == ADMISSIBLE_POS_SOURCE_KIND
    assert produced["POS_UNIT"] == POS_UNIT
    assert produced["POS_SIGN_SEMANTICS"] == POS_SIGN_SEMANTICS
    assert produced["FILL_SZ_COPY"] is False
    assert produced["VENUE_GET_USED"] is False
    assert produced["clOrdId"] == BOUND_CLORDID
    assert produced["ordId"] == BOUND_ORDID
    assert produced["instId"] == BOUND_INSTID
    assert produced["posSide"] == BOUND_POS_SIDE
    assert produced["pos"] == str(BOUND_FILL_SZ)
    record = construct_five_field_handoff_record_v1(
        producer_output=produced,
        attempt_identity=TEST_ATTEMPT_IDENTITY,
        captured_at_utc=TEST_CAPTURED_AT,
    )
    for name in REQUIRED_HANDOFF_FIELDS:
        assert str(record[name]).strip() != ""
    assert record["schema_version"] == HANDOFF_SCHEMA_VERSION
    assert record["SCHEMA_CHANGE_REQUIRED"] is False
    assert record["owner_id"] == FIRST_OWNER_ID


def test_owner_is_minted_and_writer_is_bound_reader_unbound() -> None:
    mint = mint_section_11_14_live_durable_pre_restart_handoff_owner_v1()
    binding = bind_pos_producer_capture_record_owner_and_writer_implementation_v1()
    assert mint["SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT"] == (
        "SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1"
    )
    assert mint["STORAGE_OWNER_MINTED"] is True
    assert mint["A1_WAL_AS_LIVE_HANDOFF_ALLOWED"] is False
    assert mint["DDO_REUSE"] is False
    assert mint["FILEGATE_REUSE"] is False
    assert mint["READER_BOUND"] is False
    assert SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT == FIRST_OWNER_ID
    assert SECTION_11_14_LIVE_HANDOFF_WRITER_PRESENT is True
    assert SECTION_11_14_LIVE_HANDOFF_READER_PRESENT is True
    assert binding["WRITER_BOUND"] is True
    assert binding["WRITER_SEAM_ID"] == WRITER_SEAM_ID
    assert binding["CAPTURE_TRIGGER_PRODUCTIVELY_BOUND"] is True
    assert binding["SELECTED_CAPTURE_TRIGGER"] == (
        "REQUIRED_WINDOW_HANDOFF_COMMIT_AFTER_BOUND_FILL_BEFORE_RESTART"
    )
    assert READER_BOUND is False
    assert binding["READER_BOUND"] is False
    assert binding["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert COMPLETE_CAPTURE_SEAM == "UNPROVEN"
    assert binding["LIVE_RESTART_RECONSTRUCTED"] is False
    assert binding["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    assert binding["DURABILITY_PROVEN_EFFECTIVE"] is False
    assert binding["IMPLEMENTATION_AUTHORIZED"] is False
    assert NEW_PRODUCER_IMPLEMENTED is True
    assert PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED is True
    assert POS_SEMANTICS == "PROVEN"
    assert binding["PROPOSED_NEXT_SLICE"] == PROPOSED_NEXT_SLICE


def test_durable_roundtrip_is_process_restart_readable(tmp_path: Path) -> None:
    ack = commit_handoff_after_bound_fill_before_restart_v1(**_commit_kwargs(tmp_path))
    assert ack["DURABLE_SUCCESS_ACK"] is True
    assert ack["IDEMPOTENT_REPLAY"] is False
    assert ack["PROCESS_RESTART_READABLE"] is True
    assert ack["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    claim = claim_handoff_mutation_success_v1(durable_success_ack=ack)
    assert claim["MUTATION_SUCCESS_CLAIM"] is True
    assert claim["DURABLE_SUCCESS_ACK_BEFORE_MUTATION_SUCCESS_CLAIM"] is True
    assert claim["LIVE_RESTART_RECONSTRUCTED"] is False
    loaded = load_durable_handoff_record_v1(storage_root=tmp_path)
    for name in REQUIRED_HANDOFF_FIELDS:
        assert loaded[name] == ack["record"][name]
    path = durable_handoff_path_v1(storage_root=tmp_path)
    assert path.is_file()
    assert path.name == HANDOFF_FILENAME
    assert RELATIVE_DURABLE_DIR in str(path)


def test_idempotent_exact_same_record_replays(tmp_path: Path) -> None:
    first = commit_handoff_after_bound_fill_before_restart_v1(**_commit_kwargs(tmp_path))
    second = commit_handoff_after_bound_fill_before_restart_v1(**_commit_kwargs(tmp_path))
    assert first["DURABLE_SUCCESS_ACK"] is True
    assert second["DURABLE_SUCCESS_ACK"] is True
    assert second["IDEMPOTENT_REPLAY"] is True
    loaded = load_durable_handoff_record_v1(storage_root=tmp_path)
    assert loaded["pos"] == first["record"]["pos"]
    assert loaded["attempt_identity"] == TEST_ATTEMPT_IDENTITY


def test_different_record_and_second_identity_fail_closed(tmp_path: Path) -> None:
    commit_handoff_after_bound_fill_before_restart_v1(**_commit_kwargs(tmp_path))
    with pytest.raises(Section1114OfflineSurfaceError, match="IDEMPOTENT_REJECT_DIFFERENT_RECORD"):
        commit_handoff_after_bound_fill_before_restart_v1(
            **_commit_kwargs(tmp_path, attempt_identity="test-attempt-different")
        )
    path = durable_handoff_path_v1(storage_root=tmp_path)
    alien = load_durable_handoff_record_v1(storage_root=tmp_path)
    alien["clOrdId"] = "alien-clordid"
    path.write_text(
        '{"DOCUMENT_CLASS":"SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_V1",'
        '"schema_version":"section_11_14_live_durable_pre_restart_handoff.v1",'
        f'"owner_id":"{FIRST_OWNER_ID}",'
        '"clOrdId":"alien-clordid","ordId":"alien-ord",'
        f'"instId":"{BOUND_INSTID}","posSide":"{BOUND_POS_SIDE}","pos":"1",'
        f'"provenance_class":"{CONTEMPORANEOUS_PROVENANCE_CLASS}",'
        f'"attempt_identity":"{TEST_ATTEMPT_IDENTITY}"}}',
        encoding="utf-8",
    )
    with pytest.raises(Section1114OfflineSurfaceError, match="NO_SECOND_IDENTITY"):
        commit_handoff_after_bound_fill_before_restart_v1(**_commit_kwargs(tmp_path))


def test_torn_write_is_invisible(tmp_path: Path) -> None:
    def _no_replace(_src: str, _dst: str) -> None:
        return None

    with pytest.raises(Section1114OfflineSurfaceError, match="DURABLE_HANDOFF_ABSENT"):
        commit_handoff_after_bound_fill_before_restart_v1(
            **_commit_kwargs(tmp_path, replace_fn=_no_replace)
        )
    path = durable_handoff_path_v1(storage_root=tmp_path)
    assert path.is_file() is False
    with pytest.raises(Section1114OfflineSurfaceError, match="DURABLE_HANDOFF_ABSENT"):
        load_durable_handoff_record_v1(storage_root=tmp_path)


def test_write_serialize_and_fsync_failures_forbid_mutation_claim(tmp_path: Path) -> None:
    def _fsync_boom(_fd: int) -> None:
        raise OSError("injected fsync failure")

    with pytest.raises(Section1114OfflineSurfaceError, match="WRITE_FAILURE"):
        commit_handoff_after_bound_fill_before_restart_v1(
            **_commit_kwargs(tmp_path, fsync_file_fn=_fsync_boom)
        )
    assert durable_handoff_path_v1(storage_root=tmp_path).is_file() is False
    with pytest.raises(Section1114OfflineSurfaceError, match="SERIALIZATION_FAILURE"):
        commit_handoff_after_bound_fill_before_restart_v1(
            **_commit_kwargs(tmp_path, serialize_fail=True)
        )
    assert durable_handoff_path_v1(storage_root=tmp_path).is_file() is False
    with pytest.raises(
        Section1114OfflineSurfaceError,
        match="MUTATION_SUCCESS_FORBIDDEN_WITHOUT_DURABLE_ACK",
    ):
        claim_handoff_mutation_success_v1(durable_success_ack={})


def test_malformed_wrong_unit_wrong_instrument_and_forbidden_sources_fail_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="QTY_MALFORMED"):
        emit_s05_handoff_pos_v1(**_producer_kwargs(resulting_current_position_qty="not-a-qty"))
    with pytest.raises(Section1114OfflineSurfaceError, match="WRONG_UNIT"):
        emit_s05_handoff_pos_v1(**_producer_kwargs(unit="USDT"))
    with pytest.raises(Section1114OfflineSurfaceError, match="WRONG_INSTRUMENT"):
        emit_s05_handoff_pos_v1(**_producer_kwargs(inst_id="BTC-USDT"))
    with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_DERIVATION_FIELD"):
        emit_s05_handoff_pos_v1(**_producer_kwargs(extra_fields={"fillSz": "1"}))
    with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_POS_DERIVATION"):
        emit_s05_handoff_pos_v1(**_producer_kwargs(source_kind="VENUE_GET_COPY"))
    with pytest.raises(Section1114OfflineSurfaceError, match="RETROACTIVE_SYNTHESIS_FORBIDDEN"):
        emit_s05_handoff_pos_v1(**_producer_kwargs(restart_already_occurred=True))
    with pytest.raises(Section1114OfflineSurfaceError, match="SILENT_REINITIALIZATION_FORBIDDEN"):
        emit_s05_handoff_pos_v1(**_producer_kwargs(resulting_current_position_qty="0"))


def test_execute_is_offline_and_does_not_prove_restart_or_complete_seam() -> None:
    result = execute_live_handoff_pos_producer_capture_record_owner_and_writer_implementation_v1(
        owner_go=HISTORICAL_IMPLEMENTATION_OWNER_GO,
        origin_main_sha=HISTORICAL_IMPLEMENTATION_SHA,
        repo_root=REPO_ROOT,
        run_id="20260907T014000Z-test",
    )
    summary = result["summary"]
    assert summary["WIRE_SEND"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["CREDENTIAL_USE"] is False
    assert summary["LIVE_RESTART_RECONSTRUCTED"] is False
    assert summary["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert summary["NEW_PRODUCER_IMPLEMENTED"] is True
    assert summary["STORAGE_OWNER_MINTED"] is True
    assert summary["WRITER_BOUND"] is True
    assert summary["READER_BOUND"] is False
    assert summary["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    assert summary["IMPLEMENTATION_AUTHORIZED"] is False
    assert summary["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is False
    assert summary["SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT"] == FIRST_OWNER_ID
    assert LIVE_RESTART_RECONSTRUCTED is False
    live = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    assert live["LIVE_RESTART_RECONSTRUCTED"] is False
    assert result["raw_exchanges"] == []
    assert result["adjudication"]["LIVE_RESTART_RECONSTRUCTED"] is False
