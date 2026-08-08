"""Tests for §11.12.8 ACTUAL productive Testnet campaign RUN START."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_path_v1.constants_v1 import (
    DEPRECATED_AS_NON_CANONICAL_WRAPPER as PATH_DEPRECATED,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_execution_v1.constants_v1 import (
    DEPRECATED_AS_NON_CANONICAL_WRAPPER as EXEC_DEPRECATED,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_v1.constants_v1 import (
    DEPRECATED_AS_NON_CANONICAL_WRAPPER as RUN_DEPRECATED,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1.constants_v1 import (
    DEPRECATED_AS_NON_CANONICAL_WRAPPER as RUN_ACT_DEPRECATED,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.acceptance_gate_v1 import (
    run_pre_merge_acceptance_gate_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.account_endpoint_binding_v1 import (
    ActualStartBindingError,
    assert_endpoint_allowlisted_v1,
    bind_and_verify_testnet_account_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.blocker_matrix_v1 import (
    build_b01_b24_closure_matrix_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.call_chain_proof_v1 import (
    build_static_productive_call_chain_proof_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.closeout_v1 import (
    evaluate_section_11_12_8_closeout_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    BLOCKER_IDS,
    CAPABILITY_ID,
    LIVE_AUTHORIZED,
    LIVE_FORBIDDEN_HOSTS,
    NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    SCOPED_OWNER_GO_AUTHORIZATION,
    SCOPED_OWNER_GO_SCOPE,
    SCOPED_OWNER_GO_TOKEN,
    SECTION_11_13_STARTED,
    STATE_ARMED,
    STATE_AUTHORIZED,
    STATE_ENABLED,
    STATE_GO_CONSUMED,
    STATE_IDLE,
    TESTNET_PRIVATE_ENDPOINTS,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.durable_state_v1 import (
    ActualStartDurableStateError,
    default_actual_start_durable_state_v1,
    load_actual_start_durable_state_v1,
    transition_actual_start_state_v1,
    validate_actual_start_durable_state_v1,
    write_actual_start_durable_state_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.evidence_v1 import (
    seal_evidence_dir_v1,
    verify_evidence_seal_v1,
    write_productive_execution_evidence_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.hidden_confirm_v1 import (
    ActualStartConfirmError,
    latch_and_consume_confirm_digest_v1,
    reset_confirm_consumption_registry_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.network_session_v1 import (
    ActualStartNetworkSessionError,
    reach_network_session_entry_boundary_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.owner_go_consumer_v1 import (
    ActualStartOwnerGoError,
    consume_actual_start_owner_go_v1,
    reset_owner_go_consumption_registry_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.productive_consumer_v1 import (
    ActualStartConsumerError,
    execute_productive_section_11_12_8_campaign_run_v1,
    refuse_real_productive_campaign_in_implementation_go_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.productive_execution_port_v1 import (
    ActualStartPortError,
    construct_productive_testnet_execution_port_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.safety_preflight_v1 import (
    ActualStartSafetyError,
    evaluate_safety_preflight_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.secretref_credential_v1 import (
    ActualStartSecretRefError,
    assert_no_plaintext_in_payload_v1,
    resolve_and_load_secretref_ephemeral_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.testnet_authorization_v1 import (
    ActualStartTestnetAuthError,
    authorize_testnet_runtime_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.testnet_transport_v1 import (
    ActualStartTransportError,
    ProductiveTestnetTransportV1,
    build_stubbed_testnet_transport_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.activation_executor_v1 import (
    Section11128ActivationExecutorError,
    refuse_productive_campaign_start_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.run_consumer_v1 import (
    Section11128RunConsumerError,
    execute_section_11_12_8_productive_campaign_run_v1,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.terminal_consumer_v1 import (
    Section11128TerminalConsumerError,
    run_section_11_12_8_terminal_consumer_v1,
)

_DIGEST = "c" * 64


@pytest.fixture(autouse=True)
def _reset_registries() -> None:
    reset_owner_go_consumption_registry_v1()
    reset_confirm_consumption_registry_v1()


def test_capability_identity() -> None:
    assert CAPABILITY_ID.endswith("ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START_V1")
    assert LIVE_AUTHORIZED is False
    assert PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False
    assert SECTION_11_13_STARTED is False
    assert set(BLOCKER_IDS) == {f"B{i:02d}" for i in range(1, 25)}


def test_owner_go_accept_and_rejects() -> None:
    ok = consume_actual_start_owner_go_v1(
        owner_go_token=SCOPED_OWNER_GO_TOKEN,
        owner_go_scope=SCOPED_OWNER_GO_SCOPE,
        owner_go_authorization=SCOPED_OWNER_GO_AUTHORIZATION,
        consumption_id="cid-1",
    )
    assert ok.consumed is True
    assert ok.one_time_consume is True
    assert ok.productive_campaign_authorized is True
    assert ok.live_authorized is False
    with pytest.raises(ActualStartOwnerGoError, match="TOKEN_MISMATCH"):
        consume_actual_start_owner_go_v1(
            owner_go_token="WRONG",
            owner_go_scope=SCOPED_OWNER_GO_SCOPE,
            owner_go_authorization=SCOPED_OWNER_GO_AUTHORIZATION,
            consumption_id="cid-2",
        )
    with pytest.raises(ActualStartOwnerGoError, match="SCOPE_MISMATCH"):
        consume_actual_start_owner_go_v1(
            owner_go_token=SCOPED_OWNER_GO_TOKEN,
            owner_go_scope="WRONG",
            owner_go_authorization=SCOPED_OWNER_GO_AUTHORIZATION,
            consumption_id="cid-3",
        )
    with pytest.raises(ActualStartOwnerGoError, match="AUTHORIZATION_MISMATCH"):
        consume_actual_start_owner_go_v1(
            owner_go_token=SCOPED_OWNER_GO_TOKEN,
            owner_go_scope=SCOPED_OWNER_GO_SCOPE,
            owner_go_authorization="WRONG",
            consumption_id="cid-4",
        )
    with pytest.raises(ActualStartOwnerGoError, match="REPLAY"):
        consume_actual_start_owner_go_v1(
            owner_go_token=SCOPED_OWNER_GO_TOKEN,
            owner_go_scope=SCOPED_OWNER_GO_SCOPE,
            owner_go_authorization=SCOPED_OWNER_GO_AUTHORIZATION,
            consumption_id="cid-1",
        )


def test_activation_state_machine_and_restart(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    state = default_actual_start_durable_state_v1()
    assert state.stage == STATE_IDLE
    write_actual_start_durable_state_v1(state_dir, state)
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_GO_CONSUMED,
        owner_go_consumed=True,
    )
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_AUTHORIZED,
        authorization_state="AUTHORIZED",
        testnet_authorized_runtime=True,
    )
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_ENABLED,
        campaign_enabled=True,
    )
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_ARMED,
        campaign_armed=True,
    )
    reloaded = load_actual_start_durable_state_v1(state_dir)
    assert reloaded.stage == STATE_ARMED
    assert reloaded.campaign_enabled is True
    # campaign_started without auth must fail validation
    bad = reloaded.to_dict()
    bad["campaign_started"] = True
    bad["testnet_authorized_runtime"] = False
    assert "CAMPAIGN_STARTED_REQUIRES_RUNTIME_TESTNET_AUTH_AND_OWNER_GO" in (
        validate_actual_start_durable_state_v1(bad)
    )


def test_testnet_authorization_runtime() -> None:
    auth = authorize_testnet_runtime_v1(owner_go_consumed=True, productive_campaign_authorized=True)
    assert auth.testnet_authorized_runtime is True
    assert auth.testnet_authorized_persisted is False
    assert auth.live_authorized is False
    with pytest.raises(ActualStartTestnetAuthError, match="LIVE_PATH"):
        authorize_testnet_runtime_v1(
            owner_go_consumed=True,
            productive_campaign_authorized=True,
            runtime_mode="LIVE",
        )
    with pytest.raises(ActualStartTestnetAuthError, match="LIVE_PATH"):
        authorize_testnet_runtime_v1(
            owner_go_consumed=True,
            productive_campaign_authorized=True,
            live_endpoint_configured=True,
        )


def test_secretref_and_plaintext_leak_negatives() -> None:
    handle = resolve_and_load_secretref_ephemeral_v1(
        stub_material="stub-testnet-material-not-a-secret-pattern"
    )
    assert handle.bound is True
    assert "plaintext" not in handle.to_dict()
    with pytest.raises(ActualStartSecretRefError, match="SECRET_REFERENCE_ONLY"):
        resolve_and_load_secretref_ephemeral_v1(
            secret_reference="plaintext:abc",
            stub_material="x",
        )
    with pytest.raises(ActualStartSecretRefError, match="PLAINTEXT_LEAK"):
        assert_no_plaintext_in_payload_v1({"api_secret": "x"})


def test_hidden_confirm_one_time_replay() -> None:
    latch = latch_and_consume_confirm_digest_v1(
        confirm_token_digest=_DIGEST, expected_confirm_token_digest=_DIGEST
    )
    assert latch.consumed is True
    with pytest.raises(ActualStartConfirmError, match="REPLAY"):
        latch_and_consume_confirm_digest_v1(
            confirm_token_digest=_DIGEST, expected_confirm_token_digest=_DIGEST
        )
    with pytest.raises(ActualStartConfirmError):
        latch_and_consume_confirm_digest_v1(
            confirm_token_digest=_DIGEST,
            expected_confirm_token_digest=_DIGEST,
            argv=["--confirm-token", "secret"],
        )


def test_safety_preflight_fail_closed() -> None:
    ok = evaluate_safety_preflight_v1()
    assert ok.risk_gate_allows is True
    assert ok.kill_switch_operational is True
    assert ok.emergency_control_operational is True
    with pytest.raises(ActualStartSafetyError, match="KILL_SWITCH"):
        evaluate_safety_preflight_v1(force_killed=True)


def test_account_and_endpoint_binding() -> None:
    handle = resolve_and_load_secretref_ephemeral_v1(
        stub_material="stub-testnet-material-not-a-secret-pattern"
    )
    binding = bind_and_verify_testnet_account_v1(credential_handle=handle)
    assert binding.account_verified is True
    assert binding.live_hosts_blocked is True
    assert_endpoint_allowlisted_v1(endpoint=TESTNET_PRIVATE_ENDPOINTS[0])
    with pytest.raises(ActualStartBindingError, match="LIVE_ACCOUNT"):
        bind_and_verify_testnet_account_v1(credential_handle=handle, live_account=True)
    with pytest.raises(ActualStartBindingError, match="LIVE_HOST"):
        bind_and_verify_testnet_account_v1(
            credential_handle=handle, rest_base="https://www.okx.com"
        )
    assert "www.okx.com" in LIVE_FORBIDDEN_HOSTS


def test_network_session_go_ephemeral_only() -> None:
    inspect = reach_network_session_entry_boundary_v1(
        preflight_pass=True,
        testnet_authorized_runtime=True,
        campaign_enabled=True,
        campaign_armed=True,
        network_session_go=False,
    )
    assert inspect.boundary_reached is True
    assert inspect.network_session_started is False
    started = reach_network_session_entry_boundary_v1(
        preflight_pass=True,
        testnet_authorized_runtime=True,
        campaign_enabled=True,
        campaign_armed=True,
        network_session_go=True,
    )
    assert started.network_session_started is True
    assert started.next_operation == NEXT_OPERATION_AFTER_STUBBED_BOUNDARY
    with pytest.raises(ActualStartNetworkSessionError):
        reach_network_session_entry_boundary_v1(
            preflight_pass=True,
            testnet_authorized_runtime=True,
            campaign_enabled=True,
            campaign_armed=True,
            network_session_go=True,
            environ={"PEAK_TRADE_NETWORK_SESSION_GO": "true"},
        )


def test_productive_port_and_transport() -> None:
    transport = build_stubbed_testnet_transport_v1()
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    effect = port.submit_order_v1(
        client_order_id="c1",
        instrument="BTC-USDT-SWAP",
        order_type="LIMIT",
        side="buy",
        quantity="1",
    )
    assert effect["stubbed"] is True
    assert effect["live_order_effect"] == "NONE"
    with pytest.raises(ActualStartPortError, match="REQUIRES_AUTHORIZATION"):
        construct_productive_testnet_execution_port_v1(authorized=False)
    real = ProductiveTestnetTransportV1(allow_real_network=False)
    with pytest.raises(ActualStartTransportError, match="REAL_NETWORK_FORBIDDEN"):
        real.request(method="GET", endpoint="/api/v5/account/balance")


def test_campaign_lifecycle_complete_and_abort(tmp_path: Path) -> None:
    completed = execute_productive_section_11_12_8_campaign_run_v1(
        work_dir=tmp_path / "c",
        confirm_token_digest=_DIGEST,
        expected_confirm_token_digest=_DIGEST,
        consumption_id="life-complete",
    )
    assert completed.ok is True
    assert completed.lifecycle.completed is True
    abort_digest = "d" * 64
    aborted = execute_productive_section_11_12_8_campaign_run_v1(
        work_dir=tmp_path / "a",
        confirm_token_digest=abort_digest,
        expected_confirm_token_digest=abort_digest,
        consumption_id="life-abort",
        abort=True,
    )
    assert aborted.lifecycle.aborted is True


def test_execution_evidence_and_seal(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "ev"
    path = write_productive_execution_evidence_v1(evidence_dir, payload={"k": "v"})
    assert path.is_file()
    seal = seal_evidence_dir_v1(evidence_dir)
    assert seal.sealed is True
    assert verify_evidence_seal_v1(evidence_dir) == 0


def test_closeout_does_not_flip_proven_on_stub() -> None:
    closeout = evaluate_section_11_12_8_closeout_v1(stubbed_acceptance=True)
    assert closeout.section_11_12_8_closed is False
    assert closeout.testnet_order_lifecycle_proven is False
    assert closeout.section_11_13_started is False


def test_legacy_hard_refuse_preserved() -> None:
    with pytest.raises(Section11128ActivationExecutorError, match="FORBIDDEN"):
        refuse_productive_campaign_start_v1()
    with pytest.raises(Section11128RunConsumerError, match="FORBIDDEN"):
        execute_section_11_12_8_productive_campaign_run_v1(owner_go=True)
    with pytest.raises(Section11128TerminalConsumerError, match="FORBIDDEN"):
        run_section_11_12_8_terminal_consumer_v1(owner_go=True)
    with pytest.raises(ActualStartConsumerError, match="FORBIDDEN_IN_IMPLEMENTATION"):
        refuse_real_productive_campaign_in_implementation_go_v1()


def test_deprecated_wrappers_not_extended() -> None:
    assert PATH_DEPRECATED is True
    assert EXEC_DEPRECATED is True
    assert RUN_DEPRECATED is True
    assert RUN_ACT_DEPRECATED is True


def test_static_call_chain_proof() -> None:
    proof = build_static_productive_call_chain_proof_v1()
    assert proof["ok"] is True
    assert all(v.startswith("PRESENT_AND_PRODUCTIVE") for v in proof["classifications"].values())


def test_b01_b24_closure_matrix() -> None:
    matrix = build_b01_b24_closure_matrix_v1()
    assert matrix["ok"] is True
    assert matrix["ALL_B01_B24_CLOSED"] is True
    assert matrix["RESIDUAL_BLOCKER_COUNT"] == 0


def test_pre_merge_acceptance_gate(tmp_path: Path) -> None:
    gate = run_pre_merge_acceptance_gate_v1(work_dir=tmp_path / "gate")
    assert gate["ok"] is True
    assert gate["PRE_MERGE_ACCEPTANCE_GATE"] == "PASS"
    assert gate["ALL_B01_B24_CLOSED"] is True
    assert gate["STATIC_PRODUCTIVE_CALL_CHAIN"] == "PASS"
    assert gate["NEXT_OPERATION_AFTER_STUBBED_BOUNDARY"] == (NEXT_OPERATION_AFTER_STUBBED_BOUNDARY)
    assert gate["REMAINING_ARCHITECTURAL_BLOCKERS"] == 0
    assert gate["PRODUCTIVE_TESTNET_CAMPAIGN_STARTED"] is False
    assert gate["NETWORK_EFFECT"] == "NONE"
    assert gate["ORDER_EFFECT"] == "NONE"
    assert gate["LIVE_ORDER_EFFECT"] == "NONE"
    assert gate["SECTION_11_13_STARTED"] is False


def test_operator_entrypoint_stubbed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = tmp_path
    import scripts.ops.run_section_11_12_8_actual_productive_testnet_campaign_run_start_operator_entrypoint_v1 as ep

    monkeypatch.setattr(ep, "main", ep.main)
    rc = ep.main([])
    assert rc == 0


def test_live_mode_rejects_in_consumer(tmp_path: Path) -> None:
    with pytest.raises(ActualStartTestnetAuthError, match="LIVE_PATH"):
        execute_productive_section_11_12_8_campaign_run_v1(
            work_dir=tmp_path / "live",
            confirm_token_digest=_DIGEST,
            expected_confirm_token_digest=_DIGEST,
            consumption_id="live-rej",
            runtime_mode="LIVE",
        )
