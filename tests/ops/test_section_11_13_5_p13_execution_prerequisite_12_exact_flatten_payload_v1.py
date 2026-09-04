"""P13 EXECUTION_PREREQUISITE_12 exact flatten payload contract tests. Offline only."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FlattenPricePermitV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.captured_payload_v1 import (
    AUTHORIZED_TARGET_ROW,
    captured_envelope_v1,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.adjudicate_v1 import (
    P13ExactFlattenPayloadAdjudicationError,
    adjudicate_execution_prerequisite_12_exact_flatten_payload_v1,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_CLOSED,
    P10_CLOSED,
    P11_CLOSED,
    P12_EXACT_FLATTEN_PAYLOAD_CLOSED_VALUE,
    P12_EXACT_FLATTEN_PAYLOAD_PROVEN_VALUE,
    POST_ALLOWED,
    PRIVATE_AUTH_USED,
    REQUEST_POS_SIDE,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.contract_v1 import (
    EXACT_FLATTEN_PAYLOAD_ALLOWED_KEYS,
    ExactFlattenPayloadError,
    assert_exact_flatten_payload_contract_v1,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.payload_builder_v1 import (
    build_exact_flatten_payload_from_observed_position_v1,
    offline_contract_proof_price_permit_v1,
)

TARGET = "SUI-USD_UM_XPERP-310404"


def _envelope(*rows: dict[str, str]) -> dict[str, object]:
    return {"code": "0", "msg": "", "data": list(rows)}


def _row(*, inst_id: str = TARGET, pos: str = "1") -> dict[str, str]:
    return {"instId": inst_id, "pos": pos, "posSide": "net", "mgnMode": "cross"}


def _permit(*, side: str, signed_pos: str) -> FlattenPricePermitV1:
    return offline_contract_proof_price_permit_v1(flatten_side=side, signed_pos=signed_pos)


def test_owner_go_is_forbidden_flatten_and_does_not_authorize_runtime() -> None:
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert POST_ALLOWED is False
    assert GET_ALLOWED is False
    assert PRIVATE_AUTH_USED is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert THIS_SLICE == "11.13.5.P13"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_13_5_P13"
    assert P08_CLOSED is True
    assert P10_CLOSED is True
    assert P11_CLOSED is True
    assert P12_EXACT_FLATTEN_PAYLOAD_PROVEN_VALUE is True
    assert P12_EXACT_FLATTEN_PAYLOAD_CLOSED_VALUE is True
    assert THIS_GO_GET_COUNT == 0
    assert REQUEST_POS_SIDE == "OMITTED"
    assert EARLIEST_UNRESOLVED_DEPENDENCY == (
        "EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED"
    )
    assert NEXT_AUTHORITY_BOUNDARY == (
        "SEPARATE_OWNER_GO_FOR_EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION"
    )


def test_positive_position_builds_sell_sz_identity() -> None:
    payload = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=_envelope(_row(pos="1")),
        price_permit=_permit(side="SELL", signed_pos="1"),
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert payload.flatten_side == "SELL"
    assert payload.body["side"] == "sell"
    assert payload.body["sz"] == "1"
    assert payload.body["instId"] == TARGET
    assert payload.body["tdMode"] == "cross"
    assert payload.body["ordType"] == "limit"
    assert payload.body["reduceOnly"] is True
    assert "posSide" not in payload.body
    assert set(payload.body) == set(EXACT_FLATTEN_PAYLOAD_ALLOWED_KEYS)


def test_negative_position_builds_buy_sz_abs() -> None:
    payload = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=_envelope(_row(pos="-2")),
        price_permit=_permit(side="BUY", signed_pos="-2"),
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert payload.flatten_side == "BUY"
    assert payload.body["side"] == "buy"
    assert payload.body["sz"] == "2"
    assert Decimal(payload.quantity) == abs(Decimal(payload.signed_pos))


def test_zero_position_has_no_flatten_payload() -> None:
    with pytest.raises(ExactFlattenPayloadError, match="ZERO_POSITION_NO_FLATTEN_ORDER"):
        build_exact_flatten_payload_from_observed_position_v1(
            positions_payload=_envelope(_row(pos="0")),
            price_permit=_permit(side="SELL", signed_pos="1"),
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        )


def test_empty_position_evidence_fails_closed() -> None:
    with pytest.raises(ExactFlattenPayloadError, match="TARGET_INSTRUMENT_NOT_OBSERVED"):
        build_exact_flatten_payload_from_observed_position_v1(
            positions_payload=_envelope(),
            price_permit=_permit(side="SELL", signed_pos="1"),
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        )


def test_stale_position_evidence_fails_closed() -> None:
    with pytest.raises(ExactFlattenPayloadError, match="STALE_OR_INVALID_POSITION_FRESHNESS"):
        build_exact_flatten_payload_from_observed_position_v1(
            positions_payload=_envelope(_row(pos="1")),
            price_permit=_permit(side="SELL", signed_pos="1"),
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            response_received_monotonic_ms=0,
            adjudication_monotonic_ms=5001,
        )


def test_wrong_instrument_fails_closed() -> None:
    with pytest.raises(ExactFlattenPayloadError, match="TARGET_INSTRUMENT_NOT_OBSERVED"):
        build_exact_flatten_payload_from_observed_position_v1(
            positions_payload=_envelope(_row(inst_id="BTC-USD_UM_XPERP-000000", pos="1")),
            price_permit=_permit(side="SELL", signed_pos="1"),
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        )


def test_ambiguous_multiple_target_rows_fail_closed() -> None:
    with pytest.raises(ExactFlattenPayloadError, match="AMBIGUOUS_TARGET_POSITION_ROWS"):
        build_exact_flatten_payload_from_observed_position_v1(
            positions_payload=_envelope(_row(pos="1"), _row(pos="2")),
            price_permit=_permit(side="SELL", signed_pos="1"),
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        )


def test_invalid_quantity_fails_closed() -> None:
    with pytest.raises(ExactFlattenPayloadError, match="POSITION_SIZE_UNPARSEABLE"):
        build_exact_flatten_payload_from_observed_position_v1(
            positions_payload=_envelope(_row(pos="not-a-number")),
            price_permit=_permit(side="SELL", signed_pos="1"),
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        )


def test_quantity_unit_mismatch_fails_closed() -> None:
    body = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=_envelope(_row(pos="1")),
        price_permit=_permit(side="SELL", signed_pos="1"),
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    ).body
    mutated = dict(body)
    mutated["sz"] = "2"
    with pytest.raises(ExactFlattenPayloadError, match="FLATTEN_BODY_SZ_NOT_PLAN_QUANTITY"):
        assert_exact_flatten_payload_contract_v1(
            mutated,
            instrument_id=TARGET,
            side="SELL",
            quantity="1",
            td_mode="cross",
            px=str(body["px"]),
            clordid=str(body["clOrdId"]),
        )


def test_side_mismatch_fails_closed() -> None:
    body = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=_envelope(_row(pos="1")),
        price_permit=_permit(side="SELL", signed_pos="1"),
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    ).body
    mutated = dict(body)
    mutated["side"] = "buy"
    with pytest.raises(ExactFlattenPayloadError, match="FLATTEN_BODY_SIDE_NOT_PLAN_SIDE"):
        assert_exact_flatten_payload_contract_v1(
            mutated,
            instrument_id=TARGET,
            side="SELL",
            quantity="1",
            td_mode="cross",
            px=str(body["px"]),
            clordid=str(body["clOrdId"]),
        )


def test_accidental_pos_side_insertion_fails_closed() -> None:
    body = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=_envelope(_row(pos="1")),
        price_permit=_permit(side="SELL", signed_pos="1"),
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    ).body
    mutated = dict(body)
    mutated["posSide"] = "net"
    with pytest.raises(ExactFlattenPayloadError, match="UNEXPECTED_PAYLOAD_FIELD:posSide"):
        assert_exact_flatten_payload_contract_v1(
            mutated,
            instrument_id=TARGET,
            side="SELL",
            quantity="1",
            td_mode="cross",
            px=str(body["px"]),
            clordid=str(body["clOrdId"]),
        )


def test_unexpected_payload_field_fails_closed() -> None:
    body = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=_envelope(_row(pos="1")),
        price_permit=_permit(side="SELL", signed_pos="1"),
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    ).body
    mutated = dict(body)
    mutated["tgtCcy"] = "SUI"
    with pytest.raises(ExactFlattenPayloadError, match="UNEXPECTED_PAYLOAD_FIELD"):
        assert_exact_flatten_payload_contract_v1(
            mutated,
            instrument_id=TARGET,
            side="SELL",
            quantity="1",
            td_mode="cross",
            px=str(body["px"]),
            clordid=str(body["clOrdId"]),
        )


def test_missing_required_payload_field_fails_closed() -> None:
    body = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=_envelope(_row(pos="1")),
        price_permit=_permit(side="SELL", signed_pos="1"),
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    ).body
    mutated = dict(body)
    mutated.pop("sz")
    with pytest.raises(ExactFlattenPayloadError, match="MISSING_REQUIRED_PAYLOAD_FIELD:sz"):
        assert_exact_flatten_payload_contract_v1(
            mutated,
            instrument_id=TARGET,
            side="SELL",
            quantity="1",
            td_mode="cross",
            px=str(body["px"]),
            clordid=str(body["clOrdId"]),
        )


def test_incorrect_td_mode_fails_closed() -> None:
    with pytest.raises(ExactFlattenPayloadError, match="INCORRECT_TD_MODE"):
        build_exact_flatten_payload_from_observed_position_v1(
            positions_payload=_envelope(_row(pos="1")),
            price_permit=_permit(side="SELL", signed_pos="1"),
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            td_mode="isolated",
        )


def test_incorrect_ord_type_fails_closed() -> None:
    body = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=_envelope(_row(pos="1")),
        price_permit=_permit(side="SELL", signed_pos="1"),
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    ).body
    mutated = dict(body)
    mutated["ordType"] = "market"
    with pytest.raises(ExactFlattenPayloadError, match="INCORRECT_ORD_TYPE"):
        assert_exact_flatten_payload_contract_v1(
            mutated,
            instrument_id=TARGET,
            side="SELL",
            quantity="1",
            td_mode="cross",
            px=str(body["px"]),
            clordid=str(body["clOrdId"]),
        )


def test_reduce_only_mismatch_fails_closed() -> None:
    body = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=_envelope(_row(pos="1")),
        price_permit=_permit(side="SELL", signed_pos="1"),
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    ).body
    mutated = dict(body)
    mutated["reduceOnly"] = False
    with pytest.raises(ExactFlattenPayloadError, match="REDUCE_ONLY_MISMATCH"):
        assert_exact_flatten_payload_contract_v1(
            mutated,
            instrument_id=TARGET,
            side="SELL",
            quantity="1",
            td_mode="cross",
            px=str(body["px"]),
            clordid=str(body["clOrdId"]),
        )


def test_deterministic_repeated_build() -> None:
    first = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=_envelope(_row(pos="1")),
        price_permit=_permit(side="SELL", signed_pos="1"),
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    second = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=_envelope(_row(pos="1")),
        price_permit=_permit(side="SELL", signed_pos="1"),
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert first.body == second.body
    assert first.body_sha256 == second.body_sha256
    assert first.canonical_json == second.canonical_json


def test_builder_has_no_network_import_side_effect() -> None:
    import src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.payload_builder_v1 as builder

    text = Path(builder.__file__).read_text(encoding="utf-8")
    assert "urllib" not in text
    assert "http.client" not in text
    assert "requests" not in text


def test_p08_captured_row_is_not_used_as_px() -> None:
    assert AUTHORIZED_TARGET_ROW["avgPx"] == "0.7774"
    payload = build_exact_flatten_payload_from_observed_position_v1(
        positions_payload=captured_envelope_v1(),
        price_permit=_permit(side="SELL", signed_pos="1"),
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert payload.body["px"] != AUTHORIZED_TARGET_ROW["avgPx"]
    assert payload.px_source_class == "BOUND_EXTERNAL_INPUT_NOT_FROM_OBSERVED_POSITION"


def test_live_window_nonzero_advances_to_prerequisite_20() -> None:
    result = adjudicate_prerequisite_08_window_v1(positions_payload=_envelope(_row(pos="1")))
    assert result["EXECUTION_PREREQUISITE_12_STATUS"] == "PASS"
    assert result["EARLIEST_UNRESOLVED_DEPENDENCY"] == (
        "EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION"
    )
    assert result["EXECUTION_READY"] is False


def test_origin_main_mismatch_fails_closed() -> None:
    with pytest.raises(P13ExactFlattenPayloadAdjudicationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        adjudicate_execution_prerequisite_12_exact_flatten_payload_v1(origin_main_sha="deadbeef")


def test_adjudication_closes_prerequisite_12_without_runtime() -> None:
    verdict = adjudicate_execution_prerequisite_12_exact_flatten_payload_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA
    )
    assert verdict["CASE"] == "CASE_B_OFFLINE_CLOSABLE"
    assert verdict["EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION"] == (
        "PASS"
    )
    assert verdict["P12_EXACT_FLATTEN_PAYLOAD_CLOSED"] is True
    assert verdict["FLATTEN_ORDER_SIDE"] == "SELL"
    assert verdict["REQUEST_POS_SIDE"] == "OMITTED"
    assert "posSide" not in verdict["VENUE_NATIVE_BODY_KEYS"]
    assert verdict["SEND_TIME_PX_MINTED"] is False
    assert verdict["PRIVATE_AUTH_USED"] is False
    assert verdict["POST_PERFORMED"] is False
    assert verdict["LIVE_EXECUTION"] is False
    assert verdict["PAYLOAD_DETERMINISM_STATUS"] == "PASS"
    assert verdict["EARLIEST_UNRESOLVED_DEPENDENCY"] == EARLIEST_UNRESOLVED_DEPENDENCY
