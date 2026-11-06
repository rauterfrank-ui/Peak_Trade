"""Current execution-readiness snapshot from already-authoritative sources.

Reuses Z2DP create-readiness, P08 observation packs, and standing fail-closed
constants. Does not GET. Does not POST. Historical packs remain historical.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.constants_v1 import (
    AUTHORIZED_HOST,
    BOUND_ACCOUNT_SCOPE,
    GET_NOT_REQUIRED_REASON,
    G_POSMODE_RESULT_CLASS_BOUND,
    G_POSMODE_STATUS_BOUND,
    G_POSMODE_STATUS_CLOSED_AS_BOUND,
    G_POSMODE_SUBMIT_BODY_PROVEN,
    HISTORICAL_P08_EMPTY_DATA_PACK,
    HISTORICAL_P08_READ_ONLY_PACK,
    HISTORICAL_Z2DP_PACK,
    MAX_POSITIONS_EFFECTIVE,
    STANDING_CANARY_AUTHORIZED,
    STANDING_CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
    STANDING_LIVE_ARMED,
    STANDING_LIVE_AUTHORIZED,
    STANDING_LIVE_ENABLED,
    STANDING_SUBMIT_UNLOCKED,
    STANDING_TESTNET_AUTHORIZED,
    TARGET_INSTRUMENT_ID,
    TARGET_INST_TYPE,
    TARGET_LEVERAGE,
    TARGET_TD_MODE,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


class P08ReadinessAdjudicationError(RuntimeError):
    """Fail-closed readiness snapshot violation."""


def _load_json(relative: str, name: str) -> dict[str, Any]:
    path = REPO_ROOT / relative / name
    if not path.is_file():
        raise P08ReadinessAdjudicationError(f"MISSING_UPSTREAM_EVIDENCE:{relative}{name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise P08ReadinessAdjudicationError(f"UPSTREAM_EVIDENCE_NOT_OBJECT:{name}")
    return payload


def adjudicate_current_execution_readiness_v1() -> dict[str, Any]:
    """Classify current readiness. Not GET, not send-time, not P08 close."""
    z2dp = _load_json(HISTORICAL_Z2DP_PACK, "ADJUDICATION.json")
    z2dp_snap = _load_json(HISTORICAL_Z2DP_PACK, "GET_SNAPSHOT.sanitized.json")
    p08_obs = _load_json(HISTORICAL_P08_EMPTY_DATA_PACK, "ADJUDICATION.json")
    p08_ro = _load_json(HISTORICAL_P08_READ_ONLY_PACK, "SUMMARY.json")
    parsed = z2dp_snap.get("PARSED_SURFACES")
    if not isinstance(parsed, dict):
        raise P08ReadinessAdjudicationError("Z2DP_PARSED_SURFACES_MISSING")
    instrument_state = str((parsed.get("INSTRUMENT_STATE") or {}).get("state") or "")
    pos_mode = str((parsed.get("ACCOUNT_CONFIG") or {}).get("posMode") or "")
    acct_lv = str((parsed.get("ACCOUNT_CONFIG") or {}).get("acctLv") or "")
    leverage = str((parsed.get("LEVERAGE") or {}).get("lever") or "")
    mgn_mode = str((parsed.get("LEVERAGE") or {}).get("mgnMode") or "")
    max_buy = str((parsed.get("MAX_AVAILABLE") or {}).get("maxBuy") or "")
    max_sell = str((parsed.get("MAX_AVAILABLE") or {}).get("maxSell") or "")
    avail_eq_status = str((parsed.get("AVAILABLE_MARGIN") or {}).get("avail_eq_status") or "")
    price_band_enabled = str((parsed.get("PRICE_BAND") or {}).get("enabled") or "")
    credential_perm = str((parsed.get("ACCOUNT_CONFIG") or {}).get("perm") or "")
    if z2dp.get("TARGET_INSTRUMENT_ID") != TARGET_INSTRUMENT_ID:
        raise P08ReadinessAdjudicationError("TARGET_INSTRUMENT_DRIFT")
    if p08_obs.get("TARGET_POSITION_NONZERO_PROVEN") is True:
        raise P08ReadinessAdjudicationError("FORBIDDEN_HISTORICAL_NONZERO_PROMOTION")
    if p08_ro.get("P08_CLOSED") is True:
        raise P08ReadinessAdjudicationError("FORBIDDEN_P08_CLOSED_PROMOTION")
    blockers = [
        "G_POSMODE_SUBMIT_BODY_UNPROVEN",
        "FIRST_PARTY_CREATE_NOT_AUTHORIZED",
        "LIVE_ENABLED_FALSE",
        "LIVE_ARMED_FALSE",
        "SUBMIT_UNLOCKED_FALSE",
        "CANARY_AUTHORIZED_FALSE",
        "HISTORICAL_VENUE_CAPACITY_PROVEN_ZERO",
        "AVAILABLE_MARGIN_NOT_OBSERVED",
        "NO_UNCONSUMED_P08_OBSERVATION_GET_GO",
        "OWNER_VENUE_MANUAL_TARGET_POSITION_ABSENT",
    ]
    return {
        "CURRENT_EXECUTION_READINESS_STATUS": (
            "FIRST_PARTY_CREATE_NOT_READY;EXTERNAL_APPEARANCE_SEMANTICALLY_OPEN"
        ),
        "SELECTED_BOUND_TARGET_INSTRUMENT": TARGET_INSTRUMENT_ID,
        "TARGET_INST_TYPE": TARGET_INST_TYPE,
        "INSTRUMENT_LIVE_STATE": instrument_state,
        "INSTRUMENT_LIVE_STATE_FRESHNESS": "HISTORICAL_Z2DP_NOT_SENDTIME",
        "ACCOUNT_UID": BOUND_ACCOUNT_SCOPE,
        "ACCOUNT_MODE_ACCTLV": acct_lv,
        "POS_MODE": pos_mode,
        "POS_MODE_MATCHES_REQUIRED_NET_MODE": pos_mode == "net_mode",
        "LEVERAGE": leverage,
        "LEVERAGE_EXPECTED": TARGET_LEVERAGE,
        "MARGIN_MODE": mgn_mode,
        "MARGIN_MODE_EXPECTED": TARGET_TD_MODE,
        "MAX_BUY": max_buy,
        "MAX_SELL": max_sell,
        "VENUE_NONZERO_CAPACITY": z2dp.get("VENUE_NONZERO_CAPACITY"),
        "AVAILABLE_MARGIN_STATUS": avail_eq_status,
        "PRICE_BAND_ENABLED": price_band_enabled,
        "CREDENTIAL_PERM": credential_perm,
        "CREDENTIAL_PRIVATE_GET_HEALTH": "P08_READ_ONLY_PACK_HTTP_200_OKX_0_IDENTIFIER_CHANNELS",
        "EGRESS_WHITELIST_STATE": "POST_WHITELIST_PRIVATE_GET_PROVEN_ON_P08_PACKS",
        "LIVE_ENABLED": STANDING_LIVE_ENABLED,
        "LIVE_ARMED": STANDING_LIVE_ARMED,
        "LIVE_AUTHORIZED": STANDING_LIVE_AUTHORIZED,
        "TESTNET_AUTHORIZED": STANDING_TESTNET_AUTHORIZED,
        "CANARY_AUTHORIZED": STANDING_CANARY_AUTHORIZED,
        "SUBMIT_UNLOCKED": STANDING_SUBMIT_UNLOCKED,
        "CANARY_SUBMIT_TRANSPORT_IMPLEMENTED": STANDING_CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
        "EXECUTION_PERMIT_STATE": "NONE",
        "MAX_POSITIONS_EFFECTIVE": MAX_POSITIONS_EFFECTIVE,
        "G_POSMODE_STATUS": G_POSMODE_STATUS_BOUND,
        "G_POSMODE_STATUS_CLOSED_AS": G_POSMODE_STATUS_CLOSED_AS_BOUND,
        "G_POSMODE_RESULT_CLASS": G_POSMODE_RESULT_CLASS_BOUND,
        "G_POSMODE_SUBMIT_BODY_PROVEN": G_POSMODE_SUBMIT_BODY_PROVEN,
        "CREATE_PATH_CURRENTLY_AUTHORIZED": bool(z2dp.get("CREATE_PATH_CURRENTLY_AUTHORIZED")),
        "CREATE_PATH_ARCHITECTURALLY_COMPLETE": bool(
            z2dp.get("CREATE_PATH_ARCHITECTURALLY_COMPLETE")
        ),
        "HOST": AUTHORIZED_HOST,
        "P08_POSITION_OBSERVATION_CLASS": p08_obs.get("POSITION_OBSERVATION_CLASS"),
        "P08_READ_ONLY_CLOSURE_RESULT": p08_ro.get("P08_READ_ONLY_CLOSURE_RESULT"),
        "GET_PERFORMED_THIS_PERSIST": False,
        "GET_NOT_REQUIRED_REASON": GET_NOT_REQUIRED_REASON,
        "CURRENT_BLOCKERS": blockers,
        "OPEN_CONTRADICTIONS": [],
        "HISTORICAL_Z2DP_PACK": HISTORICAL_Z2DP_PACK,
        "HISTORICAL_P08_EMPTY_DATA_PACK": HISTORICAL_P08_EMPTY_DATA_PACK,
        "HISTORICAL_P08_READ_ONLY_PACK": HISTORICAL_P08_READ_ONLY_PACK,
        "HISTORICAL_PACKS_ARE_NOT_CURRENT_08_PROOF": True,
        "HISTORICAL_CAPACITY_IS_NOT_SENDTIME_PROOF": True,
    }
