"""DW exchange reconciliation wiring on one-shot join host (offline/injected only)."""

from __future__ import annotations

import json
import socket
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_dw_exchange_reconciliation_wiring_v1 import (
    DISPOSITION_FAIL_CLOSED,
    DISPOSITION_PASS,
    DISPOSITION_SKIPPED,
    RECONCILIATION_FAILED,
    DwExchangeReconciliationWiringConfigV1,
    DwExchangeReconciliationWiringModeV1,
    _safe_reconciliation_error_message_v1,
    run_dw_exchange_reconciliation_wiring_after_post_submit_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    OkxReadOnlyReconciliationProviderError,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
    FullCoreOrchestratedLifecycleReconciliationError,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    FullCorePostSubmitLifecycleReconciliationJoinError,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_OPEN,
    OUTCOME_HALTED_UNRESOLVED,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    join_full_core_post_result_to_lifecycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    POST_OWNER_GO as JOIN_POST_GO,
    _FakeKeychainBackend,
    _TimeoutOpener,
    _persist_post_go,
)
from tests.ops._pilot_guard_enter_post_test_helpers_v1 import (
    bind_authorized_exact_object_flatten_envelope_for_tests_v1,
)
from tests.ops.test_full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    FixtureBackedOkxReadOnlyTransport,
)
from tests.ops.test_full_core_exchange_reconciliation_v1 import CL, INST, _order_row
from tests.ops.test_full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    _ack_post_result,
    _join_from_post,
)


def _origin_main() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=True,
    )
    return str(proc.stdout or "").strip()


def _envelope() -> Any:
    return bind_authorized_exact_object_flatten_envelope_for_tests_v1(clordid=CL)


def _binding_for_envelope(envelope: Any) -> FullCoreAuthorizationBindingV1:
    return FullCoreAuthorizationBindingV1(
        owner_go="OWNER_GO_CURRENT_FULL_CORE_PRE_POST_CAPITAL_GUARD_JOIN_V1",
        origin_main_sha="abc123",
        account_scope="acct-shadow-1",
        environment="SHADOW",
        execution_mode="OFFLINE_STUB",
        canonical_decision_id="dec-1",
        instrument_id=INST,
        native_id=INST,
        selected_direction="ENTER_LONG",
        order_side="buy",
        final_quantity="10",
        order_type="limit",
        order_price="1.0",
        venue_plan_digest="vp-digest",
        envelope_digest=str(envelope.envelope_digest),
        guard_config_digest="gc-digest",
        session_id="sess-recon-1",
        clordid=str(envelope.client_order_id),
    )


def _wiring_config(
    envelope: Any,
    *,
    transport: FixtureBackedOkxReadOnlyTransport,
    private_get_go: str = "GRANTED_SCOPED_READ_ONLY",
) -> DwExchangeReconciliationWiringConfigV1:
    return DwExchangeReconciliationWiringConfigV1(
        binding=_binding_for_envelope(envelope),
        decision_outcome="ENTER",
        venue_plan_identity="vp-wiring-1",
        envelope_identity=str(envelope.envelope_id),
        submit_attempt_id="submit-wiring-1",
        local_durable_state_version="v1",
        pretrade_decision_id="pretrade-wiring-1",
        origin_main_sha=_origin_main(),
        read_only_get_transport=transport,
        private_get_go=private_get_go,
    )


def _order_row_for_cl(*, state: str = "live") -> dict[str, Any]:
    row = _order_row(state=state)
    row["clOrdId"] = CL
    row["instId"] = INST
    row["ordId"] = "ord-wiring-1"
    return row


class _AckOpener:
    class _Resp:
        status = 200
        url = "https://eea.okx.com/api/v5/trade/order"

        def __init__(self, body: bytes) -> None:
            self._body = body

        def read(self) -> bytes:
            return self._body

        def __enter__(self) -> _AckOpener._Resp:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    def __init__(self, clordid: str) -> None:
        payload = {
            "code": "0",
            "data": [{"clOrdId": clordid, "ordId": "ord-wiring-1", "sCode": "0"}],
        }
        self._body = json.dumps(payload).encode("utf-8")

    def open(self, _req: Any, timeout: float = 0) -> _Resp:
        del timeout
        return self._Resp(self._body)


