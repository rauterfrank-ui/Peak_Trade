"""Transfer one expired occupied BREV WAIT to a signed simulation window."""

from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import fcntl
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sqlite3
import time
from types import SimpleNamespace
from typing import Callable
from uuid import uuid4

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    canonical_json_dumps,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    CAP24_PUBLISH_MANIFEST_FILENAME,
    CurrentProductive29PCap24ProvenanceHandoffError,
    inspect_selection_v1,
)
from src.ops.n1_occupied_scope_recovery_v2 import runtime as v2


OWNER = "n1_brev_offline_window_v1"
SCHEMA = "peaktrade.n1_brev_offline_window_grant.v1"


@dataclass(frozen=True)
class OfflineWindowTrust:
    """Explicit simulation authority supplied by the caller, outside the manifest."""

    key: VerifyKey
    revoked: Callable[[str], bool]


class WindowRefused(ValueError):
    pass


def _require(condition, reason):
    if not condition:
        raise WindowRefused(reason)


def _hash(data):
    return sha256(data).hexdigest()


def _encode(value):
    return canonical_json_dumps(value).encode("utf-8")


def _read(path):
    _require(path == path.resolve(), "BREV_WINDOW_NONCANONICAL_PATH")
    return path.read_bytes()


def grant_body(manifest, *, lock_sha, checkpoint_sha, not_before, expires_at):
    """Canonical payload for a test issuer. This function creates no signature."""
    base = {key: value for key, value in manifest.items() if key != "runtime_window"}
    return {
        "schema": SCHEMA,
        "manifest_sha256": _hash(_encode(base)),
        "implementation_sha256": {
            name: _hash(Path(__file__).with_name(name).read_bytes())
            for name in ("brev_v2_offline_window.py", "brev_v2_mac_host_service.py")
        },
        "predecessor_lock_sha256": lock_sha,
        "predecessor_checkpoint_sha256": checkpoint_sha,
        "not_before": not_before,
        "expires_at": expires_at,
    }


