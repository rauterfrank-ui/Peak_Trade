"""Unified Blueprint Phase 20 — MARKET_CONTEXT(t) → REALIZED_BEHAVIOR(t+N) join."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.unified_blueprint_phase_19_orthogonal_context_v1 import (
    prove_unified_blueprint_phase_19_orthogonal_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
    SCHEMA_VERSION,
    assert_realized_behavior_authority_invariants_v1,
)

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_20_BEHAVIOR_JOIN_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_20_BEHAVIOR_JOIN_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_20_behavior_join_v1.json"
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    NORMATIVE_SPEC,
    INTEGRATION_CONFIG,
    "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/realized_behavior_v1.py",
    "src/governance/unified_blueprint_phase_20_behavior_join_v1.py",
    "tests/learning/test_market_context_realized_behavior_join_v1.py",
    "tests/governance/test_unified_blueprint_phase_20_behavior_join_v1.py",
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


def validate_phase_20_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    for key, expected in (
        ("cross_market_is_context_only", True),
        ("forecast_is_not_decision", True),
        ("no_second_market_truth", True),
        ("no_authority_expansion", True),
        ("mv2_dp_unchanged", True),
        ("no_duplicate_outcome_truth", True),
        ("multi_future_runtime_authorized", False),
        ("runtime_apply_authorized", False),
        ("phase_19_prerequisite_required", True),
    ):
        if inv.get(key) is not expected:
            errors.append(f"phase_20 authority_invariant {key} must be {expected}")
    if inv.get("market_context_authority") != "NONE":
        errors.append("market_context_authority must be NONE")
    if inv.get("realized_behavior_authority") != "NONE":
        errors.append("realized_behavior_authority must be NONE")
    if doc.get("phase_20_closure_status") != "PROVEN_COMPLETE":
        errors.append("phase_20_closure_status must be PROVEN_COMPLETE")
    families = doc.get("behavior_family_status")
    if not isinstance(families, dict):
        errors.append("behavior_family_status missing")
    else:
        if families.get("forward_behavior") != "PROVEN_TYPED":
            errors.append("forward_behavior must be PROVEN_TYPED")
        if families.get("excursion") != "PROVEN_TYPED_CLOSE_PATH":
            errors.append("excursion status invalid")
        if families.get("realized_volatility") != "PROVEN_TYPED":
            errors.append("realized_volatility must be PROVEN_TYPED")
        if families.get("transition") != "SEMANTICALLY_UNRESOLVED":
            errors.append("transition must be SEMANTICALLY_UNRESOLVED")
    return errors


def validate_phase_20_module(repo_root: Path) -> list[str]:
    errors: list[str] = []
    path = (
        repo_root / "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/"
        "realized_behavior_v1.py"
    )
    text = path.read_text(encoding="utf-8")
    for token in (
        f'SCHEMA_VERSION: Final[str] = "{SCHEMA_VERSION}"',
        "realized_behavior_v1",
        "def join_market_context_to_realized_behavior_v1",
        "def assert_realized_behavior_authority_invariants_v1",
        "REALIZED_BEHAVIOR_AUTHORITY",
        "N_BARS_OUTCOME_OWNER",
    ):
        if token not in text:
            errors.append(f"phase_20 module missing token: {token}")
    return errors


def validate_phase_20_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def prove_unified_blueprint_phase_20_behavior_join_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    if not prove_unified_blueprint_phase_19_orthogonal_context_v1(repo_root=repo_root):
        errors.append("phase_19 proof failed")
    try:
        assert_realized_behavior_authority_invariants_v1()
    except Exception:
        errors.append("realized_behavior authority invariants failed")
    errors.extend(validate_phase_20_authority_invariants(doc))
    errors.extend(validate_phase_20_module(repo_root))
    errors.extend(validate_phase_20_evidence_files(repo_root, doc))
    return not errors


def build_phase_20_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_20_closure_status": doc.get("phase_20_closure_status"),
        "behavior_family_status": doc.get("behavior_family_status"),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }


__all__ = [
    "INTEGRATION_CONFIG",
    "NORMATIVE_SPEC",
    "WORKPACKAGE_ID",
    "build_phase_20_integration_summary_v1",
    "prove_unified_blueprint_phase_20_behavior_join_v1",
]
