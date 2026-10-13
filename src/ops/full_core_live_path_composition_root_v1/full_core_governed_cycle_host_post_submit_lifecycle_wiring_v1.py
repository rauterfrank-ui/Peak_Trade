"""Governed Full-Core Cycle Host → post-submit lifecycle reconciliation wiring.

Explicit offline-only composition join. Default DISABLED — no import-time or
cycle-startup side effects. Productive exchange POST/GET remain forbidden unless
separate scoped Owner-GO surfaces authorize them.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import os
from contextvars import ContextVar
from contextvars import Token as _CtxReset
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    CurrentProductiveGovernedCycleResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
    full_core_atomic_mark_submit_boundary_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
    LifecycleReconciliationOrchestrationMode,
    PostSubmitLifecycleReconciliationOrchestrationRequestV1,
    orchestrate_post_submit_lifecycle_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    FullCorePostSubmitJoinResultV1,
    join_full_core_post_result_to_lifecycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    FullCorePostSubmitLifecycleReconciliationJoinResultV1,
    NETWORK_REQUEST_COUNT,
    POST_COUNT,
    PRIVATE_GET_COUNT,
    REAL_ORDER_COUNT,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
    FullCoreCapitalGuardHandoffContextV1,
    try_build_binding_from_governed_cycle_pre_external_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
    FullCoreCapitalGuardJoinMode,
    FullCorePrePostCapitalGuardJoinBindingV1,
    run_full_core_pre_post_capital_guard_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreTradeOrderPostResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
    CanaryCapitalGuardExposureEvidenceV1,
    CanaryCapitalGuardMarginEvidenceV1,
    IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
)

CONTRACT_ID = "FULL_CORE_GOVERNED_CYCLE_HOST_POST_SUBMIT_LIFECYCLE_WIRING_V1"
WORK_PACKAGE_ID = "GHV_CURRENT_FULL_CORE_GOVERNED_LIFECYCLE_WIRING_V1"
WIRING_ENV_VAR = "PEAK_TRADE_FULL_CORE_CYCLE_LIFECYCLE_WIRING_MODE"

CANONICAL_CYCLE_HOST_OWNER = (
    "ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1"
)
POST_SUBMIT_LIFECYCLE_ORCHESTRATION_OWNER = (
    "ops.full_core_live_path_composition_root_v1."
    "full_core_orchestrated_post_submit_lifecycle_reconciliation_v1"
)

ACCEPTED_GOVERNED_LIFECYCLE_WIRING_GO = "GRANTED"
ACCEPTED_OFFLINE_IMPLEMENTATION_GO = "GRANTED"
ACCEPTED_PRIVATE_GET_GO_OFFLINE = "GRANTED_SCOPED_READ_ONLY"
ACCEPTED_PRIVATE_GET_GO_DENIED = "NOT_GRANTED"


class FullCoreCycleLifecycleWiringError(RuntimeError):
    """Fail-closed cycle host ↔ lifecycle wiring violation."""


class CycleLifecycleWiringMode(str, Enum):
    DISABLED = "DISABLED"
    OFFLINE_INJECTED = "OFFLINE_INJECTED"


class CycleSubmitInjectionKind(str, Enum):
    """Deterministic offline submit boundary outcomes (injected transport only)."""

    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    REJECTED = "REJECTED"
    UNKNOWN_TIMEOUT = "UNKNOWN_TIMEOUT"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    TRANSPORT_API_FAILURE = "TRANSPORT_API_FAILURE"


@dataclass(frozen=True)
class FullCoreCycleLifecycleWiringOwnerGosV1:
    governed_lifecycle_wiring_go: str
    offline_implementation_go: str
    private_get_go: str

    def validate_v1(self) -> None:
        if (
            str(self.governed_lifecycle_wiring_go or "").strip()
            != ACCEPTED_GOVERNED_LIFECYCLE_WIRING_GO
        ):
            raise FullCoreCycleLifecycleWiringError("GOVERNED_LIFECYCLE_WIRING_GO_DENIED")
        if str(self.offline_implementation_go or "").strip() != ACCEPTED_OFFLINE_IMPLEMENTATION_GO:
            raise FullCoreCycleLifecycleWiringError("OFFLINE_IMPLEMENTATION_GO_DENIED")


@dataclass(frozen=True)
class FullCoreCycleLifecycleWiringRequestV1:
    """Explicit per-invocation wiring request. Never implied by cycle startup."""

    mode: CycleLifecycleWiringMode
    owner_gos: FullCoreCycleLifecycleWiringOwnerGosV1
    origin_main_sha: str
    submit_kind: CycleSubmitInjectionKind
    offline_fixture: OfflineExchangeFixtureV1 | None = None
    injected_post_result: FullCoreTradeOrderPostResultV1 | None = None
    read_only_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None
    pretrade_decision_id: str = "cycle-lifecycle-wiring-pretrade"
    submit_attempt_id: str = "cycle-lifecycle-wiring-submit"
    local_durable_state_version: str = "v1"
    atomic_state_dir: Path | None = None
    apply_durable_atomic_state: bool = False
    session_id: str = "full-core-cycle-lifecycle-wiring"


@dataclass(frozen=True)
class FullCoreCycleLifecycleWiringResultV1:
    wiring_mode: str
    capital_guard_join_mode: str
    guard_allowed: bool | None
    guard_blocked: bool
    submit_kind: str
    post_submit_join: FullCorePostSubmitJoinResultV1 | None
    lifecycle: FullCorePostSubmitLifecycleReconciliationJoinResultV1 | None
    ghv_forward_join: Literal["PASS", "FAIL", "SKIPPED"]
    ghv_reverse_join: Literal["PASS", "FAIL", "SKIPPED"]
    skip_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": CONTRACT_ID,
            "work_package_id": WORK_PACKAGE_ID,
            "wiring_mode": self.wiring_mode,
            "capital_guard_join_mode": self.capital_guard_join_mode,
            "guard_allowed": self.guard_allowed,
            "guard_blocked": self.guard_blocked,
            "submit_kind": self.submit_kind,
            "ghv_forward_join": self.ghv_forward_join,
            "ghv_reverse_join": self.ghv_reverse_join,
            "skip_reason": self.skip_reason,
            "post_count": POST_COUNT,
            "private_get_count": PRIVATE_GET_COUNT,
            "network_request_count": NETWORK_REQUEST_COUNT,
            "real_order_count": REAL_ORDER_COUNT,
        }


_wiring_invocation: ContextVar[FullCoreCycleLifecycleWiringRequestV1 | None] = ContextVar(
    "full_core_cycle_lifecycle_wiring_invocation_v1",
    default=None,
)
_wiring_margin: ContextVar[CanaryCapitalGuardMarginEvidenceV1 | None] = ContextVar(
    "full_core_cycle_lifecycle_wiring_margin_v1",
    default=None,
)
_wiring_exposure: ContextVar[CanaryCapitalGuardExposureEvidenceV1 | None] = ContextVar(
    "full_core_cycle_lifecycle_wiring_exposure_v1",
    default=None,
)


def bind_full_core_cycle_lifecycle_wiring_invocation_v1(
    *,
    request: FullCoreCycleLifecycleWiringRequestV1 | None,
    margin_evidence: CanaryCapitalGuardMarginEvidenceV1 | None = None,
    exposure_evidence: CanaryCapitalGuardExposureEvidenceV1 | None = None,
) -> tuple[_CtxReset, _CtxReset, _CtxReset]:
    return (
        _wiring_invocation.set(request),
        _wiring_margin.set(margin_evidence),
        _wiring_exposure.set(exposure_evidence),
    )


def reset_full_core_cycle_lifecycle_wiring_invocation_v1(
    tokens: tuple[_CtxReset, _CtxReset, _CtxReset],
) -> None:
    _wiring_invocation.reset(tokens[0])
    _wiring_margin.reset(tokens[1])
    _wiring_exposure.reset(tokens[2])


def resolve_cycle_lifecycle_wiring_mode_v1(
    *,
    explicit_mode: str | CycleLifecycleWiringMode | None = None,
) -> CycleLifecycleWiringMode:
    if isinstance(explicit_mode, CycleLifecycleWiringMode):
        return explicit_mode
    if explicit_mode is not None:
        try:
            return CycleLifecycleWiringMode(str(explicit_mode).strip().upper())
        except ValueError:
            return CycleLifecycleWiringMode.DISABLED
    raw = str(os.environ.get(WIRING_ENV_VAR) or CycleLifecycleWiringMode.DISABLED.value).strip()
    try:
        return CycleLifecycleWiringMode(raw.upper())
    except ValueError:
        return CycleLifecycleWiringMode.DISABLED


def _assert_standing_pins_v1() -> None:
    if (
        EXTERNAL_EFFECT_AUTHORIZED is True
        or POST_ALLOWED is True
        or REAL_VENUE_POST_ALLOWED is True
    ):
        raise FullCoreCycleLifecycleWiringError("STANDING_POST_PINS_MUST_REMAIN_FALSE")


def _authorization_binding_from_join_v1(
    binding: FullCorePrePostCapitalGuardJoinBindingV1,
    *,
    session_id: str,
) -> FullCoreAuthorizationBindingV1:
    return FullCoreAuthorizationBindingV1(
        owner_go=binding.owner_go,
        origin_main_sha=binding.origin_main_sha,
        account_scope=binding.account_identity,
        environment=binding.environment,
        execution_mode=binding.execution_mode,
        canonical_decision_id=binding.canonical_decision_id,
        instrument_id=binding.instrument_id,
        native_id=binding.native_id,
        selected_direction=binding.selected_direction,
        order_side=binding.order_side,
        final_quantity=binding.final_quantity,
        order_type=binding.order_type,
        order_price=binding.order_price,
        venue_plan_digest=binding.venue_plan_digest,
        envelope_digest=binding.envelope_digest,
        guard_config_digest=binding.guard_config_digest,
        session_id=session_id,
        clordid=binding.clordid,
    )


def _default_clean_margin_v1(**kw: object) -> CanaryCapitalGuardMarginEvidenceV1:
    base = dict(
        avail_eq_usdc="10000",
        imr_rate="0.05",
        imr_source_class=IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
        pretrade_decision_id="dec-cycle-lifecycle",
        expected_pretrade_decision_id="dec-cycle-lifecycle",
    )
    base.update(kw)
    return CanaryCapitalGuardMarginEvidenceV1(**base)  # type: ignore[arg-type]


def _default_clean_exposure_v1(**kw: object) -> CanaryCapitalGuardExposureEvidenceV1:
    base = dict(
        open_order_count=0,
        open_position_count=0,
        unknown_submit_active=False,
        recovery_state_clear=True,
        transport_retry_count=0,
    )
    base.update(kw)
    return CanaryCapitalGuardExposureEvidenceV1(**base)  # type: ignore[arg-type]


def _post_join_from_injection_v1(
    *,
    binding: FullCorePrePostCapitalGuardJoinBindingV1,
    submit_kind: CycleSubmitInjectionKind,
    injected: FullCoreTradeOrderPostResultV1 | None,
) -> FullCorePostSubmitJoinResultV1:
    cl = binding.clordid
    if submit_kind is CycleSubmitInjectionKind.NOT_ATTEMPTED:
        return join_full_core_post_result_to_lifecycle_v1(
            result=None,
            sent_clordid=cl,
            submit_count=0,
        )
    if submit_kind is CycleSubmitInjectionKind.UNKNOWN_TIMEOUT:
        return join_full_core_post_result_to_lifecycle_v1(
            result=None,
            sent_clordid=cl,
            submit_count=1,
            transport_error="socket.timeout",
        )
    if submit_kind is CycleSubmitInjectionKind.UNKNOWN_OUTCOME:
        return join_full_core_post_result_to_lifecycle_v1(
            result=None,
            sent_clordid=cl,
            submit_count=1,
            transport_error="UNKNOWN_OUTCOME",
        )
    if submit_kind is CycleSubmitInjectionKind.TRANSPORT_API_FAILURE:
        return join_full_core_post_result_to_lifecycle_v1(
            result=None,
            sent_clordid=cl,
            submit_count=1,
            transport_error="HTTP_502",
        )
    if submit_kind is CycleSubmitInjectionKind.REJECTED:
        rejected = injected
        if rejected is None:
            rejected = FullCoreTradeOrderPostResultV1(
                post_attempted=True,
                venue_live_contact=False,
                method="POST",
                http_status=200,
                payload={
                    "code": "0",
                    "data": [{"clOrdId": cl, "sCode": "51008", "sMsg": "reject"}],
                },
                unknown_outcome=False,
                transport_class="INJECTED_OFFLINE_WIRING",
                endpoint="/api/v5/trade/order",
            )
        return join_full_core_post_result_to_lifecycle_v1(
            result=rejected,
            sent_clordid=cl,
            submit_count=1,
        )
    if submit_kind is CycleSubmitInjectionKind.ACKNOWLEDGED:
        ack = injected
        if ack is None:
            raise FullCoreCycleLifecycleWiringError("INJECTED_ACK_POST_RESULT_REQUIRED")
        return join_full_core_post_result_to_lifecycle_v1(
            result=ack,
            sent_clordid=cl,
            submit_count=1,
        )
    raise FullCoreCycleLifecycleWiringError("UNKNOWN_SUBMIT_INJECTION_KIND")


def _orchestration_mode_for_request_v1(
    request: FullCoreCycleLifecycleWiringRequestV1,
) -> LifecycleReconciliationOrchestrationMode:
    if request.read_only_get_transport is not None:
        return LifecycleReconciliationOrchestrationMode.INJECTED_OKX_TRANSPORT
    if request.offline_fixture is not None:
        return LifecycleReconciliationOrchestrationMode.OFFLINE_FIXTURE
    raise FullCoreCycleLifecycleWiringError("OFFLINE_FIXTURE_OR_INJECTED_TRANSPORT_REQUIRED")


def run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
    *,
    cycle: CurrentProductiveGovernedCycleResultV1,
    handoff: FullCoreCapitalGuardHandoffContextV1,
    request: FullCoreCycleLifecycleWiringRequestV1,
    margin_evidence: CanaryCapitalGuardMarginEvidenceV1 | None = None,
    exposure_evidence: CanaryCapitalGuardExposureEvidenceV1 | None = None,
) -> FullCoreCycleLifecycleWiringResultV1:
    """Cycle Host composition join: PRE_EXTERNAL → capital guard → submit injection → lifecycle."""

    _assert_standing_pins_v1()
    request.owner_gos.validate_v1()
    mode = resolve_cycle_lifecycle_wiring_mode_v1(explicit_mode=request.mode)
    if mode is CycleLifecycleWiringMode.DISABLED:
        raise FullCoreCycleLifecycleWiringError("WIRING_MODE_DISABLED")

    if str(cycle.disposition or "") != DISPOSITION_PRE_EXTERNAL_EFFECT:
        raise FullCoreCycleLifecycleWiringError("CYCLE_NOT_AT_PRE_EXTERNAL")
    envelope = cycle.final_order_envelope
    if envelope is None or not isinstance(envelope, FinalOrderEnvelopeV1):
        raise FullCoreCycleLifecycleWiringError("FINAL_ORDER_ENVELOPE_MISSING")

    join_binding = try_build_binding_from_governed_cycle_pre_external_v1(
        cycle=cycle,
        bound_instrument=handoff.bound_instrument,
        canonical_decision_id=handoff.canonical_decision_id,
        account_identity=handoff.account_identity,
        environment=handoff.environment,
        origin_main_sha=handoff.origin_main_sha,
        instrument_metadata=handoff.instrument_metadata,
    )
    if join_binding is None:
        raise FullCoreCycleLifecycleWiringError("CAPITAL_GUARD_BINDING_BUILD_FAILED")

    margin = margin_evidence or _default_clean_margin_v1(
        pretrade_decision_id=join_binding.canonical_decision_id,
        expected_pretrade_decision_id=join_binding.canonical_decision_id,
    )
    guard_result = run_full_core_pre_post_capital_guard_join_v1(
        binding=join_binding,
        envelope=envelope,
        join_mode=FullCoreCapitalGuardJoinMode.OFFLINE_STUB,
        margin_evidence=margin,
        exposure_evidence=exposure_evidence or _default_clean_exposure_v1(),
        atomic_state_dir=request.atomic_state_dir,
        session_id=request.session_id,
    )
    if guard_result.guard_blocked or guard_result.guard_allowed is not True:
        return FullCoreCycleLifecycleWiringResultV1(
            wiring_mode=mode.value,
            capital_guard_join_mode=guard_result.join_mode,
            guard_allowed=guard_result.guard_allowed,
            guard_blocked=guard_result.guard_blocked,
            submit_kind=request.submit_kind.value,
            post_submit_join=None,
            lifecycle=None,
            ghv_forward_join="SKIPPED",
            ghv_reverse_join="SKIPPED",
            skip_reason="CAPITAL_GUARD_BLOCKED",
        )

    auth_binding = _authorization_binding_from_join_v1(
        join_binding,
        session_id=request.session_id,
    )
    if request.atomic_state_dir is not None and request.submit_kind not in {
        CycleSubmitInjectionKind.NOT_ATTEMPTED,
    }:
        full_core_atomic_mark_submit_boundary_v1(
            state_dir=request.atomic_state_dir,
            binding=auth_binding,
        )

    post_join = _post_join_from_injection_v1(
        binding=join_binding,
        submit_kind=request.submit_kind,
        injected=request.injected_post_result,
    )

    orch_mode = _orchestration_mode_for_request_v1(request)
    private_get = request.owner_gos.private_get_go
    if orch_mode is LifecycleReconciliationOrchestrationMode.OFFLINE_FIXTURE:
        if str(private_get or "").strip() not in {
            ACCEPTED_PRIVATE_GET_GO_OFFLINE,
            ACCEPTED_PRIVATE_GET_GO_DENIED,
        }:
            raise FullCoreCycleLifecycleWiringError("PRIVATE_GET_GO_INVALID_FOR_OFFLINE")
        private_get_for_orch = (
            ACCEPTED_PRIVATE_GET_GO_OFFLINE
            if str(private_get).strip() != ACCEPTED_PRIVATE_GET_GO_DENIED
            else ACCEPTED_PRIVATE_GET_GO_OFFLINE
        )
    else:
        if str(private_get or "").strip() != ACCEPTED_PRIVATE_GET_GO_OFFLINE:
            raise FullCoreCycleLifecycleWiringError("PRIVATE_GET_GO_REQUIRED_FOR_INJECTED_OKX")
        private_get_for_orch = ACCEPTED_PRIVATE_GET_GO_OFFLINE

    proven_never = request.submit_kind is CycleSubmitInjectionKind.NOT_ATTEMPTED
    orch_request = PostSubmitLifecycleReconciliationOrchestrationRequestV1(
        mode=orch_mode,
        work_package_owner_go=ACCEPTED_GOVERNED_LIFECYCLE_WIRING_GO,
        private_get_go=private_get_for_orch,
        offline_implementation_go=ACCEPTED_OFFLINE_IMPLEMENTATION_GO,
        origin_main_sha=request.origin_main_sha,
        decision_outcome=str(cycle.decision_result or "ENTER"),
        venue_plan_identity=join_binding.venue_plan_digest,
        envelope_identity=join_binding.envelope_digest,
        submit_attempt_id=request.submit_attempt_id,
        local_durable_state_version=request.local_durable_state_version,
        pretrade_decision_id=request.pretrade_decision_id,
        offline_fixture=request.offline_fixture,
        read_only_get_transport=request.read_only_get_transport,
        state_dir=request.atomic_state_dir,
        apply_durable_atomic_state=request.apply_durable_atomic_state,
        proven_never_submitted=proven_never,
    )
    lifecycle = orchestrate_post_submit_lifecycle_reconciliation_v1(
        post_submit_join=post_join,
        binding=auth_binding,
        request=orch_request,
    )
    return FullCoreCycleLifecycleWiringResultV1(
        wiring_mode=mode.value,
        capital_guard_join_mode=guard_result.join_mode,
        guard_allowed=guard_result.guard_allowed,
        guard_blocked=guard_result.guard_blocked,
        submit_kind=request.submit_kind.value,
        post_submit_join=post_join,
        lifecycle=lifecycle,
        ghv_forward_join=lifecycle.ghv_forward_join,
        ghv_reverse_join=lifecycle.ghv_reverse_join,
        skip_reason="",
    )


def _fail_closed_lifecycle_wiring_fields_for_exception_v1(exc: BaseException) -> dict[str, str]:
    """Record lifecycle wiring failure without implying post-submit reconciliation success."""

    message = str(exc).strip()
    if len(message) > 500:
        message = message[:497] + "..."
    fields: dict[str, str] = {
        "FULL_CORE_CYCLE_LIFECYCLE_WIRING": "FAIL_CLOSED",
        "FULL_CORE_CYCLE_LIFECYCLE_WIRING_UNEXPECTED": "true",
        "FULL_CORE_CYCLE_LIFECYCLE_WIRING_EXCEPTION_TYPE": type(exc).__name__,
    }
    if message:
        fields["FULL_CORE_CYCLE_LIFECYCLE_WIRING_EXCEPTION_MESSAGE"] = message
    return fields


def lifecycle_wiring_invocation_is_bound_v1() -> bool:
    return _wiring_invocation.get() is not None


def lifecycle_wiring_disabled_in_context_v1() -> bool:
    invocation = _wiring_invocation.get()
    if invocation is None:
        return False
    return resolve_cycle_lifecycle_wiring_mode_v1(explicit_mode=invocation.mode) is (
        CycleLifecycleWiringMode.DISABLED
    )


def maybe_record_full_core_governed_cycle_lifecycle_wiring_v1(
    *,
    cycle: CurrentProductiveGovernedCycleResultV1,
    handoff: FullCoreCapitalGuardHandoffContextV1 | None,
) -> dict[str, str]:
    """Optional cycle-host hook — runs only when wiring invocation context is bound."""

    invocation = _wiring_invocation.get()
    if invocation is None:
        return {}
    if resolve_cycle_lifecycle_wiring_mode_v1(explicit_mode=invocation.mode) is (
        CycleLifecycleWiringMode.DISABLED
    ):
        return {}
    if handoff is None:
        return {"FULL_CORE_CYCLE_LIFECYCLE_WIRING": "HANDOFF_MISSING"}
    try:
        result = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
            cycle=cycle,
            handoff=handoff,
            request=invocation,
            margin_evidence=_wiring_margin.get(),
            exposure_evidence=_wiring_exposure.get(),
        )
    except FullCoreCycleLifecycleWiringError as exc:
        return {
            "FULL_CORE_CYCLE_LIFECYCLE_WIRING": "FAIL_CLOSED",
            "FULL_CORE_CYCLE_LIFECYCLE_WIRING_REASON": str(exc),
        }
    except Exception as exc:
        return _fail_closed_lifecycle_wiring_fields_for_exception_v1(exc)
    fields = {
        "FULL_CORE_CYCLE_LIFECYCLE_WIRING": "INVOKED",
        "FULL_CORE_CYCLE_LIFECYCLE_WIRING_MODE": result.wiring_mode,
        "FULL_CORE_CYCLE_LIFECYCLE_GHV_FORWARD": result.ghv_forward_join,
        "FULL_CORE_CYCLE_LIFECYCLE_GHV_REVERSE": result.ghv_reverse_join,
    }
    if result.skip_reason:
        fields["FULL_CORE_CYCLE_LIFECYCLE_WIRING_SKIP"] = result.skip_reason
    if result.lifecycle is not None:
        fields["FULL_CORE_CYCLE_LIFECYCLE_RECON_OUTCOME"] = (
            result.lifecycle.reconciliation.decision.outcome
        )
    return fields


__all__ = [
    "ACCEPTED_GOVERNED_LIFECYCLE_WIRING_GO",
    "ACCEPTED_OFFLINE_IMPLEMENTATION_GO",
    "CANONICAL_CYCLE_HOST_OWNER",
    "CONTRACT_ID",
    "CycleLifecycleWiringMode",
    "CycleSubmitInjectionKind",
    "FullCoreCycleLifecycleWiringError",
    "FullCoreCycleLifecycleWiringOwnerGosV1",
    "FullCoreCycleLifecycleWiringRequestV1",
    "FullCoreCycleLifecycleWiringResultV1",
    "POST_SUBMIT_LIFECYCLE_ORCHESTRATION_OWNER",
    "WORK_PACKAGE_ID",
    "WIRING_ENV_VAR",
    "bind_full_core_cycle_lifecycle_wiring_invocation_v1",
    "lifecycle_wiring_disabled_in_context_v1",
    "lifecycle_wiring_invocation_is_bound_v1",
    "maybe_record_full_core_governed_cycle_lifecycle_wiring_v1",
    "reset_full_core_cycle_lifecycle_wiring_invocation_v1",
    "resolve_cycle_lifecycle_wiring_mode_v1",
    "run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1",
]
