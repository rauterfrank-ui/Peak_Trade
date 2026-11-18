"""Offline N1 occupied-scope recovery using the original S6 and budget owners."""

from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sqlite3
import time

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
    AuthorizationLifecycleLockV1,
    LifecycleLockError,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.process_identity_v1 import (
    capture_process_identity,
    read_local_boot_identity_v1,
)
from src.ops.execution_reconciliation_get_provenance_v1 import AuthenticatedReconciliationGetV1
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_governed_continuous_cycle_orchestrator_v1 as s6,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from src.ops.managed_filegate_v1 import (
    configured_filegate_writer_v1,
    read_configured_filegate_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.startup_binding_v1 import (
    acquire_account_bound_n1_startup_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.startup_factory_v1 import (
    _prepare_occupied_n1_request,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    budget_owner_root_for_config_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.unattended_v1 import (
    _filegate_revision,
    unattended_request_digest_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    PortfolioBudgetHostV1,
    StandingStartupAccountObservationPortV1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.recovery_v1 import (
    bounded_retry_policy_v1,
)

from .cap24 import reconcile_cap24_owned_position_v1
from .checkpoint import occupied_wait_checkpoint_v1, verify_occupied_wait_checkpoint_v1


CHECKPOINT_FILENAME = "occupied_scope_wait_v2.json"
_OWNER = "n1_occupied_scope_recovery_v2"
_LANE = "LANE_1"
_INSTRUMENT = "BREV-USDT-SWAP"


def _read(path):
    if path.resolve() != path:
        raise ValueError("N1_V2_CHECKPOINT_PATH_CHANGED")
    raw = path.read_bytes()
    return json.loads(raw), sha256(raw).hexdigest()


def _native_wait(attempt_root, *, cursor_root, lock, native_id):
    ledger, ledger_sha = _read(attempt_root / s6.LEDGER_FILENAME)
    inner_lock, inner_sha = _read(attempt_root / "s6-lock" / s6.LOCK_NAME)
    cursor_sha = sha256((cursor_root / CURSOR_FILENAME).read_bytes()).hexdigest()
    context = inner_lock["recovery_context"]
    consumed = ledger["consumed_instance_ids"]
    if (
        ledger["state"] != s6.STATE_WAITING_FOR_NEXT_C1
        or ledger["occupied_mark_only"] is not True
        or ledger["native_id"] != native_id
        or ledger["continuous_owner_go"] != s6.RUNTIME_OWNER_GO
        or ledger["POST_COUNT"] != "0"
        or ledger["PERMIT_CREATED"] != s6.FALSE_TOKEN
        or ledger["EXTERNAL_EFFECT_COUNT"] != "0"
        or ledger["checkpoint_cursor_sha256"] != cursor_sha
        or type(ledger["s5_invoke_count"]) is not int
        or ledger["s5_invoke_count"] != len(set(consumed))
        or len(consumed) != len(set(consumed))
        or inner_lock["owner"] != s6.__name__.rsplit(".", 1)[-1]
        or inner_lock["authorization_id"] != s6.LOCK_AUTHORIZATION_ID
        or inner_lock["writer_identity"] != f"{inner_lock['owner']}:{s6.LOCK_AUTHORIZATION_ID}"
        or not inner_lock["claim_id"]
        or inner_lock["pid"] != lock["pid"]
        or context["process_identity"] != lock["recovery_context"]["process_identity"]
        or context["boot_identity"] != lock["recovery_context"]["boot_identity"]
        or context["evidence_root"] != str(attempt_root)
        or context["cursor_store_root"] != str(cursor_root)
        or context["binding_digest"] != ledger["binding_digest"]
    ):
        raise ValueError("N1_V2_ORIGINAL_WAIT_UNPROVEN")
    return {
        "ledger_sha256": ledger_sha,
        "s6_lock_sha256": inner_sha,
        "cursor_sha256": cursor_sha,
        "cycles": ledger["s5_invoke_count"],
    }


def run_offline_occupied_n1_v2(
    *,
    sandbox_root: Path,
    runtime_config: dict,
    expires_at_unix: float,
    open_fixture_ports,
    replay_clock=time.time,
    sleep=time.sleep,
    allow_offline_first_fill: bool = False,
):
    """Run BREV with explicitly supplied replay ports and recover its original WAIT.

    The caller supplies simulated GET data. This entry point has no transport
    factory, service action, order port, or runtime authorization of its own.
    A first attempt may explicitly hand an observed full fill to the portfolio owner.
    """
    root = Path(sandbox_root)
    if (
        root.resolve() != root
        or not root.is_dir()
        or runtime_config["bound"]["venue_native_id"] != _INSTRUMENT
    ):
        raise ValueError("N1_V2_OFFLINE_BREV_ROOT_REQUIRED")
    if not callable(open_fixture_ports) or not math.isfinite(expires_at_unix):
        raise ValueError("N1_V2_FIXTURE_PORTS_AND_BOUNDS_REQUIRED")
    state_root = root / "occupied-n1-v2"
    attempts = state_root / "attempts"
    prepared = _prepare_occupied_n1_request(
        attempt_index=1, evidence_root=state_root, runtime_config=runtime_config
    )
    request = prepared.request
    config, bound, auth = (request[key] for key in ("config", "bound", "authorization"))
    revision = request["origin_main_sha"]
    proof_root = request["occupied_mark_proof_root"]
    filegate = Path(config.kill_switch_state_path)
    lock_path = config.lock_root / s6.LOCK_NAME
    cursor_root = config.lane_state_root / _LANE
    budget_root = budget_owner_root_for_config_v1(config)
    db = budget_root / "owner/reservations.sqlite3"
    for path in (
        state_root,
        attempts,
        config.public_store_root,
        config.private_store_root,
        lock_path,
        config.cap24_productivity_root,
        cursor_root,
        db,
        filegate,
        proof_root,
    ):
        if not path.is_relative_to(root) or path.resolve() != path:
            raise ValueError("N1_V2_MUTABLE_ROOT_OUTSIDE_REPLAY")
    filegate_revision = _filegate_revision(filegate)
    if not filegate.is_file() or filegate_revision is None:
        return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": "N1_V2_FILEGATE_BLOCKED"}
    managed = configured_filegate_writer_v1(filegate)
    if managed is not None and (
        not managed.root.is_relative_to(root.parent) or managed.root.is_relative_to(root)
    ):
        raise ValueError("N1_V2_INDEPENDENT_FILEGATE_OUTSIDE_REPLAY")
    release = (read_configured_filegate_v1(filegate) or {}).get("filegate_release_sha256")
    binding = unattended_request_digest_v1(prepared)
    boot = read_local_boot_identity_v1()
    if not boot:
        raise ValueError("N1_V2_BOOT_IDENTITY_REQUIRED")
    now = time.time()
    try:
        prior = _read(lock_path)[0] if lock_path.exists() else None
    except (OSError, ValueError):
        return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": "N1_V2_ORIGINAL_WAIT_UNPROVEN"}
    if prior is not None and not isinstance(prior, dict):
        return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": "N1_V2_ORIGINAL_WAIT_UNPROVEN"}
    previous = None if prior is None else prior.get("recovery_context", {})
    if prior is not None and (
        not isinstance(previous, dict)
        or prior.get("owner") != _OWNER
        or previous.get("binding") != binding
        or previous.get("state_root") != str(state_root)
        or type(previous.get("attempt")) is not int
        or previous["attempt"] < 1
        or type(previous.get("cycles_before")) is not int
        or not 0 <= previous["cycles_before"] <= auth.max_cycles_per_run
        or type(previous.get("deadline")) not in {int, float}
        or not math.isfinite(previous["deadline"])
    ):
        return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": "N1_V2_LOCK_BINDING_CHANGED"}
    if previous is None and attempts.exists():
        return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": "N1_V2_PREVIOUS_LOCK_REQUIRED"}
    attempt = 1 if previous is None else previous["attempt"] + 1
    deadline = min(expires_at_unix, now + auth.max_run_duration_seconds)
    if previous is not None:
        deadline = min(deadline, previous["deadline"])
    if (
        deadline <= now
        or not bounded_retry_policy_v1(attempt=attempt - 1, automatic_recovery_allowed=True)[
            "retry_allowed"
        ]
    ):
        return {"status": "BOUNDS_EXHAUSTED"}
    attempt_root = attempts / str(attempt)
    admitted = None
    cycles = 0
    if previous is not None:
        try:
            old_root = attempts / str(previous["attempt"])
            prior_wait = _native_wait(
                old_root, cursor_root=cursor_root, lock=prior, native_id=_INSTRUMENT
            )
            cycles = previous["cycles_before"] + prior_wait["cycles"]
        except (AttributeError, OSError, KeyError, TypeError, ValueError):
            return {
                "status": "RECOVERY_CHECKPOINT_REQUIRED",
                "reason": "N1_V2_ORIGINAL_WAIT_UNPROVEN",
            }
    remaining = auth.max_cycles_per_run - cycles
    if remaining <= 0:
        return {"status": "BOUNDS_EXHAUSTED"}

    def verify_dead_owner(receipt):
        nonlocal admitted
        if receipt != prior or previous is None:
            return False
        try:
            old_root = attempts / str(previous["attempt"])
            checkpoint, checkpoint_sha = _read(old_root / CHECKPOINT_FILENAME)
            _, outer_sha = _read(lock_path)
            if (
                checkpoint["schema"] != _OWNER
                or checkpoint["outer_lock_sha256"] != outer_sha
                or checkpoint["binding"] != binding
                or checkpoint["repository_sha"] != revision
                or checkpoint["filegate_revision"] != filegate_revision
                or checkpoint["cycles_before"] != previous["cycles_before"]
                or checkpoint["native_wait"] != prior_wait
                or checkpoint["store_identity"] != [db.stat().st_dev, db.stat().st_ino]
                or checkpoint["native_wait"]
                != _native_wait(
                    old_root, cursor_root=cursor_root, lock=receipt, native_id=_INSTRUMENT
                )
            ):
                return False
            if previous["boot_identity"] != boot or managed is not None:
                if managed is None or managed.read_host_checkpoint_v1(lock_path=lock_path) != {
                    "lock_sha256": outer_sha,
                    "ledger_sha256": checkpoint_sha,
                    "cursor_sha256": checkpoint["native_wait"]["cursor_sha256"],
                    "repository_sha": revision,
                }:
                    return False
            if not verify_occupied_wait_checkpoint_v1(
                checkpoint["scope"],
                cursor_root=cursor_root,
                budget_root=db.parent,
                account=config.expected_account_identity,
                native_id=_INSTRUMENT,
            ):
                return False
            admitted = checkpoint
            return True
        except (AttributeError, OSError, KeyError, TypeError, ValueError, sqlite3.Error):
            return False

    lock = AuthorizationLifecycleLockV1(
        lock_path=lock_path,
        authorization_id=_OWNER,
        owner=_OWNER,
        recover_dead_local_owner=True,
        recovery_context={
            "attempt": attempt,
            "binding": binding,
            "boot_identity": boot,
            "cycles_before": cycles,
            "deadline": deadline,
            "process_identity": capture_process_identity(os.getpid()).to_dict(),
            "state_root": str(state_root),
        },
        dead_owner_validator=verify_dead_owner,
    )
    try:
        lock.acquire()
    except LifecycleLockError:
        return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": "N1_V2_ORIGINAL_WAIT_UNPROVEN"}
    try:
        if previous is not None and admitted is None:
            return {
                "status": "RECOVERY_CHECKPOINT_REQUIRED",
                "reason": "N1_V2_PREVIOUS_LOCK_REQUIRED",
            }
        attempt_root.mkdir(parents=True)
        if deadline <= time.time():
            return {"status": "BOUNDS_EXHAUSTED"}
        if _filegate_revision(filegate) != filegate_revision:
            return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": "N1_V2_FILEGATE_BLOCKED"}
        auth = replace(
            auth, max_cycles_per_run=remaining, max_run_duration_seconds=deadline - time.time()
        )
        return _run_attempt(
            attempt_root=attempt_root,
            auth=auth,
            bound=bound,
            config=config,
            request=request,
            revision=revision,
            proof_root=proof_root,
            filegate=filegate,
            filegate_revision=filegate_revision,
            managed=managed,
            release=release,
            lock=lock,
            cursor_root=cursor_root,
            db=db,
            admitted=admitted,
            cycles=cycles,
            binding=binding,
            open_fixture_ports=open_fixture_ports,
            replay_clock=replay_clock,
            sleep=sleep,
            allow_offline_first_fill=allow_offline_first_fill is True and previous is None,
        )
    finally:
        lock.release()


def _run_attempt(
    *,
    attempt_root,
    auth,
    bound,
    config,
    request,
    revision,
    proof_root,
    filegate,
    filegate_revision,
    managed,
    release,
    lock,
    cursor_root,
    db,
    admitted,
    cycles,
    binding,
    open_fixture_ports,
    replay_clock,
    sleep,
    allow_offline_first_fill=False,
):
    def wait(seconds):
        # The original S6 calls its sleeper after publishing a native WAIT.
        # Its other sleeps must never publish recovery evidence.
        ledger, _ = _read(attempt_root / s6.LEDGER_FILENAME)
        if ledger["state"] == s6.STATE_WAITING_FOR_NEXT_C1:
            lock.assert_held()
            if _filegate_revision(filegate) != filegate_revision:
                raise ValueError("N1_V2_FILEGATE_CHANGED")
            outer, outer_sha = _read(lock.lock_path)
            native_wait = _native_wait(
                attempt_root, cursor_root=cursor_root, lock=outer, native_id=_INSTRUMENT
            )
            scope = occupied_wait_checkpoint_v1(
                host=host, cursor_root=cursor_root, native_id=_INSTRUMENT
            )
            path = attempt_root / CHECKPOINT_FILENAME
            atomic_write_json(
                path=path,
                payload={
                    "schema": _OWNER,
                    "outer_lock_sha256": outer_sha,
                    "binding": binding,
                    "repository_sha": revision,
                    "native_wait": native_wait,
                    "scope": scope,
                    "filegate_revision": filegate_revision,
                    "cycles_before": cycles,
                    "store_identity": [db.stat().st_dev, db.stat().st_ino],
                },
            )
            if managed is not None:
                _, checkpoint_sha = _read(path)
                managed.set_host_checkpoint_v1(
                    lock_path=lock.lock_path,
                    checkpoint={
                        "lock_sha256": outer_sha,
                        "ledger_sha256": checkpoint_sha,
                        "cursor_sha256": native_wait["cursor_sha256"],
                        "repository_sha": revision,
                    },
                    expected_release_sha256=release,
                )
        sleep(seconds)

    with open_fixture_ports(auth) as ports:
        host = PortfolioBudgetHostV1(
            root=db.parents[1],
            private_rest_fetch=ports["private_rest_fetch"],
            repository_sha=revision,
            session_id=f"occupied-n1-v2:{attempt_root.name}",
            expected_account_identity=config.expected_account_identity,
            clock=replay_clock,
            reconciliation_transport=ports["pretrade_transport"],
            execution_incident_state_path=filegate,
        )
        try:

            def reconcile(observation):
                if observation.pending_orders:
                    raise ValueError("N1_V2_STARTUP_PENDING_ORDERS")
                capture = AuthenticatedReconciliationGetV1(
                    host.reconciliation_transport,
                    account=host.account,
                    clock=replay_clock,
                    proof_root=proof_root,
                )
                context = host._bind_observation_v1(
                    {_LANE: bound},
                    observation,
                    capture=capture,
                    deliver_authenticated_incidents=True,
                )
                capture.discard_response_bodies_v1()
                reconcile_cap24_owned_position_v1(
                    context=replace(context, authenticated_reconciliation=capture),
                    productivity_root=config.cap24_productivity_root,
                    proof_root=proof_root,
                    allow_offline_first_fill=allow_offline_first_fill,
                )

            acquire_account_bound_n1_startup_v1(
                productivity_root=config.cap24_productivity_root,
                repository_sha=revision,
                binding_epoch=datetime.fromtimestamp(replay_clock(), timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                expected_account_identity=config.expected_account_identity,
                session_id=host.session_id,
                private_rest_fetch=StandingStartupAccountObservationPortV1(
                    fetch=ports["private_rest_fetch"],
                    reconcile=reconcile,
                ),
                expected_bound=bound,
                clock=replay_clock,
            )
            if admitted is not None and not verify_occupied_wait_checkpoint_v1(
                admitted["scope"],
                cursor_root=cursor_root,
                budget_root=db.parent,
                account=config.expected_account_identity,
                native_id=_INSTRUMENT,
                admitted_host=host,
            ):
                raise ValueError("N1_V2_STARTUP_ORIGINAL_HOLD_CHANGED")
            result = run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1(
                authorization=auth,
                origin_main_sha=revision,
                lane_state_root=config.lane_state_root,
                bound=bound,
                g17_producers=ports["g17_producers"],
                observation_source=ports["observation_source"],
                evidence_root=attempt_root,
                f1_m9_cycle_evaluator=ports["f1_m9_cycle_evaluator"],
                repo_root=request["repo_root"],
                lock_root=attempt_root / "s6-lock",
                sleep_fn=wait,
                fresh_pretrade_get_transport=ports["pretrade_transport"],
                cap24_productivity_root=config.cap24_productivity_root,
                portfolio_budget_host=host,
                occupied_mark_proof_root=proof_root,
                cancel_requested=lambda: _filegate_revision(filegate) != filegate_revision,
            )
            return {"status": "FINISHED", "result": result}
        finally:
            host.close()
