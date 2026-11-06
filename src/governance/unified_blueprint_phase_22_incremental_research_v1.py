"""Unified Blueprint Phase 22 — incremental information research (B0–B5)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.unified_blueprint_phase_21_learning_integration_v1 import (
    prove_unified_blueprint_phase_21_learning_integration_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.phase_22_incremental_research_evidence_v1 import (
    PHASE_22_SCHEMA,
    assert_phase_22_authority_invariants_v1,
)

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_22_INCREMENTAL_RESEARCH_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_22_INCREMENTAL_RESEARCH_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_22_incremental_research_v1.json"
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    NORMATIVE_SPEC,
    INTEGRATION_CONFIG,
    "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/incremental_information_set_v1.py",
    "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_22_incremental_research_evidence_v1.py",
    "src/governance/unified_blueprint_phase_22_incremental_research_v1.py",
    "tests/learning/test_incremental_information_set_v1.py",
    "tests/learning/test_phase_22_incremental_research_evidence_v1.py",
    "tests/governance/test_unified_blueprint_phase_22_incremental_research_v1.py",
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


def validate_phase_22_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    for key, expected in (
        ("forecast_is_not_decision", True),
        ("no_feature_admission_by_availability", True),
        ("no_automatic_promotion", True),
        ("no_self_deploy", True),
        ("cross_market_is_context_only", True),
        ("no_authority_expansion", True),
        ("mv2_dp_unchanged", True),
        ("multi_future_runtime_authorized", False),
        ("runtime_apply_authorized", False),
        ("phase_21_prerequisite_required", True),
        ("phase_23_dual_routing_forbidden", True),
    ):
        if inv.get(key) is not expected:
            errors.append(f"phase_22 authority_invariant {key} must be {expected}")
    for key, expected in (
        ("market_context_authority", "NONE"),
        ("realized_behavior_authority", "NONE"),
        ("learning_trading_authority", "NONE"),
        ("optimization_trading_decision_authority", "NONE"),
        ("optimization_promotion_authority", "NONE"),
        ("optimization_direct_productive_write", "FORBIDDEN"),
        ("meta_evidence_authority", "NONE"),
        ("research_disposition_authority", "NONE"),
    ):
        if inv.get(key) != expected:
            errors.append(f"phase_22 authority_invariant {key} must be {expected}")
    if doc.get("phase_22_closure_status") != "PROVEN_COMPLETE":
        errors.append("phase_22_closure_status must be PROVEN_COMPLETE")
    return errors


def validate_phase_22_module(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for rel, tokens in (
        (
            "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/"
            "incremental_information_set_v1.py",
            (
                'INCREMENTAL_INFORMATION_SET_SCHEMA: Final[str] = "incremental_information_set_v1"',
                "def build_incremental_information_set_v1",
                "def project_market_context_to_stage_v1",
                "def assert_market_context_respects_stage_boundary_v1",
            ),
        ),
        (
            "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/"
            "phase_22_incremental_research_evidence_v1.py",
            (
                f'PHASE_22_SCHEMA: Final[str] = "{PHASE_22_SCHEMA}"',
                "def run_incremental_stage_research_v1",
                "def run_phase_22_incremental_research_closure_v1",
                "def assert_phase_22_authority_invariants_v1",
            ),
        ),
    ):
        text = (repo_root / rel).read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                errors.append(f"phase_22 module missing token: {token} in {rel}")
    return errors


def validate_phase_22_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def build_current_optimization_research_census_v1() -> Mapping[str, str]:
    return {
        "optimization_universe": "PROVEN_CURRENT",
        "experiment_identity": "PROVEN_CURRENT",
        "dataset_evidence_identity": "DERIVABLE_FROM_CURRENT",
        "learning_input": "PROVEN_CURRENT",
        "research_feature_representation": "PROVEN_CURRENT",
        "search_choice": "PROVEN_CURRENT",
        "challenger": "PROVEN_CURRENT",
        "oos": "PROVEN_CURRENT",
        "walk_forward": "DERIVABLE_FROM_CURRENT",
        "robustness_stress": "PROVEN_CURRENT",
        "calibration_evaluation": "DERIVABLE_FROM_CURRENT",
        "coverage_evaluation": "DERIVABLE_FROM_CURRENT",
        "failure_evidence": "PROVEN_CURRENT",
        "experiment_persistence": "PROVEN_CURRENT",
        "experiment_registry": "PROVEN_CURRENT",
        "meta_learning_ingest": "PROVEN_CURRENT",
        "optimization_evidence_return": "PROVEN_CURRENT",
        "true_l2_research_substrate": "MISSING",
        "phase_22_incremental_information_set": "PROVEN_CURRENT",
    }


def prove_unified_blueprint_phase_22_incremental_research_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    if not prove_unified_blueprint_phase_21_learning_integration_v1(repo_root=repo_root):
        errors.append("phase_21 proof failed")
    try:
        assert_phase_22_authority_invariants_v1()
    except Exception:
        errors.append("phase_22 authority invariants failed")
    errors.extend(validate_phase_22_authority_invariants(doc))
    errors.extend(validate_phase_22_module(repo_root))
    errors.extend(validate_phase_22_evidence_files(repo_root, doc))
    return not errors


def build_phase_22_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_22_closure_status": doc.get("phase_22_closure_status"),
        "b5_status": doc.get("b5_status"),
        "research_census": build_current_optimization_research_census_v1(),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }


__all__ = [
    "INTEGRATION_CONFIG",
    "NORMATIVE_SPEC",
    "WORKPACKAGE_ID",
    "build_current_optimization_research_census_v1",
    "build_phase_22_integration_summary_v1",
    "prove_unified_blueprint_phase_22_incremental_research_v1",
]
