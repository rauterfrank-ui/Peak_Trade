"""P11 POS_TO_SZ unit-identity independent proof unit tests. Offline only."""

from __future__ import annotations

from decimal import Decimal

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
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.adjudicate_v1 import (
    P11PosToSzAdjudicationError,
    adjudicate_pos_to_sz_unit_identity_v1,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.constants_v1 import (
    CONFLICT_COUNT,
    CURRENT_UNIT_CONTRACT_VALUE,
    EARLIEST_MISSING_QTY_UNIT_PROOF,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_CLOSED,
    P10_CLOSED,
    POS_TO_SZ_UNIT_IDENTITY,
    POST_ALLOWED,
    PRIVATE_AUTH_USED,
    TARGET_POSITION_QTY_UNIT,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.contract_v1 import (
    NUMBER_OF_CONTRACTS,
    PosToSzUnitIdentityError,
    assert_identity_sz_equals_abs_pos_v1,
    assert_pos_to_sz_identity_applicable_v1,
    identity_flatten_sz_from_signed_pos_v1,
    venue_semantic_proof_v1,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.lineage_v1 import (
    LINEAGE_FIELD_NAMES,
    target_position_qty_lineage_v1,
)


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
    assert THIS_SLICE == "11.13.5.P11"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_13_5_P11"
    assert P08_CLOSED is True
    assert P10_CLOSED is True
    assert TARGET_POSITION_QTY_UNIT == "PROVEN"
    assert CURRENT_UNIT_CONTRACT_VALUE == NUMBER_OF_CONTRACTS
    assert POS_TO_SZ_UNIT_IDENTITY == "PROVEN"
    assert EARLIEST_MISSING_QTY_UNIT_PROOF == "NONE_POS_TO_SZ_UNIT_IDENTITY_PROVEN"
    assert THIS_GO_GET_COUNT == 0


def test_official_semantics_are_case_1_identity() -> None:
    proof = venue_semantic_proof_v1()
    assert proof["CASE"] == "CASE_1_SAME_QUANTITY_DOMAIN"
    assert proof["POS_UNIT"] == NUMBER_OF_CONTRACTS
    assert proof["SZ_UNIT"] == NUMBER_OF_CONTRACTS
    assert proof["IDENTITY_OR_CONVERSION"] == "IDENTITY"
    assert proof["ONE_CONTRACT_EQUALS_ONE_SUI"] is False
    assert proof["TGTCCY_APPLICABLE_TO_FUTURES"] is False
    assert proof["CTVAL_IS_NOT_POS_TO_SZ_FACTOR"] is True
    assert proof["INDEPENDENT_VENUE_SEMANTIC_PROOF"] is True


def test_identity_copy_is_abs_signed_pos_not_ctval() -> None:
    assert identity_flatten_sz_from_signed_pos_v1(Decimal("1")) == Decimal("1")
    assert identity_flatten_sz_from_signed_pos_v1(Decimal("-3")) == Decimal("3")
    assert_identity_sz_equals_abs_pos_v1(signed_pos=Decimal("-2"), sz=Decimal("2"))
    with pytest.raises(PosToSzUnitIdentityError, match="SZ_NOT_IDENTITY_ABS_POS"):
        assert_identity_sz_equals_abs_pos_v1(signed_pos=Decimal("1"), sz=Decimal("2"))


def test_spot_margin_and_tgtccy_fail_closed() -> None:
    with pytest.raises(PosToSzUnitIdentityError, match="POS_TO_SZ_IDENTITY_NOT_APPLICABLE:SPOT"):
        assert_pos_to_sz_identity_applicable_v1(
            instrument_id="BTC-USDT",
            inst_type="SPOT",
        )
    with pytest.raises(PosToSzUnitIdentityError, match="POS_TO_SZ_IDENTITY_NOT_APPLICABLE:MARGIN"):
        assert_pos_to_sz_identity_applicable_v1(
            instrument_id="BTC-USDT",
            inst_type="MARGIN",
        )
    with pytest.raises(PosToSzUnitIdentityError, match="TGTCCY_FORBIDDEN_FOR_FUTURES_SZ"):
        assert_pos_to_sz_identity_applicable_v1(
            instrument_id="SUI-USD_UM_XPERP-310404",
            inst_type="FUTURES",
            tgt_ccy="base_ccy",
        )


def test_lineage_rows_have_required_fields_and_proven_pos_sz() -> None:
    rows = target_position_qty_lineage_v1()
    assert len(rows) >= 8
    proven_fields = {
        row["field"]
        for row in rows
        if row["output_unit"] == NUMBER_OF_CONTRACTS
        and row["field"] in {"pos", "signed_pos", "TARGET_POSITION_QTY", "sz"}
    }
    assert "pos" in proven_fields
    assert "sz" in proven_fields
    for row in rows:
        assert tuple(row.keys()) == LINEAGE_FIELD_NAMES


def test_adjudication_proves_identity_without_aliasing_order_plan() -> None:
    verdict = adjudicate_pos_to_sz_unit_identity_v1(origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA)
    assert verdict["TARGET_POSITION_QTY_UNIT"] == "PROVEN"
    assert verdict["CURRENT_UNIT_CONTRACT"] == NUMBER_OF_CONTRACTS
    assert verdict["POS_TO_SZ_UNIT_IDENTITY"] == "PROVEN"
    assert verdict["POS_UNIT"] == NUMBER_OF_CONTRACTS
    assert verdict["SZ_UNIT"] == NUMBER_OF_CONTRACTS
    assert verdict["IDENTITY_OR_CONVERSION"] == "IDENTITY"
    assert verdict["CASE"] == "CASE_1_SAME_QUANTITY_DOMAIN"
    assert verdict["QTY_UNIT_CENSUS_COMPLETE"] is True
    assert verdict["QTY_UNIT_LINEAGE_COMPLETE"] is True
    assert verdict["EARLIEST_MISSING_QTY_UNIT_PROOF"] == EARLIEST_MISSING_QTY_UNIT_PROOF
    assert verdict["EARLIEST_UNRESOLVED_DEPENDENCY"] == EARLIEST_UNRESOLVED_DEPENDENCY
    assert verdict["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY
    assert verdict["CONFLICT_COUNT"] == CONFLICT_COUNT
    assert verdict["ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY"] is True
    assert verdict["ONE_CONTRACT_EQUALS_ONE_SUI"] is False
    assert verdict["NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF"] is True
    assert verdict["CTVAL_IS_NOT_POS_TO_SZ_FACTOR"] is True
    assert verdict["IDENTITY_NOW_INDEPENDENTLY_PROVEN"] is True
    assert verdict["TARGET_POSITION_QTY_NUMERIC"] == "PASS"
    assert verdict["signed_pos"] == "1"
    assert verdict["P08_CLOSED"] is True
    assert verdict["P10_CLOSED"] is True
    assert verdict["POST_PERFORMED"] is False
    assert verdict["GET_PERFORMED_THIS_PERSIST"] is False
    assert verdict["PRIVATE_AUTH_USED"] is False
    assert verdict["LIVE_EXECUTION"] is False
    assert verdict["ORDER_PLAN_QTY_UNIT"] == "contracts"
    assert verdict["ORDER_PLAN_QTY_UNIT"] != verdict["TARGET_POSITION_QTY_UNIT"]
    assert verdict["ORDER_PLAN_QTY_UNIT"] != verdict["CURRENT_UNIT_CONTRACT"]


@pytest.mark.parametrize(
    "claimed",
    [
        "contracts",
        "VENUE_CONTRACT_COUNT",
        "CONTRACTS_SZ",
        "qty",
        "sz",
        "notional",
        "base",
        "minSz",
        "ctVal",
    ],
)
def test_alias_claim_fail_closed(claimed: str) -> None:
    with pytest.raises(P11PosToSzAdjudicationError, match="FORBIDDEN_ALIAS_AS_UNIT"):
        adjudicate_pos_to_sz_unit_identity_v1(
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            claimed_unit=claimed,
        )


def test_wrong_origin_sha_fail_closed() -> None:
    with pytest.raises(P11PosToSzAdjudicationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        adjudicate_pos_to_sz_unit_identity_v1(origin_main_sha="deadbeef")
