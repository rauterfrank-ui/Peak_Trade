"""Versioned config schema for §11.13.3 LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.constants_v1 import (
    CONFIG_VERSION,
    DEFAULT_MAX_REQUEST_COUNT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    ENDPOINT_ALLOWLIST,
    MAX_REQUEST_COUNT_HARD_CAP,
    MAX_RETRIES_HARD_CAP,
    MAX_TIMEOUT_SECONDS,
    METHOD_ALLOWLIST,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_ENVIRONMENT,
    SCHEMA_VERSION,
)


class LiveShadowReconConfigError(RuntimeError):
    """Fail-closed config violation."""


@dataclass(frozen=True)
class LiveShadowReconConfigV1:
    environment: str
    venue: str
    entity: str
    region: str
    rest_host: str
    rest_base: str
    account_scope: str
    instrument_scope: str | None
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
    config_version: str = CONFIG_VERSION
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "venue": self.venue,
            "entity": self.entity,
            "region": self.region,
            "rest_host": self.rest_host,
            "rest_base": self.rest_base,
            "account_scope": self.account_scope,
            "instrument_scope": self.instrument_scope,
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
        }

    def digest(self) -> str:
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


def _as_tuple_str(value: Any, *, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        out = tuple(str(v).strip() for v in value if str(v).strip())
        return out
    raise LiveShadowReconConfigError(f"CONFIG_FIELD_TYPE_INVALID:{field}")


def load_live_shadow_recon_config_v1(payload: Mapping[str, Any]) -> LiveShadowReconConfigV1:
    """Load config. Productive fields may be empty; execute/preflight gates fail closed."""
    if not isinstance(payload, Mapping):
        raise LiveShadowReconConfigError("CONFIG_PAYLOAD_MUST_BE_MAPPING")

    environment = str(payload.get("environment", "")).strip().upper()
    venue = str(payload.get("venue", "")).strip()
    entity = str(payload.get("entity", payload.get("venue_entity", ""))).strip()
    region = str(payload.get("region", "")).strip()
    rest_host = str(payload.get("rest_host", "")).strip().lower()
    rest_base = str(payload.get("rest_base", "")).strip()
    account_scope = str(payload.get("account_scope", payload.get("account_identity", ""))).strip()
    instrument_raw = payload.get("instrument_scope")
    instrument_scope = None if instrument_raw in (None, "") else str(instrument_raw).strip()
    secretref_uri = str(payload.get("secretref_uri", payload.get("secret_reference", ""))).strip()
    credential_class = str(payload.get("credential_class", REQUIRED_CREDENTIAL_CLASS)).strip()
    methods = _as_tuple_str(
        payload.get("method_allowlist", METHOD_ALLOWLIST), field="method_allowlist"
    )
    endpoints = _as_tuple_str(
        payload.get("endpoint_allowlist", ENDPOINT_ALLOWLIST), field="endpoint_allowlist"
    )
    max_request_count = int(payload.get("max_request_count", DEFAULT_MAX_REQUEST_COUNT))
    timeout_seconds = float(payload.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS))
    max_retries = int(payload.get("max_retries", DEFAULT_MAX_RETRIES))
    evidence_root = str(payload.get("evidence_root", "")).strip()
    evidence_version = str(
        payload.get(
            "evidence_version", "section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1"
        )
    ).strip()
    expected_live_marker = str(payload.get("expected_live_marker", "LIVE")).strip().upper()
    expected_demo_marker_absent = bool(payload.get("expected_demo_marker_absent", True))
    allowlist = _as_tuple_str(
        payload.get("owner_declared_host_allowlist", ()),
        field="owner_declared_host_allowlist",
    )

    if methods != METHOD_ALLOWLIST:
        raise LiveShadowReconConfigError("METHOD_ALLOWLIST_MUST_BE_GET_ONLY")
    if max_request_count < 1 or max_request_count > MAX_REQUEST_COUNT_HARD_CAP:
        raise LiveShadowReconConfigError("MAX_REQUEST_COUNT_OUT_OF_BOUNDS")
    if max_retries < 0 or max_retries > MAX_RETRIES_HARD_CAP:
        raise LiveShadowReconConfigError("MAX_RETRIES_OUT_OF_BOUNDS")
    if timeout_seconds <= 0 or timeout_seconds > MAX_TIMEOUT_SECONDS:
        raise LiveShadowReconConfigError("TIMEOUT_OUT_OF_BOUNDS")
    if not endpoints:
        raise LiveShadowReconConfigError("ENDPOINT_ALLOWLIST_REQUIRED")
    for ep in endpoints:
        if ep not in ENDPOINT_ALLOWLIST:
            raise LiveShadowReconConfigError(f"ENDPOINT_NOT_IN_CANONICAL_ALLOWLIST:{ep}")

    return LiveShadowReconConfigV1(
        environment=environment or REQUIRED_ENVIRONMENT,
        venue=venue,
        entity=entity,
        region=region,
        rest_host=rest_host,
        rest_base=rest_base,
        account_scope=account_scope,
        instrument_scope=instrument_scope,
        secretref_uri=secretref_uri,
        credential_class=credential_class or REQUIRED_CREDENTIAL_CLASS,
        method_allowlist=METHOD_ALLOWLIST,
        endpoint_allowlist=endpoints,
        max_request_count=max_request_count,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        evidence_root=evidence_root,
        evidence_version=evidence_version,
        expected_live_marker=expected_live_marker or "LIVE",
        expected_demo_marker_absent=expected_demo_marker_absent,
        owner_declared_host_allowlist=allowlist,
    )


def require_execute_time_fields_v1(config: LiveShadowReconConfigV1) -> None:
    """Deterministic FAIL_CLOSED_PRE_FLIGHT before any network access."""
    missing: list[str] = []
    for field, value in (
        ("venue", config.venue),
        ("entity", config.entity),
        ("region", config.region),
        ("rest_host", config.rest_host),
        ("account_scope", config.account_scope),
        ("secretref_uri", config.secretref_uri),
        ("credential_class", config.credential_class),
    ):
        if not str(value or "").strip():
            missing.append(field)
    if missing:
        raise LiveShadowReconConfigError("FAIL_CLOSED_PRE_FLIGHT:MISSING:" + ",".join(missing))
    if config.environment != REQUIRED_ENVIRONMENT:
        raise LiveShadowReconConfigError("FAIL_CLOSED_PRE_FLIGHT:ENVIRONMENT_NOT_LIVE")
    if config.credential_class != REQUIRED_CREDENTIAL_CLASS:
        raise LiveShadowReconConfigError("FAIL_CLOSED_PRE_FLIGHT:CREDENTIAL_CLASS")
    if not config.expected_demo_marker_absent:
        raise LiveShadowReconConfigError("FAIL_CLOSED_PRE_FLIGHT:DEMO_MARKER_MUST_BE_ABSENT")


def load_live_shadow_recon_config_from_json_file_v1(path: Path | str) -> LiveShadowReconConfigV1:
    text = Path(path).read_text(encoding="utf-8")
    payload = json.loads(text)
    if not isinstance(payload, Mapping):
        raise LiveShadowReconConfigError("CONFIG_FILE_MUST_BE_OBJECT")
    return load_live_shadow_recon_config_v1(payload)


def example_incomplete_config_dict_v1() -> dict[str, Any]:
    """Schema example with productive fields intentionally empty."""
    return {
        "environment": "LIVE",
        "venue": "",
        "entity": "",
        "region": "",
        "rest_host": "",
        "rest_base": "",
        "account_scope": "",
        "instrument_scope": None,
        "secretref_uri": "",
        "credential_class": REQUIRED_CREDENTIAL_CLASS,
        "method_allowlist": list(METHOD_ALLOWLIST),
        "endpoint_allowlist": list(ENDPOINT_ALLOWLIST),
        "max_request_count": DEFAULT_MAX_REQUEST_COUNT,
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "max_retries": DEFAULT_MAX_RETRIES,
        "evidence_root": "evidence/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1",
        "evidence_version": "section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1",
        "expected_live_marker": "LIVE",
        "expected_demo_marker_absent": True,
        "owner_declared_host_allowlist": [],
        "config_version": CONFIG_VERSION,
        "schema_version": SCHEMA_VERSION,
        "notes": "Owner must fill productive fields at execute time. Empty fields fail closed pre-flight.",
    }
