"""Poll the stopped Originalowner paths and consume their independent evidence."""

from collections.abc import Callable, Mapping
import json
from hashlib import sha256
import os
from pathlib import Path
import re
import sqlite3
import stat
import time

from nacl.signing import SigningKey

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
)
from src.ops.filegate_recovery_authority_v1 import (
    EVIDENCE_ROLES,
    FilegateAuthorityError,
    attest_filegate_owner_evidence_v1,
)
from src.ops.gates.risk_gate import canonical_kill_switch_state_path
from src.ops.managed_filegate_v1 import ManagedFilegateV1, configured_filegate_writer_v1


class ManagedFaultRecoveryV1:
    """The issuer receives signed proofs and has no owner signing key or order port."""

    def __init__(
        self,
        *,
        writer: ManagedFilegateV1,
        issuer_key: SigningKey,
        observations: Mapping,
        interval_seconds: float,
        sleeper: Callable = time.sleep,
    ):
        if (
            type(writer) is not ManagedFilegateV1
            or not isinstance(issuer_key, SigningKey)
            or set(observations) != EVIDENCE_ROLES
            or not all(callable(poll) for poll in observations.values())
            or type(interval_seconds) not in {float, int}
            or not 1 <= interval_seconds <= 60
        ):
            raise FilegateAuthorityError("FAULT_RECOVERY_ORIGINAL_OWNER_PORTS_REQUIRED")
        self.writer = writer
        self._issuer_key = issuer_key
        self._observations = dict(observations)
        self._interval = interval_seconds
        self._sleep = sleeper

    def poll_v1(self, *, allow_release=True):
        try:
            stop = self.writer.repair_projection_v1()
        except (ValueError, OSError, RuntimeError, sqlite3.Error):
            return {"status": "FILEGATE_UNPROVEN"}
        if stop is None:
            return {"status": "NO_CURRENT_STOP"}
        proofs = {}
        blockers = {}
        for role, observe in self._observations.items():
            try:
                if self.writer.inspect_stop_v1() != stop:
                    return {"status": "STOP_SUPERSEDED", "stop": stop}
                observed = observe(stop)
            except (ValueError, OSError, RuntimeError, sqlite3.Error) as exc:
                code = str(exc).split(":", 1)[0]
                blockers[role] = (
                    code
                    if re.fullmatch(r"[A-Z][A-Z0-9_]{3,95}", code)
                    else "OWNER_OBSERVATION_UNAVAILABLE"
                )
                continue
            if observed is not None:
                proofs[role] = observed
        if not allow_release or set(proofs) != EVIDENCE_ROLES:
            return {
                "status": "BLOCKED_OBSERVING",
                "stop": stop,
                "missing_proofs": sorted(EVIDENCE_ROLES - proofs.keys()),
                "owner_blockers": blockers,
            }
        try:
            release = self.writer.issue_release_v1(evidence=proofs, issuer_key=self._issuer_key)
            projection = self.writer.release_v1(release=release, evidence=proofs)
            if self.writer.read_v1() != projection:
                raise FilegateAuthorityError("FAULT_RECOVERY_RELEASE_READBACK_CHANGED")
        except (ValueError, OSError, RuntimeError, sqlite3.Error):
            return {"status": "BLOCKED_OBSERVING", "stop": stop}
        return {
            "status": "SAFETY_RELEASE_CONFIRMED",
            "stop": stop,
            "release_generation": projection["filegate_generation"],
            "release_sha256": projection["filegate_release_sha256"],
        }

    def run_v1(
        self,
        *,
        stop_requested: Callable[[], bool],
        publish_observation: Callable,
        allow_release=True,
    ):
        """Keep an existing service observing across holds, with a bounded polling rate."""
        while not stop_requested():
            result = self.poll_v1(allow_release=allow_release)
            publish_observation(result)
            if result["status"] == "SAFETY_RELEASE_CONFIRMED":
                return result
            if not stop_requested():
                self._sleep(self._interval)
        return {"status": "FAULT_RECOVERY_SERVICE_STOPPED"}


