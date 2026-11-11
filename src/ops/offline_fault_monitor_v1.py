"""Autonomous observation and authorized feed recovery for one isolated Safety scope."""

from dataclasses import dataclass
import fcntl
import json
import math
import re
import time

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
)
from src.ops.offline_public_feed_recovery_v1 import OfflinePublicFeedRecoveryError
from src.ops.offline_public_feed_restart_v1 import OfflinePublicFeedRestartV1
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.constants_v1 import (
    DEFAULT_BOUNDED_RETRY_LIMIT,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.recovery_v1 import (
    bounded_retry_policy_v1,
)

_SCHEMA = "offline_fault_observation.v1"


@dataclass(frozen=True)
class OfflineFaultPortsV1:
    host: object
    bound: object
    feed_restart: dict | None = None


class OfflineFaultMonitorV1:
    """Persist poll reservations before owner calls and keep observing unresolved stops."""

    def __init__(self, safety, *, interval_seconds=5, clock=time.time):
        if (
            type(safety) is not OfflinePublicFeedRestartV1
            or type(interval_seconds) not in {float, int}
            or not 1 <= interval_seconds <= 300
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_FAULT_MONITOR_SCOPE_REQUIRED")
        self._safety = safety
        self._interval = interval_seconds
        self._clock = clock
        root = safety.repair.incident.root
        self._journal = root / "offline-fault-observation.json"
        self._lock = root / "offline-fault-observation.lock"
        self._scope = {
            "state_path": str(safety.repair.incident.state_path),
            "session_id": safety.repair.incident.session_id,
            "instrument": safety.repair.incident.instrument.to_dict(),
            "interval_seconds": interval_seconds,
        }

    def _load(self):
        try:
            envelope = json.loads(self._journal.read_bytes())
            body = envelope["body"]
            if (
                envelope["sha256"] != fact_digest(body)
                or body["schema"] != _SCHEMA
                or body["scope"] != self._scope
                or not math.isfinite(body["observed_at"])
                or type(body["feed_attempts"]) is not int
                or not 0 <= body["feed_attempts"] <= DEFAULT_BOUNDED_RETRY_LIMIT
            ):
                raise ValueError("invalid observation journal")
            return body
        except FileNotFoundError:
            return None
        except (KeyError, TypeError, ValueError) as exc:
            raise OfflinePublicFeedRecoveryError("OFFLINE_FAULT_JOURNAL_UNPROVEN") from exc

    def _save(self, body):
        atomic_write_json(path=self._journal, payload={"body": body, "sha256": fact_digest(body)})
        if self._load() != body:
            raise OfflinePublicFeedRecoveryError("OFFLINE_FAULT_READBACK_UNPROVEN")
        return body

    def poll_v1(self, open_ports):
        """open_ports returns a fresh, bounded owner context for a single observation."""
        self._safety.repair._require_scope()
        for path in (self._lock, self._journal, self._journal.with_suffix(".json.tmp")):
            if path.resolve() != path or (path.exists() and not path.is_file()):
                raise OfflinePublicFeedRecoveryError("OFFLINE_FAULT_JOURNAL_SCOPE_UNPROVEN")
        with self._lock.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            # Read/fence Safety even if the diagnostic journal is corrupt or rate-limited.
            gate = self._safety.observe_filegate_integrity_v1()
            try:
                old = self._load()
            except (OfflinePublicFeedRecoveryError, OSError):
                return {"status": "OBSERVATION_JOURNAL_UNPROVEN", "filegate": gate}
            now = self._clock()
            if type(now) not in {int, float} or not math.isfinite(now):
                raise OfflinePublicFeedRecoveryError("OFFLINE_FAULT_CLOCK_UNPROVEN")
            if old and now < old["observed_at"]:
                raise OfflinePublicFeedRecoveryError("OFFLINE_FAULT_CLOCK_UNPROVEN")
            if old and gate == old["filegate"] and now < old["observed_at"] + self._interval:
                # A prior sample is diagnostic history and carries no current admission.
                return {"status": "WAITING_FOR_NEXT_OBSERVATION", "filegate": gate}
            attempts = (
                old["feed_attempts"]
                if old and gate in (old["filegate"], old.get("filegate_after"))
                else 0
            )
            body = {
                "schema": _SCHEMA,
                "scope": self._scope,
                "observed_at": now,
                "status": "OBSERVATION_RESERVED",
                "filegate": gate,
                "feed_attempts": attempts,
            }
            self._save(body)
            return self._poll(gate, body, open_ports)

    def _poll(self, gate, body, open_ports):
        stop = gate.get("filegate_sha256")
        incident = self._safety.repair.incident
        stopped = gate["status"] == "STOP_CONFIRMED"
        active = gate["status"] == "ACTIVE_HEAD_CONFIRMED"
        if not (stopped or active):
            body["status"] = "BLOCKED_OBSERVING"
            return self._save(body)
        retry = bounded_retry_policy_v1(
            attempt=body["feed_attempts"], automatic_recovery_allowed=True
        )["retry_allowed"]
        recovered_revision = None
        try:
            with open_ports() as ports:
                if type(ports) is not OfflineFaultPortsV1:
                    raise OfflinePublicFeedRecoveryError("OFFLINE_FAULT_ORIGINAL_PORTS_REQUIRED")
                if (
                    ports.feed_restart is not None
                    and retry
                    and (active or stop == incident.filegate_sha256)
                ):
                    body["feed_attempts"] += 1
                    self._save(body)
                    body["host_result"] = self._safety.recover_and_resume_v1(
                        host=ports.host, bound=ports.bound, **ports.feed_restart
                    )
                    _, recovered_revision = self._safety._read_active(ports.feed_restart["mandate"])
                elif stopped:
                    body["account_observation"] = self._safety.inspect_stopped_account_v1(
                        host=ports.host, bound=ports.bound, stop_sha256=stop
                    )
        except (ValueError, RuntimeError, OSError) as exc:
            reason = str(exc).split(":", 1)[0]
            body["reason"] = (
                reason
                if re.fullmatch(r"[A-Z][A-Z0-9_]{3,95}", reason)
                else "OWNER_OBSERVATION_FAILED"
            )
        after = self._safety.observe_filegate_integrity_v1()
        if (
            recovered_revision is not None
            and after["status"] == "ACTIVE_HEAD_CONFIRMED"
            and after["filegate_sha256"] == recovered_revision
        ):
            body["status"] = "HOST_CONTINUATION_CONFIRMED"
        elif after != gate or "host_result" in body:
            body["status"] = "FILEGATE_CHANGED"
            body.pop("account_observation", None)
            body.pop("host_result", None)
        else:
            body["status"] = "BLOCKED_OBSERVING" if stopped else "ACTIVE_WITHOUT_HOST_PROOF"
        body["filegate_after"] = after
        return self._save(body)

    def run_v1(self, *, open_ports, stop_requested, sleeper=time.sleep):
        """Remain on bounded observation cadence until original host proof or service stop."""
        while not stop_requested():
            result = self.poll_v1(open_ports)
            if result["status"] == "HOST_CONTINUATION_CONFIRMED":
                return result
            if not stop_requested():
                sleeper(self._interval)
        return {"status": "MONITOR_STOPPED"}
