"""Orchestrated Full-Core post-submit lifecycle → exchange reconciliation join.

Single composition entry for offline fixtures, injected OKX transport, or scoped
productive read-only GET (explicit Owner-GO only). No import-time network. No POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    FullCoreFreshPretradeGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    OkxReadOnlyReconciliationQueryOptionsV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    FullCorePostSubmitJoinResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    FullCorePostSubmitLifecycleReconciliationJoinResultV1,
    run_full_core_post_submit_lifecycle_reconciliation_join_v1,
)

CONTRACT_ID = "FULL_CORE_ORCHESTRATED_POST_SUBMIT_LIFECYCLE_RECONCILIATION_V1"
WORK_PACKAGE_ID = "GHV_CURRENT_OKX_PRODUCTIVE_GET_ACTIVATION_READINESS_V1"
ACCEPTED_WORK_PACKAGE_OWNER_GO = "GRANTED"
ACCEPTED_PRIVATE_GET_GO = "GRANTED_SCOPED_READ_ONLY"
ACCEPTED_OFFLINE_IMPLEMENTATION_GO = "GRANTED"
K1_SESSION_OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1"
)

ORCHESTRATION_OWNER = (
    "ops.full_core_live_path_composition_root_v1."
    "full_core_orchestrated_post_submit_lifecycle_reconciliation_v1"
)


class FullCoreOrchestratedLifecycleReconciliationError(RuntimeError):
    """Fail-closed orchestrated lifecycle reconciliation violation."""


class LifecycleReconciliationOrchestrationMode(str, Enum):
    OFFLINE_FIXTURE = "OFFLINE_FIXTURE"
    INJECTED_OKX_TRANSPORT = "INJECTED_OKX_TRANSPORT"
    PRODUCTIVE_OKX_SCOPED_READ_ONLY = "PRODUCTIVE_OKX_SCOPED_READ_ONLY"


RECONCILIATION_READ_ONLY_GET_ALLOWLIST: frozenset[str] = frozenset(
    {
        ENDPOINT_ACCOUNT_CONFIG,
        "/api/v5/trade/orders-pending",
        "/api/v5/trade/orders-history",
        "/api/v5/trade/fills",
        "/api/v5/account/positions",
        "/api/v5/trade/order",
    }
)


@dataclass(frozen=True)
class PostSubmitLifecycleReconciliationOrchestrationRequestV1:
    """Explicit orchestration request. Never implied by import or cycle startup."""

    mode: LifecycleReconciliationOrchestrationMode
    work_package_owner_go: str
    private_get_go: str
    offline_implementation_go: str
    origin_main_sha: str
    decision_outcome: str
    venue_plan_identity: str
    envelope_identity: str
    submit_attempt_id: str
    local_durable_state_version: str
    pretrade_decision_id: str
    offline_fixture: OfflineExchangeFixtureV1 | None = None
    read_only_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None
    query_options: OkxReadOnlyReconciliationQueryOptionsV1 | None = None
    state_dir: Path | None = None
    apply_durable_atomic_state: bool = False
    proven_never_submitted: bool = False


def _assert_standing_pins_v1() -> None:
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise FullCoreOrchestratedLifecycleReconciliationError("EXTERNAL_EFFECT_MUST_REMAIN_FALSE")
    if POST_ALLOWED is True or REAL_VENUE_POST_ALLOWED is True:
        raise FullCoreOrchestratedLifecycleReconciliationError("POST_STANDING_MUST_REMAIN_FALSE")


def resolve_origin_main_sha_v1(*, declared: str) -> str:
    text = str(declared or "").strip().lower()
    if not text:
        raise FullCoreOrchestratedLifecycleReconciliationError("ORIGIN_MAIN_SHA_REQUIRED")
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise FullCoreOrchestratedLifecycleReconciliationError(
            "ORIGIN_MAIN_SHA_GIT_VERIFY_FAILED"
        ) from exc
    actual = str(proc.stdout or "").strip().lower()
    if actual != text:
        raise FullCoreOrchestratedLifecycleReconciliationError("ORIGIN_MAIN_SHA_DRIFT")
    return actual


def assert_orchestration_owner_gos_v1(
    request: PostSubmitLifecycleReconciliationOrchestrationRequestV1,
) -> None:
    if str(request.work_package_owner_go or "").strip() != ACCEPTED_WORK_PACKAGE_OWNER_GO:
        raise FullCoreOrchestratedLifecycleReconciliationError("WORK_PACKAGE_OWNER_GO_DENIED")
    if str(request.private_get_go or "").strip() != ACCEPTED_PRIVATE_GET_GO:
        raise FullCoreOrchestratedLifecycleReconciliationError("PRIVATE_GET_GO_DENIED")
    if str(request.offline_implementation_go or "").strip() != ACCEPTED_OFFLINE_IMPLEMENTATION_GO:
        raise FullCoreOrchestratedLifecycleReconciliationError("OFFLINE_IMPLEMENTATION_GO_DENIED")
    resolve_origin_main_sha_v1(declared=request.origin_main_sha)


def orchestrate_post_submit_lifecycle_reconciliation_v1(
    *,
    post_submit_join: FullCorePostSubmitJoinResultV1,
    binding: FullCoreAuthorizationBindingV1,
    request: PostSubmitLifecycleReconciliationOrchestrationRequestV1,
) -> FullCorePostSubmitLifecycleReconciliationJoinResultV1:
    """Run lifecycle reconciliation join under explicit mode and Owner-GO gates."""

    _assert_standing_pins_v1()
    assert_orchestration_owner_gos_v1(request)

    if request.mode is LifecycleReconciliationOrchestrationMode.OFFLINE_FIXTURE:
        if request.offline_fixture is None:
            raise FullCoreOrchestratedLifecycleReconciliationError("OFFLINE_FIXTURE_REQUIRED")
        if request.read_only_get_transport is not None:
            raise FullCoreOrchestratedLifecycleReconciliationError(
                "INJECTED_TRANSPORT_FORBIDDEN_OFFLINE"
            )
        return run_full_core_post_submit_lifecycle_reconciliation_join_v1(
            post_submit_join=post_submit_join,
            binding=binding,
            decision_outcome=request.decision_outcome,
            venue_plan_identity=request.venue_plan_identity,
            envelope_identity=request.envelope_identity,
            submit_attempt_id=request.submit_attempt_id,
            local_durable_state_version=request.local_durable_state_version,
            offline_fixture=request.offline_fixture,
            state_dir=request.state_dir,
            apply_durable_state=request.apply_durable_atomic_state,
            proven_never_submitted=request.proven_never_submitted,
        )

    if request.mode is LifecycleReconciliationOrchestrationMode.INJECTED_OKX_TRANSPORT:
        if request.read_only_get_transport is None:
            raise FullCoreOrchestratedLifecycleReconciliationError("INJECTED_TRANSPORT_REQUIRED")
        if request.offline_fixture is not None:
            raise FullCoreOrchestratedLifecycleReconciliationError(
                "OFFLINE_FIXTURE_FORBIDDEN_INJECTED"
            )
        return run_full_core_post_submit_lifecycle_reconciliation_join_v1(
            post_submit_join=post_submit_join,
            binding=binding,
            decision_outcome=request.decision_outcome,
            venue_plan_identity=request.venue_plan_identity,
            envelope_identity=request.envelope_identity,
            submit_attempt_id=request.submit_attempt_id,
            local_durable_state_version=request.local_durable_state_version,
            read_only_get_transport=request.read_only_get_transport,
            pretrade_decision_id=request.pretrade_decision_id,
            query_options=request.query_options,
            state_dir=request.state_dir,
            apply_durable_state=request.apply_durable_atomic_state,
            proven_never_submitted=request.proven_never_submitted,
            okx_read_only_forensic_profile="INJECTED",
        )

    if request.mode is LifecycleReconciliationOrchestrationMode.PRODUCTIVE_OKX_SCOPED_READ_ONLY:
        if request.read_only_get_transport is None:
            raise FullCoreOrchestratedLifecycleReconciliationError(
                "PRODUCTIVE_TRANSPORT_MUST_BE_CALLER_BOUND"
            )
        if request.apply_durable_atomic_state is True:
            raise FullCoreOrchestratedLifecycleReconciliationError(
                "PRODUCTIVE_GET_MUST_NOT_APPLY_DURABLE_ATOMIC"
            )
        transport = request.read_only_get_transport
        tc = getattr(transport, "transport_class", "")
        if str(tc) != "FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1":
            raise FullCoreOrchestratedLifecycleReconciliationError(
                "PRODUCTIVE_TRANSPORT_CLASS_REQUIRED"
            )
        return run_full_core_post_submit_lifecycle_reconciliation_join_v1(
            post_submit_join=post_submit_join,
            binding=binding,
            decision_outcome=request.decision_outcome,
            venue_plan_identity=request.venue_plan_identity,
            envelope_identity=request.envelope_identity,
            submit_attempt_id=request.submit_attempt_id,
            local_durable_state_version=request.local_durable_state_version,
            read_only_get_transport=transport,
            pretrade_decision_id=request.pretrade_decision_id,
            query_options=request.query_options,
            state_dir=None,
            apply_durable_state=False,
            proven_never_submitted=request.proven_never_submitted,
            okx_read_only_forensic_profile="PRODUCTIVE_SCOPED",
        )

    raise FullCoreOrchestratedLifecycleReconciliationError("UNKNOWN_ORCHESTRATION_MODE")


def orchestration_mode_label_v1(
    mode: LifecycleReconciliationOrchestrationMode,
) -> Literal["OFFLINE", "INJECTED", "PRODUCTIVE_SCOPED"]:
    if mode is LifecycleReconciliationOrchestrationMode.OFFLINE_FIXTURE:
        return "OFFLINE"
    if mode is LifecycleReconciliationOrchestrationMode.INJECTED_OKX_TRANSPORT:
        return "INJECTED"
    return "PRODUCTIVE_SCOPED"


__all__ = [
    "ACCEPTED_PRIVATE_GET_GO",
    "CONTRACT_ID",
    "K1_SESSION_OWNER_GO",
    "LifecycleReconciliationOrchestrationMode",
    "ORCHESTRATION_OWNER",
    "PostSubmitLifecycleReconciliationOrchestrationRequestV1",
    "RECONCILIATION_READ_ONLY_GET_ALLOWLIST",
    "WORK_PACKAGE_ID",
    "assert_orchestration_owner_gos_v1",
    "orchestrate_post_submit_lifecycle_reconciliation_v1",
    "orchestration_mode_label_v1",
    "resolve_origin_main_sha_v1",
]
