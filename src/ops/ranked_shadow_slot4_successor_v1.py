"""One checked successor generation for the fixed Shadow slot 4, with the original N5 intact."""

import json
import re
import time
from dataclasses import asdict, replace
from hashlib import sha256
from datetime import datetime
from pathlib import Path

from src.ops.current_mf_member_to_pinned_cap23_n1_adapter_v1.adapter_v1 import (
    build_governed_cap23_pin_v1,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1 import persistence_v1 as store
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    LANE_IDS,
    SHADOW_SLOT4_SUCCESSOR_POLICY,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    _empty_slot,
    _finish_topology,
    _occupied_slot,
)
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1.checked_publication_v1 import (
    _require_replacement_clearance_v1,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    build_bootstrap_membership_from_cap22_snapshot_v1,
    read_membership_context_artifact_v1,
    write_membership_context_artifact_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    require_i17_shadow_instrument_v1,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import SNAPSHOT_FILENAME
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.startup_portfolio_document_v1 import (
    STARTUP_PORTFOLIO_MAX_AGE_SECONDS,
)
from src.ops.ranked_shadow_slot4_rotation_v1 import read_slot4_session_origin_v1
from src.ops.ranked_shadow_slot4_nomination_v1 import require_slot4_nomination_v1
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from src.ops.single_selected_future_policy_v1.persistence_v1 import validate_selection_bindings_v1
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    build_selection_evidence_v1,
    resume_lane_selection_publication_v1,
)
from src.ops.single_selected_future_policy_v1.selection_v1 import produce_single_selected_future_v1
from src.ops.single_selected_future_policy_v1.single_writer_v1 import (
    SingleSelectedFutureSingleWriterV1,
)

LANE = "LANE_4"
ROTATION_INPUTS = (
    "venue_flat",
    "reconciled",
    "pending_pre_external_custody",
    "pending_external_custody",
    "lane_health_allows_replacement",
)
TARGET = require_i17_shadow_instrument_v1(("CSOPSKHYNIX2L-USDT-SWAP",))


def successor_root_v1(original_root):
    return Path(original_root).resolve() / "shadow_slot4_successor_v1"


