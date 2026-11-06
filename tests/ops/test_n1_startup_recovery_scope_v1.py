"""Runtime observations and sample contract proofs have different evidence scope."""

from src.ops.n1_whole_system_hard_facts_integration_wp_v1.unified_recovery_orchestration_v1 import (
    execute_unified_recovery_orchestration_v1,
)
from tests.ops._host_private_rest_fixture_v1 import host_private_rest_fixture_v1


def test_contract_examples_do_not_claim_runtime_financial_recovery(tmp_path, monkeypatch):
    state = tmp_path / "kill.json"
    state.write_text('{"state":"ACTIVE"}')
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(state))
    result = execute_unified_recovery_orchestration_v1(
        public_store_root=tmp_path / "public",
        private_store_root=tmp_path / "private",
        public_rest_fetch=lambda *_: {"code": "0", "data": []},
        private_rest_fetch=host_private_rest_fixture_v1,
        kill_switch_state_path=str(state),
    )
    assert result.ok
    assert not result.runtime_owner_recovery_complete
    assert result.evidence_scope == "PUBLIC_PRIVATE_OBSERVATION_RECOVERY_AND_CONTRACT_CHECKS"
    assert len(result.steps_completed) == 4
    assert "runtime_eligibility" in result.pending_runtime_steps
    assert len(result.contract_checks) == 6
    assert "order_lifecycle_reconstruction" not in result.steps_completed
    assert "reservation_reconstruction" not in result.steps_completed
    assert "treasury_account_truth_reconstruction" not in result.steps_completed
    assert "runtime_eligibility" not in result.steps_completed
