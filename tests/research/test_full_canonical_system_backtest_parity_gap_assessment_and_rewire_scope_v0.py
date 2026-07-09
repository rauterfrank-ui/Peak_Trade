import json
from pathlib import Path

SCOPE_PATH = Path(
    "docs/research/full_canonical_system_backtest_parity_gap_assessment_and_rewire_scope_v0.json"
)
MD_PATH = Path(
    "docs/research/FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_AND_REWIRE_SCOPE_V0.md"
)


def test_full_canonical_system_backtest_parity_gap_assessment_and_rewire_scope_v0():
    payload = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))

    assert (
        payload["schema_version"]
        == "full_canonical_system_backtest_parity_gap_assessment_and_rewire_scope_v0"
    )
    assert (
        payload["verdict"]
        == "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_SCOPE_BOUND_READ_ONLY"
    )
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"
    assert payload["futures_only"] is True
    assert payload["bitcoin_direction_allowed"] is False
    assert payload["spot_allowed"] is False
    assert payload["synthetic_spot_allowed"] is False
    assert payload["assessment_mode"] == "READ_ONLY_NO_RUNTIME_NO_ECONOMIC_CLAIM"

    goals = payload["goals"]
    assert goals["full_canonical_chain_wired_status"] == "ASSESSED"
    assert goals["backtest_runtime_decision_parity_status"] == "ASSESSED"
    assert goals["system_economic_evidence_admissibility_status"] == "ASSESSED"

    surfaces = payload["required_assessment_surfaces"]
    assert len(surfaces) == 14
    assert "bull_bear_state_switch_owner" in surfaces
    assert "backtest_offline_replay_runtime_decision_parity" in surfaces

    allowed = payload["allowed_scope"]
    assert "offline_parity_assessment" in allowed
    assert "gap_classification" in allowed
    assert "owner_mapping" in allowed
    assert "reuse_first_rewire_scope_proposal" in allowed

    disallowed = payload["disallowed_scope"]
    assert "runtime_rewire" in disallowed
    assert "live" in disallowed
    assert "orders" in disallowed
    assert "core_system_mutation" in disallowed
    assert "economic_pass_claim" in disallowed

    reuse_first = payload["reuse_first_order"]
    assert reuse_first[0] == "REUSE_AS_IS"
    assert reuse_first[-1] == "NEW_IMPLEMENTATION_JUSTIFIED"

    assert payload["system_economic_evidence_admissible"] is False
    assert payload["economic_evaluation_authorized"] is False
    assert payload["runtime_rewire_admissible"] is False
    assert payload["full_canonical_chain_wired"] is False
    assert payload["backtest_runtime_decision_parity_pass"] is False

    assert (
        payload["next_step"]
        == "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_AND_REWIRE_SCOPE"
    )


def test_full_canonical_system_backtest_parity_gap_assessment_and_rewire_scope_doc_v0():
    text = MD_PATH.read_text(encoding="utf-8")
    assert "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_SCOPE_BOUND_READ_ONLY" in text
    assert "does not execute assessment" in text.lower()
    assert "AUTHORITY_EFFECT=NONE" in text
    assert "RUNTIME_EFFECT=NONE" in text
    assert "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_AND_REWIRE_SCOPE" in text
    assert "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_V0.md" in text
    assert "STEP29M_EXECUTION_RESULT_FAIL_CLOSED_PRECONDITIONS_NOT_ADMISSIBLE_V0.md" in text
