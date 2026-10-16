"""GHV Full Autonomous Offline E2E Closure V2 — S1 cancel interleaving, S2 GHOSV A/B, S3 unified chain.

Tests-only harness. No venue POST/GET. Uses CURRENT production contracts with injected doubles.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.order_lifecycle_state_machine_v1 import (
    HARD_TERMINAL_ORDER_STATES,
    OrderLifecycleStateMachineV1,
    OrderLifecycleTransitionError,
)
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
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_integration_v1 import (
    run_full_core_offline_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_PARTIALLY_FILLED,
    OUTCOME_CONFIRMED_FILLED,
    OUTCOME_HALTED_UNRESOLVED,
    LocalSubmitOutcome,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 import (
    CycleSubmitInjectionKind,
    run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    POST_COUNT,
    REAL_ORDER_COUNT,
    run_full_core_post_submit_lifecycle_reconciliation_join_v1,
)
from src.ops.ghosv_bounded_context_v1.constants_v1 import ADAPTER_MODE, SAFETY_ESCALATION_ENABLED
from src.ops.ghosv_bounded_context_v1.execution_bounded_offline_observer_v1 import (
    ExecutionOfflineObserverPathsV1,
    run_execution_bounded_offline_observer_v1,
)
from tests.ops.test_full_core_exchange_reconciliation_v1 import CL, _binding, _identity, _order_row
from tests.ops.test_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 import (
    _ack_post,
    _cycle,
    _envelope,
    _handoff,
    _order_row_join,
    _origin_main,
    _wiring_request,
)
from tests.ops.test_full_core_post_response_to_ack_mapper_and_lifecycle_join_v1 import (
    FixturePostTransportV1,
    _ack_payload,
    _post_result,
    _send,
)
from tests.ops.test_full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    ORD,
    _ack_post_result,
    _join_from_post,
    _join_kwargs,
    _order_row_join as _order_row_join_recon,
)


def _fsm_from_ack() -> OrderLifecycleStateMachineV1:
    machine = OrderLifecycleStateMachineV1(client_order_id=CL)
    for state in (
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
        "ACKNOWLEDGED",
    ):
        machine.transition(state)
    return machine


def _offline_recon(fixture: OfflineExchangeFixtureV1):
    binding = _binding()
    return run_full_core_offline_exchange_reconciliation_v1(
        identity=_identity(binding),
        binding=binding,
        fixture=fixture,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )


class TestSlice1CancelInterleaving:
    """Cap 11.1 FSM + Full-Core reconciliation for cancel/fill interleaving."""

    def test_s1_a_ack_cancel_partial_fill_cancel_ack(self) -> None:
        m = _fsm_from_ack()
        m.transition("OPEN")
        m.transition("CANCEL_PENDING")
        m.transition("PARTIALLY_FILLED")
        m.transition("CANCELLED")
        assert m.history[-3:] == ["CANCEL_PENDING", "PARTIALLY_FILLED", "CANCELLED"]
        fixture = OfflineExchangeFixtureV1(
            order_history={"data": [_order_row(state="canceled", sz="10", acc="4")]}
        )
        rec = _offline_recon(fixture)
        assert rec.decision.outcome == OUTCOME_CONFIRMED_PARTIALLY_FILLED
        assert Decimal(str(rec.decision.cumulative_filled_qty or "0")) >= Decimal("4")

    def test_s1_b_partial_then_cancel_additional_fill_cancel_ack(self) -> None:
        m = _fsm_from_ack()
        m.transition("OPEN")
        m.transition("PARTIALLY_FILLED")
        m.transition("CANCEL_PENDING")
        m.transition("PARTIALLY_FILLED")
        m.transition("CANCELLED")
        fixture = OfflineExchangeFixtureV1(
            order_history={"data": [_order_row(state="canceled", sz="10", acc="7")]}
        )
        rec = _offline_recon(fixture)
        assert rec.decision.outcome == OUTCOME_CONFIRMED_PARTIALLY_FILLED
        assert Decimal(str(rec.decision.cumulative_filled_qty or "0")) == Decimal("7")

    def test_s1_c_full_fill_blocks_late_cancel_fsm_and_conflicting_recon_halts(self) -> None:
        m = _fsm_from_ack()
        m.transition("OPEN")
        m.transition("CANCEL_PENDING")
        m.transition("FILLED")
        assert "FILLED" in HARD_TERMINAL_ORDER_STATES
        with pytest.raises(OrderLifecycleTransitionError) as exc:
            m.transition("CANCELLED")
        assert exc.value.code == "ILLEGAL_LIFECYCLE_TRANSITION"
        fixture = OfflineExchangeFixtureV1(
            pending_orders={"data": [_order_row_join_recon(state="live")]},
            order_history={"data": [_order_row_join_recon(state="filled", acc="10")]},
        )
        post_join = _join_from_post(_ack_post_result())
        res = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
            post_submit_join=post_join,
            binding=_binding(),
            offline_fixture=fixture,
            **_join_kwargs(),
        )
        assert res.reconciliation.decision.outcome == OUTCOME_HALTED_UNRESOLVED
        assert res.reconciliation.decision.reasons == ("CONFLICTING_ORDER_STATE",)

    def test_s1_d_cancel_rejected_not_modeled_fsm_order_remains_live_via_partial(self) -> None:
        """CANCEL_REJECTED is not a Cap-11.1 state; live order modeled as CANCEL_PENDING → PARTIAL without CANCELLED."""
        m = _fsm_from_ack()
        m.transition("OPEN")
        m.transition("CANCEL_PENDING")
        m.transition("PARTIALLY_FILLED")
        assert m.current_state == "PARTIALLY_FILLED"
        fixture = OfflineExchangeFixtureV1(
            pending_orders={"data": [_order_row(state="partially_filled", sz="10", acc="2")]}
        )
        rec = _offline_recon(fixture)
        assert rec.decision.outcome == OUTCOME_CONFIRMED_PARTIALLY_FILLED

    def test_s1_e_unknown_cancel_outcome_halts_reconciliation(self) -> None:
        post_join = _join_from_post(None, err="cancel.timeout")
        fixture = OfflineExchangeFixtureV1()
        res = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
            post_submit_join=post_join,
            binding=_binding(),
            offline_fixture=fixture,
            **_join_kwargs(),
        )
        assert post_join.typed_outcome == "UNKNOWN"
        assert res.reconciliation.decision.outcome == OUTCOME_HALTED_UNRESOLVED
        assert res.ghv_forward_join == "PASS"
        assert res.ghv_reverse_join == "PASS"


class TestSlice2GhosvNoninterferenceAB:
    """Identical productive wiring; B adds post-hoc GHOSV observer only."""

    @staticmethod
    def _productive_wiring(tmp_path: Path) -> dict[str, Any]:
        sha = _origin_main()
        env = _envelope()
        fixture = OfflineExchangeFixtureV1(
            pending_orders={"data": [_order_row_join(state="partially_filled", acc="4")]}
        )
        state_dir = tmp_path / "atomic"
        state_dir.mkdir()
        res = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
            cycle=_cycle(envelope=env),
            handoff=_handoff(sha=sha),
            request=_wiring_request(
                sha=sha,
                submit_kind=CycleSubmitInjectionKind.ACKNOWLEDGED,
                fixture=fixture,
                post=_ack_post(),
                state_dir=state_dir,
                apply_durable=True,
            ),
        )
        assert res.lifecycle is not None
        view = res.to_dict()
        lc = res.lifecycle
        view["lifecycle"] = {
            "local_submit_outcome": lc.local_submit_outcome.value,
            "reconciliation_outcome": lc.reconciliation.decision.outcome,
            "ghv_forward_join": lc.ghv_forward_join,
            "ghv_reverse_join": lc.ghv_reverse_join,
            "atomic_state_after": lc.reconciliation.atomic_state_after,
        }
        view["post_submit_join"] = {
            "typed_outcome": res.post_submit_join.typed_outcome if res.post_submit_join else None,
            "lifecycle_state": res.post_submit_join.lifecycle_state
            if res.post_submit_join
            else None,
            "recon_class": res.post_submit_join.recon_class if res.post_submit_join else None,
        }
        return view

    def test_s2_ab_productive_outputs_identical_observer_read_only(self, tmp_path: Path) -> None:
        path_a = tmp_path / "run_a"
        path_b = tmp_path / "run_b"
        path_a.mkdir()
        path_b.mkdir()
        out_a = self._productive_wiring(path_a)
        out_b = self._productive_wiring(path_b)

        assert out_a == out_b

        atomic_files = list((path_b / "atomic").glob("**/*"))
        snapshots_before = {
            str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in atomic_files if p.is_file()
        }

        observer_dir = path_b / "observer_out"
        report = run_execution_bounded_offline_observer_v1(
            ExecutionOfflineObserverPathsV1(
                trade_id="closure-v2-ab",
                output_dir=observer_dir,
                recon_dir=None,
            )
        )
        assert report["observer_run_success"] is True
        assert report["safety_adapter_status"]["adapter_mode"] == ADAPTER_MODE == "DISABLED"
        assert report["safety_adapter_status"]["safety_escalation_enabled"] is False
        assert SAFETY_ESCALATION_ENABLED is False

        for p, (content, mtime) in snapshots_before.items():
            path = Path(p)
            assert path.read_bytes() == content
            assert path.stat().st_mtime_ns == mtime

        assert POST_COUNT == 0
        assert REAL_ORDER_COUNT == 0


class TestSlice3UnifiedOfflineE2E:
    """Send seam → join → durable → simulated restart → reconciliation → GHOSV read."""

    def test_s3_positive_partial_crash_restart_full_fill_continuation(self, tmp_path: Path) -> None:
        store = tmp_path / "permit_store"
        store.mkdir()
        transport = FixturePostTransportV1(result=_post_result(payload=_ack_payload()))
        seam = _send(transport=transport, tmp_path=store)
        assert seam.real_post_count == 0
        assert seam.mocked_post_count == 1
        assert seam.post_submit_join is not None
        assert seam.durable_consumed is True

        binding = _binding()
        state_dir = tmp_path / "atomic"
        state_dir.mkdir()
        full_core_atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=binding)
        full_core_atomic_mark_submit_boundary_v1(state_dir=state_dir, binding=binding)

        post_join = _join_from_post(_ack_post_result())
        partial_row = _order_row(state="partially_filled", sz="10", acc="4")
        partial_row["ordId"] = ORD
        partial_fixture = OfflineExchangeFixtureV1(pending_orders={"data": [partial_row]})
        first = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
            post_submit_join=post_join,
            binding=binding,
            offline_fixture=partial_fixture,
            state_dir=state_dir,
            apply_durable_state=True,
            **_join_kwargs(),
        )
        assert first.reconciliation.decision.outcome == OUTCOME_CONFIRMED_PARTIALLY_FILLED
        mid = load_full_core_atomic_authorization_state_v1(
            state_dir=state_dir, consumption_key=binding.consumption_key()
        )
        assert mid is not None
        assert mid.state in {STATE_RECONCILIATION_PENDING, STATE_TERMINAL_RECONCILED}

        # Simulated crash + restart: reload durable state, reconcile against updated exchange truth.
        filled_row = _order_row(state="filled", sz="10", acc="10")
        filled_row["ordId"] = ORD
        filled_fixture = OfflineExchangeFixtureV1(order_history={"data": [filled_row]})
        second = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
            post_submit_join=post_join,
            binding=binding,
            offline_fixture=filled_fixture,
            state_dir=state_dir,
            apply_durable_state=True,
            **_join_kwargs(),
        )
        assert second.reconciliation.decision.outcome == OUTCOME_CONFIRMED_FILLED
        terminal = load_full_core_atomic_authorization_state_v1(
            state_dir=state_dir, consumption_key=binding.consumption_key()
        )
        assert terminal is not None
        assert terminal.state == STATE_TERMINAL_RECONCILED
        assert first.ghv_forward_join == "PASS" and second.ghv_forward_join == "PASS"

        obs = run_execution_bounded_offline_observer_v1(
            ExecutionOfflineObserverPathsV1(
                trade_id="closure-v2-unified",
                output_dir=tmp_path / "ghosv_obs",
            )
        )
        assert obs["observer_run_success"] is True

    def test_s3_negative_unknown_restart_halt_no_second_submit(self, tmp_path: Path) -> None:
        sha = _origin_main()
        env = _envelope()
        state_dir = tmp_path / "halt"
        state_dir.mkdir()
        first = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
            cycle=_cycle(envelope=env),
            handoff=_handoff(sha=sha),
            request=_wiring_request(
                sha=sha,
                submit_kind=CycleSubmitInjectionKind.UNKNOWN_TIMEOUT,
                state_dir=state_dir,
                apply_durable=True,
            ),
        )
        assert first.lifecycle is not None
        assert first.lifecycle.reconciliation.decision.outcome == OUTCOME_HALTED_UNRESOLVED
        assert first.lifecycle.reconciliation.atomic_state_after in {
            STATE_HALTED_UNRESOLVED,
            STATE_RECONCILIATION_PENDING,
            None,
        }

        second = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
            cycle=_cycle(envelope=env),
            handoff=_handoff(sha=sha),
            request=_wiring_request(
                sha=sha,
                submit_kind=CycleSubmitInjectionKind.UNKNOWN_TIMEOUT,
                state_dir=state_dir,
                apply_durable=True,
            ),
        )
        assert second.lifecycle is None
        assert second.guard_blocked is True
        assert second.skip_reason == "CAPITAL_GUARD_BLOCKED"
        assert POST_COUNT == 0
