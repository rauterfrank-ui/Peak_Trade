from __future__ import annotations

import json
from pathlib import Path


CONTRACT_PATH = Path(
    "docs/research/owner_bound_narrow_reuse_first_integration_slice_for_highest_priority_confirmed_gap_v0.json"
)
SOURCE_PATH = Path(
    "docs/research/full_canonical_system_backtest_parity_gap_assessment_execution_v0.json"
)


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_owner_bound_slice_contract_source_assessment_exists() -> None:
    contract = _contract()
    assert contract["source_assessment_required"] is True
    assert SOURCE_PATH.is_file()
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    assert source["next_allowed_step"] == contract["next_step"]


def test_owner_bound_slice_contract_selected_gap_bound() -> None:
    contract = _contract()
    selected_gap = contract["selected_gap"]
    assert contract["selected_gap_source_path"]
    assert selected_gap
    assert selected_gap.get("surface") or selected_gap.get("gap_id") or selected_gap.get("id")
    assert contract["owner_binding_required"] is True
    assert contract["narrow_slice_required"] is True


def test_owner_bound_slice_contract_authority_neutral() -> None:
    contract = _contract()
    authority = contract["authority"]
    assert authority["authority_effect"] == "NONE"
    assert authority["runtime_effect"] == "NONE"
    assert authority["economic_evidence_claim"] is False
    assert authority["runtime_rewire_admissible"] is False
    assert authority["system_economic_evidence_admissible"] is False
    assert authority["orders_allowed"] is False
    assert authority["credentials_allowed"] is False
    assert authority["arming_allowed"] is False


def test_owner_bound_slice_contract_implementation_scope_recorded() -> None:
    contract = _contract()
    scope = contract["implementation_scope"]
    assert scope["allowed"]
    assert scope["disallowed"]
    assert "runtime_rewire" in scope["disallowed"]
    assert "orders" in scope["disallowed"]
    assert "identify_existing_owner" in scope["allowed"]


def test_owner_bound_slice_contract_reuse_first_order_recorded() -> None:
    contract = _contract()
    assert contract["reuse_first_order"] == [
        "REUSE_AS_IS",
        "REUSE_WITH_NARROW_ADAPTER",
        "REWIRE_EXISTING_COMPONENT",
        "CONSOLIDATE_TO_EXISTING_OWNER",
        "NEW_IMPLEMENTATION_JUSTIFIED_ONLY_IF_REUSE_BLOCKED",
    ]


def test_owner_bound_slice_contract_verdict_and_acceptance_gates() -> None:
    contract = _contract()
    assert contract["verdict"] == (
        "PASS_OWNER_BOUND_NARROW_REUSE_FIRST_INTEGRATION_SLICE_CONTRACT_CREATED"
    )
    assert contract["slice_mode"] == "CONTRACT_AND_IMPLEMENTATION_SCOPE_ONLY"
    assert "source_assessment_exists" in contract["acceptance_gates"]
    assert "manifest_verify_rc_0" in contract["acceptance_gates"]