def _epoch(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def _original(path):
    from src.ops.ranked_slot_run_source_v1 import _read_ranked_run_slot_v1

    config = json.loads(path.read_bytes())
    if (config["surface"], config["lane"], config["native_instrument_id"]) != (
        "SHADOW",
        LANE,
        "PIEVERSE-USDT-SWAP",
    ):
        raise ValueError("SHADOW_SLOT4_FIXED_PREDECESSOR_REQUIRED")
    return config, _read_ranked_run_slot_v1(config, fixed_original_only=True)


def _check_clearance(old, predecessor, portfolio, admission, now):
    _require_replacement_clearance_v1(
        {LANE: old.selection.instrument_id}, portfolio, {LANE: admission}, now
    )
    prefix = f"SHADOW:{predecessor['session_id']}:{LANE}:"
    if (
        not portfolio.source_id.startswith(prefix)
        or not re.fullmatch("[0-9a-f]{64}", portfolio.source_id[len(prefix) :])
        or portfolio.wall_time_unix is None
        or now - portfolio.event_time_unix > STARTUP_PORTFOLIO_MAX_AGE_SECONDS
        or not portfolio.event_time_unix <= portfolio.wall_time_unix <= now
        or any(
            p.instrument_id != old.selection.instrument_id
            or p.source_id != portfolio.source_id
            or p.event_time_unix != portfolio.event_time_unix
            or p.wall_time_unix != portfolio.wall_time_unix
            for p in portfolio.positions
        )
        or len(portfolio.positions) > 1
    ):
        raise ValueError("SHADOW_SLOT4_POSITION_SOURCE_MISMATCH")


def read_slot4_shadow_positions_v1(predecessor_profile, evidence_root):
    """Recover the final virtual position at its original observation time."""
    return _read_slot4_evidence(predecessor_profile, evidence_root, rotation_at=None)


def prepare_slot4_shadow_rotation_v1(predecessor_profile, evidence_root, *, clock=time.time):
    """Read only. Return the portfolio, native owner decision and sealed source digest."""
    from src.ops.ranked_shadow_slot4_pre_tick_v1 import (
        CHECKPOINT,
        read_slot4_pre_tick_checkpoint_v1,
    )
    from src.ops.ranked_slot_run_source_v1 import read_ranked_run_slot_v1

    root = Path(evidence_root)
    manifest = root / "evidence_manifest.sha256"
    checkpoint = root / CHECKPOINT
    if checkpoint.exists() or checkpoint.is_symlink():
        config = json.loads(Path(predecessor_profile).read_bytes())
        if (config["surface"], config["lane"]) != ("SHADOW", LANE):
            raise ValueError("SHADOW_SLOT4_CHECKPOINT_SCOPE_MISMATCH")
        unsealed = not manifest.exists() and not manifest.is_symlink()
        if unsealed or config["native_instrument_id"] != "PIEVERSE-USDT-SWAP":
            expected_sha = None
            if not unsealed:
                sealed, _, pins = _verified_archive(root)
                expected_sha = pins[CHECKPOINT]
            if config["native_instrument_id"] == "PIEVERSE-USDT-SWAP":
                config, slot = _original(Path(predecessor_profile))
            else:
                slot = read_ranked_run_slot_v1(config)
            observation = read_slot4_pre_tick_checkpoint_v1(
                root, slot, config["session_id"], expected_sha=expected_sha
            )
            if (unsealed and (manifest.exists() or manifest.is_symlink())) or (
                not unsealed and manifest.read_bytes() != sealed
            ):
                raise ValueError("SHADOW_SLOT4_OWNER_EVIDENCE_CHANGED")
            raise Slot4ShadowRecoveryRequired(
                dict(
                    session_id=config["session_id"],
                    assignment=slot.reference(),
                    pre_tick_checkpoint=observation,
                    unproven_rotation_inputs=list(ROTATION_INPUTS),
                )
            )
    return _read_slot4_evidence(predecessor_profile, evidence_root, rotation_at=clock)


class Slot4ShadowRecoveryRequired(ValueError):
    """Owner evidence is available, but the rotation cannot commit."""

    def __init__(self, evidence):
        review = evidence.get("abort_owner_observation") or {}
        reason = review.get("rotation_owner_reason")
        super().__init__(
            "SHADOW_SLOT4_ROTATION_VETO:" + reason
            if reason
            else "SHADOW_SLOT4_RECOVERY_OWNER_INPUTS_REQUIRED"
        )
        self.evidence = evidence


def _abort_evidence(root, session, original_bytes, pins, sealed, *, old, predecessor, clock):
    from src.ops.ranked_shadow_slot4_pre_tick_v1 import (
        CHECKPOINT,
        read_slot4_pre_tick_checkpoint_v1,
    )
    from src.ops.ranked_shadow_slot4_rotation_v1 import (
        ABORT_OBSERVATION,
        RECEIPT,
        inspect_slot4_reconciliation_readbacks_v1,
        review_slot4_shadow_abort_v1,
    )

    def document(name):
        return json.loads(original_bytes(name)) if name in pins else {}

    session_id = session["session_id"]
    terminal = json.loads(original_bytes("terminal_verdict.json"))
    if (
        terminal["verdict"] != "ABORT"
        or terminal.get("paper_execution") is not False
        or terminal.get("credentials_used") is not False
    ):
        raise ValueError("SHADOW_SLOT4_SESSION_ORIGIN_UNPROVEN")
    snapshot = document("portfolio_snapshot.json")
    shutdown = document("shutdown_reason.json")
    orders = document("no_order_attestation.json")
    counters = document("observation_cycle_counters.json")
    evidence = {
        "session_id": session_id,
        "assignment": session["n5_assignment"],
        "repository_sha": read_slot4_session_origin_v1(original_bytes, session_id),
        "evidence_manifest_sha256": sha256(sealed).hexdigest(),
        "historical_session": {
            "verdict": terminal["verdict"],
            "shutdown": shutdown,
            "accepted_ticks": counters.get("accepted_ticks"),
            "cycle_count": counters.get("cycle_count"),
            "portfolio_stub": snapshot.get("stub"),
            "portfolio_blocker": snapshot.get("blocker"),
            "no_order_attestation": orders or None,
            "closeout_in_manifest": RECEIPT in pins,
            "archived_rows": {
                name: len(original_bytes(name).splitlines()) if name in pins else None
                for name in (
                    "portfolio_snapshots.jsonl",
                    "order_intent_trace.jsonl",
                    "bridge_cycle_ledger.jsonl",
                    "bridge_fill_ledger.jsonl",
                )
            },
        },
        "reconciliation_readbacks": inspect_slot4_reconciliation_readbacks_v1(root, session_id),
        # These are the current inputs of the native COMMIT owner. An aborted
        # session cannot supply them from initial defaults or historical counters.
        "unproven_rotation_inputs": list(ROTATION_INPUTS),
    }
    if CHECKPOINT in pins:
        evidence["pre_tick_checkpoint"] = read_slot4_pre_tick_checkpoint_v1(
            root, old, session_id, expected_sha=pins[CHECKPOINT]
        )
    receipt = document(RECEIPT)
    evidence["abort_owner_observation"] = None
    if receipt.get("kind") == ABORT_OBSERVATION:

        def rows(name):
            return (
                [json.loads(line) for line in original_bytes(name).splitlines()]
                if name in pins
                else None
            )

        review = review_slot4_shadow_abort_v1(
            receipt=receipt,
            slot=old,
            session=session_id,
            shutdown=shutdown,
            counters=counters,
            cycles=rows("bridge_cycle_ledger.jsonl"),
            fills=rows("bridge_fill_ledger.jsonl"),
            orders=orders,
            evidence_root=root,
            repository_sha=evidence["repository_sha"],
            entry_repository_sha=(
                predecessor.get("shadow_entry_admission") or predecessor["n5_source"]
            )["repository_sha"],
            clock=clock,
        )
        evidence["abort_owner_observation"] = review
        evidence["unproven_rotation_inputs"] = [
            k for k, value in review["current_inputs"].items() if value is None
        ]
    elif receipt.get("unavailable") and receipt.get("session_id") == session_id:
        evidence["abort_owner_observation_unavailable"] = receipt["unavailable"]
    if sealed != (root / "evidence_manifest.sha256").read_bytes():
        raise ValueError("SHADOW_SLOT4_OWNER_EVIDENCE_CHANGED")
    return evidence


def _verified_archive(root):
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (
        verify_wallclock_evidence_bundle_v1,
    )

    manifest = root / "evidence_manifest.sha256"
    sealed = manifest.read_bytes()
    verified = verify_wallclock_evidence_bundle_v1(evidence_root=root)
    if not verified.verified or manifest.read_bytes() != sealed:
        raise ValueError("SHADOW_SLOT4_ARCHIVE_VERIFICATION_FAILED")
    pins = {
        name: digest
        for digest, name in (line.split("  ", 1) for line in sealed.decode().splitlines() if line)
    }
    return sealed, verified, pins


def _read_slot4_evidence(predecessor_profile, evidence_root, *, rotation_at, historical=False):
    from src.ops.ranked_shadow_entry_selection_v1 import ranked_shadow_positions_from_snapshot_v1
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.provenance_v2 import (
        portfolio_state_hash,
    )

    root = Path(evidence_root)
    predecessor, old = _original(Path(predecessor_profile))
    manifest = root / "evidence_manifest.sha256"
    if not manifest.is_file() or manifest.is_symlink():
        raise ValueError("SHADOW_SLOT4_COMPLETED_PORTFOLIO_REQUIRED")
    sealed, verified, pins = _verified_archive(root)

    def original_bytes(name):
        path = root / name
        raw = path.read_bytes()
        if path.is_symlink() or sha256(raw).hexdigest() != pins.get(name):
            raise ValueError("SHADOW_SLOT4_SEALED_POSITION_REQUIRED")
        return raw

    session = json.loads(original_bytes("session_manifest.json"))
    if (
        session.get("n5_assignment") != old.reference()
        or session["session_id"] != predecessor["session_id"]
    ):
        raise ValueError("SHADOW_SLOT4_POSITION_ORIGINAL_MISMATCH")
    if verified.verdict == "ABORT" and rotation_at is not None:
        raise Slot4ShadowRecoveryRequired(
            _abort_evidence(
                root,
                session,
                original_bytes,
                pins,
                sealed,
                old=old,
                predecessor=predecessor,
                clock=rotation_at,
            )
        )
    if verified.incomplete:
        raise ValueError("SHADOW_SLOT4_COMPLETED_PORTFOLIO_REQUIRED")
    snapshot = json.loads(original_bytes("portfolio_snapshot.json"))

    def last(name):
        rows = original_bytes(name).splitlines()
        if not rows:
            raise ValueError("SHADOW_SLOT4_POSITION_ROWS_REQUIRED")
        return json.loads(rows[-1])

    cycle_bytes = original_bytes("bridge_cycle_ledger.jsonl").splitlines()
    if not cycle_bytes:
        raise ValueError("SHADOW_SLOT4_POSITION_ROWS_REQUIRED")
    cycle = json.loads(cycle_bytes[-1])
    row = last("portfolio_snapshots.jsonl")
    if (
        session["session_id"] != row["session_id"]
        or session["session_id"] != cycle["session_id"]
        or old.selection.instrument_id != cycle["instrument_id"]
        or row["cycle_id"] != cycle["cycle_id"]
        or row["snapshot"] != snapshot
        or cycle["portfolio_snapshot"] != snapshot
        or portfolio_state_hash(snapshot) != row["portfolio_state_after_hash"]
        or row["portfolio_state_after_hash"] != cycle["portfolio_state_after_hash"]
    ):
        raise ValueError("SHADOW_SLOT4_POSITION_ORIGINAL_MISMATCH")
    event = cycle["shadow_decision_timing"]["decision_cycle_ts_unix"]
    truth = ranked_shadow_positions_from_snapshot_v1(
        snapshot, old, session_id=session["session_id"], now=event
    )
    portfolio = replace(truth, max_age_seconds=STARTUP_PORTFOLIO_MAX_AGE_SECONDS)
    if rotation_at is None:
        return portfolio
    from src.ops.ranked_shadow_slot4_rotation_v1 import (
        RECEIPT,
        adjudicate_slot4_closeout_v1,
        read_slot4_reconciliation_sources_v1,
    )

    if RECEIPT not in pins:
        raise ValueError("SHADOW_SLOT4_OWNER_CLOSEOUT_REQUIRED")
    receipt = json.loads(original_bytes(RECEIPT))
    if "unavailable" in receipt:
        raise ValueError("SHADOW_SLOT4_OWNER_CLOSEOUT_UNAVAILABLE")
    repository_sha = read_slot4_session_origin_v1(original_bytes, session["session_id"])
    if not historical and receipt["reconciliation"] != read_slot4_reconciliation_sources_v1(
        root, session["session_id"]
    ):
        raise ValueError("SHADOW_SLOT4_RECONCILIATION_SOURCE_CHANGED")
    decision = adjudicate_slot4_closeout_v1(
        receipt=receipt,
        portfolio=portfolio,
        economic=snapshot,
        cycles=[json.loads(raw) for raw in cycle_bytes],
        fills=[json.loads(raw) for raw in original_bytes("bridge_fill_ledger.jsonl").splitlines()],
        orders=json.loads(original_bytes("no_order_attestation.json")),
        shutdown=json.loads(original_bytes("shutdown_reason.json")),
        terminal=json.loads(original_bytes("terminal_verdict.json")),
        counters=json.loads(original_bytes("observation_cycle_counters.json")),
        completion=json.loads(original_bytes("completion_verdict.json")),
        session=session["session_id"],
        slot=old,
        repository_sha=repository_sha,
        entry_repository_sha=(
            predecessor.get("shadow_entry_admission") or predecessor["n5_source"]
        )["repository_sha"],
        now=rotation_at(),
    )
    if sealed != manifest.read_bytes():
        raise ValueError("SHADOW_SLOT4_OWNER_EVIDENCE_CHANGED")
    if (
        not receipt["captured_at_unix"]
        <= rotation_at()
        <= event + STARTUP_PORTFOLIO_MAX_AGE_SECONDS
    ):
        raise ValueError("SHADOW_SLOT4_OWNER_EVIDENCE_STALE")
    return portfolio, decision, sha256(sealed).hexdigest()


def _target_row(rank, universe):
    rows = [
        r
        for r in universe.instruments
        if r.venue_native_inst_id == TARGET.native_id and r.eligibility
    ]
    if (
        len(rows) != 1
        or (
            rows[0].canonical_instrument_id,
            rows[0].instrument_type,
            rows[0].contract_type,
            rows[0].quote_currency,
            rows[0].settlement_currency,
        )
        != (TARGET.canonical_id, "SWAP", "linear_perpetual", "USDT", "USDT")
        or (rank.universe_snapshot_id, rank.universe_payload_digest, rank.universe_source_digest)
        != (universe.snapshot_id, universe.payload_digest, universe.source_digest)
    ):
        raise ValueError("SHADOW_SLOT4_CAP21_CAP22_SCOPE_MISMATCH")
    return rows[0]


def _reconciled_positions(predecessor, old, document, original, now):
    """Match the current Shadow reconciler's complete observation to its own economic original."""
    from src.ops.productive_reconciliation_runtime_binding_v1.startup_portfolio_document_v1 import (
        read_startup_portfolio_document_v1,
    )
    from src.ops.ranked_shadow_entry_selection_v1 import ranked_shadow_positions_from_snapshot_v1

    session = predecessor["session_id"]
    observed = read_startup_portfolio_document_v1(
        document, expected_account_identity=f"SHADOW:{session}:{LANE}", now_unix=now
    )
    snapshot = json.loads(Path(original).read_bytes())
    truth = ranked_shadow_positions_from_snapshot_v1(
        snapshot, old, session_id=session, now=observed.event_time_unix
    )
    if truth.source_id != observed.source_id or {
        p.instrument_id: p.signed_quantity for p in truth.positions
    } != {p.instrument_id: p.signed_quantity for p in observed.positions}:
        raise ValueError("SHADOW_SLOT4_RECONCILIATION_ORIGINAL_MISMATCH")
    return replace(observed, max_age_seconds=STARTUP_PORTFOLIO_MAX_AGE_SECONDS)


def publish_shadow_slot4_successor_v1(
    *,
    predecessor_profile,
    predecessor_evidence_root,
    comparison_path,
    approved_comparison_sha256,
    ranking_root,
    universe_root,
    repository_sha,
    session_id,
    rotation_admission,
    reconciliation_document=None,
    shadow_portfolio_original=None,
    clock=time.time,
):
    """Consume owner observations. Publish only an N5/Cap23 reference, with no execution authority."""
    from src.ops.ranked_slot_run_source_v1 import read_ranked_run_slot_v1

    path = Path(predecessor_profile).resolve()
    predecessor, old = _original(path)
    if not session_id or session_id == predecessor["session_id"]:
        raise ValueError("SHADOW_SLOT4_NEW_SESSION_REQUIRED")
    base = successor_root_v1(old.selection_root.parent)
    ranking_root, universe_root = Path(ranking_root).resolve(), Path(universe_root).resolve()
    request = dict(
        predecessor_profile=str(path),
        predecessor_evidence_root=str(Path(predecessor_evidence_root).resolve()),
        comparison_path=str(Path(comparison_path).resolve()),
        approved_comparison_sha256=approved_comparison_sha256,
        predecessor=old.reference(),
        session_id=session_id,
        ranking_root=str(ranking_root),
        universe_root=str(universe_root),
        repository_sha=repository_sha,
    )

    def profile(receipt):
        s = receipt["recovery_plan"][LANE]["selection"]
        if receipt["recovery_plan"][LANE]["request"] != request:
            raise ValueError("SHADOW_SLOT4_SUCCESSOR_CONFLICT")
        return dict(
            session_id=session_id,
            surface="SHADOW",
            lane=LANE,
            authority="NONE",
            native_instrument_id=TARGET.native_id,
            canonical_instrument_id=TARGET.canonical_id,
            shadow_entry_cost_limit_usdc="10",
            n5_source=dict(
                topology_root=str(base),
                ranking_root=str(ranking_root),
                universe_root=str(universe_root),
                repository_sha=repository_sha,
                transition_id=receipt["transition_id"],
                selection_id=s["selection_id"],
                selection_digest=s["integrity_digest"],
            ),
        )

    def read_published_profile(receipt):
        from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
            immutable_json_v1,
        )

        result = profile(receipt)
        read_ranked_run_slot_v1(result)
        path = base / "slot.json"
        immutable_json_v1(path, result)
        return json.loads(path.read_bytes())

    # A rejected observation must leave even the previous slot's filesystem untouched.
    completed = store.load_completed_selection_publication_v1(base)
    if completed and not store.load_pending_selection_publication_v1(base):
        return read_published_profile(completed)
    if (reconciliation_document is None) != (shadow_portfolio_original is None):
        raise ValueError("SHADOW_SLOT4_RECONCILIATION_ORIGINAL_REQUIRED")
    if reconciliation_document is not None:
        corroborating = _reconciled_positions(
            predecessor, old, reconciliation_document, shadow_portfolio_original, clock()
        )
    observed_portfolio, owner_decision, source_digest = prepare_slot4_shadow_rotation_v1(
        path, predecessor_evidence_root, clock=clock
    )
    if (
        reconciliation_document is not None
        and observed_portfolio.source_id != corroborating.source_id
    ):
        raise ValueError("SHADOW_SLOT4_RECONCILIATION_ORIGINAL_MISMATCH")
    if not owner_decision.allowed:
        raise ValueError("SHADOW_SLOT4_ROTATION_VETO:" + owner_decision.reason_code)
    _check_clearance(old, predecessor, observed_portfolio, rotation_admission, clock())
    if rotation_admission != owner_decision:
        raise ValueError("SHADOW_SLOT4_ROTATION_DECISION_MISMATCH")

    def require_current_handoff():
        seal = Path(predecessor_evidence_root) / "evidence_manifest.sha256"
        sealed = seal.read_bytes()
        if seal.is_symlink() or sha256(sealed).hexdigest() != source_digest:
            raise ValueError("SHADOW_SLOT4_OWNER_EVIDENCE_CHANGED")
        from src.ops.ranked_shadow_slot4_rotation_v1 import (
            RECEIPT,
            read_slot4_reconciliation_sources_v1,
        )

        root = seal.parent
        raw = (root / RECEIPT).read_bytes()
        if (
            (root / RECEIPT).is_symlink()
            or f"{sha256(raw).hexdigest()}  {RECEIPT}" not in sealed.decode().splitlines()
        ):
            raise ValueError("SHADOW_SLOT4_OWNER_EVIDENCE_CHANGED")
        recorded = json.loads(raw)["reconciliation"]
        if recorded != read_slot4_reconciliation_sources_v1(root, predecessor["session_id"]):
            raise ValueError("SHADOW_SLOT4_RECONCILIATION_SOURCE_CHANGED")
        _check_clearance(old, predecessor, observed_portfolio, owner_decision, clock())

    rank = load_and_validate_ranking_snapshot_v1(
        ranking_root, expected_repository_sha=repository_sha
    )
    universe = load_and_validate_universe_snapshot_v1(
        universe_root, expected_repository_sha=repository_sha
    )
    if not rank.ok or not universe.ok:
        raise ValueError("SHADOW_SLOT4_GOVERNED_SOURCES_REQUIRED")
    rank, universe = rank.snapshot, universe.snapshot
    _target_row(rank, universe)
    manifest = store.load_completed_fixed_rank_publication_v1(old.selection_root.parent)
    occupied = {s["canonical_instrument_id"] for s in manifest["topology"]["slots"]}
    membership = build_bootstrap_membership_from_cap22_snapshot_v1(
        snapshot_path=ranking_root / SNAPSHOT_FILENAME, source_relative_path=SNAPSHOT_FILENAME
    )
    if (
        membership.cap22_provenance.ranking_integrity_digest != rank.integrity_digest
        or TARGET.canonical_id not in membership.ordered_instrument_ids
        or TARGET.canonical_id in occupied
        or _epoch(rank.event_time) <= _epoch(old.selection.ranking_event_time)
    ):
        raise ValueError("SHADOW_SLOT4_RANKING_OR_OCCUPANCY_MISMATCH")
    refs = dict(
        universe_snapshot_id=universe.snapshot_id,
        ranking_snapshot_id=rank.ranking_snapshot_id,
        ranking_integrity_digest=rank.integrity_digest,
    )
    slot = _occupied_slot(
        lane_id=LANE, instrument_id=TARGET.canonical_id, topology_state_root_base=base, **refs
    )
    topology = _finish_topology(
        membership=membership,
        topology_state_root_base=base,
        **refs,
        slots=[
            slot if lane == LANE else _empty_slot(lane_id=lane, topology_state_root_base=base)
            for lane in LANE_IDS
        ],
        initial_assignment_policy=SHADOW_SLOT4_SUCCESSOR_POLICY,
    )
    lane_root = Path(slot.lane_state_root)
    pin = build_governed_cap23_pin_v1(
        canonical_instrument_id=TARGET.canonical_id,
        ranking_snapshot=rank.to_dict(),
        lane_state_root=lane_root,
    )
    writer = DurableLaneAssignmentSingleWriterV1(
        store.checkpoint_root_for(base), session_id=session_id
    )
    writer.acquire()
    try:
        pending = store.load_pending_selection_publication_v1(base)
        completed = store.load_completed_selection_publication_v1(base)
        if completed and not pending:
            return read_published_profile(completed)
        now = clock()
        _check_clearance(old, predecessor, observed_portfolio, rotation_admission, now)
        if pending:
            profile(pending)
            if pending["topology"] != topology.to_dict():
                raise ValueError("SHADOW_SLOT4_SUCCESSOR_CONFLICT")
            store.validate_pending_publication_source_v1(base, pending)
        decision_time = pending["recovery_plan"][LANE]["decision_time_unix"] if pending else now
        require_slot4_nomination_v1(
            comparison_path,
            approved_comparison_sha256,
            target=TARGET,
            rank=rank,
            universe=universe,
            occupied=occupied,
            now=decision_time,
        )
        produced = produce_single_selected_future_v1(
            ranking_snapshot=rank.to_dict(),
            repository_sha=repository_sha,
            expected_ranking_repository_sha=repository_sha,
            producer_observed_at_unix=decision_time,
            previous_selection=old.selection,
            governed_pin=pin,
            lane_state_root=lane_root,
        )
        s = produced.selection
        if (
            not produced.ok
            or produced.hard_stop
            or s.state != "SELECTED_ACTIVE"
            or s.instrument_id != TARGET.canonical_id
            or s.previous_selection_id != old.selection.selection_id
            or not _epoch(s.valid_from) <= now <= _epoch(s.valid_until)
        ):
            raise ValueError("SHADOW_SLOT4_CAP23_DEFERRED:" + ",".join(s.reason_codes))
        evidence = build_selection_evidence_v1(
            produced=produced,
            persistence_path=str(lane_root),
            persistence_verification=None,
            restart_verification=None,
            previous_selection=old.selection.to_dict(),
        )
        if pending:
            plan = pending["recovery_plan"][LANE]
            if (
                plan.get("rotation_source_sha256") != source_digest
                or plan["portfolio"] != observed_portfolio.to_dict()
                or plan["clearance"] != asdict(owner_decision)
                or plan["selection"] != s.to_dict()
                or store.canonical_json_dumps(plan["evidence"])
                != store.canonical_json_dumps(evidence)
                or pending["selection_digests"] != {LANE: s.integrity_digest}
            ):
                raise ValueError("SHADOW_SLOT4_RECOVERY_MISMATCH")
            transition = pending["transition_id"]
        else:
            if store.prior_durable_lane_assignment_commit_exists(base) or lane_root.exists():
                raise ValueError("SHADOW_SLOT4_UNEXPLAINED_PRIOR_STATE")
            plan = dict(
                request=request,
                selection=s.to_dict(),
                evidence=evidence,
                portfolio=observed_portfolio.to_dict(),
                clearance=asdict(owner_decision),
                rotation_source_sha256=source_digest,
                decision_time_unix=decision_time,
            )
            require_current_handoff()
            transition = store.begin_selection_publication_v1(
                topology=topology,
                writer=writer,
                selection_digests={LANE: s.integrity_digest},
                recovery_plan={LANE: plan},
            )
        write_membership_context_artifact_v1(membership, store_root=base / "membership")
        lane_writer = SingleSelectedFutureSingleWriterV1(lane_root)
        lane_writer.acquire()
        try:
            require_current_handoff()
            # Previous selection lives in the immutable genesis, outside this new generation.
            resume_lane_selection_publication_v1(
                writer=lane_writer, selection=s, previous_digest=None, evidence=evidence
            )
            store.persist_durable_lane_assignment_v1(
                topology=topology, writer=writer, selection_publication_id=transition
            )
            require_current_handoff()
            store.finish_selection_publication_v1(
                topology=topology, writer=writer, transition_id=transition
            )
        finally:
            lane_writer.release()
        return read_published_profile(store.load_completed_selection_publication_v1(base))
    finally:
        writer.release()


