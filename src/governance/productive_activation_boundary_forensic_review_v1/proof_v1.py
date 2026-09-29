"""Static proof for Productive Activation boundary forensic review (no activation mint)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from src.governance.current_productive_activation_policy_v1 import (
    RATIFIED_F1_M9_THRESHOLD_SECONDS,
    standing_productive_activation_authorized_v1,
    validate_productive_activation_policy_record_v1,
)
from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS,
)
from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_closure_v1 import (
    prove_governed_f1_m9_productive_runtime_threshold_consumer_wiring_v1,
)
from src.governance.productive_activation_boundary_forensic_review_v1.constants_v1 import (
    F1_M9_THRESHOLD_CONSUMER_RUNTIME_PRODUCERS,
    MASTER_RUNBOOK_PRODUCTIVE_BOUNDARY_SECTION,
    PRODUCTIVE_ACTIVATION_NAMED_BOUNDARY_DECISION_CONFIGS,
    SEMANTIC_COLLISION_SURFACES,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED as FULL_CORE_EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CONTINUOUS_RUN_AUTHORIZED as ORCHESTRATOR_CONTINUOUS_RUN_AUTHORIZED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
    FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY,
)
from src.ops.p5_10_productive_activation_and_binding_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED as P5_EXTERNAL_EFFECT_AUTHORIZED,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1.proof_v1 import (
    prove_pre_external_to_external_effect_boundary_v1,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]

_RUNBOOK_PRODUCTIVE_BOUNDARY_MARKERS = (
    "CURRENT_PRODUCTIVE_BOUNDARY=EXTERNAL_EFFECT_AND_BOUNDED_CONTINUOUS_RUN_FAIL_CLOSED",
    "CONTINUOUS_RUN_AUTHORIZED=false",
    "EXTERNAL_EFFECT_AUTHORIZED=false",
    "REAL_VENUE_POST_ALLOWED=false",
    "POST_ALLOWED=false",
)


@dataclass(frozen=True)
class ProductiveActivationBoundaryForensicProofResultV1:
    ok: bool
    guard_failures: Tuple[str, ...]
    decision_failures: Tuple[str, ...]
    runtime_path_failures: Tuple[str, ...]
    semantic_collision_failures: Tuple[str, ...]
    upstream_closure_failures: Tuple[str, ...]


def _read_rel(rel: str) -> str:
    return (_REPO_ROOT / rel).read_text(encoding="utf-8")


def prove_productive_activation_boundary_forensic_review_v1(
    *, repo_root: Path | None = None
) -> ProductiveActivationBoundaryForensicProofResultV1:
    """Fail-closed static census; does not activate, POST, or consume credentials."""
    root = repo_root or _REPO_ROOT
    guard_failures: list[str] = []

    policy = validate_productive_activation_policy_record_v1(repo_root=root)
    if policy.policy_authorized is not True:
        guard_failures.append("PRODUCTIVE_ACTIVATION_POLICY_NOT_AUTHORIZED")
    if standing_productive_activation_authorized_v1(repo_root=root) is not True:
        guard_failures.append("STANDING_PRODUCTIVE_ACTIVATION_NOT_AUTHORIZED")
    if int(RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS) != int(RATIFIED_F1_M9_THRESHOLD_SECONDS):
        guard_failures.append("F1_M9_THRESHOLD_SECONDS_DRIFT")
    if ORCHESTRATOR_CONTINUOUS_RUN_AUTHORIZED is not False:
        guard_failures.append("ORCHESTRATOR_CONTINUOUS_RUN_AUTHORIZED")
    if FULL_CORE_EXTERNAL_EFFECT_AUTHORIZED is not False:
        guard_failures.append("FULL_CORE_EXTERNAL_EFFECT_AUTHORIZED")
    if P5_EXTERNAL_EFFECT_AUTHORIZED is not False:
        guard_failures.append("P5_EXTERNAL_EFFECT_AUTHORIZED")
    if POST_ALLOWED is not False:
        guard_failures.append("FULL_CORE_POST_ALLOWED")
    if REAL_VENUE_POST_ALLOWED is not False:
        guard_failures.append("FULL_CORE_REAL_VENUE_POST_ALLOWED")
    if AUTONOMY_CAN_MINT_PERMIT is not False:
        guard_failures.append("AUTONOMY_CAN_MINT_PERMIT")
    if AUTONOMY_CAN_POST is not False:
        guard_failures.append("AUTONOMY_CAN_POST")
    if FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY != (
        "ONE_CYCLE_ORCHESTRATION_TO_PRE_EXTERNAL_EFFECT_ONLY"
    ):
        guard_failures.append("FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY")

    runbook = _read_rel(MASTER_RUNBOOK_PRODUCTIVE_BOUNDARY_SECTION)
    for marker in _RUNBOOK_PRODUCTIVE_BOUNDARY_MARKERS:
        if marker not in runbook:
            guard_failures.append(f"RUNBOOK_MISSING:{marker}")

    decision_failures: list[str] = []
    for rel in PRODUCTIVE_ACTIVATION_NAMED_BOUNDARY_DECISION_CONFIGS:
        payload = json.loads((root / rel).read_text(encoding="utf-8"))
        if payload.get("productive_activation_authorized") is not False:
            decision_failures.append(f"{rel}:productive_activation_authorized_not_false")
        # F1/M9 wiring decisions may retain historical boundary naming; policy owner supersedes.
        threshold = payload.get("ratified_threshold_numeric_max_age_seconds")
        if threshold is not None and int(threshold) != RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS:
            decision_failures.append(f"{rel}:threshold_drift")

    review_decision_path = root / (
        "config/governance/productive_activation_boundary_forensic_review_v1_decision_v1.json"
    )
    if review_decision_path.is_file():
        review = json.loads(review_decision_path.read_text(encoding="utf-8"))
        if review.get("productive_activation_authorized") is not False:
            decision_failures.append("FORENSIC_REVIEW_DECISION:productive_activation_authorized")
        if review.get("consumer_reachability_implies_productive_activation") is not False:
            decision_failures.append("FORENSIC_REVIEW_DECISION:consumer_reachability_implies")

    runtime_path_failures: list[str] = []
    for rel in F1_M9_THRESHOLD_CONSUMER_RUNTIME_PRODUCERS:
        text = _read_rel(rel)
        if "evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1" not in text:
            runtime_path_failures.append(f"{rel}:missing_consumer_path_eval")
        if "PRODUCTIVE_ACTIVATION_AUTHORIZED = True" in text:
            runtime_path_failures.append(f"{rel}:forbidden_activation_true_literal")

    semantic_collision_failures: list[str] = []
    p5_text = _read_rel(SEMANTIC_COLLISION_SURFACES[0])
    if PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is not True:
        semantic_collision_failures.append("P5_LAYERED_BIND_NOT_ENABLED")
    if P5_AUTHORITY_CUTOVER_AUTHORIZED is not False:
        semantic_collision_failures.append("P5_CUTOVER_NOT_FALSE")
    if "PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is True" not in p5_text:
        semantic_collision_failures.append("P5_CONSTANTS_MISSING_BIND_ASSERT")

    upstream_closure_failures: list[str] = []
    if not prove_governed_f1_m9_productive_runtime_threshold_consumer_wiring_v1(repo_root=root):
        upstream_closure_failures.append("F1_M9_CONSUMER_WIRING_CLOSURE")
    pre_external = prove_pre_external_to_external_effect_boundary_v1()
    if pre_external.ok is not True:
        upstream_closure_failures.append("PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY")

    ok = not (
        guard_failures
        or decision_failures
        or runtime_path_failures
        or semantic_collision_failures
        or upstream_closure_failures
    )
    return ProductiveActivationBoundaryForensicProofResultV1(
        ok=ok,
        guard_failures=tuple(guard_failures),
        decision_failures=tuple(decision_failures),
        runtime_path_failures=tuple(runtime_path_failures),
        semantic_collision_failures=tuple(semantic_collision_failures),
        upstream_closure_failures=tuple(upstream_closure_failures),
    )


__all__ = [
    "ProductiveActivationBoundaryForensicProofResultV1",
    "prove_productive_activation_boundary_forensic_review_v1",
]
