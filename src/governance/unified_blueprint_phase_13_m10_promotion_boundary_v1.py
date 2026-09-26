"""Unified Blueprint Phase 13 — M10 promotion boundary closure proof (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.experiments.canonical_optimization_productive_lineage_registry_v1 import (
    prove_phase_12_productive_lineage_closure_v1,
)
from src.governance.m10_promotion_boundary_v1 import (
    DECISION_CONFIG,
    NORMATIVE_SPEC,
    build_m10_promotion_topology_adjudication_v1,
    prove_m10_promotion_boundary_v1,
)

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_13_M10_PROMOTION_BOUNDARY_V1"
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_13_m10_promotion_boundary_v1.json"
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    "src/governance/m10_promotion_boundary_v1.py",
    "config/governance/m10_promotion_boundary_v1_decision_v1.json",
    "config/governance/m10_promotion_topology_adjudication_v1.json",
    "tests/governance/test_m10_promotion_boundary_v1.py",
    "tests/governance/test_unified_blueprint_phase_13_m10_promotion_boundary_v1.py",
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


def validate_phase_13_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    required_true = (
        "research_authorization_implies_promotion_authorization_false",
        "productive_relevance_implies_promotion_authorization_false",
        "proposal_implies_authorization_false",
        "evidence_implies_authorization_false",
        "authorized_promotion_implies_runtime_apply_false",
        "authorized_promotion_implies_deployment_false",
        "authorized_promotion_implies_external_effect_false",
        "no_self_deploy",
        "risk_is_hard_boundary",
        "mv2_dp_unchanged",
        "cap_2_3_unchanged",
        "phase_12_productive_lineage_closure_required",
    )
    for key in required_true:
        if inv.get(key) is not True:
            errors.append(f"phase_13 authority_invariant {key} must be true")
    required_false = (
        "optimization_direct_productive_write_authorized",
        "promotion_authorized_by_optimizer",
        "runtime_apply_authorized_by_optimizer",
        "m11_automation_authorized",
    )
    for key in required_false:
        if inv.get(key) is not False:
            errors.append(f"phase_13 authority_invariant {key} must be false")
    if doc.get("phase_13_m10_promotion_boundary_status") != "PROVEN_COMPLETE":
        errors.append("phase_13_m10_promotion_boundary_status must be PROVEN_COMPLETE")
    return errors


def validate_phase_13_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    refs = doc.get("evidence_refs")
    if not isinstance(refs, list):
        return ["evidence_refs missing"]
    for ref in _REQUIRED_EVIDENCE:
        if ref not in refs:
            errors.append(f"evidence_refs missing required ref: {ref}")
        if not (repo_root / ref).is_file():
            errors.append(f"missing evidence file: {ref}")
    if not (repo_root / NORMATIVE_SPEC).is_file():
        errors.append(f"missing normative spec: {NORMATIVE_SPEC}")
    return errors


def validate_phase_13_runtime(repo_root: Path) -> list[str]:
    errors: list[str] = []
    if not prove_phase_12_productive_lineage_closure_v1():
        errors.append("phase_12_productive_lineage_closure_not_proven")
    if not prove_m10_promotion_boundary_v1(repo_root=repo_root):
        errors.append("prove_m10_promotion_boundary_v1 failed")
    topology = build_m10_promotion_topology_adjudication_v1()
    canonical = str(topology.get("canonical_m10_boundary_module") or "")
    if canonical != "src/governance/m10_promotion_boundary_v1.py":
        errors.append("m10_topology_canonical_boundary_mismatch")
    decision = _load_json(repo_root, DECISION_CONFIG)
    if decision.get("canonical_m10_boundary_module") != canonical:
        errors.append("decision_config_canonical_boundary_mismatch")
    return errors


def prove_unified_blueprint_phase_13_m10_promotion_boundary_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    errors.extend(validate_phase_13_authority_invariants(doc))
    errors.extend(validate_phase_13_evidence_files(repo_root, doc))
    errors.extend(validate_phase_13_runtime(repo_root))
    return not errors


def build_phase_13_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_13_m10_promotion_boundary_status": doc.get("phase_13_m10_promotion_boundary_status"),
        "first_unproven_dependency_after_closure": doc.get(
            "first_unproven_dependency_after_closure"
        ),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
        "topology_adjudication_digest": build_m10_promotion_topology_adjudication_v1().get(
            "adjudication_digest"
        ),
    }
