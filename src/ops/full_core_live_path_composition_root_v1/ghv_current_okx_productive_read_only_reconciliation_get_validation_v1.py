"""Bounded productive OKX read-only GET validation for Full-Core reconciliation.

Phase-7 safety gates and Phase-8 validation session. GET only. No POST.
No atomic durable mutation. No credential export.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlencode

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    METHOD_GET,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
    RECONCILIATION_READ_ONLY_GET_ALLOWLIST,
    WORK_PACKAGE_ID,
    FullCoreOrchestratedLifecycleReconciliationError,
    PostSubmitLifecycleReconciliationOrchestrationRequestV1,
    assert_orchestration_owner_gos_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    ENDPOINT_ORDERS_PENDING,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_unknown_post_attempt_read_only_reconciliation_v1 import (
    _assert_no_secrets,
)

CONTRACT_ID = "GHV_CURRENT_OKX_PRODUCTIVE_READ_ONLY_RECONCILIATION_GET_VALIDATION_V1"
MAX_VALIDATION_GET_REQUESTS = 8
VALIDATION_TIMEOUT_SECONDS = 20.0
DEMO_MODE_DISABLED = True
READ_ONLY_METHOD_ENFORCEMENT = True
LIVE_POST_DISABLED = True
ORDER_SUBMISSION_DISABLED = True
AUTO_RESUBMIT = False


class GhvOkxProductiveReadOnlyValidationError(RuntimeError):
    """Fail-closed productive read-only validation violation."""


@dataclass(frozen=True)
class ProductiveGetSafetyGateReportV1:
    offline_reproof: str
    adversarial_review: str
    authentication_identity: str
    okx_environment: str
    demo_mode: str
    read_only_method_enforcement: str
    live_post: str
    order_submission: str
    auto_resubmit: str
    endpoint_allowlist: str
    overall: str

    def to_dict(self) -> dict[str, str]:
        return {
            "offline_reproof": self.offline_reproof,
            "adversarial_review": self.adversarial_review,
            "authentication_identity": self.authentication_identity,
            "okx_environment": self.okx_environment,
            "demo_mode": self.demo_mode,
            "read_only_method_enforcement": self.read_only_method_enforcement,
            "live_post": self.live_post,
            "order_submission": self.order_submission,
            "auto_resubmit": self.auto_resubmit,
            "endpoint_allowlist": self.endpoint_allowlist,
            "overall": self.overall,
        }


@dataclass(frozen=True)
class ProductiveOkxReadOnlyValidationSessionResultV1:
    disposition: str
    get_request_count: int
    authorized_host: str
    account_config_http_status: int
    account_config_api_code: str
    orders_pending_http_status: int
    orders_pending_api_code: str
    environment_label: str
    demo_mode_detected: bool
    provider_compatible: bool
    transport_class: str
    methods_used: tuple[str, ...]
    surfaces_summary: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition,
            "get_request_count": self.get_request_count,
            "authorized_host": self.authorized_host,
            "account_config_http_status": self.account_config_http_status,
            "account_config_api_code": self.account_config_api_code,
            "orders_pending_http_status": self.orders_pending_http_status,
            "orders_pending_api_code": self.orders_pending_api_code,
            "environment_label": self.environment_label,
            "demo_mode_detected": self.demo_mode_detected,
            "provider_compatible": self.provider_compatible,
            "transport_class": self.transport_class,
            "methods_used": self.methods_used,
            "surfaces_summary": self.surfaces_summary,
            "contract_id": CONTRACT_ID,
        }

    def __repr__(self) -> str:
        return "ProductiveOkxReadOnlyValidationSessionResultV1(redacted)"


def _assert_endpoint_on_allowlist_v1(path: str) -> None:
    base = str(path or "").split("?", 1)[0]
    if base not in RECONCILIATION_READ_ONLY_GET_ALLOWLIST:
        raise GhvOkxProductiveReadOnlyValidationError(f"ENDPOINT_NOT_ALLOWLISTED:{base}")


def _api_code(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return ""
    return str(payload.get("code") or "")


def _demo_from_config_payload(payload: Any) -> bool:
    if not isinstance(payload, Mapping):
        return False
    rows = payload.get("data")
    if not isinstance(rows, list) or not rows:
        return False
    row = rows[0] if isinstance(rows[0], Mapping) else {}
    for key in ("simulatedTrading", "simulated_trading", "isDemo"):
        val = row.get(key)
        if val in {True, "true", "1", 1}:
            return True
    return False


def evaluate_productive_get_safety_gates_v1(
    *,
    offline_reproof_pass: bool,
    adversarial_review_pass: bool,
    orchestration_request: PostSubmitLifecycleReconciliationOrchestrationRequestV1,
) -> ProductiveGetSafetyGateReportV1:
    """Phase 7 gates. Does not perform network I/O."""

    if (
        EXTERNAL_EFFECT_AUTHORIZED is True
        or POST_ALLOWED is True
        or REAL_VENUE_POST_ALLOWED is True
    ):
        raise GhvOkxProductiveReadOnlyValidationError("STANDING_POST_PINS_MUST_REMAIN_FALSE")

    offline = "PASS" if offline_reproof_pass else "FAIL"
    adv = "PASS" if adversarial_review_pass else "FAIL"
    auth_id = "PENDING"
    env = "PENDING"
    demo = "DISABLED" if DEMO_MODE_DISABLED else "FAIL"
    ro = "ACTIVE" if READ_ONLY_METHOD_ENFORCEMENT else "FAIL"
    live = "DISABLED" if LIVE_POST_DISABLED else "FAIL"
    order = "DISABLED" if ORDER_SUBMISSION_DISABLED else "FAIL"
    auto = "DISABLED" if not AUTO_RESUBMIT else "FAIL"
    allow = "ACTIVE"

    try:
        assert_orchestration_owner_gos_v1(orchestration_request)
        auth_id = "VERIFIED"
        env = "PRODUCTION_EEA_OKX"
    except FullCoreOrchestratedLifecycleReconciliationError:
        auth_id = "FAIL"
        env = "FAIL"

    overall = (
        "PASS"
        if offline == "PASS"
        and adv == "PASS"
        and auth_id == "VERIFIED"
        and demo == "DISABLED"
        and ro == "ACTIVE"
        and live == "DISABLED"
        and order == "DISABLED"
        and auto == "DISABLED"
        and allow == "ACTIVE"
        else "FAIL"
    )
    return ProductiveGetSafetyGateReportV1(
        offline_reproof=offline,
        adversarial_review=adv,
        authentication_identity=auth_id,
        okx_environment=env,
        demo_mode=demo,
        read_only_method_enforcement=ro,
        live_post=live,
        order_submission=order,
        auto_resubmit=auto,
        endpoint_allowlist=allow,
        overall=overall,
    )


def run_bounded_productive_okx_read_only_validation_session_v1(
    *,
    transport: FullCoreProductiveReadOnlyGetTransportV1,
    pretrade_decision_id: str,
    instrument_id: str,
    inst_type: str = "SWAP",
) -> ProductiveOkxReadOnlyValidationSessionResultV1:
    """Phase 8: bounded GET session (auth + structure probes only)."""

    if transport.transport_class != "FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1":
        raise GhvOkxProductiveReadOnlyValidationError("TRANSPORT_CLASS")
    inst = str(instrument_id or "").strip()
    if not inst:
        raise GhvOkxProductiveReadOnlyValidationError("INSTRUMENT_ID_REQUIRED")

    surfaces: list[str] = []

    def _get(path: str, query: dict[str, str]) -> Any:
        _assert_endpoint_on_allowlist_v1(path)
        if transport.request_count >= MAX_VALIDATION_GET_REQUESTS:
            raise GhvOkxProductiveReadOnlyValidationError("MAX_VALIDATION_GET_BUDGET_EXCEEDED")
        endpoint = f"{path}?{urlencode(query)}"
        result = transport.get(
            endpoint=endpoint,
            auth_required=True,
            pretrade_decision_id=pretrade_decision_id,
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )
        if str(result.method or "").upper() != METHOD_GET:
            raise GhvOkxProductiveReadOnlyValidationError("NON_GET_METHOD_FORBIDDEN")
        surfaces.append(f"{path}:http={result.http_status}:code={_api_code(result.payload)}")
        _assert_no_secrets({"payload_code": _api_code(result.payload)})
        return result

    cfg = _get(ENDPOINT_ACCOUNT_CONFIG, {})
    pending = _get(
        ENDPOINT_ORDERS_PENDING,
        {"instType": inst_type, "instId": inst},
    )

    demo_detected = _demo_from_config_payload(cfg.payload)
    if demo_detected and DEMO_MODE_DISABLED:
        raise GhvOkxProductiveReadOnlyValidationError("DEMO_MODE_DETECTED")

    provider_ok = (
        cfg.http_status == 200
        and _api_code(cfg.payload) == "0"
        and pending.http_status == 200
        and _api_code(pending.payload) == "0"
    )

    disposition = "VALIDATION_PASS" if provider_ok else "VALIDATION_INCOMPLETE"
    return ProductiveOkxReadOnlyValidationSessionResultV1(
        disposition=disposition,
        get_request_count=int(transport.request_count),
        authorized_host=AUTHORIZED_HOST,
        account_config_http_status=int(cfg.http_status),
        account_config_api_code=_api_code(cfg.payload),
        orders_pending_http_status=int(pending.http_status),
        orders_pending_api_code=_api_code(pending.payload),
        environment_label="PRODUCTION_EEA_OKX",
        demo_mode_detected=demo_detected,
        provider_compatible=provider_ok,
        transport_class=str(transport.transport_class),
        methods_used=tuple(transport.methods_used),
        surfaces_summary=tuple(surfaces),
    )


__all__ = [
    "AUTO_RESUBMIT",
    "CONTRACT_ID",
    "DEMO_MODE_DISABLED",
    "LIVE_POST_DISABLED",
    "MAX_VALIDATION_GET_REQUESTS",
    "ORDER_SUBMISSION_DISABLED",
    "ProductiveGetSafetyGateReportV1",
    "ProductiveOkxReadOnlyValidationSessionResultV1",
    "READ_ONLY_METHOD_ENFORCEMENT",
    "WORK_PACKAGE_ID",
    "evaluate_productive_get_safety_gates_v1",
    "run_bounded_productive_okx_read_only_validation_session_v1",
]
