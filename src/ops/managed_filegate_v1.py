"""Coordinate the original FILEGATE projection with a separately retained Safety head."""

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
from tempfile import NamedTemporaryFile, TemporaryDirectory
import time
from uuid import uuid4

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    canonical_json_text,
)
from src.ops.filegate_recovery_authority_v1 import (
    EVIDENCE_ROLES,
    RECOVERABLE_CAUSES,
    FilegateAuthorityError,
    FilegateRecoveryScopeV1,
    is_digest_v1,
    issue_filegate_release_v1,
    public_key_hex_v1,
    require_filegate_loss_violation_v1,
    requires_cause_proof_set_v1,
    verify_filegate_owner_proof_v1,
    verify_filegate_release_v1,
    verify_filegate_protection_v1,
    verify_filegate_revocation_v1,
)

ROOT_ENV = "PEAK_FILEGATE_AUTHORITY_ROOT"
_DATABASE = "filegate-authority.sqlite3"


def _scope_marker(state_path):
    return Path(state_path).with_name(Path(state_path).name + ".managed")


def managed_filegate_configured_v1(state_path):
    marker = _scope_marker(state_path)
    if marker.exists() or marker.is_symlink():
        return True
    if ROOT_ENV not in os.environ:
        return False
    from src.ops.gates.risk_gate import canonical_kill_switch_state_path

    return Path(state_path).absolute() == Path(canonical_kill_switch_state_path()).absolute()


def configured_filegate_writer_v1(state_path):
    if ROOT_ENV not in os.environ or not managed_filegate_configured_v1(state_path):
        return None
    return ManagedFilegateV1(
        state_path=Path(state_path).absolute(), root=Path(os.environ[ROOT_ENV])
    )


def read_configured_filegate_v1(state_path):
    """Return the original projection only when it matches the independent head."""
    try:
        writer = configured_filegate_writer_v1(state_path)
        return writer.read_v1() if writer is not None else None
    except (KeyError, OSError, TypeError, ValueError, sqlite3.Error):
        return None


