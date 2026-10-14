"""Bounded CURRENT full-system offline E2E integration proof. No exchange network."""

from __future__ import annotations

import multiprocessing as mp
import socket
from pathlib import Path
from typing import Any

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_full_system_offline_e2e_integration_proof_v1 import (
    FAKE_EXCHANGE_TRANSPORT_CLASS,
    INTEGRATION_GAP_CLASSIFICATIONS_V1,
    IntegrationGapClassification,
    FullSystemOfflinePostScenario,
    run_current_full_system_offline_e2e_integration_proof_v1,
    standing_real_exchange_counts_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_FILLED,
    OUTCOME_CONFIRMED_OPEN,
    OUTCOME_HALTED_UNRESOLVED,
)
from src.ops.full_core_live_path_composition_root_v1.current_full_system_offline_e2e_integration_proof_v1 import (
    run_pre_external_capital_guard_phase_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 import (
    CycleSubmitInjectionKind,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    NETWORK_REQUEST_COUNT,
    POST_COUNT,
    PRIVATE_GET_COUNT,
)
from tests.ops.test_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 import (
    _ack_post,
    _cycle,
    _envelope,
    _handoff,
    _order_row_join,
    _origin_main,
)
from tests.ops.test_full_core_exchange_reconciliation_v1 import CL
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)


@pytest.fixture(autouse=True)
def _forbid_real_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("NETWORK_FORBIDDEN")

    monkeypatch.setattr(socket, "create_connection", _boom)
    monkeypatch.setattr(socket.socket, "connect", _boom)


def test_gap_registry_documents_boundary_audit() -> None:
    assert (
        INTEGRATION_GAP_CLASSIFICATIONS_V1["GAP_06_DISABLED_LIFECYCLE_HOOKS_DEFAULT"]
        is IntegrationGapClassification.INTENTIONAL_SAFETY_BOUNDARY
    )
    assert (
        INTEGRATION_GAP_CLASSIFICATIONS_V1["GAP_LIVE_PRODUCTIVE_OKX_POST"]
        is IntegrationGapClassification.EXTERNAL_LIVE_VALIDATION_ONLY
    )


def test_standing_real_exchange_counts_zero() -> None:
    counts = standing_real_exchange_counts_v1()
    assert counts["REAL_EXCHANGE_POST_COUNT"] == 0
    assert counts["REAL_EXCHANGE_GET_COUNT"] == 0
    assert POST_COUNT == 0
    assert PRIVATE_GET_COUNT == 0
    assert NETWORK_REQUEST_COUNT == 0


@pytest.mark.parametrize(
    "scenario,submit_kind",
    [
        (FullSystemOfflinePostScenario.CASE_A_EXCHANGE_ACCEPTANCE, "ACK"),
        (FullSystemOfflinePostScenario.CASE_B_BUSINESS_REJECTION, "REJECT"),
        (FullSystemOfflinePostScenario.CASE_C_POST_TIMEOUT, "TIMEOUT"),
        (FullSystemOfflinePostScenario.CASE_N_RESTART_UNKNOWN_EXTERNAL, "UNKNOWN"),
    ],
)
def test_downstream_pre_external_lifecycle_join_offline(
    tmp_path: Path,
    scenario: FullSystemOfflinePostScenario,
    submit_kind: str,
) -> None:
    sha = _origin_main()
    env = _envelope()
    fixture: OfflineExchangeFixtureV1 | None = None
    post = None
    if submit_kind == "ACK":
        fixture = OfflineExchangeFixtureV1(pending_orders={"data": [_order_row_join(state="live")]})
        post = _ack_post()
    elif submit_kind == "REJECT":
        fixture = OfflineExchangeFixtureV1()
        post = None
    else:
        fixture = OfflineExchangeFixtureV1()
    proof = run_current_full_system_offline_e2e_integration_proof_v1(
        cycle=_cycle(envelope=env),
        handoff=_handoff(sha=sha),
        state_root=tmp_path / scenario.value,
        scenario=scenario,
        offline_fixture=fixture,
        injected_ack_post=post,
        apply_durable_atomic_state=submit_kind in {"UNKNOWN", "TIMEOUT"},
    )
    assert proof.capital_guard_allowed is True
    assert proof.lifecycle_wiring is not None
    assert proof.lifecycle_wiring.lifecycle is not None
    assert proof.standing_real_exchange_counts["REAL_EXCHANGE_POST_COUNT"] == 0
    assert proof.fake_post_witness_count == 0
    if submit_kind == "ACK":
        assert proof.lifecycle_wiring.lifecycle.reconciliation.decision.outcome == (
            OUTCOME_CONFIRMED_OPEN
        )
        assert proof.ghv_forward_join == "PASS"
        assert proof.ghv_reverse_join == "PASS"
    if submit_kind in {"UNKNOWN", "TIMEOUT"}:
        assert (
            proof.lifecycle_wiring.lifecycle.reconciliation.decision.outcome
            == OUTCOME_HALTED_UNRESOLVED
        )


