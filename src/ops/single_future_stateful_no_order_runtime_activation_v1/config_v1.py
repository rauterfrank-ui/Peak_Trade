"""Canonical Cap 7.2 activation config owner (no silent env activation)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    CAPABILITY_ID,
    CONFIG_RELATIVE_PATH,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    PREDECESSOR_CAPABILITY_ID,
    PREDECESSOR_MERGE_SHA,
    RUNTIME_MODE,
    SCHEMA_VERSION,
    repo_root_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.models_v1 import (
    ActivationConfigV1,
    RuntimeModeV1,
    canonical_digest_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.reason_codes_v1 import (
    ActivationFailureCodeV1,
)


class ActivationConfigError(RuntimeError):
    def __init__(self, code: ActivationFailureCodeV1, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code.value}:{detail}" if detail else code.value)


_FORBIDDEN_ENV_KEYS = (
    "PEAK_TRADE_FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE",
    "PEAK_TRADE_SIMULATED_EXECUTION_ACTIVE",
    "PEAK_TRADE_RUNTIME_ACTIVATED",
    "PEAK_TRADE_LIVE_ORDERS",
    "PEAK_TRADE_TESTNET_ORDERS",
)


def reject_env_activation_overrides_v1() -> None:
    for key in _FORBIDDEN_ENV_KEYS:
        if os.environ.get(key) is not None:
            raise ActivationConfigError(ActivationFailureCodeV1.ENV_OVERRIDE_REJECTED, key)


def compute_config_digest_v1(payload: Mapping[str, Any]) -> str:
    material = {k: payload[k] for k in sorted(payload.keys()) if k != "config_digest"}
    return canonical_digest_v1(material)


def load_activation_config_v1(
    *,
    config_path: Path | None = None,
    require_active_claim: bool = False,
) -> ActivationConfigV1:
    reject_env_activation_overrides_v1()
    path = Path(config_path) if config_path is not None else repo_root_v1() / CONFIG_RELATIVE_PATH
    if not path.is_file():
        raise ActivationConfigError(ActivationFailureCodeV1.MISSING_ACTIVATION_STATE, str(path))
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ActivationConfigError(ActivationFailureCodeV1.CORRUPT_CHECKPOINT, "config")
    if str(raw.get("schema_version")) != SCHEMA_VERSION:
        raise ActivationConfigError(
            ActivationFailureCodeV1.CORRUPT_CHECKPOINT,
            f"schema:{raw.get('schema_version')}",
        )
    if str(raw.get("capability_id")) != CAPABILITY_ID:
        raise ActivationConfigError(
            ActivationFailureCodeV1.CORRUPT_CHECKPOINT,
            f"capability_id:{raw.get('capability_id')}",
        )
    digest = compute_config_digest_v1(raw)
    declared = str(raw.get("config_digest") or "")
    if declared and declared != digest:
        raise ActivationConfigError(
            ActivationFailureCodeV1.CONFIG_DIGEST_MISMATCH,
            f"{declared}!={digest}",
        )
    mode = RuntimeModeV1(str(raw.get("runtime_mode") or RUNTIME_MODE))
    if mode.value != RUNTIME_MODE:
        raise ActivationConfigError(ActivationFailureCodeV1.RUNTIME_MODE_MISMATCH, mode.value)
    cfg = ActivationConfigV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        runtime_mode=mode,
        repository_sha_bound=str(raw.get("repository_sha_bound") or ""),
        config_digest=digest,
        stateful_runtime_ready_for_activation=bool(
            raw.get("STATEFUL_RUNTIME_READY_FOR_ACTIVATION")
        ),
        full_canonical_stateful_runtime_active=bool(
            raw.get("FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE")
        ),
        simulated_execution_active=bool(raw.get("SIMULATED_EXECUTION_ACTIVE")),
        public_md_runtime_capable=bool(raw.get("PUBLIC_MD_RUNTIME_CAPABLE", True)),
        public_md_network_session_observed=bool(
            raw.get("PUBLIC_MD_NETWORK_SESSION_OBSERVED", False)
        ),
        live_orders=bool(raw.get("LIVE_ORDERS", False)),
        testnet_orders=bool(raw.get("TESTNET_ORDERS", False)),
        paper_exchange_orders=bool(raw.get("PAPER_EXCHANGE_ORDERS", False)),
        exchange_credential_use=bool(raw.get("EXCHANGE_CREDENTIAL_USE", False)),
        real_capital_movement=bool(raw.get("REAL_CAPITAL_MOVEMENT", False)),
        multi_future_runtime_authorized=bool(raw.get("MULTI_FUTURE_RUNTIME_AUTHORIZED", False)),
        network_allowlist=str(raw.get("NETWORK_ALLOWLIST") or NETWORK_ALLOWLIST),
        http_method_allowlist=str(raw.get("HTTP_METHOD_ALLOWLIST") or HTTP_METHOD_ALLOWLIST),
        predecessor_capability_id=str(
            raw.get("predecessor_capability_id") or PREDECESSOR_CAPABILITY_ID
        ),
        predecessor_merge_sha=str(raw.get("predecessor_merge_sha") or PREDECESSOR_MERGE_SHA),
    )
    if cfg.live_orders or cfg.testnet_orders or cfg.paper_exchange_orders:
        raise ActivationConfigError(ActivationFailureCodeV1.NO_ORDER_MODE_VIOLATION, "orders_true")
    if cfg.exchange_credential_use or cfg.real_capital_movement:
        raise ActivationConfigError(
            ActivationFailureCodeV1.NO_ORDER_MODE_VIOLATION, "credential_or_capital"
        )
    if cfg.multi_future_runtime_authorized:
        raise ActivationConfigError(ActivationFailureCodeV1.NO_ORDER_MODE_VIOLATION, "multi_future")
    if cfg.public_md_network_session_observed:
        raise ActivationConfigError(
            ActivationFailureCodeV1.NO_ORDER_MODE_VIOLATION, "network_session_claimed"
        )
    if require_active_claim and not (
        cfg.stateful_runtime_ready_for_activation
        and cfg.full_canonical_stateful_runtime_active
        and cfg.simulated_execution_active
    ):
        raise ActivationConfigError(
            ActivationFailureCodeV1.ACTIVATION_NOT_READY, "active_claim_missing"
        )
    return cfg


def build_canonical_config_payload_v1(*, repository_sha: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "capability_id": CAPABILITY_ID,
        "runtime_mode": RUNTIME_MODE,
        "repository_sha_bound": repository_sha,
        "STATEFUL_RUNTIME_READY_FOR_ACTIVATION": True,
        "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": True,
        "SIMULATED_EXECUTION_ACTIVE": True,
        "PUBLIC_MD_RUNTIME_CAPABLE": True,
        "PUBLIC_MD_NETWORK_SESSION_OBSERVED": False,
        "LIVE_ORDERS": False,
        "TESTNET_ORDERS": False,
        "PAPER_EXCHANGE_ORDERS": False,
        "EXCHANGE_CREDENTIAL_USE": False,
        "REAL_CAPITAL_MOVEMENT": False,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
        "NETWORK_ALLOWLIST": NETWORK_ALLOWLIST,
        "HTTP_METHOD_ALLOWLIST": HTTP_METHOD_ALLOWLIST,
        "predecessor_capability_id": PREDECESSOR_CAPABILITY_ID,
        "predecessor_merge_sha": PREDECESSOR_MERGE_SHA,
        "owner": "ops.single_future_stateful_no_order_runtime_activation_v1",
        "note": (
            "Activation config for Cap 7.2 no-order stateful runtime. "
            "Does not authorize public-MD network sessions, live/testnet/paper "
            "exchange orders, credentials, or real capital movement."
        ),
    }
    payload["config_digest"] = compute_config_digest_v1(payload)
    return payload
