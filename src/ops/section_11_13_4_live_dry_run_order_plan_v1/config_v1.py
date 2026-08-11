"""Config loader for §11.13.4 LIVE_DRY_RUN_ORDER_PLAN."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    CONFIG_VERSION,
    DEFAULT_FEE_BPS_ASSUMPTION,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_MAX_REQUEST_COUNT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_ORDER_TYPE,
    DEFAULT_QUANTITY,
    DEFAULT_SIDE,
    DEFAULT_SLIPPAGE_BPS_ASSUMPTION,
    DEFAULT_TD_MODE,
    DEFAULT_TIMEOUT_SECONDS,
    ENDPOINT_ALLOWLIST,
    EVIDENCE_DIRNAME,
    FORBIDDEN_ENVIRONMENTS,
    FORBIDDEN_HOST_MARKERS,
    MAX_REQUEST_COUNT_HARD_CAP,
    MAX_RETRIES_HARD_CAP,
    MAX_TIMEOUT_SECONDS,
    METHOD_ALLOWLIST,
    MIN_NOTIONAL_USDT_ASSUMPTION,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_ENVIRONMENT,
    SCHEMA_VERSION,
)


class LiveDryRunOrderPlanConfigError(RuntimeError):
    """Fail-closed config violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class LiveDryRunOrderPlanConfigV1:
    environment: str
    venue: str
    entity: str
    region: str
    rest_host: str
    rest_base: str
    account_scope: str
    instrument_id: str
    side: str
    order_type: str
    quantity: str
    td_mode: str
    fee_bps_assumption: str
    slippage_bps_assumption: str
    min_notional_usdt_assumption: str
    secretref_uri: str
    credential_class: str
    method_allowlist: tuple[str, ...]
    endpoint_allowlist: tuple[str, ...]
    max_request_count: int
    timeout_seconds: float
    max_retries: int
    evidence_root: str
    evidence_version: str
    expected_live_marker: str
    expected_demo_marker_absent: bool
    owner_declared_host_allowlist: tuple[str, ...]
    config_version: str
    schema_version: str
    predecessor_shadow_evidence_root: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "venue": self.venue,
            "entity": self.entity,
            "region": self.region,
            "rest_host": self.rest_host,
            "rest_base": self.rest_base,
            "account_scope": self.account_scope,
            "instrument_id": self.instrument_id,
            "side": self.side,
            "order_type": self.order_type,
            "quantity": self.quantity,
            "td_mode": self.td_mode,
            "fee_bps_assumption": self.fee_bps_assumption,
            "slippage_bps_assumption": self.slippage_bps_assumption,
            "min_notional_usdt_assumption": self.min_notional_usdt_assumption,
            "secretref_uri": self.secretref_uri,
            "credential_class": self.credential_class,
            "method_allowlist": list(self.method_allowlist),
            "endpoint_allowlist": list(self.endpoint_allowlist),
            "max_request_count": self.max_request_count,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "evidence_root": self.evidence_root,
            "evidence_version": self.evidence_version,
            "expected_live_marker": self.expected_live_marker,
            "expected_demo_marker_absent": self.expected_demo_marker_absent,
            "owner_declared_host_allowlist": list(self.owner_declared_host_allowlist),
            "config_version": self.config_version,
            "schema_version": self.schema_version,
            "predecessor_shadow_evidence_root": self.predecessor_shadow_evidence_root,
            "notes": self.notes,
        }

    def digest(self) -> str:
        return hashlib.sha256(_canonical_dumps(self.to_dict()).encode("utf-8")).hexdigest()