class ManagedFilegateV1:
    """Safety operations only. The separate head never confers order authority."""

    def __init__(self, *, state_path: Path, root: Path, clock=time.time):
        self.state_path = state_path
        self.root = root
        self._clock = clock

    def _validate_paths(self):
        state_root = self.state_path.parent
        if (
            not self.root.is_absolute()
            or self.root.resolve() != self.root
            or not self.root.is_dir()
            or not self.state_path.is_absolute()
            or self.state_path.resolve() != self.state_path
            or not state_root.is_dir()
            or self.root.is_relative_to(state_root)
            or state_root.is_relative_to(self.root)
            or self.root.stat().st_uid != os.getuid()
            or self.root.stat().st_mode & 0o077
        ):
            raise FilegateAuthorityError("FILEGATE_AUTHORITY_ROOT_UNPROVEN")
        for path in (
            self.state_path,
            *(
                self.root / name
                for name in (
                    _DATABASE,
                    _DATABASE + "-journal",
                    _DATABASE + "-wal",
                    _DATABASE + "-shm",
                    "filegate.lock",
                )
            ),
        ):
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
                raise FilegateAuthorityError("FILEGATE_AUTHORITY_FILE_UNPROVEN")

    @contextmanager
    def _lock(self):
        self._validate_paths()
        flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
        with os.fdopen(os.open(self.root / "filegate.lock", flags, 0o600), "r+b") as lock:
            info = os.fstat(lock.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.getuid()
                or info.st_nlink != 1
                or info.st_mode & 0o077
            ):
                raise FilegateAuthorityError("FILEGATE_AUTHORITY_LOCK_UNPROVEN")
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            self._validate_paths()
            yield

    @contextmanager
    def _database(self, *, readonly=False, create=False):
        database = self.root / _DATABASE
        mode = "ro" if readonly else "rwc" if create else "rw"
        conn = sqlite3.connect(database.as_uri() + "?mode=" + mode, uri=True, timeout=0)
        try:
            if not readonly:
                conn.execute("PRAGMA synchronous=FULL")
            yield conn
        finally:
            conn.close()

    def _head(self, conn):
        row = conn.execute("SELECT binding, head FROM authority WHERE singleton = 1").fetchone()
        if row is None:
            raise FilegateAuthorityError("FILEGATE_AUTHORITY_NOT_PROVISIONED")
        binding, head = map(json.loads, row)
        if binding["state_path"] != str(self.state_path):
            raise FilegateAuthorityError("FILEGATE_AUTHORITY_SCOPE_CHANGED")
        projection = head["projection"]
        if (
            type(head["generation"]) is not int
            or head["generation"] <= 0
            or projection["filegate_generation"] != head["generation"]
            or projection["state"] != ("ACTIVE" if head["stop"] is None else "KILLED")
        ):
            raise FilegateAuthorityError("FILEGATE_AUTHORITY_HEAD_INVALID")
        return binding, head

    def _raw(self):
        try:
            return self.state_path.read_bytes()
        except FileNotFoundError:
            return None

    def _matches(self, head):
        return self._raw() == canonical_json_text(head["projection"]).encode()

    def read_v1(self):
        self._validate_paths()
        with self._database(readonly=True) as conn:
            _, head = self._head(conn)
            if (
                not self._matches(head)
                or (head["stop"] is None and self._has_pending_kill())
                or self._head(conn)[1] != head
            ):
                raise FilegateAuthorityError("FILEGATE_PROJECTION_UNPROVEN")
            return head["projection"]

    def _publish(self, projection):
        self._publish_json(self.state_path, projection)

    @staticmethod
    def _publish_json(path, payload):
        raw = canonical_json_text(payload).encode()
        with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temp = Path(stream.name)
            try:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
                os.replace(temp, path)
                fd = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            finally:
                temp.unlink(missing_ok=True)
        if path.read_bytes() != raw:
            raise FilegateAuthorityError("FILEGATE_PROJECTION_READBACK_CHANGED")

    def _has_pending_kill(self):
        return next(self.root.glob("kill-intent-*.json"), None) is not None

    def _original_projection(self, *, state, reason=None, previous=None):
        from src.risk_layer.kill_switch.core import KillSwitch
        from src.risk_layer.kill_switch.persistence import StatePersistence
        from src.risk_layer.kill_switch.state import KillSwitchState

        with TemporaryDirectory(dir=self.state_path.parent) as directory:
            store = StatePersistence(str(Path(directory) / "state.json"))
            if state == "KILLED":
                store.save(
                    KillSwitchState.KILLED,
                    killed_at=datetime.fromtimestamp(self._clock(), timezone.utc).replace(
                        tzinfo=None
                    ),
                    trigger_reason=reason,
                )
            else:
                store.state_file.write_text(canonical_json_text(previous))
                # The published file stays KILLED while the original transition is staged.
                switch = KillSwitch({"recovery_cooldown_seconds": 0}, persistence=store)
                if (
                    not switch.request_recovery("managed-filegate")
                    or not switch.complete_recovery()
                ):
                    raise FilegateAuthorityError("FILEGATE_ORIGINAL_RELEASE_DENIED")
            projection = store.load()
        if not projection or projection["state"] != state:
            raise FilegateAuthorityError("FILEGATE_ORIGINAL_WRITER_UNPROVEN")
        return projection

    def provision_v1(
        self,
        *,
        scope,
        issuer_public_key,
        owner_public_keys,
        recoverable_causes,
        protection_public_key=None,
        cause_public_keys=None,
    ):
        """Initialize one new deployment in KILLED. Reopening never provisions a head."""
        causes = set(recoverable_causes)
        if (
            type(scope) is not FilegateRecoveryScopeV1
            or set(owner_public_keys) != EVIDENCE_ROLES
            or not causes <= RECOVERABLE_CAUSES
        ):
            raise FilegateAuthorityError("FILEGATE_TRUST_BINDING_INVALID")
        owners = {role: public_key_hex_v1(key) for role, key in owner_public_keys.items()}
        cause_keys = {
            cause: public_key_hex_v1(key) for cause, key in (cause_public_keys or {}).items()
        }
        if not cause_keys.keys() <= causes:
            raise FilegateAuthorityError("FILEGATE_TRUST_BINDING_INVALID")
        issuer = public_key_hex_v1(issuer_public_key)
        protection = (
            None if protection_public_key is None else public_key_hex_v1(protection_public_key)
        )
        keys = [issuer, *owners.values(), *cause_keys.values()]
        if protection is not None:
            keys.append(protection)
        if len(set(keys)) != len(keys):
            raise FilegateAuthorityError("FILEGATE_INDEPENDENT_KEYS_REQUIRED")
        binding = {
            "state_path": str(self.state_path),
            "scope": scope.binding_v1(),
            "issuer": issuer,
            "owners": owners,
            "cause_keys": cause_keys,
            "recoverable_causes": sorted(causes),
            "protection": protection,
        }
        with self._lock():
            if (self.root / _DATABASE).exists():
                raise FilegateAuthorityError("FILEGATE_AUTHORITY_ALREADY_PROVISIONED")
            if self._raw() is not None:
                raise FilegateAuthorityError("FILEGATE_PROVISIONING_REQUIRES_NEW_PROJECTION_PATH")
            marker = _scope_marker(self.state_path)
            if marker.exists() or marker.is_symlink():
                raise FilegateAuthorityError("FILEGATE_AUTHORITY_ALREADY_PROVISIONED")
            self._publish_json(marker, {"schema": "managed_filegate_scope.v1"})
            event = uuid4().hex
            head = self._stop(binding, None, event, "R03", "FILEGATE_PROVISIONED_BLOCKED")
            with self._database(create=True) as conn, conn:
                conn.execute(
                    "CREATE TABLE authority (singleton INTEGER PRIMARY KEY, binding TEXT, head TEXT)"
                )
                conn.execute(
                    "CREATE TABLE events (id TEXT PRIMARY KEY, generation INTEGER, kind TEXT)"
                )
                conn.execute(
                    "CREATE TABLE host_checkpoints (lock_path TEXT PRIMARY KEY, checkpoint TEXT)"
                )
                conn.execute(
                    "INSERT INTO authority VALUES (1, ?, ?)",
                    (
                        canonical_json_text(binding),
                        canonical_json_text(head),
                    ),
                )
                conn.execute("INSERT INTO events VALUES (?, 1, 'KILL')", (event,))
            self._publish(head["projection"])
            return head["stop"]

    def _stop(
        self, binding, head, event, cause, reason, *, execution_incident=False, risk_violation=None
    ):
        sequence = 1 if head is None else head["generation"] + 1
        previous = head["stop"] if head is not None else None
        if previous is not None:
            reason = head["projection"]["trigger_reason"]
        projection = self._original_projection(state="KILLED", reason=reason)
        stop = {
            "scope": binding["scope"],
            "state_path": str(self.state_path),
            "generation": sequence,
            "stop_id": event,
            "killed_at": self._clock(),
            "causes": sorted(set(() if previous is None else previous["causes"]) | {cause}),
        }
        incidents = (
            previous.get("execution_incident_ids")
            if previous is not None and "R04" in previous["causes"]
            else []
        )
        if cause == "R04":
            if execution_incident and is_digest_v1(event) and incidents is not None:
                incidents = sorted({*incidents, event})
            else:
                incidents = None
        if incidents:
            stop["execution_incident_ids"] = incidents
        prior_risk = None if previous is None else previous.get("risk_violation")
        if cause == "R05":
            if (
                previous is not None
                and "R05" in previous["causes"]
                and (
                    prior_risk is None
                    or risk_violation is None
                    or prior_risk["policy_sha256"] != risk_violation["policy_sha256"]
                )
            ):
                risk_violation = None
        else:
            risk_violation = prior_risk
        if risk_violation is not None:
            stop["risk_violation"] = risk_violation
        projection.update(filegate_generation=sequence, filegate_stop_id=event)
        if execution_incident:
            projection["latest_authenticated_execution_incident"] = event
        return {"generation": sequence, "stop": stop, "projection": projection}

    def _commit(self, conn, head, *, event, kind):
        with conn:
            conn.execute("INSERT INTO events VALUES (?, ?, ?)", (event, head["generation"], kind))
            conn.execute(
                "UPDATE authority SET head = ? WHERE singleton = 1", (canonical_json_text(head),)
            )

    def kill_v1(self, *, cause, reason, incident_id=None, incident_scope=None, risk_violation=None):
        """Record a newly accepted incident or emergency under the same lock as release."""
        if (
            cause not in RECOVERABLE_CAUSES | {"R08", "R09"}
            or not reason
            or not isinstance(reason, str)
        ):
            raise FilegateAuthorityError("FILEGATE_KILL_CAUSE_INVALID")
        event = uuid4().hex if incident_id is None else incident_id
        if not isinstance(event, str) or not re.fullmatch(r"(?:[a-f0-9]{32}|[a-f0-9]{64})", event):
            raise FilegateAuthorityError("FILEGATE_KILL_ID_INVALID")
        self._validate_paths()
        intent = {
            "event": event,
            "cause": cause,
            "reason": reason,
            "incident_scope": incident_scope,
        }
        if risk_violation is not None:
            if cause != "R05" or type(risk_violation) is not dict:
                raise FilegateAuthorityError("FILEGATE_KILL_CAUSE_INVALID")
            intent["risk_violation"] = require_filegate_loss_violation_v1(
                risk_violation, scope=risk_violation.get("scope")
            )
        path = self.root / f"kill-intent-{event}.json"
        # Declare the veto before waiting for an in-flight release. A crash
        # here leaves a durable pending intent for the standing controller.
        self._publish_json(path, intent)
        with self._lock(), self._database() as conn:
            return self._commit_kill_intent(conn, path, intent)

    def _commit_kill_intent(self, conn, path, intent):
        binding, old = self._head(conn)
        event, source = intent["event"], intent["incident_scope"]
        bound = binding["scope"]
        if source is not None and (
            any(source[key] != bound[key] for key in ("account", "environment", "host"))
            or source["instrument"] not in bound["instruments"]
        ):
            path.unlink(missing_ok=True)
            raise FilegateAuthorityError("FILEGATE_KILL_INCIDENT_SCOPE_CHANGED")
        risk_violation = intent.get("risk_violation")
        if risk_violation is not None:
            try:
                require_filegate_loss_violation_v1(risk_violation, scope=bound)
            except FilegateAuthorityError:
                path.unlink(missing_ok=True)
                raise
        duplicate = conn.execute(
            "SELECT generation, kind FROM events WHERE id = ?", (event,)
        ).fetchone()
        if duplicate is not None:
            if duplicate != (old["generation"], "KILL") or old["stop"] is None:
                path.unlink(missing_ok=True)
                raise FilegateAuthorityError("FILEGATE_KILL_SUPERSEDED")
            head = old
        else:
            head = self._stop(
                binding,
                old,
                event,
                intent["cause"],
                intent["reason"],
                execution_incident=source is not None,
                risk_violation=risk_violation,
            )
            if not self._matches(old):
                head["stop"]["causes"] = sorted(set(head["stop"]["causes"]) | {"R03"})
            self._commit(conn, head, event=event, kind="KILL")
        if not self._matches(head):
            self._publish(head["projection"])
        path.unlink(missing_ok=True)
        return head["stop"]

    def inspect_stop_v1(self):
        self._validate_paths()
        with self._database(readonly=True) as conn:
            _, head = self._head(conn)
            if (
                head["stop"] is None
                or not self._matches(head)
                or self._head(conn)[1] != head
                or self._has_pending_kill()
            ):
                raise FilegateAuthorityError("FILEGATE_STOP_UNPROVEN")
            return head["stop"]

    def set_host_checkpoint_v1(
        self, *, lock_path: Path, checkpoint: dict | None, expected_release_sha256=None
    ):
        """Fence old WAIT evidence before the original host advances to a cycle."""
        with self._lock(), self._database() as conn, conn:
            _, head = self._head(conn)
            if checkpoint is None:
                conn.execute("DELETE FROM host_checkpoints WHERE lock_path = ?", (str(lock_path),))
                return
            if (
                head["stop"] is not None
                or not self._matches(head)
                or self._has_pending_kill()
                or expected_release_sha256 is None
                or head["projection"].get("filegate_release_sha256") != expected_release_sha256
            ):
                raise FilegateAuthorityError("FILEGATE_HOST_CHECKPOINT_ADMISSION_DENIED")
            conn.execute(
                "INSERT INTO host_checkpoints VALUES (?, ?) ON CONFLICT(lock_path) "
                "DO UPDATE SET checkpoint = excluded.checkpoint",
                (str(lock_path), canonical_json_text(checkpoint)),
            )

    def read_host_checkpoint_v1(self, *, lock_path: Path):
        self._validate_paths()
        with self._database(readonly=True) as conn:
            self._head(conn)
            row = conn.execute(
                "SELECT checkpoint FROM host_checkpoints WHERE lock_path = ?", (str(lock_path),)
            ).fetchone()
            return None if row is None else json.loads(row[0])

    def retire_host_checkpoint_v1(self, *, lock_path: Path, lock_receipt: bytes):
        """Retain the confirmed WAIT claim before its owner releases exclusion."""
        with self._lock(), self._database() as conn, conn:
            self._head(conn)
            row = conn.execute(
                "SELECT checkpoint FROM host_checkpoints WHERE lock_path = ?", (str(lock_path),)
            ).fetchone()
            checkpoint = None if row is None else json.loads(row[0])
            if (
                checkpoint is None
                or lock_path.read_bytes() != lock_receipt
                or json.loads(lock_receipt).get("pid") != os.getpid()
                or checkpoint["lock_sha256"] != sha256(lock_receipt).hexdigest()
            ):
                raise FilegateAuthorityError("FILEGATE_HOST_CHECKPOINT_RETIRE_UNPROVEN")
            checkpoint["retired_lock_receipt"] = lock_receipt.decode()
            conn.execute(
                "UPDATE host_checkpoints SET checkpoint = ? WHERE lock_path = ?",
                (canonical_json_text(checkpoint), str(lock_path)),
            )

    def repair_projection_v1(self):
        """Record an integrity stop when the projection has been damaged or rolled back."""
        with self._lock(), self._database() as conn:
            for path in sorted(self.root.glob("kill-intent-*.json")):
                if path.is_symlink() or not path.is_file():
                    raise FilegateAuthorityError("FILEGATE_KILL_INTENT_UNPROVEN")
                intent = json.loads(path.read_bytes())
                if path.name != f"kill-intent-{intent['event']}.json" or intent[
                    "cause"
                ] not in RECOVERABLE_CAUSES | {"R08", "R09"}:
                    raise FilegateAuthorityError("FILEGATE_KILL_INTENT_UNPROVEN")
                try:
                    self._commit_kill_intent(conn, path, intent)
                except FilegateAuthorityError:
                    if path.exists():
                        raise
            binding, old = self._head(conn)
            if self._matches(old):
                return old["stop"]
            event = uuid4().hex
            head = self._stop(binding, old, event, "R03", "FILEGATE_INTEGRITY_UNPROVEN")
            try:
                interrupted_kill = json.loads(self._raw() or b"{}").get(
                    "filegate_pending_emergency"
                )
            except (ValueError, AttributeError):
                interrupted_kill = None
            if interrupted_kill is True:
                head["stop"]["causes"] = sorted(set(head["stop"]["causes"]) | {"R09"})
            self._commit(conn, head, event=event, kind="KILL")
            self._publish(head["projection"])
            return head["stop"]

    def emergency_v1(self, reason):
        """Keep a local veto even if the separate authority is temporarily unavailable."""
        try:
            return self.kill_v1(cause="R09", reason=reason)
        except sqlite3.Error:
            with self._lock():
                # If the store is still unavailable, retain the emergency
                # in the original projection for the integrity repair to ingest.
                try:
                    with self._database() as conn:
                        self._head(conn)
                except sqlite3.Error:
                    pending = self._original_projection(state="KILLED", reason=reason)
                    pending.update(filegate_pending_emergency=True)
                    self._publish(pending)
                    return None
            return self.kill_v1(cause="R09", reason=reason)

    def requires_cause_proof_set_v1(self, stop):
        self._validate_paths()
        with self._database(readonly=True) as conn:
            binding, head = self._head(conn)
            if head["stop"] is None or head["stop"] != stop:
                raise FilegateAuthorityError("FILEGATE_STOP_UNPROVEN")
            return requires_cause_proof_set_v1(stop, binding.get("cause_keys", {}))

    def validate_owner_publication_v1(self, *, proof, stop, role, cause=None):
        """Check the proof against the current stop and the registered owner's key."""
        self._validate_paths()
        with self._database(readonly=True) as conn:
            binding, head = self._head(conn)
            if head["stop"] != stop or not self._matches(head) or self._has_pending_kill():
                raise FilegateAuthorityError("FILEGATE_STOP_UNPROVEN")
            key = binding["owners"].get(role)
            require_cause = False
            if role == "CAUSE":
                if cause not in stop["causes"] or cause not in binding["recoverable_causes"]:
                    raise FilegateAuthorityError("FILEGATE_OWNER_CAUSE_UNPROVEN")
                cause_keys = binding.get("cause_keys", {})
                require_cause = requires_cause_proof_set_v1(stop, cause_keys)
                if require_cause:
                    key = cause_keys.get(cause)
            if key is None:
                raise FilegateAuthorityError("FILEGATE_OWNER_KEY_UNPROVEN")
            verify_filegate_owner_proof_v1(
                proof=proof,
                key=key,
                role=role,
                stop=stop,
                now=self._clock(),
                cause=cause,
                require_cause=require_cause,
            )
            if self._head(conn)[1] != head or self._has_pending_kill():
                raise FilegateAuthorityError("FILEGATE_STOP_UNPROVEN")

    def issue_release_v1(self, *, evidence, issuer_key):
        self._validate_paths()
        with self._database(readonly=True) as conn:
            binding, head = self._head(conn)
            if head["stop"] is None or not self._matches(head) or self._has_pending_kill():
                raise FilegateAuthorityError("FILEGATE_STOP_UNPROVEN")
            return issue_filegate_release_v1(
                stop=head["stop"],
                evidence=evidence,
                trust=binding,
                issuer_key=issuer_key,
                now=self._clock(),
            )

    def release_v1(self, *, release, evidence):
        with self._lock(), self._database() as conn:
            binding, old = self._head(conn)
            if (
                old["stop"] is None
                or not self._matches(old)
                or os.environ.get("PEAK_KILL_SWITCH") == "1"
                or self._has_pending_kill()
            ):
                raise FilegateAuthorityError("FILEGATE_STOP_UNPROVEN")
            kwargs = dict(
                release=release,
                stop=old["stop"],
                evidence=evidence,
                trust=binding,
            )
            verify_filegate_release_v1(**kwargs, now=self._clock())
            projection = self._original_projection(state="ACTIVE", previous=old["projection"])
            verify_filegate_release_v1(**kwargs, now=self._clock())
            if (
                not self._matches(old)
                or os.environ.get("PEAK_KILL_SWITCH") == "1"
                or self._has_pending_kill()
            ):
                raise FilegateAuthorityError("FILEGATE_STOP_CHANGED_BEFORE_RELEASE")
            generation = old["generation"] + 1
            event = sha256(canonical_json_text(release).encode()).hexdigest()
            if conn.execute("SELECT 1 FROM events WHERE id = ?", (event,)).fetchone():
                raise FilegateAuthorityError("FILEGATE_RELEASE_CONSUMED_OR_REVOKED")
            projection.update(filegate_generation=generation, filegate_release_sha256=event)
            head = {"generation": generation, "stop": None, "projection": projection}
            self._commit(conn, head, event=event, kind="RELEASE")
            if (
                not self._matches(old)
                or os.environ.get("PEAK_KILL_SWITCH") == "1"
                or self._has_pending_kill()
            ):
                raise FilegateAuthorityError("FILEGATE_STOP_CHANGED_BEFORE_RELEASE")
            self._publish(projection)
            if self._has_pending_kill():
                raise FilegateAuthorityError("FILEGATE_STOP_CHANGED_BEFORE_RELEASE")
            return projection

    def revoke_release_v1(self, *, revocation):
        """The provisioned issuer can revoke a release, including one already published."""
        with self._lock(), self._database() as conn:
            binding, old = self._head(conn)
            event = verify_filegate_revocation_v1(revocation, binding["issuer"])
            row = conn.execute("SELECT kind FROM events WHERE id = ?", (event,)).fetchone()
            if row == ("REVOKED",):
                return
            if old["projection"].get("filegate_release_sha256") == event:
                kill = uuid4().hex
                head = self._stop(binding, old, kill, "R06", "FILEGATE_RELEASE_REVOKED")
                with conn:
                    conn.execute("UPDATE events SET kind = 'REVOKED' WHERE id = ?", (event,))
                    conn.execute(
                        "INSERT INTO events VALUES (?, ?, 'KILL')", (kill, head["generation"])
                    )
                    conn.execute(
                        "UPDATE authority SET head = ? WHERE singleton = 1",
                        (canonical_json_text(head),),
                    )
                self._publish(head["projection"])
            else:
                with conn:
                    conn.execute(
                        "INSERT INTO events VALUES (?, ?, 'REVOKED') ON CONFLICT(id) DO UPDATE SET kind = 'REVOKED'",
                        (event, old["generation"]),
                    )

    def claim_reduce_only_v1(self, *, permit, receipt):
        """Preserve KILL and reserve one originally admitted protection attempt."""
        from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
            FlattenPreSendGateReceiptV1,
        )

        if (
            type(receipt) is not FlattenPreSendGateReceiptV1
            or receipt.allowed is not True
            or receipt.reduce_only is not True
            or receipt.approved_method != "POST"
            or receipt.approved_endpoint != "/api/v5/trade/order"
            or not receipt.approved_body_text
        ):
            raise FilegateAuthorityError("FILEGATE_ORIGINAL_PROTECTION_GATE_REQUIRED")
        with self._lock(), self._database() as conn:
            binding, old = self._head(conn)
            stop = old["stop"]
            if (
                stop is None
                or not self._matches(old)
                or self._has_pending_kill()
                or os.environ.get("PEAK_KILL_SWITCH") == "1"
                or not binding.get("protection")
                or receipt.request_body["instId"] not in stop["scope"]["instruments"]
            ):
                raise FilegateAuthorityError("FILEGATE_PROTECTION_STOP_UNPROVEN")
            body = verify_filegate_protection_v1(
                permit=permit,
                stop=stop,
                approved_body_sha256=sha256(receipt.approved_body_text.encode()).hexdigest(),
                public_key=binding["protection"],
                now=self._clock(),
            )
            event = "PROTECTION:" + body["permit_id"]
            request = (
                "PROTECTION_REQUEST:"
                + sha256(
                    canonical_json_text(
                        {
                            "account": stop["scope"]["account"],
                            "environment": stop["scope"]["environment"],
                            "body_sha256": body["approved_body_sha256"],
                        }
                    ).encode()
                ).hexdigest()
            )
            if conn.execute("SELECT 1 FROM events WHERE id IN (?, ?)", (event, request)).fetchone():
                raise FilegateAuthorityError("FILEGATE_PROTECTION_ALREADY_RESERVED")
            with conn:
                conn.executemany(
                    "INSERT INTO events VALUES (?, ?, 'PROTECTION_RESERVED')",
                    [(key, old["generation"]) for key in (event, request)],
                )
            if self._has_pending_kill():
                raise FilegateAuthorityError("FILEGATE_PROTECTION_STOP_SUPERSEDED")
            return body["permit_id"]
