"""Complete contemporaneous capture-seam and required-field provenance tests.

All inputs are TEST_FIXTURE. These tests do not execute productive Live
capture, submit, wire send, or restart.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_hook_v1 import (
    run_capture_hook_after_bound_fill_before_restart_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_OWNER_GO,
    HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_SHA,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_execute_v1 import (
    execute_live_handoff_complete_contemporaneous_capture_seam_and_required_field_provenance_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_v1 import (
    CASE_ADJUDICATION,
    COMPLETE_CAPTURE_SEAM,
    FIELD_STATUS_PROVEN_FAIL_CLOSED_IF_ABSENT,
    INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
    INPUT_CLASS_TEST_FIXTURE,
    accept_complete_contemporaneous_capture_inputs_v1,
    bind_complete_contemporaneous_capture_seam_and_required_field_provenance_v1,
    bind_required_field_provenance_matrix_v1,
    build_test_fixture_field_provenance_v1,
    census_productive_capture_dataflow_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    CANONICAL_BOUND_FILL_KIND,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
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
LIFECYCLE_ID = "test-fixture-complete-capture-seam-lifecycle-v1"


def _provenance(**overrides: object) -> dict[str, object]:
    payload = build_test_fixture_field_provenance_v1(
        bound_fill_identity=TEST_FIXTURE_IDENTITY,
        lifecycle_id=LIFECYCLE_ID,
    )
    payload.update(overrides)
    return payload


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
        "bound_fill_proven_at": "2026-09-07T12:00:00Z",
        "capture_started_at": "2026-09-07T12:00:01Z",
        "attempt_identity": "test-fixture-attempt-v1",
        "lifecycle_id": LIFECYCLE_ID,
        "field_provenance": _provenance(),
    }
    payload.update(overrides)
    return payload


def test_current_slice_and_owner_go_match_this_workpackage() -> None:
    assert HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_OWNER_GO.endswith(
        "COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_AND_REQUIRED_FIELD_PROVENANCE_V1"
    )
    assert HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_SHA == (
        "4437d3e48fb900202fb87e349a7f1b81df4bb6b5"
    )


def test_dataflow_census_does_not_invent_post_fill_normalization() -> None:
    census = census_productive_capture_dataflow_v1()
    assert census["POST_FILL_NORMALIZATION_OWNER"] == "NONE"
    assert census["HOOK_PRODUCTIVE_CALLER_COUNT"] == 1
    assert census["UPSTREAM_LIVE_ORDER_JOIN_TO_HOOK"] == "PROVEN"
    assert census["READER_IS_NOT_A_PRE_RESTART_SOURCE"] is True
    assert census["NAMING_SIMILARITY_IS_NOT_BINDING"] is True


def test_required_field_matrix_is_fail_closed_and_not_complete_production() -> None:
    matrix = bind_required_field_provenance_matrix_v1()
    assert matrix["HANDOFF_REQUIRED_FIELD_COUNT"] == len(REQUIRED_HANDOFF_FIELDS)
    assert matrix["PROVEN_COMPLETE_FIELD_COUNT"] == 0
    assert matrix["PROVEN_FAIL_CLOSED_FIELD_COUNT"] == 5
    assert matrix["UNPROVEN_FIELD_COUNT"] == 0
    assert matrix["CONTRADICTORY_FIELD_COUNT"] == 0
    assert matrix["PARTIAL_CAPTURE_ALLOWED"] is False
    assert matrix["RETROACTIVE_SYNTHESIS_ALLOWED"] is False
    for row in matrix["rows"]:
        assert row["STATUS"] == FIELD_STATUS_PROVEN_FAIL_CLOSED_IF_ABSENT
        assert row["MISSING_BEHAVIOR"] == "HARD_FAIL"
        assert row["HISTORICAL_BOUND_IDENTITY_IS_NOT_CURRENT_PRODUCER"] is True
        assert row["UPSTREAM_LIVE_ORDER_JOIN_TO_HOOK"] == "PROVEN"


def test_complete_test_fixture_input_constructs_complete_record_without_productive_claim() -> None:
    accepted = accept_complete_contemporaneous_capture_inputs_v1(**_accept_kwargs())
    assert accepted["ALLOWED"] is True
    assert accepted["TEST_FIXTURE"] is True
    assert accepted["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert accepted["PARTIAL_CAPTURE"] is False
    for name in REQUIRED_HANDOFF_FIELDS:
        assert str(accepted["record"][name]).strip() != ""
    assert accepted["record"]["pos"] == "3"
    assert accepted["record"]["instId"] == TEST_FIXTURE_IDENTITY["instId"]


def test_each_required_field_missing_hard_fails() -> None:
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


def test_wrong_fill_order_instrument_identity_hard_fails() -> None:
    provenance = _provenance()
    fields = dict(provenance["fields"])
    fields["ordId"] = dict(fields["ordId"])
    fields["ordId"]["VALUE"] = "9999999999999999999"
    provenance["fields"] = fields
    with pytest.raises(Section1114OfflineSurfaceError, match="IDENTITY_MISMATCH"):
        accept_complete_contemporaneous_capture_inputs_v1(
            **_accept_kwargs(field_provenance=provenance)
        )
    wrong_instrument = dict(TEST_FIXTURE_IDENTITY)
    wrong_instrument["instId"] = "BTC-USD_UM_XPERP-WRONG"
    with pytest.raises(Section1114OfflineSurfaceError, match="IDENTITY_MISMATCH"):
        accept_complete_contemporaneous_capture_inputs_v1(
            **_accept_kwargs(
                bound_fill_identity=wrong_instrument,
                field_provenance=_provenance(),
            )
        )


def test_stale_and_forbidden_provenance_hard_fail() -> None:
    provenance = _provenance()
    fields = dict(provenance["fields"])
    fields["clOrdId"] = dict(fields["clOrdId"])
    fields["clOrdId"]["FRESHNESS"] = "STALE_CACHE"
    provenance["fields"] = fields
    with pytest.raises(Section1114OfflineSurfaceError, match="STALE_OR_INVALID_PROVENANCE"):
        accept_complete_contemporaneous_capture_inputs_v1(
            **_accept_kwargs(field_provenance=provenance)
        )
    provenance = _provenance()
    fields = dict(provenance["fields"])
    fields["pos"] = dict(fields["pos"])
    fields["pos"]["SOURCE_KIND"] = "FILL_SZ_COPY"
    provenance["fields"] = fields
    with pytest.raises(Section1114OfflineSurfaceError, match="FIELD_SOURCE_KIND_REJECTED"):
        accept_complete_contemporaneous_capture_inputs_v1(
            **_accept_kwargs(field_provenance=provenance)
        )


def test_ambiguous_duplicate_identity_hard_fails() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="AMBIGUOUS_DUPLICATE_IDENTITY"):
        accept_complete_contemporaneous_capture_inputs_v1(
            **_accept_kwargs(extra_fields={"clOrdId": "other-clordid-not-the-same"})
        )


def test_restart_derived_and_historical_inputs_hard_fail() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="RESTART_DERIVED_INPUT_FORBIDDEN"):
        accept_complete_contemporaneous_capture_inputs_v1(**_accept_kwargs(restart_derived=True))
    with pytest.raises(
        Section1114OfflineSurfaceError, match="RESTART_READER_IS_NOT_A_PRE_RESTART_SOURCE"
    ):
        accept_complete_contemporaneous_capture_inputs_v1(
            **_accept_kwargs(source_is_restart_reader=True)
        )
    with pytest.raises(
        Section1114OfflineSurfaceError, match="HISTORICAL_EVIDENCE_IS_NOT_CURRENT_RUNTIME"
    ):
        accept_complete_contemporaneous_capture_inputs_v1(
            **_accept_kwargs(source_is_historical_evidence=True)
        )
    provenance = _provenance()
    fields = dict(provenance["fields"])
    fields["pos"] = dict(fields["pos"])
    fields["pos"]["SOURCE_KIND"] = "RESTART_READER"
    provenance["fields"] = fields
    with pytest.raises(Section1114OfflineSurfaceError, match="FIELD_SOURCE_KIND_REJECTED"):
        accept_complete_contemporaneous_capture_inputs_v1(
            **_accept_kwargs(field_provenance=provenance)
        )


def test_productive_capture_executed_claim_is_rejected() -> None:
    with pytest.raises(
        Section1114OfflineSurfaceError, match="PRODUCTIVE_CAPTURE_MUST_NOT_BE_CLAIMED"
    ):
        accept_complete_contemporaneous_capture_inputs_v1(
            **_accept_kwargs(contemporaneous_productive_capture_executed=True)
        )


def test_unauthorized_productive_input_class_cannot_persist_through_hook(
    tmp_path: Path,
) -> None:
    provenance = build_test_fixture_field_provenance_v1(
        bound_fill_identity=TEST_FIXTURE_IDENTITY,
        lifecycle_id=LIFECYCLE_ID,
    )
    for row in provenance["fields"].values():
        row["INPUT_CLASS"] = INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT
        if row["FIELD"] == "pos":
            row["SOURCE_KIND"] = "PEAK_TRADE_OWNED_S05_QTY"
        else:
            row["SOURCE_KIND"] = "PARAMETERIZED_BOUND_FILL_IDENTITY"
    provenance["INPUT_CLASS"] = INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT
    accepted = accept_complete_contemporaneous_capture_inputs_v1(
        **_accept_kwargs(
            input_class=INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
            field_provenance=provenance,
        )
    )
    assert accepted["COMPLETE_RECORD_STRUCTURALLY_CONSTRUCTIBLE"] is True
    assert accepted["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    with pytest.raises(Section1114OfflineSurfaceError, match="RUNTIME_EXECUTION_UNAUTHORIZED"):
        run_capture_hook_after_bound_fill_before_restart_v1(
            storage_root=tmp_path,
            bound_fill_proven=True,
            bound_fill_kind=CANONICAL_BOUND_FILL_KIND,
            bound_fill_identity=TEST_FIXTURE_IDENTITY,
            peak_trade_owned_resulting_current_position_qty="3",
            source_kind=ADMISSIBLE_POS_SOURCE_KIND,
            unit=POS_UNIT,
            restart_already_occurred=False,
            restart_not_yet_occurred_proven=True,
            bound_fill_proven_at="2026-09-07T12:00:00Z",
            capture_started_at="2026-09-07T12:00:01Z",
            attempt_identity="test-fixture-attempt-v1",
            input_class=INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
            lifecycle_id=LIFECYCLE_ID,
            field_provenance=provenance,
        )


def test_test_fixture_hook_persist_is_not_productive_capture(tmp_path: Path) -> None:
    result = run_capture_hook_after_bound_fill_before_restart_v1(
        storage_root=tmp_path,
        bound_fill_proven=True,
        bound_fill_kind=CANONICAL_BOUND_FILL_KIND,
        bound_fill_identity=TEST_FIXTURE_IDENTITY,
        peak_trade_owned_resulting_current_position_qty="3",
        source_kind=ADMISSIBLE_POS_SOURCE_KIND,
        unit=POS_UNIT,
        restart_already_occurred=False,
        restart_not_yet_occurred_proven=True,
        bound_fill_proven_at="2026-09-07T12:00:00Z",
        capture_started_at="2026-09-07T12:00:01Z",
        attempt_identity="test-fixture-attempt-v1",
        input_class=INPUT_CLASS_TEST_FIXTURE,
        lifecycle_id=LIFECYCLE_ID,
        field_provenance=_provenance(),
    )
    assert result["TEST_FIXTURE"] is True
    assert result["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert result["DURABLE_SUCCESS_ACK"] is True
    assert result["LIVE_RESTART_RECONSTRUCTED"] is False


def test_adjudication_keeps_complete_seam_unproven_and_runtime_unauthorized() -> None:
    adjudication = bind_complete_contemporaneous_capture_seam_and_required_field_provenance_v1(
        repo_root=REPO_ROOT
    )
    assert adjudication["COMPLETE_CAPTURE_SEAM"] == COMPLETE_CAPTURE_SEAM
    assert adjudication["PRODUCTIVE_CAPTURE_OWNER"] == PRODUCTIVE_CAPTURE_OWNER
    assert adjudication["PRODUCTIVE_LIFECYCLE_HOOK"] == PRODUCTIVE_LIFECYCLE_HOOK
    assert adjudication["STRUCTURAL_RUNTIME_BINDING_PROVEN"] is True
    assert adjudication["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert adjudication["COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND"] is True
    assert adjudication["REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND"] is True
    assert adjudication["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert adjudication["CURRENT_RUNTIME_EXECUTION_AUTHORIZED"] is False
    assert adjudication["AUTHORIZED_RUNTIME_SURFACE"] == "NONE"
    assert adjudication["LIVE_RESTART_RECONSTRUCTED"] is False
    assert adjudication["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    assert adjudication["CAN_STRUCTURALLY_CONSTRUCT_COMPLETE_RECORD"] is True
    assert adjudication["HAS_PRODUCTIVELY_CONSTRUCTED_COMPLETE_RECORD"] is False
    assert LIVE_RESTART_RECONSTRUCTED is False
    assert LIVE_ENABLED is False
    assert POST_ALLOWED is False
    assert SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is False


def test_execute_is_offline_and_does_not_claim_productive_capture() -> None:
    result = (
        execute_live_handoff_complete_contemporaneous_capture_seam_and_required_field_provenance_v1(
            owner_go=HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_OWNER_GO,
            origin_main_sha=HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_SHA,
            repo_root=REPO_ROOT,
            run_id="20260907T120000Z-test",
        )
    )
    summary = result["summary"]
    assert summary["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert summary["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert summary["COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND"] is True
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