def validate_successor_source_v1(config, receipt, s, rank, universe):
    from src.ops.hard_facts_system_closure_v1.position_aware_rotation_v1 import (
        PositionAwareRotationDecisionV1,
    )
    from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import (
        snapshot_from_payload,
    )

    plan = receipt["recovery_plan"][LANE]
    request = plan["request"]
    prior_config, old = _original(Path(request["predecessor_profile"]))
    proven, owner_decision, seal = _read_slot4_evidence(
        request["predecessor_profile"],
        request["predecessor_evidence_root"],
        rotation_at=lambda: plan["decision_time_unix"],
        historical=True,
    )
    if (
        plan.get("rotation_source_sha256") != seal
        or proven.to_dict() != plan["portfolio"]
        or asdict(owner_decision) != plan["clearance"]
    ):
        raise ValueError("SHADOW_SLOT4_ROTATION_SOURCE_MISMATCH")
    _check_clearance(
        old,
        prior_config,
        snapshot_from_payload(plan["portfolio"]),
        PositionAwareRotationDecisionV1(**plan["clearance"]),
        plan["decision_time_unix"],
    )
    source = config["n5_source"]
    _target_row(rank, universe)
    topology = receipt["topology"]
    membership = read_membership_context_artifact_v1(
        topology["membership_instance_id"], store_root=Path(source["topology_root"]) / "membership"
    )
    if (
        config["lane"] != LANE
        or config["surface"] != "SHADOW"
        or config.get("shadow_entry_cost_limit_usdc") != "10"
        or config["session_id"] != request["session_id"]
        or set(receipt["selection_digests"]) != {LANE}
        or plan["selection"] != s.to_dict()
        or request["predecessor"] != old.reference()
        or s.previous_selection_id != old.selection.selection_id
        or s.instrument_id != TARGET.canonical_id
        or Path(source["topology_root"]) != successor_root_v1(old.selection_root.parent)
        or membership.cap22_provenance.ranking_integrity_digest != rank.integrity_digest
        or s.instrument_id not in membership.ordered_instrument_ids
        or any(
            source[key] != request[key]
            for key in ("ranking_root", "universe_root", "repository_sha")
        )
    ):
        raise ValueError("SHADOW_SLOT4_SUCCESSOR_LINEAGE_MISMATCH")
    return old.reference()


