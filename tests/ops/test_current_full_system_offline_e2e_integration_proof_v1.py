"""Bounded CURRENT full-system offline E2E integration proof. No exchange network."""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import socket
import subprocess
from pathlib import Path
from typing import Any

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    CurrentProductiveOneShotFreshEnvelopeJoinError,
    POST_OWNER_GO,
)
from src.ops.full_core_live_path_composition_root_v1.current_full_system_offline_e2e_integration_proof_v1 import (
    CRASH_POINT_ENV_VAR,
    OfflineE2eCrashPoint,
    default_fake_post_witness_path_v1,
    load_offline_e2e_worker_result_v1,
    persist_offline_e2e_worker_input_v1,
    run_production_pre_external_to_fake_post_chain_v1,
)
from tests.ops._current_full_system_offline_e2e_test_helpers_v1 import (
    fake_k1_backend_v1,
    offline_recon_fixture_for_envelope_v1,
    pilot_get_transport_v1,
    prepare_offline_owner_authorization_for_one_shot_v1,
    run_gap_true_01_natural_enter_pre_external_v1,
)

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


def test_full_production_chain_natural_enter_pre_external_fake_post_and_recon(
    tmp_path: Path,
) -> None:
    bound, gap, origin_sha, _transport = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
    closure = gap.closure
    state_root = tmp_path / "full_chain"
    pilot_auth = prepare_offline_owner_authorization_for_one_shot_v1(
        state_root=state_root,
        closure=closure,
        origin_main_sha=origin_sha,
        bound=bound,
    )
    fixture = offline_recon_fixture_for_envelope_v1(closure)
    chain = run_production_pre_external_to_fake_post_chain_v1(
        closure=closure,
        bound_instrument=bound,
        origin_main_sha=origin_sha,
        state_root=state_root,
        read_only_get_transport=pilot_get_transport_v1(native_inst_id=str(bound.venue_native_id)),
        offline_recon_fixture=fixture,
        k1_backend=fake_k1_backend_v1(),
        post_owner_go_persisted=True,
        admission_seal_established=True,
        capital_guard_prevalidated=True,
        pilot_authorization_binding=pilot_auth,
    )
    assert chain.natural_enter_proof == "PASS"
    assert chain.pre_external_proof == "PASS"
    assert chain.fake_post_witness_count == 1
    assert chain.standing_real_exchange_counts["REAL_EXCHANGE_POST_COUNT"] == 0
    assert chain.standing_real_exchange_counts["REAL_EXCHANGE_GET_COUNT"] == 0
    assert chain.one_shot_join.http_post_attempts == 1
    assert chain.one_shot_join.durable_consumed is True
    assert chain.ghv_forward_join == "PASS"
    assert chain.reconciliation_outcome in {
        OUTCOME_CONFIRMED_OPEN,
        OUTCOME_CONFIRMED_FILLED,
    }


def test_negative_business_rejection_fake_post(tmp_path: Path) -> None:
    bound, gap, origin_sha, _ = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
    closure = gap.closure
    state_root = tmp_path / "reject"
    pilot_auth = prepare_offline_owner_authorization_for_one_shot_v1(
        state_root=state_root,
        closure=closure,
        origin_main_sha=origin_sha,
        bound=bound,
    )
    chain = run_production_pre_external_to_fake_post_chain_v1(
        closure=closure,
        bound_instrument=bound,
        origin_main_sha=origin_sha,
        state_root=state_root,
        read_only_get_transport=pilot_get_transport_v1(native_inst_id=str(bound.venue_native_id)),
        offline_recon_fixture=OfflineExchangeFixtureV1(),
        k1_backend=fake_k1_backend_v1(),
        post_owner_go_persisted=True,
        admission_seal_established=True,
        scenario=FullSystemOfflinePostScenario.CASE_B_BUSINESS_REJECTION,
        capital_guard_prevalidated=True,
        pilot_authorization_binding=pilot_auth,
    )
    assert chain.fake_post_witness_count == 1
    assert chain.one_shot_join.unknown_outcome is False


def test_negative_permit_reuse_fail_closed(tmp_path: Path) -> None:
    bound, gap, origin_sha, _transport = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
    closure = gap.closure
    state_root = tmp_path / "reuse"
    pilot_auth = prepare_offline_owner_authorization_for_one_shot_v1(
        state_root=state_root,
        closure=closure,
        origin_main_sha=origin_sha,
        bound=bound,
    )
    fixture = offline_recon_fixture_for_envelope_v1(closure)
    run_production_pre_external_to_fake_post_chain_v1(
        closure=closure,
        bound_instrument=bound,
        origin_main_sha=origin_sha,
        state_root=state_root,
        read_only_get_transport=pilot_get_transport_v1(native_inst_id=str(bound.venue_native_id)),
        offline_recon_fixture=fixture,
        k1_backend=fake_k1_backend_v1(),
        post_owner_go_persisted=True,
        admission_seal_established=True,
        capital_guard_prevalidated=True,
        pilot_authorization_binding=pilot_auth,
    )
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match="CONSUMED_PERMIT"):
        run_production_pre_external_to_fake_post_chain_v1(
            closure=closure,
            bound_instrument=bound,
            origin_main_sha=origin_sha,
            state_root=state_root,
            read_only_get_transport=pilot_get_transport_v1(
                native_inst_id=str(bound.venue_native_id)
            ),
            offline_recon_fixture=fixture,
            k1_backend=fake_k1_backend_v1(),
            post_owner_go_persisted=True,
            admission_seal_established=True,
            capital_guard_prevalidated=True,
            pilot_authorization_binding=pilot_auth,
        )
    witness = default_fake_post_witness_path_v1(state_root)
    assert witness.is_file()
    assert int(json.loads(witness.read_text())["post_attempt_count"]) == 1


