"""Per-channel classifiers for P08 identifier-recovery evidence.

Order/fill/algo channels never become current-position authority. Empty is
never zero. posId is never invented. Canonical P08 CASE_A/B is applied only
to the posId-filtered /account/positions elicitation.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.classify_v1 import (
    extract_target_pos_ids_v1,
    extract_target_rows_v1,
    merge_independently_proven_pos_ids_v1,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.constants_v1 import (
    CASE_A_TARGET_NONZERO,
    CASE_B_TARGET_ZERO,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    CASE_D_TARGET_NOT_OBSERVED,
    CASE_E_HTTP_OR_OKX_ERROR,
    CASE_F_AMBIGUOUS,
    CLOSURE_RESULT_CLOSED_NONZERO,
    CLOSURE_RESULT_READ_ONLY_EXHAUSTED,
    EMPTY_DATA_IS_ZERO,
    FILLS_EMPTY_IS_CURRENT_ZERO,
    FILLS_EMPTY_IS_NEVER_HELD,
    ID_CLASS_AMBIGUOUS_POSID,
    ID_CLASS_EMPTY,
    ID_CLASS_HTTP_OR_OKX_ERROR,
    ID_CLASS_TARGET_NOT_OBSERVED,
    ID_CLASS_TARGET_POSID_ABSENT,
    ID_CLASS_TARGET_POSID_PROVEN,
    NEXT_AUTHORITY_BOUNDARY_CONTRADICTION,
    NEXT_AUTHORITY_BOUNDARY_READ_ONLY_EXHAUSTED,
    ORDERS_EMPTY_IS_CURRENT_ZERO,
    ORDERS_EMPTY_IS_NEVER_HELD,
    RESULT_CLASS_200_OKX_0,
    TARGET_INSTRUMENT_ID,
)


class P08ReadOnlyClosureClassifyError(RuntimeError):
    """Fail-closed classifier invariant violation."""


def _as_rows(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def classify_identifier_channel_v1(
    *,
    channel: str,
    result_class: str,
    payload: Mapping[str, Any] | None,
    instrument_id: str = TARGET_INSTRUMENT_ID,
) -> dict[str, Any]:
    if ORDERS_EMPTY_IS_NEVER_HELD or ORDERS_EMPTY_IS_CURRENT_ZERO:
        raise P08ReadOnlyClosureClassifyError("ORDERS_EMPTY_MUST_NOT_BE_PROMOTED")
    if FILLS_EMPTY_IS_NEVER_HELD or FILLS_EMPTY_IS_CURRENT_ZERO:
        raise P08ReadOnlyClosureClassifyError("FILLS_EMPTY_MUST_NOT_BE_PROMOTED")
    if result_class != RESULT_CLASS_200_OKX_0 or payload is None:
        return {
            "CHANNEL": channel,
            "CHANNEL_IS_CANONICAL_P08_AUTHORITY": False,
            "IDENTIFIER_OBSERVATION_CLASS": ID_CLASS_HTTP_OR_OKX_ERROR,
            "CHANNEL_RESPONSE_OBSERVED": payload is not None,
            "TARGET_ROW_OBSERVED": False,
            "TARGET_POS_ID_PROVEN": False,
            "TARGET_POS_ID": None,
            "TARGET_POS_ID_CANDIDATES": [],
            "HISTORICAL_OR_INDIRECT_IS_CURRENT_STATE": False,
            "EMPTY_IS_NEVER_HELD": False,
            "EMPTY_IS_CURRENT_ZERO": False,
            "DATA_ROW_COUNT": None,
            "TARGET_ROW_COUNT": 0,
        }
    data = payload.get("data")
    rows = _as_rows(data)
    target_rows = extract_target_rows_v1(rows, instrument_id=instrument_id)
    pos_ids = extract_target_pos_ids_v1(rows, instrument_id=instrument_id)
    empty = isinstance(data, list) and len(data) == 0
    if empty:
        observation_class = ID_CLASS_EMPTY
    elif not target_rows:
        observation_class = ID_CLASS_TARGET_NOT_OBSERVED
    elif len(pos_ids) == 1:
        observation_class = ID_CLASS_TARGET_POSID_PROVEN
    elif len(pos_ids) > 1:
        observation_class = ID_CLASS_AMBIGUOUS_POSID
    else:
        observation_class = ID_CLASS_TARGET_POSID_ABSENT
    return {
        "CHANNEL": channel,
        "CHANNEL_IS_CANONICAL_P08_AUTHORITY": False,
        "IDENTIFIER_OBSERVATION_CLASS": observation_class,
        "CHANNEL_RESPONSE_OBSERVED": True,
        "TARGET_ROW_OBSERVED": bool(target_rows),
        "TARGET_POS_ID_PROVEN": len(pos_ids) == 1,
        "TARGET_POS_ID": pos_ids[0] if len(pos_ids) == 1 else None,
        "TARGET_POS_ID_CANDIDATES": list(pos_ids),
        "HISTORICAL_OR_INDIRECT_IS_CURRENT_STATE": False,
        "EMPTY_IS_NEVER_HELD": False,
        "EMPTY_IS_CURRENT_ZERO": False,
        "DATA_ROW_COUNT": len(rows) if isinstance(data, list) else None,
        "TARGET_ROW_COUNT": len(target_rows),
    }


def synthesize_read_only_closure_v1(
    *,
    identifier_channels: tuple[Mapping[str, Any], ...],
    positions: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if EMPTY_DATA_IS_ZERO:
        raise P08ReadOnlyClosureClassifyError("EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO")
    groups = tuple(
        tuple(channel.get("TARGET_POS_ID_CANDIDATES") or []) for channel in identifier_channels
    )
    merged_ids = merge_independently_proven_pos_ids_v1(*groups)
    unique_pos_id = merged_ids[0] if len(merged_ids) == 1 else None
    pos_id_proven = unique_pos_id is not None
    identifier_error = any(
        str(channel.get("IDENTIFIER_OBSERVATION_CLASS") or "") == ID_CLASS_HTTP_OR_OKX_ERROR
        for channel in identifier_channels
    )
    positions_class = str((positions or {}).get("POSITION_OBSERVATION_CLASS") or "")
    positions_nonzero = bool((positions or {}).get("TARGET_POSITION_NONZERO_PROVEN"))
    positions_zero = bool((positions or {}).get("TARGET_POSITION_ZERO_PROVEN"))
    positions_observed = bool((positions or {}).get("TARGET_INSTRUMENT_ROW_OBSERVED"))
    positions_error = positions_class == CASE_E_HTTP_OR_OKX_ERROR
    contradiction = bool(positions_nonzero and positions_zero)
    if (
        any(
            str(channel.get("IDENTIFIER_OBSERVATION_CLASS") or "") == ID_CLASS_AMBIGUOUS_POSID
            for channel in identifier_channels
        )
        and pos_id_proven
    ):
        contradiction = True

    if contradiction:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_F_AMBIGUOUS,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": positions_observed,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_READ_ONLY_CLOSURE_RESULT": CLOSURE_RESULT_READ_ONLY_EXHAUSTED,
            "P08_VERDICT": "P08_NOT_CLOSED_CONTRADICTORY_IDENTIFIER_OR_CURRENT_STATE",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CONTRADICTION,
            "TARGET_POS_ID_PROVEN": False,
            "TARGET_POS_ID": None,
            "TARGET_POS_ID_CANDIDATES": list(merged_ids),
            "CANONICAL_CURRENT_STATE_SURFACE": "ACCOUNT_POSITIONS_POSID_ELICITATION",
            "HISTORICAL_OR_INDIRECT_PROMOTED_TO_CURRENT_STATE": False,
        }

    if positions_class == CASE_A_TARGET_NONZERO or positions_nonzero:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_A_TARGET_NONZERO,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": True,
            "POSITION_STATE_OBSERVED": True,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": True,
            "P08_CLOSED": True,
            "P08_READ_ONLY_CLOSURE_RESULT": CLOSURE_RESULT_CLOSED_NONZERO,
            "P08_VERDICT": "P08_CLOSED_UNIQUE_TARGET_NONZERO_ROW_POSID_ELICITATION_THIS_WINDOW",
            "NEXT_AUTHORITY_BOUNDARY": "SEPARATE_OWNER_GO_REQUIRED_BEFORE_EXECUTION_P08_CLOSED_DOES_NOT_AUTHORIZE_SUBMIT",
            "TARGET_POS_ID_PROVEN": pos_id_proven,
            "TARGET_POS_ID": unique_pos_id,
            "TARGET_POS_ID_CANDIDATES": list(merged_ids),
            "CANONICAL_CURRENT_STATE_SURFACE": "ACCOUNT_POSITIONS_POSID_ELICITATION",
            "HISTORICAL_OR_INDIRECT_PROMOTED_TO_CURRENT_STATE": False,
        }

    if positions_class == CASE_B_TARGET_ZERO or positions_zero:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_B_TARGET_ZERO,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": True,
            "POSITION_STATE_OBSERVED": True,
            "TARGET_POSITION_ZERO_PROVEN": True,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_READ_ONLY_CLOSURE_RESULT": CLOSURE_RESULT_READ_ONLY_EXHAUSTED,
            "P08_VERDICT": "P08_NOT_CLOSED_ZERO_ROW_DOES_NOT_SATISFY_NONZERO_PROOF",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_READ_ONLY_EXHAUSTED,
            "TARGET_POS_ID_PROVEN": pos_id_proven,
            "TARGET_POS_ID": unique_pos_id,
            "TARGET_POS_ID_CANDIDATES": list(merged_ids),
            "CANONICAL_CURRENT_STATE_SURFACE": "ACCOUNT_POSITIONS_POSID_ELICITATION",
            "HISTORICAL_OR_INDIRECT_PROMOTED_TO_CURRENT_STATE": False,
        }

    if identifier_error or positions_error:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_E_HTTP_OR_OKX_ERROR,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_READ_ONLY_CLOSURE_RESULT": CLOSURE_RESULT_READ_ONLY_EXHAUSTED,
            "P08_VERDICT": "P08_NOT_CLOSED_HTTP_OR_OKX_OR_TRANSPORT_ERROR",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_READ_ONLY_EXHAUSTED,
            "TARGET_POS_ID_PROVEN": False,
            "TARGET_POS_ID": None,
            "TARGET_POS_ID_CANDIDATES": list(merged_ids),
            "CANONICAL_CURRENT_STATE_SURFACE": "ACCOUNT_POSITIONS_POSID_ELICITATION",
            "HISTORICAL_OR_INDIRECT_PROMOTED_TO_CURRENT_STATE": False,
        }

    if positions_class == CASE_D_TARGET_NOT_OBSERVED:
        package_class = CASE_D_TARGET_NOT_OBSERVED
        verdict = "P08_NOT_CLOSED_TARGET_INSTRUMENT_NOT_OBSERVED_ON_POSID_ELICITATION"
    elif positions_class == CASE_C_EMPTY_DATA_NOT_ZERO:
        package_class = CASE_C_EMPTY_DATA_NOT_ZERO
        verdict = "P08_NOT_CLOSED_POSID_ELICITATION_EMPTY_REMAINS_NOT_ZERO"
    elif positions_class == CASE_F_AMBIGUOUS:
        package_class = CASE_F_AMBIGUOUS
        verdict = "P08_NOT_CLOSED_AMBIGUOUS_OR_CONTRADICTORY_ROWS"
    else:
        package_class = CASE_C_EMPTY_DATA_NOT_ZERO
        verdict = "P08_NOT_CLOSED_READ_ONLY_IDENTIFIER_CHANNELS_DO_NOT_PROVE_CURRENT_NONZERO"

    return {
        "POSITION_OBSERVATION_CLASS": package_class,
        "POSITION_RESPONSE_OBSERVED": True,
        "TARGET_INSTRUMENT_ROW_OBSERVED": positions_observed,
        "POSITION_STATE_OBSERVED": False,
        "TARGET_POSITION_ZERO_PROVEN": False,
        "TARGET_POSITION_NONZERO_PROVEN": False,
        "P08_CLOSED": False,
        "P08_READ_ONLY_CLOSURE_RESULT": CLOSURE_RESULT_READ_ONLY_EXHAUSTED,
        "P08_VERDICT": verdict,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_READ_ONLY_EXHAUSTED,
        "TARGET_POS_ID_PROVEN": pos_id_proven,
        "TARGET_POS_ID": unique_pos_id,
        "TARGET_POS_ID_CANDIDATES": list(merged_ids),
        "CANONICAL_CURRENT_STATE_SURFACE": "ACCOUNT_POSITIONS_POSID_ELICITATION",
        "HISTORICAL_OR_INDIRECT_PROMOTED_TO_CURRENT_STATE": False,
    }
