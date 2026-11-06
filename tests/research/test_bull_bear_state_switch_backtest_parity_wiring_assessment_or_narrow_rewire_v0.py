import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "docs"
    / "research"
    / "bull_bear_state_switch_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_contract_is_authority_neutral_and_no_runtime():
    data = load_contract()
    assert data["authority_effect"] == "NONE"
    assert data["runtime_effect"] == "NONE"
    assert data["orders_allowed"] is False
    assert data["scheduler_runtime_allowed"] is False
    assert data["live_authorized"] is False
    assert data["shadow_authorized"] is False
    assert data["paper_authorized"] is False
    assert data["testnet_authorized"] is False


def test_contract_does_not_claim_system_economic_or_runtime_parity():
    data = load_contract()
    assert data["system_economic_evidence_admissible"] is False
    assert data["runtime_rewire_admissible"] is False
    assert data["economic_evaluation_authorized"] is False
    assert data["full_canonical_chain_wired_claim"] is False
    assert data["backtest_runtime_decision_parity_pass_claim"] is False


def test_contract_binds_expected_surface_and_owner():
    data = load_contract()
    assert data["target_surface"] == "Bull/Bear State Switch Backtest Parity Wiring"
    assert data["canonical_owner"] == "src/trading/master_v2"
    assert data["prior_owner_binding"].endswith("bull_bear_state_switch_owner_binding_v0.py")
    assert data["assessment_status"] in {
        "ASSESSED_EXISTING_BACKTEST_PARITY_WIRING_CANDIDATE_FOUND_REVIEW_REQUIRED",
        "FAIL_CLOSED_OWNER_BOUND_BUT_BACKTEST_WIRING_NOT_PROVEN",
        "FAIL_CLOSED_GAP_CONFIRMED_REWIRE_REQUIRED",
    }


def test_narrow_rewire_is_not_implemented_by_assessment_slice():
    data = load_contract()
    decision = data["narrow_rewire_decision"]
    assert decision["mode"] == "ASSESSMENT_FIRST_FAIL_CLOSED"
    assert decision["rewire_implemented"] is False
    assert (
        decision["admissible_next_slice_if_gap_confirmed"]
        == "BULL_BEAR_STATE_SWITCH_BACKTEST_PARITY_NARROW_REWIRE_V0"
    )
