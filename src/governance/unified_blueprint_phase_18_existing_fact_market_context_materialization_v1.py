"""Unified Blueprint Phase 18 — existing-fact MARKET_CONTEXT_V1 materialization (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.unified_blueprint_phase_17_normative_non_price_cmc_contract_v1 import (
    prove_unified_blueprint_phase_17_normative_non_price_cmc_contract_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_existing_fact_materialization_v1 import (
    MATERIALIZATION_SCHEMA,
)

WORKPACKAGE_ID: Final[str] = (
    "UNIFIED_BLUEPRINT_PHASE_18_EXISTING_FACT_MARKET_CONTEXT_MATERIALIZATION_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_18_EXISTING_FACT_MARKET_CONTEXT_MATERIALIZATION_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_18_existing_fact_market_context_materialization_v1.json"
)
PHASE_17_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_17_normative_non_price_cmc_contract_v1.json"
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    NORMATIVE_SPEC,
    INTEGRATION_CONFIG,
    "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_existing_fact_materialization_v1.py",
    "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_existing_fact_mi_bridge_v1.py",
    "src/governance/unified_blueprint_phase_18_existing_fact_market_context_materialization_v1.py",
    "tests/learning/test_market_context_existing_fact_materialization_v1.py",
    "tests/governance/test_unified_blueprint_phase_18_existing_fact_market_context_materialization_v1.py",
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


def validate_phase_18_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    required_true = (
        "canonical_market_facts_remain_ssot",
        "missing_semantics_explicit",
        "pit_no_lookahead",
        "provenance_required",
        "feature_versions_required",
        "information_set_identity_required",
        "deterministic_replay_required",
        "microstructure_proxy_l2_not_collapsed",
        "n_bars_backbone_semantics_unchanged",
        "mv2_dp_unchanged",
        "phase_17_contract_required",
        "implicit_producer_discovery_forbidden",
    )
    for key in required_true:
        if inv.get(key) is not True:
            errors.append(f"phase_18 authority_invariant {key} must be true")
    required_false = (
        "second_market_truth_created",
        "trading_decision_authority_created",
        "selection_authority_created",
        "promotion_authority_created",
        "risk_sizing_authority_created",
        "external_effect_authority_created",
        "runtime_apply_authorized",
    )
    for key in required_false:
        if inv.get(key) is not False:
            errors.append(f"phase_18 authority_invariant {key} must be false")
    if inv.get("market_context_authority") != "NONE":
        errors.append("market_context_authority must be NONE")
    if doc.get("phase_18_closure_status") != "PROVEN_COMPLETE":
        errors.append("phase_18_closure_status must be PROVEN_COMPLETE")
    families = doc.get("family_materialization_status")
    if not isinstance(families, dict):
        errors.append("family_materialization_status missing")
    return errors


def validate_phase_18_materialization_module(repo_root: Path) -> list[str]:
    errors: list[str] = []
    module = (
        repo_root / "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/"
        "market_context_existing_fact_materialization_v1.py"
    )
    text = module.read_text(encoding="utf-8")
    for token in (
        f'MATERIALIZATION_SCHEMA: Final[str] = "{MATERIALIZATION_SCHEMA}"',
        "def materialize_market_context_v1_from_existing_facts_v1",
        "def validate_governed_canonical_fact_v1",
        "def replay_market_context_serialization_v1",
        "MICROSTRUCTURE_KIND_PROXY_OHLCV",
    ):
        if token not in text:
            errors.append(f"materialization module missing token: {token}")
    return errors


def validate_phase_18_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def prove_unified_blueprint_phase_18_existing_fact_market_context_materialization_v1(
    *, repo_root: Path
) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    if not prove_unified_blueprint_phase_17_normative_non_price_cmc_contract_v1(
        repo_root=repo_root
    ):
        errors.append("phase_17 proof failed")
    errors.extend(validate_phase_18_authority_invariants(doc))
    errors.extend(validate_phase_18_materialization_module(repo_root))
    errors.extend(validate_phase_18_evidence_files(repo_root, doc))
    return not errors


def build_phase_18_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_18_closure_status": doc.get("phase_18_closure_status"),
        "market_context_materialization_status": doc.get("market_context_materialization_status"),
        "family_materialization_status": doc.get("family_materialization_status"),
        "first_unproven_dependency_after_closure": doc.get(
            "first_unproven_dependency_after_closure"
        ),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }
