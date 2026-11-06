"""CURRENT_PRODUCTIVE U01 account-mode adapter v1.

Ratifies raw venue ACCOUNT_MODE evidence field acctLv against the already
proven productive required value "2" and the already proven venue semantic
FUTURES_MODE. OPEN is not CURRENT_PRODUCTIVE U01 authority. The adapter
does not rewrite raw venue evidence.

U01 remains eligibility/context, not a numeric equity term.
Unknown, missing, non-string, unmapped, or non-2 raw values fail closed.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    ELIGIBILITY_FACT_ID,
    REQUIRED_ACCOUNT_MODE,
    REQUIRED_TD_MODE,
    CurrentProductiveAccountEligibilityFactV1,
)

OWNER_GO = "CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION_AND_29P_CONTINUATION_TO_FIRST_REAL_BLOCKER_V1"
SCHEMA_CLASS = "CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_ADAPTER_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
RAW_FIELD = "acctLv"
REQUIRED_RAW_TOKEN = "2"
CANONICAL_SEMANTIC_TOKEN = "FUTURES_MODE"
RETIRED_OPEN_TOKEN = "OPEN"
OPEN_AUTHORITY_STATUS = "RETIRED_NOT_CURRENT_PRODUCTIVE_AUTHORITY"
STATUS_ELIGIBLE = "ELIGIBLE"
STATUS_INELIGIBLE = "INELIGIBLE"
STATUS_FAIL_CLOSED = "FAIL_CLOSED"
VENUE_ALLOWED_RAW_TOKENS: frozenset[str] = frozenset({"1", "2", "3", "4"})
VENUE_SEMANTIC_BY_RAW: dict[str, str] = {
    "1": "SPOT_MODE",
    "2": "FUTURES_MODE",
    "3": "MULTI_CURRENCY_MARGIN",
    "4": "PORTFOLIO_MARGIN",
}


class CurrentProductiveU01AccountModeAdapterError(ValueError):
    """Fail-closed CURRENT_PRODUCTIVE U01 account-mode adapter violation."""


@dataclass(frozen=True)
class CurrentProductiveU01AccountModeAdaptationV1:
    status: str
    raw_field: str
    raw_token: str
    semantic_token: str
    eligible: str
    raw_rewritten: str
    reason_codes: tuple[str, ...]


def _fail(
    *reasons: str,
    raw_token: str = "",
    semantic_token: str = "",
    status: str = STATUS_FAIL_CLOSED,
) -> CurrentProductiveU01AccountModeAdaptationV1:
    unique = tuple(dict.fromkeys(reason for reason in reasons if reason))
    return CurrentProductiveU01AccountModeAdaptationV1(
        status=status,
        raw_field=RAW_FIELD,
        raw_token=raw_token,
        semantic_token=semantic_token,
        eligible=FALSE_TOKEN,
        raw_rewritten=FALSE_TOKEN,
        reason_codes=unique or ("U01_ACCOUNT_MODE_FAIL_CLOSED",),
    )


def adapt_current_productive_u01_account_mode_v1(
    raw_acct_lv: object,
) -> CurrentProductiveU01AccountModeAdaptationV1:
    if REQUIRED_ACCOUNT_MODE != CANONICAL_SEMANTIC_TOKEN:
        raise CurrentProductiveU01AccountModeAdapterError(
            "REQUIRED_ACCOUNT_MODE_MUST_BE_FUTURES_MODE"
        )
    if raw_acct_lv is None:
        return _fail("U01_RAW_ACCT_LV_MISSING")
    if isinstance(raw_acct_lv, bool) or not isinstance(raw_acct_lv, str):
        return _fail("U01_RAW_ACCT_LV_NOT_STRING")
    if raw_acct_lv != raw_acct_lv.strip() or raw_acct_lv == "":
        return _fail("U01_RAW_ACCT_LV_EMPTY")
    if raw_acct_lv == RETIRED_OPEN_TOKEN:
        return _fail("U01_OPEN_IS_NOT_CURRENT_PRODUCTIVE_AUTHORITY", raw_token=raw_acct_lv)
    if raw_acct_lv not in VENUE_ALLOWED_RAW_TOKENS:
        return _fail("U01_RAW_ACCT_LV_UNMAPPED", raw_token=raw_acct_lv)
    semantic = VENUE_SEMANTIC_BY_RAW[raw_acct_lv]
    if raw_acct_lv != REQUIRED_RAW_TOKEN:
        return _fail(
            "U01_RAW_ACCT_LV_NOT_REQUIRED_2",
            raw_token=raw_acct_lv,
            semantic_token=semantic,
            status=STATUS_INELIGIBLE,
        )
    if semantic != CANONICAL_SEMANTIC_TOKEN:
        return _fail(
            "U01_SEMANTIC_TOKEN_MISMATCH",
            raw_token=raw_acct_lv,
            semantic_token=semantic,
        )
    return CurrentProductiveU01AccountModeAdaptationV1(
        status=STATUS_ELIGIBLE,
        raw_field=RAW_FIELD,
        raw_token=raw_acct_lv,
        semantic_token=semantic,
        eligible=TRUE_TOKEN,
        raw_rewritten=FALSE_TOKEN,
        reason_codes=("U01_ACCT_LV_2_MAPS_TO_FUTURES_MODE",),
    )


def extract_raw_acct_lv_from_account_config_payload_v1(
    payload: Mapping[str, Any] | None,
) -> CurrentProductiveU01AccountModeAdaptationV1:
    if not isinstance(payload, Mapping):
        return _fail("U01_CONFIG_PAYLOAD_MISSING")
    code = payload.get("code")
    if code is None:
        return _fail("U01_VENUE_CODE_MISSING")
    if not isinstance(code, str) or code != "0":
        return _fail("U01_VENUE_CODE_UNSUCCESSFUL", raw_token="")
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return _fail("U01_CONFIG_DATA_MISSING")
    objects = [item for item in data if isinstance(item, Mapping)]
    if not objects:
        return _fail("U01_CONFIG_OBJECT_MISSING")
    if len(objects) != 1:
        return _fail("U01_CONFIG_OBJECT_AMBIGUOUS")
    row = objects[0]
    if RAW_FIELD not in row:
        return _fail("U01_RAW_ACCT_LV_MISSING")
    return adapt_current_productive_u01_account_mode_v1(row.get(RAW_FIELD))


def build_current_productive_u01_eligibility_fact_v1(
    *,
    adaptation: CurrentProductiveU01AccountModeAdaptationV1,
    bound_account_identity: str,
    bound_venue_identity: str,
    bound_td_mode: str,
    decision_epoch: str,
    provenance_digest: str,
) -> CurrentProductiveAccountEligibilityFactV1 | None:
    if adaptation.eligible != TRUE_TOKEN:
        return None
    if adaptation.semantic_token != CANONICAL_SEMANTIC_TOKEN:
        return None
    if adaptation.raw_rewritten != FALSE_TOKEN:
        raise CurrentProductiveU01AccountModeAdapterError("U01_RAW_REWRITE_FORBIDDEN")
    account = str(bound_account_identity or "").strip()
    venue = str(bound_venue_identity or "").strip()
    td_mode = str(bound_td_mode or "").strip()
    epoch = str(decision_epoch or "").strip()
    digest = str(provenance_digest or "").strip()
    if not account or not venue or not epoch or not digest:
        return None
    if td_mode != REQUIRED_TD_MODE:
        return None
    return CurrentProductiveAccountEligibilityFactV1(
        fact_id=ELIGIBILITY_FACT_ID,
        account_mode=adaptation.semantic_token,
        bound_account_identity=account,
        bound_venue_identity=venue,
        bound_td_mode=td_mode,
        decision_epoch=epoch,
        provenance_digest=digest,
    )
