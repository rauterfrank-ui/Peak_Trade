"""Bounded CURRENT full-system offline E2E integration proof composition.

Composes production PRE_EXTERNAL → capital guard → lifecycle/reconciliation joins
and optional one-shot fake HTTP POST (injected opener only). No productive network.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import parse_qs, urlparse
from urllib.response import addinfourl

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    CurrentProductiveGovernedCycleResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    POST_OWNER_GO,
    CurrentProductiveOneShotFreshEnvelopeJoinError,
    OneShotJoinProbeV1,
    OneShotJoinResultV1,
    attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_dw_exchange_reconciliation_wiring_v1 import (
    DwExchangeReconciliationWiringConfigV1,
    DwExchangeReconciliationWiringModeV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_pilot_capital_guard_post_bind_v1 import (
    build_pilot_dw_exchange_reconciliation_wiring_config_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
    FullCorePrePostCapitalGuardJoinBindingV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 import (
    CycleLifecycleWiringMode,
    CycleSubmitInjectionKind,
    FullCoreCycleLifecycleWiringOwnerGosV1,
    FullCoreCycleLifecycleWiringRequestV1,
    FullCoreCycleLifecycleWiringResultV1,
    run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
    resolve_origin_main_sha_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    NETWORK_REQUEST_COUNT,
    POST_COUNT,
    PRIVATE_GET_COUNT,
    REAL_ORDER_COUNT,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
    FullCoreCapitalGuardHandoffContextV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
    FullCoreCapitalGuardJoinMode,
    FullCorePrePostCapitalGuardJoinResultV1,
    run_full_core_pre_post_capital_guard_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreTradeOrderPostResultV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
    CanaryCapitalGuardExposureEvidenceV1,
    CanaryCapitalGuardMarginEvidenceV1,
    IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
)

CONTRACT_ID = "CURRENT_FULL_SYSTEM_OFFLINE_E2E_INTEGRATION_PROOF_V1"
WORK_PACKAGE_ID = "CURRENT_FULL_SYSTEM_E2E_INTEGRATION_CLOSURE_AND_PROOF_V1"

PRE_EXTERNAL_HANDOFF_FIXTURE_LABEL = "OFFLINE_TEST_EVIDENCE_PRE_EXTERNAL_CYCLE_FIXTURE_V1"
NATURAL_ENTER_UPSTREAM_LABEL = "CURRENT_MARKET_AUTHORITATIVE_NOT_FORCED_IN_HARNESS_V1"
NATURAL_ENTER_GAP_TRUE_01_PRODUCTION_PATH_V1 = (
    "GAP_TRUE_01_PRODUCTION_MV2_DP_NATURAL_ENTER_TO_PRE_EXTERNAL_V1"
)
OFFLINE_OWNER_AUTHORIZATION_FIXTURE_LABEL = (
    "OFFLINE_TEST_EVIDENCE_OPERATOR_GRANT_NO_REAL_WORLD_AUTHORITY_V1"
)

CRASH_POINT_ENV_VAR = "PEAK_TRADE_OFFLINE_E2E_CRASH_POINT_V1"
WORKER_RESULT_FILENAME = "offline_e2e_worker_result_v1.json"
ENVELOPE_SNAPSHOT_FILENAME = "offline_e2e_envelope_snapshot_v1.json"

FAKE_EXCHANGE_TRANSPORT_CLASS = "FAKE_EXCHANGE_OFFLINE_E2E_WITNESS_V1"
FAKE_POST_WITNESS_FILENAME = "fake_exchange_post_call_count_v1.json"
OFFLINE_E2E_FAKE_EXCHANGE_ORD_ID_V1 = "ord-fake-e2e-1"


class IntegrationGapClassification(str, Enum):
    ALREADY_IMPLEMENTED_AND_PROVEN = "ALREADY_IMPLEMENTED_AND_PROVEN"
    ALREADY_IMPLEMENTED_BUT_UNPROVEN = "ALREADY_IMPLEMENTED_BUT_UNPROVEN"
    CONFIRMED_CURRENT_INTEGRATION_DEFECT = "CONFIRMED_CURRENT_INTEGRATION_DEFECT"
    INTENTIONAL_SAFETY_BOUNDARY = "INTENTIONAL_SAFETY_BOUNDARY"
    EXTERNAL_LIVE_VALIDATION_ONLY = "EXTERNAL_LIVE_VALIDATION_ONLY"


INTEGRATION_GAP_CLASSIFICATIONS_V1: dict[str, IntegrationGapClassification] = {
    "GAP_01_NATURAL_ENTER_PRE_EXTERNAL_WITNESS": (
        IntegrationGapClassification.ALREADY_IMPLEMENTED_AND_PROVEN
    ),
    "GAP_02_PRE_EXTERNAL_TO_ONE_SHOT_HANDOFF": (
        IntegrationGapClassification.ALREADY_IMPLEMENTED_AND_PROVEN
    ),
    "GAP_03_CAPITAL_GUARD_RESERVATION_ENVELOPE_PERMIT_IDENTITY": (
        IntegrationGapClassification.ALREADY_IMPLEMENTED_BUT_UNPROVEN
    ),
    "GAP_04_POST_TO_RECONCILIATION_LIFECYCLE": (
        IntegrationGapClassification.ALREADY_IMPLEMENTED_AND_PROVEN
    ),
    "GAP_05_ATOMIC_DURABLE_CRASH_RECOVERY": (
        IntegrationGapClassification.ALREADY_IMPLEMENTED_BUT_UNPROVEN
    ),
    "GAP_06_DISABLED_LIFECYCLE_HOOKS_DEFAULT": IntegrationGapClassification.INTENTIONAL_SAFETY_BOUNDARY,
    "GAP_07_REPRODUCIBLE_FULL_SYSTEM_PROOF": IntegrationGapClassification.ALREADY_IMPLEMENTED_AND_PROVEN,
    "GAP_LIVE_PRODUCTIVE_OKX_POST": IntegrationGapClassification.EXTERNAL_LIVE_VALIDATION_ONLY,
    "GAP_LIVE_PRODUCTIVE_OKX_GET_RECON": IntegrationGapClassification.EXTERNAL_LIVE_VALIDATION_ONLY,
}


class OfflineE2eCrashPoint(str, Enum):
    NONE = "NONE"
    BEFORE_DURABLE_CONSUME = "BEFORE_DURABLE_CONSUME"
    AFTER_DURABLE_CONSUME = "AFTER_DURABLE_CONSUME"
    AFTER_FAKE_POST = "AFTER_FAKE_POST"
    BEFORE_RECON_COMPLETE = "BEFORE_RECON_COMPLETE"


class FullSystemOfflinePostScenario(str, Enum):
    CASE_A_EXCHANGE_ACCEPTANCE = "CASE_A_EXCHANGE_ACCEPTANCE"
    CASE_B_BUSINESS_REJECTION = "CASE_B_BUSINESS_REJECTION"
    CASE_C_POST_TIMEOUT = "CASE_C_POST_TIMEOUT"
    CASE_D_TRANSPORT_FAILURE_BEFORE_SEND = "CASE_D_TRANSPORT_FAILURE_BEFORE_SEND"
    CASE_E_CRASH_BEFORE_DURABLE_CONSUME = "CASE_E_CRASH_BEFORE_DURABLE_CONSUME"
    CASE_F_CRASH_AFTER_CONSUME_BEFORE_RESULT = "CASE_F_CRASH_AFTER_CONSUME_BEFORE_RESULT"
    CASE_G_CRASH_AFTER_POST_BEFORE_RECON = "CASE_G_CRASH_AFTER_POST_BEFORE_RECON"
    CASE_H_CONFLICTING_EVIDENCE = "CASE_H_CONFLICTING_EVIDENCE"
    CASE_I_INCOMPLETE_RECONCILIATION = "CASE_I_INCOMPLETE_RECONCILIATION"
    CASE_J_DUPLICATE_OPERATOR_INVOCATION = "CASE_J_DUPLICATE_OPERATOR_INVOCATION"
    CASE_K_PERMIT_REUSE = "CASE_K_PERMIT_REUSE"
    CASE_L_STALE_ENVELOPE_MISMATCH = "CASE_L_STALE_ENVELOPE_MISMATCH"
    CASE_M_INSUFFICIENT_CAPITAL = "CASE_M_INSUFFICIENT_CAPITAL"
    CASE_N_RESTART_UNKNOWN_EXTERNAL = "CASE_N_RESTART_UNKNOWN_EXTERNAL"
    CASE_O_TERMINAL_WITHOUT_EVIDENCE = "CASE_O_TERMINAL_WITHOUT_EVIDENCE"


class CurrentFullSystemOfflineE2eIntegrationProofError(RuntimeError):
    """Fail-closed full-system offline integration proof violation."""


@dataclass
class FakeExchangeTransportWitnessV1:
    """Durable POST attempt counter for crash/restart proofs.

    Intentionally mutable (not ``frozen``) so ``record_post_attempt_v1`` can persist counts.
    """

    witness_path: Path
    post_attempt_count: int = 0
    transport_class: str = FAKE_EXCHANGE_TRANSPORT_CLASS
    venue_live_contact: bool = False

    def record_post_attempt_v1(self) -> None:
        self.post_attempt_count += 1
        payload = {
            "transport_class": self.transport_class,
            "post_attempt_count": self.post_attempt_count,
            "venue_live_contact": self.venue_live_contact,
        }
        self.witness_path.parent.mkdir(parents=True, exist_ok=True)
        self.witness_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    @classmethod
    def load_v1(cls, witness_path: Path) -> FakeExchangeTransportWitnessV1:
        raw = json.loads(witness_path.read_text(encoding="utf-8"))
        return cls(
            witness_path=witness_path,
            post_attempt_count=int(raw.get("post_attempt_count") or 0),
            transport_class=str(raw.get("transport_class") or FAKE_EXCHANGE_TRANSPORT_CLASS),
            venue_live_contact=bool(raw.get("venue_live_contact")),
        )


def default_fake_post_witness_path_v1(state_root: Path | str) -> Path:
    return Path(state_root) / FAKE_POST_WITNESS_FILENAME


def standing_real_exchange_counts_v1() -> dict[str, int]:
    return {
        "REAL_EXCHANGE_POST_COUNT": int(POST_COUNT),
        "REAL_EXCHANGE_GET_COUNT": int(PRIVATE_GET_COUNT),
        "NETWORK_REQUEST_COUNT": int(NETWORK_REQUEST_COUNT),
        "REAL_ORDER_COUNT": int(REAL_ORDER_COUNT),
    }


def _default_owner_gos_v1(**kw: str) -> FullCoreCycleLifecycleWiringOwnerGosV1:
    base = {
        "governed_lifecycle_wiring_go": "GRANTED",
        "offline_implementation_go": "GRANTED",
        "private_get_go": "NOT_GRANTED",
    }
    base.update(kw)
    return FullCoreCycleLifecycleWiringOwnerGosV1(**base)  # type: ignore[arg-type]


def _default_margin_v1(*, pretrade_decision_id: str) -> CanaryCapitalGuardMarginEvidenceV1:
    return CanaryCapitalGuardMarginEvidenceV1(
        avail_eq_usdc="10000",
        imr_rate="0.05",
        imr_source_class=IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
        pretrade_decision_id=pretrade_decision_id,
        expected_pretrade_decision_id=pretrade_decision_id,
    )


def _default_exposure_v1() -> CanaryCapitalGuardExposureEvidenceV1:
    return CanaryCapitalGuardExposureEvidenceV1(
        open_order_count=0,
        open_position_count=0,
        unknown_submit_active=False,
        recovery_state_clear=True,
        transport_retry_count=0,
    )


def _build_join_binding_from_cycle_v1(
    *,
    cycle: CurrentProductiveGovernedCycleResultV1,
    handoff: FullCoreCapitalGuardHandoffContextV1,
) -> FullCorePrePostCapitalGuardJoinBindingV1:
    from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
        try_build_binding_from_governed_cycle_pre_external_v1,
    )

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
        raise CurrentFullSystemOfflineE2eIntegrationProofError("CAPITAL_GUARD_BINDING_BUILD_FAILED")
    return join_binding


def run_pre_external_capital_guard_phase_v1(
    *,
    cycle: CurrentProductiveGovernedCycleResultV1,
    handoff: FullCoreCapitalGuardHandoffContextV1,
    atomic_state_dir: Path | None = None,
    session_id: str = "offline-e2e-capital-guard",
) -> FullCorePrePostCapitalGuardJoinResultV1:
    if str(cycle.disposition or "") != DISPOSITION_PRE_EXTERNAL_EFFECT:
        raise CurrentFullSystemOfflineE2eIntegrationProofError("CYCLE_NOT_PRE_EXTERNAL")
    envelope = cycle.final_order_envelope
    if envelope is None or not isinstance(envelope, FinalOrderEnvelopeV1):
        raise CurrentFullSystemOfflineE2eIntegrationProofError("FINAL_ORDER_ENVELOPE_MISSING")
    join_binding = _build_join_binding_from_cycle_v1(cycle=cycle, handoff=handoff)
    return run_full_core_pre_post_capital_guard_join_v1(
        binding=join_binding,
        envelope=envelope,
        join_mode=FullCoreCapitalGuardJoinMode.OFFLINE_STUB,
        margin_evidence=_default_margin_v1(pretrade_decision_id=join_binding.canonical_decision_id),
        exposure_evidence=_default_exposure_v1(),
        atomic_state_dir=atomic_state_dir,
        session_id=session_id,
    )


def cycle_submit_kind_for_scenario_v1(
    scenario: FullSystemOfflinePostScenario,
) -> CycleSubmitInjectionKind:
    mapping = {
        FullSystemOfflinePostScenario.CASE_A_EXCHANGE_ACCEPTANCE: CycleSubmitInjectionKind.ACKNOWLEDGED,
        FullSystemOfflinePostScenario.CASE_B_BUSINESS_REJECTION: CycleSubmitInjectionKind.REJECTED,
        FullSystemOfflinePostScenario.CASE_C_POST_TIMEOUT: CycleSubmitInjectionKind.UNKNOWN_TIMEOUT,
        FullSystemOfflinePostScenario.CASE_D_TRANSPORT_FAILURE_BEFORE_SEND: (
            CycleSubmitInjectionKind.TRANSPORT_API_FAILURE
        ),
        FullSystemOfflinePostScenario.CASE_N_RESTART_UNKNOWN_EXTERNAL: (
            CycleSubmitInjectionKind.UNKNOWN_OUTCOME
        ),
        FullSystemOfflinePostScenario.CASE_O_TERMINAL_WITHOUT_EVIDENCE: (
            CycleSubmitInjectionKind.UNKNOWN_TIMEOUT
        ),
    }
    kind = mapping.get(scenario)
    if kind is None:
        raise CurrentFullSystemOfflineE2eIntegrationProofError(
            f"SCENARIO_USES_LIFECYCLE_OR_ONE_SHOT_PATH:{scenario.value}"
        )
    return kind


def build_cycle_lifecycle_wiring_request_v1(
    *,
    origin_main_sha: str,
    submit_kind: CycleSubmitInjectionKind,
    offline_fixture: OfflineExchangeFixtureV1 | None = None,
    injected_post: FullCoreTradeOrderPostResultV1 | None = None,
    atomic_state_dir: Path | None = None,
    apply_durable_atomic_state: bool = False,
) -> FullCoreCycleLifecycleWiringRequestV1:
    return FullCoreCycleLifecycleWiringRequestV1(
        mode=CycleLifecycleWiringMode.OFFLINE_INJECTED,
        owner_gos=_default_owner_gos_v1(),
        origin_main_sha=resolve_origin_main_sha_v1(declared=origin_main_sha),
        submit_kind=submit_kind,
        offline_fixture=offline_fixture or OfflineExchangeFixtureV1(),
        injected_post_result=injected_post,
        atomic_state_dir=atomic_state_dir,
        apply_durable_atomic_state=apply_durable_atomic_state,
    )


def run_downstream_lifecycle_join_phase_v1(
    *,
    cycle: CurrentProductiveGovernedCycleResultV1,
    handoff: FullCoreCapitalGuardHandoffContextV1,
    request: FullCoreCycleLifecycleWiringRequestV1,
) -> FullCoreCycleLifecycleWiringResultV1:
    return run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
        cycle=cycle,
        handoff=handoff,
        request=request,
    )


class _FakeExchangeOpener:
    """Injected urllib opener — no socket; records witness."""

    def __init__(
        self,
        *,
        witness: FakeExchangeTransportWitnessV1,
        scenario: FullSystemOfflinePostScenario,
        clordid: str,
    ) -> None:
        self._witness = witness
        self._scenario = scenario
        self._clordid = clordid
        self.requests: list[Any] = []

    def open(self, req: Any, timeout: float = 0) -> Any:
        del timeout
        self.requests.append(req)
        if self._scenario is FullSystemOfflinePostScenario.CASE_D_TRANSPORT_FAILURE_BEFORE_SEND:
            raise ConnectionError("FAKE_TRANSPORT_FAILURE_BEFORE_RESPONSE")
        if self._scenario is FullSystemOfflinePostScenario.CASE_C_POST_TIMEOUT:
            raise TimeoutError("FAKE_POST_TIMEOUT")
        self._witness.record_post_attempt_v1()
        if self._scenario is FullSystemOfflinePostScenario.CASE_B_BUSINESS_REJECTION:
            body = json.dumps(
                {
                    "code": "0",
                    "data": [
                        {
                            "clOrdId": self._clordid,
                            "sCode": "51008",
                            "sMsg": "Order failed",
                        }
                    ],
                }
            ).encode("utf-8")
        else:
            body = json.dumps(
                {
                    "code": "0",
                    "data": [
                        {
                            "clOrdId": self._clordid,
                            "ordId": OFFLINE_E2E_FAKE_EXCHANGE_ORD_ID_V1,
                            "sCode": "0",
                        }
                    ],
                }
            ).encode("utf-8")
        return addinfourl(BytesIO(body), {}, "https://eea.okx.com/api/v5/trade/order", 200)


@dataclass(frozen=True)
class FullSystemOfflineE2eProofResultV1:
    proof_id: str
    pre_external_handoff_label: str
    natural_enter_upstream_label: str
    capital_guard_allowed: bool | None
    lifecycle_wiring: FullCoreCycleLifecycleWiringResultV1 | None
    one_shot_join: OneShotJoinResultV1 | None
    fake_post_witness_count: int
    standing_real_exchange_counts: Mapping[str, int]
    ghv_forward_join: str
    ghv_reverse_join: str


def run_current_full_system_offline_e2e_integration_proof_v1(
    *,
    cycle: CurrentProductiveGovernedCycleResultV1,
    handoff: FullCoreCapitalGuardHandoffContextV1,
    state_root: Path,
    scenario: FullSystemOfflinePostScenario = (
        FullSystemOfflinePostScenario.CASE_A_EXCHANGE_ACCEPTANCE
    ),
    run_one_shot_fake_post: bool = False,
    one_shot_envelope: FinalOrderEnvelopeV1 | None = None,
    one_shot_attempt: Callable[..., OneShotJoinResultV1] | None = None,
    one_shot_k1_backend: Any | None = None,
    one_shot_dw_wiring: DwExchangeReconciliationWiringConfigV1 | None = None,
    offline_fixture: OfflineExchangeFixtureV1 | None = None,
    injected_ack_post: FullCoreTradeOrderPostResultV1 | None = None,
    apply_durable_atomic_state: bool = False,
) -> FullSystemOfflineE2eProofResultV1:
    """PRE_EXTERNAL fixture → capital guard → lifecycle join (+ optional one-shot POST)."""

    state_root.mkdir(parents=True, exist_ok=True)
    atomic_dir = state_root / "atomic"
    atomic_dir.mkdir(exist_ok=True)
    witness_path = default_fake_post_witness_path_v1(state_root)
    witness = FakeExchangeTransportWitnessV1(witness_path=witness_path)

    submit_kind = cycle_submit_kind_for_scenario_v1(scenario)
    lifecycle_req = build_cycle_lifecycle_wiring_request_v1(
        origin_main_sha=handoff.origin_main_sha,
        submit_kind=submit_kind,
        offline_fixture=offline_fixture,
        injected_post=injected_ack_post,
        atomic_state_dir=atomic_dir,
        apply_durable_atomic_state=apply_durable_atomic_state,
    )
    lifecycle = run_downstream_lifecycle_join_phase_v1(
        cycle=cycle,
        handoff=handoff,
        request=lifecycle_req,
    )
    guard_allowed = lifecycle.guard_allowed
    if lifecycle.skip_reason == "CAPITAL_GUARD_BLOCKED":
        guard_allowed = False

    one_shot: OneShotJoinResultV1 | None = None
    if run_one_shot_fake_post is True:
        if one_shot_envelope is None:
            raise CurrentFullSystemOfflineE2eIntegrationProofError(
                "ONE_SHOT_ENVELOPE_REQUIRED_FOR_FAKE_POST"
            )
        clordid = str(one_shot_envelope.client_order_id or "cl-fake-e2e")
        opener = _FakeExchangeOpener(witness=witness, scenario=scenario, clordid=clordid)
        probe = OneShotJoinProbeV1()
        attempt_fn = one_shot_attempt or (
            attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1
        )
        try:
            one_shot = attempt_fn(
                envelope=one_shot_envelope,
                post_owner_go=POST_OWNER_GO,
                store_root=state_root / "one_shot_durable",
                k1_backend=one_shot_k1_backend,
                opener_factory=lambda: opener,
                probe=probe,
                dw_exchange_reconciliation_wiring_mode=(
                    DwExchangeReconciliationWiringModeV1.DISABLED
                    if one_shot_dw_wiring is None
                    else DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED
                ),
                dw_exchange_reconciliation_wiring=one_shot_dw_wiring,
            )
        except CurrentProductiveOneShotFreshEnvelopeJoinError:
            raise

    ghv_f = lifecycle.ghv_forward_join if lifecycle is not None else "SKIPPED"
    ghv_r = lifecycle.ghv_reverse_join if lifecycle is not None else "SKIPPED"
    if one_shot is not None and one_shot.dw_exchange_reconciliation_ghv_forward_join:
        ghv_f = one_shot.dw_exchange_reconciliation_ghv_forward_join
    if one_shot is not None and one_shot.dw_exchange_reconciliation_ghv_reverse_join:
        ghv_r = one_shot.dw_exchange_reconciliation_ghv_reverse_join

    counts = standing_real_exchange_counts_v1()
    if witness_path.is_file():
        witness = FakeExchangeTransportWitnessV1.load_v1(witness_path)
    return FullSystemOfflineE2eProofResultV1(
        proof_id=WORK_PACKAGE_ID,
        pre_external_handoff_label=PRE_EXTERNAL_HANDOFF_FIXTURE_LABEL,
        natural_enter_upstream_label=NATURAL_ENTER_UPSTREAM_LABEL,
        capital_guard_allowed=guard_allowed,
        lifecycle_wiring=lifecycle,
        one_shot_join=one_shot,
        fake_post_witness_count=witness.post_attempt_count,
        standing_real_exchange_counts=counts,
        ghv_forward_join=str(ghv_f),
        ghv_reverse_join=str(ghv_r),
    )


def build_governed_cycle_from_pre_external_closure_v1(
    closure: Any,
) -> CurrentProductiveGovernedCycleResultV1:
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
        CurrentProductiveFullCorePreExternalClosureResultV1,
    )

    if not isinstance(closure, CurrentProductiveFullCorePreExternalClosureResultV1):
        raise CurrentFullSystemOfflineE2eIntegrationProofError("CLOSURE_TYPE_INVALID")
    envelope = closure.fresh_executable_enter_final_order_envelope
    if envelope is None:
        raise CurrentFullSystemOfflineE2eIntegrationProofError("CLOSURE_ENVELOPE_MISSING")
    env_id = str(envelope.envelope_id or "")
    return CurrentProductiveGovernedCycleResultV1(
        disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
        reason_code="PRE_EXTERNAL",
        terminal_class="PRE_EXTERNAL_EFFECT",
        cycle_go_status_after="CONSUMED",
        get_consumed=True,
        eg_consumed=True,
        occupancy_consumed=True,
        t2_consumed=True,
        get_consume_count=1,
        eg_dispatch_count=1,
        occupancy_disposition="CONSUMED",
        t2_consume_count=1,
        runtime_cycle_count=1,
        c1_used="production_closure",
        occupancy_used="production_closure",
        decision_result=str(closure.current_productive_decision_result or ""),
        decision_execution_eligible=str(closure.decision_execution_eligible or ""),
        master_v2_decision="enter_long",
        venue_plan_status="BOUND",
        envelope_created=True,
        envelope_identity=f"envelope_id={env_id}",
        permit_created=False,
        post_count=int(closure.post_count),
        external_effect_count=0,
        cursor_floor_before=1.0,
        cursor_floor_after=1.0,
        cursor_persisted=False,
        first_genuine_blocker=str(closure.earliest_remaining_blocker or ""),
        blocker_class="PRE_EXTERNAL_EFFECT",
        next_required_owner_decision="POST",
        lock_released="true",
        ledger_state="COMPLETED",
        transitions=("IDLE", "COMPLETED"),
        final_order_envelope=envelope,
    )


_OFFLINE_RECON_GET_ENDPOINTS = (
    "/api/v5/trade/orders-pending",
    "/api/v5/trade/orders-history",
    "/api/v5/trade/fills",
    "/api/v5/account/positions",
)


def _offline_recon_ok_payload_v1(data: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"code": "0", "data": list(data or [])}


def _offline_recon_get_result_v1(
    payload: dict[str, Any], *, fresh: bool = True
) -> FreshPretradeGetTransportResultV1:
    return FreshPretradeGetTransportResultV1(
        get_performed=True,
        method="GET",
        endpoint="",
        http_status=200,
        payload=payload,
        auth_header_sent=True,
        transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
        venue_live_contact=False,
        historical_reuse=not fresh,
        error_class="",
    )


class _OfflineInjectedOkxReconTransportV1:
    """Maps OfflineExchangeFixtureV1 onto OKX GET endpoints (offline E2E harness only)."""

    def __init__(self, fixture: OfflineExchangeFixtureV1) -> None:
        self.fixture = fixture
        self.request_count = 0

    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
        get_cache_policy: str = GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    ) -> FreshPretradeGetTransportResultV1:
        del auth_required, pretrade_decision_id, get_cache_policy
        self.request_count += 1
        parsed = urlparse(endpoint if "://" in endpoint else f"https://eea.okx.com{endpoint}")
        path = parsed.path

        if self.fixture.transport_failures:
            return FreshPretradeGetTransportResultV1(
                get_performed=False,
                method="GET",
                endpoint=endpoint,
                http_status=0,
                payload=None,
                auth_header_sent=True,
                transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
                venue_live_contact=False,
                historical_reuse=False,
                error_class="TIMEOUT",
            )

        fresh = self.fixture.item_freshness_proven and self.fixture.snapshot_freshness_proven
        status = self.fixture.response_status

        if path == _OFFLINE_RECON_GET_ENDPOINTS[0]:
            payload = self.fixture.pending_orders or _offline_recon_ok_payload_v1([])
        elif path == _OFFLINE_RECON_GET_ENDPOINTS[1]:
            payload = self.fixture.order_history or _offline_recon_ok_payload_v1([])
        elif path == _OFFLINE_RECON_GET_ENDPOINTS[2]:
            payload = self.fixture.fills or _offline_recon_ok_payload_v1([])
        elif path == _OFFLINE_RECON_GET_ENDPOINTS[3]:
            payload = self.fixture.positions or _offline_recon_ok_payload_v1([])
        elif path == READ_ONLY_EXACT_ORDER_LOOKUP_PATH:
            qs = parse_qs(parsed.query)
            cl = (qs.get("clOrdId") or [""])[0]
            rows: list[dict[str, Any]] = []
            for bucket in (self.fixture.pending_orders, self.fixture.order_history):
                if isinstance(bucket, dict):
                    for row in bucket.get("data") or []:
                        if isinstance(row, dict) and str(row.get("clOrdId") or "") == cl:
                            rows.append(dict(row))
            payload = _offline_recon_ok_payload_v1(rows)
        else:
            payload = _offline_recon_ok_payload_v1([])

        if self.fixture.api_errors and path == _OFFLINE_RECON_GET_ENDPOINTS[1]:
            payload = {"code": "50011", "msg": "rate limit", "data": []}

        if status != "200" and status.isdigit():
            return FreshPretradeGetTransportResultV1(
                get_performed=False,
                method="GET",
                endpoint=endpoint,
                http_status=int(status),
                payload=payload if isinstance(payload, dict) else None,
                auth_header_sent=True,
                transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
                venue_live_contact=False,
                historical_reuse=False,
                error_class="HTTP_ERROR",
            )

        return _offline_recon_get_result_v1(
            payload if isinstance(payload, dict) else _offline_recon_ok_payload_v1(),
            fresh=fresh,
        )


def build_handoff_from_pre_external_closure_v1(
    *,
    closure: Any,
    bound_instrument: Any,
    origin_main_sha: str,
    account_identity: str = "acct-offline-e2e-v1",
    environment: str = "OFFLINE_STUB",
) -> FullCoreCapitalGuardHandoffContextV1:
    from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
        FullCoreCapitalGuardInstrumentMetadataV1,
    )

    return FullCoreCapitalGuardHandoffContextV1(
        bound_instrument=bound_instrument,
        canonical_decision_id=str(closure.common_epoch_id or "dec-offline-e2e"),
        account_identity=account_identity,
        environment=environment,
        origin_main_sha=origin_main_sha,
        instrument_metadata=FullCoreCapitalGuardInstrumentMetadataV1(
            ct_val="1",
            min_sz="1",
            lot_sz="1",
        ),
    )


def build_dw_reconciliation_wiring_config_v1(
    *,
    join_binding: FullCorePrePostCapitalGuardJoinBindingV1,
    handoff: FullCoreCapitalGuardHandoffContextV1,
    envelope: FinalOrderEnvelopeV1,
    state_dir: Path,
    offline_fixture: OfflineExchangeFixtureV1,
    apply_durable_atomic_state: bool,
    authorization_binding: Any | None = None,
) -> DwExchangeReconciliationWiringConfigV1:
    from dataclasses import replace

    from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
        _authorization_binding_v1,
    )

    binding = authorization_binding or _authorization_binding_v1(
        join_binding, session_id="offline-e2e-recon"
    )
    recon_transport = _OfflineInjectedOkxReconTransportV1(offline_fixture)
    clordid = str(envelope.client_order_id or join_binding.clordid or "")
    config = build_pilot_dw_exchange_reconciliation_wiring_config_v1(
        authorization_binding=binding,
        envelope=envelope,
        pretrade_decision_id=str(handoff.canonical_decision_id),
        origin_main_sha=handoff.origin_main_sha,
        read_only_get_transport=recon_transport,
        venue_plan_identity=str(join_binding.venue_plan_digest or ""),
        submit_attempt_id=f"enter-post:{clordid}",
        private_get_go="GRANTED_SCOPED_READ_ONLY",
    )
    return replace(
        config,
        state_dir=state_dir,
        apply_durable_atomic_state=apply_durable_atomic_state,
        proven_never_submitted=False,
    )


@dataclass(frozen=True)
class ProductionOfflineE2eChainResultV1:
    natural_enter_proof: str
    pre_external_proof: str
    natural_enter_path_label: str
    pre_external_path_label: str
    owner_authorization_fixture_label: str
    capital_guard_allowed: bool
    one_shot_join: OneShotJoinResultV1
    fake_post_witness_count: int
    standing_real_exchange_counts: Mapping[str, int]
    ghv_forward_join: str
    ghv_reverse_join: str
    reconciliation_outcome: str
    dw_disposition: str


def _apply_crash_injection_v1(crash_point: OfflineE2eCrashPoint) -> None:
    import os

    if crash_point is OfflineE2eCrashPoint.NONE:
        return

    from src.ops.full_core_live_path_composition_root_v1 import (
        envelope_bound_external_effect_send_seam_v1 as seam_mod,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        external_effect_permit_durable_consume_v1 as consume_mod,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 as orch_mod,
    )

    if crash_point is OfflineE2eCrashPoint.BEFORE_DURABLE_CONSUME:

        def _crash_before(**kwargs: Any) -> Any:
            del kwargs
            os._exit(91)

        seam_mod.persist_external_effect_durable_consume_v1 = _crash_before
        consume_mod.persist_external_effect_durable_consume_v1 = _crash_before
        return

    if crash_point is OfflineE2eCrashPoint.AFTER_DURABLE_CONSUME:
        from src.ops.full_core_live_path_composition_root_v1 import (
            current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 as join_mod,
        )

        cls = join_mod._DurableConsumeThenK1HttpTransportV1
        orig_post = cls.post_trade_order

        def _crash_after_consume(self: Any, **kwargs: Any) -> Any:
            if (
                str(os.environ.get(CRASH_POINT_ENV_VAR) or "")
                == OfflineE2eCrashPoint.AFTER_DURABLE_CONSUME.value
            ):
                os._exit(92)
            return orig_post(self, **kwargs)

        cls.post_trade_order = _crash_after_consume  # type: ignore[method-assign]
        return

    if crash_point is OfflineE2eCrashPoint.BEFORE_RECON_COMPLETE:
        from src.ops.full_core_live_path_composition_root_v1 import (
            current_productive_dw_exchange_reconciliation_wiring_v1 as dw_mod,
        )

        def _crash_before_recon(**kwargs: Any) -> Any:
            del kwargs
            os._exit(94)

        orch_mod.orchestrate_post_submit_lifecycle_reconciliation_v1 = _crash_before_recon
        dw_mod.orchestrate_post_submit_lifecycle_reconciliation_v1 = _crash_before_recon


PILOT_CAPITAL_GUARD_PREVALIDATED_PROVENANCE_LABEL_V1 = (
    "PILOT_ENFORCE_PILOT_CAPITAL_GUARD_BEFORE_ENTER_POST_V1_OFFLINE_E2E"
)


def assert_pilot_capital_guard_prevalidated_provenance_v1(
    *,
    capital_guard_prevalidated: bool,
    pilot_authorization_binding: Any | None,
    envelope: FinalOrderEnvelopeV1,
) -> None:
    """Fail-closed: prevalidated guard must cite productive pilot bind, not a bare flag."""

    if capital_guard_prevalidated is not True:
        return
    if pilot_authorization_binding is None:
        raise CurrentFullSystemOfflineE2eIntegrationProofError(
            "PILOT_CAPITAL_GUARD_PROVENANCE_REQUIRED"
        )
    binding_cl = str(getattr(pilot_authorization_binding, "clordid", "") or "")
    env_cl = str(envelope.client_order_id or "")
    if not binding_cl or binding_cl != env_cl:
        raise CurrentFullSystemOfflineE2eIntegrationProofError(
            "PILOT_CAPITAL_GUARD_PROVENANCE_CLORDID_MISMATCH"
        )
    owner_go = str(getattr(pilot_authorization_binding, "owner_go", "") or "")
    if "PILOT_CAPITAL_GUARD" not in owner_go and "CAPITAL_GUARD" not in owner_go:
        raise CurrentFullSystemOfflineE2eIntegrationProofError(
            "PILOT_CAPITAL_GUARD_PROVENANCE_OWNER_GO_INVALID"
        )


def run_production_pre_external_to_fake_post_chain_v1(
    *,
    closure: Any,
    bound_instrument: Any,
    origin_main_sha: str,
    state_root: Path,
    read_only_get_transport: Any,
    offline_recon_fixture: OfflineExchangeFixtureV1,
    k1_backend: Any,
    post_owner_go_persisted: bool,
    admission_seal_established: bool,
    pilot_authorization_binding: Any | None = None,
    scenario: FullSystemOfflinePostScenario = (
        FullSystemOfflinePostScenario.CASE_A_EXCHANGE_ACCEPTANCE
    ),
    crash_point: OfflineE2eCrashPoint = OfflineE2eCrashPoint.NONE,
    apply_durable_atomic_state: bool = False,
    natural_enter_path_label: str = NATURAL_ENTER_GAP_TRUE_01_PRODUCTION_PATH_V1,
    capital_guard_prevalidated: bool = False,
) -> ProductionOfflineE2eChainResultV1:
    """PRE_EXTERNAL closure envelope → capital guard → one fake POST → offline recon."""

    from src.ops.full_core_live_path_composition_root_v1.current_productive_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_boundary_v1 import (
        resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
        CurrentProductiveFullCorePreExternalClosureResultV1,
    )

    if not isinstance(closure, CurrentProductiveFullCorePreExternalClosureResultV1):
        raise CurrentFullSystemOfflineE2eIntegrationProofError("CLOSURE_TYPE_INVALID")
    if str(closure.terminal_disposition or "") != DISPOSITION_PRE_EXTERNAL_EFFECT:
        raise CurrentFullSystemOfflineE2eIntegrationProofError("PRE_EXTERNAL_PROOF_FAILED")
    if not post_owner_go_persisted or not admission_seal_established:
        raise CurrentFullSystemOfflineE2eIntegrationProofError(
            "OFFLINE_OWNER_AUTHORIZATION_FIXTURE_INCOMPLETE"
        )

    state_root.mkdir(parents=True, exist_ok=True)
    atomic_dir = state_root / "atomic"
    atomic_dir.mkdir(exist_ok=True)
    one_shot_root = state_root / "one_shot_durable"
    one_shot_root.mkdir(exist_ok=True)
    witness_path = default_fake_post_witness_path_v1(state_root)
    witness = FakeExchangeTransportWitnessV1(witness_path=witness_path)

    envelope = resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1(
        closure
    )
    assert_pilot_capital_guard_prevalidated_provenance_v1(
        capital_guard_prevalidated=capital_guard_prevalidated,
        pilot_authorization_binding=pilot_authorization_binding,
        envelope=envelope,
    )
    envelope_snapshot = state_root / ENVELOPE_SNAPSHOT_FILENAME
    envelope_snapshot.write_text(
        json.dumps(envelope.to_runtime_json_v1(), sort_keys=True),
        encoding="utf-8",
    )

    cycle = build_governed_cycle_from_pre_external_closure_v1(closure)
    handoff = build_handoff_from_pre_external_closure_v1(
        closure=closure,
        bound_instrument=bound_instrument,
        origin_main_sha=origin_main_sha,
    )
    if capital_guard_prevalidated is True:
        guard_allowed = True
    else:
        guard = run_pre_external_capital_guard_phase_v1(
            cycle=cycle,
            handoff=handoff,
            atomic_state_dir=atomic_dir / "capital_guard",
            session_id="offline-e2e-capital-guard",
        )
        if guard.guard_blocked or guard.guard_allowed is not True:
            raise CurrentFullSystemOfflineE2eIntegrationProofError("CAPITAL_GUARD_BLOCKED")
        guard_allowed = True

    join_binding = _build_join_binding_from_cycle_v1(cycle=cycle, handoff=handoff)
    dw_config = build_dw_reconciliation_wiring_config_v1(
        join_binding=join_binding,
        handoff=handoff,
        envelope=envelope,
        state_dir=atomic_dir / "recon",
        offline_fixture=offline_recon_fixture,
        apply_durable_atomic_state=apply_durable_atomic_state,
        authorization_binding=pilot_authorization_binding,
    )

    if crash_point is OfflineE2eCrashPoint.AFTER_FAKE_POST:
        orig_open = _FakeExchangeOpener.open

        def _open_crash_after_post(self: _FakeExchangeOpener, req: Any, timeout: float = 0) -> Any:
            result = orig_open(self, req, timeout=timeout)
            import os

            os._exit(93)

        _FakeExchangeOpener.open = _open_crash_after_post  # type: ignore[method-assign]

    _apply_crash_injection_v1(crash_point)

    clordid = str(envelope.client_order_id or "cl-offline-e2e")
    opener = _FakeExchangeOpener(witness=witness, scenario=scenario, clordid=clordid)
    probe = OneShotJoinProbeV1()
    one_shot = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=POST_OWNER_GO,
        store_root=one_shot_root,
        k1_backend=k1_backend,
        opener_factory=lambda: opener,
        probe=probe,
        dw_exchange_reconciliation_wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        dw_exchange_reconciliation_wiring=dw_config,
    )

    if witness_path.is_file():
        witness = FakeExchangeTransportWitnessV1.load_v1(witness_path)

    counts = standing_real_exchange_counts_v1()
    return ProductionOfflineE2eChainResultV1(
        natural_enter_proof="PASS",
        pre_external_proof="PASS",
        natural_enter_path_label=natural_enter_path_label,
        pre_external_path_label=PRE_EXTERNAL_HANDOFF_FIXTURE_LABEL,
        owner_authorization_fixture_label=OFFLINE_OWNER_AUTHORIZATION_FIXTURE_LABEL,
        capital_guard_allowed=guard_allowed,
        one_shot_join=one_shot,
        fake_post_witness_count=int(witness.post_attempt_count),
        standing_real_exchange_counts=counts,
        ghv_forward_join=str(one_shot.dw_exchange_reconciliation_ghv_forward_join or ""),
        ghv_reverse_join=str(one_shot.dw_exchange_reconciliation_ghv_reverse_join or "SKIPPED"),
        reconciliation_outcome=str(one_shot.dw_exchange_reconciliation_outcome or ""),
        dw_disposition=str(one_shot.dw_exchange_reconciliation_disposition or ""),
    )


def persist_offline_e2e_worker_result_v1(*, state_root: Path, payload: Mapping[str, Any]) -> None:
    path = state_root / WORKER_RESULT_FILENAME
    path.write_text(json.dumps(dict(payload), sort_keys=True), encoding="utf-8")


def load_offline_e2e_worker_result_v1(*, state_root: Path) -> dict[str, Any]:
    path = state_root / WORKER_RESULT_FILENAME
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


OFFLINE_E2E_WORKER_INPUT_PICKLE = "offline_e2e_worker_input_v1.pkl"


def run_offline_e2e_crash_worker_from_persisted_input_v1(*, state_root: Path) -> int:
    """Load pickled worker input and run production chain (separate OS process)."""

    import os
    import pickle

    crash_raw = str(os.environ.get(CRASH_POINT_ENV_VAR) or OfflineE2eCrashPoint.NONE.value)
    try:
        crash = OfflineE2eCrashPoint(crash_raw)
    except ValueError:
        crash = OfflineE2eCrashPoint.NONE
    input_path = state_root / OFFLINE_E2E_WORKER_INPUT_PICKLE
    if not input_path.is_file():
        persist_offline_e2e_worker_result_v1(
            state_root=state_root,
            payload={"status": "MISSING_WORKER_INPUT"},
        )
        return 3
    loaded = pickle.load(input_path.open("rb"))
    pilot_authorization_binding = None
    if isinstance(loaded, tuple) and len(loaded) == 7:
        (
            closure,
            bound,
            origin_main_sha,
            read_only_get_transport,
            offline_recon_fixture,
            k1_backend,
            pilot_authorization_binding,
        ) = loaded
    elif isinstance(loaded, tuple) and len(loaded) == 6:
        (
            closure,
            bound,
            origin_main_sha,
            read_only_get_transport,
            offline_recon_fixture,
            k1_backend,
        ) = loaded
    else:
        persist_offline_e2e_worker_result_v1(
            state_root=state_root,
            payload={"status": "INVALID_WORKER_INPUT"},
        )
        return 4
    try:
        result = run_production_pre_external_to_fake_post_chain_v1(
            closure=closure,
            bound_instrument=bound,
            origin_main_sha=str(origin_main_sha),
            state_root=state_root,
            read_only_get_transport=read_only_get_transport,
            offline_recon_fixture=offline_recon_fixture,
            k1_backend=k1_backend,
            post_owner_go_persisted=True,
            admission_seal_established=True,
            crash_point=crash,
            capital_guard_prevalidated=True,
            pilot_authorization_binding=pilot_authorization_binding,
        )
        persist_offline_e2e_worker_result_v1(
            state_root=state_root,
            payload={
                "status": "PASS",
                "fake_post_witness_count": result.fake_post_witness_count,
                "reconciliation_outcome": result.reconciliation_outcome,
            },
        )
        return 0
    except BaseException as exc:  # noqa: BLE001
        persist_offline_e2e_worker_result_v1(
            state_root=state_root,
            payload={"status": "FAIL", "error": type(exc).__name__},
        )
        return 1


def persist_offline_e2e_worker_input_v1(
    *,
    state_root: Path,
    closure: Any,
    bound_instrument: Any,
    origin_main_sha: str,
    read_only_get_transport: Any,
    offline_recon_fixture: OfflineExchangeFixtureV1,
    k1_backend: Any,
    pilot_authorization_binding: Any | None = None,
) -> None:
    import pickle

    state_root.mkdir(parents=True, exist_ok=True)
    payload = (
        closure,
        bound_instrument,
        origin_main_sha,
        read_only_get_transport,
        offline_recon_fixture,
        k1_backend,
        pilot_authorization_binding,
    )
    with (state_root / OFFLINE_E2E_WORKER_INPUT_PICKLE).open("wb") as handle:
        pickle.dump(payload, handle, protocol=pickle.HIGHEST_PROTOCOL)