def load_live_dry_run_order_plan_config_v1(
    payload: Mapping[str, Any],
) -> LiveDryRunOrderPlanConfigV1:
    environment = str(payload.get("environment", "")).strip().upper()
    if environment != REQUIRED_ENVIRONMENT:
        raise LiveDryRunOrderPlanConfigError(f"ENVIRONMENT_MUST_BE_LIVE:{environment}")
    if environment in FORBIDDEN_ENVIRONMENTS:
        raise LiveDryRunOrderPlanConfigError(f"FORBIDDEN_ENVIRONMENT:{environment}")

    venue = str(payload.get("venue", "")).strip()
    entity = str(payload.get("entity", "")).strip()
    region = str(payload.get("region", "")).strip()
    rest_host = str(payload.get("rest_host", "")).strip().lower()
    rest_base = str(payload.get("rest_base", "")).strip()
    account_scope = str(payload.get("account_scope", "")).strip()
    instrument_id = str(payload.get("instrument_id", DEFAULT_INSTRUMENT_ID)).strip()
    side = str(payload.get("side", DEFAULT_SIDE)).strip().upper()
    order_type = str(payload.get("order_type", DEFAULT_ORDER_TYPE)).strip().upper()
    quantity = str(payload.get("quantity", DEFAULT_QUANTITY)).strip()
    td_mode = str(payload.get("td_mode", DEFAULT_TD_MODE)).strip().lower()
    fee_bps = str(payload.get("fee_bps_assumption", DEFAULT_FEE_BPS_ASSUMPTION)).strip()
    slip_bps = str(payload.get("slippage_bps_assumption", DEFAULT_SLIPPAGE_BPS_ASSUMPTION)).strip()
    min_notional = str(
        payload.get("min_notional_usdt_assumption", MIN_NOTIONAL_USDT_ASSUMPTION)
    ).strip()
    secretref_uri = str(payload.get("secretref_uri", payload.get("secret_reference", ""))).strip()
    credential_class = str(payload.get("credential_class", REQUIRED_CREDENTIAL_CLASS)).strip()

    methods = tuple(
        str(x).strip().upper() for x in payload.get("method_allowlist", METHOD_ALLOWLIST)
    )
    if methods != METHOD_ALLOWLIST:
        raise LiveDryRunOrderPlanConfigError("METHOD_ALLOWLIST_MUST_BE_GET_ONLY")

    endpoints = tuple(str(x).strip() for x in payload.get("endpoint_allowlist", ENDPOINT_ALLOWLIST))
    for ep in endpoints:
        if ep not in ENDPOINT_ALLOWLIST:
            raise LiveDryRunOrderPlanConfigError(f"ENDPOINT_NOT_IN_PACKAGE_ALLOWLIST:{ep}")

    max_request_count = int(payload.get("max_request_count", DEFAULT_MAX_REQUEST_COUNT))
    if max_request_count < 1 or max_request_count > MAX_REQUEST_COUNT_HARD_CAP:
        raise LiveDryRunOrderPlanConfigError("MAX_REQUEST_COUNT_OUT_OF_BOUNDS")
    timeout_seconds = float(payload.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS))
    if timeout_seconds <= 0 or timeout_seconds > MAX_TIMEOUT_SECONDS:
        raise LiveDryRunOrderPlanConfigError("TIMEOUT_OUT_OF_BOUNDS")
    max_retries = int(payload.get("max_retries", DEFAULT_MAX_RETRIES))
    if max_retries < 0 or max_retries > MAX_RETRIES_HARD_CAP:
        raise LiveDryRunOrderPlanConfigError("MAX_RETRIES_OUT_OF_BOUNDS")

    host_allow = tuple(
        str(x).strip().lower()
        for x in payload.get("owner_declared_host_allowlist", [])
        if str(x).strip()
    )
    evidence_root = str(payload.get("evidence_root", f"evidence/ops/{EVIDENCE_DIRNAME}")).strip()
    evidence_version = str(payload.get("evidence_version", EVIDENCE_DIRNAME)).strip()
    predecessor = str(
        payload.get(
            "predecessor_shadow_evidence_root",
            "evidence/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1/20260811T211828Z/",
        )
    ).strip()

    return LiveDryRunOrderPlanConfigV1(
        environment=environment,
        venue=venue,
        entity=entity,
        region=region,
        rest_host=rest_host,
        rest_base=rest_base,
        account_scope=account_scope,
        instrument_id=instrument_id,
        side=side,
        order_type=order_type,
        quantity=quantity,
        td_mode=td_mode,
        fee_bps_assumption=fee_bps,
        slippage_bps_assumption=slip_bps,
        min_notional_usdt_assumption=min_notional,
        secretref_uri=secretref_uri,
        credential_class=credential_class,
        method_allowlist=methods,
        endpoint_allowlist=endpoints,
        max_request_count=max_request_count,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        evidence_root=evidence_root,
        evidence_version=evidence_version,
        expected_live_marker=str(payload.get("expected_live_marker", "LIVE")).strip(),
        expected_demo_marker_absent=bool(payload.get("expected_demo_marker_absent", True)),
        owner_declared_host_allowlist=host_allow,
        config_version=str(payload.get("config_version", CONFIG_VERSION)).strip(),
        schema_version=str(payload.get("schema_version", SCHEMA_VERSION)).strip(),
        predecessor_shadow_evidence_root=predecessor,
        notes=str(payload.get("notes", "")),
    )