@pytest.fixture(autouse=True)
def _forbid_real_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("NETWORK_FORBIDDEN")

    monkeypatch.setattr(socket, "create_connection", _boom)
    monkeypatch.setattr(socket.socket, "connect", _boom)


def test_a_default_disabled_preserves_join_and_skips_wiring(tmp_path: Path) -> None:
    _persist_post_go(tmp_path)
    baseline = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=_envelope(),
        post_owner_go=JOIN_POST_GO,
        store_root=tmp_path,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=_TimeoutOpener,
    )
    assert baseline.unknown_outcome is True
    assert baseline.dw_exchange_reconciliation_wiring_mode == "DISABLED"
    assert baseline.dw_exchange_reconciliation_invoked is False
    assert baseline.dw_exchange_reconciliation_disposition == DISPOSITION_SKIPPED


def test_b_disabled_does_not_call_orchestrator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock = MagicMock()
    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1."
        "current_productive_dw_exchange_reconciliation_wiring_v1."
        "orchestrate_post_submit_lifecycle_reconciliation_v1",
        mock,
    )
    _persist_post_go(tmp_path)
    attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=_envelope(),
        post_owner_go=JOIN_POST_GO,
        store_root=tmp_path,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=_TimeoutOpener,
    )
    mock.assert_not_called()


def test_c_offline_injected_unknown_timeout_reconciles_open(tmp_path: Path) -> None:
    envelope = _envelope()
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_for_cl()]})
    transport = FixtureBackedOkxReadOnlyTransport(fixture)
    config = _wiring_config(envelope, transport=transport)
    _persist_post_go(tmp_path)
    join = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=JOIN_POST_GO,
        store_root=tmp_path,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=_TimeoutOpener,
        dw_exchange_reconciliation_wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        dw_exchange_reconciliation_wiring=config,
    )
    assert join.unknown_outcome is True
    assert join.dw_exchange_reconciliation_invoked is True
    assert join.dw_exchange_reconciliation_disposition == DISPOSITION_PASS
    assert join.dw_exchange_reconciliation_outcome == OUTCOME_CONFIRMED_OPEN
    assert join.dw_exchange_reconciliation_ghv_forward_join == "PASS"


def test_d_offline_injected_ack_post_reconciles_open(tmp_path: Path) -> None:
    envelope = _envelope()
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_for_cl()]})
    transport = FixtureBackedOkxReadOnlyTransport(fixture)
    config = _wiring_config(envelope, transport=transport)
    _persist_post_go(tmp_path)
    join = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=JOIN_POST_GO,
        store_root=tmp_path,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=lambda: _AckOpener(CL),
        dw_exchange_reconciliation_wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        dw_exchange_reconciliation_wiring=config,
    )
    assert join.unknown_outcome is False
    assert join.dw_exchange_reconciliation_disposition == DISPOSITION_PASS
    assert join.dw_exchange_reconciliation_outcome == OUTCOME_CONFIRMED_OPEN


def test_e_orchestrator_failure_does_not_mutate_send_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(**_kwargs: object) -> None:
        raise FullCoreOrchestratedLifecycleReconciliationError("ORCHESTRATOR_FORCED_FAIL")

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1."
        "current_productive_dw_exchange_reconciliation_wiring_v1."
        "orchestrate_post_submit_lifecycle_reconciliation_v1",
        _boom,
    )
    envelope = _envelope()
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_for_cl()]})
    config = _wiring_config(envelope, transport=FixtureBackedOkxReadOnlyTransport(fixture))
    _persist_post_go(tmp_path)
    join = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=JOIN_POST_GO,
        store_root=tmp_path,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=_TimeoutOpener,
        dw_exchange_reconciliation_wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        dw_exchange_reconciliation_wiring=config,
    )
    assert join.unknown_outcome is True
    assert join.durable_consumed is True
    assert join.outcome
    assert join.dw_exchange_reconciliation_disposition == DISPOSITION_FAIL_CLOSED
    assert join.dw_exchange_reconciliation_error == (
        "RECONCILIATION_FAILED:FULL_CORE_ORCHESTRATED_LIFECYCLE_RECON"
    )
    assert "ORCHESTRATOR_FORCED_FAIL" not in join.dw_exchange_reconciliation_error
    assert join.http_post_attempts == 1


