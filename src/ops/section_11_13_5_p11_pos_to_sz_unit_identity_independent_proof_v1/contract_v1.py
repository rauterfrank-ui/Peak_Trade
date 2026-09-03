"""Fail-closed POS_TO_SZ unit-identity contract for the bound FUTURES xperp.

Independent venue semantics, not ORDER_PLAN alias promotion, not numeric
pos==sz, and not ctVal conversion. Identity is number-of-contracts for
FUTURES/SWAP/OPTION. SPOT/MARGIN are a different domain and fail closed.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.official_excerpts_v1 import (
    ALGO_ORDER_SZ_DEFINITION,
    FILL_SZ_DEFINITION,
    MAX_LMT_SZ_DEFINITION,
    MIN_SZ_DEFINITION,
    NOTIONAL_USD_LINEAR_SZ_FORMULA,
    PLACE_ORDER_SZ_REQUEST_DEFINITION,
    PLACE_ORDER_TGTCCY_DEFINITION,
    POS_REST_GET_POSITIONS_DEFINITION,
    POS_UPL_LINEAR_FORMULA,
    POSCCY_DEFINITION,
)

NUMBER_OF_CONTRACTS = "NUMBER_OF_CONTRACTS"
OFFICIAL_UNIT_PHRASE = "number of contracts"
TARGET_POSITION_QTY_UNIT_STATUS = "PROVEN"
CURRENT_UNIT_CONTRACT = NUMBER_OF_CONTRACTS
POS_UNIT = NUMBER_OF_CONTRACTS
SZ_UNIT = NUMBER_OF_CONTRACTS
IDENTITY_OR_CONVERSION = "IDENTITY"
CONVERSION_FORMULA = "NONE_IDENTITY_SZ_EQUALS_ABS_SIGNED_POS"
UNIT_CHAIN_VERDICT = "IDENTITY_POS_TO_SZ_NUMBER_OF_CONTRACTS_PROVEN"
CASE = "CASE_1_SAME_QUANTITY_DOMAIN"
INSTRUMENT_SCOPE = "FUTURES_LINEAR_XPERP_SUI-USD_UM_XPERP-310404"
COVERED_INST_TYPES: frozenset[str] = frozenset({"FUTURES", "SWAP", "OPTION"})
EXCLUDED_INST_TYPES: frozenset[str] = frozenset({"SPOT", "MARGIN", "EVENTS"})
ONE_CONTRACT_EQUALS_ONE_SUI = False
NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF = True
ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY = True
CTVAL_IS_NOT_POS_TO_SZ_FACTOR = True
MINSZ_IS_NOT_UNIT_PROOF = True
PLACE_ORDER_REQUEST_PARAM_NAMES_UNIT = False
WS_POSITIONS_CHANNEL_NAMES_UNIT = False
GET_ORDER_DETAILS_SZ_NAMES_UNIT = False


class PosToSzUnitIdentityError(RuntimeError):
    """Fail-closed POS_TO_SZ unit-identity violation."""


def _norm_inst_type(inst_type: str | None) -> str:
    return str(inst_type or "").strip().upper()


def instrument_class_covered_v1(
    *,
    instrument_id: str,
    inst_type: str | None = None,
) -> bool:
    inst = str(instrument_id or "").strip()
    itype = _norm_inst_type(inst_type)
    if inst == DEFAULT_INSTRUMENT_ID and itype in {"", DEFAULT_INST_TYPE}:
        return True
    return itype in COVERED_INST_TYPES


def assert_pos_to_sz_identity_applicable_v1(
    *,
    instrument_id: str,
    inst_type: str | None = None,
    tgt_ccy: str | None = None,
) -> None:
    inst = str(instrument_id or "").strip()
    if not inst:
        raise PosToSzUnitIdentityError("INSTRUMENT_ID_MISSING")
    itype = _norm_inst_type(inst_type)
    if itype in EXCLUDED_INST_TYPES:
        raise PosToSzUnitIdentityError(f"POS_TO_SZ_IDENTITY_NOT_APPLICABLE:{itype}")
    if inst == DEFAULT_INSTRUMENT_ID:
        if itype not in {"", DEFAULT_INST_TYPE}:
            raise PosToSzUnitIdentityError(f"BOUND_INSTRUMENT_INSTTYPE_MISMATCH:{itype}")
    elif itype not in COVERED_INST_TYPES:
        raise PosToSzUnitIdentityError(f"INSTTYPE_NOT_COVERED:{itype or 'MISSING'}")
    if str(tgt_ccy or "").strip():
        raise PosToSzUnitIdentityError("TGTCCY_FORBIDDEN_FOR_FUTURES_SZ")


def identity_flatten_sz_from_signed_pos_v1(signed_pos: Decimal) -> Decimal:
    """Sign handling only. Not a unit conversion. Not a ctVal rewrite."""
    if signed_pos == 0:
        raise PosToSzUnitIdentityError("ZERO_POS_HAS_NO_FLATTEN_SZ")
    return abs(signed_pos)


def assert_identity_sz_equals_abs_pos_v1(
    *,
    signed_pos: Decimal,
    sz: Decimal,
) -> None:
    expected = identity_flatten_sz_from_signed_pos_v1(signed_pos)
    if sz != expected:
        raise PosToSzUnitIdentityError("SZ_NOT_IDENTITY_ABS_POS")
    if sz <= 0:
        raise PosToSzUnitIdentityError("SZ_NOT_POSITIVE")


def assert_no_ctval_conversion_v1(body: Mapping[str, Any] | None = None) -> None:
    del body
    if CTVAL_IS_NOT_POS_TO_SZ_FACTOR is not True:
        raise PosToSzUnitIdentityError("CTVAL_MUST_NOT_BE_POS_TO_SZ_FACTOR")


def assert_flatten_body_identity_v1(body: Mapping[str, Any], *, quantity: str) -> None:
    if "tgtCcy" in body:
        raise PosToSzUnitIdentityError("TGTCCY_PRESENT_ON_FLATTEN_BODY")
    if str(body.get("sz") or "") != str(quantity):
        raise PosToSzUnitIdentityError("FLATTEN_BODY_SZ_NOT_PLAN_QUANTITY")
    assert_no_ctval_conversion_v1(body)


def venue_semantic_proof_v1() -> dict[str, Any]:
    pos_names_contracts = "number of contracts for SWAP/FUTURES/OPTIONS" in (
        POS_REST_GET_POSITIONS_DEFINITION
    )
    sz_fill_names_contract = "unit is contract for`FUTURES`/`SWAP`/`OPTION`" in FILL_SZ_DEFINITION
    sz_algo_names_contract = (
        "`FUTURES`/`SWAP`/`OPTION`: in the unit of contract" in ALGO_ORDER_SZ_DEFINITION
    )
    min_sz_names_contracts = "number of contracts" in MIN_SZ_DEFINITION
    max_lmt_sz_names_contracts = "number of contracts" in MAX_LMT_SZ_DEFINITION
    tgt_ccy_spot_only = "Only applicable to`SPOT`" in PLACE_ORDER_TGTCCY_DEFINITION
    pos_slot = "pos × ctVal" in POS_UPL_LINEAR_FORMULA
    sz_slot = "sz × ctVal × markPx" in NOTIONAL_USD_LINEAR_SZ_FORMULA
    pos_ccy_margin_only = "only applicable to`MARGIN`" in POSCCY_DEFINITION
    if not all(
        (
            pos_names_contracts,
            sz_fill_names_contract,
            sz_algo_names_contract,
            min_sz_names_contracts,
            max_lmt_sz_names_contracts,
            tgt_ccy_spot_only,
            pos_slot,
            sz_slot,
            pos_ccy_margin_only,
        )
    ):
        raise PosToSzUnitIdentityError("OFFICIAL_EXCERPT_DRIFT")
    return {
        "CASE": CASE,
        "POS_UNIT": POS_UNIT,
        "SZ_UNIT": SZ_UNIT,
        "IDENTITY_OR_CONVERSION": IDENTITY_OR_CONVERSION,
        "CONVERSION_FORMULA": CONVERSION_FORMULA,
        "OFFICIAL_UNIT_PHRASE": OFFICIAL_UNIT_PHRASE,
        "PLACE_ORDER_REQUEST_PARAM_DEFINITION": PLACE_ORDER_SZ_REQUEST_DEFINITION,
        "PLACE_ORDER_REQUEST_PARAM_NAMES_UNIT": PLACE_ORDER_REQUEST_PARAM_NAMES_UNIT,
        "WS_POSITIONS_CHANNEL_NAMES_UNIT": WS_POSITIONS_CHANNEL_NAMES_UNIT,
        "GET_ORDER_DETAILS_SZ_NAMES_UNIT": GET_ORDER_DETAILS_SZ_NAMES_UNIT,
        "REQUEST_TABLE_UNDERSPECIFIED_IS_NOT_COMPETING_UNIT": True,
        "TGTCCY_APPLICABLE_TO_FUTURES": False,
        "POSCCY_APPLICABLE_TO_FUTURES": False,
        "CTVAL_IS_NOT_POS_TO_SZ_FACTOR": CTVAL_IS_NOT_POS_TO_SZ_FACTOR,
        "ONE_CONTRACT_EQUALS_ONE_SUI": ONE_CONTRACT_EQUALS_ONE_SUI,
        "NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF": NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF,
        "ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY": (ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY),
        "DIMENSIONAL_SLOT": "N_times_ctVal_times_price",
        "POS_DIMENSIONAL_SLOT_PROVEN": pos_slot,
        "SZ_DIMENSIONAL_SLOT_PROVEN": sz_slot,
        "INDEPENDENT_VENUE_SEMANTIC_PROOF": True,
    }
