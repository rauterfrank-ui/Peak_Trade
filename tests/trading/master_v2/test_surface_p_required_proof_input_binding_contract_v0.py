"""Surface P required proof-input binding contract tests (offline only)."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import patch

from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    parity_surface_assessments_v0,
)
from trading.master_v2.legacy_runtime_entrypoint_guard_v0 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
)
from trading.master_v2.surface_p_required_proof_input_binding_v0 import (
    BINDING_SLICE_ID,
    PACKAGE_MARKER,
    REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P,
    SURFACE_P_PROOF_INPUT_ID,
    SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_OWNER,
    SURFACE_P_SURFACE_ID,
    binding_result_field_names_v0,
    evaluate_surface_p_required_proof_input_binding_v0,
    surface_p_required_proof_input_binding_to_dict_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

_SLICE_CHANGED_FILES = (
    "src/trading/master_v2/surface_p_required_proof_input_binding_v0.py",
    "scripts/research/full_canonical_parity_proof_bundle_assembler_v0.py",
    "scripts/research/full_canonical_surface_p_required_proof_input_v0.py",
    "tests/trading/master_v2/test_surface_p_required_proof_input_binding_contract_v0.py",
)

_SLICE_SOURCE_PATHS = tuple(REPO_ROOT / p for p in _SLICE_CHANGED_FILES if p.endswith(".py"))


def _scan_forbidden_imports(path: Path, forbidden_tokens: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in forbidden_tokens):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden_tokens):
                hits.append(node.module)
    return hits


def test_binding_constants_v0() -> None:
    assert BINDING_SLICE_ID == "SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_V0"
    assert PACKAGE_MARKER == "SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_V0=true"
    assert SURFACE_P_PROOF_INPUT_ID == "backtest_offline_replay_runtime_decision_parity"
    assert SURFACE_P_SURFACE_ID == "P"
    assert SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_OWNER.endswith(
        "surface_p_required_proof_input_binding_v0"
    )


def test_surface_p_resolved_registry_passes_when_proof_input_satisfied_v0() -> None:
    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    assert surface_p.parity_status == "PASS"
    assert surface_p.missing_binding_if_any == ""


def test_current_head_surface_p_required_proof_input_binding_verified_v0() -> None:
    result = evaluate_surface_p_required_proof_input_binding_v0(REPO_ROOT)
    assert result.satisfied is True
    assert result.binding_status == "VERIFIED"
    assert result.registry_parity_status == "PARTIAL"
    assert result.offline_four_way_fixtures_complete is True
    assert result.semantic_binding_confirmations_complete is True
    assert result.surface_p_offline_parity_complete is True
    assert result.runtime_bridge_bound_not_activated is True
    assert result.owner_evidence_refs_present is True
    assert result.present_evidence_ref_count == result.evidence_ref_count
    assert result.missing_evidence_refs == ()
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "BOUND_NOT_ACTIVATED"


def test_missing_owner_evidence_refs_fail_closed_with_surface_p_reason_v0(
    tmp_path: Path,
) -> None:
    with patch(
        "trading.master_v2.surface_p_required_proof_input_binding_v0._count_present_evidence_refs",
        return_value=(0, ("missing/evidence.py",)),
    ):
        result = evaluate_surface_p_required_proof_input_binding_v0(tmp_path)
    assert result.satisfied is False
    assert result.binding_status == "MISSING_REQUIRED_PROOF_INPUT_SURFACE_P"
    assert REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P in result.fail_closed_reasons


def test_binding_json_schema_deterministic_v0() -> None:
    result = evaluate_surface_p_required_proof_input_binding_v0(REPO_ROOT)
    payload = surface_p_required_proof_input_binding_to_dict_v0(result)
    assert payload["binding_slice_id"] == BINDING_SLICE_ID
    assert payload["proof_input_id"] == SURFACE_P_PROOF_INPUT_ID
    assert payload["surface_id"] == SURFACE_P_SURFACE_ID
    assert payload["binding_status"] == "VERIFIED"
    assert payload["full_canonical_chain_wired"] is False
    assert payload["backtest_runtime_decision_parity_pass"] is False
    assert payload["system_economic_evidence_admissible"] is False
    assert payload["runtime_rewire_admissible"] is False
    assert payload["claim_promotion_allowed"] is False
    assert payload["no_runtime_authority_confirmed"] is True
    assert payload["no_economic_claim_confirmed"] is True
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    assert '"binding_status": "VERIFIED"' in encoded


def test_final_success_flags_remain_false_v0() -> None:
    result = evaluate_surface_p_required_proof_input_binding_v0(REPO_ROOT)
    assert result.full_canonical_chain_wired is False
    assert result.backtest_runtime_decision_parity_pass is False
    assert result.system_economic_evidence_admissible is False
    assert result.runtime_rewire_admissible is False
    assert result.claim_promotion_allowed is False


def test_slice_sources_exclude_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "scheduler",
            "credentials",
            "live_runtime",
            "testnet",
            "shadow",
            "paper_lane",
        }
    )
    for path in _SLICE_SOURCE_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_binding_result_has_required_fields_v0() -> None:
    names = binding_result_field_names_v0()
    assert "binding_status" in names
    assert "satisfied" in names
    assert "missing_evidence_refs" in names
