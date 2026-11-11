"""Read execution incidents independently of the order host."""

from __future__ import annotations

import argparse
import fcntl
import json
import math
import os
import plistlib
import stat
import sys
import time
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
)
from src.ops.execution_incident_safety_v1 import (
    AuthenticatedExecutionIncidentScopeV1,
    ExecutionIncidentObservationError,
    ExecutionIncidentSafetyError,
    OfflineExecutionIncidentScopeV1,
    observe_offline_execution_incident_v1,
    observe_standing_execution_incident_v1,
)

_LATEST = "execution-incident-diagnostics-latest-v1.json"
_SERVICE_LABEL = "de.peaktrade.execution-incident-diagnostics.v1"
_MODULE = "src.ops.execution_incident_diagnostics_v1"


def _check_polling(interval_seconds, samples):
    if (
        type(interval_seconds) not in (float, int)
        or not math.isfinite(interval_seconds)
        or interval_seconds <= 0
        or (samples is not None and (type(samples) is not int or samples < 1))
    ):
        raise ValueError("INCIDENT_DIAGNOSTIC_BOUNDS_INVALID")


from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)


def iter_offline_execution_incident_diagnostics_v1(
    *,
    scope: OfflineExecutionIncidentScopeV1,
    envelope: FinalOrderEnvelopeV1,
    interval_seconds: float,
    samples: int,
) -> Iterator[dict]:
    """Read the original gate on each sample. A lost observation is never an all-clear."""
    if samples is None:
        raise ValueError("INCIDENT_DIAGNOSTIC_BOUNDS_INVALID")
    _check_polling(interval_seconds, samples)
    assert_envelope_unmodified_v1(envelope)
    for index in range(samples):
        if index:
            time.sleep(interval_seconds)
        try:
            observed = observe_offline_execution_incident_v1(scope=scope, envelope=envelope)
        except (ExecutionIncidentObservationError, OSError) as exc:
            yield {
                "observation_status": "UNAVAILABLE",
                "observation_error": (
                    str(exc)
                    if isinstance(exc, ExecutionIncidentObservationError)
                    else "INCIDENT_FILEGATE_READ_FAILED"
                ),
                "correlated_incident_veto": False,
            }
        else:
            yield {"observation_status": "OBSERVED", **observed}


def _standing_scope(*, budget_host_root: Path, filegate: Path, account: str, output_root: Path):
    if (
        any(
            not path.is_absolute() or path.resolve() != path
            for path in (budget_host_root, filegate, output_root)
        )
        or not account
        or account.strip() != account
    ):
        raise ValueError("INCIDENT_DIAGNOSTIC_SOURCE_PATH_UNPROVEN")
    if (
        output_root.is_relative_to(budget_host_root)
        or budget_host_root.is_relative_to(output_root)
        or filegate.is_relative_to(output_root)
        or output_root.is_relative_to(filegate.parent / "backups")
    ):
        raise ValueError("INCIDENT_DIAGNOSTIC_OUTPUT_OVERLAPS_SOURCE")
    return AuthenticatedExecutionIncidentScopeV1(
        budget_host_root / "execution-incident-safety", account, filegate
    )


def _require_private_output_root(output_root):
    output_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    info = output_root.stat()
    if output_root.resolve() != output_root or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("INCIDENT_DIAGNOSTIC_OUTPUT_NOT_PRIVATE")


def _require_safe_output_file(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
        raise ValueError("INCIDENT_DIAGNOSTIC_OUTPUT_PATH_UNPROVEN")


def run_standing_execution_incident_diagnostics_v1(
    *,
    budget_host_root: Path,
    filegate: Path,
    account: str,
    output_root: Path,
    interval_seconds: float,
    samples: int | None = None,
) -> None:
    """Publish one replaceable observation until the independent process stops."""
    _check_polling(interval_seconds, samples)
    scope = _standing_scope(
        budget_host_root=budget_host_root,
        filegate=filegate,
        account=account,
        output_root=output_root,
    )
    _require_private_output_root(output_root)
    latest = output_root / _LATEST
    lock_path = output_root / "execution-incident-diagnostics.lock"
    flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(lock_path, flags, 0o600), "r+b") as lock:
        info = os.fstat(lock.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
            or info.st_nlink != 1
        ):
            raise ValueError("INCIDENT_DIAGNOSTIC_LOCK_UNPROVEN")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        started = datetime.now(timezone.utc).isoformat()
        index = 0
        while samples is None or index < samples:
            if index:
                time.sleep(interval_seconds)
            index += 1
            try:
                observation = observe_standing_execution_incident_v1(scope=scope)
            except (ExecutionIncidentSafetyError, OSError) as exc:
                observation = {
                    "observation_status": "UNAVAILABLE",
                    "observation_error": (
                        str(exc)
                        if isinstance(exc, ExecutionIncidentSafetyError)
                        else "INCIDENT_FILEGATE_READ_FAILED"
                    ),
                    "state_name": None,
                    "evidence_status": None,
                    "filegate_blocked": None,
                    "incident_id": None,
                    "kill_revision": None,
                    "acceptance": None,
                    "incident_evidence_error": None,
                    "incident_type": None,
                    "reconciliation_reason": None,
                    "incident_source": None,
                    "raw_get_proof_status": None,
                    "transport_abort": None,
                    "post_safety_veto": None,
                    "original_post_veto_checked": False,
                    "correlated_incident_veto": False,
                }
            else:
                observation["observation_status"] = "OBSERVED"
                observation["observation_error"] = None
            _require_safe_output_file(latest)
            _require_safe_output_file(latest.with_suffix(".json.tmp"))
            atomic_write_json(
                path=latest,
                payload={
                    "schema": "standing_execution_incident_diagnostics.v1",
                    "runtime_authorization_effect": "NONE",
                    "source_scope": scope.binding(),
                    "pid": os.getpid(),
                    "process_started_at_utc": started,
                    "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                    "poll_interval_seconds": interval_seconds,
                    "sample_sequence": index,
                    **observation,
                },
            )