def _proof_path(root, *, stop, role):
    if (
        role not in EVIDENCE_ROLES
        or type(stop["generation"]) is not int
        or not re.fullmatch(r"(?:[0-9a-f]{32}|[0-9a-f]{64})", stop["stop_id"])
        or not root.is_absolute()
        or root.resolve() != root
        or not root.is_dir()
        or root.stat().st_uid != os.getuid()
        or root.stat().st_mode & 0o077
    ):
        raise FilegateAuthorityError("FAULT_OWNER_PROOF_SCOPE_UNPROVEN")
    path = root / f"{stop['generation']}-{stop['stop_id']}-{role}.json"
    if path.resolve() != path or (path.exists() and not path.is_file()):
        raise FilegateAuthorityError("FAULT_OWNER_PROOF_SCOPE_UNPROVEN")
    return path


def publish_managed_owner_proof_v1(*, root, proof):
    """Publish an already signed Owner receipt for the independent service."""
    body = proof["body"]
    path = _proof_path(root, stop=body["stop"], role=body["role"])
    temp = path.with_suffix(".json.tmp")
    if temp.resolve() != temp or (temp.exists() and not temp.is_file()):
        raise FilegateAuthorityError("FAULT_OWNER_PROOF_SCOPE_UNPROVEN")
    atomic_write_json(path=path, payload=proof)


def attest_managed_filegate_integrity_v1(*, writer, stop, expires_at, key):
    """Independently read the re-established original KILLED projection for R03."""
    from src.ops.full_core_live_path_composition_root_v1.durable_filegate_join_v1 import (
        read_durable_filegate_join_evidence_v1,
    )

    if type(writer) is not ManagedFilegateV1 or stop["causes"] != ["R03"]:
        raise FilegateAuthorityError("FAULT_FILEGATE_INTEGRITY_SCOPE_UNPROVEN")
    raw = writer.state_path.read_bytes()
    evidence = read_durable_filegate_join_evidence_v1(state_path=str(writer.state_path))
    if (
        evidence.evidence_status != "TRUSTED_PRESENT"
        or evidence.state_name != "KILLED"
        or evidence.blocked is not True
        or writer.inspect_stop_v1() != stop
        or writer.state_path.read_bytes() != raw
    ):
        raise FilegateAuthorityError("FAULT_FILEGATE_INTEGRITY_SCOPE_UNPROVEN")
    return attest_filegate_owner_evidence_v1(
        role="CAUSE",
        stop=stop,
        evidence_sha256=sha256(raw).hexdigest(),
        observed_at=time.time(),
        expires_at=expires_at,
        key=key,
    )


def build_standing_managed_fault_recovery_v1(*, state_root: Path, runtime_config):
    """Provision the canonical service with signed original proofs from separate owners."""
    if (
        type(runtime_config) is not dict
        or set(runtime_config) != {"proof_root", "issuer_seed_path", "interval_seconds"}
        or not state_root.is_absolute()
    ):
        raise FilegateAuthorityError("HOST_FAULT_RECOVERY_CONFIG_UNPROVEN")
    root = Path(runtime_config["proof_root"])
    key_path = Path(runtime_config["issuer_seed_path"])
    writer = configured_filegate_writer_v1(canonical_kill_switch_state_path())
    if writer is None or not key_path.is_absolute() or key_path.resolve() != key_path:
        raise FilegateAuthorityError("HOST_FAULT_RECOVERY_CONFIG_UNPROVEN")
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(key_path, flags), "rb") as key_file:
        info = os.fstat(key_file.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_nlink != 1
            or info.st_mode & 0o077
            or info.st_size != 32
        ):
            raise FilegateAuthorityError("HOST_FAULT_RECOVERY_ISSUER_SCOPE_UNPROVEN")
        issuer = SigningKey(key_file.read(33))

    def observe(role):
        def read(stop):
            path = _proof_path(root, stop=stop, role=role)
            try:
                return json.loads(path.read_bytes())
            except FileNotFoundError:
                return None

        return read

    return ManagedFaultRecoveryV1(
        writer=writer,
        issuer_key=issuer,
        observations={role: observe(role) for role in EVIDENCE_ROLES},
        interval_seconds=runtime_config["interval_seconds"],
    )
