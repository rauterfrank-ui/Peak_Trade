"""Per-channel classifiers for distinct first-party P08 evidence.

History and risk never become current-position authority. Empty is never
zero. posId is never invented. Canonical P08 CASE_A/B is applied only to
the posId-filtered /account/positions elicitation.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.constants_v1 import (
    CASE_A_TARGET_NONZERO,
    CASE_B_TARGET_ZERO,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    CASE_D_TARGET_NOT_OBSERVED,
    CASE_E_HTTP_OR_OKX_ERROR,
    CASE_F_AMBIGUOUS,
    EMPTY_DATA_IS_ZERO,
    HISTORY_CLASS_AMBIGUOUS_POSID,
    HISTORY_CLASS_EMPTY,
    HISTORY_CLASS_HTTP_OR_OKX_ERROR,
    HISTORY_CLASS_TARGET_NOT_OBSERVED,
    HISTORY_CLASS_TARGET_POSID_ABSENT,
    HISTORY_CLASS_TARGET_POSID_PROVEN,
    HISTORY_EMPTY_IS_CURRENT_ZERO,
    HISTORY_EMPTY_IS_NEVER_HELD,
    HISTORY_EMPTY_IS_ZERO,
    HISTORY_PAGE_LIMIT,
    NEXT_AUTHORITY_BOUNDARY_CASE_A_QTY_NUMERIC_REUSED,
    NEXT_AUTHORITY_BOUNDARY_CASE_A_QTY_UNRESOLVED_REUSED,
    NEXT_AUTHORITY_BOUNDARY_CASE_B_REUSED,
    NEXT_AUTHORITY_BOUNDARY_CASE_E_REUSED,
    NEXT_AUTHORITY_BOUNDARY_CASE_F_REUSED,
    NEXT_AUTHORITY_BOUNDARY_CHANNELS_UNRESOLVED,
    NEXT_AUTHORITY_BOUNDARY_CONTRADICTION,
    RESULT_CLASS_200_OKX_0,
    RISK_CLASS_AMBIGUOUS,
    RISK_CLASS_HTTP_OR_OKX_ERROR,
    RISK_CLASS_POSDATA_EMPTY,
    RISK_CLASS_TARGET_NOT_OBSERVED,
    RISK_CLASS_TARGET_OBSERVED,
    RISK_POSDATA_EMPTY_IS_ZERO,
    TARGET_INSTRUMENT_ID,
)


class P08DistinctFirstPartyClassifyError(RuntimeError):
    """Fail-closed classifier invariant violation."""


def _as_rows(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def extract_target_rows_v1(
    rows: tuple[Mapping[str, Any], ...],
    *,
    instrument_id: str = TARGET_INSTRUMENT_ID,
) -> tuple[Mapping[str, Any], ...]:
    wanted = str(instrument_id or "").strip()
    matched: list[Mapping[str, Any]] = []
    for row in rows:
        if str(row.get("instId") or "").strip() == wanted:
            matched.append(row)
    return tuple(matched)


def extract_target_pos_ids_v1(
    rows: tuple[Mapping[str, Any], ...],
    *,
    instrument_id: str = TARGET_INSTRUMENT_ID,
) -> tuple[str, ...]:
    seen: list[str] = []
    for row in extract_target_rows_v1(rows, instrument_id=instrument_id):
        pos_id = str(row.get("posId") or "").strip()
        if pos_id and pos_id not in seen:
            seen.append(pos_id)
    return tuple(seen)


def pagination_cursor_v1(rows: tuple[Mapping[str, Any], ...]) -> str | None:
    if len(rows) != HISTORY_PAGE_LIMIT:
        return None
    last = rows[-1]
    for key in ("uTime", "cTime"):
        raw = str(last.get(key) or "").strip()
        if raw:
            return raw
    return None


def classify_history_channel_v1(
    *,
    result_class: str,
    payload: Mapping[str, Any] | None,
    instrument_id: str = TARGET_INSTRUMENT_ID,
) -> dict[str, Any]:
    if HISTORY_EMPTY_IS_ZERO or HISTORY_EMPTY_IS_NEVER_HELD or HISTORY_EMPTY_IS_CURRENT_ZERO:
        raise P08DistinctFirstPartyClassifyError("HISTORY_EMPTY_MUST_NOT_BE_PROMOTED")
    if result_class != RESULT_CLASS_200_OKX_0 or payload is None:
        return {
            "CHANNEL": "POSITIONS_HISTORY",
            "CHANNEL_IS_CANONICAL_P08_AUTHORITY": False,
            "HISTORY_OBSERVATION_CLASS": HISTORY_CLASS_HTTP_OR_OKX_ERROR,
            "HISTORY_RESPONSE_OBSERVED": payload is not None,
            "TARGET_HISTORY_ROW_OBSERVED": False,
            "TARGET_POS_ID_PROVEN": False,
            "TARGET_POS_ID": None,
            "TARGET_POS_ID_CANDIDATES": [],
            "HISTORY_EMPTY_IS_NEVER_HELD": False,
            "HISTORY_EMPTY_IS_CURRENT_ZERO": False,
            "HISTORY_IS_CURRENT_STATE": False,
            "DATA_ROW_COUNT": None,
            "TARGET_ROW_COUNT": 0,
            "PAGINATION_TRUNCATED": False,
            "PAGINATION_CURSOR": None,
        }
    data = payload.get("data")
    rows = _as_rows(data)
    target_rows = extract_target_rows_v1(rows, instrument_id=instrument_id)
    pos_ids = extract_target_pos_ids_v1(rows, instrument_id=instrument_id)
    empty = isinstance(data, list) and len(data) == 0
    if empty:
        observation_class = HISTORY_CLASS_EMPTY
    elif not target_rows:
        observation_class = HISTORY_CLASS_TARGET_NOT_OBSERVED
    elif len(pos_ids) == 1:
        observation_class = HISTORY_CLASS_TARGET_POSID_PROVEN
    elif len(pos_ids) > 1:
        observation_class = HISTORY_CLASS_AMBIGUOUS_POSID
    else:
        observation_class = HISTORY_CLASS_TARGET_POSID_ABSENT
    cursor = pagination_cursor_v1(rows)
    return {
        "CHANNEL": "POSITIONS_HISTORY",
        "CHANNEL_IS_CANONICAL_P08_AUTHORITY": False,
        "HISTORY_OBSERVATION_CLASS": observation_class,
        "HISTORY_RESPONSE_OBSERVED": True,
        "TARGET_HISTORY_ROW_OBSERVED": bool(target_rows),
        "TARGET_POS_ID_PROVEN": len(pos_ids) == 1,
        "TARGET_POS_ID": pos_ids[0] if len(pos_ids) == 1 else None,
        "TARGET_POS_ID_CANDIDATES": list(pos_ids),
        "HISTORY_EMPTY_IS_NEVER_HELD": False,
        "HISTORY_EMPTY_IS_CURRENT_ZERO": False,
        "HISTORY_IS_CURRENT_STATE": False,
        "DATA_ROW_COUNT": len(rows) if isinstance(data, list) else None,
        "TARGET_ROW_COUNT": len(target_rows),
        "PAGINATION_TRUNCATED": cursor is not None,
        "PAGINATION_CURSOR": cursor,
    }


def _risk_posdata_rows(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    data = payload.get("data")
    rows = _as_rows(data)
    collected: list[Mapping[str, Any]] = []
    for item in rows:
        pos_data = item.get("posData")
        collected.extend(_as_rows(pos_data))
    return tuple(collected)


def classify_risk_channel_v1(
    *,
    result_class: str,
    payload: Mapping[str, Any] | None,
    instrument_id: str = TARGET_INSTRUMENT_ID,
) -> dict[str, Any]:
    if RISK_POSDATA_EMPTY_IS_ZERO:
        raise P08DistinctFirstPartyClassifyError("RISK_POSDATA_EMPTY_MUST_NOT_BE_PROMOTED_TO_ZERO")
    if result_class != RESULT_CLASS_200_OKX_0 or payload is None:
        return {
            "CHANNEL": "ACCOUNT_POSITION_RISK",
            "CHANNEL_IS_CANONICAL_P08_AUTHORITY": False,
            "RISK_OBSERVATION_CLASS": RISK_CLASS_HTTP_OR_OKX_ERROR,
            "RISK_RESPONSE_OBSERVED": payload is not None,
            "TARGET_RISK_ROW_OBSERVED": False,
            "TARGET_POS_ID_PROVEN": False,
            "TARGET_POS_ID": None,
            "TARGET_POS_ID_CANDIDATES": [],
            "RISK_POSDATA_EMPTY_IS_ZERO": False,
            "RISK_IS_CURRENT_STATE_CROSS_CHECK_ONLY": True,
            "POSDATA_ROW_COUNT": None,
            "TARGET_ROW_COUNT": 0,
        }
    pos_rows = _risk_posdata_rows(payload)
    target_rows = extract_target_rows_v1(pos_rows, instrument_id=instrument_id)
    pos_ids = extract_target_pos_ids_v1(pos_rows, instrument_id=instrument_id)
    data = payload.get("data")
    envelope_empty = isinstance(data, list) and (
        len(data) == 0 or (len(pos_rows) == 0 and all(isinstance(item, Mapping) for item in data))
    )
    if envelope_empty and not target_rows:
        observation_class = RISK_CLASS_POSDATA_EMPTY
    elif not target_rows:
        observation_class = RISK_CLASS_TARGET_NOT_OBSERVED
    elif len(target_rows) > 1 and len(pos_ids) != 1:
        observation_class = RISK_CLASS_AMBIGUOUS
    else:
        observation_class = RISK_CLASS_TARGET_OBSERVED
    return {
        "CHANNEL": "ACCOUNT_POSITION_RISK",
        "CHANNEL_IS_CANONICAL_P08_AUTHORITY": False,
        "RISK_OBSERVATION_CLASS": observation_class,
        "RISK_RESPONSE_OBSERVED": True,
        "TARGET_RISK_ROW_OBSERVED": bool(target_rows),
        "TARGET_POS_ID_PROVEN": len(pos_ids) == 1,
        "TARGET_POS_ID": pos_ids[0] if len(pos_ids) == 1 else None,
        "TARGET_POS_ID_CANDIDATES": list(pos_ids),
        "RISK_POSDATA_EMPTY_IS_ZERO": False,
        "RISK_IS_CURRENT_STATE_CROSS_CHECK_ONLY": True,
        "POSDATA_ROW_COUNT": len(pos_rows),
        "TARGET_ROW_COUNT": len(target_rows),
    }


def merge_independently_proven_pos_ids_v1(
    *candidate_groups: tuple[str, ...],
) -> tuple[str, ...]:
    seen: list[str] = []
    for group in candidate_groups:
        for item in group:
            text = str(item or "").strip()
            if text and text not in seen:
                seen.append(text)
    return tuple(seen)


def synthesize_package_v1(
    *,
    history: Mapping[str, Any] | None,
    risk: Mapping[str, Any] | None,
    positions: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Synthesize only after independent channel adjudications."""
    if EMPTY_DATA_IS_ZERO:
        raise P08DistinctFirstPartyClassifyError("EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO")
    history_ids = tuple(history.get("TARGET_POS_ID_CANDIDATES") or []) if history else ()
    risk_ids = tuple(risk.get("TARGET_POS_ID_CANDIDATES") or []) if risk else ()
    merged_ids = merge_independently_proven_pos_ids_v1(history_ids, risk_ids)
    unique_pos_id = merged_ids[0] if len(merged_ids) == 1 else None
    pos_id_proven = unique_pos_id is not None

    positions_class = str((positions or {}).get("POSITION_OBSERVATION_CLASS") or "")
    positions_nonzero = bool((positions or {}).get("TARGET_POSITION_NONZERO_PROVEN"))
    positions_zero = bool((positions or {}).get("TARGET_POSITION_ZERO_PROVEN"))
    positions_observed = bool((positions or {}).get("TARGET_INSTRUMENT_ROW_OBSERVED"))

    history_class = str((history or {}).get("HISTORY_OBSERVATION_CLASS") or "")
    risk_class = str((risk or {}).get("RISK_OBSERVATION_CLASS") or "")
    history_error = history_class == HISTORY_CLASS_HTTP_OR_OKX_ERROR
    risk_error = risk_class == RISK_CLASS_HTTP_OR_OKX_ERROR
    positions_error = positions_class == CASE_E_HTTP_OR_OKX_ERROR

    contradiction = False
    if positions_nonzero and positions_zero:
        contradiction = True
    if history_class == HISTORY_CLASS_AMBIGUOUS_POSID and pos_id_proven:
        contradiction = True
    if (
        risk_class == RISK_CLASS_TARGET_OBSERVED
        and positions is not None
        and not positions_observed
        and positions_class == CASE_C_EMPTY_DATA_NOT_ZERO
    ):
        contradiction = True

    if contradiction:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_F_AMBIGUOUS,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": positions_observed
            or bool((history or {}).get("TARGET_HISTORY_ROW_OBSERVED"))
            or bool((risk or {}).get("TARGET_RISK_ROW_OBSERVED")),
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_CONTRADICTORY_DISTINCT_CHANNELS",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CONTRADICTION,
            "TARGET_POS_ID_PROVEN": False,
            "TARGET_POS_ID": None,
            "TARGET_POS_ID_CANDIDATES": list(merged_ids),
            "CANONICAL_CURRENT_STATE_SURFACE": "ACCOUNT_POSITIONS_POSID_ELICITATION",
            "HISTORY_PROMOTED_TO_CURRENT_STATE": False,
            "RISK_PROMOTED_TO_CANONICAL_AUTHORITY": False,
        }

    if positions_class == CASE_A_TARGET_NONZERO or positions_nonzero:
        qty_pass = str((positions or {}).get("TARGET_POSITION_QTY_NUMERIC") or "") == "PASS"
        return {
            "POSITION_OBSERVATION_CLASS": CASE_A_TARGET_NONZERO,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": True,
            "POSITION_STATE_OBSERVED": True,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": True,
            "P08_CLOSED": True,
            "P08_VERDICT": "P08_CLOSED_UNIQUE_TARGET_NONZERO_ROW_POSID_ELICITATION_THIS_WINDOW",
            "NEXT_AUTHORITY_BOUNDARY": (
                NEXT_AUTHORITY_BOUNDARY_CASE_A_QTY_NUMERIC_REUSED
                if qty_pass
                else NEXT_AUTHORITY_BOUNDARY_CASE_A_QTY_UNRESOLVED_REUSED
            ),
            "TARGET_POS_ID_PROVEN": pos_id_proven,
            "TARGET_POS_ID": unique_pos_id,
            "TARGET_POS_ID_CANDIDATES": list(merged_ids),
            "CANONICAL_CURRENT_STATE_SURFACE": "ACCOUNT_POSITIONS_POSID_ELICITATION",
            "HISTORY_PROMOTED_TO_CURRENT_STATE": False,
            "RISK_PROMOTED_TO_CANONICAL_AUTHORITY": False,
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
            "P08_VERDICT": "P08_NOT_CLOSED_ZERO_ROW_DOES_NOT_SATISFY_NONZERO_PROOF",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_B_REUSED,
            "TARGET_POS_ID_PROVEN": pos_id_proven,
            "TARGET_POS_ID": unique_pos_id,
            "TARGET_POS_ID_CANDIDATES": list(merged_ids),
            "CANONICAL_CURRENT_STATE_SURFACE": "ACCOUNT_POSITIONS_POSID_ELICITATION",
            "HISTORY_PROMOTED_TO_CURRENT_STATE": False,
            "RISK_PROMOTED_TO_CANONICAL_AUTHORITY": False,
        }

    if positions_class == CASE_F_AMBIGUOUS:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_F_AMBIGUOUS,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_AMBIGUOUS_OR_CONTRADICTORY_ROWS",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_F_REUSED,
            "TARGET_POS_ID_PROVEN": pos_id_proven,
            "TARGET_POS_ID": unique_pos_id,
            "TARGET_POS_ID_CANDIDATES": list(merged_ids),
            "CANONICAL_CURRENT_STATE_SURFACE": "ACCOUNT_POSITIONS_POSID_ELICITATION",
            "HISTORY_PROMOTED_TO_CURRENT_STATE": False,
            "RISK_PROMOTED_TO_CANONICAL_AUTHORITY": False,
        }

    if history_error or risk_error or positions_error:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_E_HTTP_OR_OKX_ERROR,
            "POSITION_RESPONSE_OBSERVED": bool(history or risk or positions),
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_HTTP_OR_OKX_OR_TRANSPORT_ERROR",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_E_REUSED,
            "TARGET_POS_ID_PROVEN": False,
            "TARGET_POS_ID": None,
            "TARGET_POS_ID_CANDIDATES": list(merged_ids),
            "CANONICAL_CURRENT_STATE_SURFACE": "ACCOUNT_POSITIONS_POSID_ELICITATION",
            "HISTORY_PROMOTED_TO_CURRENT_STATE": False,
            "RISK_PROMOTED_TO_CANONICAL_AUTHORITY": False,
        }

    if positions_class == CASE_D_TARGET_NOT_OBSERVED:
        package_class = CASE_D_TARGET_NOT_OBSERVED
        verdict = "P08_NOT_CLOSED_TARGET_INSTRUMENT_NOT_OBSERVED_ON_POSID_ELICITATION"
    elif positions_class == CASE_C_EMPTY_DATA_NOT_ZERO:
        package_class = CASE_C_EMPTY_DATA_NOT_ZERO
        verdict = "P08_NOT_CLOSED_POSID_ELICITATION_EMPTY_REMAINS_NOT_ZERO"
    else:
        package_class = CASE_C_EMPTY_DATA_NOT_ZERO
        verdict = "P08_NOT_CLOSED_DISTINCT_CHANNELS_DO_NOT_PROVE_CURRENT_ZERO_OR_NONZERO"

    return {
        "POSITION_OBSERVATION_CLASS": package_class,
        "POSITION_RESPONSE_OBSERVED": True,
        "TARGET_INSTRUMENT_ROW_OBSERVED": bool(positions_observed),
        "POSITION_STATE_OBSERVED": False,
        "TARGET_POSITION_ZERO_PROVEN": False,
        "TARGET_POSITION_NONZERO_PROVEN": False,
        "P08_CLOSED": False,
        "P08_VERDICT": verdict,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CHANNELS_UNRESOLVED,
        "TARGET_POS_ID_PROVEN": pos_id_proven,
        "TARGET_POS_ID": unique_pos_id,
        "TARGET_POS_ID_CANDIDATES": list(merged_ids),
        "CANONICAL_CURRENT_STATE_SURFACE": "ACCOUNT_POSITIONS_POSID_ELICITATION",
        "HISTORY_PROMOTED_TO_CURRENT_STATE": False,
        "RISK_PROMOTED_TO_CANONICAL_AUTHORITY": False,
    }
