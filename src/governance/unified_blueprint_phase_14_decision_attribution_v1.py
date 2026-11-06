"""Unified Blueprint Phase 14 — decision attribution closure proof (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.unified_blueprint_decision_attribution_evidence_v1 import (
    DECISION_CONFIG,
    NORMATIVE_SPEC,
    build_decision_attribution_topology_census_v1,
    prove_unified_blueprint_decision_attribution_evidence_v1,
)
from src.governance.unified_blueprint_phase_13_m10_promotion_boundary_v1 import (
    prove_unified_blueprint_phase_13_m10_promotion_boundary_v1,
)

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_14_DECISION_ATTRIBUTION_V1"
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_14_decision_attribution_v1.json"
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    "src/governance/unified_blueprint_decision_attribution_evidence_v1.py",
    "config/governance/unified_blueprint_decision_attribution_evidence_v1_decision_v1.json",
    "config/governance/unified_blueprint_decision_attribution_topology_v1.json",
    "tests/governance/test_unified_blueprint_decision_attribution_evidence_v1.py",
    "tests/governance/test_unified_blueprint_phase_14_decision_attribution_v1.py",
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


def validate_phase_14_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    required_true = (
        "compose_references_dont_duplicate_ownership",
        "attribution_is_evidence_only",
        "decision_authority_not_duplicated",
        "no_self_deploy",
        "mv2_dp_unchanged",
        "cap_2_3_unchanged",
        "phase_13_m10_boundary_required",
        "lookahead_guard_required",
        "fail_closed_identity_binding",
    )
    for key in required_true:
        if inv.get(key) is not True:
            errors.append(f"phase_14 authority_invariant {key} must be true")
    required_false = (
        "attribution_creates_trading_decision",
        "attribution_mutates_selection",
        "promotion_authorized",
        "runtime_apply_authorized",
        "optimizer_direct_productive_write_authorized",
    )
    for key in required_false:
        if inv.get(key) is not False:
            errors.append(f"phase_14 authority_invariant {key} must be false")
    if doc.get("phase_14_decision_attribution_status") != "PROVEN_COMPLETE":
        errors.append("phase_14_decision_attribution_status must be PROVEN_COMPLETE")
    return errors


def validate_phase_14_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def validate_phase_14_runtime(repo_root: Path) -> list[str]:
    errors: list[str] = []
    if not prove_unified_blueprint_phase_13_m10_promotion_boundary_v1(repo_root=repo_root):
        errors.append("phase_13_m10_boundary_not_proven")
    if not prove_unified_blueprint_decision_attribution_evidence_v1(repo_root=repo_root):
        errors.append("prove_unified_blueprint_decision_attribution_evidence_v1 failed")
    census = build_decision_attribution_topology_census_v1()
    if census.get("canonical_boundary_module") != (
        "src/governance/unified_blueprint_decision_attribution_evidence_v1.py"
    ):
        errors.append("topology_canonical_boundary_mismatch")
    return errors


def prove_unified_blueprint_phase_14_decision_attribution_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    errors.extend(validate_phase_14_authority_invariants(doc))
    errors.extend(validate_phase_14_evidence_files(repo_root, doc))
    errors.extend(validate_phase_14_runtime(repo_root))
    return not errors


def build_phase_14_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_14_decision_attribution_status": doc.get("phase_14_decision_attribution_status"),
        "first_unproven_dependency_after_closure": doc.get(
            "first_unproven_dependency_after_closure"
        ),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
        "topology_census_digest": build_decision_attribution_topology_census_v1().get(
            "census_digest"
        ),
    }
