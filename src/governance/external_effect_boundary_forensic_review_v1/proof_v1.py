"""Static and simulated proof for External Effect boundary forensic review v1."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from src.governance.current_continuous_run_policy_v1 import (
    standing_continuous_run_authorized_v1,
    validate_continuous_run_policy_record_v1,
)
from src.governance.current_productive_activation_policy_v1 import (
    standing_productive_activation_authorized_v1,
    validate_productive_activation_policy_record_v1,
)
from src.governance.external_effect_boundary_forensic_review_v1.constants_v1 import (
    BOUNDARY_CHAIN_SURFACES,
    DECISION_CONFIG,
    GOVERNED_UPSTREAM_POLICY_SURFACES,
    MASTER_RUNBOOK_PRODUCTIVE_BOUNDARY_SECTION,
    OWNER_WP_DECISION_CONFIG,
    VENUE_POST_SINK_OWNER,
)
from src.governance.governed_current_continuous_run_policy_closure_v1 import (
    prove_governed_current_continuous_run_policy_v1,
)
from src.governance.governed_current_productive_activation_policy_closure_v1 import (
    prove_governed_current_productive_activation_policy_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_AUTHORIZED_DOES_NOT_IMPLY_EXTERNAL_EFFECT,
    POST_ALLOWED,
    PRODUCTIVE_WIRE_SEND_REACHABLE_DOES_NOT_IMPLY_EXTERNAL_EFFECT,
    REAL_VENUE_POST_ALLOWED,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CONTINUOUS_RUN_AUTHORIZED as ORCHESTRATOR_CONTINUOUS_RUN_MODULE_PIN,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    FullCoreExternalEffectNotAuthorizedError,
    evaluate_external_effect_v1,
    refuse_external_effect_v1,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1.proof_v1 import (
    prove_pre_external_to_external_effect_boundary_v1,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]

_RUNBOOK_BOUNDARY_MARKERS = (
    "EXTERNAL_EFFECT_AUTHORIZED=false",
    "POST_ALLOWED=false",
    "CURRENT_PRODUCTIVE_BOUNDARY=EXTERNAL_EFFECT_AND_BOUNDED_CONTINUOUS_RUN_FAIL_CLOSED",
)


@dataclass(frozen=True)
class ExternalEffectBoundaryForensicProofResultV1:
    ok: bool
    guard_failures: Tuple[str, ...]
    decision_failures: Tuple[str, ...]
    chain_failures: Tuple[str, ...]
    simulated_failures: Tuple[str, ...]
    upstream_closure_failures: Tuple[str, ...]


def _read_rel(rel: str) -> str:
    return (_REPO_ROOT / rel).read_text(encoding="utf-8")


def prove_external_effect_boundary_forensic_review_v1(
    *, repo_root: Path | None = None
) -> ExternalEffectBoundaryForensicProofResultV1:
    """Fail-closed census + simulated gate checks; no POST, credentials, or venue mutation."""
    root = repo_root or _REPO_ROOT
    guard_failures: list[str] = []

    if not standing_productive_activation_authorized_v1(repo_root=root):
        guard_failures.append("PRODUCTIVE_ACTIVATION_POLICY_NOT_AUTHORIZED")
    if not standing_continuous_run_authorized_v1(repo_root=root):
        guard_failures.append("CONTINUOUS_RUN_POLICY_NOT_AUTHORIZED")
    if ORCHESTRATOR_CONTINUOUS_RUN_MODULE_PIN is not False:
        guard_failures.append("ORCHESTRATOR_CONTINUOUS_RUN_MODULE_PIN_DRIFT")
    if EXTERNAL_EFFECT_AUTHORIZED is not False:
        guard_failures.append("EXTERNAL_EFFECT_AUTHORIZED")
    if POST_ALLOWED is not False:
        guard_failures.append("POST_ALLOWED")
    if REAL_VENUE_POST_ALLOWED is not False:
        guard_failures.append("REAL_VENUE_POST_ALLOWED")
    if LIVE_AUTHORIZED_DOES_NOT_IMPLY_EXTERNAL_EFFECT is not True:
        guard_failures.append("LIVE_AUTHORIZED_DOES_NOT_IMPLY_EXTERNAL_EFFECT")
    if PRODUCTIVE_WIRE_SEND_REACHABLE_DOES_NOT_IMPLY_EXTERNAL_EFFECT is not True:
        guard_failures.append("PRODUCTIVE_WIRE_SEND_REACHABLE_DOES_NOT_IMPLY_EXTERNAL_EFFECT")
    if SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST is not True:
        guard_failures.append("SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST")
    if AUTONOMY_CAN_MINT_PERMIT is not False:
        guard_failures.append("AUTONOMY_CAN_MINT_PERMIT")
    if AUTONOMY_CAN_POST is not False:
        guard_failures.append("AUTONOMY_CAN_POST")

    activation = validate_productive_activation_policy_record_v1(repo_root=root)
    if activation.policy_authorized is not True:
        guard_failures.append("PRODUCTIVE_ACTIVATION_POLICY_RECORD_INVALID")
    continuous = validate_continuous_run_policy_record_v1(repo_root=root)
    if continuous.policy_authorized is not True:
        guard_failures.append("CONTINUOUS_RUN_POLICY_RECORD_INVALID")

    runbook = _read_rel(MASTER_RUNBOOK_PRODUCTIVE_BOUNDARY_SECTION)
    for marker in _RUNBOOK_BOUNDARY_MARKERS:
        if marker not in runbook:
            guard_failures.append(f"RUNBOOK_MISSING:{marker}")

    decision_failures: list[str] = []
    for rel in (DECISION_CONFIG, OWNER_WP_DECISION_CONFIG):
        path = root / rel
        if not path.is_file():
            decision_failures.append(f"MISSING:{rel}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("external_effect_authorized") is not False:
            decision_failures.append(f"{rel}:external_effect_authorized_not_false")
        if rel == DECISION_CONFIG:
            if payload.get("forensic_review_complete") is not True:
                decision_failures.append(f"{rel}:forensic_review_complete")
            if payload.get("pre_external_reachability_implies_external_effect") is not False:
                decision_failures.append(f"{rel}:pre_external_implies_external_effect")
            if payload.get("earliest_unclosed_boundary") != "EXTERNAL_EFFECT_AUTHORIZATION":
                decision_failures.append(f"{rel}:earliest_boundary")

    chain_failures: list[str] = []
    for rel in BOUNDARY_CHAIN_SURFACES:
        if not (root / rel).is_file():
            chain_failures.append(f"MISSING_SURFACE:{rel}")
    boundary_text = _read_rel(BOUNDARY_CHAIN_SURFACES[0])
    if "halt_at_live_execution_boundary_v1" not in boundary_text:
        chain_failures.append("EXECUTION_BOUNDARY_MISSING")
    gate_text = _read_rel(BOUNDARY_CHAIN_SURFACES[1])
    if "EXTERNAL_EFFECT_NOT_AUTHORIZED" not in gate_text:
        chain_failures.append("EXTERNAL_EFFECT_GATE_MISSING_DENY_REASON")
    seam_text = _read_rel(BOUNDARY_CHAIN_SURFACES[2])
    if "STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE" not in seam_text:
        chain_failures.append("ENVELOPE_SEAM_MISSING_STANDING_GUARD")
    post_text = _read_rel(BOUNDARY_CHAIN_SURFACES[4])
    if "post_trade_order" not in post_text:
        chain_failures.append("VENUE_POST_SINK_MISSING")
    if "REAL_VENUE_POST_ALLOWED" not in post_text:
        chain_failures.append("VENUE_POST_SINK_MISSING_STANDING_GUARD")
    for rel in GOVERNED_UPSTREAM_POLICY_SURFACES:
        if not (root / rel).is_file():
            chain_failures.append(f"MISSING_UPSTREAM:{rel}")

    simulated_failures: list[str] = []
    standing = evaluate_external_effect_v1()
    if standing.external_effect_authorized is True:
        simulated_failures.append("STANDING_GATE_AUTHORIZED")
    if standing.fail_closed is not True:
        simulated_failures.append("STANDING_GATE_NOT_FAIL_CLOSED")
    try:
        refuse_external_effect_v1()
    except FullCoreExternalEffectNotAuthorizedError:
        pass
    else:
        simulated_failures.append("REFUSE_EXTERNAL_EFFECT_DID_NOT_RAISE")
    wire_pred = evaluate_external_effect_v1(wire_send_permitted=True)
    if wire_pred.external_effect_authorized is True:
        simulated_failures.append("WIRE_SEND_IMPLIED_EXTERNAL_EFFECT")
    live_pred = evaluate_external_effect_v1(live_authorized=True)
    if live_pred.external_effect_authorized is True:
        simulated_failures.append("LIVE_AUTHORIZED_IMPLIED_EXTERNAL_EFFECT")

    upstream_closure_failures: list[str] = []
    if not prove_governed_current_productive_activation_policy_v1(repo_root=root):
        upstream_closure_failures.append("PRODUCTIVE_ACTIVATION_POLICY_CLOSURE")
    if not prove_governed_current_continuous_run_policy_v1(repo_root=root):
        upstream_closure_failures.append("CONTINUOUS_RUN_POLICY_CLOSURE")
    pre_external = prove_pre_external_to_external_effect_boundary_v1()
    if pre_external.ok is not True:
        upstream_closure_failures.append("PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY")

    ok = not (
        guard_failures
        or decision_failures
        or chain_failures
        or simulated_failures
        or upstream_closure_failures
    )
    return ExternalEffectBoundaryForensicProofResultV1(
        ok=ok,
        guard_failures=tuple(guard_failures),
        decision_failures=tuple(decision_failures),
        chain_failures=tuple(chain_failures),
        simulated_failures=tuple(simulated_failures),
        upstream_closure_failures=tuple(upstream_closure_failures),
    )


__all__ = [
    "ExternalEffectBoundaryForensicProofResultV1",
    "prove_external_effect_boundary_forensic_review_v1",
]
