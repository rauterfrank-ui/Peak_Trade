"""Unified Blueprint Phase 16 — non-price CMC census (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_16_CMC_NON_PRICE_CENSUS_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_16_CMC_NON_PRICE_CENSUS_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_16_cmc_non_price_census_v1.json"
)

_REQUIRED_CENSUS_ROW_IDS: Final[frozenset[str]] = frozenset(
    {
        "cmc_trading_runtime_canonical_market_context_v1",
        "cmc_feature_contract_layer_pointer",
        "i25_typed_volatility_estimate",
        "wp_a_public_market_facts",
        "i04_sentiment_news_onchain",
        "i05_orderbook_tick",
        "microstructure_proxy_vs_l2_separation",
        "mi_forecast_information_set_ref",
    }
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    NORMATIVE_SPEC,
    INTEGRATION_CONFIG,
    "src/governance/unified_blueprint_phase_16_cmc_non_price_census_v1.py",
    "tests/governance/test_unified_blueprint_phase_16_cmc_non_price_census_v1.py",
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


def validate_phase_16_census_rows(doc: Mapping[str, Any], repo_root: Path) -> list[str]:
    errors: list[str] = []
    rows = doc.get("census_rows")
    if not isinstance(rows, list) or not rows:
        return ["census_rows missing"]
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"census_rows[{index}] not object")
            continue
        row_id = str(row.get("row_id") or "")
        if not row_id:
            errors.append(f"census_rows[{index}] missing row_id")
            continue
        seen.add(row_id)
        refs = row.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"census row {row_id} missing evidence_refs")
            continue
        for ref in refs:
            if not (repo_root / str(ref)).is_file():
                errors.append(f"census row {row_id} missing evidence file: {ref}")
    missing_rows = _REQUIRED_CENSUS_ROW_IDS - seen
    if missing_rows:
        errors.append(f"census missing required rows: {sorted(missing_rows)}")
    return errors


def validate_phase_16_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    for key, expected in (
        ("canonical_market_facts_remain_ssot", True),
        ("cmc_does_not_create_second_market_truth", True),
        ("mv2_canonical_market_context_is_trading_input_not_mi_compositional_owner", True),
        ("n_bars_backbone_unchanged", True),
        ("cross_market_context_only_required", True),
        ("microstructure_proxy_l2_must_not_collapse", True),
        ("unknown_mixed_ownership_fail_closed", True),
        ("ws_transport_redesign_forbidden", True),
        ("mv2_dp_sole_trading_decision_authority", True),
    ):
        if inv.get(key) is not expected:
            errors.append(f"phase_16 authority_invariant {key} must be {expected}")
    if doc.get("phase_16_cmc_census_status") != "PROVEN_COMPLETE":
        errors.append("phase_16_cmc_census_status must be PROVEN_COMPLETE")
    if doc.get("cmc_census_closure_status") != "CLOSED":
        errors.append("cmc_census_closure_status must be CLOSED")
    if doc.get("earliest_blocker_before_phase_17") != (
        "NORMATIVE_NON_PRICE_CMC_CONTRACT_OWNER_DECISION"
    ):
        errors.append("earliest_blocker_before_phase_17 mismatch")
    return errors


def validate_phase_16_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
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


def prove_unified_blueprint_phase_16_cmc_non_price_census_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    errors.extend(validate_phase_16_authority_invariants(doc))
    errors.extend(validate_phase_16_census_rows(doc, repo_root))
    errors.extend(validate_phase_16_evidence_files(repo_root, doc))
    return not errors


def build_phase_16_census_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_16_cmc_census_status": doc.get("phase_16_cmc_census_status"),
        "cmc_census_closure_status": doc.get("cmc_census_closure_status"),
        "earliest_blocker_before_phase_17": doc.get("earliest_blocker_before_phase_17"),
        "blocker_status_at_census_close": doc.get("blocker_status_at_census_close"),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }
