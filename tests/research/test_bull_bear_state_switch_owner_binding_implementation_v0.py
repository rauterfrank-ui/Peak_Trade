from __future__ import annotations

import json
from pathlib import Path

from src.research.owner_bindings.bull_bear_state_switch_owner_binding_v0 import (
    build_bull_bear_state_switch_owner_binding_v0,
)


DOC_JSON = Path("docs/research/bull_bear_state_switch_owner_binding_implementation_v0.json")


def test_bull_bear_state_switch_owner_binding_contract_is_authority_neutral() -> None:
    binding = build_bull_bear_state_switch_owner_binding_v0()
    contract = binding.as_contract()

    assert contract["surface_id"] == "bull_bear_state_switch_owner"
    assert contract["canonical_owner"] == "src/trading/master_v2"
    assert contract["reuse_decision"] == "REUSE_WITH_NARROW_ADAPTER"
    assert contract["implementation_mode"] == "OWNER_BINDING_ONLY_NO_RUNTIME_REWIRE"
    assert contract["authority_effect"] == "NONE"
    assert contract["runtime_effect"] == "NONE"
    assert contract["no_runtime_rewire"] is True
    assert contract["no_runtime_evidence"] is True
    assert contract["no_order_authority"] is True
    assert contract["no_credential_authority"] is True
    assert contract["no_scheduler_authority"] is True
    assert contract["no_promotion_authority"] is True
    assert contract["no_economic_pass_authority"] is True


def test_bull_bear_state_switch_owner_binding_blocks_runtime_and_promotion_effects() -> None:
    binding = build_bull_bear_state_switch_owner_binding_v0()
    blocked = set(binding.blocked_effects)

    assert "runtime_rewire" in blocked
    assert "runtime_evidence" in blocked
    assert "order_submission" in blocked
    assert "credential_use" in blocked
    assert "arming" in blocked
    assert "scheduler_start" in blocked
    assert "promotion_pass" in blocked
    assert "economic_pass_claim" in blocked


def test_bull_bear_state_switch_owner_binding_doc_matches_runtime_contract() -> None:
    doc = json.loads(DOC_JSON.read_text())
    binding = build_bull_bear_state_switch_owner_binding_v0()
    contract = binding.as_contract()

    assert doc["surface_id"] == contract["surface_id"]
    assert doc["canonical_owner"] == contract["canonical_owner"]
    assert doc["reuse_decision"] == contract["reuse_decision"]
    assert doc["implementation_mode"] == contract["implementation_mode"]
    assert doc["authority_effect"] == contract["authority_effect"]
    assert doc["runtime_effect"] == contract["runtime_effect"]
    assert doc["system_economic_evidence_admissible"] is False
    assert doc["backtest_runtime_decision_parity_pass"] is False
    assert doc["runtime_rewire_admissible"] is False


def test_bull_bear_state_switch_owner_binding_does_not_claim_backtest_parity() -> None:
    binding = build_bull_bear_state_switch_owner_binding_v0()
    assertions = set(binding.required_parity_assertions)

    assert "BULL_BEAR_STATE_SWITCH_OWNER_BOUND" in assertions
    assert "NO_PARALLEL_STATE_SWITCH_OWNER" in assertions
    assert "BACKTEST_PARITY_NOT_CLAIMED_BY_THIS_SLICE" in assertions
    assert "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE_FALSE" in assertions
