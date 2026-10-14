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
    DwExchangeReconciliationWiringConfigV1,
    DwExchangeReconciliationWiringModeV1,
    run_dw_exchange_reconciliation_wiring_after_post_submit_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
    FullCoreOrchestratedLifecycleReconciliationError,
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
    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="buy",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid=CL,
        venue_native_payload={
            "instId": INST,
            "ordType": "market",
            "side": "buy",
            "sz": "1",
            "tdMode": "cross",
        },
        quantity_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="DH_CAP24_BOUND_INSTRUMENT_ID",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="TEST_ADMISSION_REF",
        provenance_ref="TEST_PROVENANCE_REF",
        creation_epoch="2026-09-22T00:00:00Z",
    )


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
    assert "ORCHESTRATOR_FORCED_FAIL" in join.dw_exchange_reconciliation_error


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