@contextmanager
def _guard(path):
    fd = os.open(str(path) + ".recovery_guard", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise WindowRefused("BREV_WINDOW_CONCURRENT_CLAIM") from exc
        yield
    finally:
        os.close(fd)


def _publish(path, raw):
    """Publish the full claim and grant consumption at a single commit point."""
    staging = path.with_name(f".{path.name}.{uuid4().hex}")
    try:
        with staging.open("xb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staging, path)
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        staging.unlink(missing_ok=True)


def _require_dead(claim):
    pid = claim["pid"]
    _require(type(pid) is int and pid > 0, "BREV_WINDOW_OWNER_UNPROVEN")
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return
    raise WindowRefused("BREV_WINDOW_OWNER_MAY_BE_ALIVE")


@dataclass
class _Claim:
    lock_path: Path
    value: dict

    def assert_held(self):
        _require(_read(self.lock_path) == _encode(self.value), "BREV_WINDOW_CLAIM_LOST")

    def publish(self):
        _publish(self.lock_path, _encode(self.value))
        self.assert_held()


def _verify_grant(manifest, trust):
    grant = manifest["runtime_window"]
    body = grant["body"]
    expected = grant_body(
        manifest,
        lock_sha=body["predecessor_lock_sha256"],
        checkpoint_sha=body["predecessor_checkpoint_sha256"],
        not_before=body["not_before"],
        expires_at=body["expires_at"],
    )
    _require(
        isinstance(trust, OfflineWindowTrust)
        and isinstance(trust.key, VerifyKey)
        and set(grant) == {"body", "signature"}
        and body == expected
        and all(
            type(body[key]) in (int, float) and math.isfinite(body[key])
            for key in ("not_before", "expires_at")
        )
        and body["not_before"] < body["expires_at"],
        "BREV_WINDOW_GRANT_INVALID",
    )
    trust.key.verify(_encode(body), bytes.fromhex(grant["signature"]))
    return body, _hash(_encode(body))


def _cap24(manifest, bound, replay_clock):
    cap = manifest["cap24"]
    root = Path(cap["productivity_root"])
    publication = _read(root / CAP24_PUBLISH_MANIFEST_FILENAME)
    _require(
        cap["repository_sha"] == manifest["checkout_sha"]
        and _hash(publication) == cap["publication_sha256"],
        "BREV_WINDOW_CAP24_PUBLICATION_CHANGED",
    )
    epoch = datetime.fromtimestamp(replay_clock(), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _require(json.loads(publication)["decision_epoch"] <= epoch, "BREV_WINDOW_CAP24_FROM_FUTURE")
    selection = inspect_selection_v1(
        productivity_root=root,
        repository_sha=cap["repository_sha"],
        binding_epoch=epoch,
    ).selection
    _require(
        _read(root / CAP24_PUBLISH_MANIFEST_FILENAME) == publication,
        "BREV_WINDOW_CAP24_PUBLICATION_CHANGED",
    )
    _require(
        (selection.instrument_id, selection.venue_native_id)
        == (bound.instrument_id, "BREV-USDT-SWAP"),
        "BREV_WINDOW_CAP24_FOREIGN_INSTRUMENT",
    )


def _wait_proof(
    prior_raw,
    *,
    attempts,
    cursor,
    db,
    config,
    bound,
    binding,
    revision,
    lock_path,
    filegate_revision,
    boot,
    managed,
):
    prior = json.loads(prior_raw)
    context = prior["recovery_context"]
    attempt = context["attempt"]
    _require(type(attempt) is int and attempt > 0, "BREV_WINDOW_ATTEMPT_INVALID")
    attempt_root = attempts / str(attempt)
    _require(
        (attempt_root / v2.CHECKPOINT_FILENAME).is_file(),
        "BREV_WINDOW_ORIGINAL_WAIT_UNPROVEN",
    )
    checkpoint_raw = _read(attempt_root / v2.CHECKPOINT_FILENAME)
    checkpoint = json.loads(checkpoint_raw)
    stat = db.stat()
    wait = v2._native_wait(
        attempt_root, cursor_root=cursor, lock=prior, native_id=bound.venue_native_id
    )
    _require(
        context["binding"] == binding
        and context["state_root"] == str(attempts.parent)
        and checkpoint["schema"] == v2._OWNER
        and checkpoint["binding"] == binding
        and checkpoint["repository_sha"] == revision
        and checkpoint["outer_lock_sha256"] == _hash(prior_raw)
        and checkpoint["filegate_revision"] == filegate_revision
        and checkpoint["cycles_before"] == context["cycles_before"]
        and checkpoint["store_identity"] == [stat.st_dev, stat.st_ino]
        and checkpoint["native_wait"] == wait
        and checkpoint["scope"]["position"]["bound"] == bound.to_dict()
        and v2.verify_occupied_wait_checkpoint_v1(
            checkpoint["scope"],
            cursor_root=cursor,
            budget_root=db.parent,
            native_id=bound.venue_native_id,
            account=config.expected_account_identity,
        ),
        "BREV_WINDOW_ORIGINAL_WAIT_UNPROVEN",
    )
    if managed is not None or context["boot_identity"] != boot:
        _require(
            managed is not None
            and managed.read_host_checkpoint_v1(lock_path=lock_path)
            == {
                "lock_sha256": _hash(prior_raw),
                "ledger_sha256": _hash(checkpoint_raw),
                "cursor_sha256": wait["cursor_sha256"],
                "repository_sha": revision,
            },
            "BREV_WINDOW_FILEGATE_CHECKPOINT_UNPROVEN",
        )
    return checkpoint, _hash(checkpoint_raw)


def run_offline_window(manifest, sandbox, bounds, prepared, replay, open_ports, sleep):
    try:
        return _run(manifest, sandbox, bounds, prepared, replay, open_ports, sleep)
    except BadSignatureError:
        return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": "BREV_WINDOW_SIGNATURE_INVALID"}
    except (
        WindowRefused,
        v2.LifecycleLockError,
        CurrentProductive29PCap24ProvenanceHandoffError,
    ) as exc:
        return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": str(exc)}
    except (KeyError, ValueError, TypeError, OSError, sqlite3.Error) as exc:
        return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": str(exc)}


def _run(manifest, sandbox, bounds, prepared, replay, open_ports, sleep):
    trust = replay.window_trust
    body, grant_id = _verify_grant(manifest, trust)
    request = prepared.request
    config, bound, auth = (request[key] for key in ("config", "bound", "authorization"))
    binding, revision = bounds.runtime_config_digest, request["origin_main_sha"]
    attempts = sandbox / "occupied-n1-v2" / "attempts"
    filegate = Path(config.kill_switch_state_path)
    cursor = config.lane_state_root / "LANE_1"
    lock_path = config.lock_root / v2.s6.LOCK_NAME
    db = v2.budget_owner_root_for_config_v1(config) / "owner" / "reservations.sqlite3"
    proof_root = request["occupied_mark_proof_root"]
    _require(
        manifest["mode"] == "offline_replay"
        and all(
            p.is_relative_to(sandbox) and p == p.resolve()
            for p in (
                filegate,
                cursor,
                lock_path,
                db,
                proof_root,
                attempts,
                config.public_store_root,
                config.private_store_root,
                config.cap24_productivity_root,
            )
        ),
        "BREV_WINDOW_OFFLINE_ROOT_REQUIRED",
    )
    gate = v2._filegate_revision(filegate)
    boot = v2.read_local_boot_identity_v1()
    _require(gate and boot and filegate.is_file(), "BREV_WINDOW_HOST_STATE_UNPROVEN")
    managed = v2.configured_filegate_writer_v1(filegate)
    if managed is not None:
        _require(
            managed.root.is_relative_to(sandbox.parent)
            and not managed.root.is_relative_to(sandbox),
            "BREV_WINDOW_FILEGATE_ROOT_INVALID",
        )
    release = (v2.read_configured_filegate_v1(filegate) or {}).get("filegate_release_sha256")
    archive = lock_path.with_name(lock_path.name + ".window-predecessor")
    common = dict(
        attempts=attempts,
        cursor=cursor,
        db=db,
        config=config,
        bound=bound,
        binding=binding,
        revision=revision,
        lock_path=lock_path,
        filegate_revision=gate,
        boot=boot,
        managed=managed,
    )

    def require_current(now, deadline, recorded_at):
        _require(recorded_at <= now < deadline, "BREV_WINDOW_BOUNDS_EXHAUSTED")
        _require(trust.revoked(grant_id) is False, "BREV_WINDOW_GRANT_REVOKED")
        _require(v2._filegate_revision(filegate) == gate, "BREV_WINDOW_FILEGATE_CHANGED")

    with _guard(lock_path):
        now = time.time()
        require_current(now, min(bounds.expires_at_unix, body["expires_at"]), body["not_before"])
        raw = _read(lock_path)
        prior = json.loads(raw)
        _require_dead(prior)
        old = prior["recovery_context"]
        _cap24(manifest, bound, replay.clock)
        if prior["owner"] == v2._OWNER:
            _require(
                _hash(raw) == body["predecessor_lock_sha256"] and old["deadline"] <= now,
                "BREV_WINDOW_PREDECESSOR_MISMATCH",
            )
            started_at = now
            predecessor, deadline = (
                raw,
                min(
                    now + auth.max_run_duration_seconds, bounds.expires_at_unix, body["expires_at"]
                ),
            )
            checkpoint, checkpoint_sha = _wait_proof(raw, **common)
            _require(
                checkpoint_sha == body["predecessor_checkpoint_sha256"],
                "BREV_WINDOW_PREDECESSOR_MISMATCH",
            )
            attempt = old["attempt"] + 1
            cycles = old["cycles_before"] + checkpoint["native_wait"]["cycles"]
        else:
            _require(
                prior["owner"] == OWNER
                and old["grant_id"] == grant_id
                and old["binding"] == binding
                and old["state_root"] == str(attempts.parent),
                "BREV_WINDOW_CONSUMED_OR_FOREIGN_GRANT",
            )
            deadline = old["deadline"]
            started_at = old["started_at"]
            _require(
                body["not_before"] <= started_at <= old["recorded_at"]
                and deadline
                == min(
                    started_at + auth.max_run_duration_seconds,
                    bounds.expires_at_unix,
                    body["expires_at"],
                ),
                "BREV_WINDOW_DEADLINE_CHANGED",
            )
            require_current(now, deadline, old["recorded_at"])
            predecessor = _read(archive)
            _require(
                _hash(predecessor) == body["predecessor_lock_sha256"],
                "BREV_WINDOW_ARCHIVE_MISMATCH",
            )
            if old["phase"] == "claimed":
                checkpoint, checkpoint_sha = _wait_proof(predecessor, **common)
                _require(
                    checkpoint_sha == body["predecessor_checkpoint_sha256"],
                    "BREV_WINDOW_PREDECESSOR_MISMATCH",
                )
                attempt, cycles = old["attempt"], old["cycles_before"]
            else:
                _require(old["phase"] == "ports_may_have_opened", "BREV_WINDOW_TERMINAL")
                checkpoint, _ = _wait_proof(raw, **common)
                first_attempt = json.loads(predecessor)["recovery_context"]["attempt"]
                original_raw = _read(attempts / str(first_attempt) / v2.CHECKPOINT_FILENAME)
                _require(
                    _hash(original_raw) == body["predecessor_checkpoint_sha256"],
                    "BREV_WINDOW_PREDECESSOR_MISMATCH",
                )
                original = json.loads(original_raw)
                old_hold = original["scope"]["position"]
                resumed_hold = checkpoint["scope"]["position"]
                _require(
                    checkpoint["store_identity"] == original["store_identity"]
                    and all(
                        resumed_hold[key] == old_hold[key]
                        for key in ("reservation_id", "reserve_amount")
                    ),
                    "BREV_WINDOW_ORIGINAL_HOLD_CHANGED",
                )
                attempt = old["attempt"] + 1
                cycles = old["cycles_before"] + checkpoint["native_wait"]["cycles"]

        remaining = auth.max_cycles_per_run - cycles
        _require(
            remaining > 0
            and v2.bounded_retry_policy_v1(
                attempt=attempt - 1,
                automatic_recovery_allowed=True,
            )["retry_allowed"],
            "BREV_WINDOW_BUDGET_EXHAUSTED",
        )
        attempt_root = attempts / str(attempt)
        _require(
            not attempt_root.exists() and not attempt_root.is_symlink(),
            "BREV_WINDOW_ATTEMPT_EXISTS",
        )
        require_current(time.time(), deadline, now)
        if archive.exists():
            _require(_read(archive) == predecessor, "BREV_WINDOW_ARCHIVE_MISMATCH")
        else:
            _require(not archive.is_symlink(), "BREV_WINDOW_ARCHIVE_MISMATCH")
            _publish(archive, predecessor)
        claim = _Claim(
            lock_path,
            {
                "owner": OWNER,
                "authorization_id": OWNER,
                "writer_identity": f"{OWNER}:{OWNER}",
                "pid": os.getpid(),
                "claim_id": uuid4().hex,
                "recovery_context": {
                    "grant_id": grant_id,
                    "deadline": deadline,
                    "started_at": started_at,
                    "recorded_at": now,
                    "phase": "claimed",
                    "process_identity": v2.capture_process_identity(os.getpid()).to_dict(),
                    "boot_identity": boot,
                    "binding": binding,
                    "state_root": str(attempts.parent),
                    "attempt": attempt,
                    "cycles_before": cycles,
                },
            },
        )
        claim.publish()

    context = claim.value["recovery_context"]
    last_wall = now
    monotonic_deadline = time.monotonic() + max(0, deadline - now)

    def guard_window():
        nonlocal last_wall
        claim.assert_held()
        current = time.time()
        require_current(current, deadline, last_wall)
        _require(time.monotonic() < monotonic_deadline, "BREV_WINDOW_BOUNDS_EXHAUSTED")
        last_wall = current

    @contextmanager
    def ports(authorization):
        with _guard(lock_path):
            guard_window()
            _cap24(manifest, bound, replay.clock)
            stat = db.stat()
            _require(
                [stat.st_dev, stat.st_ino] == checkpoint["store_identity"]
                and _hash(_read(cursor / v2.CURSOR_FILENAME))
                == checkpoint["native_wait"]["cursor_sha256"]
                and v2.verify_occupied_wait_checkpoint_v1(
                    checkpoint["scope"],
                    cursor_root=cursor,
                    budget_root=db.parent,
                    account=config.expected_account_identity,
                    native_id=bound.venue_native_id,
                ),
                "BREV_WINDOW_ORIGINAL_WAIT_UNPROVEN",
            )
            context.update(phase="ports_may_have_opened", recorded_at=last_wall)
            claim.publish()
            attempt_root.mkdir()
        with open_ports(authorization) as opened:
            source = opened["observation_source"]
            first_poll = True

            def poll():
                nonlocal first_poll
                guard_window()
                if first_poll:
                    stamp = db.stat()
                    _require(
                        [stamp.st_dev, stamp.st_ino] == checkpoint["store_identity"]
                        and _hash(_read(cursor / v2.CURSOR_FILENAME))
                        == checkpoint["native_wait"]["cursor_sha256"],
                        "BREV_WINDOW_ORIGINAL_WAIT_UNPROVEN",
                    )
                    first_poll = False
                return source.poll()

            yield {**opened, "observation_source": SimpleNamespace(poll=poll)}

    def wait(seconds):
        guard_window()
        sleep(min(seconds, max(0, deadline - time.time())))
        guard_window()

    guard_window()
    result = v2._run_attempt(
        attempt_root=attempt_root,
        auth=replace(
            auth,
            max_cycles_per_run=remaining,
            max_run_duration_seconds=deadline - time.time(),
        ),
        bound=bound,
        config=config,
        request=request,
        revision=revision,
        proof_root=proof_root,
        filegate=filegate,
        filegate_revision=gate,
        managed=managed,
        release=release,
        lock=claim,
        cursor_root=cursor,
        db=db,
        admitted=checkpoint,
        cycles=cycles,
        binding=binding,
        open_fixture_ports=ports,
        replay_clock=replay.clock,
        sleep=wait,
    )
    with _guard(lock_path):
        claim.assert_held()
        context.update(phase="finished", recorded_at=max(last_wall, time.time()))
        claim.publish()
    return {**result, "runtime_window": {"grant_id": grant_id, "deadline": deadline}}
