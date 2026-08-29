"""Decision-bound fresh LEVERAGE observation for §11.13.5 pretrade.

Owner-adjudicated operative source is authenticated GET /api/v5/account/leverage-info.
This is current configured set-account leverage, not max leverage, not MMR/IMR,
not public instruments lever, not historical BTC lever=3, and not a TTL cache.
Request uses mgnMode. Order trade mode remains tdMode. No POST. No set-leverage.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlencode, urlparse

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_FAMILY,
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_ACCOUNT_LEVERAGE_INFO,
    HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID,
    HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
    REUSED_BINDING_REST_HOST,
    LiveCanaryInstrumentBindingError,
    assert_live_canary_instrument_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_observation_v1 import (
    utc_now_iso_v1,
)

LEVERAGE_ENDPOINT_PATH = ENDPOINT_ACCOUNT_LEVERAGE_INFO
LEVERAGE_OUTPUT_DOMAIN = "SET_ACCOUNT_LEVERAGE"
LEVERAGE_COMPARISON_DOMAIN = "SET_ACCOUNT_LEVERAGE"
LEVERAGE_FRESHNESS_POLICY = "FRESH_GET_PER_PRETRADE_DECISION"
LEVERAGE_TS_AGE_BOUND = "UNBOUND"
LEVERAGE_NO_TS_FIELD = True
LEVERAGE_AUTH_CLASS = "AUTHENTICATED_PRIVATE_GET"
LEVERAGE_SCOPE = "PER_INSTRUMENT_FAMILY"
LEVERAGE_REQUEST_INSTID_ROLE = "FAMILY_SELECTOR"
LEVERAGE_EXPECTED_MGN_MODE = "cross"
LEVERAGE_EXPECTED_POS_SIDE = "net"
MGNMODE_IS_NOT_TDMODE = True
MGNMODE_IS_NOT_ACCOUNT_MODE = True
TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF = True
ACCOUNT_MODE = "UNPROVEN"
ACCOUNT_MODE_PROOF_STATUS = "UNPROVEN"
OBSERVATION_CLASS_SUCCESS_NUMERIC = "SUCCESS_NUMERIC"
OBSERVATION_CLASS_VENUE_ERROR = "VENUE_ERROR"
OBSERVATION_CLASS_AUTH_ERROR = "AUTH_ERROR"
OBSERVATION_CLASS_NETWORK_ERROR = "NETWORK_ERROR"
OBSERVATION_CLASS_MALFORMED = "MALFORMED"
OBSERVATION_CLASS_NOT_PERFORMED = "NOT_PERFORMED"
MAX_RAW_DIGIT_LEN = 40
_SCIENTIFIC_NOTATION = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+")
HISTORICAL_BTC_PACK = "section_11_13_5_post_k_cross_imr_leverage_get_bind_v1"
HISTORICAL_BTC_INSTRUMENT_ID = HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID
FORBIDDEN_SOURCE_MARKERS = (
    "adjust-leverage-info",
    "set-leverage",
    "max-avail-size",
    "public/instruments",
    "public/position-tiers",
    "account/positions",
)
FORBIDDEN_HEADER_NAME_MARKERS = (
    "authorization",
    "ok-access",
    "cookie",
    "api-key",
    "secret",
    "sign",
)
SAFE_HEADER_ALLOWLIST = frozenset({"content-type", "date", "server"})
PRODUCTION_REST_BASE = "https://eea.okx.com"
OWNER_GO_THIS_SLICE = "PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1"


class LiveCanaryLeverageObservationError(RuntimeError):
    """Fail-closed fresh LEVERAGE observation violation."""


@dataclass(frozen=True)
class FreshLeverageObservationV1:
    pretrade_decision_id: str
    observed_at_utc: str
    venue: str
    rest_host: str
    method: str
    endpoint: str
    instrument_id: str
    requested_inst_id: str
    requested_mgn_mode: str
    inst_id_raw: str
    ccy_raw: str
    mgn_mode_raw: str
    pos_side_raw: str
    lever_raw: str
    inst_family_bound: str
    leverage_scope: str
    request_instid_role: str
    http_status: int
    venue_code: str
    get_performed: bool
    auth_header_sent: bool
    leverage_domain: str
    historical_reuse: bool
    body_sha256: str
    row_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "pretrade_decision_id": self.pretrade_decision_id,
            "observed_at_utc": self.observed_at_utc,
            "venue": self.venue,
            "rest_host": self.rest_host,
            "method": self.method,
            "endpoint": self.endpoint,
            "instrument_id": self.instrument_id,
            "requested_inst_id": self.requested_inst_id,
            "requested_mgn_mode": self.requested_mgn_mode,
            "inst_id_raw": self.inst_id_raw,
            "ccy_raw": self.ccy_raw,
            "mgn_mode_raw": self.mgn_mode_raw,
            "pos_side_raw": self.pos_side_raw,
            "lever_raw": self.lever_raw,
            "inst_family_bound": self.inst_family_bound,
            "leverage_scope": self.leverage_scope,
            "request_instid_role": self.request_instid_role,
            "http_status": self.http_status,
            "venue_code": self.venue_code,
            "get_performed": self.get_performed,
            "auth_header_sent": self.auth_header_sent,
            "leverage_domain": self.leverage_domain,
            "historical_reuse": self.historical_reuse,
            "body_sha256": self.body_sha256,
            "row_count": self.row_count,
        }


@dataclass(frozen=True)
class ValidatedFreshLeverageObservationV1:
    raw: FreshLeverageObservationV1
    lever: Decimal
    comparison_domain: str
    mgn_mode: str
    pos_side: str
    inst_family: str


def account_leverage_info_query_path_v1(
    *,
    instrument_id: str,
    mgn_mode: str,
) -> str:
    inst = str(instrument_id or "").strip()
    mode = str(mgn_mode or "").strip()
    if not inst:
        raise LiveCanaryLeverageObservationError("LEVERAGE_INSTID_REQUIRED")
    if not mode:
        raise LiveCanaryLeverageObservationError("LEVERAGE_MGNMODE_REQUIRED")
    if mode != LEVERAGE_EXPECTED_MGN_MODE:
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_MGNMODE_UNSUPPORTED:{mode}")
    try:
        assert_live_canary_instrument_binding_v1(instrument_id=inst, inst_type=DEFAULT_INST_TYPE)
    except LiveCanaryInstrumentBindingError as exc:
        raise LiveCanaryLeverageObservationError(str(exc)) from exc
    return f"{LEVERAGE_ENDPOINT_PATH}?{urlencode({'instId': inst, 'mgnMode': mode})}"


def classify_leverage_observation_class_v1(
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
    return OBSERVATION_CLASS_SUCCESS_NUMERIC


def _raise_for_observation_class(observation_class: str) -> None:
    if observation_class == OBSERVATION_CLASS_SUCCESS_NUMERIC:
        return
    mapping = {
        OBSERVATION_CLASS_NOT_PERFORMED: "FRESH_GET_NOT_PERFORMED",
        OBSERVATION_CLASS_AUTH_ERROR: "LEVERAGE_AUTH_ERROR",
        OBSERVATION_CLASS_NETWORK_ERROR: "LEVERAGE_NETWORK_ERROR",
        OBSERVATION_CLASS_VENUE_ERROR: "LEVERAGE_VENUE_CODE_UNSUCCESSFUL",
        OBSERVATION_CLASS_MALFORMED: "LEVERAGE_MALFORMED",
    }
    raise LiveCanaryLeverageObservationError(
        mapping.get(observation_class, f"LEVERAGE_FAIL_CLOSED:{observation_class}")
    )


def _reject_historical_reuse(
    *,
    pretrade_decision_id: str,
    endpoint: str,
    historical_reuse: bool,
    instrument_id: str,
) -> None:
    if historical_reuse:
        raise LiveCanaryLeverageObservationError("HISTORICAL_LEVERAGE_REUSE_FORBIDDEN")
    decision = str(pretrade_decision_id or "").strip()
    ep = str(endpoint or "")
    if HISTORICAL_BTC_PACK in decision or HISTORICAL_BTC_PACK in ep:
        raise LiveCanaryLeverageObservationError("HISTORICAL_BTC_LEVERAGE_PACK_REUSE_FORBIDDEN")
    if HISTORICAL_BTC_INSTRUMENT_ID in ep or instrument_id == HISTORICAL_BTC_INSTRUMENT_ID:
        raise LiveCanaryLeverageObservationError("HISTORICAL_BTC_INSTRUMENT_FORBIDDEN")
    if HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID in ep or "-SWAP" in instrument_id:
        raise LiveCanaryLeverageObservationError("SWAP_LEVERAGE_SUBSTITUTION_FORBIDDEN")
    for marker in FORBIDDEN_SOURCE_MARKERS:
        if marker in ep:
            raise LiveCanaryLeverageObservationError(
                f"LEVERAGE_RECONSTRUCTION_SOURCE_FORBIDDEN:{marker}"
            )


def _require_positive_decimal(raw: Any, *, field: str) -> Decimal:
    if raw is None:
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_FIELD_NULL:{field}")
    text = str(raw).strip()
    if not text:
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_FIELD_MISSING:{field}")
    lowered = text.lower()
    if lowered in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_FIELD_NON_NUMERIC:{field}")
    if _SCIENTIFIC_NOTATION.fullmatch(text) or len(text) > MAX_RAW_DIGIT_LEN:
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_FIELD_OUT_OF_DOMAIN:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_FIELD_NON_NUMERIC:{field}") from exc
    if value.is_nan() or value.is_infinite():
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_FIELD_NON_NUMERIC:{field}")
    if value <= 0:
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_FIELD_NON_POSITIVE:{field}")
    return value


def _query_pairs(endpoint: str) -> dict[str, str]:
    query = str(endpoint or "").split("?", 1)
    if len(query) != 2:
        return {}
    return {str(k): str(v) for k, v in parse_qsl(query[1], keep_blank_values=True)}


def _target_row(
    *,
    payload: Mapping[str, Any],
    instrument_id: str,
    mgn_mode: str,
) -> tuple[Mapping[str, Any], int]:
    try:
        assert_live_canary_instrument_binding_v1(
            instrument_id=instrument_id, inst_type=DEFAULT_INST_TYPE
        )
    except LiveCanaryInstrumentBindingError as exc:
        raise LiveCanaryLeverageObservationError(str(exc)) from exc
    if str(payload.get("code") or "") != "0":
        raise LiveCanaryLeverageObservationError(
            f"LEVERAGE_VENUE_CODE_UNSUCCESSFUL:{payload.get('code')}"
        )
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise LiveCanaryLeverageObservationError("LEVERAGE_DATA_MISSING")
    matches: list[Mapping[str, Any]] = []
    for item in data:
        if isinstance(item, Mapping) and str(item.get("instId") or "") == instrument_id:
            matches.append(item)
    if not matches:
        raise LiveCanaryLeverageObservationError(f"INSTRUMENT_MISMATCH:{instrument_id}")
    if len(matches) > 1:
        raise LiveCanaryLeverageObservationError("LEVERAGE_AMBIGUOUS_TARGET_ROW")
    row = matches[0]
    row_mode = str(row.get("mgnMode") or "").strip()
    if row_mode != mgn_mode:
        raise LiveCanaryLeverageObservationError(
            f"LEVERAGE_MGNMODE_MISMATCH:{row_mode or '<empty>'}"
        )
    pos_side = str(row.get("posSide") or "").strip()
    if not pos_side:
        raise LiveCanaryLeverageObservationError("LEVERAGE_FIELD_MISSING:posSide")
    if pos_side != LEVERAGE_EXPECTED_POS_SIDE:
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_POS_SIDE_NOT_NET:{pos_side}")
    return row, len(data)


def acquire_fresh_leverage_observation_from_payload_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    mgn_mode: str = LEVERAGE_EXPECTED_MGN_MODE,
    observed_at_utc: str,
    endpoint: str,
    http_status: int,
    get_performed: bool,
    rest_host: str = REUSED_BINDING_REST_HOST,
    auth_header_sent: bool = True,
    historical_reuse: bool = False,
    body_sha256: str = "",
    expected_inst_family: str = DEFAULT_INST_FAMILY,
) -> FreshLeverageObservationV1:
    decision = str(pretrade_decision_id or "").strip()
    if not decision:
        raise LiveCanaryLeverageObservationError("PRETRADE_DECISION_ID_REQUIRED")
    mode = str(mgn_mode or "").strip()
    if mode != LEVERAGE_EXPECTED_MGN_MODE:
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_MGNMODE_UNSUPPORTED:{mode}")
    family = str(expected_inst_family or "").strip()
    if family != DEFAULT_INST_FAMILY:
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_INST_FAMILY_MISMATCH:{family}")
    _reject_historical_reuse(
        pretrade_decision_id=decision,
        endpoint=endpoint,
        historical_reuse=historical_reuse,
        instrument_id=instrument_id,
    )
    observation_class = classify_leverage_observation_class_v1(
        get_performed=get_performed,
        http_status=http_status,
        payload=payload,
    )
    _raise_for_observation_class(observation_class)
    if not auth_header_sent:
        raise LiveCanaryLeverageObservationError("LEVERAGE_AUTH_HEADER_REQUIRED")
    if str(rest_host or "") != REUSED_BINDING_REST_HOST:
        raise LiveCanaryLeverageObservationError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    path = str(endpoint or "").split("?", 1)[0]
    if path != LEVERAGE_ENDPOINT_PATH:
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_ENDPOINT_MISMATCH:{endpoint}")
    query = _query_pairs(endpoint)
    if "tdMode" in query:
        raise LiveCanaryLeverageObservationError("LEVERAGE_TDMODE_QUERY_FORBIDDEN")
    if "ccy" in query:
        raise LiveCanaryLeverageObservationError("LEVERAGE_CCY_QUERY_FORBIDDEN")
    if "posSide" in query:
        raise LiveCanaryLeverageObservationError("LEVERAGE_POSSIDE_QUERY_FORBIDDEN")
    if query.get("instId") != instrument_id:
        raise LiveCanaryLeverageObservationError("LEVERAGE_QUERY_INSTID_MISMATCH")
    if query.get("mgnMode") != mode:
        raise LiveCanaryLeverageObservationError("LEVERAGE_QUERY_MGNMODE_MISMATCH")
    row, row_count = _target_row(payload=payload, instrument_id=instrument_id, mgn_mode=mode)
    if "lever" not in row:
        raise LiveCanaryLeverageObservationError("LEVERAGE_FIELD_MISSING:lever")
    if "instId" not in row:
        raise LiveCanaryLeverageObservationError("LEVERAGE_FIELD_MISSING:instId")
    if "mgnMode" not in row:
        raise LiveCanaryLeverageObservationError("LEVERAGE_FIELD_MISSING:mgnMode")
    if "posSide" not in row:
        raise LiveCanaryLeverageObservationError("LEVERAGE_FIELD_MISSING:posSide")
    lever_raw = row.get("lever")
    if lever_raw is None:
        raise LiveCanaryLeverageObservationError("LEVERAGE_FIELD_NULL:lever")
    digest = str(body_sha256 or "").strip()
    if not digest:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
    ccy_present = "ccy" in row
    return FreshLeverageObservationV1(
        pretrade_decision_id=decision,
        observed_at_utc=str(observed_at_utc or "").strip() or utc_now_iso_v1(),
        venue="OKX_EEA",
        rest_host=REUSED_BINDING_REST_HOST,
        method="GET",
        endpoint=str(endpoint or "").strip(),
        instrument_id=instrument_id,
        requested_inst_id=instrument_id,
        requested_mgn_mode=mode,
        inst_id_raw=str(row.get("instId") or "").strip(),
        ccy_raw=str(row.get("ccy") if ccy_present else ""),
        mgn_mode_raw=str(row.get("mgnMode") or "").strip(),
        pos_side_raw=str(row.get("posSide") or "").strip(),
        lever_raw=str(lever_raw).strip(),
        inst_family_bound=DEFAULT_INST_FAMILY,
        leverage_scope=LEVERAGE_SCOPE,
        request_instid_role=LEVERAGE_REQUEST_INSTID_ROLE,
        http_status=int(http_status),
        venue_code=str(payload.get("code") or ""),
        get_performed=True,
        auth_header_sent=True,
        leverage_domain=LEVERAGE_OUTPUT_DOMAIN,
        historical_reuse=False,
        body_sha256=digest,
        row_count=int(row_count),
    )


def validate_fresh_leverage_observation_v1(
    observation: FreshLeverageObservationV1,
    *,
    pretrade_decision_id: str,
    instrument_id: str,
    leverage_domain: str,
    mgn_mode: str = LEVERAGE_EXPECTED_MGN_MODE,
    expected_inst_family: str = DEFAULT_INST_FAMILY,
) -> ValidatedFreshLeverageObservationV1:
    if observation.pretrade_decision_id != str(pretrade_decision_id).strip():
        raise LiveCanaryLeverageObservationError("OBSERVATION_DECISION_ID_MISMATCH")
    if observation.instrument_id != instrument_id:
        raise LiveCanaryLeverageObservationError("OBSERVATION_INSTRUMENT_MISMATCH")
    if str(leverage_domain) != LEVERAGE_OUTPUT_DOMAIN:
        raise LiveCanaryLeverageObservationError("LEVERAGE_DOMAIN_INCOMPATIBLE")
    if observation.leverage_domain != LEVERAGE_OUTPUT_DOMAIN:
        raise LiveCanaryLeverageObservationError("OBSERVATION_DOMAIN_INCOMPATIBLE")
    if observation.requested_mgn_mode != mgn_mode:
        raise LiveCanaryLeverageObservationError("OBSERVATION_MGNMODE_MISMATCH")
    if observation.mgn_mode_raw != mgn_mode:
        raise LiveCanaryLeverageObservationError("LEVERAGE_MGNMODE_MISMATCH")
    if observation.pos_side_raw != LEVERAGE_EXPECTED_POS_SIDE:
        raise LiveCanaryLeverageObservationError(
            f"LEVERAGE_POS_SIDE_NOT_NET:{observation.pos_side_raw}"
        )
    if observation.inst_family_bound != expected_inst_family:
        raise LiveCanaryLeverageObservationError("LEVERAGE_INST_FAMILY_MISMATCH")
    if observation.leverage_scope != LEVERAGE_SCOPE:
        raise LiveCanaryLeverageObservationError("LEVERAGE_SCOPE_MISMATCH")
    if observation.row_count != 1:
        raise LiveCanaryLeverageObservationError("LEVERAGE_AMBIGUOUS_TARGET_ROW")
    lever = _require_positive_decimal(observation.lever_raw, field="lever")
    return ValidatedFreshLeverageObservationV1(
        raw=observation,
        lever=lever,
        comparison_domain=LEVERAGE_COMPARISON_DOMAIN,
        mgn_mode=observation.mgn_mode_raw,
        pos_side=observation.pos_side_raw,
        inst_family=observation.inst_family_bound,
    )


def _safe_headers(headers: Mapping[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in dict(headers).items():
        lowered = str(key).strip().lower()
        if any(marker in lowered for marker in FORBIDDEN_HEADER_NAME_MARKERS):
            continue
        if lowered in SAFE_HEADER_ALLOWLIST:
            out[str(key)] = str(value)
    return out


def persist_authorized_fresh_leverage_observation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    pretrade_decision_id: str,
    evidence_root: Path,
    vault_file: Path | str,
    mgn_mode: str = LEVERAGE_EXPECTED_MGN_MODE,
) -> dict[str, Any]:
    """Perform one authenticated account/leverage-info GET and persist forensic evidence.

    No POST. No set-leverage. The pack is not an operative cache.
    """
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        REQUIRED_CREDENTIAL_CLASS,
        REQUIRED_SECRETREF_URI,
        USER_AGENT_CANARY,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
        LiveCanaryHttpClientV1,
        LiveCanaryHttpError,
        UrllibLiveCanaryTransportV1,
        parse_json_object_v1,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
        build_file_secretref_vault_backend_v1,
        release_live_canary_ephemeral_material_v1,
        resolve_and_load_live_canary_secretref_ephemeral_v1,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
        build_okx_live_canary_auth_headers_v1,
    )

    owned = str(owner_go or "").strip()
    if owned != OWNER_GO_THIS_SLICE:
        raise LiveCanaryLeverageObservationError("OWNER_GO_MISMATCH")
    endpoint = account_leverage_info_query_path_v1(
        instrument_id=DEFAULT_INSTRUMENT_ID, mgn_mode=mgn_mode
    )
    client = LiveCanaryHttpClientV1(
        rest_base=PRODUCTION_REST_BASE,
        rest_host=REUSED_BINDING_REST_HOST,
        transport=UrllibLiveCanaryTransportV1(wire_send_enabled=True),
        max_retries=0,
        timeout_seconds=10.0,
    )
    backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
    handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
        secret_reference=REQUIRED_SECRETREF_URI,
        vault_backend=backend,
        credential_class=REQUIRED_CREDENTIAL_CLASS,
    )
    auth_headers: dict[str, str] = {}
    request_time = utc_now_iso_v1()
    try:
        url = f"{PRODUCTION_REST_BASE}{endpoint}"
        parsed = urlparse(url)
        signed_target = f"{parsed.path}?{parsed.query}" if parsed.query else parsed.path
        if signed_target != endpoint:
            raise LiveCanaryLeverageObservationError(
                f"SIGNED_REQUEST_TARGET_MISMATCH:{signed_target}"
            )
        auth_headers = build_okx_live_canary_auth_headers_v1(handle=handle, url=url, method="GET")
        response = client.get(endpoint=endpoint, headers=auth_headers)
    except LiveCanaryHttpError as exc:
        raise LiveCanaryLeverageObservationError(f"LEVERAGE_FRESH_GET_FAILED:{exc}") from exc
    finally:
        auth_headers.clear()
        release_live_canary_ephemeral_material_v1(handle)
    response_time = utc_now_iso_v1()
    payload = parse_json_object_v1(response.body_bytes)
    observation_class = classify_leverage_observation_class_v1(
        get_performed=True,
        http_status=int(response.status_code),
        payload=payload,
    )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / run_id
    pack.mkdir(parents=True, exist_ok=False)
    data = payload.get("data") if isinstance(payload, Mapping) else None
    raw_rows: list[dict[str, Any]] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, Mapping):
                raw_rows.append(
                    {
                        "instId": item.get("instId") if "instId" in item else None,
                        "ccy": item.get("ccy") if "ccy" in item else None,
                        "mgnMode": item.get("mgnMode") if "mgnMode" in item else None,
                        "posSide": item.get("posSide") if "posSide" in item else None,
                        "lever": item.get("lever") if "lever" in item else None,
                    }
                )
    raw_fields = {
        "HTTP_STATUS": int(response.status_code),
        "VENUE_CODE": str(payload.get("code") or ""),
        "VENUE_MSG": str(payload.get("msg") or ""),
        "REQUEST_INST_ID": DEFAULT_INSTRUMENT_ID,
        "REQUEST_MGN_MODE": mgn_mode,
        "BOUND_INST_FAMILY": DEFAULT_INST_FAMILY,
        "INST_FAMILY_PARSED_FROM_INSTID": False,
        "raw_rows": raw_rows,
    }
    if observation_class != OBSERVATION_CLASS_SUCCESS_NUMERIC:
        forensic = {
            "DOCUMENT_CLASS": "LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
            "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
            "ENDPOINT": endpoint,
            "GET_REQUEST_COUNT_AUTHENTICATED": 1,
            "HOST": REUSED_BINDING_REST_HOST,
            "METHOD": "GET",
            "OBSERVATION_CLASS": observation_class,
            "OWNER_GO": owned,
            "POST_COUNT": 0,
            "AUTH_HEADER_SENT": True,
            "AUTH_REQUIRED": True,
            "SECRET_VALUES_INCLUDED": False,
            "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
            "ZERO_NORMALIZATION_PERFORMED": False,
            "DEFAULT_LEVERAGE_USED": False,
            "HISTORICAL_BTC_LEVERAGE_REUSED": False,
            "raw_fields": raw_fields,
            "payload": payload,
        }
        encoded = json.dumps(forensic, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (pack / "GET_SNAPSHOT.sanitized.json").write_bytes(encoded)
        (pack / "MANIFEST.sha256").write_text(
            f"{hashlib.sha256(encoded).hexdigest()}  GET_SNAPSHOT.sanitized.json\n",
            encoding="utf-8",
        )
        _raise_for_observation_class(observation_class)
    try:
        observation = acquire_fresh_leverage_observation_from_payload_v1(
            pretrade_decision_id=pretrade_decision_id,
            payload=payload,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            mgn_mode=mgn_mode,
            observed_at_utc=response_time,
            endpoint=endpoint,
            http_status=int(response.status_code),
            get_performed=True,
            auth_header_sent=True,
            body_sha256=hashlib.sha256(response.body_bytes).hexdigest(),
        )
        validated = validate_fresh_leverage_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            leverage_domain=LEVERAGE_OUTPUT_DOMAIN,
            mgn_mode=mgn_mode,
        )
        observation_class = OBSERVATION_CLASS_SUCCESS_NUMERIC
    except LiveCanaryLeverageObservationError as exc:
        forensic = {
            "DOCUMENT_CLASS": "LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
            "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
            "ENDPOINT": endpoint,
            "GET_REQUEST_COUNT_AUTHENTICATED": 1,
            "HOST": REUSED_BINDING_REST_HOST,
            "METHOD": "GET",
            "OBSERVATION_CLASS": OBSERVATION_CLASS_MALFORMED,
            "OWNER_GO": owned,
            "POST_COUNT": 0,
            "AUTH_HEADER_SENT": True,
            "AUTH_REQUIRED": True,
            "SECRET_VALUES_INCLUDED": False,
            "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
            "ZERO_NORMALIZATION_PERFORMED": False,
            "DEFAULT_LEVERAGE_USED": False,
            "HISTORICAL_BTC_LEVERAGE_REUSED": False,
            "FAIL_CLOSED_REASON": str(exc),
            "raw_fields": raw_fields,
            "payload": payload,
        }
        encoded = json.dumps(forensic, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (pack / "GET_SNAPSHOT.sanitized.json").write_bytes(encoded)
        (pack / "MANIFEST.sha256").write_text(
            f"{hashlib.sha256(encoded).hexdigest()}  GET_SNAPSHOT.sanitized.json\n",
            encoding="utf-8",
        )
        raise
    snapshot = {
        "AUTHENTICATION_REQUIREMENT": "AUTHENTICATED_PRIVATE_GET",
        "AUTH_HEADER_SENT": True,
        "AUTH_REQUIRED": True,
        "AUTH_CLASS": LEVERAGE_AUTH_CLASS,
        "COOKIE_HEADER_SENT": False,
        "DOCUMENT_CLASS": "LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
        "ENDPOINT": endpoint,
        "EVIDENCE_READ_ONLY": True,
        "GET_REQUEST_COUNT_AUTHENTICATED": 1,
        "GET_REQUEST_COUNT_PUBLIC": 0,
        "HOST": REUSED_BINDING_REST_HOST,
        "METHOD": "GET",
        "NO_POST": True,
        "OWNER_GO": owned,
        "POST_COUNT": 0,
        "SECRET_VALUES_INCLUDED": False,
        "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "TARGET_MGN_MODE": mgn_mode,
        "TARGET_VENUE": "OKX_EEA",
        "BOUND_INST_FAMILY": DEFAULT_INST_FAMILY,
        "LEVERAGE_SCOPE": LEVERAGE_SCOPE,
        "REQUEST_INSTID_ROLE": LEVERAGE_REQUEST_INSTID_ROLE,
        "INST_FAMILY_PARSED_FROM_INSTID": False,
        "MGNMODE_IS_NOT_TDMODE": MGNMODE_IS_NOT_TDMODE,
        "MGNMODE_IS_NOT_ACCOUNT_MODE": MGNMODE_IS_NOT_ACCOUNT_MODE,
        "TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF": TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF,
        "ACCOUNT_MODE": ACCOUNT_MODE,
        "ACCOUNT_MODE_PROOF_STATUS": ACCOUNT_MODE_PROOF_STATUS,
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "HISTORICAL_BTC_LEVERAGE_REUSED": False,
        "DEFAULT_LEVERAGE_USED": False,
        "ZERO_NORMALIZATION_PERFORMED": False,
        "MAX_LEVERAGE_SUBSTITUTION_USED": False,
        "IMR_MMR_RECONSTRUCTION_USED": False,
        "FRESHNESS_POLICY": LEVERAGE_FRESHNESS_POLICY,
        "TS_AGE_BOUND": LEVERAGE_TS_AGE_BOUND,
        "NO_TS_FIELD": LEVERAGE_NO_TS_FIELD,
        "observation": observation.to_dict(),
        "validated": {
            "lever": format(validated.lever, "f"),
            "comparison_domain": validated.comparison_domain,
            "mgn_mode": validated.mgn_mode,
            "pos_side": validated.pos_side,
            "inst_family": validated.inst_family,
            "observation_class": observation_class,
        },
        "raw_fields": raw_fields,
        "http_evidence": {
            "SECRET_VALUES_INCLUDED": False,
            "body_byte_len": len(response.body_bytes),
            "body_sha256": hashlib.sha256(response.body_bytes).hexdigest(),
            "http_status": response.status_code,
            "json_parse_ok": True,
            "okx_code": str(payload.get("code") or ""),
            "okx_msg": str(payload.get("msg") or ""),
            "response_headers_safe": _safe_headers(response.response_headers_safe),
        },
        "payload": payload,
        "request_event_time": request_time,
        "response_event_time": response_time,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
    }
    summary = {
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "DOCUMENT_CLASS": "LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "GET_REQUEST_COUNT_AUTHENTICATED": 1,
        "HOST": REUSED_BINDING_REST_HOST,
        "HTTP_STATUS": response.status_code,
        "LIVE_AUTHORIZED": False,
        "METHOD": "GET",
        "OKX_CODE": observation.venue_code,
        "OWNER_GO": owned,
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "POST_COUNT": 0,
        "PRETRADE_DECISION_ID": pretrade_decision_id,
        "RESPONSE_BODY_SHA256": hashlib.sha256(response.body_bytes).hexdigest(),
        "RUN_ID": run_id,
        "SECRET_VALUES_INCLUDED": False,
        "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "OBSERVATION_CLASS": observation_class,
        "LEVER_RAW": observation.lever_raw,
        "MGN_MODE_RAW": observation.mgn_mode_raw,
        "POS_SIDE_RAW": observation.pos_side_raw,
        "INST_ID_RAW": observation.inst_id_raw,
        "ok": True,
    }
    claims = {
        "FRESH_GET_PERFORMED": True,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "HISTORICAL_BTC_LEVERAGE_REUSED": False,
        "NETWORK_POST_PERFORMED": False,
        "NETWORK_AUTHENTICATED_GET_PERFORMED": True,
        "ZERO_NORMALIZATION_PERFORMED": False,
        "DEFAULT_LEVERAGE_USED": False,
        "MAX_LEVERAGE_SUBSTITUTION_USED": False,
        "IMR_MMR_RECONSTRUCTION_USED": False,
        "TRADING_PERFORMED": False,
        "SET_LEVERAGE_EXECUTED": False,
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "MGNMODE_USED_AS_ACCOUNT_MODE_PROOF": False,
        "TDMODE_USED_AS_ACCOUNT_MODE_PROOF": False,
    }
    redaction = {
        "AUTH_HEADER_PERSISTED": False,
        "COOKIE_PERSISTED": False,
        "SECRET_VALUES_INCLUDED": False,
    }
    zero_write = {
        "DELETE_COUNT": 0,
        "FUNDING_EXECUTED": False,
        "GET_COUNT_PUBLIC": 0,
        "GET_COUNT_AUTHENTICATED": 1,
        "ORDER_EXECUTED": False,
        "PATCH_COUNT": 0,
        "POST_COUNT": 0,
        "PUT_COUNT": 0,
        "RETRY_EXECUTED": False,
        "SET_LEVERAGE_EXECUTED": False,
    }
    persistence = {"ok": True, "OPERATIVE_CACHE": False, "pack": str(pack)}
    files = {
        "GET_SNAPSHOT.sanitized.json": snapshot,
        "SUMMARY.json": summary,
        "claims.json": claims,
        "redaction_check.json": redaction,
        "zero_write_assertions.json": zero_write,
        "PERSISTENCE_RESULT.json": persistence,
    }
    digest_lines: list[str] = []
    for name, body in files.items():
        encoded = json.dumps(body, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (pack / name).write_bytes(encoded)
        digest_lines.append(f"{hashlib.sha256(encoded).hexdigest()}  {name}")
    (pack / "MANIFEST.sha256").write_text("\n".join(digest_lines) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "run_id": run_id,
        "pack": str(pack),
        "observation": observation.to_dict(),
        "http_status": response.status_code,
        "venue_code": observation.venue_code,
        "observed_at_utc": observation.observed_at_utc,
        "endpoint": endpoint,
        "observation_class": observation_class,
        "lever": format(validated.lever, "f"),
        "mgn_mode": validated.mgn_mode,
        "pos_side": validated.pos_side,
        "inst_family": validated.inst_family,
    }
