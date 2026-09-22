"""Static proof for PRE_EXTERNAL → external-effect authorization boundary (no POST)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, Tuple

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CONTINUOUS_RUN_AUTHORIZED,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    evaluate_external_effect_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    LIVE_ADMISSION_GAP_NODES,
)
from src.ops.p5_10_productive_activation_and_binding_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    FINAL_D_T_FORMULA_SELECTED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1.constants_v1 import (
    CANARY_WIRE_SEND_HARNESS_PREFIX,
    INTENTIONALLY_ISOLATED_OWNER_GO_POST_SLICES,
    INTENTIONALLY_LEGACY_PRE_EXTERNAL_CLAIM_MODULES,
    PRE_EXTERNAL_PRODUCTIVE_ENTRY_MODULES,
)
from src.ops.whole_system_connection_closure_bounded_wp_v1.proof_v1 import (
    prove_whole_system_connection_closure_v1,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SKIP_SCAN_PREFIX = "src/ops/pre_external_to_external_effect_boundary_bounded_wp_v1/"

_SINK_CALL_MARKERS = (
    "attempt_envelope_bound_external_effect_send_v1(",
    "invoke_external_effect_v1(",
    "run_productive_wire_send_orchestrator_v1(",
    "issue_external_effect_permit_v1(",
)

_ALLOWED_SINK_CALLER_PREFIXES = (
    "src/ops/full_core_live_path_composition_root_v1/execution_boundary_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/external_effect_gate_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/external_effect_permit_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_envelope_bound_single_use_external_effect_send_seam_v1.py",
    CANARY_WIRE_SEND_HARNESS_PREFIX,
    "tests/",
) + INTENTIONALLY_ISOLATED_OWNER_GO_POST_SLICES


@dataclass(frozen=True)
class PreExternalToExternalEffectBoundaryProofResultV1:
    ok: bool
    guard_failures: Tuple[str, ...]
    pre_external_sink_violations: Tuple[str, ...]
    unclassified_sink_callers: Tuple[str, ...]
    boundary_chain_failures: Tuple[str, ...]
    whole_system_connection_ok: bool


def _rel(path: Path) -> str:
    try:
        return path.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _read_rel(rel: str) -> str:
    return (_REPO_ROOT / rel).read_text(encoding="utf-8")


def _allowed_sink_caller(rel: str) -> bool:
    for prefix in _ALLOWED_SINK_CALLER_PREFIXES:
        if rel == prefix or rel.startswith(prefix):
            return True
    return False


def _scan_sink_callers() -> FrozenSet[str]:
    src_root = _REPO_ROOT / "src"
    hits: set[str] = set()
    for path in src_root.rglob("*.py"):
        rel = _rel(path)
        if rel.startswith(_SKIP_SCAN_PREFIX):
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in _SINK_CALL_MARKERS):
            hits.add(rel)
    return frozenset(hits)


def prove_pre_external_to_external_effect_boundary_v1() -> (
    PreExternalToExternalEffectBoundaryProofResultV1
):
    """Fail-closed static census; does not execute cycles, permits, or network I/O."""
    guard_failures: list[str] = []
    if P5_AUTHORITY_CUTOVER_AUTHORIZED is not False:
        guard_failures.append("P5_AUTHORITY_CUTOVER_AUTHORIZED")
    if PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED is not False:
        guard_failures.append("PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED")
    if FINAL_D_T_FORMULA_SELECTED is not False:
        guard_failures.append("FINAL_D_T_FORMULA_SELECTED")
    if EXTERNAL_EFFECT_AUTHORIZED is not False:
        guard_failures.append("EXTERNAL_EFFECT_AUTHORIZED")
    if MULTI_FUTURE_RUNTIME_AUTHORIZED is not False:
        guard_failures.append("MULTI_FUTURE_RUNTIME_AUTHORIZED")
    if MAX_POSITIONS_EFFECTIVE != 1:
        guard_failures.append("MAX_POSITIONS_EFFECTIVE")
    if CONTINUOUS_RUN_AUTHORIZED is not False:
        guard_failures.append("CONTINUOUS_RUN_AUTHORIZED")

    standing = evaluate_external_effect_v1()
    if standing.external_effect_authorized is True or standing.venue_mutation_performed is True:
        guard_failures.append("STANDING_EXTERNAL_EFFECT_GATE")

    whole = prove_whole_system_connection_closure_v1()
    whole_ok = whole.ok is True
    if not whole_ok:
        guard_failures.append("WHOLE_SYSTEM_CONNECTION_PROOF")

    pre_external_violations: list[str] = []
    for rel in PRE_EXTERNAL_PRODUCTIVE_ENTRY_MODULES:
        text = _read_rel(rel)
        if (
            "PRE_EXTERNAL_EFFECT_BOUNDARY_REACHED" not in text
            and "DISPOSITION_PRE_EXTERNAL_EFFECT" not in text
        ):
            pre_external_violations.append(f"{rel}:missing_pre_external_terminal_marker")
        for marker in _SINK_CALL_MARKERS:
            if marker in text:
                pre_external_violations.append(f"{rel}:forbidden_sink_marker:{marker}")
        if "one_shot_real_post=True" in text:
            pre_external_violations.append(f"{rel}:one_shot_real_post_true")

    for rel in INTENTIONALLY_LEGACY_PRE_EXTERNAL_CLAIM_MODULES:
        text = _read_rel(rel)
        if "PRE_EXTERNAL_EFFECT_BOUNDARY_REACHED" not in text:
            pre_external_violations.append(f"{rel}:missing_legacy_pre_external_marker")

    boundary_failures: list[str] = []
    boundary_text = _read_rel(
        "src/ops/full_core_live_path_composition_root_v1/execution_boundary_v1.py"
    )
    if "halt_at_live_execution_boundary_v1" not in boundary_text:
        boundary_failures.append("execution_boundary_missing")
    if "evaluate_external_effect_v1" not in boundary_text:
        boundary_failures.append("execution_boundary_missing_external_effect_eval")
    if "refuse_wire_send_v1" not in boundary_text:
        boundary_failures.append("execution_boundary_missing_refuse_wire")

    path_text = _read_rel("src/ops/full_core_live_path_composition_root_v1/path_v1.py")
    if "halt_at_live_execution_boundary_v1" not in path_text:
        boundary_failures.append("offline_live_path_missing_halt_join")
    if "wire_send_occurred=False" not in path_text:
        boundary_failures.append("offline_live_path_wire_send_hard_false")

    seam_text = _read_rel(
        "src/ops/full_core_live_path_composition_root_v1/"
        "envelope_bound_external_effect_send_seam_v1.py"
    )
    if "evaluate_external_effect_v1()" not in seam_text:
        boundary_failures.append("envelope_seam_missing_standing_gate")
    if "EXTERNAL_EFFECT_AUTHORIZED is True" not in seam_text:
        boundary_failures.append("envelope_seam_missing_standing_false_guard")

    dag_ids = {node.component_id for node in LIVE_ADMISSION_GAP_NODES}
    for required in ("SUBMISSION_AUTHORIZED", "LIVE_AUTHORIZED", "EXTERNAL_EFFECT"):
        if required not in dag_ids:
            boundary_failures.append(f"live_admission_gap_missing:{required}")

    observed_sink_callers = _scan_sink_callers()
    unclassified = sorted(rel for rel in observed_sink_callers if not _allowed_sink_caller(rel))

    ok = (
        not guard_failures
        and not pre_external_violations
        and not unclassified
        and not boundary_failures
        and whole_ok
    )
    return PreExternalToExternalEffectBoundaryProofResultV1(
        ok=ok,
        guard_failures=tuple(guard_failures),
        pre_external_sink_violations=tuple(pre_external_violations),
        unclassified_sink_callers=tuple(unclassified),
        boundary_chain_failures=tuple(boundary_failures),
        whole_system_connection_ok=whole_ok,
    )


__all__ = [
    "PreExternalToExternalEffectBoundaryProofResultV1",
    "prove_pre_external_to_external_effect_boundary_v1",
]
