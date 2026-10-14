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

FAKE_EXCHANGE_TRANSPORT_CLASS = "FAKE_EXCHANGE_OFFLINE_E2E_WITNESS_V1"
FAKE_POST_WITNESS_FILENAME = "fake_exchange_post_call_count_v1.json"


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
        IntegrationGapClassification.ALREADY_IMPLEMENTED_BUT_UNPROVEN
    ),
    "GAP_03_CAPITAL_GUARD_RESERVATION_ENVELOPE_PERMIT_IDENTITY": (
        IntegrationGapClassification.ALREADY_IMPLEMENTED_AND_PROVEN
    ),
    "GAP_04_POST_TO_RECONCILIATION_LIFECYCLE": (
        IntegrationGapClassification.ALREADY_IMPLEMENTED_AND_PROVEN
    ),
    "GAP_05_ATOMIC_DURABLE_CRASH_RECOVERY": (
        IntegrationGapClassification.ALREADY_IMPLEMENTED_BUT_UNPROVEN
    ),
    "GAP_06_DISABLED_LIFECYCLE_HOOKS_DEFAULT": IntegrationGapClassification.INTENTIONAL_SAFETY_BOUNDARY,
    "GAP_07_REPRODUCIBLE_FULL_SYSTEM_PROOF": IntegrationGapClassification.ALREADY_IMPLEMENTED_BUT_UNPROVEN,
    "GAP_LIVE_PRODUCTIVE_OKX_POST": IntegrationGapClassification.EXTERNAL_LIVE_VALIDATION_ONLY,
    "GAP_LIVE_PRODUCTIVE_OKX_GET_RECON": IntegrationGapClassification.EXTERNAL_LIVE_VALIDATION_ONLY,
}


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


@dataclass(frozen=True)
class FakeExchangeTransportWitnessV1:
    """Durable POST attempt counter for crash/restart proofs."""

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
                            "ordId": "ord-fake-e2e-1",
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
