"""Real SIGKILL at a proven offline checkpoint; no restart of uncertain cycles."""

import json
from hashlib import sha256
import os
from pathlib import Path
import signal
import subprocess
import time

import pytest

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
    AuthorizationLifecycleLockV1,
    LifecycleLockError,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    LOCK_NAME,
    LEDGER_FILENAME,
    REASON_CONCURRENT_RUN,
)

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("stage", ["before", "during"])
def test_real_process_death_allows_only_proven_wait_checkpoint(tmp_path, stage):
    command = [
        str(REPO / "scripts/pt"),
        "-m",
        "tests.ops._continuous_crash_checkpoint_worker_v1",
        str(tmp_path),
    ]
    with (
        (tmp_path / "before.stdout").open("w") as stdout,
        (tmp_path / "before.stderr").open("w") as stderr,
    ):
        process = subprocess.Popen([*command, stage], cwd=REPO, stdout=stdout, stderr=stderr)
        try:
            deadline = time.monotonic() + 15
            marker = tmp_path / "checkpoint.json"
            while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.03)
            assert marker.exists(), (tmp_path / "before.stderr").read_text()
            # The marker is atomically published after reaching the test boundary.
            os.kill(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
            checkpoint = json.loads(marker.read_text())
            assert checkpoint["pid"] == process.pid
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
    lock = tmp_path / "shared_lock" / LOCK_NAME
    lock_before = lock.read_bytes()
    assert json.loads(lock_before)["pid"] == process.pid
    ledger = tmp_path / "before" / LEDGER_FILENAME
    ledger_before = ledger.read_bytes()
    prior = json.loads(ledger_before)
    cursor = Path(checkpoint["cursor"])
    cursor_before = cursor.read_bytes()
    epoch_before = json.loads(cursor_before)["trading_epoch"]
    # The old interrupted run remains forbidden even though its process is dead.
    refused = subprocess.run(
        [*command, "old-ledger"], cwd=REPO, capture_output=True, text=True, timeout=15
    )
    assert refused.returncode != 0
    assert "PARTIAL_CONTINUOUS_RUN_NOT_RESUMABLE" in refused.stderr
    assert lock.read_bytes() == lock_before and ledger.read_bytes() == ledger_before
    assert cursor.read_bytes() == cursor_before
    # A distinct bounded offline authorization uses a new evidence root and the
    # same state/lock roots; the stale C1 is ignored and only the fresh one runs.
    resumed = subprocess.run(
        [*command, "after"], cwd=REPO, capture_output=True, text=True, timeout=15
    )
    if stage == "during":
        assert prior["state"] == "IN_PROGRESS"
        assert resumed.returncode != 0 and REASON_CONCURRENT_RUN in resumed.stderr
        assert lock.read_bytes() == lock_before and ledger.read_bytes() == ledger_before
        assert cursor.read_bytes() == cursor_before
        assert not list(lock.parent.glob(LOCK_NAME + ".dead_process.*"))
        return
    assert resumed.returncode == 0, resumed.stderr
    result = json.loads(resumed.stdout.splitlines()[-1])
    assert result["cycles"] == 1
    assert result["accepted"] == [float(prior["last_accepted_c1"]) + 60]
    assert result["floor_before"] == float(prior["last_accepted_c1"])
    assert result["post_count"] == result["external_effect_count"] == 0
    assert result["permit_created"] is False
    assert json.loads(cursor.read_bytes())["trading_epoch"] == epoch_before + 1
    assert ledger.read_bytes() == ledger_before
    archives = list(lock.parent.glob(LOCK_NAME + ".dead_process.*"))
    assert len(archives) == 1 and archives[0].read_bytes() == lock_before
    assert not lock.exists()


@pytest.mark.parametrize("kind", ["alive", "unknown", "legacy", "foreign"])
def test_unproven_lifecycle_lock_is_preserved(tmp_path, kind):
    lock = AuthorizationLifecycleLockV1(
        tmp_path / "lock", "scope", "owner", recover_dead_local_owner=True
    )
    payload = {"writer_identity": "owner:scope", "pid": os.getpid()}
    if kind == "unknown":
        payload["pid"] = "not-a-pid"
    if kind == "legacy":
        payload.pop("writer_identity")
    if kind == "foreign":
        payload["writer_identity"] = "different"
    lock.lock_path.write_text(json.dumps(payload))
    before = lock.lock_path.read_bytes()
    with pytest.raises(LifecycleLockError):
        lock.acquire()
    lock.release()
    assert lock.lock_path.read_bytes() == before


def test_claim_loss_and_repeated_acquire_cannot_remove_another_lock(tmp_path):
    lock = AuthorizationLifecycleLockV1(
        tmp_path / "lock", "scope", "owner", recover_dead_local_owner=True
    )
    lock.acquire()
    with pytest.raises(LifecycleLockError):
        lock.acquire()
    lock.assert_held()
    payload = json.loads(lock.lock_path.read_text())
    payload["claim_id"] = "other-claim"
    lock.lock_path.write_text(json.dumps(payload))
    before = lock.lock_path.read_bytes()
    with pytest.raises(LifecycleLockError):
        lock.assert_held()
    lock.release()
    assert lock.lock_path.read_bytes() == before


def test_generic_authorization_lock_keeps_strict_default(tmp_path):
    lock = AuthorizationLifecycleLockV1(tmp_path / "lock", "scope", "owner")
    assert lock.recover_dead_local_owner is False
    lock.lock_path.write_text(
        json.dumps({"pid": 999999999, "owner": "owner", "authorization_id": "scope"})
    )
    before = lock.lock_path.read_bytes()
    with pytest.raises(LifecycleLockError):
        lock.acquire()
    assert lock.lock_path.read_bytes() == before
    assert not list(tmp_path.glob("*.dead_process.*"))


@pytest.mark.parametrize(
    "change",
    ["none", "state", "binding", "native", "effect", "cursor", "missing_context", "missing_cursor"],
)
def test_dead_owner_checkpoint_binding_is_required(tmp_path, change):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_governed_continuous_cycle_orchestrator_v1 as owner,
    )

    # Technical checkpoint binding only; strategy/cursor semantics are still
    # validated by the existing consumer when a new run attempts processing.
    cursor_root = tmp_path / "cursor"
    cursor_root.mkdir()
    cursor = cursor_root / owner.CURSOR_FILENAME
    cursor.write_text('{"fixture": "checkpoint"}')
    root = tmp_path / "evidence"
    root.mkdir()
    ledger = {
        "state": owner.STATE_WAITING_FOR_NEXT_C1,
        "binding_digest": "prior-binding",
        "native_id": "TEST-SWAP",
        "continuous_owner_go": owner.RUNTIME_OWNER_GO,
        "POST_COUNT": "0",
        "PERMIT_CREATED": owner.FALSE_TOKEN,
        "EXTERNAL_EFFECT_COUNT": "0",
        "consumed_instance_ids": ["prior-cycle"],
        "s5_invoke_count": 1,
        "checkpoint_cursor_sha256": sha256(cursor.read_bytes()).hexdigest(),
    }
    receipt = {
        "recovery_context": {
            "evidence_root": str(root),
            "cursor_store_root": str(cursor_root.resolve()),
            "binding_digest": "prior-binding",
        }
    }
    if change == "state":
        ledger["state"] = owner.STATE_IN_PROGRESS
    elif change == "binding":
        ledger["binding_digest"] = "other-binding"
    elif change == "native":
        ledger["native_id"] = "OTHER-SWAP"
    elif change == "effect":
        ledger["EXTERNAL_EFFECT_COUNT"] = "1"
    elif change == "cursor":
        cursor.write_text('{"fixture": "changed"}')
    elif change == "missing_context":
        receipt = {}
    elif change == "missing_cursor":
        cursor.unlink()
    ledger_path = root / owner.LEDGER_FILENAME
    ledger_path.write_text(json.dumps(ledger))
    before = ledger_path.read_bytes()
    assert owner._dead_owner_wait_checkpoint_proven_v1(
        receipt, cursor_store_root=cursor_root, native_id="TEST-SWAP"
    ) is (change == "none")
    assert ledger_path.read_bytes() == before
