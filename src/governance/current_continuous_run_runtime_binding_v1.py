"""Runtime binding: Continuous Run policy → S6 orchestrator with per-cycle revalidation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Final, Mapping

from src.governance.current_continuous_run_policy_v1 import (
    BOUNDED_ORCHESTRATION_TERMINAL,
    STATUS_ADMISSION_DENIED,
    TARGET_ORCHESTRATOR_SURFACE,
    evaluate_continuous_runtime_admission_v1,
    standing_continuous_run_authorized_v1,
    validate_continuous_run_policy_record_v1,
)
from src.governance.current_productive_activation_policy_v1 import (
    RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
)
from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    F1M9ProductiveRuntimeThresholdConsumerPathResultV1,
    STATUS_WIRED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CurrentProductiveGovernedContinuousCycleOrchestratorError,
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    CurrentProductiveGovernedContinuousCycleRunResultV1,
    ContinuousObservationSourceV1,
    run_current_productive_governed_continuous_cycle_run_v1,
)

BINDING_OWNER: Final[str] = "governance.current_continuous_run_runtime_binding_v1"
DEFAULT_RUNTIME_SURFACE: Final[str] = RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE

F1M9CycleEvaluatorV1 = Callable[
    [int],
    F1M9ProductiveRuntimeThresholdConsumerPathResultV1,
]


class ContinuousRunRuntimeBindingError(ValueError):
    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


@dataclass(frozen=True, slots=True)
class ContinuousRunIterationEvidenceV1:
    cycle_index: int
    continuous_admission_granted: bool
    productive_activation_authorized: bool
    f1_m9_wiring_status: str | None
    f1_m9_threshold_seconds: float | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PolicyGovernedContinuousRunResultV1:
    orchestrator_result: CurrentProductiveGovernedContinuousCycleRunResultV1
    iteration_evidence: tuple[ContinuousRunIterationEvidenceV1, ...]
    continuous_run_policy_digest: str | None
    productive_activation_policy_digest: str | None
    bounded_orchestration_terminal: str
    external_effect_authorized: bool
    post_allowed: bool
    wire_send_permitted: bool
    autonomy_can_mint_permit: bool
    autonomy_can_post: bool
    extra: dict[str, str] = field(default_factory=dict)


def _require_admission(
    *,
    cycle_index: int,
    runtime_surface: str,
    repo_root: Path,
    evidence: list[ContinuousRunIterationEvidenceV1],
    f1_m9_evaluator: F1M9CycleEvaluatorV1 | None,
) -> None:
    admission = evaluate_continuous_runtime_admission_v1(
        runtime_surface=runtime_surface,
        repo_root=repo_root,
        orchestrator_target=TARGET_ORCHESTRATOR_SURFACE,
    )
    f1_status: str | None = None
    f1_threshold: float | None = None
    iter_reasons = list(admission.reason_codes)
    if f1_m9_evaluator is not None:
        f1_result = f1_m9_evaluator(cycle_index)
        f1_status = f1_result.wiring_status
        f1_threshold = f1_result.threshold_numeric_max_age_seconds
        if f1_result.wiring_status != STATUS_WIRED:
            iter_reasons.extend(list(f1_result.reason_codes) or ["F1_M9_CYCLE_DENIED"])
        if f1_result.external_effect_authorized is True:
            iter_reasons.append("F1_M9_EXTERNAL_EFFECT_LEAK")
    evidence.append(
        ContinuousRunIterationEvidenceV1(
            cycle_index=cycle_index,
            continuous_admission_granted=admission.continuous_runtime_admission_granted,
            productive_activation_authorized=admission.productive_activation_authorized,
            f1_m9_wiring_status=f1_status,
            f1_m9_threshold_seconds=f1_threshold,
            reason_codes=tuple(dict.fromkeys(iter_reasons)),
        )
    )
    if not admission.continuous_runtime_admission_granted:
        raise ContinuousRunRuntimeBindingError(
            "CONTINUOUS_RUNTIME_ADMISSION_DENIED",
            ",".join(admission.reason_codes) or STATUS_ADMISSION_DENIED,
        )
    if f1_m9_evaluator is not None and f1_status != STATUS_WIRED:
        raise ContinuousRunRuntimeBindingError(
            "F1_M9_BOUNDED_CYCLE_DENIED",
            ",".join(iter_reasons),
        )


def run_policy_governed_current_productive_continuous_cycle_run_v1(
    *,
    authorization: CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    origin_main_sha: str,
    cursor_store_root: Path,
    lock_root: Path,
    evidence_root: Path,
    observation_source: ContinuousObservationSourceV1 | None,
    repo_root: Path | None = None,
    runtime_surface: str = DEFAULT_RUNTIME_SURFACE,
    f1_m9_cycle_evaluator: F1M9CycleEvaluatorV1 | None = None,
    require_f1_m9_each_cycle: bool = True,
    **orchestrator_kwargs: Any,
) -> PolicyGovernedContinuousRunResultV1:
    """Policy-governed continuous run; module pin CONTINUOUS_RUN_AUTHORIZED stays false."""
    root = repo_root or Path(__file__).resolve().parents[2]
    if not standing_continuous_run_authorized_v1(repo_root=root):
        policy = validate_continuous_run_policy_record_v1(repo_root=root)
        raise ContinuousRunRuntimeBindingError(
            "CONTINUOUS_RUN_POLICY_DENIED",
            ",".join(policy.reason_codes) or "POLICY_INVALID",
        )

    iteration_evidence: list[ContinuousRunIterationEvidenceV1] = []
    evaluator = f1_m9_cycle_evaluator
    if require_f1_m9_each_cycle and evaluator is None:
        raise ContinuousRunRuntimeBindingError("F1_M9_CYCLE_EVALUATOR_REQUIRED")

    def iteration_gate(cycle_index: int) -> None:
        _require_admission(
            cycle_index=cycle_index,
            runtime_surface=runtime_surface,
            repo_root=root,
            evidence=iteration_evidence,
            f1_m9_evaluator=evaluator,
        )

    _require_admission(
        cycle_index=0,
        runtime_surface=runtime_surface,
        repo_root=root,
        evidence=iteration_evidence,
        f1_m9_evaluator=evaluator,
    )

    try:
        orchestrator_result = run_current_productive_governed_continuous_cycle_run_v1(
            authorization=authorization,
            origin_main_sha=origin_main_sha,
            cursor_store_root=cursor_store_root,
            lock_root=lock_root,
            evidence_root=evidence_root,
            observation_source=observation_source,
            iteration_authority_gate_v1=iteration_gate,
            **orchestrator_kwargs,
        )
    except CurrentProductiveGovernedContinuousCycleOrchestratorError as exc:
        raise ContinuousRunRuntimeBindingError(exc.reason_code, exc.detail) from exc

    policy = validate_continuous_run_policy_record_v1(repo_root=root)
    admission = evaluate_continuous_runtime_admission_v1(
        runtime_surface=runtime_surface,
        repo_root=root,
    )
    payload_path = Path(evidence_root) / "continuous_run_policy_evidence_v1.json"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(
        json.dumps(
            {
                "continuous_run_policy_digest": policy.policy_record_digest,
                "productive_activation_policy_digest": policy.productive_activation_policy_digest,
                "iteration_evidence": [
                    {
                        "cycle_index": item.cycle_index,
                        "continuous_admission_granted": item.continuous_admission_granted,
                        "productive_activation_authorized": item.productive_activation_authorized,
                        "f1_m9_wiring_status": item.f1_m9_wiring_status,
                        "f1_m9_threshold_seconds": item.f1_m9_threshold_seconds,
                        "reason_codes": list(item.reason_codes),
                    }
                    for item in iteration_evidence
                ],
                "orchestrator_disposition": orchestrator_result.disposition,
                "cycles_completed": orchestrator_result.cycles_completed,
            },
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return PolicyGovernedContinuousRunResultV1(
        orchestrator_result=orchestrator_result,
        iteration_evidence=tuple(iteration_evidence),
        continuous_run_policy_digest=policy.policy_record_digest,
        productive_activation_policy_digest=policy.productive_activation_policy_digest,
        bounded_orchestration_terminal=BOUNDED_ORCHESTRATION_TERMINAL,
        external_effect_authorized=admission.external_effect_authorized,
        post_allowed=admission.post_allowed,
        wire_send_permitted=admission.wire_send_permitted,
        autonomy_can_mint_permit=admission.autonomy_can_mint_permit,
        autonomy_can_post=admission.autonomy_can_post,
        extra={"BINDING_OWNER": BINDING_OWNER},
    )


__all__ = [
    "BINDING_OWNER",
    "ContinuousRunIterationEvidenceV1",
    "ContinuousRunRuntimeBindingError",
    "F1M9CycleEvaluatorV1",
    "PolicyGovernedContinuousRunResultV1",
    "run_policy_governed_current_productive_continuous_cycle_run_v1",
]
