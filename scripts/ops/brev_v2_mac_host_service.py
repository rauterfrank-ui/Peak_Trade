"""Versioned macOS entry point for recovery of an occupied BREV V2 lane."""

from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import plistlib
import re
import time
from typing import Callable

from scripts.ops.run_offline_occupied_brev_with_cap24_v1 import (
    run_offline_occupied_brev_with_cap24_v1,
)
from src.governance.current_continuous_run_policy_v1 import standing_continuous_run_authorized_v1
from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_run_owner_go_wiring_v1 import (
    validate_bounded_continuous_run_owner_go_decision_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    CurrentProductive29PChainBaselineError,
    assert_current_productive_29p_execution_identity_v1,
)
from src.ops.managed_filegate_v1 import ROOT_ENV
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.startup_factory_v1 import (
    _prepare_occupied_n1_request,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.unattended_v1 import (
    UnattendedHostBoundsV1,
    _filegate_revision,
    unattended_request_digest_v1,
)


SCHEMA = "n1_unattended_brev_host_service.v2"
LABEL = "de.peaktrade.n1-host.v2"
REPO = Path(__file__).resolve().parents[2]
FILEGATE_ENV = "PEAK_KILL_SWITCH_STATE_PATH"


@dataclass(frozen=True)
class BrevHostReplayV2:
    """An in-process simulation input. The manifest cannot construct its ports."""

    open_ports: Callable[..., AbstractContextManager]
    clock: Callable[[], float]


class _HostRefusal(ValueError):
    pass


def _absolute_path(value):
    if not isinstance(value, str):
        raise ValueError("HOST_BREV_V2_PATH_INVALID")
    path = Path(value)
    if not path.is_absolute() or path.resolve() != path:
        raise ValueError("HOST_BREV_V2_PATH_INVALID")
    return path


def _manifest_inputs(value):
    if value.keys() != {
        "schema",
        "repository_root",
        "checkout_sha",
        "sandbox_root",
        "bounds",
        "runtime_request_config",
        "cap24",
        "filegate",
        "mode",
    } or value["mode"] not in ("offline_replay", "scoped_readonly_get"):
        raise ValueError("HOST_BREV_V2_MANIFEST_INVALID")
    if _absolute_path(value["repository_root"]) != REPO:
        raise ValueError("HOST_SERVICE_CHECKOUT_MISMATCH")
    sandbox = _absolute_path(value["sandbox_root"])
    config = value["runtime_request_config"]
    cap24, filegate = value["cap24"], value["filegate"]
    if cap24.keys() != {
        "productivity_root",
        "repository_sha",
        "publication_sha256",
    } or filegate.keys() != {"state_path", "authority_root"}:
        raise ValueError("HOST_BREV_V2_MANIFEST_INVALID")
    _absolute_path(cap24["productivity_root"])
    filegate_path = _absolute_path(filegate["state_path"])
    if not sandbox.is_dir() or not filegate_path.is_relative_to(sandbox):
        raise ValueError("HOST_BREV_V2_SANDBOX_REQUIRED")
    env = {FILEGATE_ENV: str(filegate_path)}
    if filegate["authority_root"] is not None:
        authority = _absolute_path(filegate["authority_root"])
        if authority.is_relative_to(sandbox) or not authority.is_relative_to(sandbox.parent):
            raise ValueError("HOST_BREV_V2_FILEGATE_AUTHORITY_ROOT_INVALID")
        env[ROOT_ENV] = str(authority)

    bounds = UnattendedHostBoundsV1(**value["bounds"])
    bounds.validate_v1()
    if (
        not all(
            re.fullmatch(r"[0-9a-f]{40}", sha)
            for sha in (value["checkout_sha"], bounds.repository_sha, cap24["repository_sha"])
        )
        or not all(
            re.fullmatch(r"[0-9a-f]{64}", digest)
            for digest in (bounds.runtime_config_digest, cap24["publication_sha256"])
        )
        or bounds.repository_sha != config["repository_sha"]
        or config["bound"]["venue_native_id"] != "BREV-USDT-SWAP"
        or (bounds.max_total_cycles, bounds.max_total_seconds, bounds.wait_interval_seconds)
        != (
            config["authorization"]["max_cycles_per_run"],
            config["authorization"]["max_run_duration_seconds"],
            config["authorization"]["wait_interval_seconds"],
        )
    ):
        raise ValueError("HOST_BREV_V2_MANIFEST_BINDING_INVALID")
    return sandbox, bounds, env


def _require_checkout(revision):
    try:
        assert_current_productive_29p_execution_identity_v1(declared_origin_main_sha=revision)
    except CurrentProductive29PChainBaselineError as exc:
        raise _HostRefusal(str(exc)) from exc


def _require_governed_start(value):
    revision = value["checkout_sha"]
    _require_checkout(revision)
    valid_go, reasons = validate_bounded_continuous_run_owner_go_decision_v1(
        repo_root=REPO,
        baseline_origin_main_sha=revision,
    )
    if not valid_go:
        raise _HostRefusal(reasons[0])
    if not standing_continuous_run_authorized_v1(repo_root=REPO):
        raise _HostRefusal("HOST_BREV_V2_STANDING_POLICY_DENIED")
    if (
        value["runtime_request_config"]["repository_sha"] != revision
        or value["cap24"]["repository_sha"] != revision
    ):
        raise _HostRefusal("HOST_BREV_V2_START_REVISION_MISMATCH")


def _run(value, sandbox, bounds, env, replay):
    config = value["runtime_request_config"]
    filegate = Path(env[FILEGATE_ENV])
    state_root = sandbox / "occupied-n1-v2"
    stop_file = state_root / "STOP"
    offline = value["mode"] == "offline_replay"
    if offline and replay is None:
        raise _HostRefusal("HOST_BREV_V2_OFFLINE_FIXTURE_PORTS_REQUIRED")
    if not offline and replay is not None:
        raise _HostRefusal("HOST_BREV_V2_FIXTURE_PORTS_FORBIDDEN")
    if stop_file.exists():
        return {"status": "STOPPED"}
    if time.time() >= bounds.expires_at_unix:
        return {"status": "BOUNDS_EXHAUSTED"}
    if any(os.environ.get(key) != env.get(key) for key in (FILEGATE_ENV, ROOT_ENV)):
        raise _HostRefusal("HOST_BREV_V2_FILEGATE_ENVIRONMENT_CHANGED")
    if offline:
        _require_checkout(value["checkout_sha"])
    else:
        _require_governed_start(value)
    if not filegate.is_file() or not _filegate_revision(filegate):
        raise _HostRefusal("HOST_BREV_V2_FILEGATE_BLOCKED")
    prepared = _prepare_occupied_n1_request(
        attempt_index=1,
        evidence_root=state_root,
        runtime_config=config,
    )
    if unattended_request_digest_v1(prepared) != bounds.runtime_config_digest:
        raise _HostRefusal("HOST_BREV_V2_RUNTIME_DIGEST_MISMATCH")

    @contextmanager
    def open_ports(authorization):
        if stop_file.exists():
            raise _HostRefusal("HOST_BREV_V2_STOP_REQUESTED")
        if offline:
            source = replay.open_ports
        else:
            _require_governed_start(value)
            source = prepared.open_ports
        with source(authorization) as ports:
            yield ports

    def sleep(seconds):
        if stop_file.exists():
            raise _HostRefusal("HOST_BREV_V2_STOP_REQUESTED")
        time.sleep(seconds)

    cap24 = value["cap24"]
    return run_offline_occupied_brev_with_cap24_v1(
        sandbox_root=sandbox,
        runtime_config=config,
        expires_at_unix=bounds.expires_at_unix,
        cap24_productivity_root=Path(cap24["productivity_root"]),
        cap24_repository_sha=cap24["repository_sha"],
        cap24_publication_sha256=cap24["publication_sha256"],
        open_fixture_ports=open_ports,
        replay_clock=replay.clock if offline else time.time,
        sleep=sleep,
    )


def _prepare_plist(path, manifest, sandbox, env):
    payload = {
        "Label": LABEL,
        "ProgramArguments": [
            str(REPO / "scripts/pt"),
            str(REPO / "scripts/ops/peak_trade_runtime.py"),
            "--repository-root",
            str(REPO),
            "host-service",
            "run",
            "--manifest",
            str(manifest.resolve()),
        ],
        "WorkingDirectory": str(REPO),
        "RunAtLoad": True,
        "KeepAlive": {"SuccessfulExit": False},
        "ThrottleInterval": 60,
        "ProcessType": "Background",
        "Umask": 0o077,
        "EnvironmentVariables": env,
        "StandardOutPath": str(sandbox / "host-service-v2.stdout.log"),
        "StandardErrorPath": str(sandbox / "host-service-v2.stderr.log"),
    }
    with path.open("xb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        plistlib.dump(payload, stream)
        stream.flush()
        os.fsync(stream.fileno())


def dispatch_brev_host_service(args, *, replay=None):
    """Handle the V2 manifest on the canonical host-service command."""
    try:
        value = json.loads(args.manifest.read_bytes())
    except (OSError, UnicodeError, ValueError):
        return None
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        return None

    result = {"ok": True, "service_activated": False, "external_effect_authorized": False}
    try:
        sandbox, bounds, env = _manifest_inputs(value)
        if args.repository_root is not None and Path(args.repository_root).resolve() != REPO:
            raise ValueError("HOST_SERVICE_CHECKOUT_MISMATCH")
        if args.owner_role is not None or args.owner_seed_path is not None:
            raise ValueError("HOST_BREV_V2_OWNER_ACTION_UNSUPPORTED")
        if args.action == "validate":
            result.update(manifest_valid=True, runtime_ports_validated=False)
        elif args.action == "prepare" and args.output_path is not None:
            _prepare_plist(args.output_path, args.manifest, sandbox, env)
            result["plist_path"] = str(args.output_path)
        elif args.action == "run":
            state = _run(value, sandbox, bounds, env, replay)
            result["result"] = {
                key: state[key]
                for key in ("status", "reason", "cap24_confirmation")
                if key in state
            }
            result["ok"] = state["status"] in ("FINISHED", "STOPPED", "BOUNDS_EXHAUSTED")
        else:
            raise ValueError("HOST_BREV_V2_ACTION_INVALID")
    except _HostRefusal as exc:
        if str(exc) == "HOST_BREV_V2_STOP_REQUESTED":
            result.update(result={"status": "STOPPED"})
        else:
            result.update(ok=False, error_code=str(exc))
    except (AttributeError, KeyError, OSError, TypeError, ValueError) as exc:
        code = str(exc)
        result.update(
            ok=False, error_code=code if code.startswith("HOST_") else "HOST_BREV_V2_REFUSED"
        )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 75