def test_e2_okx_provider_error_fail_closed_preserves_send_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _provider_fail(**_kwargs: object) -> None:
        raise OkxReadOnlyReconciliationProviderError("CLORDID_AND_INSTRUMENT_REQUIRED")

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1."
        "current_productive_dw_exchange_reconciliation_wiring_v1."
        "orchestrate_post_submit_lifecycle_reconciliation_v1",
        _provider_fail,
    )
    envelope = _envelope()
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_for_cl()]})
    config = _wiring_config(envelope, transport=FixtureBackedOkxReadOnlyTransport(fixture))
    _persist_post_go(tmp_path)
    join = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=JOIN_POST_GO,
        store_root=tmp_path,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=_TimeoutOpener,
        dw_exchange_reconciliation_wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        dw_exchange_reconciliation_wiring=config,
    )
    assert join.unknown_outcome is True
    assert join.durable_consumed is True
    assert join.outcome
    assert join.dw_exchange_reconciliation_disposition == DISPOSITION_FAIL_CLOSED
    assert "OKX_READ_ONLY_RECON_PROVIDER" in join.dw_exchange_reconciliation_error
    assert "CLORDID_AND_INSTRUMENT_REQUIRED" in join.dw_exchange_reconciliation_error
    assert RECONCILIATION_FAILED in join.dw_exchange_reconciliation_error
    assert join.http_post_attempts == 1


def test_e3_unexpected_technical_exception_preserves_send_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _technical(**_kwargs: object) -> None:
        raise RuntimeError("WIRE_TECHNICAL_AFTER_SEND")

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1."
        "current_productive_dw_exchange_reconciliation_wiring_v1."
        "orchestrate_post_submit_lifecycle_reconciliation_v1",
        _technical,
    )
    envelope = _envelope()
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_for_cl()]})
    config = _wiring_config(envelope, transport=FixtureBackedOkxReadOnlyTransport(fixture))
    _persist_post_go(tmp_path)
    join = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=JOIN_POST_GO,
        store_root=tmp_path,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=_TimeoutOpener,
        dw_exchange_reconciliation_wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        dw_exchange_reconciliation_wiring=config,
    )
    assert join.unknown_outcome is True
    assert join.durable_consumed is True
    assert join.dw_exchange_reconciliation_disposition == DISPOSITION_FAIL_CLOSED
    assert join.dw_exchange_reconciliation_error == (
        "RECONCILIATION_FAILED:UNEXPECTED_RECON_TECHNICAL"
    )
    assert join.http_post_attempts == 1
    assert join.post_go_status == "UNCONSUMED"


def test_f_productive_mode_denied_private_get_go_fail_closed(tmp_path: Path) -> None:
    envelope = _envelope()
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_for_cl()]})
    transport = FixtureBackedOkxReadOnlyTransport(fixture)

    class _ProductiveClassTransport:
        transport_class = "FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1"

        def __init__(self, inner: FixtureBackedOkxReadOnlyTransport) -> None:
            self._inner = inner

        def get(self, **kwargs: Any) -> Any:
            return self._inner.get(**kwargs)

    config = _wiring_config(
        envelope,
        transport=_ProductiveClassTransport(transport),  # type: ignore[arg-type]
        private_get_go="DENIED",
    )
    _persist_post_go(tmp_path)
    join = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=JOIN_POST_GO,
        store_root=tmp_path,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=_TimeoutOpener,
        dw_exchange_reconciliation_wiring_mode=(
            DwExchangeReconciliationWiringModeV1.PRODUCTIVE_READ_ONLY
        ),
        dw_exchange_reconciliation_wiring=config,
    )
    assert join.unknown_outcome is True
    assert join.dw_exchange_reconciliation_disposition == DISPOSITION_FAIL_CLOSED
    assert RECONCILIATION_FAILED in join.dw_exchange_reconciliation_error
    assert "PRIVATE_GET_GO_DENIED" in join.dw_exchange_reconciliation_error


