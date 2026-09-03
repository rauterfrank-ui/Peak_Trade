"""P10 TARGET_POSITION_QTY unit forensic adjudication unit tests. Offline only."""

from __future__ import annotations

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
from src.ops.section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1.adjudicate_v1 import (
    P10QtyUnitAdjudicationError,
    adjudicate_target_position_qty_unit_v1,
)
from src.ops.section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1.constants_v1 import (
    CONFLICT_COUNT,
    CURRENT_UNIT_CONTRACT,
    EARLIEST_MISSING_QTY_UNIT_PROOF,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_CLOSED,
    POST_ALLOWED,
    TARGET_POSITION_QTY_UNIT,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
)
from src.ops.section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1.lineage_v1 import (
    LINEAGE_FIELD_NAMES,
    target_position_qty_lineage_v1,
)


def test_owner_go_is_forbidden_flatten_and_does_not_authorize_runtime() -> None:
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert POST_ALLOWED is False
    assert GET_ALLOWED is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert THIS_SLICE == "11.13.5.P10"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_13_5_P10"
    assert P08_CLOSED is True
    assert TARGET_POSITION_QTY_UNIT == "UNPROVEN"
    assert CURRENT_UNIT_CONTRACT == "UNPROVEN"
    assert EARLIEST_MISSING_QTY_UNIT_PROOF == "POS_TO_SZ_UNIT_IDENTITY"
    assert THIS_GO_GET_COUNT == 0


def test_lineage_rows_have_required_fields_and_no_proven_target_unit() -> None:
    rows = target_position_qty_lineage_v1()
    assert len(rows) >= 16
    for row in rows:
        assert tuple(row.keys()) == LINEAGE_FIELD_NAMES
        if row["field"] in {
            "TARGET_POSITION_QTY_UNIT",
            "TARGET_POSITION_QTY_RAW",
            "signed_pos",
            "pos",
            "candidate_flatten_qty",
            "sz",
        }:
            assert row["output_unit"] in {
                "UNPROVEN",
                "PASSTHROUGH_POS_TO_SZ_UNIT_IDENTITY_UNPROVEN",
                "NOT_AVAILABLE",
            }


def test_adjudication_preserves_unproven_and_does_not_alias_order_plan() -> None:
    verdict = adjudicate_target_position_qty_unit_v1(origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA)
    assert verdict["TARGET_POSITION_QTY_UNIT"] == "UNPROVEN"
    assert verdict["CURRENT_UNIT_CONTRACT"] == "UNPROVEN"
    assert verdict["QTY_UNIT_CENSUS_COMPLETE"] is True
    assert verdict["QTY_UNIT_LINEAGE_COMPLETE"] is True
    assert verdict["EARLIEST_MISSING_QTY_UNIT_PROOF"] == EARLIEST_MISSING_QTY_UNIT_PROOF
    assert verdict["EARLIEST_UNRESOLVED_DEPENDENCY"] == EARLIEST_UNRESOLVED_DEPENDENCY
    assert verdict["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY
    assert verdict["CONFLICT_COUNT"] == CONFLICT_COUNT
    assert verdict["ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY"] is True
    assert verdict["SUI_OPERATIVE_ORDER_SZ_IS_NOT_TARGET_POSITION_QTY"] is True
    assert verdict["ONE_CONTRACT_EQUALS_ONE_SUI"] is False
    assert verdict["NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF"] is True
    assert verdict["IMPLICIT_PASSTHROUGH_PRESENT"] is True
    assert verdict["IMPLICIT_PASSTHROUGH_IS_NOT_UNIT_PROOF"] is True
    assert verdict["POSCCY_PRESENT_IN_AUTHORIZED_P08_CAPTURE"] is False
    assert verdict["TARGET_POSITION_QTY_NUMERIC"] == "PASS"
    assert verdict["signed_pos"] == "1"
    assert verdict["P08_CLOSED"] is True
    assert verdict["POST_PERFORMED"] is False
    assert verdict["GET_PERFORMED_THIS_PERSIST"] is False
    assert verdict["LIVE_EXECUTION"] is False
    assert verdict["UNIT_CHAIN_VERDICT"] == "PASSTHROUGH_POS_TO_SZ_UNIT_IDENTITY_UNPROVEN"
    assert verdict["ORDER_PLAN_QTY_UNIT"] == "contracts"
    assert verdict["ORDER_PLAN_QTY_UNIT"] != verdict["TARGET_POSITION_QTY_UNIT"]


@pytest.mark.parametrize(
    "claimed",
    [
        "contracts",
        "VENUE_CONTRACT_COUNT",
        "CONTRACTS_SZ",
        "qty",
        "sz",
        "notional",
        "PROVEN",
        "base",
    ],
)
def test_alias_or_proven_claim_fail_closed(claimed: str) -> None:
    with pytest.raises(P10QtyUnitAdjudicationError, match="FORBIDDEN_"):
        adjudicate_target_position_qty_unit_v1(
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            claimed_unit=claimed,
        )


def test_wrong_origin_sha_fail_closed() -> None:
    with pytest.raises(P10QtyUnitAdjudicationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        adjudicate_target_position_qty_unit_v1(origin_main_sha="deadbeef")
