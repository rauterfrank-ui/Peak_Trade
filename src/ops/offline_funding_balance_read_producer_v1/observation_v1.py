"""Deterministic Funding Account balance observation. No capital actions.

Venue source is GET /api/v5/asset/balances only. This is not
GET /api/v5/account/balance, not totalEq, not available margin, and not a
transfer/withdraw/conversion decision. Absent currency rows are not zero.
USD is not USDC.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.offline_funding_balance_read_producer_v1.constants_v1 import (
    ABSENT_CURRENCY_ROW_ZERO_SEMANTICS_CREATED,
    FUNDING_ACCOUNT_SCOPE,
    FUNDING_BALANCE_ENDPOINT,
    FUNDING_BALANCE_ENDPOINT_METHOD,
    MAX_RAW_DIGIT_LEN,
    ROW_CCY_MAX_LEN,
    SOURCE_ENDPOINT_FIELD,
    TRADING_ACCOUNT_BALANCE_ENDPOINT,
    USD_USDC_COLLAPSED,
    VENUE_ROW_FIELDS,
)

_SCIENTIFIC_NOTATION = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+$")
_FORBIDDEN_HEADER_MARKERS = (
    "authorization",
    "ok-access",
    "cookie",
    "api-key",
    "secret",
    "sign",
    "passphrase",
)

OBSERVATION_CLASS_SUCCESS = "SUCCESS"
OBSERVATION_CLASS_VENUE_ERROR = "VENUE_ERROR"
OBSERVATION_CLASS_AUTH_ERROR = "AUTH_ERROR"
OBSERVATION_CLASS_NETWORK_ERROR = "NETWORK_ERROR"
OBSERVATION_CLASS_MALFORMED = "MALFORMED"
CURRENCY_ROW_STATUS_PRESENT = "PRESENT"
CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO = "ABSENT_NOT_ZERO"
CURRENCY_ROW_NUMERIC_STATUS_NONZERO = "NONZERO"
CURRENCY_ROW_NUMERIC_STATUS_ZERO = "ZERO"
CURRENCY_ROW_NUMERIC_STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"


class FundingAccountBalanceObservationError(RuntimeError):
    """Fail-closed Funding Account balance observation violation."""


@dataclass(frozen=True)
class FundingAccountBalanceRowV1:
    ccy: str
    bal_raw: str
    frozen_bal_raw: str
    avail_bal_raw: str

    def to_dict(self) -> dict[str, str]:
        return {
            "ccy": self.ccy,
            "bal": self.bal_raw,
            "frozenBal": self.frozen_bal_raw,
            "availBal": self.avail_bal_raw,
        }


@dataclass(frozen=True)
class FundingAccountBalanceObservationV1:
    observed_at_utc: str
    venue: str
    rest_host: str
    method: str
    endpoint: str
    source_endpoint: str
    account_scope: str
    trading_account_endpoint: str
    http_status: int
    venue_code: str
    venue_msg: str
    observation_class: str
    row_count: int
    rows: tuple[FundingAccountBalanceRowV1, ...]
    observed_ccys: tuple[str, ...]
    nonzero_ccys: tuple[str, ...]
    usdc_row_status: str
    usd_row_status: str
    other_asset_row_status: str
    usdc_numeric_status: str
    usd_numeric_status: str
    other_asset_numeric_status: str
    body_sha256: str
    get_performed: bool
    auth_header_sent: bool
    transport_class: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "observed_at_utc": self.observed_at_utc,
            "venue": self.venue,
            "rest_host": self.rest_host,
            "method": self.method,
            "endpoint": self.endpoint,
            "source_endpoint": self.source_endpoint,
            "account_scope": self.account_scope,
            "trading_account_endpoint": self.trading_account_endpoint,
            "http_status": self.http_status,
            "venue_code": self.venue_code,
            "venue_msg": self.venue_msg,
            "observation_class": self.observation_class,
            "row_count": self.row_count,
            "rows": [row.to_dict() for row in self.rows],
            "observed_ccys": list(self.observed_ccys),
            "nonzero_ccys": list(self.nonzero_ccys),
            "usdc_row_status": self.usdc_row_status,
            "usd_row_status": self.usd_row_status,
            "other_asset_row_status": self.other_asset_row_status,
            "usdc_numeric_status": self.usdc_numeric_status,
            "usd_numeric_status": self.usd_numeric_status,
            "other_asset_numeric_status": self.other_asset_numeric_status,
            "body_sha256": self.body_sha256,
            "get_performed": self.get_performed,
            "auth_header_sent": self.auth_header_sent,
            "transport_class": self.transport_class,
            "ABSENT_CURRENCY_ROW_IS_NOT_ZERO": True,
            "ABSENT_CURRENCY_ROW_ZERO_SEMANTICS_CREATED": (
                ABSENT_CURRENCY_ROW_ZERO_SEMANTICS_CREATED
            ),
            "USD_USDC_COLLAPSED": USD_USDC_COLLAPSED,
            "EMPTY_DATA_IS_NOT_ZERO": True,
            "FUNDING_ACCOUNT_IS_NOT_TRADING_ACCOUNT": True,
            "AVAILBAL_IS_NOT_TRANSFER_AUTHORITY": True,
            "AVAILBAL_IS_NOT_AVAILABLE_MARGIN": True,
            "BAL_IS_NOT_ACCOUNT_TOTAL_EQ": True,
            "CAPITAL_NEXT_STEP_EMITTED": False,
            "SECRET_VALUES_INCLUDED": False,
        }


def _require_non_negative_decimal(raw: Any, *, field: str) -> Decimal:
    if raw is None:
        raise FundingAccountBalanceObservationError(f"FUNDING_BALANCE_FIELD_NULL:{field}")
    text = str(raw).strip()
    if not text:
        raise FundingAccountBalanceObservationError(f"FUNDING_BALANCE_FIELD_EMPTY:{field}")
    lowered = text.lower()
    if lowered in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
        raise FundingAccountBalanceObservationError(f"FUNDING_BALANCE_FIELD_NON_NUMERIC:{field}")
    if _SCIENTIFIC_NOTATION.fullmatch(text) or len(text) > MAX_RAW_DIGIT_LEN:
        raise FundingAccountBalanceObservationError(f"FUNDING_BALANCE_FIELD_OUT_OF_DOMAIN:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise FundingAccountBalanceObservationError(
            f"FUNDING_BALANCE_FIELD_NON_NUMERIC:{field}"
        ) from exc
    if value.is_nan() or value.is_infinite():
        raise FundingAccountBalanceObservationError(f"FUNDING_BALANCE_FIELD_NON_NUMERIC:{field}")
    if value < 0:
        raise FundingAccountBalanceObservationError(f"FUNDING_BALANCE_FIELD_NEGATIVE:{field}")
    return value


def _require_ccy(raw: Any) -> str:
    if raw is None:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_FIELD_NULL:ccy")
    text = str(raw).strip()
    if not text:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_FIELD_EMPTY:ccy")
    if len(text) > ROW_CCY_MAX_LEN:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_FIELD_OUT_OF_DOMAIN:ccy")
    if text != str(raw).strip():
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_CCY_NOT_EXACT")
    return text


def _parse_row(item: Any, *, index: int) -> tuple[FundingAccountBalanceRowV1, Decimal]:
    if not isinstance(item, Mapping):
        raise FundingAccountBalanceObservationError(f"FUNDING_BALANCE_ROW_NOT_OBJECT:{index}")
    ccy = _require_ccy(item.get("ccy"))
    bal_raw = str(item.get("bal") if item.get("bal") is not None else "").strip()
    frozen_raw = str(item.get("frozenBal") if item.get("frozenBal") is not None else "").strip()
    avail_raw = str(item.get("availBal") if item.get("availBal") is not None else "").strip()
    for field_name, raw in (
        ("bal", item.get("bal")),
        ("frozenBal", item.get("frozenBal")),
        ("availBal", item.get("availBal")),
    ):
        _require_non_negative_decimal(raw, field=f"{field_name}[{ccy}]")
    if "ccy" not in item:
        raise FundingAccountBalanceObservationError(f"FUNDING_BALANCE_ROW_MISSING_CCY:{index}")
    missing = [name for name in VENUE_ROW_FIELDS if name not in item]
    if missing:
        raise FundingAccountBalanceObservationError(
            f"FUNDING_BALANCE_ROW_MISSING_FIELDS:{ccy}:{','.join(missing)}"
        )
    bal = _require_non_negative_decimal(item.get("bal"), field=f"bal[{ccy}]")
    return (
        FundingAccountBalanceRowV1(
            ccy=ccy,
            bal_raw=bal_raw if item.get("bal") is not None else str(item.get("bal")),
            frozen_bal_raw=frozen_raw,
            avail_bal_raw=avail_raw,
        ),
        bal,
    )


def _row_status(present: bool) -> str:
    if present:
        return CURRENCY_ROW_STATUS_PRESENT
    return CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO


def _numeric_status(*, present: bool, nonzero: bool) -> str:
    if not present:
        return CURRENCY_ROW_NUMERIC_STATUS_NOT_APPLICABLE
    if nonzero:
        return CURRENCY_ROW_NUMERIC_STATUS_NONZERO
    return CURRENCY_ROW_NUMERIC_STATUS_ZERO


def _auth_header_sent(headers: Mapping[str, str] | None) -> bool:
    for key in dict(headers or {}):
        lowered = str(key).strip().lower()
        if lowered.startswith("ok-access-") or lowered in _FORBIDDEN_HEADER_MARKERS:
            return True
    return False


def classify_funding_balance_envelope_v1(
    *,
    http_status: int,
    payload: Mapping[str, Any] | None,
) -> str:
    status = int(http_status)
    if status in {401, 403}:
        return OBSERVATION_CLASS_AUTH_ERROR
    if status != 200:
        return OBSERVATION_CLASS_NETWORK_ERROR
    if not isinstance(payload, Mapping):
        return OBSERVATION_CLASS_MALFORMED
    code = str(payload.get("code") or "").strip()
    if code != "0":
        return OBSERVATION_CLASS_VENUE_ERROR
    data = payload.get("data")
    if not isinstance(data, list):
        return OBSERVATION_CLASS_MALFORMED
    return OBSERVATION_CLASS_SUCCESS


def parse_funding_account_balance_observation_v1(
    *,
    body_bytes: bytes,
    http_status: int,
    observed_at_utc: str,
    venue: str,
    rest_host: str,
    endpoint: str,
    headers: Mapping[str, str] | None = None,
    transport_class: str,
    get_performed: bool,
) -> FundingAccountBalanceObservationV1:
    if "?" in str(endpoint or ""):
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_QUERY_FORBIDDEN")
    if str(endpoint or "").strip() != FUNDING_BALANCE_ENDPOINT:
        raise FundingAccountBalanceObservationError(f"FUNDING_BALANCE_ENDPOINT_MISMATCH:{endpoint}")
    raw = body_bytes or b""
    body_sha256 = hashlib.sha256(raw).hexdigest()
    try:
        payload: Any = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_MALFORMED_ENVELOPE") from exc
    if not isinstance(payload, Mapping):
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_MALFORMED_ENVELOPE")
    observation_class = classify_funding_balance_envelope_v1(
        http_status=http_status,
        payload=payload,
    )
    venue_code = str(payload.get("code") if payload.get("code") is not None else "")
    venue_msg = str(payload.get("msg") if payload.get("msg") is not None else "")[:200]
    if observation_class == OBSERVATION_CLASS_AUTH_ERROR:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_AUTH_ERROR")
    if observation_class == OBSERVATION_CLASS_NETWORK_ERROR:
        raise FundingAccountBalanceObservationError(
            f"FUNDING_BALANCE_HTTP_UNSUCCESSFUL:{http_status}"
        )
    if observation_class == OBSERVATION_CLASS_VENUE_ERROR:
        raise FundingAccountBalanceObservationError(
            f"FUNDING_BALANCE_VENUE_CODE_UNSUCCESSFUL:{venue_code}"
        )
    if observation_class != OBSERVATION_CLASS_SUCCESS:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_MALFORMED_ENVELOPE")
    data = payload.get("data")
    if not isinstance(data, list):
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_MALFORMED_ENVELOPE")
    rows: list[FundingAccountBalanceRowV1] = []
    nonzero: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(data):
        row, bal = _parse_row(item, index=index)
        if row.ccy in seen:
            raise FundingAccountBalanceObservationError(f"FUNDING_BALANCE_DUPLICATE_CCY:{row.ccy}")
        seen.add(row.ccy)
        rows.append(row)
        if bal > 0:
            nonzero.append(row.ccy)
    observed_ccys = tuple(row.ccy for row in rows)
    frozen_rows = tuple(rows)
    usdc_present = "USDC" in seen
    usd_present = "USD" in seen
    other_present = bool(seen - {"USDC", "USD"})
    usdc_nonzero = "USDC" in nonzero
    usd_nonzero = "USD" in nonzero
    other_nonzero = bool(set(nonzero) - {"USDC", "USD"})
    return FundingAccountBalanceObservationV1(
        observed_at_utc=str(observed_at_utc),
        venue=str(venue),
        rest_host=str(rest_host),
        method=FUNDING_BALANCE_ENDPOINT_METHOD,
        endpoint=FUNDING_BALANCE_ENDPOINT,
        source_endpoint=SOURCE_ENDPOINT_FIELD,
        account_scope=FUNDING_ACCOUNT_SCOPE,
        trading_account_endpoint=TRADING_ACCOUNT_BALANCE_ENDPOINT,
        http_status=int(http_status),
        venue_code=venue_code,
        venue_msg=venue_msg,
        observation_class=observation_class,
        row_count=len(frozen_rows),
        rows=frozen_rows,
        observed_ccys=observed_ccys,
        nonzero_ccys=tuple(nonzero),
        usdc_row_status=_row_status(usdc_present),
        usd_row_status=_row_status(usd_present),
        other_asset_row_status=_row_status(other_present),
        usdc_numeric_status=_numeric_status(present=usdc_present, nonzero=usdc_nonzero),
        usd_numeric_status=_numeric_status(present=usd_present, nonzero=usd_nonzero),
        other_asset_numeric_status=_numeric_status(present=other_present, nonzero=other_nonzero),
        body_sha256=body_sha256,
        get_performed=bool(get_performed),
        auth_header_sent=_auth_header_sent(headers),
        transport_class=str(transport_class),
    )


def row_for_ccy_v1(
    observation: FundingAccountBalanceObservationV1,
    ccy: str,
) -> FundingAccountBalanceRowV1 | None:
    wanted = str(ccy)
    for row in observation.rows:
        if row.ccy == wanted:
            return row
    return None
