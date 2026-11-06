"""Offline process recovery of the existing internal reservation owner."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import signal
import sqlite3
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    PortfolioCapitalBudgetError,
    ReserveDispositionV1 as D,
    ReleaseReasonV1,
    observation_identity_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
    DurableBudgetStoreError,
    digest,
)
from src.ops.portfolio_capital_reservation_budget_v1.recovery_v1 import (
    reconcile_durable_budget_startup_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    PORTFOLIO_STATE_FILENAME,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import _produce, ACCOUNT

REPO = Path(__file__).resolve().parents[2]
EPOCH = "2026-11-03T12:00:00Z"
NOW = datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp()
BOUND = BoundInstrumentV1(
    instrument_id="ETH-USD-PERP",
    venue_native_id="ETH-USDC-SWAP",
    ranking_snapshot_id="ranking-1",
    ranking_integrity_digest="a" * 64,
    universe_snapshot_id="universe-1",
    selection_id="selection-1",
    selection_integrity_digest="b" * 64,
    selection_state="SELECTED",
)
BINDINGS = {"LANE_1": BOUND}


def _owner(root, mode="create", **kwargs):
    return Owner(
        durable_root=root / "budget",
        durable_account_identity=ACCOUNT,
        durable_mode=mode,
        durable_lane_bindings=BINDINGS,
        **kwargs,
    )


def _observed(quantity="0"):
    return PortfolioTruthSnapshotV1(
        positions=()
        if quantity == "0"
        else (
            PositionTruthV1.from_signed(
                instrument_id=BOUND.instrument_id,
                signed_quantity=quantity,
                source_id="synthetic-account-bound-port",
                event_time_unix=NOW,
                wall_time_unix=NOW,
            ),
        ),
        source_id="synthetic-account-bound-port",
        event_time_unix=NOW,
        wall_time_unix=NOW,
        max_age_seconds=5,
    )


def _auto(owner, root, *, output=None, observed=None, bindings=None, now=NOW):
    observed = observed if observed is not None else _observed()
    recon_root = root / "reconciliation"
    if not recon_root.exists():
        recon_root.mkdir()
        # Synthetic persisted truth for the real existing startup gate.
        (recon_root / PORTFOLIO_STATE_FILENAME).write_text(json.dumps(observed.to_dict()))
    return reconcile_durable_budget_startup_v1(
        owner,
        output=output if output is not None else _produce(epoch=EPOCH),
        observed=observed,
        lane_bindings=bindings if bindings is not None else BINDINGS,
        reconciliation_state_root=recon_root,
        session_id="offline-durable-recovery",
        repository_sha="242b7974fc93f0bdb47706556101bd6f0c497414",
        now_unix=now,
        capital_max_age_seconds=5,
    )


def _reserve(owner, amount="60", decision="enter-1", observation=None):
    return owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id=decision,
        cycle_id="cycle-1",
        observation_id=observation or owner.budget_state_v1().observation_id,
        amount=Decimal(amount),
    )


def _seed(root):
    owner = _owner(root)
    assert _auto(owner, root).disposition is D.ADMITTED
    held = _reserve(owner)
    assert held.disposition is D.ADMITTED
    owner.commit_internal_pre_external_effect_v1(str(held.reservation.reservation_id))
    return owner, held.reservation


def test_fresh_and_restarted_owner_use_automatic_gate_and_keep_holds(tmp_path):
    owner, held = _seed(tmp_path)
    owner.close()
    owner = _owner(tmp_path, "recover")
    try:
        state = owner.budget_state_v1()
        assert not state.admitted and state.recovery_required
        assert state.active_reservation_sum == 60 and state.remaining_unreserved == 0
        assert owner.invariant_holds_v1()
        assert (
            owner.bind_canonical_producer_output_v1(_produce(epoch=EPOCH)).disposition
            is D.FAIL_CLOSED
        )
        assert owner.release_plan_failure_v1(str(held.reservation_id)).disposition is D.FAIL_CLOSED
        assert _auto(owner, tmp_path).disposition is D.ADMITTED
        assert owner.budget_state_v1().remaining_unreserved == 40
        assert _reserve(owner).disposition is D.IDEMPOTENT_REPLAY
        assert _reserve(owner, "50", "new-oversized").disposition is D.DENIED
        assert _reserve(owner, "30", "new-allowed").disposition is D.ADMITTED
        assert owner.active_sum_v1() == 90
    finally:
        owner.close()


def test_observation_refresh_never_expires_or_duplicates_durable_holds(tmp_path):
    owner, held = _seed(tmp_path)
    try:
        new = _produce(epoch="2026-11-03T12:00:01Z")
        assert owner.bind_canonical_producer_output_v1(new).disposition is D.ADMITTED
        assert owner.active_sum_v1() == 60
        assert _reserve(owner).disposition is D.IDEMPOTENT_REPLAY
        assert owner.stored_reservation_count_v1() == 1
        owner.restart_fail_closed_v1()
        assert owner.active_sum_v1() == 60
        assert _auto(owner, tmp_path).disposition is D.ADMITTED
        owner.release_plan_failure_v1(str(held.reservation_id))
    finally:
        owner.close()
    owner = _owner(tmp_path, "recover")
    try:
        assert _auto(owner, tmp_path).disposition is D.ADMITTED
        assert owner.active_sum_v1() == 0
        assert _reserve(owner).disposition is D.FAIL_CLOSED
        assert owner.active_sum_v1() == 0
    finally:
        owner.close()


@pytest.mark.parametrize(
    "fault",
    [
        "stale_capital",
        "stale_portfolio",
        "account",
        "generation",
        "too_small",
        "unknown_instrument",
        "missing",
        "venue",
        "mode",
    ],
)
def test_blocked_recovery_retains_holds_and_fresh_facts_recover_without_operator(tmp_path, fault):
    owner, held = _seed(tmp_path)
    owner.close()
    owner = _owner(tmp_path, "recover")
    kwargs = {}
    if fault == "stale_capital":
        kwargs["output"] = _produce(epoch="2026-11-03T11:59:00Z")
    elif fault == "stale_portfolio":
        kwargs["observed"] = replace(_observed(), event_time_unix=NOW - 60)
    elif fault == "account":
        kwargs["output"] = replace(_produce(epoch=EPOCH), bound_account_identity="other-account")
    elif fault == "venue":
        kwargs["output"] = replace(_produce(epoch=EPOCH), bound_venue_identity="foreign-venue")
    elif fault == "mode":
        kwargs["output"] = replace(_produce(epoch=EPOCH), bound_td_mode="isolated")
    elif fault == "generation":
        kwargs["bindings"] = {"LANE_1": replace(BOUND, selection_id="new-generation")}
    elif fault == "too_small":
        kwargs["output"] = _produce(value="50", epoch=EPOCH)
    elif fault == "unknown_instrument":
        kwargs["observed"] = replace(
            _observed(),
            positions=(PositionTruthV1.from_signed(instrument_id="FOREIGN", signed_quantity="1"),),
        )
    else:
        kwargs["observed"] = replace(_observed(), missing=True)
    try:
        assert _auto(owner, tmp_path, **kwargs).disposition is D.FAIL_CLOSED
        assert owner.active_sum_v1() == 60
        assert not owner.budget_state_v1().admitted
        assert _auto(owner, tmp_path).disposition is D.ADMITTED
        assert owner.budget_state_v1().remaining_unreserved == 40
    finally:
        owner.close()


def test_missing_foreign_and_concurrent_store_are_rejected(tmp_path):
    with pytest.raises(DurableBudgetStoreError, match="STATE_MISSING"):
        _owner(tmp_path, "recover")
    owner, _ = _seed(tmp_path)
    try:
        with pytest.raises(DurableBudgetStoreError):
            _owner(tmp_path, "recover")
    finally:
        owner.close()
    with pytest.raises(DurableBudgetStoreError, match="ALREADY_EXISTS"):
        _owner(tmp_path)
    with pytest.raises(DurableBudgetStoreError, match="IDENTITY_MISMATCH"):
        Owner(
            durable_root=tmp_path / "budget",
            durable_account_identity="foreign",
            durable_mode="recover",
            durable_lane_bindings=BINDINGS,
        )


@pytest.mark.parametrize("valid_hash", [False, True])
def test_corrupt_history_or_semantically_invalid_record_is_rejected(tmp_path, valid_hash):
    owner, _ = _seed(tmp_path)
    owner.close()
    with sqlite3.connect(tmp_path / "budget/reservations.sqlite3") as connection:
        seq, prior, checksum, body = connection.execute(
            "SELECT * FROM states ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        payload = json.loads(body)
        payload["reservations"][0]["amount"] = "-60"
        if valid_hash:
            checksum = digest({"seq": seq, "previous": prior, "state": payload})
        connection.execute(
            "UPDATE states SET digest=?, payload=? WHERE seq=?",
            (checksum, json.dumps(payload), seq),
        )
    with pytest.raises((DurableBudgetStoreError, PortfolioCapitalBudgetError)):
        _owner(tmp_path, "recover")


def test_failed_persistence_fences_writer_and_reopen_uses_last_committed_state(
    tmp_path, monkeypatch
):
    owner, _ = _seed(tmp_path)

    def fail(state):
        raise OSError("synthetic disk failure")

    monkeypatch.setattr(owner._store, "save", fail)
    with pytest.raises(PortfolioCapitalBudgetError, match="COMMIT_UNPROVEN"):
        _reserve(owner, "10", "not-committed")
    assert not owner.budget_state_v1().admitted
    assert _auto(owner, tmp_path).disposition is D.FAIL_CLOSED
    owner.close()
    owner = _owner(tmp_path, "recover")
    try:
        assert _auto(owner, tmp_path).disposition is D.ADMITTED
        assert owner.active_sum_v1() == 60
    finally:
        owner.close()


def test_verified_flat_refresh_and_close_replay_marker_survive_restart(tmp_path):
    owner, held = _seed(tmp_path)
    output = _produce(epoch="2026-11-03T12:00:01Z")
    kwargs = dict(
        output=output,
        slot_id="LANE_1",
        reservation_ids=(str(held.reservation_id),),
        expected_observation_id=held.observation_id,
        account_identity=ACCOUNT,
        close_evidence_ref="c" * 64,
    )
    assert owner.refresh_after_reconciled_flat_v1(**kwargs).disposition is D.ADMITTED
    owner.close()
    owner = _owner(tmp_path, "recover")
    try:
        assert _auto(owner, tmp_path, output=output, now=NOW + 1).disposition is D.ADMITTED
        assert owner.refresh_after_reconciled_flat_v1(**kwargs).disposition is D.IDEMPOTENT_REPLAY
        assert owner.active_sum_v1() == 0
    finally:
        owner.close()


def test_unknown_observation_or_slot_cannot_replay_a_hold(tmp_path):
    owner, _ = _seed(tmp_path)
    try:
        assert _reserve(owner, observation="f" * 64).disposition is D.FAIL_CLOSED
        assert not owner.slot_account_binding_matches_v1(
            slot_id="LANE_1", instrument_id="FOREIGN", account_identity=ACCOUNT
        )
        assert (
            owner.try_reserve_v1(
                slot_id="LANE_2",
                decision_id="new",
                cycle_id="cycle",
                observation_id=owner.budget_state_v1().observation_id,
                amount=Decimal(1),
            ).disposition
            is D.FAIL_CLOSED
        )
        assert owner.active_sum_v1() == 60
    finally:
        owner.close()


def test_parallel_reservations_cannot_overspend_and_replay_matches_disk(tmp_path):
    owner, _ = _seed(tmp_path)
    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda n: _reserve(owner, "10", f"parallel-{n}"), range(8)))
        assert sum(r.disposition is D.ADMITTED for r in results) == 4
        assert owner.active_sum_v1() == 100
    finally:
        owner.close()
    owner = _owner(tmp_path, "recover")
    try:
        assert _auto(owner, tmp_path).disposition is D.ADMITTED
        assert owner.active_sum_v1() == 100
        assert owner.budget_state_v1().remaining_unreserved == 0
    finally:
        owner.close()


@pytest.mark.parametrize(
    "phase,quantity,expected",
    [
        ("held", "1", "60"),
        ("held", "-2", "60"),
        ("before_commit", "0", "60"),
        ("after_commit", "0", "70"),
    ],
)
def test_sigkill_and_fresh_process_recover_committed_history(tmp_path, phase, quantity, expected):
    command = [
        str(REPO / "scripts/pt"),
        "-m",
        "tests.ops._durable_budget_crash_worker_v1",
        str(tmp_path),
    ]
    marker = tmp_path / "checkpoint"
    with (tmp_path / "stdout").open("w") as out, (tmp_path / "stderr").open("w") as err:
        process = subprocess.Popen([*command, phase, quantity], cwd=REPO, stdout=out, stderr=err)
        try:
            deadline = time.monotonic() + 20
            while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.03)
            assert marker.exists(), (tmp_path / "stderr").read_text()
            process.send_signal(signal.SIGKILL)
            process.wait(timeout=5)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
    after = subprocess.run(
        [*command, "recover", quantity], cwd=REPO, capture_output=True, text=True, timeout=20
    )
    assert after.returncode == 0, after.stdout + after.stderr
    result = json.loads(after.stdout.splitlines()[-1])
    assert result["held_before_reconciliation"] == expected
    assert result["admitted_before_reconciliation"] is False
    assert result["admitted_after_automatic_reconciliation"] is True
    assert result["held_after"] == expected
    assert result["remaining"] == str(Decimal("100.00") - Decimal(expected))
    if phase == "after_commit":
        assert result["retry_disposition"] == "IDEMPOTENT_REPLAY"
    elif phase == "before_commit":
        assert result["retry_disposition"] == "ADMITTED"
