"""Decision-bound ACCOUNT_MODE observation for §11.13.5 pretrade.

Owner-adjudicated operative source is authenticated GET /api/v5/account/config
field ``acctLv``. This is account-global configuration, not posMode, not
tdMode, not mgnMode, not leverage, not settleCcy, not instrument state, and
not a TTL cache. No POST. No set-account-level. Raw venue token ``2`` is not
rewritten to an alias. This slice performs no network GET; it reuses the
already-committed POS_MODE account-config observation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qsl

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_ACCOUNT_CONFIG,
    HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID,
    HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_observation_v1 import (
    utc_now_iso_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    POS_MODE_ENDPOINT_PATH,
    POS_MODE_RESPONSE_FIELD,
    account_config_query_path_v1,
)

ACCOUNT_MODE_ENDPOINT_PATH = ENDPOINT_ACCOUNT_CONFIG
ACCOUNT_MODE_OUTPUT_DOMAIN = "ACCOUNT_ACCTLV"
ACCOUNT_MODE_COMPARISON_DOMAIN = "ACCOUNT_ACCTLV"
ACCOUNT_MODE_FRESHNESS_POLICY = "CONFIGURATION_SCOPED_CURRENT_READ_PER_PRETRADE_DECISION"
ACCOUNT_MODE_TS_AGE_BOUND = "UNBOUND"
ACCOUNT_MODE_NO_TS_FIELD = True
ACCOUNT_MODE_AUTH_CLASS = "AUTHENTICATED_PRIVATE_GET"
ACCOUNT_MODE_VENUE_SCOPE = "ACCOUNT_GLOBAL"
ACCOUNT_MODE_CONSUMER_SCOPE = "CURRENT_SUI_PRETRADE_CONSUMER"
ACCOUNT_MODE_REQUEST_GRAMMAR = "NONE"
ACCOUNT_MODE_RESPONSE_FIELD = "acctLv"
ACCOUNT_MODE_IDENTITY_FIELD = "uid"
ACCOUNT_MODE_VENUE_ALLOWED_VALUES = frozenset({"1", "2", "3", "4"})
ACCOUNT_MODE_REQUIRED_VALUE = "2"
ACCOUNT_MODE_KNOWN_NEGATIVE_RAW = frozenset({"1", "3", "4"})
ACCOUNT_MODE_SEMANTIC_CLASS = "FUTURES_MODE"
ACCOUNT_MODE_SEMANTIC_BY_RAW = {
    "1": "SPOT_MODE",
    "2": "FUTURES_MODE",
    "3": "MULTI_CURRENCY_MARGIN",
    "4": "PORTFOLIO_MARGIN",
}
POS_MODE_IS_NOT_ACCOUNT_MODE = True
TDMODE_CROSS_IS_NOT_ACCOUNT_MODE = True
MGNMODE_CROSS_IS_NOT_ACCOUNT_MODE = True
LEVERAGE_IS_NOT_ACCOUNT_MODE = True
SETTLE_CCY_IS_NOT_ACCOUNT_MODE = True
INSTRUMENT_STATE_IS_NOT_ACCOUNT_MODE = True
AVAILABLE_MARGIN_IS_NOT_ACCOUNT_MODE = True
ACCOUNT_IDENTITY_IS_NOT_ACCOUNT_MODE = True
DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF = True
OBSERVATION_CLASS_SUCCESS_TOKEN = "SUCCESS_TOKEN"
OBSERVATION_CLASS_VENUE_ERROR = "VENUE_ERROR"
OBSERVATION_CLASS_AUTH_ERROR = "AUTH_ERROR"
OBSERVATION_CLASS_NETWORK_ERROR = "NETWORK_ERROR"
OBSERVATION_CLASS_MALFORMED = "MALFORMED"
OBSERVATION_CLASS_NOT_PERFORMED = "NOT_PERFORMED"
HISTORICAL_BTC_PACK = "section_11_13_5_post_k_cross_imr_leverage_get_bind_v1"
HISTORICAL_GATE20_STATUS = "SATISFIED_HISTORICAL_ACCOUNT_WIDE_GET_acctLv=2_NOT_REOBSERVED_POST_SUI"
COMMITTED_POS_MODE_EVIDENCE_PACK = (
    "evidence/ops/pos_mode_forensic_binding_implementation_and_closure_v1/20260829T233351Z"
)
COMMITTED_POS_MODE_SNAPSHOT_RELATIVE = (
    f"{COMMITTED_POS_MODE_EVIDENCE_PACK}/GET_SNAPSHOT.sanitized.json"
)
COMMITTED_BODY_SHA256 = "cc422bd0667007af7207eb09c8ae5a01b5ccef20ddf48a3a0ef26c4df05d36ae"
COMMITTED_OBSERVED_AT_UTC = "2026-08-29T23:33:51.694980Z"
FORBIDDEN_SOURCE_MARKERS = (
    "set-account-level",
    "set-position-mode",
    "leverage-info",
    "max-avail-size",
    "account/max-size",
    "account/positions",
    "account/balance",
    "public/instruments",
    "public/price-limit",
)
FORBIDDEN_HOST_MARKERS = ("demo.", "testnet.", "sandbox.", "www.okx.com")
OWNER_GO_THIS_SLICE = "PEAK_TRADE_POST_6160_ACCOUNT_MODE_FORENSIC_BINDING_AND_CLOSURE_V1"


class LiveCanaryAccountModeObservationError(RuntimeError):
    """Fail-closed ACCOUNT_MODE observation violation."""


@dataclass(frozen=True)
class FreshAccountModeObservationV1:
    pretrade_decision_id: str
    observed_at_utc: str
    venue: str
    rest_host: str
    method: str
    endpoint: str
    consumer_instrument_id: str
    acct_lv_raw: str
    uid_raw: str
    pos_mode_raw_contextual: str
    venue_scope: str
    consumer_scope: str
    http_status: int
    venue_code: str
    get_performed: bool
    auth_header_sent: bool
    account_mode_domain: str
    historical_reuse: bool
    body_sha256: str
    row_count: int
    source_evidence: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pretrade_decision_id": self.pretrade_decision_id,
            "observed_at_utc": self.observed_at_utc,
            "venue": self.venue,
            "rest_host": self.rest_host,
            "method": self.method,
            "endpoint": self.endpoint,
            "consumer_instrument_id": self.consumer_instrument_id,
            "acct_lv_raw": self.acct_lv_raw,
            "uid_raw": self.uid_raw,
            "pos_mode_raw_contextual": self.pos_mode_raw_contextual,
            "venue_scope": self.venue_scope,
            "consumer_scope": self.consumer_scope,
            "http_status": self.http_status,
            "venue_code": self.venue_code,
            "get_performed": self.get_performed,
            "auth_header_sent": self.auth_header_sent,
            "account_mode_domain": self.account_mode_domain,
            "historical_reuse": self.historical_reuse,
            "body_sha256": self.body_sha256,
            "row_count": self.row_count,
            "source_evidence": self.source_evidence,
        }


@dataclass(frozen=True)
class ValidatedFreshAccountModeObservationV1:
    raw: FreshAccountModeObservationV1
    acct_lv: str
    comparison_domain: str
    semantic_class: str
    venue_scope: str
    consumer_scope: str
    account_identity_bound: bool
    environment_bound: bool
    provenance_bound: bool


def account_mode_query_path_v1() -> str:
    path = account_config_query_path_v1()
    if path != ACCOUNT_MODE_ENDPOINT_PATH or path != POS_MODE_ENDPOINT_PATH:
        raise LiveCanaryAccountModeObservationError("ACCOUNT_MODE_ENDPOINT_OWNER_DRIFT")
    return path


def classify_account_mode_observation_class_v1(
    *,
    get_performed: bool,
    http_status: int,
    payload: Mapping[str, Any] | None,
) -> str:
    if not get_performed:
        return OBSERVATION_CLASS_NOT_PERFORMED
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
    return OBSERVATION_CLASS_SUCCESS_TOKEN


def _raise_for_observation_class(observation_class: str) -> None:
    if observation_class == OBSERVATION_CLASS_SUCCESS_TOKEN:
        return
    mapping = {
        OBSERVATION_CLASS_NOT_PERFORMED: "FRESH_GET_NOT_PERFORMED",
        OBSERVATION_CLASS_AUTH_ERROR: "ACCOUNT_MODE_AUTH_ERROR",
        OBSERVATION_CLASS_NETWORK_ERROR: "ACCOUNT_MODE_NETWORK_ERROR",
        OBSERVATION_CLASS_VENUE_ERROR: "ACCOUNT_MODE_VENUE_CODE_UNSUCCESSFUL",
        OBSERVATION_CLASS_MALFORMED: "ACCOUNT_MODE_MALFORMED",
    }
    raise LiveCanaryAccountModeObservationError(
        mapping.get(observation_class, f"ACCOUNT_MODE_FAIL_CLOSED:{observation_class}")
    )


def _reject_historical_reuse(
    *,
    pretrade_decision_id: str,
    endpoint: str,
    historical_reuse: bool,
    instrument_id: str,
    source_evidence: str,
) -> None:
    if historical_reuse:
        raise LiveCanaryAccountModeObservationError("HISTORICAL_ACCOUNT_MODE_REUSE_FORBIDDEN")
    decision = str(pretrade_decision_id or "").strip()
    ep = str(endpoint or "")
    evidence = str(source_evidence or "")
    if (
        HISTORICAL_BTC_PACK in decision
        or HISTORICAL_BTC_PACK in ep
        or HISTORICAL_BTC_PACK in evidence
    ):
        raise LiveCanaryAccountModeObservationError(
            "HISTORICAL_BTC_ACCOUNT_MODE_PACK_REUSE_FORBIDDEN"
        )
    if HISTORICAL_GATE20_STATUS in decision or HISTORICAL_GATE20_STATUS in evidence:
        raise LiveCanaryAccountModeObservationError(
            "HISTORICAL_GATE20_STATUS_IS_NOT_CURRENT_AUTHORITY"
        )
    if HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID in ep:
        raise LiveCanaryAccountModeObservationError("HISTORICAL_BTC_INSTRUMENT_FORBIDDEN")
    if instrument_id == HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID:
        raise LiveCanaryAccountModeObservationError("HISTORICAL_BTC_INSTRUMENT_FORBIDDEN")
    if HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID in ep or "-SWAP" in instrument_id:
        raise LiveCanaryAccountModeObservationError("SWAP_ACCOUNT_MODE_SUBSTITUTION_FORBIDDEN")
    for marker in FORBIDDEN_SOURCE_MARKERS:
        if marker in ep:
            raise LiveCanaryAccountModeObservationError(
                f"ACCOUNT_MODE_RECONSTRUCTION_SOURCE_FORBIDDEN:{marker}"
            )


def _query_pairs(endpoint: str) -> dict[str, str]:
    query = str(endpoint or "").split("?", 1)
    if len(query) != 2:
        return {}
    return {str(k): str(v) for k, v in parse_qsl(query[1], keep_blank_values=True)}


def _config_object(*, payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], int]:
    if str(payload.get("code") or "") != "0":
        raise LiveCanaryAccountModeObservationError(
            f"ACCOUNT_MODE_VENUE_CODE_UNSUCCESSFUL:{payload.get('code')}"
        )
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise LiveCanaryAccountModeObservationError("ACCOUNT_MODE_DATA_MISSING")
    objects = [item for item in data if isinstance(item, Mapping)]
    if not objects:
        raise LiveCanaryAccountModeObservationError("ACCOUNT_MODE_CONFIG_OBJECT_MISSING")
    if len(objects) != 1:
        raise LiveCanaryAccountModeObservationError("ACCOUNT_MODE_AMBIGUOUS_CONFIG_OBJECT")
    return objects[0], len(objects)


def _require_string_field(*, row: Mapping[str, Any], field: str) -> str:
    if field not in row:
        raise LiveCanaryAccountModeObservationError(f"ACCOUNT_MODE_FIELD_MISSING:{field}")
    raw_value = row.get(field)
    if raw_value is None:
        raise LiveCanaryAccountModeObservationError(f"ACCOUNT_MODE_FIELD_NULL:{field}")
    if not isinstance(raw_value, str):
        raise LiveCanaryAccountModeObservationError(f"ACCOUNT_MODE_FIELD_WRONG_TYPE:{field}")
    if raw_value != raw_value.strip() or raw_value == "":
        raise LiveCanaryAccountModeObservationError(f"ACCOUNT_MODE_FIELD_EMPTY:{field}")
    return raw_value


def acquire_fresh_account_mode_observation_from_payload_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    observed_at_utc: str,
    endpoint: str,
    http_status: int,
    get_performed: bool,
    rest_host: str = REUSED_BINDING_REST_HOST,
    auth_header_sent: bool = True,
    historical_reuse: bool = False,
    body_sha256: str = "",
    source_evidence: str = COMMITTED_POS_MODE_SNAPSHOT_RELATIVE,
) -> FreshAccountModeObservationV1:
    decision = str(pretrade_decision_id or "").strip()
    if not decision:
        raise LiveCanaryAccountModeObservationError("PRETRADE_DECISION_ID_REQUIRED")
    _reject_historical_reuse(
        pretrade_decision_id=decision,
        endpoint=endpoint,
        historical_reuse=historical_reuse,
        instrument_id=instrument_id,
        source_evidence=source_evidence,
    )
    observation_class = classify_account_mode_observation_class_v1(
        get_performed=get_performed,
        http_status=http_status,
        payload=payload,
    )
    _raise_for_observation_class(observation_class)
    if not auth_header_sent:
        raise LiveCanaryAccountModeObservationError("ACCOUNT_MODE_AUTH_HEADER_REQUIRED")
    host = str(rest_host or "")
    if host != REUSED_BINDING_REST_HOST:
        raise LiveCanaryAccountModeObservationError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    lowered_host = host.lower()
    if any(marker in lowered_host for marker in FORBIDDEN_HOST_MARKERS):
        raise LiveCanaryAccountModeObservationError(f"ACCOUNT_MODE_ENVIRONMENT_MISMATCH:{host}")
    path = str(endpoint or "").split("?", 1)[0]
    if path != ACCOUNT_MODE_ENDPOINT_PATH:
        raise LiveCanaryAccountModeObservationError(f"ACCOUNT_MODE_ENDPOINT_MISMATCH:{endpoint}")
    if _query_pairs(endpoint):
        raise LiveCanaryAccountModeObservationError("ACCOUNT_MODE_QUERY_FORBIDDEN")
    row, row_count = _config_object(payload=payload)
    acct_lv_raw = _require_string_field(row=row, field=ACCOUNT_MODE_RESPONSE_FIELD)
    if acct_lv_raw not in ACCOUNT_MODE_VENUE_ALLOWED_VALUES:
        raise LiveCanaryAccountModeObservationError(f"ACCOUNT_MODE_UNKNOWN_ENUM:{acct_lv_raw}")
    if acct_lv_raw in ACCOUNT_MODE_KNOWN_NEGATIVE_RAW:
        raise LiveCanaryAccountModeObservationError(f"ACCOUNT_MODE_NOT_ADMISSIBLE:{acct_lv_raw}")
    uid_raw = _require_string_field(row=row, field=ACCOUNT_MODE_IDENTITY_FIELD)
    if uid_raw != REUSED_BINDING_ACCOUNT_SCOPE:
        raise LiveCanaryAccountModeObservationError(f"ACCOUNT_IDENTITY_MISMATCH:{uid_raw}")
    main_uid = row.get("mainUid")
    if main_uid is not None:
        if not isinstance(main_uid, str) or main_uid != uid_raw:
            raise LiveCanaryAccountModeObservationError("ACCOUNT_IDENTITY_MAIN_UID_MISMATCH")
    pos_mode_contextual = row.get(POS_MODE_RESPONSE_FIELD)
    pos_mode_raw_contextual = pos_mode_contextual if isinstance(pos_mode_contextual, str) else ""
    digest = str(body_sha256 or "").strip()
    if not digest:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
    return FreshAccountModeObservationV1(
        pretrade_decision_id=decision,
        observed_at_utc=str(observed_at_utc or "").strip() or utc_now_iso_v1(),
        venue="OKX_EEA",
        rest_host=REUSED_BINDING_REST_HOST,
        method="GET",
        endpoint=str(endpoint or "").strip(),
        consumer_instrument_id=instrument_id,
        acct_lv_raw=acct_lv_raw,
        uid_raw=uid_raw,
        pos_mode_raw_contextual=pos_mode_raw_contextual,
        venue_scope=ACCOUNT_MODE_VENUE_SCOPE,
        consumer_scope=ACCOUNT_MODE_CONSUMER_SCOPE,
        http_status=int(http_status),
        venue_code=str(payload.get("code") or ""),
        get_performed=True,
        auth_header_sent=True,
        account_mode_domain=ACCOUNT_MODE_OUTPUT_DOMAIN,
        historical_reuse=False,
        body_sha256=digest,
        row_count=int(row_count),
        source_evidence=str(source_evidence or "").strip() or COMMITTED_POS_MODE_SNAPSHOT_RELATIVE,
    )


def validate_fresh_account_mode_observation_v1(
    observation: FreshAccountModeObservationV1,
    *,
    pretrade_decision_id: str,
    instrument_id: str,
    account_mode_domain: str,
) -> ValidatedFreshAccountModeObservationV1:
    if observation.pretrade_decision_id != str(pretrade_decision_id).strip():
        raise LiveCanaryAccountModeObservationError("OBSERVATION_DECISION_ID_MISMATCH")
    if observation.consumer_instrument_id != instrument_id:
        raise LiveCanaryAccountModeObservationError("OBSERVATION_INSTRUMENT_MISMATCH")
    if str(account_mode_domain) != ACCOUNT_MODE_OUTPUT_DOMAIN:
        raise LiveCanaryAccountModeObservationError("ACCOUNT_MODE_DOMAIN_INCOMPATIBLE")
    if observation.account_mode_domain != ACCOUNT_MODE_OUTPUT_DOMAIN:
        raise LiveCanaryAccountModeObservationError("OBSERVATION_DOMAIN_INCOMPATIBLE")
    if observation.venue_scope != ACCOUNT_MODE_VENUE_SCOPE:
        raise LiveCanaryAccountModeObservationError("ACCOUNT_MODE_VENUE_SCOPE_MISMATCH")
    if observation.consumer_scope != ACCOUNT_MODE_CONSUMER_SCOPE:
        raise LiveCanaryAccountModeObservationError("ACCOUNT_MODE_CONSUMER_SCOPE_MISMATCH")
    if observation.row_count != 1:
        raise LiveCanaryAccountModeObservationError("ACCOUNT_MODE_AMBIGUOUS_CONFIG_OBJECT")
    if observation.acct_lv_raw != ACCOUNT_MODE_REQUIRED_VALUE:
        raise LiveCanaryAccountModeObservationError(
            f"ACCOUNT_MODE_REQUIRED_VALUE_MISMATCH:{observation.acct_lv_raw}"
        )
    if observation.uid_raw != REUSED_BINDING_ACCOUNT_SCOPE:
        raise LiveCanaryAccountModeObservationError(
            f"ACCOUNT_IDENTITY_MISMATCH:{observation.uid_raw}"
        )
    if observation.rest_host != REUSED_BINDING_REST_HOST:
        raise LiveCanaryAccountModeObservationError(
            f"ACCOUNT_MODE_ENVIRONMENT_MISMATCH:{observation.rest_host}"
        )
    if not observation.source_evidence:
        raise LiveCanaryAccountModeObservationError("ACCOUNT_MODE_PROVENANCE_MISSING")
    semantic = ACCOUNT_MODE_SEMANTIC_BY_RAW.get(observation.acct_lv_raw)
    if semantic != ACCOUNT_MODE_SEMANTIC_CLASS:
        raise LiveCanaryAccountModeObservationError(
            f"ACCOUNT_MODE_SEMANTIC_PROJECTION_FORBIDDEN:{observation.acct_lv_raw}"
        )
    return ValidatedFreshAccountModeObservationV1(
        raw=observation,
        acct_lv=observation.acct_lv_raw,
        comparison_domain=ACCOUNT_MODE_COMPARISON_DOMAIN,
        semantic_class=ACCOUNT_MODE_SEMANTIC_CLASS,
        venue_scope=observation.venue_scope,
        consumer_scope=observation.consumer_scope,
        account_identity_bound=True,
        environment_bound=True,
        provenance_bound=True,
    )


def bind_account_mode_from_committed_pos_mode_pack_v1(
    *,
    repo_root: Path,
    pretrade_decision_id: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
) -> ValidatedFreshAccountModeObservationV1:
    """Bind ACCOUNT_MODE from the committed POS_MODE GET pack. No network."""
    snapshot_path = repo_root / COMMITTED_POS_MODE_SNAPSHOT_RELATIVE
    if not snapshot_path.is_file():
        raise LiveCanaryAccountModeObservationError("COMMITTED_POS_MODE_PACK_MISSING")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if not isinstance(snapshot, Mapping):
        raise LiveCanaryAccountModeObservationError("COMMITTED_POS_MODE_PACK_MALFORMED")
    payload = snapshot.get("payload")
    if not isinstance(payload, Mapping):
        raise LiveCanaryAccountModeObservationError("COMMITTED_POS_MODE_PAYLOAD_MISSING")
    http_evidence = snapshot.get("http_evidence")
    body_sha256 = ""
    if isinstance(http_evidence, Mapping):
        body_sha256 = str(http_evidence.get("body_sha256") or "")
    if body_sha256 != COMMITTED_BODY_SHA256:
        raise LiveCanaryAccountModeObservationError("COMMITTED_POS_MODE_BODY_SHA256_MISMATCH")
    host = str(snapshot.get("HOST") or REUSED_BINDING_REST_HOST)
    endpoint = str(snapshot.get("ENDPOINT") or ACCOUNT_MODE_ENDPOINT_PATH)
    observed_at = str(snapshot.get("response_event_time") or COMMITTED_OBSERVED_AT_UTC)
    observation = acquire_fresh_account_mode_observation_from_payload_v1(
        pretrade_decision_id=pretrade_decision_id,
        payload=payload,
        instrument_id=instrument_id,
        observed_at_utc=observed_at,
        endpoint=endpoint,
        http_status=200,
        get_performed=True,
        rest_host=host,
        auth_header_sent=True,
        historical_reuse=False,
        body_sha256=body_sha256,
        source_evidence=COMMITTED_POS_MODE_SNAPSHOT_RELATIVE,
    )
    return validate_fresh_account_mode_observation_v1(
        observation,
        pretrade_decision_id=pretrade_decision_id,
        instrument_id=instrument_id,
        account_mode_domain=ACCOUNT_MODE_OUTPUT_DOMAIN,
    )