def test_happy_path_ack_durable_atomic(tmp_path: Path) -> None:
    sha = _origin_main()
    env = _envelope()
    fixture = OfflineExchangeFixtureV1(
        order_history={"data": [_order_row_join(state="filled", acc="1")]}
    )
    proof = run_current_full_system_offline_e2e_integration_proof_v1(
        cycle=_cycle(envelope=env),
        handoff=_handoff(sha=sha),
        state_root=tmp_path,
        scenario=FullSystemOfflinePostScenario.CASE_A_EXCHANGE_ACCEPTANCE,
        offline_fixture=fixture,
        injected_ack_post=_ack_post(),
        apply_durable_atomic_state=True,
    )
    assert proof.lifecycle_wiring is not None
    lifecycle = proof.lifecycle_wiring.lifecycle
    assert lifecycle is not None
    assert lifecycle.reconciliation.decision.outcome in {
        OUTCOME_CONFIRMED_OPEN,
        OUTCOME_CONFIRMED_FILLED,
    }


def test_pre_external_capital_guard_phase_isolated(tmp_path: Path) -> None:
    sha = _origin_main()
    env = _envelope()
    guard = run_pre_external_capital_guard_phase_v1(
        cycle=_cycle(envelope=env),
        handoff=_handoff(sha=sha),
        atomic_state_dir=tmp_path / "guard-only",
    )
    assert guard.guard_allowed is True
    assert guard.guard_blocked is False


def _spawn_proof_worker(state_dir: str, origin_sha: str) -> dict[str, Any]:
    env = _envelope()
    proof = run_current_full_system_offline_e2e_integration_proof_v1(
        cycle=_cycle(envelope=env),
        handoff=_handoff(sha=origin_sha),
        state_root=Path(state_dir),
        scenario=FullSystemOfflinePostScenario.CASE_N_RESTART_UNKNOWN_EXTERNAL,
        apply_durable_atomic_state=True,
    )
    return {
        "outcome": proof.lifecycle_wiring.lifecycle.reconciliation.decision.outcome
        if proof.lifecycle_wiring and proof.lifecycle_wiring.lifecycle
        else "",
        "fake_post_count": proof.fake_post_witness_count,
        "real_post": proof.standing_real_exchange_counts["REAL_EXCHANGE_POST_COUNT"],
    }


def test_multiprocess_restart_unknown_consistent_outcome(tmp_path: Path) -> None:
    sha = _origin_main()
    ctx = mp.get_context("spawn")
    with ctx.Pool(2) as pool:
        results = pool.starmap(
            _spawn_proof_worker,
            [(str(tmp_path / "a"), sha), (str(tmp_path / "b"), sha)],
        )
    assert results[0]["outcome"] == results[1]["outcome"]
    assert results[0]["outcome"] == OUTCOME_HALTED_UNRESOLVED
    for row in results:
        assert row["fake_post_count"] == 0
        assert row["real_post"] == 0


def test_adversarial_permit_reuse_and_duplicate_paths_use_existing_kinds() -> None:
    assert CycleSubmitInjectionKind.ACKNOWLEDGED.value == "ACKNOWLEDGED"
    assert FullSystemOfflinePostScenario.CASE_K_PERMIT_REUSE.value.startswith("CASE_K")


def test_ssot_docs_once_present() -> None:
    from tests.ops.test_full_core_post_response_to_ack_mapper_and_lifecycle_join_v1 import (
        test_ssot_docs_once_present as _mapper_ssot,
    )

    _mapper_ssot()