def _run_crash_worker_subprocess(state_root: Path, crash: OfflineE2eCrashPoint) -> int:
    repo = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PEAK_TRADE_OFFLINE_E2E_STATE_ROOT"] = str(state_root)
    env[CRASH_POINT_ENV_VAR] = crash.value
    proc = subprocess.run(
        [
            str(repo / "scripts" / "pt"),
            "scripts/ops/run_current_full_system_offline_e2e_crash_worker_v1.py",
        ],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
    )
    return int(proc.returncode)


def test_crash_restart_no_duplicate_fake_post(tmp_path: Path) -> None:
    bound, gap, origin_sha, _transport = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
    closure = gap.closure
    state_root = tmp_path / "crash_restart"
    pilot_auth = prepare_offline_owner_authorization_for_one_shot_v1(
        state_root=state_root,
        closure=closure,
        origin_main_sha=origin_sha,
        bound=bound,
    )
    fixture = offline_recon_fixture_for_envelope_v1(closure)
    persist_offline_e2e_worker_input_v1(
        state_root=state_root,
        closure=closure,
        bound_instrument=bound,
        origin_main_sha=origin_sha,
        read_only_get_transport=None,
        offline_recon_fixture=fixture,
        k1_backend=fake_k1_backend_v1(),
        pilot_authorization_binding=pilot_auth,
    )
    rc_crash = _run_crash_worker_subprocess(state_root, OfflineE2eCrashPoint.AFTER_FAKE_POST)
    assert rc_crash == 93
    witness_count = json.loads(
        default_fake_post_witness_path_v1(state_root).read_text(encoding="utf-8")
    )["post_attempt_count"]
    assert witness_count == 1
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match="CONSUMED_PERMIT"):
        run_production_pre_external_to_fake_post_chain_v1(
            closure=closure,
            bound_instrument=bound,
            origin_main_sha=origin_sha,
            state_root=state_root,
            read_only_get_transport=pilot_get_transport_v1(
                native_inst_id=str(bound.venue_native_id)
            ),
            offline_recon_fixture=fixture,
            k1_backend=fake_k1_backend_v1(),
            post_owner_go_persisted=True,
            admission_seal_established=True,
            capital_guard_prevalidated=True,
            pilot_authorization_binding=pilot_auth,
        )
    witness_count_after = json.loads(
        default_fake_post_witness_path_v1(state_root).read_text(encoding="utf-8")
    )["post_attempt_count"]
    assert witness_count_after == 1


def test_crash_before_durable_consume_allows_single_post_after_restart(tmp_path: Path) -> None:
    bound, gap, origin_sha, _ = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
    closure = gap.closure
    state_root = tmp_path / "crash_before_consume"
    pilot_auth = prepare_offline_owner_authorization_for_one_shot_v1(
        state_root=state_root,
        closure=closure,
        origin_main_sha=origin_sha,
        bound=bound,
    )
    fixture = offline_recon_fixture_for_envelope_v1(closure)
    persist_offline_e2e_worker_input_v1(
        state_root=state_root,
        closure=closure,
        bound_instrument=bound,
        origin_main_sha=origin_sha,
        read_only_get_transport=None,
        offline_recon_fixture=fixture,
        k1_backend=fake_k1_backend_v1(),
        pilot_authorization_binding=pilot_auth,
    )
    rc = _run_crash_worker_subprocess(state_root, OfflineE2eCrashPoint.BEFORE_DURABLE_CONSUME)
    assert rc == 91
    chain = run_production_pre_external_to_fake_post_chain_v1(
        closure=closure,
        bound_instrument=bound,
        origin_main_sha=origin_sha,
        state_root=state_root,
        read_only_get_transport=pilot_get_transport_v1(native_inst_id=str(bound.venue_native_id)),
        offline_recon_fixture=fixture,
        k1_backend=fake_k1_backend_v1(),
        post_owner_go_persisted=True,
        admission_seal_established=True,
        capital_guard_prevalidated=True,
        pilot_authorization_binding=pilot_auth,
    )
    assert chain.fake_post_witness_count == 1
    worker = load_offline_e2e_worker_result_v1(state_root=state_root)
    assert worker.get("status") in {None, "PASS", ""} or worker == {}
