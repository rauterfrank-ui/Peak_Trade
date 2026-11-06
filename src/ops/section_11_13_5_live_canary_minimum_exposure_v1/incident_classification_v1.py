"""Classify §11.13.5 canary POST HTTP 401 shots without conflating incidents.

A parseable allowlisted OKX `code`/`msg` on one trading POST must not be
rewritten onto a different shot that had no proven incident body, and must
not be attributed to instrument/market GETs. Classification never grants
retry, a second submit, or general Live authority.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

UNPROVEN_FAIL_CLOSED = "UNPROVEN_FAIL_CLOSED"
HISTORICAL_FIRST_401_ROOT_CAUSE = UNPROVEN_FAIL_CLOSED
OKX_50124_OBSERVED_ONESHOT_TRADING_POST = "OKX_50124_OBSERVED_ONESHOT_TRADING_POST"
OKX_50113_INVALID_SIGN = "OKX_50113_INVALID_SIGN"

HTTP_401_WITHOUT_PROVEN_OKX_BODY = UNPROVEN_FAIL_CLOSED
HTTP_401_WITH_PARSEABLE_ALLOWLISTED_OKX_CODE_MSG = "CLASSIFY_EXACT_OBSERVED_OKX_ERROR"
HTTP_401_REQUEST_CLASS_ONESHOT_TRADING_POST = "ONESHOT_TRADING_POST_/api/v5/trade/order"

_EXACT_CODE_CLASSIFICATION: dict[str, str] = {
    "50124": OKX_50124_OBSERVED_ONESHOT_TRADING_POST,
    "50113": OKX_50113_INVALID_SIGN,
}
_OKX_CODE_RE = re.compile(r"^[0-9]{4,6}$")


def classify_canary_post_http_401_root_cause_v1(
    *,
    http_status: int | None,
    json_parse_ok: bool,
    okx_code: str | None,
    okx_msg: str | None = None,
) -> str:
    """Classify one trading-POST response. `okx_msg` is evidence-only, not a mapper."""
    del okx_msg
    if int(http_status or 0) != 401:
        return "NOT_HTTP_401"
    if not json_parse_ok:
        return UNPROVEN_FAIL_CLOSED
    code = str(okx_code or "").strip()
    if not code:
        return UNPROVEN_FAIL_CLOSED
    exact = _EXACT_CODE_CLASSIFICATION.get(code)
    if exact is not None:
        return exact
    if _OKX_CODE_RE.fullmatch(code):
        return f"OKX_{code}_OBSERVED_PARSEABLE_BODY"
    return UNPROVEN_FAIL_CLOSED


def retry_safe_now_from_401_classification_v1(root_cause: str) -> bool:
    del root_cause
    return False


def historical_first_401_root_cause_v1() -> str:
    return HISTORICAL_FIRST_401_ROOT_CAUSE


def attach_canary_post_401_classification_v1(
    payload: dict[str, Any],
    *,
    http_evidence: Mapping[str, Any],
    http_status: int,
) -> dict[str, Any]:
    """Mutate a copy: keep historical first-401 distinct from this POST shot."""
    out = dict(payload)
    if int(http_status) != 401:
        return out
    shot = classify_canary_post_http_401_root_cause_v1(
        http_status=int(http_evidence.get("http_status") or http_status),
        json_parse_ok=bool(http_evidence.get("json_parse_ok")),
        okx_code=(
            None if http_evidence.get("okx_code") is None else str(http_evidence.get("okx_code"))
        ),
        okx_msg=(
            None if http_evidence.get("okx_msg") is None else str(http_evidence.get("okx_msg"))
        ),
    )
    out["POST_401_ROOT_CAUSE"] = shot
    out["HISTORICAL_FIRST_401_ROOT_CAUSE"] = HISTORICAL_FIRST_401_ROOT_CAUSE
    out["HTTP_401_REQUEST_CLASS"] = HTTP_401_REQUEST_CLASS_ONESHOT_TRADING_POST
    out["HTTP_50124_INSTRUMENT_SPECIFIC_PROVEN"] = False
    out["ROOT_CAUSE_PROVEN"] = False
    out["RETRY_SAFE_NOW"] = False
    out["CANARY_RETRY_AUTHORIZED"] = False
    out["GENERAL_LIVE_SUBMIT_UNLOCKED"] = False
    out["LIVE_AUTHORIZED"] = False
    return out
