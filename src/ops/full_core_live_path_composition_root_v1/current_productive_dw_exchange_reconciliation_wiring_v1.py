"""Optional DW post-submit exchange reconciliation wiring for one-shot join host.

Runs after envelope-bound send seam returns. Default DISABLED preserves prior
behavior. Reconciliation failures are fail-closed observability only; they do
not alter send outcome, durable consume, or POST authorization.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    POST_SUBMIT_RECON,
    UNKNOWN_OUTCOME_RECON,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
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
from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
    FullCoreOrchestratedLifecycleReconciliationError,
    LifecycleReconciliationOrchestrationMode,
    PostSubmitLifecycleReconciliationOrchestrationRequestV1,
    orchestrate_post_submit_lifecycle_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    FullCorePostSubmitJoinResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    FullCorePostSubmitLifecycleReconciliationJoinError,
)

CONTRACT_ID = "CURRENT_PRODUCTIVE_DW_EXCHANGE_RECONCILIATION_WIRING_V1"
WORK_PACKAGE_ID = "GHV_CURRENT_PHASE9_DW_EXCHANGE_RECONCILIATION_WIRING_V1"

DISPOSITION_SKIPPED = "SKIPPED"
DISPOSITION_PASS = "PASS"
DISPOSITION_FAIL_CLOSED = "FAIL_CLOSED"


class DwExchangeReconciliationWiringModeV1(str, Enum):
    DISABLED = "DISABLED"
    OFFLINE_INJECTED = "OFFLINE_INJECTED"
    PRODUCTIVE_READ_ONLY = "PRODUCTIVE_READ_ONLY"


@dataclass(frozen=True)
class DwExchangeReconciliationWiringConfigV1:
    binding: FullCoreAuthorizationBindingV1
    decision_outcome: str
    venue_plan_identity: str
    envelope_identity: str
    submit_attempt_id: str
    local_durable_state_version: str
    pretrade_decision_id: str
    origin_main_sha: str
    work_package_owner_go: str = "GRANTED"
    private_get_go: str = "GRANTED_SCOPED_READ_ONLY"
    offline_implementation_go: str = "GRANTED"
    read_only_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None
    offline_fixture: OfflineExchangeFixtureV1 | None = None
    query_options: OkxReadOnlyReconciliationQueryOptionsV1 | None = None
    state_dir: Path | None = None
    apply_durable_atomic_state: bool = False
    proven_never_submitted: bool = False


@dataclass(frozen=True)
class DwExchangeReconciliationWiringResultV1:
    wiring_mode: str
    invoked: bool
    disposition: str
    reconciliation_outcome: str
    ghv_forward_join: str
    ghv_reverse_join: str
    provider_mode: str
    error: str
    skip_reason: str


def _skipped(
    *,
    mode: DwExchangeReconciliationWiringModeV1,
    skip_reason: str,
) -> DwExchangeReconciliationWiringResultV1:
    return DwExchangeReconciliationWiringResultV1(
        wiring_mode=mode.value,
        invoked=False,
        disposition=DISPOSITION_SKIPPED,
        reconciliation_outcome="",
        ghv_forward_join="",
        ghv_reverse_join="",
        provider_mode="",
        error="",
        skip_reason=skip_reason,
    )


def _orchestration_mode_for_wiring_v1(
    mode: DwExchangeReconciliationWiringModeV1,
) -> LifecycleReconciliationOrchestrationMode:
    if mode is DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED:
        return LifecycleReconciliationOrchestrationMode.INJECTED_OKX_TRANSPORT
    if mode is DwExchangeReconciliationWiringModeV1.PRODUCTIVE_READ_ONLY:
        return LifecycleReconciliationOrchestrationMode.PRODUCTIVE_OKX_SCOPED_READ_ONLY
    raise FullCoreOrchestratedLifecycleReconciliationError("WIRING_MODE_NOT_ORCHESTRABLE")


def _build_orchestration_request_v1(
    *,
    wiring_mode: DwExchangeReconciliationWiringModeV1,
    config: DwExchangeReconciliationWiringConfigV1,
) -> PostSubmitLifecycleReconciliationOrchestrationRequestV1:
    orch_mode = _orchestration_mode_for_wiring_v1(wiring_mode)
    apply_durable = config.apply_durable_atomic_state
    state_dir = config.state_dir
    if wiring_mode is DwExchangeReconciliationWiringModeV1.PRODUCTIVE_READ_ONLY:
        apply_durable = False
        state_dir = None
    return PostSubmitLifecycleReconciliationOrchestrationRequestV1(
        mode=orch_mode,
        work_package_owner_go=config.work_package_owner_go,
        private_get_go=config.private_get_go,
        offline_implementation_go=config.offline_implementation_go,
        origin_main_sha=config.origin_main_sha,
        decision_outcome=config.decision_outcome,
        venue_plan_identity=config.venue_plan_identity,
        envelope_identity=config.envelope_identity,
        submit_attempt_id=config.submit_attempt_id,
        local_durable_state_version=config.local_durable_state_version,
        pretrade_decision_id=config.pretrade_decision_id,
        offline_fixture=config.offline_fixture,
        read_only_get_transport=config.read_only_get_transport,
        query_options=config.query_options,
        state_dir=state_dir,
        apply_durable_atomic_state=apply_durable,
        proven_never_submitted=config.proven_never_submitted,
    )


def _post_submit_join_admits_wiring_v1(join: FullCorePostSubmitJoinResultV1) -> bool:
    recon = str(join.recon_class or "")
    return recon in {POST_SUBMIT_RECON, UNKNOWN_OUTCOME_RECON}


def _coerce_wiring_mode_v1(
    wiring_mode: DwExchangeReconciliationWiringModeV1 | str,
) -> DwExchangeReconciliationWiringModeV1 | None:
    if isinstance(wiring_mode, DwExchangeReconciliationWiringModeV1):
        return wiring_mode
    raw = str(wiring_mode or "").strip()
    if raw.startswith("DwExchangeReconciliationWiringModeV1."):
        raw = raw.rsplit(".", 1)[-1]
    raw = raw.upper()
    try:
        return DwExchangeReconciliationWiringModeV1(raw)
    except ValueError:
        return None


def run_dw_exchange_reconciliation_wiring_after_post_submit_v1(
    *,
    wiring_mode: DwExchangeReconciliationWiringModeV1 | str = (
        DwExchangeReconciliationWiringModeV1.DISABLED
    ),
    wiring_config: DwExchangeReconciliationWiringConfigV1 | None,
    post_submit_join: FullCorePostSubmitJoinResultV1 | None,
) -> DwExchangeReconciliationWiringResultV1:
    """Invoke orchestrated lifecycle reconciliation when explicitly enabled."""

    mode = _coerce_wiring_mode_v1(wiring_mode)
    if mode is None:
        return DwExchangeReconciliationWiringResultV1(
            wiring_mode=str(wiring_mode or ""),
            invoked=False,
            disposition=DISPOSITION_FAIL_CLOSED,
            reconciliation_outcome="",
            ghv_forward_join="",
            ghv_reverse_join="",
            provider_mode="",
            error="UNKNOWN_WIRING_MODE",
            skip_reason="",
        )

    if mode is DwExchangeReconciliationWiringModeV1.DISABLED:
        return _skipped(mode=mode, skip_reason="WIRING_DISABLED")

    if post_submit_join is None:
        return _skipped(mode=mode, skip_reason="NO_POST_SUBMIT_JOIN")

    if not _post_submit_join_admits_wiring_v1(post_submit_join):
        return _skipped(mode=mode, skip_reason="RECON_CLASS_NOT_RECONCILABLE")

    if wiring_config is None:
        return DwExchangeReconciliationWiringResultV1(
            wiring_mode=mode.value,
            invoked=False,
            disposition=DISPOSITION_FAIL_CLOSED,
            reconciliation_outcome="",
            ghv_forward_join="",
            ghv_reverse_join="",
            provider_mode="",
            error="WIRING_CONFIG_REQUIRED",
            skip_reason="",
        )

    if mode is DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED:
        if wiring_config.read_only_get_transport is None:
            return DwExchangeReconciliationWiringResultV1(
                wiring_mode=mode.value,
                invoked=False,
                disposition=DISPOSITION_FAIL_CLOSED,
                reconciliation_outcome="",
                ghv_forward_join="",
                ghv_reverse_join="",
                provider_mode="",
                error="INJECTED_TRANSPORT_REQUIRED",
                skip_reason="",
            )
    if mode is DwExchangeReconciliationWiringModeV1.PRODUCTIVE_READ_ONLY:
        if wiring_config.read_only_get_transport is None:
            return DwExchangeReconciliationWiringResultV1(
                wiring_mode=mode.value,
                invoked=False,
                disposition=DISPOSITION_FAIL_CLOSED,
                reconciliation_outcome="",
                ghv_forward_join="",
                ghv_reverse_join="",
                provider_mode="",
                error="PRODUCTIVE_TRANSPORT_REQUIRED",
                skip_reason="",
            )

    request = _build_orchestration_request_v1(wiring_mode=mode, config=wiring_config)
    try:
        joined = orchestrate_post_submit_lifecycle_reconciliation_v1(
            post_submit_join=post_submit_join,
            binding=wiring_config.binding,
            request=request,
        )
    except (
        FullCoreOrchestratedLifecycleReconciliationError,
        FullCorePostSubmitLifecycleReconciliationJoinError,
    ) as exc:
        return DwExchangeReconciliationWiringResultV1(
            wiring_mode=mode.value,
            invoked=True,
            disposition=DISPOSITION_FAIL_CLOSED,
            reconciliation_outcome="",
            ghv_forward_join="",
            ghv_reverse_join="",
            provider_mode="",
            error=str(exc),
            skip_reason="",
        )

    return DwExchangeReconciliationWiringResultV1(
        wiring_mode=mode.value,
        invoked=True,
        disposition=DISPOSITION_PASS,
        reconciliation_outcome=str(joined.reconciliation.decision.outcome),
        ghv_forward_join=str(joined.ghv_forward_join),
        ghv_reverse_join=str(joined.ghv_reverse_join),
        provider_mode=str(joined.provider_mode),
        error="",
        skip_reason="",
    )


__all__ = [
    "CONTRACT_ID",
    "DISPOSITION_FAIL_CLOSED",
    "DISPOSITION_PASS",
    "DISPOSITION_SKIPPED",
    "DwExchangeReconciliationWiringConfigV1",
    "DwExchangeReconciliationWiringModeV1",
    "DwExchangeReconciliationWiringResultV1",
    "WORK_PACKAGE_ID",
    "run_dw_exchange_reconciliation_wiring_after_post_submit_v1",
]
