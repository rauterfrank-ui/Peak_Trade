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
    APPLY_DURABLE_ATOMIC_ENV_VAR,
    CRASH_POINT_ENV_VAR,
    FakeExchangeTransportWitnessV1,
    OfflineE2eCrashPoint,
    default_fake_post_witness_path_v1,
    load_offline_e2e_worker_result_v1,
    persist_offline_e2e_worker_input_v1,
    format_pretrade_reference_mark_px_v1,
    load_offline_e2e_natural_enter_full_core_guard_config_v1,
    build_governed_cycle_from_pre_external_closure_v1,
    build_handoff_from_pre_external_closure_v1,
    run_pre_external_capital_guard_phase_v1,
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
    CurrentFullSystemOfflineE2eIntegrationProofError,
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


def test_capital_guard_prevalidated_requires_pilot_binding_provenance(
    tmp_path: Path,
) -> None:
    bound, gap, origin_sha, _, _mark_px = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
    closure = gap.closure
    state_root = tmp_path / "no_pilot_binding"
    prepare_offline_owner_authorization_for_one_shot_v1(
        state_root=state_root,
        closure=closure,
        origin_main_sha=origin_sha,
        bound=bound,
    )
    fixture = offline_recon_fixture_for_envelope_v1(closure)
    with pytest.raises(
        CurrentFullSystemOfflineE2eIntegrationProofError,
        match="PILOT_CAPITAL_GUARD_PROVENANCE_REQUIRED",
    ):
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
            pilot_authorization_binding=None,
        )


def test_gap_registry_documents_boundary_audit() -> None:
    assert (
        INTEGRATION_GAP_CLASSIFICATIONS_V1["GAP_06_DISABLED_LIFECYCLE_HOOKS_DEFAULT"]
        is IntegrationGapClassification.INTENTIONAL_SAFETY_BOUNDARY
    )
    assert (
        INTEGRATION_GAP_CLASSIFICATIONS_V1["GAP_LIVE_PRODUCTIVE_OKX_POST"]
        is IntegrationGapClassification.EXTERNAL_LIVE_VALIDATION_ONLY
    )
    assert (
        INTEGRATION_GAP_CLASSIFICATIONS_V1[
            "GAP_03_CAPITAL_GUARD_RESERVATION_ENVELOPE_PERMIT_IDENTITY"
        ]
        is IntegrationGapClassification.ALREADY_IMPLEMENTED_AND_PROVEN
    )
    assert (
        INTEGRATION_GAP_CLASSIFICATIONS_V1["GAP_05_ATOMIC_DURABLE_CRASH_RECOVERY"]
        is IntegrationGapClassification.ALREADY_IMPLEMENTED_AND_PROVEN
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
    bound, gap, origin_sha, _transport, _mark_px = run_gap_true_01_natural_enter_pre_external_v1(
        tmp_path
    )
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
    assert chain.ghv_reverse_join == "PASS"
    assert chain.ghv_reverse_join == chain.one_shot_join.dw_exchange_reconciliation_ghv_reverse_join
    assert chain.reconciliation_outcome in {
        OUTCOME_CONFIRMED_OPEN,
        OUTCOME_CONFIRMED_FILLED,
    }


def test_negative_business_rejection_fake_post(tmp_path: Path) -> None:
    bound, gap, origin_sha, _, _mark_px = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
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
    bound, gap, origin_sha, _transport, _mark_px = run_gap_true_01_natural_enter_pre_external_v1(
        tmp_path
    )
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


def test_fake_exchange_transport_witness_is_mutable_and_persists_attempts(
    tmp_path: Path,
) -> None:
    witness_path = tmp_path / "witness.json"
    witness = FakeExchangeTransportWitnessV1(witness_path=witness_path)
    witness.record_post_attempt_v1()
    assert witness.post_attempt_count == 1
    loaded = FakeExchangeTransportWitnessV1.load_v1(witness_path)
    assert loaded.post_attempt_count == 1


def _run_crash_worker_subprocess(
    state_root: Path,
    crash: OfflineE2eCrashPoint,
    *,
    extra_env: dict[str, str] | None = None,
) -> int:
    repo = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PEAK_TRADE_OFFLINE_E2E_STATE_ROOT"] = str(state_root)
    env[CRASH_POINT_ENV_VAR] = crash.value
    if extra_env:
        env.update(extra_env)
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
    bound, gap, origin_sha, _transport, _mark_px = run_gap_true_01_natural_enter_pre_external_v1(
        tmp_path
    )
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
    bound, gap, origin_sha, _, _mark_px = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
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


def test_crash_before_recon_complete_exits_94(tmp_path: Path) -> None:
    bound, gap, origin_sha, _, _mark_px = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
    closure = gap.closure
    state_root = tmp_path / "crash_before_recon"
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
    rc = _run_crash_worker_subprocess(state_root, OfflineE2eCrashPoint.BEFORE_RECON_COMPLETE)
    assert rc == 94
    worker = load_offline_e2e_worker_result_v1(state_root=state_root)
    assert worker.get("status") != "PASS"


def test_gap_03_full_core_capital_guard_production_chain_positive(tmp_path: Path) -> None:
    bound, gap, origin_sha, _, mark_px = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
    closure = gap.closure
    ref_mark = format_pretrade_reference_mark_px_v1(mark_px)
    state_root = tmp_path / "gap_03_full_core_guard"
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
        capital_guard_prevalidated=False,
        pilot_authorization_binding=pilot_auth,
        pretrade_reference_mark_px=ref_mark,
    )
    e2e_guard_cfg = load_offline_e2e_natural_enter_full_core_guard_config_v1()
    assert chain.full_core_capital_guard_invoked is True
    assert chain.full_core_capital_guard_join_mode == "OFFLINE_STUB"
    assert chain.full_core_capital_guard_binding_digest
    assert chain.capital_guard_allowed is True
    guard_state_files = list((state_root / "atomic" / "capital_guard").glob("*.state.json"))
    assert guard_state_files
    guard_state = json.loads(guard_state_files[0].read_text(encoding="utf-8"))
    assert (
        str(guard_state["binding"]["guard_config_digest"]).lower()
        == str(e2e_guard_cfg.config_digest).lower()
    )
    assert chain.fake_post_witness_count == 1
    assert closure.current_productive_decision_result == "EXECUTABLE_VENUE_PLAN_BOUND"


