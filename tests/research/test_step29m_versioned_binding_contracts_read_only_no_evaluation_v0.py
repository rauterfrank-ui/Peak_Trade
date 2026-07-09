import json
from pathlib import Path


CONTRACT_PATH = Path(
    "docs/research/step29m_versioned_binding_contracts_read_only_no_evaluation_v0.json"
)


def test_step29m_binding_contracts_are_complete_read_only_no_eval_v0():
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert (
        payload["contract_id"] == "STEP29M_VERSIONED_BINDING_CONTRACTS_READ_ONLY_NO_EVALUATION_V0"
    )
    assert payload["step29m_candidate_fleet"] == [
        "trend_following",
        "bollinger_bands",
        "momentum_1h",
    ]

    boundaries = payload["authority_boundaries"]
    assert boundaries["runtime_rewire_admissible"] is False
    assert boundaries["economic_evaluation_execution_authorized"] is False
    assert boundaries["promotion_authority_granted"] is False
    assert boundaries["system_economic_evidence_admissible"] is False
    assert boundaries["shadow_authorized"] is False
    assert boundaries["paper_authorized"] is False
    assert boundaries["testnet_authorized"] is False
    assert boundaries["live_authorized"] is False
    assert boundaries["orders_allowed"] is False
    assert boundaries["credentials_required"] is False
    assert boundaries["arming_allowed"] is False

    required = set(payload["required_binding_fields"])
    assert "canonical_decision_chain_digest" in required
    assert "backtest_runtime_parity_digest" in required
    assert "linear_diagnostics_refs_optional_support_only" in required

    bindings = payload["fleet_bindings"]
    assert {item["strategy_id"] for item in bindings} == {
        "trend_following",
        "bollinger_bands",
        "momentum_1h",
    }

    for item in bindings:
        missing = [field for field in required if not item.get(field)]
        assert missing == []
        assert item["binding_status"] == "CONTRACT_BOUND_READ_ONLY_NO_EVAL"
        assert item["economic_evaluation_status"] == "NOT_AUTHORIZED_IN_THIS_SLICE"
        assert item["linear_diagnostics_refs_optional_support_only"].startswith(
            "src/research/linear_evidence"
        )


def test_step29m_binding_contracts_do_not_create_authority_v0():
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert payload["binding_policy"]["no_economic_evaluation_in_this_slice"] is True
    assert payload["binding_policy"]["linear_diagnostics_support_only"] is True
    assert payload["binding_policy"]["no_strategy_logic_change"] is True
    assert payload["binding_policy"]["no_core_system_change"] is True
    assert payload["binding_policy"]["no_master_v2_change"] is True
    assert payload["binding_policy"]["no_double_play_change"] is True
    assert payload["binding_policy"]["no_risk_sizing_change"] is True
    assert payload["binding_policy"]["no_safety_runtime_change"] is True
    assert payload["binding_policy"]["no_runtime_rewire"] is True
    assert payload["binding_policy"]["raw_signal_evidence_not_promotion_admissible"] is True
