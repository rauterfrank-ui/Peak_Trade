"""Unified Blueprint Phase 12 — productive lineage closure proof (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.experiments.canonical_optimization_productive_lineage_registry_v1 import (
    INTEGRATION_CONFIG,
    NORMATIVE_SPEC,
    WORKPACKAGE_ID,
    assert_phase_12_census_closed_v1,
    build_productive_lineage_registry_v1,
    prove_phase_12_productive_lineage_closure_v1,
)
from src.experiments.canonical_optimization_surface_portfolio_registry_v1 import (
    prove_phase_11_surface_portfolio_closure_v1,
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    "src/experiments/canonical_optimization_productive_lineage_registry_v1.py",
    "config/governance/pdf_v3_3_productive_consumer_binding_registry_v1.json",
    "config/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1_decision_v1.json",
    "tests/experiments/test_canonical_optimization_productive_lineage_registry_v1.py",
    "tests/governance/test_unified_blueprint_phase_12_productive_lineage_closure_v1.py",
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


def validate_phase_12_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    required_true = (
        "research_authorization_implies_productive_authorization_false",
        "candidate_implies_productive_configuration_false",
        "proposal_implies_authorization_false",
        "evidence_implies_authorization_false",
        "no_self_deploy",
        "risk_is_hard_boundary",
        "mv2_dp_unchanged",
        "cap_2_3_unchanged",
        "no_promotion_authority_created",
        "no_external_effect_path",
        "risk_sizing_not_optimizable",
        "phase_11_portfolio_closure_required",
    )
    for key in required_true:
        if inv.get(key) is not True:
            errors.append(f"phase_12 authority_invariant {key} must be true")
    required_false = (
        "optimization_direct_productive_write_authorized",
        "promotion_authorized",
        "runtime_apply_authorized_by_optimizer",
        "configuration_implies_runtime_apply",
    )
    for key in required_false:
        if inv.get(key) is not False:
            errors.append(f"phase_12 authority_invariant {key} must be false")
    if doc.get("phase_12_productive_lineage_closure_status") != "PROVEN_COMPLETE":
        errors.append("phase_12_productive_lineage_closure_status must be PROVEN_COMPLETE")
    return errors


def validate_phase_12_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def validate_phase_12_runtime(repo_root: Path) -> list[str]:
    del repo_root
    errors: list[str] = []
    if not prove_phase_11_surface_portfolio_closure_v1():
        errors.append("phase_11_portfolio_closure_not_proven")
    if not prove_phase_12_productive_lineage_closure_v1():
        errors.append("prove_phase_12_productive_lineage_closure_v1 failed")
    try:
        assert_phase_12_census_closed_v1()
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def prove_unified_blueprint_phase_12_productive_lineage_closure_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    errors.extend(validate_phase_12_authority_invariants(doc))
    errors.extend(validate_phase_12_evidence_files(repo_root, doc))
    errors.extend(validate_phase_12_runtime(repo_root))
    return not errors


def build_phase_12_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    registry = build_productive_lineage_registry_v1()
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_12_productive_lineage_closure_status": doc.get(
            "phase_12_productive_lineage_closure_status"
        ),
        "surfaces": registry.get("surfaces"),
        "registry_digest": registry.get("registry_digest"),
        "first_unproven_dependency_after_closure": doc.get(
            "first_unproven_dependency_after_closure"
        ),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }


__all__ = [
    "INTEGRATION_CONFIG",
    "NORMATIVE_SPEC",
    "WORKPACKAGE_ID",
    "build_phase_12_integration_summary_v1",
    "prove_unified_blueprint_phase_12_productive_lineage_closure_v1",
    "validate_phase_12_authority_invariants",
    "validate_phase_12_evidence_files",
    "validate_phase_12_runtime",
]