def test_gap_03_full_core_capital_guard_blocks_without_reference_mark(tmp_path: Path) -> None:
    bound, gap, origin_sha, _, _mark_px = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
    closure = gap.closure
    state_root = tmp_path / "gap_03_guard_block"
    pilot_auth = prepare_offline_owner_authorization_for_one_shot_v1(
        state_root=state_root,
        closure=closure,
        origin_main_sha=origin_sha,
        bound=bound,
    )
    fixture = offline_recon_fixture_for_envelope_v1(closure)
    with pytest.raises(
        CurrentFullSystemOfflineE2eIntegrationProofError,
        match="CAPITAL_GUARD_BLOCKED",
    ):
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
            capital_guard_prevalidated=False,
            pilot_authorization_binding=pilot_auth,
            pretrade_reference_mark_px=None,
        )


def test_gap_03_guard_config_digest_mismatch_blocks_false_pass(tmp_path: Path) -> None:
    from dataclasses import replace

    from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
        load_full_core_capital_guard_config_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_full_system_offline_e2e_integration_proof_v1 import (
        _build_join_binding_from_cycle_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
        FullCoreCapitalGuardJoinMode,
        run_full_core_pre_post_capital_guard_join_v1,
    )

    bound, gap, origin_sha, _, mark_px = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
    ref_mark = format_pretrade_reference_mark_px_v1(mark_px)
    cycle = build_governed_cycle_from_pre_external_closure_v1(gap.closure)
    handoff = build_handoff_from_pre_external_closure_v1(
        closure=gap.closure,
        bound_instrument=bound,
        origin_main_sha=origin_sha,
        reference_mark_px=ref_mark,
    )
    join_binding = _build_join_binding_from_cycle_v1(cycle=cycle, handoff=handoff)
    production_digest = load_full_core_capital_guard_config_v1().config_digest
    assert join_binding.guard_config_digest == production_digest
    e2e_cfg = load_offline_e2e_natural_enter_full_core_guard_config_v1()
    assert e2e_cfg.config_digest != production_digest
    envelope = cycle.final_order_envelope
    assert envelope is not None
    result = run_full_core_pre_post_capital_guard_join_v1(
        binding=join_binding,
        envelope=envelope,
        join_mode=FullCoreCapitalGuardJoinMode.OFFLINE_STUB,
        margin_evidence=None,
        exposure_evidence=None,
        atomic_state_dir=tmp_path / "digest_mismatch",
        session_id="gap-03-digest-mismatch",
        pretrade_reference_mark_px=ref_mark,
        guard_config=e2e_cfg,
    )
    assert result.guard_blocked is True
    assert "GUARD_CONFIG_DIGEST_MISMATCH" in result.reasons

    rebound = replace(
        join_binding,
        guard_config_digest=str(e2e_cfg.config_digest).strip().lower(),
    )
    allowed = run_pre_external_capital_guard_phase_v1(
        cycle=cycle,
        handoff=handoff,
        atomic_state_dir=tmp_path / "digest_bound",
    )
    assert allowed.guard_allowed is True
    assert allowed.guard_blocked is False
    assert rebound.guard_config_digest == str(e2e_cfg.config_digest).lower()


