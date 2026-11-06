"""Unified Blueprint Phase 24 — Loop C representation feedback closure."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.unified_blueprint_phase_23_meta_dual_routing_v1 import (
    prove_unified_blueprint_phase_23_meta_dual_routing_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.phase_24_representation_feedback_loop_evidence_v1 import (
    PHASE_24_SCHEMA,
    assert_phase_24_loop_c_authority_invariants_v1,
)

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_24_REPRESENTATION_FEEDBACK_LOOP_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_24_REPRESENTATION_FEEDBACK_LOOP_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_24_representation_feedback_loop_v1.json"
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    NORMATIVE_SPEC,
    INTEGRATION_CONFIG,
    "src/experiments/canonical_learning_representation_research_adaptation_plan_v1.py",
    "src/experiments/canonical_learning_representation_offline_evaluation_v1.py",
    "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_24_representation_feedback_loop_evidence_v1.py",
    "src/governance/unified_blueprint_phase_24_representation_feedback_loop_v1.py",
    "tests/experiments/test_canonical_learning_representation_research_adaptation_plan_v1.py",
    "tests/experiments/test_canonical_learning_representation_offline_evaluation_v1.py",
    "tests/learning/test_phase_24_representation_feedback_loop_evidence_v1.py",
    "tests/governance/test_unified_blueprint_phase_24_representation_feedback_loop_v1.py",
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


def validate_phase_24_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    for key, expected in (
        ("no_automatic_promotion", True),
        ("no_self_deploy", True),
        ("no_self_modifying_learning", True),
        ("no_direct_feature_drop", True),
        ("no_direct_parameter_mutation", True),
        ("no_trading_gate_from_meta", True),
        ("mv2_dp_unchanged", True),
        ("no_authority_expansion", True),
        ("phase_23_prerequisite_required", True),
        ("phase_25_dp_attribution_forbidden", True),
        ("phase_26_final_dod_forbidden", True),
        ("productive_apply_forbidden", True),
    ):
        if inv.get(key) is not expected:
            errors.append(f"phase_24 authority_invariant {key} must be {expected}")
    for key, expected in (
        ("meta_evidence_authority", "NONE"),
        ("learning_trading_authority", "NONE"),
        ("optimization_promotion_authority", "NONE"),
        ("optimization_direct_productive_write", "FORBIDDEN"),
    ):
        if inv.get(key) != expected:
            errors.append(f"phase_24 authority_invariant {key} must be {expected}")
    if doc.get("phase_24_closure_status") != "PROVEN_COMPLETE":
        errors.append("phase_24_closure_status must be PROVEN_COMPLETE")
    loop_c = doc.get("loop_c_proof")
    if not isinstance(loop_c, dict):
        errors.append("loop_c_proof missing")
    else:
        for flag in (
            "learning_representation_input_bound",
            "bounded_learning_adaptation_consumer_proven",
            "meta_to_learning_evidence_only",
            "research_adaptation_plan_separate_from_productive_apply",
            "next_learning_evidence_generation_proven",
            "loop_c_deterministic_replay",
            "loop_c_provenance_preserved",
            "loop_c_iteration_lineage_proven",
            "no_self_modifying_learning",
            "no_direct_productive_mutation",
            "no_trading_authority_expansion",
            "no_authority_expansion",
        ):
            if loop_c.get(flag) is not True:
                errors.append(f"loop_c_proof.{flag} must be true")
        if loop_c.get("loop_c_proven") is not True:
            errors.append("loop_c_proof.loop_c_proven must be true")
    return errors


def validate_phase_24_module(repo_root: Path) -> list[str]:
    errors: list[str] = []
    rel = (
        "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/"
        "phase_24_representation_feedback_loop_evidence_v1.py"
    )
    text = (repo_root / rel).read_text(encoding="utf-8")
    for token in (
        f'PHASE_24_SCHEMA: Final[str] = "{PHASE_24_SCHEMA}"',
        "def run_loop_c_representation_feedback_closure_v1",
        "def assert_phase_24_loop_c_authority_invariants_v1",
    ):
        if token not in text:
            errors.append(f"phase_24 module missing token: {token}")
    return errors


def validate_phase_24_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def prove_unified_blueprint_phase_24_representation_feedback_loop_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    if not prove_unified_blueprint_phase_23_meta_dual_routing_v1(repo_root=repo_root):
        errors.append("phase_23 proof failed")
    try:
        assert_phase_24_loop_c_authority_invariants_v1()
    except Exception:
        errors.append("phase_24 authority invariants failed")
    errors.extend(validate_phase_24_authority_invariants(doc))
    errors.extend(validate_phase_24_module(repo_root))
    errors.extend(validate_phase_24_evidence_files(repo_root, doc))
    return not errors


def build_phase_24_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_24_closure_status": doc.get("phase_24_closure_status"),
        "loop_c_proof": doc.get("loop_c_proof"),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }


__all__ = [
    "INTEGRATION_CONFIG",
    "NORMATIVE_SPEC",
    "WORKPACKAGE_ID",
    "build_phase_24_integration_summary_v1",
    "prove_unified_blueprint_phase_24_representation_feedback_loop_v1",
]