def require_execute_time_fields_v1(config: LiveDryRunOrderPlanConfigV1) -> None:
    required = {
        "venue": config.venue,
        "entity": config.entity,
        "region": config.region,
        "rest_host": config.rest_host,
        "account_scope": config.account_scope,
        "instrument_id": config.instrument_id,
        "side": config.side,
        "order_type": config.order_type,
        "quantity": config.quantity,
        "secretref_uri": config.secretref_uri,
        "credential_class": config.credential_class,
    }
    missing = [k for k, v in required.items() if not str(v).strip()]
    if missing:
        raise LiveDryRunOrderPlanConfigError(f"EXECUTE_TIME_FIELDS_MISSING:{','.join(missing)}")
    if config.credential_class != REQUIRED_CREDENTIAL_CLASS:
        raise LiveDryRunOrderPlanConfigError("CREDENTIAL_CLASS_MISMATCH")
    host = config.rest_host.lower()
    for marker in FORBIDDEN_HOST_MARKERS:
        if marker in host:
            raise LiveDryRunOrderPlanConfigError(f"FORBIDDEN_HOST_MARKER:{marker}")
    if config.owner_declared_host_allowlist and host not in config.owner_declared_host_allowlist:
        raise LiveDryRunOrderPlanConfigError("REST_HOST_NOT_IN_OWNER_ALLOWLIST")
    if not config.rest_base:
        raise LiveDryRunOrderPlanConfigError("REST_BASE_REQUIRED")
    if not config.rest_base.lower().startswith("https://"):
        raise LiveDryRunOrderPlanConfigError("REST_BASE_MUST_BE_HTTPS")
    if config.side not in {"BUY", "SELL"}:
        raise LiveDryRunOrderPlanConfigError(f"SIDE_INVALID:{config.side}")
    if config.order_type not in {"LIMIT", "MARKET"}:
        raise LiveDryRunOrderPlanConfigError(f"ORDER_TYPE_INVALID:{config.order_type}")


def load_live_dry_run_order_plan_config_from_json_file_v1(
    path: Path | str,
) -> LiveDryRunOrderPlanConfigV1:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LiveDryRunOrderPlanConfigError("CONFIG_JSON_OBJECT_REQUIRED")
    return load_live_dry_run_order_plan_config_v1(payload)


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
        "quantity": DEFAULT_QUANTITY,
        "td_mode": DEFAULT_TD_MODE,
        "fee_bps_assumption": DEFAULT_FEE_BPS_ASSUMPTION,
        "slippage_bps_assumption": DEFAULT_SLIPPAGE_BPS_ASSUMPTION,
        "min_notional_usdt_assumption": MIN_NOTIONAL_USDT_ASSUMPTION,
        "secretref_uri": "",
        "credential_class": REQUIRED_CREDENTIAL_CLASS,
        "method_allowlist": list(METHOD_ALLOWLIST),
        "endpoint_allowlist": list(ENDPOINT_ALLOWLIST),
        "max_request_count": DEFAULT_MAX_REQUEST_COUNT,
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "max_retries": DEFAULT_MAX_RETRIES,
        "evidence_root": f"evidence/ops/{EVIDENCE_DIRNAME}",
        "evidence_version": EVIDENCE_DIRNAME,
        "expected_live_marker": "LIVE",
        "expected_demo_marker_absent": True,
        "owner_declared_host_allowlist": [],
        "config_version": CONFIG_VERSION,
        "schema_version": SCHEMA_VERSION,
        "predecessor_shadow_evidence_root": (
            "evidence/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1/"
            "20260811T211828Z/"
        ),
        "notes": (
            "Owner fills productive fields at execute time. Reuse §11.13.3 proven binding "
            "with secretref://vault/peak-trade/live-dry-run-order-plan/okx."
        ),
    }