def test_gap_05_atomic_durable_apply_isolated_state(tmp_path: Path) -> None:
    from tests.ops.test_full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
        test_orchestrator_offline_unknown_restart_recovery,
    )

    bound, gap, origin_sha, _, mark_px = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
    closure = gap.closure
    ref_mark = format_pretrade_reference_mark_px_v1(mark_px)
    state_root = tmp_path / "gap_05_atomic"
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
        capital_guard_prevalidated=False,
        pilot_authorization_binding=pilot_auth,
        pretrade_reference_mark_px=ref_mark,
        apply_durable_atomic_state=True,
    )
    assert chain.apply_durable_atomic_state is True
    assert chain.standing_real_exchange_counts["REAL_EXCHANGE_POST_COUNT"] == 0
    assert chain.one_shot_join.dw_exchange_reconciliation_invoked is True
    guard_atomic = list((state_root / "atomic" / "capital_guard").glob("*.state.json"))
    recon_atomic = list((state_root / "atomic" / "recon").glob("*"))
    assert guard_atomic
    assert recon_atomic
    test_orchestrator_offline_unknown_restart_recovery(tmp_path / "gap_05_orchestrator_reproof")


def test_gap_05_crash_before_durable_consume_atomic_restart_single_post(tmp_path: Path) -> None:
    """Crash before external-effect durable consume; restart completes one fake POST.

    First segment runs full-core capital guard (single-use authorization). Restart
    uses pilot prevalidated provenance only — guard was already consumed pre-crash.
    """

    bound, gap, origin_sha, _, mark_px = run_gap_true_01_natural_enter_pre_external_v1(tmp_path)
    closure = gap.closure
    ref_mark = format_pretrade_reference_mark_px_v1(mark_px)
    state_root = tmp_path / "gap_05_crash_atomic"
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
        pretrade_reference_mark_px=ref_mark,
    )
    rc_crash = _run_crash_worker_subprocess(
        state_root,
        OfflineE2eCrashPoint.BEFORE_DURABLE_CONSUME,
        extra_env={
            APPLY_DURABLE_ATOMIC_ENV_VAR: "true",
            "PEAK_TRADE_OFFLINE_E2E_USE_FULL_CORE_CAPITAL_GUARD": "true",
        },
    )
    assert rc_crash == 91
    rc_restart = _run_crash_worker_subprocess(
        state_root,
        OfflineE2eCrashPoint.NONE,
        extra_env={
            APPLY_DURABLE_ATOMIC_ENV_VAR: "true",
        },
    )
    assert rc_restart == 0
    witness_count = json.loads(
        default_fake_post_witness_path_v1(state_root).read_text(encoding="utf-8")
    )["post_attempt_count"]
    assert witness_count == 1
