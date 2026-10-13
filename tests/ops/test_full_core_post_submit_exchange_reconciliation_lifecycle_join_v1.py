"""End-to-end offline proofs: Cap-11.1 post-submit join → exchange reconciliation → atomic."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    STATE_HALTED_UNRESOLVED,
    STATE_RECONCILIATION_PENDING,
    STATE_TERMINAL_RECONCILED,
    full_core_atomic_mark_submit_boundary_v1,
    full_core_atomic_reserve_owner_go_authorization_v1,
    load_full_core_atomic_authorization_state_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_FILLED,
    OUTCOME_CONFIRMED_OPEN,
    OUTCOME_HALTED_UNRESOLVED,
    LocalSubmitOutcome,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    FullCorePostSubmitJoinResultV1,
    join_full_core_post_result_to_lifecycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    FullCoreExchangeReconciliationDecisionV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    NETWORK_REQUEST_COUNT,
    POST_COUNT,
    PRIVATE_GET_COUNT,
    PRODUCTION_PROVIDER_WIRING,
    REAL_ORDER_COUNT,
    FullCorePostSubmitLifecycleReconciliationJoinError,
    local_submit_outcome_from_post_submit_join_v1,
    reconciliation_fsm_identity_bound_exchange_evidence_v1,
    run_full_core_post_submit_lifecycle_reconciliation_join_v1,
    verify_ghv_forward_join_v1,
    verify_ghv_reverse_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreTradeOrderPostResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_core_exchange_reconciliation_observability_v1 import (
    STAGE_POST_SUBMIT_LIFECYCLE_JOIN,
)
from tests.ops.test_full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    FixtureBackedOkxReadOnlyTransport,
)
from tests.ops.test_full_core_exchange_reconciliation_v1 import (
    CL,
    _binding,
    _order_row,
)

SENT = CL
ORD = "ord-join-1"


def _ack_post_result() -> FullCoreTradeOrderPostResultV1:
    return FullCoreTradeOrderPostResultV1(
        post_attempted=True,
        venue_live_contact=False,
        method="POST",
        http_status=200,
        payload={
            "code": "0",
            "data": [
                {
                    "clOrdId": SENT,
                    "ordId": ORD,
                    "sCode": "0",
                }
            ],
        },
        unknown_outcome=False,
        transport_class="INJECTED_TEST_DOUBLE",
        endpoint="/api/v5/trade/order",
    )


def _join_from_post(result: FullCoreTradeOrderPostResultV1 | None, *, err: str | None = None):
    return join_full_core_post_result_to_lifecycle_v1(
        result=result,
        sent_clordid=SENT,
        submit_count=1,
        transport_error=err,
    )


def _join_kwargs() -> dict[str, str]:
    return {
        "decision_outcome": "ENTER",
        "venue_plan_identity": "vp-join-1",
        "envelope_identity": "env-join-1",
        "submit_attempt_id": "submit-join-1",
        "local_durable_state_version": "v1",
    }


class TestSafetyPins:
    def test_standing_fail_closed(self) -> None:
        assert POST_COUNT == 0
        assert PRIVATE_GET_COUNT == 0
        assert NETWORK_REQUEST_COUNT == 0
        assert REAL_ORDER_COUNT == 0
        assert PRODUCTION_PROVIDER_WIRING == "NOT_AUTHORIZED"


def _order_row_join(*, state: str, sz: str = "10", acc: str = "0") -> dict:
    row = _order_row(state=state, sz=sz, acc=acc)
    row["ordId"] = ORD
    return row


def test_ack_open_order_offline_forward_reverse_join() -> None:
    post_join = _join_from_post(_ack_post_result())
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_join(state="live")]})
    res = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=_binding(),
        offline_fixture=fixture,
        **_join_kwargs(),
    )
    assert res.local_submit_outcome is LocalSubmitOutcome.TRANSPORT_ACK
    assert res.reconciliation.decision.outcome == OUTCOME_CONFIRMED_OPEN
    assert res.ghv_forward_join == "PASS"
    assert res.ghv_reverse_join == "PASS"
    stages = [
        s["stage"]
        for s in res.reconciliation.ghv_bundle["ghv_full_core_exchange_reconciliation_stages"]
    ]
    assert stages[0] == STAGE_POST_SUBMIT_LIFECYCLE_JOIN


def test_unknown_timeout_recovery_with_exchange_evidence_passes_ghv_joins() -> None:
    post_join = _join_from_post(None, err="socket.timeout")
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_join(state="live")]})
    res = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=_binding(),
        offline_fixture=fixture,
        **_join_kwargs(),
    )
    assert res.local_submit_outcome is LocalSubmitOutcome.TRANSPORT_TIMEOUT
    assert res.reconciliation.decision.outcome == OUTCOME_CONFIRMED_OPEN
    assert res.reconciliation.decision.venue_ord_id == ORD
    assert res.ghv_forward_join == "PASS"
    assert res.ghv_reverse_join == "PASS"


def test_unknown_timeout_halts_without_terminal_promotion() -> None:
    post_join = _join_from_post(None, err="socket.timeout")
    assert post_join.typed_outcome == "UNKNOWN"
    fixture = OfflineExchangeFixtureV1()
    res = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=_binding(),
        offline_fixture=fixture,
        **_join_kwargs(),
    )
    assert res.local_submit_outcome is LocalSubmitOutcome.TRANSPORT_TIMEOUT
    assert res.reconciliation.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    assert res.ghv_forward_join == "PASS"
    assert res.ghv_reverse_join == "PASS"


def test_okx_injected_path_matches_offline_stub() -> None:
    post_join = _join_from_post(_ack_post_result())
    fixture = OfflineExchangeFixtureV1(
        pending_orders={"data": [_order_row_join(state="filled", acc="10")]}
    )
    offline = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=_binding(),
        offline_fixture=fixture,
        **_join_kwargs(),
    )
    transport = FixtureBackedOkxReadOnlyTransport(fixture)
    okx = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=_binding(),
        read_only_get_transport=transport,
        pretrade_decision_id="pretrade-1",
        **_join_kwargs(),
    )
    assert offline.reconciliation.decision.outcome == okx.reconciliation.decision.outcome
    assert offline.reconciliation.decision.outcome == OUTCOME_CONFIRMED_FILLED
    assert transport.request_count > 0


def test_durable_atomic_terminal_after_ack_and_fill(tmp_state: Path) -> None:
    binding = _binding()
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp_state, binding=binding)
    full_core_atomic_mark_submit_boundary_v1(state_dir=tmp_state, binding=binding)
    post_join = _join_from_post(_ack_post_result())
    fixture = OfflineExchangeFixtureV1(
        order_history={"data": [_order_row_join(state="filled", acc="10")]}
    )
    res = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=binding,
        offline_fixture=fixture,
        state_dir=tmp_state,
        apply_durable_state=True,
        **_join_kwargs(),
    )
    assert res.reconciliation.atomic_state_after == STATE_TERMINAL_RECONCILED
    loaded = load_full_core_atomic_authorization_state_v1(
        state_dir=tmp_state, consumption_key=binding.consumption_key()
    )
    assert loaded is not None
    assert loaded.state == STATE_TERMINAL_RECONCILED


def test_unknown_submit_leaves_reconciliation_pending_not_terminal(tmp_state: Path) -> None:
    binding = _binding()
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=tmp_state, binding=binding)
    full_core_atomic_mark_submit_boundary_v1(state_dir=tmp_state, binding=binding)
    post_join = _join_from_post(None, err="UNKNOWN_OUTCOME")
    res = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=binding,
        offline_fixture=OfflineExchangeFixtureV1(),
        state_dir=tmp_state,
        apply_durable_state=True,
        **_join_kwargs(),
    )
    assert res.reconciliation.decision.recommended_atomic_state in {
        "RECONCILIATION_PENDING",
        "HALTED_UNRESOLVED",
    }
    loaded = load_full_core_atomic_authorization_state_v1(
        state_dir=tmp_state, consumption_key=binding.consumption_key()
    )
    assert loaded is not None
    assert loaded.state in {STATE_RECONCILIATION_PENDING, STATE_HALTED_UNRESOLVED}
    assert loaded.state != STATE_TERMINAL_RECONCILED


def test_provider_xor_fail_closed() -> None:
    post_join = _join_from_post(_ack_post_result())
    with pytest.raises(FullCorePostSubmitLifecycleReconciliationJoinError) as exc:
        run_full_core_post_submit_lifecycle_reconciliation_join_v1(
            post_submit_join=post_join,
            binding=_binding(),
            **_join_kwargs(),
        )
    assert "EXACTLY_ONE_RECONCILIATION_PROVIDER_REQUIRED" in str(exc.value)


def _unknown_join_not_submitted() -> FullCorePostSubmitJoinResultV1:
    """UNKNOWN lifecycle row with no POST attempt → NOT_SUBMITTED local outcome."""
    base = _join_from_post(None, err="socket.timeout")
    return FullCorePostSubmitJoinResultV1(
        post_attempted=False,
        typed_outcome="UNKNOWN",
        lifecycle_state=base.lifecycle_state,
        recon_class=base.recon_class,
        restart_blocked=base.restart_blocked,
        fill_observed=base.fill_observed,
        resubmit_allowed=False,
        blind_retry_forbidden=True,
        exchange_query_before_retry_required=base.exchange_query_before_retry_required,
        unknown_requires_exchange_query=base.unknown_requires_exchange_query,
        venue_order_id="",
        client_order_id=SENT,
        reason=base.reason,
        http_status=0,
        ack_is_not_fill=base.ack_is_not_fill,
        http_success_is_not_ack=base.http_success_is_not_ack,
        mapper_owner=base.mapper_owner,
        lifecycle_owner=base.lifecycle_owner,
        section_11_14_promoted=base.section_11_14_promoted,
        real_post_count=0,
    )


def test_ghv_reverse_join_rejects_unknown_not_submitted_terminal_without_evidence() -> None:
    post_join = _unknown_join_not_submitted()
    assert (
        local_submit_outcome_from_post_submit_join_v1(post_join) is LocalSubmitOutcome.NOT_SUBMITTED
    )
    forged = FullCoreExchangeReconciliationDecisionV1(
        outcome=OUTCOME_CONFIRMED_FILLED,
        reasons=(),
        exposure_retained=True,
        reconciliation_complete=True,
        recommended_atomic_state="TERMINAL_RECONCILED",
        execution_authority_effect="NONE",
        order_state="filled",
        cumulative_filled_qty="10",
        remaining_qty="0",
        venue_ord_id=None,
    )
    assert (
        verify_ghv_reverse_join_v1(
            join=post_join,
            local_submit_outcome=LocalSubmitOutcome.NOT_SUBMITTED,
            decision=forged,
        )
        is False
    )
    assert (
        verify_ghv_forward_join_v1(
            join=post_join,
            local_submit_outcome=LocalSubmitOutcome.NOT_SUBMITTED,
            decision=forged,
        )
        is False
    )


def test_ghv_join_rejects_unknown_terminal_without_fsm_exchange_evidence() -> None:
    post_join = _join_from_post(None, err="socket.timeout")
    forged = FullCoreExchangeReconciliationDecisionV1(
        outcome=OUTCOME_CONFIRMED_FILLED,
        reasons=(),
        exposure_retained=True,
        reconciliation_complete=True,
        recommended_atomic_state="TERMINAL_RECONCILED",
        execution_authority_effect="NONE",
        order_state="filled",
        cumulative_filled_qty="10",
        remaining_qty="0",
        venue_ord_id=None,
    )
    assert reconciliation_fsm_identity_bound_exchange_evidence_v1(forged) is False
    assert (
        verify_ghv_reverse_join_v1(
            join=post_join,
            local_submit_outcome=LocalSubmitOutcome.TRANSPORT_TIMEOUT,
            decision=forged,
        )
        is False
    )
    assert (
        verify_ghv_forward_join_v1(
            join=post_join,
            local_submit_outcome=LocalSubmitOutcome.TRANSPORT_TIMEOUT,
            decision=forged,
        )
        is False
    )


def test_okx_read_only_productive_forensic_profile_labels() -> None:
    post_join = _join_from_post(_ack_post_result())
    fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_join(state="live")]})
    transport = FixtureBackedOkxReadOnlyTransport(fixture)
    res = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=_binding(),
        read_only_get_transport=transport,
        pretrade_decision_id="pretrade-profile",
        okx_read_only_forensic_profile="PRODUCTIVE_SCOPED",
        **_join_kwargs(),
    )
    assert res.provider_mode == "PRODUCTIVE_OKX_SCOPED_READ_ONLY"
    stages = res.reconciliation.ghv_bundle["ghv_full_core_exchange_reconciliation_stages"]
    assert stages[0]["simulation_mode"] == "PRODUCTIVE_VENUE_READ_ONLY_GET"


def test_ghv_forward_join_not_submitted_without_post_attempt() -> None:
    post_join = _join_from_post(None)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=None,
        sent_clordid=SENT,
        submit_count=0,
    )
    res = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=_binding(),
        offline_fixture=OfflineExchangeFixtureV1(),
        proven_never_submitted=True,
        **_join_kwargs(),
    )
    assert res.local_submit_outcome.value == "NOT_SUBMITTED"
    assert res.ghv_forward_join == "PASS"
    assert res.ghv_reverse_join == "PASS"


def test_local_submit_outcome_mapping_table() -> None:
    ack = _join_from_post(_ack_post_result())
    assert local_submit_outcome_from_post_submit_join_v1(ack) is LocalSubmitOutcome.TRANSPORT_ACK
    unk = _join_from_post(None, err="TimeoutError")
    assert (
        local_submit_outcome_from_post_submit_join_v1(unk) is LocalSubmitOutcome.TRANSPORT_TIMEOUT
    )


@pytest.fixture
def tmp_state() -> Path:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)