def recorded_shadow_rank_matches_v1(ref, scope):
    if "slot4_successor" not in ref:
        return type(ref.get("selected_rank")) is int and ref["selected_rank"] == int(
            scope.lane_id.split("_")[1]
        )
    proof = ref["slot4_successor"]
    if (
        not isinstance(proof, dict)
        or not isinstance(proof.get("selection"), dict)
        or not isinstance(proof.get("predecessor"), dict)
    ):
        return False
    s = SingleSelectedFutureSelectionV1.from_dict(proof["selection"])
    old = proof["predecessor"]
    return (
        scope == TARGET
        and old["lane_id"] == LANE
        and old["venue_native_id"] == "PIEVERSE-USDT-SWAP"
        and s.instrument_id == TARGET.canonical_id
        and s.venue_native_id == TARGET.native_id
        and s.state == "SELECTED_ACTIVE"
        and old["transition_id"] != ref["transition_id"]
        and s.previous_selection_id == old["selection_id"]
        and validate_selection_bindings_v1(s).ok
        and type(ref["selected_rank"]) is int
        and ref["selected_rank"] > 0
        and s.previous_instrument_id == old["canonical_instrument_id"]
        and (
            s.selected_rank,
            s.selection_id,
            s.integrity_digest,
            s.ranking_snapshot_id,
            s.ranking_integrity_digest,
        )
        == (
            ref["selected_rank"],
            ref["selection_id"],
            ref["selection_digest"],
            ref["ranking_snapshot_id"],
            ref["ranking_digest"],
        )
    )
