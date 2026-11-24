"""Read the PIEVERSE Shadow owners at quiescence and adjudicate their sealed originals."""

import json
import os
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from math import isfinite
from pathlib import Path

from src.ops.hard_facts_system_closure_v1.position_aware_rotation_v1 import (
    RotationPhase,
    evaluate_position_aware_rotation_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.classifier_v1 import (
    classify_productive_reconciliation_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    AUTHORITY_OWNER,
    SINGLE_WRITER_IDENTITY,
    EVIDENCE_FILENAME,
    MANIFEST_FILENAME,
    PORTFOLIO_STATE_FILENAME,
    WRITER_LOCK_FILENAME,
)
from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import (
    detect_duplicate_portfolio_state,
    snapshot_from_payload,
)
from src.ops.productive_reconciliation_runtime_binding_v1.startup_portfolio_document_v1 import (
    STARTUP_PORTFOLIO_MAX_AGE_SECONDS,
)
from src.ops.ranked_shadow_entry_selection_v1 import ranked_shadow_positions_from_snapshot_v1
from src.trading.master_v2.double_play_entry_exit_policy_v0 import PositionState
from src.trading.master_v2.double_play_state import SideState

RECEIPT = "slot4_shadow_closeout_v1.json"
ABORT_OBSERVATION = "PIEVERSE_SHADOW_ABORT_OBSERVATION_V1"


def read_slot4_session_origin_v1(original_bytes, session_id):
    consumption = json.loads(original_bytes("authorization_consumption.json"))
    execution = json.loads(original_bytes("authorization_consumption_record.json"))
    revision = original_bytes("repo_sha.txt").decode().strip()
    if (
        consumption.get("session_id") != session_id
        or consumption.get("mode") != "productive_wallclock_v2"
        or consumption.get("consumed") is not True
        or consumption.get("productive_authorization") is not True
        or consumption.get("forced_wiring_fixture") is not False
        or not consumption.get("authorization_id")
        or execution["authorization_id"] != consumption["authorization_id"]
        or execution["session_id"] != session_id
        or execution["expected_repository_sha"] != revision
    ):
        raise ValueError("SHADOW_SLOT4_SESSION_ORIGIN_UNPROVEN")
    return revision


def retain_slot4_observation_v1(state, slot, observed, source):
    """Keep the input seen by the actual gate alongside its economic original."""
    state.slot4_reconciliation_observations[source] = {
        "n5_assignment": slot.reference(),
        "observed": observed.to_dict(),
        "economic": state.portfolio.snapshot(),
    }


def _read_reconciliation(root):
    manifest = root / MANIFEST_FILENAME
    seal = manifest.read_bytes()
    names = (EVIDENCE_FILENAME, PORTFOLIO_STATE_FILENAME)
    files = {name: (root / name).read_bytes() for name in names}
    expected = [f"{sha256(files[n]).hexdigest()}  {n}" for n in sorted(files)]
    if (
        seal.decode().splitlines() != expected
        or seal != manifest.read_bytes()
        or root.is_symlink()
        or manifest.is_symlink()
        or any((root / n).is_symlink() for n in names)
        or detect_duplicate_portfolio_state(root)
        or (root / WRITER_LOCK_FILENAME).exists()
    ):
        raise ValueError("SHADOW_SLOT4_RECONCILIATION_READBACK_INVALID")
    return {
        "evidence": json.loads(files[EVIDENCE_FILENAME]),
        "portfolio": json.loads(files[PORTFOLIO_STATE_FILENAME]),
        "manifest_sha256": sha256(seal).hexdigest(),
    }


def _reconciliation_roots(evidence_root, session_id):
    if not session_id or session_id in (".", "..") or Path(session_id).name != session_id:
        raise ValueError("SHADOW_SLOT4_CLOSEOUT_SCOPE_MISMATCH")
    return {
        "entry": evidence_root.parent / "entry-reconciliation" / session_id,
        "reconnect": evidence_root / "post_reconnect_reconciliation",
    }


def read_slot4_reconciliation_sources_v1(evidence_root, session_id):
    return {
        key: _read_reconciliation(path)
        for key, path in _reconciliation_roots(evidence_root, session_id).items()
        if path.exists() or path.is_symlink()
    }


def inspect_slot4_reconciliation_readbacks_v1(evidence_root, session_id):
    """Inventory both owner stores independently. File integrity alone confers no clearance."""
    result = {}
    for key, path in _reconciliation_roots(evidence_root, session_id).items():
        record = {"path": str(path)}
        try:
            path.lstat()
        except FileNotFoundError:
            record["status"] = "ABSENT"
        except OSError:
            record["status"] = "UNREADABLE"
        else:
            try:
                readback = _read_reconciliation(path)
            except (OSError, ValueError):
                record["status"] = "INVALID_OR_INCOMPLETE"
            else:
                record.update(
                    status="SEALED_FILES_ONLY", manifest_sha256=readback["manifest_sha256"]
                )
        result[key] = record
    return result


def capture_slot4_shadow_closeout_v1(runtime, slot, session_id):
    """Called after the last cycle and economic replay, before sealing the session evidence."""
    state = runtime.bridge_state
    if (
        state.session_id != session_id
        or state.instrument_id != slot.instrument.canonical_instrument_id
    ):
        raise ValueError("SHADOW_SLOT4_CLOSEOUT_SCOPE_MISMATCH")
    if not state.cycle_ledger:
        return {
            "session_id": session_id,
            "n5_assignment": slot.reference(),
            "unavailable": "SHADOW_SLOT4_NO_CONFIRMED_CYCLE",
        }
    cycle = state.cycle_ledger[-1]
    return dict(
        session_id=session_id,
        n5_assignment=slot.reference(),
        last_cycle_id=cycle["cycle_id"],
        captured_at_unix=runtime.clock_wall(),
        reconciliation=read_slot4_reconciliation_sources_v1(runtime.evidence_root, session_id),
        original_observations=dict(state.slot4_reconciliation_observations),
        confirmed_entry_budget=state.ranked_confirmed_entry_budget,
        bridge_position_state=state.position_state.value,
        bridge_venue_flat=state.venue_flat,
        side_state=state.side_state.value,
        bridge_killstate_active=state.killstate_active,
        reconnect_reconciliation_pending=runtime._post_reconnect_reconciliation_required,
        quality_fail=runtime.quality_fail,
    )


def capture_slot4_shadow_abort_v1(runtime, slot, session_id):
    """Read the quiescent predecessor itself before the wallclock owner releases its lock."""
    state, lock = runtime.bridge_state, runtime.lock
    if (
        (slot.lane_id, state.venue_instrument_id) != ("LANE_4", "PIEVERSE-USDT-SWAP")
        or state.instrument_id != slot.instrument.canonical_instrument_id
        or state.venue_instrument_id != slot.instrument.venue_native_inst_id
        or state.session_id != session_id
        or runtime.session_id != session_id
        or not runtime.consumed
        or runtime.killstate.active is not True
        or lock is None
        or lock.session_id != session_id
        or lock.lock_path != runtime.evidence_root / "session.lock"
    ):
        raise ValueError("SHADOW_SLOT4_ABORT_OWNER_SCOPE_UNPROVEN")

    def check_lock():
        lock.assert_held()
        if not os.path.samestat(os.fstat(lock.fd), lock.lock_path.lstat()):
            raise ValueError("SHADOW_SLOT4_ABORT_OWNER_LOCK_CHANGED")

    check_lock()
    event = runtime.clock_wall()
    economic = state.portfolio.snapshot()
    # Take the actual budget binding and both inventories even when zero cycles finished.
    receipt = dict(
        kind=ABORT_OBSERVATION,
        session_id=session_id,
        n5_assignment=slot.reference(),
        observed_at_unix=event,
        economic=economic,
        bridge_cycle_index=state.cycle_index,
        cycle_ids=[row["cycle_id"] for row in state.cycle_ledger],
        fill_ids=[row["fill_id"] for row in state.fill_ledger],
        confirmed_entry_budget=deepcopy(state.ranked_confirmed_entry_budget),
        bridge_position_state=state.position_state.value,
        bridge_venue_flat=state.venue_flat,
        side_state=state.side_state.value,
        bridge_killstate_active=state.killstate_active,
        reconnect_reconciliation_pending=runtime._post_reconnect_reconciliation_required,
        session_state=runtime.state.value,
        killstate=runtime.killstate.to_dict(),
        original_observations=deepcopy(state.slot4_reconciliation_observations),
    )
    try:
        receipt["reconciliation"] = read_slot4_reconciliation_sources_v1(
            runtime.evidence_root, session_id
        )
    except (OSError, ValueError) as exc:
        receipt["reconciliation_error"] = str(exc)
    receipt["captured_at_unix"] = runtime.clock_wall()
    check_lock()
    return receipt


def review_slot4_shadow_abort_v1(
    *,
    receipt,
    slot,
    session,
    shutdown,
    counters,
    cycles,
    fills,
    orders,
    evidence_root,
    repository_sha,
    entry_repository_sha,
    clock,
):
    """Review an original sealed ABORT observation; an active killstate vetoes replacement."""
    event, end = receipt["observed_at_unix"], receipt["captured_at_unix"]
    kill = shutdown["killstate"]
    if (
        receipt["kind"] != ABORT_OBSERVATION
        or (receipt["session_id"], receipt["n5_assignment"]) != (session, slot.reference())
        or receipt["session_state"] != shutdown["state"]
        or shutdown["state"] not in {"ABORTED", "KILLSTATE", "INVALID"}
        or receipt["killstate"] != kill
        or kill["active"] is not True
        or not kill["events"]
        or not all(type(t) in (float, int) and isfinite(t) for t in (event, end))
        or not 0 < max(row["wall_ts"] for row in kill["events"]) <= event <= end
    ):
        raise ValueError("SHADOW_SLOT4_ABORT_OBSERVATION_MISMATCH")
    economic = receipt["economic"]
    portfolio = ranked_shadow_positions_from_snapshot_v1(
        economic, slot, session_id=session, now=event
    )
    state = PositionState(receipt["bridge_position_state"])
    side = SideState(receipt["side_state"])
    flat = all(p.signed_quantity == 0 for p in portfolio.positions)
    inputs = dict(
        venue_flat=flat if not flat or receipt["bridge_venue_flat"] is True else None,
        reconciled=None,
        pending_external_custody=None,
        pending_pre_external_custody=None,
        lane_health_allows_replacement=False,
    )
    issues = []
    if receipt["bridge_venue_flat"] is not flat:
        issues.append("SHADOW_SLOT4_ABORT_BRIDGE_POSITION_MISMATCH")
    try:
        if (
            cycles is None
            or fills is None
            or receipt["bridge_cycle_index"] != len(cycles)
            or counters["cycle_count"] != len(cycles)
            or economic["state"]["intended_action_count"] != len(cycles)
            or economic["state"]["fill_count"] != len(fills)
            or receipt["cycle_ids"] != [row["cycle_id"] for row in cycles]
            or receipt["fill_ids"] != [row["fill_id"] for row in fills]
            or (cycles and cycles[-1]["portfolio_snapshot"] != economic)
        ):
            raise ValueError("SHADOW_SLOT4_ABORT_CUSTODY_LEDGER_INCOMPLETE")
        budget_binding = receipt["confirmed_entry_budget"]
        if budget_binding is not None and (
            budget_binding["session_id"] != session
            or budget_binding["n5_assignment"] != slot.reference()
        ):
            raise ValueError("SHADOW_SLOT4_ABORT_BUDGET_SCOPE_MISMATCH")
        pending, budget = _pending_custody(
            receipt, economic, cycles, fills, orders, session, slot.reference()
        )
        inputs["pending_pre_external_custody"] = budget
        if pending or state in {
            PositionState.SUBMISSION_UNKNOWN,
            PositionState.EXIT_PENDING,
            PositionState.REDUCING_PARTIAL,
        }:
            inputs["pending_external_custody"] = True
        elif (
            state is not PositionState.RECONCILIATION_REQUIRED
            and receipt["reconnect_reconciliation_pending"] is False
        ):
            inputs["pending_external_custody"] = False
    except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
        issues.append(str(exc))
    recon_event = None
    try:
        if not receipt.get("reconciliation") or receipt[
            "reconciliation"
        ] != read_slot4_reconciliation_sources_v1(evidence_root, session):
            raise ValueError("SHADOW_SLOT4_ABORT_RECONCILIATION_SOURCE_UNPROVEN")
        latest = max(
            item["evidence"]["wall_time_unix"] for item in receipt["reconciliation"].values()
        )
        recon_event = min(
            item["evidence"]["event_time_unix"]
            for item in receipt["reconciliation"].values()
            if item["evidence"]["wall_time_unix"] == latest
        )
        if (
            not 0 < recon_event <= latest <= event
            or event - recon_event > STARTUP_PORTFOLIO_MAX_AGE_SECONDS
        ):
            raise ValueError("SHADOW_SLOT4_ABORT_RECONCILIATION_SOURCE_STALE")
        if inputs["venue_flat"] is True:
            inputs["reconciled"] = (
                _reconciled(
                    receipt, portfolio, slot, session, repository_sha, entry_repository_sha, event
                )
                and state is PositionState.FLAT_RECONCILED
                and receipt["reconnect_reconciliation_pending"] is False
            )
    except (ValueError, KeyError, TypeError, ArithmeticError, OSError) as exc:
        issues.append(str(exc))
    now = clock()
    if type(now) not in (int, float) or not isfinite(now) or now < end:
        raise ValueError("SHADOW_SLOT4_ABORT_OBSERVATION_CLOCK_INVALID")
    fresh = now - event <= STARTUP_PORTFOLIO_MAX_AGE_SECONDS
    current = inputs.copy() if fresh else dict.fromkeys(inputs)
    if current["reconciled"] is True and now - recon_event > STARTUP_PORTFOLIO_MAX_AGE_SECONDS:
        current["reconciled"] = None
        issues.append("SHADOW_SLOT4_ABORT_RECONCILIATION_SOURCE_STALE")
    decision = None
    if all(type(value) is bool for value in current.values()):
        decision = evaluate_position_aware_rotation_v1(
            phase=RotationPhase.COMMIT, **current
        ).reason_code
    return dict(
        observed_at_unix=event,
        captured_at_unix=end,
        reviewed_at_unix=now,
        fresh=fresh,
        source_id=portfolio.source_id,
        positions_native_contracts=[p.to_dict() for p in portfolio.positions],
        side_state=side.value,
        bridge_position_state=state.value,
        confirmed_entry_budget=receipt["confirmed_entry_budget"],
        inputs_at_observation=inputs,
        current_inputs=current,
        rotation_owner_reason=decision,
        issues=issues,
    )


def _reconciled(receipt, portfolio, slot, session, repository_sha, entry_repository_sha, now):
    captured = receipt["captured_at_unix"]
    sources = receipt["reconciliation"]
    if not sources or not set(sources) <= {"entry", "reconnect"}:
        raise ValueError("SHADOW_SLOT4_RECONCILIATION_READBACK_REQUIRED")
    for key, source in sources.items():
        e = source["evidence"]
        saved = snapshot_from_payload(source["portfolio"])
        original = receipt["original_observations"].get(key)
        if not original or original["n5_assignment"] != slot.reference():
            raise ValueError("SHADOW_SLOT4_RECONCILIATION_OBSERVATION_REQUIRED")
        observed = ranked_shadow_positions_from_snapshot_v1(
            original["economic"], slot, session_id=session, now=e["event_time_unix"]
        )
        if (
            observed.to_dict() != original["observed"]
            or observed.digest() != e["observed_state_digest"]
            or saved.to_dict() != source["portfolio"]
            or e["post_state_digest"] != saved.digest()
            or e["owner"] != AUTHORITY_OWNER
            or e["single_writer_identity"] != SINGLE_WRITER_IDENTITY
            or not 0 < e["event_time_unix"] <= e["wall_time_unix"] <= captured
        ):
            raise ValueError("SHADOW_SLOT4_RECONCILIATION_READBACK_INVALID")
    for key, revision in (("reconnect", repository_sha), ("entry", entry_repository_sha)):
        if key in sources and sources[key]["evidence"]["repository_sha"] != revision:
            raise ValueError("SHADOW_SLOT4_RECONCILIATION_READBACK_INVALID")
    latest = max(s["evidence"]["wall_time_unix"] for s in sources.values())
    reconciled = True
    for source in sources.values():
        e = source["evidence"]
        if e["wall_time_unix"] == latest:
            saved = snapshot_from_payload(source["portfolio"])
            classification, _, _ = classify_productive_reconciliation_v1(
                persisted=saved, observed=portfolio, now_unix=now
            )
            reconciled &= (
                e["hard_stop"] is False
                and e["alpha_enabled"] is True
                and (
                    e["classification"] == "MATCH"
                    or (
                        e["classification"] == "RECOVERABLE_DRIFT"
                        and e["recovery_verified"] is True
                    )
                )
                and classification.value == "MATCH"
                and all(p.signed_quantity == 0 and p.side == "FLAT" for p in saved.positions)
            )
    return reconciled


def _pending_custody(receipt, economic, cycles, fills, orders, session, assignment):
    # A bound first purchase survives booking as lineage. Clear it only when its
    # exact original entry occurs in a booked cycle of this portfolio.
    entries = []
    intent_ids = []
    booked = []
    pending_virtual = False
    for index, cycle in enumerate(cycles, start=1):
        action = cycle["intended_action"]
        intent = cycle["intent_id"]
        if (
            cycle["session_id"] != session
            or cycle["instrument_id"] != assignment["canonical_instrument_id"]
            or cycle["cycle_index"] != index
            or not intent
            or action["intent_id"] != intent
        ):
            raise ValueError("SHADOW_SLOT4_CUSTODY_SCOPE_MISMATCH")
        intent_ids.append(intent)
        side = action["intended_side"]
        quantity = Decimal(str(action["intended_quantity"]))
        fill = cycle["fill"]
        if side in ("BUY", "SELL") and quantity.is_finite() and quantity > 0:
            if not fill or not cycle["fill_id"]:
                pending_virtual = True
                continue
            if (
                fill["fill_id"] != cycle["fill_id"]
                or fill["intent_id"] != intent
                or fill["session_id"] != session
                or fill["cycle_id"] != cycle["cycle_id"]
                or fill["instrument_id"] != cycle["instrument_id"]
                or fill["side"] != side
                or Decimal(str(fill["quantity"])) != quantity
            ):
                raise ValueError("SHADOW_SLOT4_BOOKING_MISMATCH")
            booked.append(fill)
        elif side != "HOLD" or quantity != 0 or fill is not None or cycle["fill_id"] is not None:
            raise ValueError("SHADOW_SLOT4_INTENT_UNRESOLVED")
        purchase = cycle.get("ranked_shadow_first_purchase")
        if purchase and purchase["status"] == "FILLED":
            from src.ops.ranked_shadow_first_purchase_v1 import verify_ranked_first_purchase_v1

            if (
                not verify_ranked_first_purchase_v1(cycle)
                or purchase["entry"]["n5_assignment"] != assignment
            ):
                raise ValueError("SHADOW_SLOT4_ENTRY_BOOKING_MISMATCH")
            entries.append(purchase["entry"])
        elif purchase and purchase["status"] != "BLOCKED":
            raise ValueError("SHADOW_SLOT4_ENTRY_UNRESOLVED")
    if (
        len(set(intent_ids)) != len(intent_ids)
        or sorted(intent_ids) != economic["applied_intent_ids"]
        or booked != fills
        or sorted(f["fill_id"] for f in booked) != economic["applied_fill_ids"]
    ):
        raise ValueError("SHADOW_SLOT4_CUSTODY_LEDGER_MISMATCH")
    budget = receipt["confirmed_entry_budget"]
    pending_budget = entries != ([] if budget is None else [budget])
    if (
        orders["ok"] is not True
        or orders["orders_allowed"] is not False
        or any(
            type(orders[key]) is not int or orders[key] != 0
            for key in ("orders_submitted", "broker_writes_performed")
        )
        or economic["orders_submitted"] is not False
        or economic["broker_writes"] is not False
    ):
        raise ValueError("SHADOW_SLOT4_EXTERNAL_BOUNDARY_UNPROVEN")
    return pending_virtual, pending_budget


def adjudicate_slot4_closeout_v1(
    *,
    receipt,
    portfolio,
    economic,
    cycles,
    fills,
    orders,
    shutdown,
    terminal,
    counters,
    completion,
    session,
    slot,
    repository_sha,
    entry_repository_sha,
    now,
):
    """Only the original single-session internal simulator is in this custody domain."""
    assignment = slot.reference()
    event = portfolio.event_time_unix
    captured = receipt["captured_at_unix"]
    if not all(type(t) in (int, float) and isfinite(t) for t in (event, captured, now)) or not (
        event <= captured <= now and now - event <= STARTUP_PORTFOLIO_MAX_AGE_SECONDS
    ):
        raise ValueError("SHADOW_SLOT4_OWNER_EVIDENCE_STALE")
    if (
        session != receipt["session_id"]
        or receipt["n5_assignment"] != assignment
        or (assignment["lane_id"], assignment["venue_native_id"])
        != ("LANE_4", "PIEVERSE-USDT-SWAP")
        or not cycles
        or receipt["last_cycle_id"] != cycles[-1]["cycle_id"]
        or counters["cycle_count"] != len(cycles)
        or counters["accepted_ticks"] < len(cycles)
        or completion["full_economic_reconstruction_pass"] is not True
        or terminal["paper_execution"] is not False
        or terminal["credentials_used"] is not False
    ):
        raise ValueError("SHADOW_SLOT4_CLOSEOUT_SCOPE_MISMATCH")
    reconciled = _reconciled(
        receipt, portfolio, slot, session, repository_sha, entry_repository_sha, now
    )
    pending_virtual, pending_budget = _pending_custody(
        receipt, economic, cycles, fills, orders, session, assignment
    )
    position_state = PositionState(receipt["bridge_position_state"])
    unresolved_booking = position_state in {
        PositionState.SUBMISSION_UNKNOWN,
        PositionState.EXIT_PENDING,
        PositionState.REDUCING_PARTIAL,
    }
    side_state = SideState(receipt["side_state"])
    pending_switch = side_state in {
        SideState.SWITCH_LONG_TO_SHORT_PENDING,
        SideState.SWITCH_SHORT_TO_LONG_PENDING,
    }
    kill = shutdown["killstate"]
    healthy_end = (
        shutdown["state"] in {"COMPLETED", "TIMED_OUT"}
        and shutdown["blockers"] == []
        and kill["active"] is False
        and kill["events"] == []
        and kill["last_trigger"] == ""
        and terminal["verdict"] == "PASS"
        and terminal["incomplete"] is False
        and receipt["bridge_killstate_active"] is False
        and side_state != SideState.KILL_ALL
        and not pending_switch
        and receipt["reconnect_reconciliation_pending"] is False
        and receipt["quality_fail"] is False
    )
    return evaluate_position_aware_rotation_v1(
        phase=RotationPhase.COMMIT,
        venue_flat=all(p.signed_quantity == 0 and p.side == "FLAT" for p in portfolio.positions),
        reconciled=reconciled
        and position_state is not PositionState.RECONCILIATION_REQUIRED
        and (
            unresolved_booking
            or (
                position_state is PositionState.FLAT_RECONCILED
                and receipt["bridge_venue_flat"] is True
            )
        ),
        pending_external_custody=pending_virtual or unresolved_booking,
        pending_pre_external_custody=pending_budget,
        lane_health_allows_replacement=healthy_end,
    )