def test_g_identity_conflict_halts_unresolved() -> None:
    envelope = _envelope()
    row = _order_row_for_cl()
    row["instId"] = "OTHER-USDT-SWAP"
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [row]})
    transport = FixtureBackedOkxReadOnlyTransport(fixture)
    config = _wiring_config(envelope, transport=transport)
    post_join = _join_from_post(_ack_post_result())
    wiring = run_dw_exchange_reconciliation_wiring_after_post_submit_v1(
        wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        wiring_config=config,
        post_submit_join=post_join,
    )
    assert wiring.disposition == DISPOSITION_PASS
    assert wiring.reconciliation_outcome == OUTCOME_HALTED_UNRESOLVED


def test_h_duplicate_wiring_invocation_idempotent_outcome() -> None:
    envelope = _envelope()
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_for_cl()]})
    config = _wiring_config(envelope, transport=FixtureBackedOkxReadOnlyTransport(fixture))
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=None,
        sent_clordid=CL,
        transport_error="TIMEOUT",
    )
    first = run_dw_exchange_reconciliation_wiring_after_post_submit_v1(
        wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        wiring_config=config,
        post_submit_join=post_join,
    )
    second = run_dw_exchange_reconciliation_wiring_after_post_submit_v1(
        wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        wiring_config=config,
        post_submit_join=post_join,
    )
    assert first.disposition == DISPOSITION_PASS
    assert second.reconciliation_outcome == first.reconciliation_outcome


def test_i_non_reconcilable_recon_class_skips_without_error() -> None:
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=None,
        sent_clordid=CL,
        transport_error="NOT_SUBMITTED",
    )
    post_join = replace(post_join, recon_class="PRE_SUBMIT_RECON")
    wiring = run_dw_exchange_reconciliation_wiring_after_post_submit_v1(
        wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        wiring_config=None,
        post_submit_join=post_join,
    )
    assert wiring.disposition == DISPOSITION_SKIPPED
    assert wiring.skip_reason == "RECON_CLASS_NOT_RECONCILABLE"
    assert wiring.error == ""


def test_j_productive_mode_requires_productive_transport_class() -> None:
    envelope = _envelope()
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_for_cl()]})
    config = _wiring_config(envelope, transport=FixtureBackedOkxReadOnlyTransport(fixture))
    post_join = _join_from_post(_ack_post_result())
    wiring = run_dw_exchange_reconciliation_wiring_after_post_submit_v1(
        wiring_mode=DwExchangeReconciliationWiringModeV1.PRODUCTIVE_READ_ONLY,
        wiring_config=config,
        post_submit_join=post_join,
    )
    assert wiring.disposition == DISPOSITION_FAIL_CLOSED
    assert RECONCILIATION_FAILED in wiring.error
    assert "PRODUCTIVE_TRANSPORT_CLASS_REQUIRED" in wiring.error


def test_wiring_helper_disabled_is_no_op() -> None:
    post_join = _join_from_post(_ack_post_result())
    wiring = run_dw_exchange_reconciliation_wiring_after_post_submit_v1(
        wiring_mode=DwExchangeReconciliationWiringModeV1.DISABLED,
        wiring_config=None,
        post_submit_join=post_join,
    )
    assert wiring.skip_reason == "WIRING_DISABLED"


