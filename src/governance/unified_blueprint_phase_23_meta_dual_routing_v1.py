"""Unified Blueprint Phase 23 — Meta-Learning dual routing."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.unified_blueprint_phase_22_incremental_research_v1 import (
    prove_unified_blueprint_phase_22_incremental_research_v1,
)
from src.experiments.canonical_meta_evidence_dual_router_v1 import (
    SCHEMA_VERSION as ROUTER_SCHEMA,
    assert_meta_dual_routing_authority_invariants_v1,
)

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_23_META_DUAL_ROUTING_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_23_META_DUAL_ROUTING_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_23_meta_dual_routing_v1.json"
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    NORMATIVE_SPEC,
    INTEGRATION_CONFIG,
    "src/learning/deterministic_decision_outcome_v0/meta_evidence_v1.py",
    "src/experiments/canonical_meta_evidence_dual_router_v1.py",
    "src/experiments/canonical_meta_to_learning_research_adaptation_input_v1.py",
    "src/governance/unified_blueprint_phase_23_meta_dual_routing_v1.py",
    "tests/experiments/test_canonical_meta_evidence_dual_router_v1.py",
    "tests/learning/test_meta_evidence_v1.py",
    "tests/governance/test_unified_blueprint_phase_23_meta_dual_routing_v1.py",
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


def validate_phase_23_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
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
        ("no_meta_broadcast", True),
        ("no_trading_gate_from_meta", True),
        ("mv2_dp_unchanged", True),
        ("no_authority_expansion", True),
        ("phase_22_prerequisite_required", True),
        ("phase_24_representation_feedback_forbidden", True),
        ("loop_c_proven_claim_forbidden", True),
    ):
        if inv.get(key) is not expected:
            errors.append(f"phase_23 authority_invariant {key} must be {expected}")
    for key, expected in (
        ("meta_evidence_authority", "NONE"),
        ("optimization_promotion_authority", "NONE"),
        ("optimization_direct_productive_write", "FORBIDDEN"),
        ("learning_trading_authority", "NONE"),
    ):
        if inv.get(key) != expected:
            errors.append(f"phase_23 authority_invariant {key} must be {expected}")
    if doc.get("phase_23_closure_status") != "PROVEN_COMPLETE":
        errors.append("phase_23_closure_status must be PROVEN_COMPLETE")
    routing = doc.get("routing_proof")
    if not isinstance(routing, dict):
        errors.append("routing_proof missing")
    else:
        for flag in (
            "meta_routing_typed",
            "research_choice_to_optimization_only",
            "learning_representation_to_learning_only",
            "unknown_mixed_fail_closed",
            "no_meta_broadcast",
            "deterministic_routing_replay",
            "provenance_preserved",
            "wrong_consumer_rejected",
        ):
            if routing.get(flag) is not True:
                errors.append(f"routing_proof.{flag} must be true")
    return errors


def validate_phase_23_module(repo_root: Path) -> list[str]:
    errors: list[str] = []
    checks = (
        (
            "src/learning/deterministic_decision_outcome_v0/meta_evidence_v1.py",
            ('SCHEMA_VERSION: Final[str] = "meta_evidence_v1"', "def build_meta_evidence_v1"),
        ),
        (
            "src/experiments/canonical_meta_evidence_dual_router_v1.py",
            (f'SCHEMA_VERSION: Final[str] = "{ROUTER_SCHEMA}"', "def route_meta_evidence_v1"),
        ),
    )
    for rel, tokens in checks:
        text = (repo_root / rel).read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                errors.append(f"phase_23 module missing token: {token} in {rel}")
    return errors


def validate_phase_23_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def prove_unified_blueprint_phase_23_meta_dual_routing_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    if not prove_unified_blueprint_phase_22_incremental_research_v1(repo_root=repo_root):
        errors.append("phase_22 proof failed")
    try:
        assert_meta_dual_routing_authority_invariants_v1()
    except Exception:
        errors.append("dual router authority invariants failed")
    errors.extend(validate_phase_23_authority_invariants(doc))
    errors.extend(validate_phase_23_module(repo_root))
    errors.extend(validate_phase_23_evidence_files(repo_root, doc))
    return not errors


def build_phase_23_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_23_closure_status": doc.get("phase_23_closure_status"),
        "routing_proof": doc.get("routing_proof"),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }


__all__ = [
    "INTEGRATION_CONFIG",
    "NORMATIVE_SPEC",
    "WORKPACKAGE_ID",
    "build_phase_23_integration_summary_v1",
    "prove_unified_blueprint_phase_23_meta_dual_routing_v1",
]
