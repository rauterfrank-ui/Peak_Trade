"""Unified Blueprint Phase 21 — Loop A conditioned Learning integration."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.unified_blueprint_phase_20_behavior_join_v1 import (
    prove_unified_blueprint_phase_20_behavior_join_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.loop_a_conditioned_learning_evidence_v1 import (
    LOOP_A_SCHEMA,
    assert_loop_a_authority_invariants_v1,
)

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_21_LEARNING_INTEGRATION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_21_LEARNING_INTEGRATION_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_21_learning_integration_v1.json"
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    NORMATIVE_SPEC,
    INTEGRATION_CONFIG,
    "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/loop_a_conditioned_learning_evidence_v1.py",
    "src/governance/unified_blueprint_phase_21_learning_integration_v1.py",
    "tests/learning/test_loop_a_conditioned_learning_evidence_v1.py",
    "tests/governance/test_unified_blueprint_phase_21_learning_integration_v1.py",
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


def validate_phase_21_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    for key, expected in (
        ("forecast_is_not_decision", True),
        ("learning_is_not_promotion", True),
        ("no_second_market_truth", True),
        ("no_authority_expansion", True),
        ("mv2_dp_unchanged", True),
        ("multi_future_runtime_authorized", False),
        ("runtime_apply_authorized", False),
        ("phase_20_prerequisite_required", True),
    ):
        if inv.get(key) is not expected:
            errors.append(f"phase_21 authority_invariant {key} must be {expected}")
    if inv.get("market_context_authority") != "NONE":
        errors.append("market_context_authority must be NONE")
    if inv.get("realized_behavior_authority") != "NONE":
        errors.append("realized_behavior_authority must be NONE")
    if inv.get("learning_trading_authority") != "NONE":
        errors.append("learning_trading_authority must be NONE")
    if inv.get("learning_promotion_authority") != "NONE":
        errors.append("learning_promotion_authority must be NONE")
    if inv.get("learning_direct_productive_write") != "FORBIDDEN":
        errors.append("learning_direct_productive_write must be FORBIDDEN")
    if doc.get("phase_21_closure_status") != "PROVEN_COMPLETE":
        errors.append("phase_21_closure_status must be PROVEN_COMPLETE")
    if doc.get("loop_a_status") != "PROVEN":
        errors.append("loop_a_status must be PROVEN")
    return errors


def validate_phase_21_module(repo_root: Path) -> list[str]:
    errors: list[str] = []
    path = (
        repo_root / "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/"
        "loop_a_conditioned_learning_evidence_v1.py"
    )
    text = path.read_text(encoding="utf-8")
    for token in (
        f'LOOP_A_SCHEMA: Final[str] = "{LOOP_A_SCHEMA}"',
        "def compose_conditioned_mi_learning_evidence_v1",
        "def run_loop_a_conditioned_learning_cycle_v1",
        "def assert_loop_a_authority_invariants_v1",
        "CONDITIONED_BINDING_SCHEMA",
    ):
        if token not in text:
            errors.append(f"phase_21 module missing token: {token}")
    return errors


def validate_phase_21_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def prove_unified_blueprint_phase_21_learning_integration_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    if not prove_unified_blueprint_phase_20_behavior_join_v1(repo_root=repo_root):
        errors.append("phase_20 proof failed")
    try:
        assert_loop_a_authority_invariants_v1()
    except Exception:
        errors.append("loop_a authority invariants failed")
    errors.extend(validate_phase_21_authority_invariants(doc))
    errors.extend(validate_phase_21_module(repo_root))
    errors.extend(validate_phase_21_evidence_files(repo_root, doc))
    return not errors


def build_phase_21_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_21_closure_status": doc.get("phase_21_closure_status"),
        "loop_a_status": doc.get("loop_a_status"),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }


__all__ = [
    "INTEGRATION_CONFIG",
    "NORMATIVE_SPEC",
    "WORKPACKAGE_ID",
    "build_phase_21_integration_summary_v1",
    "prove_unified_blueprint_phase_21_learning_integration_v1",
]