def prepare_standing_diagnostics_launch_agent_v1(
    *,
    destination: Path,
    budget_host_root: Path,
    filegate: Path,
    account: str,
    output_root: Path,
    interval_seconds: float,
) -> dict:
    """Prepare the separate read-only service definition for launchd."""
    _check_polling(interval_seconds, None)
    _standing_scope(
        budget_host_root=budget_host_root,
        filegate=filegate,
        account=account,
        output_root=output_root,
    )
    if (
        not destination.is_absolute()
        or destination.resolve() != destination
        or destination.is_relative_to(budget_host_root)
        or destination in {filegate, filegate.with_suffix(".tmp")}
        or destination == filegate.with_name(filegate.name + ".execution-incident.lock")
        or destination.is_relative_to(filegate.parent / "backups")
    ):
        raise ValueError("INCIDENT_DIAGNOSTIC_SERVICE_PATH_UNPROVEN")
    repo = Path(__file__).resolve().parents[2]
    arguments = [
        str(repo / "scripts/pt"),
        "-m",
        _MODULE,
        "standing",
        "--budget-host-root",
        str(budget_host_root),
        "--filegate",
        str(filegate),
        "--account",
        account,
        "--output-root",
        str(output_root),
        "--interval-seconds",
        str(interval_seconds),
    ]
    payload = {
        "Label": _SERVICE_LABEL,
        "ProgramArguments": arguments,
        "EnvironmentVariables": {"PEAK_KILL_SWITCH_STATE_PATH": str(filegate)},
        "WorkingDirectory": str(repo),
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 60,
        "ProcessType": "Background",
        "Umask": 0o077,
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    with os.fdopen(os.open(destination, flags, 0o600), "wb") as stream:
        plistlib.dump(payload, stream)
    return {"plist_path": str(destination), "service_activated": False}


def _standing_main(argv):
    parser = argparse.ArgumentParser(description="Run independent FILEGATE diagnostics.")
    parser.add_argument("--budget-host-root", type=Path, required=True)
    parser.add_argument("--filegate", type=Path, required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--interval-seconds", type=float, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--samples", type=int)
    mode.add_argument("--prepare-launch-agent", type=Path)
    args = parser.parse_args(argv)
    request = dict(
        budget_host_root=args.budget_host_root,
        filegate=args.filegate,
        account=args.account,
        output_root=args.output_root,
        interval_seconds=args.interval_seconds,
    )
    if args.prepare_launch_agent is None:
        run_standing_execution_incident_diagnostics_v1(**request, samples=args.samples)
    else:
        print(
            json.dumps(
                prepare_standing_diagnostics_launch_agent_v1(
                    **request, destination=args.prepare_launch_agent
                ),
                sort_keys=True,
            )
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Emit observations as JSON lines. Invoke through the repository launcher."""
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "standing":
        return _standing_main(argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--started-at", type=datetime.fromisoformat, required=True)
    parser.add_argument("--envelope", type=Path, required=True)
    parser.add_argument("--interval-seconds", type=float, required=True)
    parser.add_argument("--samples", type=int, required=True)
    args = parser.parse_args(argv)
    scope = OfflineExecutionIncidentScopeV1(
        args.root, args.account, args.session_id, args.started_at
    )
    envelope = FinalOrderEnvelopeV1(**json.loads(args.envelope.read_text()))
    for observation in iter_offline_execution_incident_diagnostics_v1(
        scope=scope, envelope=envelope, interval_seconds=args.interval_seconds, samples=args.samples
    ):
        print(json.dumps(observation, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
