"""Unified Blueprint Phase 11 — optimization surface portfolio closure proof (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.experiments.canonical_optimization_surface_portfolio_registry_v1 import (
    INTEGRATION_CONFIG,
    NORMATIVE_SPEC,
    WORKPACKAGE_ID,
    assert_portfolio_census_closed_v1,
    build_optimization_surface_portfolio_registry_v1,
    prove_phase_11_surface_portfolio_closure_v1,
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    "src/experiments/canonical_optimization_surface_portfolio_registry_v1.py",
    "src/experiments/canonical_optimizable_envelope_v1.py",
    "src/experiments/canonical_optimization_surface_families_pre_test_preparation_v1.py",
    "config/governance/pdf_v3_3_optimization_surface_portfolio_classification_v1.json",
    "tests/experiments/test_canonical_optimization_surface_portfolio_registry_v1.py",
    "tests/governance/test_unified_blueprint_phase_11_surface_portfolio_closure_v1.py",
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


def validate_phase_11_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    required_true = (
        "forecast_is_not_decision",
        "meta_evidence_is_not_authority",
        "learning_is_not_promotion",
        "optimization_is_not_promotion",
        "no_automatic_promotion",
        "no_self_deploy",
        "productive_ddo_reducer_unchanged",
        "mv2_dp_unchanged",
        "cap_2_3_unchanged",
        "n_bars_normative_semantics_unchanged",
        "no_promotion_authority_created",
        "no_external_effect_path",
        "risk_sizing_not_optimizable",
        "universe_member_implies_authorization_false",
        "candidate_implies_productive_configuration_false",
    )
    for key in required_true:
        if inv.get(key) is not True:
            errors.append(f"phase_11 authority_invariant {key} must be true")
    required_false = (
        "search_execution_authorized",
        "learning_state_mutation_authorized",
        "optimization_direct_productive_write_authorized",
        "promotion_authorized",
    )
    for key in required_false:
        if inv.get(key) is not False:
            errors.append(f"phase_11 authority_invariant {key} must be false")
    if doc.get("phase_11_surface_portfolio_closure_status") != "PROVEN_COMPLETE":
        errors.append("phase_11_surface_portfolio_closure_status must be PROVEN_COMPLETE")
    return errors


def validate_phase_11_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def validate_portfolio_registry_runtime(repo_root: Path) -> list[str]:
    del repo_root
    errors: list[str] = []
    if not prove_phase_11_surface_portfolio_closure_v1():
        errors.append("prove_phase_11_surface_portfolio_closure_v1 failed")
    try:
        assert_portfolio_census_closed_v1()
    except ValueError as exc:
        errors.append(str(exc))
    registry = build_optimization_surface_portfolio_registry_v1()
    if not registry.get("authorized_research_surface_ids"):
        errors.append("authorized_research_surface_ids empty")
    return errors


def prove_unified_blueprint_phase_11_surface_portfolio_closure_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    errors.extend(validate_phase_11_authority_invariants(doc))
    errors.extend(validate_phase_11_evidence_files(repo_root, doc))
    errors.extend(validate_portfolio_registry_runtime(repo_root))
    return not errors


def build_phase_11_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    registry = build_optimization_surface_portfolio_registry_v1()
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "normative_spec": NORMATIVE_SPEC,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_11_surface_portfolio_closure_status": doc.get(
            "phase_11_surface_portfolio_closure_status"
        ),
        "authorized_research_surface_ids": registry.get("authorized_research_surface_ids"),
        "research_active_surface_ids": registry.get("research_active_surface_ids"),
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
    "build_phase_11_integration_summary_v1",
    "prove_unified_blueprint_phase_11_surface_portfolio_closure_v1",
    "validate_phase_11_authority_invariants",
    "validate_phase_11_evidence_files",
    "validate_portfolio_registry_runtime",
]
