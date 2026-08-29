"""Config loader for §11.13.5 LIVE_CANARY_MINIMUM_EXPOSURE."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CONFIG_VERSION,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    DEFAULT_SIDE,
    DEFAULT_TD_MODE,
    FORBIDDEN_ENVIRONMENTS,
    FORBIDDEN_HOST_MARKERS,
    ORDER_COUNT_LIMIT,
    POSITION_COUNT_LIMIT,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_ENVIRONMENT,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_ENTITY,
    REUSED_BINDING_REGION,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    REUSED_SECTION_11_13_4_BINDING_SOURCE,
    SCHEMA_VERSION,
    SECRETREF_CANARY_PATH_MARKER,
    SECRETREF_FORBIDDEN_CROSS_PACKAGE_MARKERS,
    SECRETREF_FORBIDDEN_PATH_MARKERS,
    SECRETREF_URI_PREFIX,
)


class LiveCanaryConfigError(RuntimeError):
    """Fail-closed config violation."""


@dataclass(frozen=True)
class LiveCanaryConfigV1:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    def digest(self) -> str:
        body = json.dumps(self.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(body.encode("utf-8")).hexdigest()


def example_incomplete_config_dict_v1() -> dict[str, Any]:
    return {
        "environment": "LIVE",
        "venue": "",
        "entity": "",
        "region": "",
        "rest_host": "",
        "rest_base": "",
        "account_scope": "",
        "instrument_id": DEFAULT_INSTRUMENT_ID,
        "side": DEFAULT_SIDE,
        "order_type": DEFAULT_ORDER_TYPE,
        "td_mode": DEFAULT_TD_MODE,
        "instrument_min_sz": "",
        "instrument_lot_sz": "",
        "instrument_ct_val": "",
        "instrument_tick_sz": "",
        "quantity": "",
        "max_notional": "",
        "position_count_limit": POSITION_COUNT_LIMIT,
        "order_count_limit": ORDER_COUNT_LIMIT,
        "secretref_uri": "",
        "credential_class": REQUIRED_CREDENTIAL_CLASS,
        "endpoint_allowlist_read": [
            "/api/v5/account/balance",
            "/api/v5/account/config",
            "/api/v5/account/positions",
            "/api/v5/account/max-size",
            "/api/v5/trade/orders-pending",
            "/api/v5/market/ticker",
            "/api/v5/public/instruments",
            "/api/v5/public/price-limit",
        ],
        "submit_endpoint": "/api/v5/trade/order",
        "cancel_endpoint": "/api/v5/trade/cancel-order",
        "timeout_seconds": 10.0,
        "max_retries": 2,
        "evidence_root": "evidence/ops/section_11_13_5_live_canary_minimum_exposure_proven_v1",
        "evidence_version": "section_11_13_5_live_canary_minimum_exposure_proven_v1",
        "expected_live_marker": "LIVE",
        "expected_demo_marker_absent": True,
        "owner_declared_host_allowlist": [],
        "config_version": CONFIG_VERSION,
        "schema_version": SCHEMA_VERSION,
        "predecessor_dry_run_evidence_root": REUSED_SECTION_11_13_4_BINDING_SOURCE,
        "notes": (
            "Owner fills productive fields at future execute time. Instrument minSz/lotSz/"
            "ctVal/tickSz must come from venue instrument metadata. SecretRef must use "
            "/live-canary-minimum-exposure/ path. Instrument minSz/lotSz/ctVal/tickSz "
            "are derived from venue GET at execute and must not be invented. "
            "Authoring/transport-prep does not authorize execute. Flatten execute "
            "defaults remain denied."
        ),
        "flatten_live_wire_enabled": False,
        "flatten_execute_token": "",
        "flatten_execute_purpose": "",
        "flatten_execute_owner_go": "",
        "flatten_execute_bound_origin_main_sha": "",
        "flatten_allow_productive_wire_send": False,
    }


def _reject_forbidden_host(host: str) -> None:
    lowered = host.lower()
    for marker in FORBIDDEN_HOST_MARKERS:
        if marker in lowered:
            raise LiveCanaryConfigError(f"FORBIDDEN_HOST_MARKER:{marker}")


def _validate_secretref(uri: str) -> None:
    if not uri.startswith(SECRETREF_URI_PREFIX):
        raise LiveCanaryConfigError("SECRETREF_URI_PREFIX_REQUIRED")
    lowered = uri.lower()
    if SECRETREF_CANARY_PATH_MARKER not in lowered:
        raise LiveCanaryConfigError("SECRETREF_CANARY_PATH_MARKER_REQUIRED")
    for marker in SECRETREF_FORBIDDEN_PATH_MARKERS:
        if marker in lowered:
            raise LiveCanaryConfigError(f"SECRETREF_FORBIDDEN_PATH:{marker}")
    for marker in SECRETREF_FORBIDDEN_CROSS_PACKAGE_MARKERS:
        if marker in lowered:
            raise LiveCanaryConfigError(f"SECRETREF_CROSS_PACKAGE_FORBIDDEN:{marker}")


def load_live_canary_config_v1(
    payload: Mapping[str, Any],
    *,
    require_execute_fields: bool = False,
) -> LiveCanaryConfigV1:
    data = dict(payload)
    env = str(data.get("environment") or "").strip().upper()
    if env != REQUIRED_ENVIRONMENT:
        raise LiveCanaryConfigError(f"ENVIRONMENT_MUST_BE_LIVE:{env or '<empty>'}")
    if env in FORBIDDEN_ENVIRONMENTS:
        raise LiveCanaryConfigError(f"FORBIDDEN_ENVIRONMENT:{env}")

    if str(data.get("config_version") or "") != CONFIG_VERSION:
        raise LiveCanaryConfigError("CONFIG_VERSION_MISMATCH")
    if str(data.get("schema_version") or "") != SCHEMA_VERSION:
        raise LiveCanaryConfigError("SCHEMA_VERSION_MISMATCH")

    if int(data.get("position_count_limit", -1)) != POSITION_COUNT_LIMIT:
        raise LiveCanaryConfigError("POSITION_COUNT_LIMIT_MUST_BE_1")
    if int(data.get("order_count_limit", -1)) != ORDER_COUNT_LIMIT:
        raise LiveCanaryConfigError("ORDER_COUNT_LIMIT_MUST_BE_1")

    if require_execute_fields:
        require_execute_time_fields_v1(data)
    return LiveCanaryConfigV1(payload=data)


def require_execute_time_fields_v1(payload: Mapping[str, Any]) -> None:
    required = (
        "venue",
        "entity",
        "region",
        "rest_host",
        "rest_base",
        "account_scope",
        "instrument_id",
        "secretref_uri",
        "credential_class",
    )
    for key in required:
        if not str(payload.get(key) or "").strip():
            raise LiveCanaryConfigError(f"EXECUTE_FIELD_REQUIRED:{key}")
    _reject_forbidden_host(str(payload["rest_host"]))
    _validate_secretref(str(payload["secretref_uri"]))
    if str(payload.get("credential_class")) != REQUIRED_CREDENTIAL_CLASS:
        raise LiveCanaryConfigError("CREDENTIAL_CLASS_MISMATCH")
    if str(payload.get("order_type") or "").upper() != "LIMIT":
        raise LiveCanaryConfigError("ORDER_TYPE_MUST_BE_LIMIT")
    allowlist = payload.get("owner_declared_host_allowlist") or []
    if str(payload["rest_host"]) not in allowlist:
        raise LiveCanaryConfigError("REST_HOST_NOT_IN_OWNER_ALLOWLIST")
    if str(payload.get("venue") or "") != REUSED_BINDING_VENUE:
        raise LiveCanaryConfigError("VENUE_BINDING_MISMATCH")
    if str(payload.get("entity") or "") != REUSED_BINDING_ENTITY:
        raise LiveCanaryConfigError("ENTITY_BINDING_MISMATCH")
    if str(payload.get("region") or "") != REUSED_BINDING_REGION:
        raise LiveCanaryConfigError("REGION_BINDING_MISMATCH")
    if str(payload.get("rest_host") or "") != REUSED_BINDING_REST_HOST:
        raise LiveCanaryConfigError("REST_HOST_BINDING_MISMATCH")
    if str(payload.get("account_scope") or "") != REUSED_BINDING_ACCOUNT_SCOPE:
        raise LiveCanaryConfigError("ACCOUNT_SCOPE_BINDING_MISMATCH")
    if str(payload.get("instrument_id") or "") != DEFAULT_INSTRUMENT_ID:
        raise LiveCanaryConfigError("INSTRUMENT_BINDING_MISMATCH")


def load_live_canary_config_from_json_file_v1(path: str | Path) -> LiveCanaryConfigV1:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LiveCanaryConfigError("CONFIG_JSON_OBJECT_REQUIRED")
    return load_live_canary_config_v1(payload)
