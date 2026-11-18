"""Continue the sealed N1 occupied-mark supervisor after a booked net reversal."""

from dataclasses import asdict, replace
import fcntl
from hashlib import sha256
import json
import math
from pathlib import Path
import time

from src.governance.current_continuous_run_policy_v1 import (
    standing_continuous_run_authorized_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    _occupied_close_attempt_root_v1,
    bind_occupied_lane_governed_cycle_store_roots_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_run_owner_go_wiring_v1 import (
    validate_bounded_continuous_run_owner_go_decision_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
    _net_reversal_submit_root_v1,
    _read_retained_net_reversal_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    LEDGER_FILENAME,
    LOCK_NAME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    build_s8_occupied_lane_pairs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    load_external_effect_durable_consume_v1,
)
from src.ops.gates.risk_gate import canonical_kill_switch_state_path
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.constants_v1 import (
    TRANSPORT_SCOPE_SCOPED_READONLY_GET,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    budget_owner_root_for_config_v1,
    run_n1_standing_pre_external_supervisor_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.unattended_v1 import (
    PreparedN1RequestV1,
    UnattendedHostBoundsV1,
    _FilegateObservationSource,
    _filegate_cycle_evaluator,
    _filegate_revision,
    _write,
    unattended_request_digest_v1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
    read_occupied_scope_mark_snapshot_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.constants_v1 import (
    DEFAULT_BOUNDED_RETRY_LIMIT,
)


_REVERSAL_TERMINAL = "NET_REVERSAL_RECONCILIATION_REQUIRED"
_PORTS = {
    "observation_source",
    "g17_producers",
    "f1_m9_cycle_evaluator",
    "public_rest_fetch",
    "private_rest_fetch",
    "pretrade_transport",
    "net_reversal_post_port",
}


def _submitted_reversal(request):
    config = request["config"]
    lane = build_s8_occupied_lane_pairs_v1(
        lane_state_root=config.lane_state_root, bound=request["bound"]
    )["LANE_1"]
    scope = read_occupied_scope_mark_snapshot_v1(Path(lane[0].lane_state_root))
    episode = scope["mark"].get("pending_reversal_episode_id") if scope else None
    if episode is None:
        return None
    root = _net_reversal_submit_root_v1(budget_owner_root_for_config_v1(config), episode)
    send = load_external_effect_durable_consume_v1(store_root=root)
    record = send["record"]
    if (
        send["durable_consumed"] is not True
        or record is None
        or record.get("transport_attempt", {}).get("phase") != "MAY_HAVE_SENT"
    ):
        return None
    reversal, envelope = _read_retained_net_reversal_v1(lane, scope)
    if (record["envelope_id"], record["envelope_digest"]) != (
        envelope.envelope_id,
        envelope.envelope_digest,
    ) or reversal.episode.account_scope.account_identity != config.expected_account_identity:
        raise ValueError("N1_V2_SUBMITTED_REVERSAL_BINDING_MISMATCH")
    return {
        "episode_id": episode,
        "envelope_digest": envelope.envelope_digest,
        "reservation_id": reversal.old_reservation_id,
        "s5_evidence_root": str(
            _occupied_close_attempt_root_v1(
                bind_occupied_lane_governed_cycle_store_roots_v1({"LANE_1": lane})["LANE_1"][2],
                cycle_id=scope["mark"]["cycle_id"],
                lane_id="LANE_1",
                authenticated=True,
            )
        ),
    }


def _reversal_cycle_count(evidence, request, submitted, limit):
    ledger = json.loads((evidence / LEDGER_FILENAME).read_bytes())
    cycles = ledger["occupied_mark_cycles"]
    count = len(cycles)
    if (
        ledger["occupied_mark_only"] is not True
        or ledger["native_id"] != request["authorization"].native_id
        or ledger["state"] != "FAILED_STOP"
        or ledger["reason_code"] != "DIRECT_REVERSAL_EXECUTION_ADMISSION_REQUIRED"
        or ledger["POST_COUNT"] != "0"
        or count != ledger["s5_invoke_count"]
        or not 0 < count <= limit
        or cycles[-1]["s5_evidence_root"] != submitted["s5_evidence_root"]
    ):
        raise ValueError("N1_V2_REVERSAL_CYCLE_UNPROVEN")
    return count


def _continues(prior, current):
    return current is not None and (
        prior is None
        or (
            current["episode_id"] == prior["envelope_digest"]
            and current["reservation_id"] == prior["reservation_id"]
        )
    )


def run_occupied_n1_net_reversal_host_v2(
    *,
    bounds: UnattendedHostBoundsV1,
    state_root: Path,
    request_factory,
    clock=time.time,
):
    """Run the occupied N1 lane with one persisted allowance across reversals.

    Only a durable original send can reopen the mark path. The sealed supervisor
    checks the actual fills and booking before reading the next mark. A retained
    S6 lock or an unproven interrupted mark cycle requires its original owner.
    """
    bounds.validate_v1()
    root = Path(state_root)
    if not root.is_absolute() or root != root.resolve():
        raise ValueError("N1_V2_STATE_ROOT_NOT_CANONICAL")
    created = not root.exists()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    filegate = Path(canonical_kill_switch_state_path()).resolve()
    binding = sha256(json.dumps(asdict(bounds), sort_keys=True).encode()).hexdigest()
    receipt = root / "occupied_host_state_v2.json"
    with (root / "occupied_host.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if created:
            state = {
                "binding": binding,
                "started_at": clock(),
                "filegate_path": str(filegate),
                "filegate_revision": _filegate_revision(filegate),
                "attempt": 0,
                "attempt_limit": 0,
                "interrupted_retries": 0,
                "cycles_used": 0,
                "awaiting": None,
                "status": "READY",
            }
            if receipt.exists():
                raise ValueError("N1_V2_STATE_ALREADY_CREATED")
            _write(receipt, state)
        else:
            state = json.loads(receipt.read_bytes())
            if state["binding"] != binding or state["filegate_path"] != str(filegate):
                raise ValueError("N1_V2_HOST_BINDING_CHANGED")
        if (
            type(state["attempt"]) is not int
            or state["attempt"] < 0
            or type(state["attempt_limit"]) is not int
            or not 0 <= state["attempt_limit"] <= bounds.max_total_cycles
            or type(state["cycles_used"]) is not int
            or not 0 <= state["cycles_used"] <= bounds.max_total_cycles
            or type(state["interrupted_retries"]) is not int
            or not 0 <= state["interrupted_retries"] <= DEFAULT_BOUNDED_RETRY_LIMIT
            or not math.isfinite(state["started_at"])
        ):
            raise ValueError("N1_V2_HOST_STATE_UNPROVEN")

        def save(status):
            state["status"] = status
            _write(receipt, state)
            return dict(state)

        def remaining():
            now = clock()
            if not math.isfinite(now) or now < state["started_at"]:
                return 0
            return min(
                bounds.expires_at_unix - now, bounds.max_total_seconds - (now - state["started_at"])
            )

        def blocked():
            return state["filegate_revision"] in (None, "UNCONFIGURED") or (
                _filegate_revision(filegate) != state["filegate_revision"]
            )

        if state["status"] not in {"READY", "RUNNING", "AWAITING_BOOKING"}:
            return dict(state)
        while True:
            if (root / "STOP").exists():
                return save("STOPPED")
            if blocked():
                return save("FILEGATE_BLOCKED")
            settlement_only = state["cycles_used"] == bounds.max_total_cycles
            if remaining() <= 0 or (settlement_only and state["awaiting"] is None):
                return save("BOUNDS_EXHAUSTED")
            attempt = state["attempt"] + 1
            evidence = root / "attempts" / str(attempt)
            prepared = request_factory(attempt, evidence)
            if type(prepared) is not PreparedN1RequestV1:
                raise ValueError("N1_V2_PREPARED_REQUEST_REQUIRED")
            request = dict(prepared.request)
            config = request["config"]
            if (
                config.evidence_root != evidence
                or config.transport_scope != TRANSPORT_SCOPE_SCOPED_READONLY_GET
                or request["origin_main_sha"] != bounds.repository_sha
                or not request.get("occupied_mark_proof_root")
                or request.get("skip_owner_go_validation")
                or unattended_request_digest_v1(prepared) != bounds.runtime_config_digest
            ):
                raise ValueError("N1_V2_REQUEST_BINDING_CHANGED")
            repo = Path(__file__).resolve().parents[2]
            valid, _ = validate_bounded_continuous_run_owner_go_decision_v1(
                repo_root=repo, baseline_origin_main_sha=bounds.repository_sha
            )
            if not valid or not standing_continuous_run_authorized_v1(repo_root=repo):
                return save("GOVERNED_RUNTIME_STOPPED")
            if (Path(config.lock_root) / LOCK_NAME).exists():
                return save("OCCUPIED_MARK_CHECKPOINT_UNPROVEN")
            retained = _submitted_reversal(request)
            awaited = state["awaiting"]
            if state["status"] == "RUNNING":
                prior_evidence = root / "attempts" / str(state["attempt"])
                if (prior_evidence / LEDGER_FILENAME).exists():
                    if not _continues(awaited, retained):
                        return save("OCCUPIED_MARK_CHECKPOINT_UNPROVEN")
                    try:
                        consumed = _reversal_cycle_count(
                            prior_evidence, request, retained, state["attempt_limit"]
                        )
                    except (KeyError, OSError, TypeError, ValueError):
                        return save("OCCUPIED_MARK_CHECKPOINT_UNPROVEN")
                    if state["cycles_used"] + consumed > bounds.max_total_cycles:
                        return save("OCCUPIED_MARK_CHECKPOINT_UNPROVEN")
                    state["cycles_used"] += consumed
                    state["awaiting"] = retained
                    save("AWAITING_BOOKING")
                    continue
                if state["interrupted_retries"] >= DEFAULT_BOUNDED_RETRY_LIMIT:
                    return save("RETRY_EXHAUSTED")
                state["interrupted_retries"] += 1
            if awaited is not None and retained != awaited:
                return save("OCCUPIED_REVERSAL_CHECKPOINT_CHANGED")
            state["awaiting"] = retained
            original_cancel = request.get("cancel_requested")

            def cancel():
                return (
                    (root / "STOP").exists()
                    or blocked()
                    or remaining() <= 0
                    or settlement_only
                    or (original_cancel is not None and original_cancel())
                )

            seconds = remaining()
            if seconds <= 0:
                return save("BOUNDS_EXHAUSTED")
            authorization = request["authorization"]
            request["authorization"] = replace(
                authorization,
                max_cycles_per_run=min(
                    authorization.max_cycles_per_run,
                    max(1, bounds.max_total_cycles - state["cycles_used"]),
                ),
                max_run_duration_seconds=min(authorization.max_run_duration_seconds, seconds),
            )
            request["cancel_requested"] = cancel
            state["attempt"] = attempt
            state["attempt_limit"] = request["authorization"].max_cycles_per_run
            save("RUNNING")
            with prepared.open_ports(request["authorization"]) as opened:
                if request.keys() & opened.keys() or not opened.keys() <= _PORTS:
                    raise ValueError("N1_V2_PORT_OVERRIDES_REQUEST")
                request.update(opened)
                for key, adapter in (
                    ("observation_source", _FilegateObservationSource),
                    ("f1_m9_cycle_evaluator", _filegate_cycle_evaluator),
                ):
                    if request.get(key) is not None:
                        request[key] = adapter(
                            request[key], path=filegate, revision=state["filegate_revision"]
                        )
                result = run_n1_standing_pre_external_supervisor_v1(**request)

            trace = result.trace
            state["last_disposition"] = trace.terminal_disposition
            if retained is not None:
                readback = trace.extra.get("net_reversal_readback", {})
                if any(
                    readback.get(key) != retained[key]
                    for key in ("episode_id", "envelope_digest", "reservation_id")
                ):
                    return save("OCCUPIED_REVERSAL_READBACK_UNPROVEN")
                if not readback.get("booking_digest"):
                    state["reconciliation_blocker"] = readback.get("reconciliation_blocker")
                    return save("AWAITING_BOOKING")
                state["last_booking"] = readback
                state.pop("reconciliation_blocker", None)
            state["awaiting"] = None
            if settlement_only:
                if trace.governed_cycle_count or trace.post_count:
                    raise ValueError("N1_V2_SETTLEMENT_ONLY_MARK_EFFECT")
                return save("BOUNDS_EXHAUSTED")
            if trace.terminal_disposition != _REVERSAL_TERMINAL or trace.post_count != 1:
                state["cycles_used"] += trace.governed_cycle_count
                if (root / "STOP").exists():
                    return save("STOPPED")
                if blocked():
                    return save("FILEGATE_BLOCKED")
                return save("COMPLETED" if result.ok else "GOVERNED_RUNTIME_STOPPED")
            submitted = _submitted_reversal(request)
            if not _continues(retained, submitted) or any(
                trace.extra["net_reversal_post"].get(key) != submitted[key]
                for key in ("envelope_digest", "reservation_id")
            ):
                return save("OCCUPIED_REVERSAL_SUBMIT_UNPROVEN")
            state["cycles_used"] += _reversal_cycle_count(
                evidence, request, submitted, state["attempt_limit"]
            )
            state["awaiting"] = submitted
            save("AWAITING_BOOKING")
