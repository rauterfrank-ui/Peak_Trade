"""GHV Final Execution & Recovery Evidence Closure V3 — S1 cancel-reject, S2 durable UNKNOWN restart.

CURRENT inventory (S1, read-only):
- Cap 11.1 FSM: CANCEL_PENDING exists; no CANCEL_REJECTED lifecycle state.
- Full-Core post-submit path: order POST mapper only (ACK/REJECT/UNKNOWN); no venue cancel-request mapper.
- Cancel truth: exchange reconciliation reads order rows (live / partially_filled / canceled).
- Testnet campaign cleanup references cancel_rejected events — not CURRENT productive Full-Core entry.

Surrogate model: cancel-reject ⇒ exchange still shows open order; FSM may remain CANCEL_PENDING or advance via fills.
"""

from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.order_lifecycle_state_machine_v1 import (
    OrderLifecycleStateMachineV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_integration_v1 import (
    run_full_core_offline_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_CANCELED,
    OUTCOME_CONFIRMED_OPEN,
    OUTCOME_CONFIRMED_PARTIALLY_FILLED,
    OUTCOME_HALTED_UNRESOLVED,
    LocalSubmitOutcome,
)
from tests.ops._current_productive_post_hard_crash_harness_v1 import (
    REPO_ROOT,
    CrashPointV1,
    bootstrap_unknown_post_store_v1,
    expected_crash_exit_v1,
    run_adversarial_reconciliation_v1,
    spawn_hard_crash_child_v1,
)
from tests.ops.test_full_core_exchange_reconciliation_v1 import CL, _binding, _identity, _order_row
from tests.ops.test_current_productive_post_hard_crash_matrix_harness_v1 import (
    CONFIRMED_ACCEPTED_WORKING,
    PILOT_TEST_INST,
    STILL_UNKNOWN,
)

RESTART_EVAL_RUNNER = REPO_ROOT / "tests/ops/_ghv_closure_v3_restart_eval_subprocess_v1.py"


def _fsm_ack_open() -> OrderLifecycleStateMachineV1:
    m = OrderLifecycleStateMachineV1(client_order_id=CL)
    for state in (
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
        "ACKNOWLEDGED",
        "OPEN",
    ):
        m.transition(state)
    return m


def _recon(fixture: OfflineExchangeFixtureV1):
    return run_full_core_offline_exchange_reconciliation_v1(
        identity=_identity(_binding()),
        binding=_binding(),
        fixture=fixture,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )


class TestSlice1CancelRejectQualification:
    """CR-01..CR-04 via FSM + exchange reconciliation (no new lifecycle states)."""

    def test_cr01_cancel_reject_surrogate_order_still_live(self) -> None:
        m = _fsm_ack_open()
        m.transition("CANCEL_PENDING")
        m.transition("PARTIALLY_FILLED")
        assert m.current_state == "PARTIALLY_FILLED"
        assert "CANCELLED" not in m.history
        rec = _recon(OfflineExchangeFixtureV1(pending_orders={"data": [_order_row(state="live")]}))
        assert rec.decision.outcome == OUTCOME_CONFIRMED_OPEN

    def test_cr02_partial_fill_cancel_reject_additional_fill(self) -> None:
        m = _fsm_ack_open()
        m.transition("PARTIALLY_FILLED")
        m.transition("CANCEL_PENDING")
        m.transition("PARTIALLY_FILLED")
        rec = _recon(
            OfflineExchangeFixtureV1(
                pending_orders={"data": [_order_row(state="partially_filled", sz="10", acc="6")]}
            )
        )
        assert rec.decision.outcome == OUTCOME_CONFIRMED_PARTIALLY_FILLED
        assert Decimal(rec.decision.cumulative_filled_qty or "0") == Decimal("6")

    def test_cr03_reconciliation_sets_follow_on_state(self) -> None:
        rec = _recon(
            OfflineExchangeFixtureV1(
                order_history={"data": [_order_row(state="canceled", sz="10", acc="0")]}
            )
        )
        assert rec.decision.outcome == OUTCOME_CONFIRMED_CANCELED
        assert rec.decision.order_state == "canceled"

    def test_cr04_conflicting_evidence_fail_closed(self) -> None:
        live = _order_row(state="live", sz="10", acc="0")
        canceled = _order_row(state="canceled", sz="10", acc="0")
        live["ordId"] = "ord-a"
        canceled["ordId"] = "ord-b"
        rec = _recon(
            OfflineExchangeFixtureV1(
                pending_orders={"data": [live]},
                order_history={"data": [canceled]},
            )
        )
        assert rec.decision.outcome == OUTCOME_HALTED_UNRESOLVED

    def test_no_full_core_cancel_request_mapper_documented(self) -> None:
        root = REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1"
        py_sources = "\n".join(p.read_text(encoding="utf-8") for p in root.glob("*.py"))
        assert "cancel_order" not in py_sources
        assert "CANCEL_REJECT" not in py_sources
        assert "ACKNOWLEDGED" in py_sources


class TestSlice2DurableUnknownRestart:
    """Two-process replay isolation (child crash + fresh interpreter evaluation)."""

    @staticmethod
    def _spawn_process_a_unknown_crash(store: Path) -> None:
        child = spawn_hard_crash_child_v1(store_root=store, crash_point=CrashPointV1.C9)
        assert child.timed_out is False, child.stderr
        assert child.exit_code == expected_crash_exit_v1(CrashPointV1.C9)

    @staticmethod
    def _spawn_process_b_evaluate(store: Path) -> dict:
        cmd = [
            sys.executable,
            str(RESTART_EVAL_RUNNER),
            "--store-root",
            str(store),
            "--crash-point",
            "C9",
        ]
        completed = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        return json.loads(completed.stdout.strip())

    def test_ur01_ur02_two_process_durable_consume_blocks_replay(self, tmp_path: Path) -> None:
        store = tmp_path / "shared_store"
        store.mkdir()
        self._spawn_process_a_unknown_crash(store)
        payload = self._spawn_process_b_evaluate(store)
        assert payload["durable_consumed"] is True
        assert payload["durable_state"] == "SENT_INITIATED"
        assert payload["second_admission_blocked"] is True
        assert payload["mock_post_attempts_after_restart"] == 0
        assert payload["replay_attempt_executed"] is True
        assert "NO_NEW_ENTRY_WHILE" in payload["second_admission_reason"]

    def test_ur03_unknown_outcome_still_requires_reconciliation(self, tmp_path: Path) -> None:
        store, env = bootstrap_unknown_post_store_v1(tmp_path)
        recon = run_adversarial_reconciliation_v1(
            scenario="GET_TECHNICAL_ERROR",
            client_order_id=str(env.client_order_id),
            instrument_id=PILOT_TEST_INST,
        )
        assert recon.reconciliation_result == STILL_UNKNOWN
        assert recon.external_effect_confirmed == "false"

    def test_ur04_conflicting_reconciliation_fail_closed(self, tmp_path: Path) -> None:
        store, env = bootstrap_unknown_post_store_v1(tmp_path)
        recon = run_adversarial_reconciliation_v1(
            scenario="CONTRADICTORY_EVIDENCE",
            client_order_id=str(env.client_order_id),
            instrument_id=PILOT_TEST_INST,
        )
        assert recon.reconciliation_result == STILL_UNKNOWN

    def test_ur05_clarified_truth_without_new_submission(self, tmp_path: Path) -> None:
        store, env = bootstrap_unknown_post_store_v1(tmp_path)
        recon = run_adversarial_reconciliation_v1(
            scenario="POSITIVE_ORDER_EVIDENCE",
            client_order_id=str(env.client_order_id),
            instrument_id=PILOT_TEST_INST,
        )
        assert recon.reconciliation_result == CONFIRMED_ACCEPTED_WORKING
        payload = self._spawn_process_b_evaluate(store)
        assert payload["mock_post_attempts_after_restart"] == 0
