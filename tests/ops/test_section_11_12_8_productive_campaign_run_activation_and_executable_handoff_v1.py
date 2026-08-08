"""Tests for §11.12.8 activation + executable handoff (dry activation proof)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.activation_executor_v1 import (
    Section11128ActivationExecutorError,
    execute_end_to_end_dry_activation_proof_v1,
    prove_section_11_12_8_activation_and_executable_handoff_v1,
    refuse_productive_campaign_start_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.constants_v1 import (
    CAMPAIGN_ARMED_DEFAULT,
    CAMPAIGN_ENABLED_DEFAULT,
    COMPLETE_BLOCKER_IDS,
    DEPRECATED_NON_EXTENDABLE,
    LIVE_ORDER_EFFECT,
    NETWORK_EFFECT,
    NEW_WRAPPER_LAYER_CREATED,
    ORDER_EFFECT,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    SCOPED_OWNER_GO_SCOPE,
    SCOPED_OWNER_GO_TOKEN,
    SECTION_11_13_STARTED,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.durable_campaign_state_v1 import (
    default_campaign_durable_state_v1,
    load_campaign_durable_state_v1,
    transition_enabled_armed_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.evidence_v1 import (
    verify_evidence_seal_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.owner_go_consumer_v1 import (
    Section11128OwnerGoConsumerError,
    consume_scoped_owner_go_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.secretref_account_binding_v1 import (
    Section11128SecretRefAccountError,
    resolve_secretref_structurally_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.verifier_v1 import (
    verify_section_11_12_8_activation_and_executable_handoff_v1,
)

_SHA = "a" * 40
_CFG = "cfg-" + ("b" * 64)
_DIGEST = "c" * 64


def test_defaults_fail_closed() -> None:
    state = default_campaign_durable_state_v1()
    assert CAMPAIGN_ENABLED_DEFAULT is False
    assert CAMPAIGN_ARMED_DEFAULT is False
    assert state.campaign_enabled is False
    assert state.campaign_armed is False
    assert state.authorization_state == "UNAUTHORIZED"
    assert DEPRECATED_NON_EXTENDABLE is False
    assert NEW_WRAPPER_LAYER_CREATED is False
    assert PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False


def test_scoped_owner_go_consumer(tmp_path: Path) -> None:
    _ = tmp_path
    consumed = consume_scoped_owner_go_v1(
        owner_go_token=SCOPED_OWNER_GO_TOKEN,
        owner_go_scope=SCOPED_OWNER_GO_SCOPE,
    )
    assert consumed.consumed is True
    assert consumed.productive_campaign_authorized is False
    assert consumed.dry_activation_proof_authorized is True
    with pytest.raises(Section11128OwnerGoConsumerError, match="TOKEN_MISMATCH"):
        consume_scoped_owner_go_v1(
            owner_go_token="WRONG",
            owner_go_scope=SCOPED_OWNER_GO_SCOPE,
        )
    with pytest.raises(Section11128OwnerGoConsumerError, match="NOT_AUTHORIZED"):
        consume_scoped_owner_go_v1(
            owner_go_token=SCOPED_OWNER_GO_TOKEN,
            owner_go_scope=SCOPED_OWNER_GO_SCOPE,
            allow_productive_campaign_start=True,
        )


def test_durable_enabled_armed_restart_readable(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    written = transition_enabled_armed_v1(
        state_dir=state_dir,
        campaign_enabled=True,
        campaign_armed=True,
        authorization_state="AUTHORIZED",
        owner_go_consumed=True,
    )
    reloaded = load_campaign_durable_state_v1(state_dir)
    assert reloaded == written
    assert reloaded.campaign_enabled is True
    assert reloaded.campaign_armed is True
    assert reloaded.campaign_started is False


def test_secretref_rejects_plaintext() -> None:
    with pytest.raises(Section11128SecretRefAccountError, match="PLAINTEXT"):
        resolve_secretref_structurally_v1(plaintext_secret="sk-demo")
    with pytest.raises(Section11128SecretRefAccountError, match="SECRET_REFERENCE_ONLY"):
        resolve_secretref_structurally_v1(secret_reference="plaintext:demo")
    resolved = resolve_secretref_structurally_v1()
    assert resolved.resolved_structurally is True
    assert resolved.plaintext_exposed is False


def test_end_to_end_dry_activation_proof(tmp_path: Path) -> None:
    proof = execute_end_to_end_dry_activation_proof_v1(
        work_dir=tmp_path / "dry",
        repository_sha=_SHA,
        config_digest=_CFG,
        confirm_token_digest=_DIGEST,
        expected_confirm_token_digest=_DIGEST,
    )
    assert proof.ok is True
    assert proof.owner_go.consumed is True
    assert proof.authorization_before == "UNAUTHORIZED"
    assert proof.authorization_after == "AUTHORIZED"
    assert proof.durable_state.campaign_enabled is True
    assert proof.durable_state.campaign_armed is True
    assert proof.restart_readable is True
    assert proof.secretref.plaintext_exposed is False
    assert proof.account_binding.bound is True
    assert proof.handoff.handoff_reached is True
    assert proof.handoff.execution_authorized is False
    assert proof.network_boundary.boundary_reached is True
    assert proof.network_boundary.network_session_started is False
    assert proof.risk_gate_in_chain is True
    assert proof.kill_switch_in_chain is True
    assert proof.emergency_control_in_chain is True
    assert proof.testnet_only_enforcement is True
    assert proof.live_path_hard_block is True
    assert proof.hidden_confirm_digest_bound is True
    assert proof.evidence_seal.sealed is True
    assert proof.completion.completed is True
    assert proof.abort.aborted is True
    assert set(proof.complete_blocker_set_closed) == set(COMPLETE_BLOCKER_IDS)
    assert proof.productive_testnet_campaign_started is False
    assert proof.network_effect == NETWORK_EFFECT == "NONE"
    assert proof.order_effect == ORDER_EFFECT == "NONE"
    assert proof.live_order_effect == LIVE_ORDER_EFFECT == "NONE"
    assert proof.section_11_13_started is False is SECTION_11_13_STARTED
    evidence_dir = Path(proof.evidence_seal.evidence_dir)
    assert verify_evidence_seal_v1(evidence_dir) == 0


def test_productive_start_refused() -> None:
    with pytest.raises(
        Section11128ActivationExecutorError,
        match="PRODUCTIVE_TESTNET_CAMPAIGN_START_FORBIDDEN",
    ):
        refuse_productive_campaign_start_v1()


def test_prove_and_verifier(tmp_path: Path) -> None:
    proof = prove_section_11_12_8_activation_and_executable_handoff_v1(work_dir=tmp_path / "prove")
    assert proof["ok"] is True
    verification = verify_section_11_12_8_activation_and_executable_handoff_v1(
        work_dir=tmp_path / "verify"
    )
    assert verification["ok"] is True
    assert verification["claims"]["END_TO_END_DRY_ACTIVATION_PROOF"] is True
    assert verification["claims"]["PRODUCTIVE_TESTNET_CAMPAIGN_STARTED"] is False
    assert set(verification["claims"]["COMPLETE_BLOCKER_SET_CLOSED"]) == set(COMPLETE_BLOCKER_IDS)
