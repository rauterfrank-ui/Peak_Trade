"""Unified Blueprint Phase 9 — MI→Optimization M4 integration proof (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_9_MI_TO_OPTIMIZATION_M4_INTEGRATION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_9_MI_TO_OPTIMIZATION_M4_INTEGRATION_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1.json"
)
D02_ADJUDICATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_d01_d02_topology_adjudication_v1.json"
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    "src/experiments/canonical_optimization_universe_mi_enriched_m4_intake_v1.py",
    "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/offline_orchestrator_v1.py",
    "tests/experiments/test_canonical_optimization_universe_mi_enriched_m4_intake_v1.py",
    "tests/governance/test_unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1.py",
    "tests/learning/test_unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1.py",
)


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def git_head_sha(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def validate_phase_9_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    required_true = (
        "forecast_is_not_decision",
        "learning_is_not_promotion",
        "optimization_is_not_promotion",
        "no_automatic_promotion",
        "no_self_deploy",
        "productive_ddo_reducer_unchanged",
        "mv2_dp_unchanged",
        "no_promotion_authority_created",
        "no_external_effect_path",
        "risk_sizing_not_optimizable",
        "cap_2_3_unchanged",
    )
    for key in required_true:
        if inv.get(key) is not True:
            errors.append(f"phase_9 authority_invariant {key} must be true")
    if inv.get("d02_mi_to_optimization_status") != "IMPLEMENTED":
        errors.append("d02_mi_to_optimization_status must be IMPLEMENTED when Phase 9 closes")
    if doc.get("phase_9_mi_to_optimization_m4_integration_status") != "PROVEN_COMPLETE":
        errors.append("phase_9_mi_to_optimization_m4_integration_status must be PROVEN_COMPLETE")
    return errors


def validate_phase_9_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    refs = doc.get("evidence_refs")
    if not isinstance(refs, list):
        return ["evidence_refs missing"]
    for ref in _REQUIRED_EVIDENCE:
        if ref not in refs:
            errors.append(f"evidence_refs missing required ref: {ref}")
        if not (repo_root / ref).is_file():
            errors.append(f"missing evidence file: {ref}")
    return errors


def validate_d02_mi_to_optimization_edge_implemented(repo_root: Path) -> list[str]:
    errors: list[str] = []
    d02 = _load_json(repo_root, D02_ADJUDICATION_CONFIG)
    edges = d02.get("d02_inter_loop_edges") or []
    mi_edge = next(
        (e for e in edges if isinstance(e, dict) and e.get("edge_id") == "d02_mi_to_optimization"),
        None,
    )
    if not isinstance(mi_edge, dict):
        return ["d02_mi_to_optimization edge missing from adjudication config"]
    if mi_edge.get("implementation_status") != "IMPLEMENTED":
        errors.append("d02_mi_to_optimization must be IMPLEMENTED after Phase 9 closure")
    if mi_edge.get("missing_dependency"):
        errors.append("d02_mi_to_optimization missing_dependency must be null when IMPLEMENTED")
    return errors


def prove_unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1(
    *, repo_root: Path
) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    errors.extend(validate_phase_9_authority_invariants(doc))
    errors.extend(validate_phase_9_evidence_files(repo_root, doc))
    errors.extend(validate_d02_mi_to_optimization_edge_implemented(repo_root))
    return not errors


def build_phase_9_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "d02_mi_to_optimization_status": doc.get("authority_invariants", {}).get(
            "d02_mi_to_optimization_status"
        ),
        "phase_9_mi_to_optimization_m4_integration_status": doc.get(
            "phase_9_mi_to_optimization_m4_integration_status"
        ),
        "first_unproven_dependency_after_closure": doc.get(
            "first_unproven_dependency_after_closure"
        ),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }
