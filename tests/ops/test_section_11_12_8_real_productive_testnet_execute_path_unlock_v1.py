"""Tests for §11.12.8 real productive Testnet execute-path unlock."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    MODE_PRODUCTIVE_REAL,
    MODE_STUBBED_ACCEPTANCE,
    SCOPED_OWNER_GO_AUTHORIZATION,
    SCOPED_OWNER_GO_SCOPE,
    SCOPED_OWNER_GO_TOKEN,
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
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.secretref_credential_v1 import (
    ActualStartSecretRefError,
    resolve_and_load_secretref_ephemeral_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.acceptance_gate_v1 import (
    run_pre_merge_unlock_acceptance_gate_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.bound_testnet_http_client_v1 import (
    BoundTestnetHttpClientError,
    construct_bound_okx_testnet_http_client_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.constants_v1 import (
    CAPABILITY_ID,
    FORBIDDEN_TRACE_TOKENS,
    PATH_IMPLEMENTATION_ONLY_REFUSAL_REMOVED,
    SECTION_11_13_STARTED,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.forensic_trace_v1 import (
    build_forensic_blocker_trace_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.unlock_orchestrator_v1 import (
    execute_unlocked_productive_path_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.vault_resolver_v1 import (
    build_acceptance_fixture_vault_backend_v1,
)

_DIGEST = "e" * 64


@pytest.fixture(autouse=True)
def _reset_registries() -> None:
    reset_owner_go_consumption_registry_v1()
    yield
    reset_owner_go_consumption_registry_v1()


def test_capability_identity() -> None:
    assert CAPABILITY_ID == (
        "CAPABILITY_11_SECTION_11_12_8_REAL_PRODUCTIVE_TESTNET_EXECUTE_PATH_UNLOCK_V1"
    )
    assert PATH_IMPLEMENTATION_ONLY_REFUSAL_REMOVED is True
    assert SECTION_11_13_STARTED is False


def test_mode_productive_real_requires_scoped_owner_auth(tmp_path: Path) -> None:
    with pytest.raises(ActualStartOwnerGoError, match="SCOPE_MISMATCH"):
        execute_productive_section_11_12_8_campaign_run_v1(
            work_dir=tmp_path / "bad-scope",
            mode=MODE_PRODUCTIVE_REAL,
            owner_go_token=SCOPED_OWNER_GO_TOKEN,
            owner_go_scope="WRONG_SCOPE",
            owner_go_authorization=SCOPED_OWNER_GO_AUTHORIZATION,
            confirm_token_digest=_DIGEST,
            vault_backend=build_acceptance_fixture_vault_backend_v1(),
            http_client_factory=lambda h: construct_bound_okx_testnet_http_client_v1(
                credential_handle=h
            ),
        )


def test_mode_productive_real_accepted_with_scoped_auth(tmp_path: Path) -> None:
    result = execute_unlocked_productive_path_v1(
        work_dir=tmp_path / "ok",
        confirm_token_digest=_DIGEST,
        allow_wire_send=False,
    )
    assert result.ok is True
    assert result.run.mode == MODE_PRODUCTIVE_REAL
    assert result.network_send_boundary_reached is True
    assert result.client_bound is True
    assert result.run.lifecycle.first_permitted_effect_stubbed is False
    assert result.run.network_effect == "NONE"
    assert result.run.order_effect == "NONE"


def test_real_secretref_resolver_reached() -> None:
    backend = build_acceptance_fixture_vault_backend_v1()
    handle = resolve_and_load_secretref_ephemeral_v1(
        allow_real_vault=True,
        vault_backend=backend,
    )
    assert handle.vault_resolved is True
    assert handle.to_dict()["plaintext_exposed"] is False
    assert handle.to_dict()["plaintext_persisted"] is False


def test_real_vault_without_backend_fails() -> None:
    with pytest.raises(ActualStartSecretRefError, match="REAL_VAULT_BACKEND_REQUIRED"):
        resolve_and_load_secretref_ephemeral_v1(allow_real_vault=True, vault_backend=None)


def test_live_host_hard_block_on_client(tmp_path: Path) -> None:
    _ = tmp_path
    backend = build_acceptance_fixture_vault_backend_v1()
    handle = resolve_and_load_secretref_ephemeral_v1(
        allow_real_vault=True,
        vault_backend=backend,
    )
    client = construct_bound_okx_testnet_http_client_v1(credential_handle=handle)
    with pytest.raises(BoundTestnetHttpClientError, match="LIVE_HOST_HARD_BLOCK|HOST_NOT_IN"):
        client.request(
            method="GET",
            url="https://www.okx.com/api/v5/account/balance",
            body={},
            headers={},
        )


def test_historical_refuse_helper_still_exists_but_not_on_real_path() -> None:
    with pytest.raises(ActualStartConsumerError, match="FORBIDDEN_IN_IMPLEMENTATION"):
        refuse_real_productive_campaign_in_implementation_go_v1()
    forensic = build_forensic_blocker_trace_v1(unlocked=True)
    assert forensic["ok"] is True
    assert forensic["residual_blockers"] == []


def test_stubbed_mode_still_works(tmp_path: Path) -> None:
    from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.hidden_confirm_v1 import (
        reset_confirm_consumption_registry_v1,
    )

    reset_confirm_consumption_registry_v1()
    result = execute_productive_section_11_12_8_campaign_run_v1(
        work_dir=tmp_path / "stub",
        mode=MODE_STUBBED_ACCEPTANCE,
        confirm_token_digest=_DIGEST,
        expected_confirm_token_digest=_DIGEST,
        consumption_id="stub-still-ok",
    )
    assert result.ok is True
    assert result.mode == MODE_STUBBED_ACCEPTANCE


def test_governance_acceptance_canonical_next_step() -> None:
    from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.governance_acceptance_v1 import (
        prove_governance_acceptance_v1,
    )
    from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.constants_v1 import (
        AUTHORIZATION_REQUIRED_AFTER_MERGE,
        CANONICAL_NEXT_STEP_AFTER_MERGE,
        NO_ADDITIONAL_IMPLEMENTATION_GO_REQUIRED_BEFORE_EXECUTE,
        REQUEST_MATCHES_CANONICAL_NEXT_STEP_FOR_EXECUTE_GO,
    )

    proof = prove_governance_acceptance_v1()
    assert proof["ok"] is True
    assert proof["GOVERNANCE_ACCEPTANCE"] == "PASS"
    assert (
        CANONICAL_NEXT_STEP_AFTER_MERGE
        == "SEPARATE_OWNER_GO_EXECUTE_BOUNDED_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_NOW"
    )
    assert REQUEST_MATCHES_CANONICAL_NEXT_STEP_FOR_EXECUTE_GO is True
    assert AUTHORIZATION_REQUIRED_AFTER_MERGE == "PRESENT_OWNER_GO_EXECUTE"
    assert NO_ADDITIONAL_IMPLEMENTATION_GO_REQUIRED_BEFORE_EXECUTE is True
    assert "WIRE_SEND_FORBIDDEN_IN_UNLOCK_IMPLEMENTATION_GO" not in Path(
        "scripts/ops/run_section_11_12_8_real_productive_testnet_execute_operator_entrypoint_v1.py"
    ).read_text(encoding="utf-8")


def test_pre_merge_acceptance_gate(tmp_path: Path) -> None:
    gate = run_pre_merge_unlock_acceptance_gate_v1(work_dir=tmp_path / "gate")
    assert gate["ok"] is True
    assert gate["PRE_MERGE_ACCEPTANCE_GATE"] == "PASS"
    assert gate["MODE_PRODUCTIVE_REAL_ACCEPTED"] is True
    assert gate["REAL_TESTNET_HTTP_CLIENT_BOUND"] is True
    assert gate["NETWORK_SEND_BOUNDARY_REACHED"] is True
    assert gate["PRODUCTIVE_TESTNET_CAMPAIGN_STARTED"] is False
    assert gate["NETWORK_EFFECT"] == "NONE"
    assert gate["ORDER_EFFECT"] == "NONE"
    assert gate["SECTION_11_13_STARTED"] is False
    assert gate["CANONICAL_NEXT_STEP_AFTER_MERGE"] == (
        "SEPARATE_OWNER_GO_EXECUTE_BOUNDED_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_NOW"
    )
    assert gate["AUTHORIZATION_REQUIRED"] == "PRESENT_OWNER_GO_EXECUTE"
    assert gate["GOVERNANCE_ACCEPTANCE"] == "PASS"
    # Forensic inventory may name closed historical tokens; runtime payload must not.
    blob = str(gate["result"]) + str(gate["runtime_audit"])
    for token in FORBIDDEN_TRACE_TOKENS:
        assert token not in blob


def test_operator_entrypoint_pre_merge() -> None:
    import scripts.ops.run_section_11_12_8_real_productive_testnet_execute_operator_entrypoint_v1 as ep

    rc = ep.main(["--pre-merge-acceptance"])
    assert rc == 0


def test_owner_go_one_time_consume() -> None:
    consume_actual_start_owner_go_v1(
        owner_go_token=SCOPED_OWNER_GO_TOKEN,
        owner_go_scope=SCOPED_OWNER_GO_SCOPE,
        owner_go_authorization=SCOPED_OWNER_GO_AUTHORIZATION,
        consumption_id="once-1",
    )
    with pytest.raises(ActualStartOwnerGoError, match="REPLAY"):
        consume_actual_start_owner_go_v1(
            owner_go_token=SCOPED_OWNER_GO_TOKEN,
            owner_go_scope=SCOPED_OWNER_GO_SCOPE,
            owner_go_authorization=SCOPED_OWNER_GO_AUTHORIZATION,
            consumption_id="once-1",
        )


def test_missing_bindings_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ActualStartConsumerError, match="SECRETREF_RESOLVER_REQUIRED"):
        execute_productive_section_11_12_8_campaign_run_v1(
            work_dir=tmp_path / "no-vault",
            mode=MODE_PRODUCTIVE_REAL,
            confirm_token_digest=_DIGEST,
            vault_backend=None,
            http_client_factory=lambda h: construct_bound_okx_testnet_http_client_v1(
                credential_handle=h
            ),
        )
    with pytest.raises(ActualStartConsumerError, match="HTTP_CLIENT_REQUIRED"):
        execute_productive_section_11_12_8_campaign_run_v1(
            work_dir=tmp_path / "no-client",
            mode=MODE_PRODUCTIVE_REAL,
            confirm_token_digest=_DIGEST,
            vault_backend=build_acceptance_fixture_vault_backend_v1(),
            http_client=None,
            http_client_factory=None,
        )