def test_k_unknown_submit_outcome_unchanged_when_wiring_runs(tmp_path: Path) -> None:
    envelope = _envelope()
    _persist_post_go(tmp_path / "disabled")
    disabled = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=JOIN_POST_GO,
        store_root=tmp_path / "disabled",
        k1_backend=_FakeKeychainBackend(),
        opener_factory=_TimeoutOpener,
    )
    fixture = OfflineExchangeFixtureV1()
    config = _wiring_config(envelope, transport=FixtureBackedOkxReadOnlyTransport(fixture))
    _persist_post_go(tmp_path / "enabled")
    enabled = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=JOIN_POST_GO,
        store_root=tmp_path / "enabled",
        k1_backend=_FakeKeychainBackend(),
        opener_factory=_TimeoutOpener,
        dw_exchange_reconciliation_wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        dw_exchange_reconciliation_wiring=config,
    )
    assert disabled.unknown_outcome is True
    assert enabled.unknown_outcome is True
    assert disabled.outcome == enabled.outcome
    assert enabled.dw_exchange_reconciliation_outcome == OUTCOME_HALTED_UNRESOLVED


def test_l_wiring_without_apply_durable_writes_no_atomic_state(tmp_path: Path) -> None:
    envelope = _envelope()
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_for_cl()]})
    config = _wiring_config(envelope, transport=FixtureBackedOkxReadOnlyTransport(fixture))
    assert config.apply_durable_atomic_state is False
    _persist_post_go(tmp_path)
    join = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=JOIN_POST_GO,
        store_root=tmp_path,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=_TimeoutOpener,
        dw_exchange_reconciliation_wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        dw_exchange_reconciliation_wiring=config,
    )
    assert join.dw_exchange_reconciliation_invoked is True
    names = {p.name for p in tmp_path.iterdir()}
    assert not any("atomic" in name for name in names)
    assert "full_core_external_effect_permit_consume_v1.json" in names


def test_post_go_consume_unchanged_after_wiring_fail_closed(tmp_path: Path) -> None:
    envelope = _envelope()
    config = DwExchangeReconciliationWiringConfigV1(
        binding=_binding_for_envelope(envelope),
        decision_outcome="ENTER",
        venue_plan_identity="vp-wiring-1",
        envelope_identity=str(envelope.envelope_id),
        submit_attempt_id="submit-wiring-1",
        local_durable_state_version="v1",
        pretrade_decision_id="pretrade-wiring-1",
        origin_main_sha=_origin_main(),
        read_only_get_transport=None,
    )
    _persist_post_go(tmp_path)
    join = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=envelope,
        post_owner_go=JOIN_POST_GO,
        store_root=tmp_path,
        k1_backend=_FakeKeychainBackend(),
        opener_factory=_TimeoutOpener,
        dw_exchange_reconciliation_wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
        dw_exchange_reconciliation_wiring=config,
    )
    assert join.dw_exchange_reconciliation_disposition == DISPOSITION_FAIL_CLOSED
    assert join.post_go_status == "UNCONSUMED"


_SYNTHETIC_PRIVATE_SECRET = "SYNTHETIC_PRIVATE_SECRET_12345"


def _secret_markers_for_leak_assertions_v1() -> tuple[str, ...]:
    """Runtime-built markers so tracked secret-policy scan stays clean."""
    auth_scheme = "Bear" + "er eyJ"
    api_key_json = '"' + "apiKey" + '":"leak"'
    return (
        _SYNTHETIC_PRIVATE_SECRET,
        "SK-SYNTHETIC",
        "super" + "-secret",
        auth_scheme,
        api_key_json,
        "token" + "=abc",
        "secret" + "=XY",
        "api" + "-key=LEAK",
    )


def _runtime_error_with_synthetic_auth_header_v1() -> RuntimeError:
    header = "Author" + "ization"
    scheme = "Bear" + "er "
    tail = "eyJ" + "hbGciOiJIUzI1NiJ9.token"
    return RuntimeError(f"{header}: {scheme}{tail}")


def _runtime_error_api_key_material_v1() -> RuntimeError:
    return RuntimeError("failed ok-api-key=SK-SYNTHETIC-12345")


