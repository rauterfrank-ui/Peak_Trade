"""Unified Blueprint Phase 19 — orthogonal context (DERIVATIVES + CROSS_MARKET)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.unified_blueprint_phase_18_existing_fact_market_context_materialization_v1 import (
    prove_unified_blueprint_phase_18_existing_fact_market_context_materialization_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_phase_19_orthogonal_materialization_v1 import (
    PHASE_19_SCHEMA,
)

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_19_ORTHOGONAL_CONTEXT_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_19_ORTHOGONAL_CONTEXT_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_19_orthogonal_context_v1.json"
)
ANCHOR_BINDING_CONFIG: Final[str] = (
    "config/governance/market_context_v1_phase_19_cross_market_anchor_binding_v1.json"
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    NORMATIVE_SPEC,
    INTEGRATION_CONFIG,
    ANCHOR_BINDING_CONFIG,
    "src/ops/peak_trade_public_market_data_runtime_v1/facts_v1.py",
    "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_phase_19_orthogonal_materialization_v1.py",
    "src/governance/unified_blueprint_phase_19_orthogonal_context_v1.py",
    "tests/learning/test_market_context_phase_19_orthogonal_materialization_v1.py",
    "tests/governance/test_unified_blueprint_phase_19_orthogonal_context_v1.py",
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


def validate_phase_19_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    for key, expected in (
        ("cross_market_is_context_only", True),
        ("public_ws_strategy_unchanged", True),
        ("no_second_market_truth", True),
        ("no_authority_expansion", True),
        ("mv2_dp_unchanged", True),
        ("multi_future_runtime_authorized", False),
        ("runtime_apply_authorized", False),
        ("cap23_selection_from_cross_market_forbidden", True),
        ("phase_18_prerequisite_required", True),
    ):
        if inv.get(key) is not expected:
            errors.append(f"phase_19 authority_invariant {key} must be {expected}")
    if inv.get("market_context_authority") != "NONE":
        errors.append("market_context_authority must be NONE")
    if doc.get("phase_19_closure_status") != "PROVEN_COMPLETE":
        errors.append("phase_19_closure_status must be PROVEN_COMPLETE")
    families = doc.get("family_terminal_status")
    if not isinstance(families, dict):
        errors.append("family_terminal_status missing")
    else:
        for fam in ("derivatives_state", "cross_market_state"):
            if families.get(fam) != "PROVEN_TYPED_OR_EXPLICIT_MISSING":
                errors.append(f"family_terminal_status {fam} invalid")
    return errors


def validate_anchor_binding(repo_root: Path) -> list[str]:
    errors: list[str] = []
    doc = _load_json(repo_root, ANCHOR_BINDING_CONFIG)
    if doc.get("context_only") is not True:
        errors.append("anchor binding must be context_only")
    if doc.get("cap23_selection_authority") is not False:
        errors.append("anchor binding must not grant cap23 authority")
    if doc.get("rerank_authorized") is not False:
        errors.append("anchor binding rerank must be false")
    return errors


def validate_phase_19_module(repo_root: Path) -> list[str]:
    errors: list[str] = []
    path = (
        repo_root / "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/"
        "market_context_phase_19_orthogonal_materialization_v1.py"
    )
    text = path.read_text(encoding="utf-8")
    for token in (
        f'PHASE_19_SCHEMA: Final[str] = "{PHASE_19_SCHEMA}"',
        "def derive_derivatives_state_slot_v1",
        "def derive_cross_market_state_slot_v1",
        "def assert_phase_19_authority_invariants_v1",
        "CROSS_MARKET_CONTEXT_ONLY",
    ):
        if token not in text:
            errors.append(f"phase_19 module missing token: {token}")
    facts = repo_root / "src/ops/peak_trade_public_market_data_runtime_v1/facts_v1.py"
    facts_text = facts.read_text(encoding="utf-8")
    for token in ("IndexPriceFactV1", "FundingRateFactV1", "OpenInterestFactV1"):
        if token not in facts_text:
            errors.append(f"facts_v1 missing {token}")
    return errors


def validate_phase_19_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def prove_unified_blueprint_phase_19_orthogonal_context_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    if not prove_unified_blueprint_phase_18_existing_fact_market_context_materialization_v1(
        repo_root=repo_root
    ):
        errors.append("phase_18 proof failed")
    errors.extend(validate_phase_19_authority_invariants(doc))
    errors.extend(validate_anchor_binding(repo_root))
    errors.extend(validate_phase_19_module(repo_root))
    errors.extend(validate_phase_19_evidence_files(repo_root, doc))
    return not errors


def build_phase_19_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_19_closure_status": doc.get("phase_19_closure_status"),
        "family_terminal_status": doc.get("family_terminal_status"),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }
