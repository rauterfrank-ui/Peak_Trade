"""Unified Blueprint Phase 17 — normative non-price CMC / MARKET_CONTEXT_V1 closure (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.unified_blueprint_phase_16_cmc_non_price_census_v1 import (
    prove_unified_blueprint_phase_16_cmc_non_price_census_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    CONTRACT_ID,
    MARKET_CONTEXT_AUTHORITY,
    N_BARS_BACKBONE_TOKEN,
    SCHEMA_VERSION,
)

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_17_NORMATIVE_NON_PRICE_CMC_CONTRACT_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_17_NORMATIVE_NON_PRICE_CMC_CONTRACT_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_17_normative_non_price_cmc_contract_v1.json"
)
OWNER_DECISION_CONFIG: Final[str] = (
    "config/governance/normative_non_price_cmc_contract_owner_decision_v1.json"
)
PHASE_16_CENSUS_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_16_cmc_non_price_census_v1.json"
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    NORMATIVE_SPEC,
    INTEGRATION_CONFIG,
    OWNER_DECISION_CONFIG,
    PHASE_16_CENSUS_CONFIG,
    "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_v1.py",
    "src/governance/unified_blueprint_phase_17_normative_non_price_cmc_contract_v1.py",
    "tests/learning/test_market_context_v1.py",
    "tests/governance/test_unified_blueprint_phase_16_cmc_non_price_census_v1.py",
    "tests/governance/test_unified_blueprint_phase_17_normative_non_price_cmc_contract_v1.py",
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


def validate_owner_decision(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("decision_id") != "NORMATIVE_NON_PRICE_CMC_CONTRACT_OWNER_DECISION":
        errors.append("owner decision_id mismatch")
    if doc.get("decision_status") != "RATIFIED":
        errors.append("owner decision must be RATIFIED")
    points = doc.get("owner_decision_points")
    if not isinstance(points, dict):
        return ["owner_decision_points missing"]
    for key, expected in points.items():
        if expected is not True:
            errors.append(f"owner_decision_point {key} must be true")
    if doc.get("contract_id") != CONTRACT_ID:
        errors.append("owner decision contract_id mismatch")
    return errors


def validate_phase_17_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    required_true = (
        "n_bars_backbone_semantics_unchanged",
        "cross_market_context_only",
        "microstructure_proxy_l2_not_collapsed",
        "missing_semantics_explicit",
        "pit_no_lookahead",
        "provenance_required",
        "feature_versions_required",
        "information_set_identity_required",
        "mv2_dp_unchanged",
        "phase_16_census_required",
        "owner_decision_ratified",
    )
    for key in required_true:
        if inv.get(key) is not True:
            errors.append(f"phase_17 authority_invariant {key} must be true")
    required_false = (
        "trading_decision_authority_created",
        "selection_authority_created",
        "promotion_authority_created",
        "risk_sizing_authority_created",
        "external_effect_authority_created",
        "second_market_truth_created",
    )
    for key in required_false:
        if inv.get(key) is not False:
            errors.append(f"phase_17 authority_invariant {key} must be false")
    if inv.get("market_context_authority") != MARKET_CONTEXT_AUTHORITY:
        errors.append("market_context_authority must be NONE")
    if doc.get("phase_17_closure_status") != "PROVEN_COMPLETE":
        errors.append("phase_17_closure_status must be PROVEN_COMPLETE")
    if doc.get("blocker_normative_non_price_cmc_contract_owner_decision") != "CLOSED":
        errors.append("blocker must be CLOSED")
    return errors


def validate_phase_17_contract_constants(repo_root: Path) -> list[str]:
    errors: list[str] = []
    module = (
        repo_root
        / "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_v1.py"
    )
    text = module.read_text(encoding="utf-8")
    for token in (
        f'SCHEMA_VERSION: Final[str] = "{SCHEMA_VERSION}"',
        f'CONTRACT_ID: Final[str] = "{CONTRACT_ID}"',
        f'MARKET_CONTEXT_AUTHORITY: Final[str] = "{MARKET_CONTEXT_AUTHORITY}"',
        f'N_BARS_BACKBONE_TOKEN: Final[str] = "{N_BARS_BACKBONE_TOKEN}"',
        "def compose_market_context_v1_from_governed_inputs",
        "def serialize_market_context_canonical_v1",
    ):
        if token not in text:
            errors.append(f"market_context_v1 missing token: {token}")
    return errors


def validate_phase_17_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def prove_unified_blueprint_phase_17_normative_non_price_cmc_contract_v1(
    *, repo_root: Path
) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    owner = _load_json(repo_root, OWNER_DECISION_CONFIG)
    errors: list[str] = []
    if not prove_unified_blueprint_phase_16_cmc_non_price_census_v1(repo_root=repo_root):
        errors.append("phase_16 census proof failed")
    errors.extend(validate_owner_decision(owner))
    errors.extend(validate_phase_17_authority_invariants(doc))
    errors.extend(validate_phase_17_contract_constants(repo_root))
    errors.extend(validate_phase_17_evidence_files(repo_root, doc))
    return not errors


def build_phase_17_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_17_closure_status": doc.get("phase_17_closure_status"),
        "market_context_v1_status": doc.get("market_context_v1_status"),
        "non_price_cmc_contract_status": doc.get("non_price_cmc_contract_status"),
        "blocker_normative_non_price_cmc_contract_owner_decision": doc.get(
            "blocker_normative_non_price_cmc_contract_owner_decision"
        ),
        "first_unproven_dependency_after_closure": doc.get(
            "first_unproven_dependency_after_closure"
        ),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }
