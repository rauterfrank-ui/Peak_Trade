"""Post-submit position reconciliation for the §11.14 flatten harness.

Reuses extract_pre_existing_position_v1 and 11.13.5 empty-data-is-not-zero.
Does not GET. Does not POST. Caller injects payload or leaves recon unexecuted.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.constants_v1 import (
    CASE_B_TARGET_ZERO,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    EMPTY_DATA_IS_ZERO_VALUE,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    INSTRUMENT_ID,
)
from src.ops.section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1.orchestrator_v1 import (
    extract_pre_existing_position_v1,
)


class FlattenPositionReconError(RuntimeError):
    """Fail-closed flatten position-recon violation."""


FLAT_CONFIRMED = "FLAT_CONFIRMED"
RESIDUAL_POSITION = "RESIDUAL_POSITION"
POSITION_RECON_AMBIGUOUS = "POSITION_RECON_AMBIGUOUS"
POSITION_RECON_FAILED = "POSITION_RECON_FAILED"
POSITION_RECON_NOT_EXECUTED = "POSITION_RECON_NOT_EXECUTED"


def evaluate_flatten_position_recon_v1(
    *,
    payload: Mapping[str, Any] | None,
    instrument_id: str = INSTRUMENT_ID,
    get_performed: bool = False,
) -> dict[str, Any]:
    """Classify injected positions payload. empty data is not zero."""
    if EMPTY_DATA_IS_ZERO_VALUE:
        raise FlattenPositionReconError("EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO")
    if get_performed is not True or payload is None:
        return {
            "outcome": POSITION_RECON_NOT_EXECUTED,
            "GET_PERFORMED": False,
            "second_submit_allowed": False,
            "retry_allowed": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "reason": "RECON_NOT_EXECUTED_NO_GET",
        }
    if str(payload.get("code") or "") != "0":
        return {
            "outcome": POSITION_RECON_FAILED,
            "GET_PERFORMED": True,
            "second_submit_allowed": False,
            "retry_allowed": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "reason": "POSITION_PAYLOAD_NOT_OK",
            "POSITION_OBSERVATION_CLASS": "CASE_E_HTTP_OR_OKX_ERROR",
        }
    data = payload.get("data")
    if isinstance(data, list) and len(data) == 0:
        return {
            "outcome": POSITION_RECON_AMBIGUOUS,
            "GET_PERFORMED": True,
            "second_submit_allowed": False,
            "retry_allowed": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "reason": CASE_C_EMPTY_DATA_NOT_ZERO,
            "POSITION_OBSERVATION_CLASS": CASE_C_EMPTY_DATA_NOT_ZERO,
        }
    extracted = extract_pre_existing_position_v1(payload=payload, instrument_id=instrument_id)
    status = str(extracted.get("status") or "")
    pos = str(extracted.get("pos") or "").strip()
    if status == "AMBIGUOUS_TARGET_ROWS":
        return {
            "outcome": POSITION_RECON_AMBIGUOUS,
            "GET_PERFORMED": True,
            "second_submit_allowed": False,
            "retry_allowed": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "reason": "AMBIGUOUS_TARGET_ROWS",
            "extracted": extracted,
        }
    if status in {"MALFORMED", "POS_FIELD_MISSING"}:
        return {
            "outcome": POSITION_RECON_FAILED,
            "GET_PERFORMED": True,
            "second_submit_allowed": False,
            "retry_allowed": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "reason": status,
            "extracted": extracted,
        }
    if status == "NO_TARGET_ROW":
        return {
            "outcome": POSITION_RECON_AMBIGUOUS,
            "GET_PERFORMED": True,
            "second_submit_allowed": False,
            "retry_allowed": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "reason": "NO_TARGET_ROW_IS_NOT_ZERO",
            "extracted": extracted,
        }
    if status == "OBSERVED" and pos == "0":
        return {
            "outcome": FLAT_CONFIRMED,
            "GET_PERFORMED": True,
            "second_submit_allowed": False,
            "retry_allowed": False,
            "TARGET_POSITION_ZERO_PROVEN": True,
            "reason": CASE_B_TARGET_ZERO,
            "extracted": extracted,
            "POSITION_OBSERVATION_CLASS": CASE_B_TARGET_ZERO,
        }
    if status == "OBSERVED":
        return {
            "outcome": RESIDUAL_POSITION,
            "GET_PERFORMED": True,
            "second_submit_allowed": False,
            "retry_allowed": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "reason": f"RESIDUAL_POS:{pos}",
            "extracted": extracted,
        }
    return {
        "outcome": POSITION_RECON_FAILED,
        "GET_PERFORMED": True,
        "second_submit_allowed": False,
        "retry_allowed": False,
        "TARGET_POSITION_ZERO_PROVEN": False,
        "reason": f"UNCLASSIFIED:{status}",
        "extracted": extracted,
    }