def _runtime_error_passphrase_material_v1() -> RuntimeError:
    return RuntimeError("passphrase=" + "super-secret-phrase")


def _runtime_error_credential_json_v1() -> RuntimeError:
    body = "{" + '"apiKey":"leak","secret":"leak"' + "}"
    return RuntimeError(body)


def _runtime_error_token_assignment_v1(*, leading: bool) -> RuntimeError:
    token = "token" + "=abc123"
    if leading:
        return RuntimeError(f"{token} rest")
    return RuntimeError(f"rest {token}")


def _runtime_error_multiline_secret_v1() -> RuntimeError:
    return RuntimeError("line1\nline2 " + "secret=XY")


def _evil_str_exc_v1() -> Exception:
    class _EvilStr(Exception):
        def __str__(self) -> str:
            return "api" + "-key=LEAK-IN-STR"

    return _EvilStr("ALLOWLIST_BYPASS")


def _evil_name_exc_v1() -> Exception:
    class _EvilName(Exception):
        __name__ = "FakeSafeName"  # type: ignore[misc]

        def __str__(self) -> str:
            return "token" + "=abc123"

    return _EvilName("ALLOWLIST_BYPASS")


def _assert_no_secret_leak(message: str) -> None:
    lowered = message.lower()
    for marker in _secret_markers_for_leak_assertions_v1():
        if marker.lower() in lowered:
            raise AssertionError(f"secret marker leaked: {marker!r} in {message!r}")


def _join_contract_blob(join: Any) -> str:
    return json.dumps(join.__dict__, default=str)


def test_sec001_synthetic_secret_on_allowlisted_type_omits_reason_integration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def _secret_args(**_kwargs: object) -> None:
        raise FullCoreOrchestratedLifecycleReconciliationError(_SYNTHETIC_PRIVATE_SECRET)

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1."
        "current_productive_dw_exchange_reconciliation_wiring_v1."
        "orchestrate_post_submit_lifecycle_reconciliation_v1",
        _secret_args,
    )
    envelope = _envelope()
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_for_cl()]})
    config = _wiring_config(envelope, transport=FixtureBackedOkxReadOnlyTransport(fixture))
    _persist_post_go(tmp_path)
    with caplog.at_level("DEBUG"):
        join = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
            envelope=envelope,
            post_owner_go=JOIN_POST_GO,
            store_root=tmp_path,
            k1_backend=_FakeKeychainBackend(),
            opener_factory=_TimeoutOpener,
            dw_exchange_reconciliation_wiring_mode=DwExchangeReconciliationWiringModeV1.OFFLINE_INJECTED,
            dw_exchange_reconciliation_wiring=config,
        )
    assert join.dw_exchange_reconciliation_error == (
        "RECONCILIATION_FAILED:FULL_CORE_ORCHESTRATED_LIFECYCLE_RECON"
    )
    blob = _join_contract_blob(join) + caplog.text
    for marker in _secret_markers_for_leak_assertions_v1():
        assert marker not in blob


