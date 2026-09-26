"""Unified Blueprint Phase 25 — DP Attribution closure proof (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.unified_blueprint_decision_attribution_evidence_v1 import (
    prove_unified_blueprint_decision_attribution_evidence_v1,
)
from src.governance.unified_blueprint_phase_24_representation_feedback_loop_v1 import (
    prove_unified_blueprint_phase_24_representation_feedback_loop_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.phase_25_dp_attribution_evidence_v1 import (
    PHASE_25_SCHEMA,
    assert_phase_25_dp_attribution_authority_invariants_v1,
)

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_25_DP_ATTRIBUTION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_25_DP_ATTRIBUTION_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_25_dp_attribution_v1.json"
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    NORMATIVE_SPEC,
    INTEGRATION_CONFIG,
    "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_25_dp_attribution_evidence_v1.py",
    "src/governance/unified_blueprint_phase_25_dp_attribution_v1.py",
    "tests/learning/test_phase_25_dp_attribution_evidence_v1.py",
    "tests/governance/test_unified_blueprint_phase_25_dp_attribution_v1.py",
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


def validate_phase_25_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    for key, expected in (
        ("attribution_evidence_only", True),
        ("compose_references_dont_duplicate_ownership", True),
        ("mv2_dp_unchanged", True),
        ("no_trading_gate_from_attribution", True),
        ("no_authority_expansion", True),
        ("no_reranking_reselection", True),
        ("no_optimization_promotion", True),
        ("phase_24_prerequisite_required", True),
        ("phase_14_decision_attribution_required", True),
        ("phase_26_final_dod_forbidden", True),
        ("pit_join_required", True),
        ("horizon_identity_required", True),
        ("deterministic_replay_required", True),
    ):
        if inv.get(key) is not expected:
            errors.append(f"phase_25 authority_invariant {key} must be {expected}")
    for key, expected in (
        ("attribution_authority", "NONE"),
        ("optimization_promotion_authority", "NONE"),
        ("optimization_direct_productive_write", "FORBIDDEN"),
    ):
        if inv.get(key) != expected:
            errors.append(f"phase_25 authority_invariant {key} must be {expected}")
    proof = doc.get("dp_attribution_proof")
    if not isinstance(proof, dict):
        errors.append("dp_attribution_proof missing")
    else:
        for flag in (
            "phase_24_prerequisite_proven",
            "phase_14_compose_reused",
            "market_context_ref_bound",
            "realized_behavior_ref_bound",
            "mv2_dp_decision_ref_bound",
            "pit_join_proven",
            "horizon_identity_proven",
            "provenance_preserved",
            "deterministic_replay_proven",
            "no_trading_gate_from_attribution",
            "mv2_dp_unchanged",
            "no_authority_expansion",
            "dp_attribution_proven",
        ):
            if proof.get(flag) is not True:
                errors.append(f"dp_attribution_proof.{flag} must be true")
    if doc.get("phase_25_closure_status") != "PROVEN_COMPLETE":
        errors.append("phase_25_closure_status must be PROVEN_COMPLETE")
    return errors


def validate_phase_25_module(repo_root: Path) -> list[str]:
    errors: list[str] = []
    rel = (
        "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/"
        "phase_25_dp_attribution_evidence_v1.py"
    )
    text = (repo_root / rel).read_text(encoding="utf-8")
    for token in (
        f'PHASE_25_SCHEMA: Final[str] = "{PHASE_25_SCHEMA}"',
        "def compose_dp_attribution_evidence_v1",
        "def inspect_dp_attribution_evidence_v1",
        "def assert_phase_25_dp_attribution_authority_invariants_v1",
    ):
        if token not in text:
            errors.append(f"phase_25 module missing token: {token}")
    return errors


def validate_phase_25_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def prove_unified_blueprint_phase_25_dp_attribution_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    if not prove_unified_blueprint_phase_24_representation_feedback_loop_v1(repo_root=repo_root):
        errors.append("phase_24 proof failed")
    if not prove_unified_blueprint_decision_attribution_evidence_v1(repo_root=repo_root):
        errors.append("phase_14 decision attribution proof failed")
    try:
        assert_phase_25_dp_attribution_authority_invariants_v1()
    except Exception:
        errors.append("phase_25 authority invariants failed")
    errors.extend(validate_phase_25_authority_invariants(doc))
    errors.extend(validate_phase_25_module(repo_root))
    errors.extend(validate_phase_25_evidence_files(repo_root, doc))
    return not errors


def build_phase_25_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_25_closure_status": doc.get("phase_25_closure_status"),
        "dp_attribution_proof": doc.get("dp_attribution_proof"),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }


__all__ = [
    "INTEGRATION_CONFIG",
    "NORMATIVE_SPEC",
    "WORKPACKAGE_ID",
    "build_phase_25_integration_summary_v1",
    "prove_unified_blueprint_phase_25_dp_attribution_v1",
]