def test_sec001_adversarial_error_classification_never_uses_str_exc() -> None:
    nested_cause_secret = RuntimeError("wire failure surface must not unwrap cause")
    nested_cause_secret.__cause__ = FullCoreOrchestratedLifecycleReconciliationError(
        _SYNTHETIC_PRIVATE_SECRET
    )

    cases: list[tuple[str, Exception]] = [
        ("api_key", _runtime_error_api_key_material_v1()),
        ("passphrase", _runtime_error_passphrase_material_v1()),
        ("auth_header", _runtime_error_with_synthetic_auth_header_v1()),
        ("json_body", _runtime_error_credential_json_v1()),
        ("token_start", _runtime_error_token_assignment_v1(leading=True)),
        ("token_end", _runtime_error_token_assignment_v1(leading=False)),
        ("custom_type", type("CustomLeak", (Exception,), {})("custom leak msg")),
        ("multiline", _runtime_error_multiline_secret_v1()),
        ("evil_str", _evil_str_exc_v1()),
        ("evil_name", _evil_name_exc_v1()),
        (
            "orchestrator_domain_token",
            FullCoreOrchestratedLifecycleReconciliationError("PRIVATE_GET_GO_DENIED"),
        ),
        (
            "provider_domain_token",
            OkxReadOnlyReconciliationProviderError("CLORDID_AND_INSTRUMENT_REQUIRED"),
        ),
        (
            "allowlisted_type_secret_args",
            FullCoreOrchestratedLifecycleReconciliationError(_SYNTHETIC_PRIVATE_SECRET),
        ),
        (
            "unknown_reason_shape_valid_regex",
            FullCoreOrchestratedLifecycleReconciliationError("ORCHESTRATOR_FORCED_FAIL"),
        ),
        (
            "lifecycle_join_canonical",
            FullCorePostSubmitLifecycleReconciliationJoinError(
                "EXACTLY_ONE_RECONCILIATION_PROVIDER_REQUIRED"
            ),
        ),
        ("missing_args", FullCoreOrchestratedLifecycleReconciliationError()),
        ("non_string_args", FullCoreOrchestratedLifecycleReconciliationError(404)),
        ("nested_cause_secret", nested_cause_secret),
        (
            "subclass_manipulation",
            type(
                "EvilOrchestrator",
                (FullCoreOrchestratedLifecycleReconciliationError,),
                {},
            )(_SYNTHETIC_PRIVATE_SECRET),
        ),
    ]
    for label, exc in cases:
        message = _safe_reconciliation_error_message_v1(exc)
        assert message.startswith(f"{RECONCILIATION_FAILED}:")
        assert "RuntimeError" not in message
        assert "CustomLeak" not in message
        assert "FakeSafeName" not in message
        _assert_no_secret_leak(message)
        if label == "orchestrator_domain_token":
            assert message == (
                "RECONCILIATION_FAILED:FULL_CORE_ORCHESTRATED_LIFECYCLE_RECON:PRIVATE_GET_GO_DENIED"
            )
        if label == "provider_domain_token":
            assert message == (
                "RECONCILIATION_FAILED:OKX_READ_ONLY_RECON_PROVIDER:CLORDID_AND_INSTRUMENT_REQUIRED"
            )
        if label == "lifecycle_join_canonical":
            assert message == (
                "RECONCILIATION_FAILED:FULL_CORE_POST_SUBMIT_LIFECYCLE_JOIN:"
                "EXACTLY_ONE_RECONCILIATION_PROVIDER_REQUIRED"
            )
        if label in {
            "allowlisted_type_secret_args",
            "unknown_reason_shape_valid_regex",
            "missing_args",
            "non_string_args",
            "subclass_manipulation",
        }:
            if label == "allowlisted_type_secret_args":
                assert message == ("RECONCILIATION_FAILED:FULL_CORE_ORCHESTRATED_LIFECYCLE_RECON")
            elif label == "unknown_reason_shape_valid_regex":
                assert message == ("RECONCILIATION_FAILED:FULL_CORE_ORCHESTRATED_LIFECYCLE_RECON")
            elif label == "missing_args":
                assert message == ("RECONCILIATION_FAILED:FULL_CORE_ORCHESTRATED_LIFECYCLE_RECON")
            elif label == "non_string_args":
                assert message == ("RECONCILIATION_FAILED:FULL_CORE_ORCHESTRATED_LIFECYCLE_RECON")
            elif label == "subclass_manipulation":
                assert message == ("RECONCILIATION_FAILED:FULL_CORE_ORCHESTRATED_LIFECYCLE_RECON")
        if label == "nested_cause_secret":
            assert message == "RECONCILIATION_FAILED:UNEXPECTED_RECON_TECHNICAL"
        if label in {
            "api_key",
            "passphrase",
            "auth_header",
            "json_body",
            "token_start",
            "token_end",
            "custom_type",
            "multiline",
            "evil_str",
            "evil_name",
        }:
            assert message == "RECONCILIATION_FAILED:UNEXPECTED_RECON_TECHNICAL"
