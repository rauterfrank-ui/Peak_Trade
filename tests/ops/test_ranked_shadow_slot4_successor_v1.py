from dataclasses import replace
from hashlib import sha256
import json
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest

from src.ops import ranked_shadow_slot4_successor_v1 as successor
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1.checked_publication_v1 import (
    publish_checked_lane_selections_v1,
)
from src.ops.hard_facts_system_closure_v1.position_aware_rotation_v1 import (
    RotationPhase,
    evaluate_position_aware_rotation_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from src.ops.ranked_slot_run_source_v1 import read_ranked_run_slot_v1, read_ranked_shadow_profile_v1
from tests.ops import test_single_selected_future_runtime_binding_v1 as sample


@pytest.fixture
def abort_archive(tmp_path, monkeypatch):
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
        WallclockEvidenceWriterV1,
    )

    root = tmp_path / "evidence"
    root.mkdir()
    session_id = "old-shadow"
    native = "PIEVERSE-USDT-SWAP"
    canonical = successor.require_i17_shadow_instrument_v1((native,)).canonical_id
    assignment = dict(lane_id="LANE_4", venue_native_id=native, canonical_instrument_id=canonical)
    instrument = SimpleNamespace(
        canonical_instrument_id=canonical,
        venue_native_inst_id=native,
        contract_value_currency="PIEVERSE",
        base_currency="PIEVERSE",
        contract_value="10",
        lot_size="1",
    )
    slot = SimpleNamespace(reference=lambda: assignment, instrument=instrument, lane_id="LANE_4")
    config = {"session_id": session_id, "n5_source": {"repository_sha": sample.REPO_SHA}}
    monkeypatch.setattr(successor, "_original", lambda _: (config, slot))
    writer = WallclockEvidenceWriterV1(root)
    writer.ensure_append_files()
    writer.write_immutable_text("repo_sha.txt", sample.REPO_SHA)
    for name, data in {
        "session_manifest.json": dict(session_id=session_id, n5_assignment=assignment),
        "authorization_consumption.json": dict(
            session_id=session_id,
            authorization_id="test",
            mode="productive_wallclock_v2",
            productive_authorization=True,
            forced_wiring_fixture=False,
            consumed=True,
        ),
        "authorization_consumption_record.json": dict(
            session_id=session_id, authorization_id="test", expected_repository_sha=sample.REPO_SHA
        ),
    }.items():
        writer.write_immutable_json(name, data)
    return root, config, slot, writer


@pytest.fixture
def aborted_predecessor(abort_archive):
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1 import (
        TerminalVerdict,
    )

    root, config, _, writer = abort_archive
    writer.write_immutable_json("portfolio_snapshot.json", dict(stub=True))
    writer.write_immutable_json(
        "observation_cycle_counters.json", dict(cycle_count=0, accepted_ticks=0)
    )
    writer.write_immutable_json(
        "shutdown_reason.json", dict(state="ABORTED", killstate=dict(active=True))
    )
    writer.finalize(verdict=TerminalVerdict.ABORT, incomplete=True)
    return root, config


@pytest.mark.parametrize(
    "case", ["observed", "bound_budget", "partial_cycle", "open", "lock_lost", "reconciled"]
)
def test_quiescent_abort_owner_to_rotation_without_a_session(abort_archive, case):
    from decimal import Decimal
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1 import (
        session_runtime_v1 as host,
    )
    from src.ops.productive_reconciliation_runtime_binding_v1 import (
        run_productive_reconciliation_startup_gate_v1,
    )
    from src.ops.ranked_shadow_entry_selection_v1 import observe_ranked_shadow_positions_v1
    from src.ops.ranked_shadow_slot4_rotation_v1 import retain_slot4_observation_v1
    from src.trading.master_v2.double_play_entry_exit_policy_v0 import PositionState

    root, config, slot, writer = abort_archive
    session, now = config["session_id"], sample.OBSERVED_UNIX
    transport = SimpleNamespace(
        opened=False, candidate_last=False, venue_instrument_id=slot.instrument.venue_native_inst_id
    )
    runtime = host.WallclockSessionRuntimeV1(
        evidence_root=root, transport=transport, clock_wall=lambda: now
    )
    runtime.writer = writer
    runtime.consumed = True
    runtime.session_id = session
    state = runtime.bridge_state = host.HardenedBridgeSessionStateV2(
        session_id=session,
        instrument_id=slot.instrument.canonical_instrument_id,
        venue_instrument_id=slot.instrument.venue_native_inst_id,
    )
    runtime.state = host.WallclockSessionState.ABORTED
    runtime.killstate.raise_killstate(trigger="INVARIANT_VIOLATION", wall_ts=now - 0.25)
    runtime.lock = host.SessionLockV1(
        lock_path=root / "session.lock", owner=host.CAPABILITY_ID, session_id=session
    )
    runtime.lock.acquire()
    if case == "bound_budget":
        state.ranked_confirmed_entry_budget = {
            "session_id": session,
            "n5_assignment": slot.reference(),
            "decision_id": "pending",
        }
        state.position_state = PositionState.SUBMISSION_UNKNOWN
    elif case == "partial_cycle":
        state.cycle_index = 1
    elif case == "open":
        state.portfolio.apply_intended_action(
            instrument_id=state.instrument_id,
            side="SELL",
            quantity=Decimal("20"),
            mark_price=Decimal("1"),
            intent_id="pending",
            fill_id="fill",
        )
        state.venue_flat = False
    elif case == "lock_lost":
        runtime.lock.release()
    elif case == "reconciled":
        original = observe_ranked_shadow_positions_v1(state, slot, session_id=session, now=now - 1)
        gate = run_productive_reconciliation_startup_gate_v1(
            state_root=root / "post_reconnect_reconciliation",
            observed=original,
            session_id=session,
            repository_sha=sample.REPO_SHA,
            now_unix=now - 1,
        )
        assert gate.ok
        retain_slot4_observation_v1(state, slot, original, "reconnect")

    # Exercise only shutdown, never the host's start, market or trading entry point.
    result = runtime._finalize_result(session_id=session, incomplete=True, ranked_slot=slot)
    assert result.terminal_verdict == "ABORT" and not result.network_opened
    assert not runtime.lock.acquired

    def read(at):
        with pytest.raises(successor.Slot4ShadowRecoveryRequired) as denied:
            successor.prepare_slot4_shadow_rotation_v1("slot.json", root, clock=lambda: at)
        return denied.value.evidence

    evidence = read(now)
    review = evidence["abort_owner_observation"]
    if case == "lock_lost":
        assert review is None and evidence["abort_owner_observation_unavailable"] == "LOCK_LOSS"
        return
    inputs = review["current_inputs"]
    assert inputs["lane_health_allows_replacement"] is False and review["observed_at_unix"] == now
    assert inputs["venue_flat"] is (case != "open")
    if case == "reconciled":
        assert inputs["reconciled"] is True and review["rotation_owner_reason"] == "COMMIT_VETO"
        assert read(now + 5)["abort_owner_observation"]["current_inputs"]["reconciled"] is None
    else:
        assert inputs["reconciled"] is None and review["rotation_owner_reason"] is None
    if case == "open":
        assert review["positions_native_contracts"][0]["signed_quantity"] == "-2"
    if case in ("partial_cycle", "open"):
        assert (
            inputs["pending_external_custody"] is None
            and inputs["pending_pre_external_custody"] is None
        )
    else:
        assert inputs["pending_external_custody"] is (case == "bound_budget")
        assert inputs["pending_pre_external_custody"] is (case == "bound_budget")
    historical = read(now + 5.001)["abort_owner_observation"]
    assert not historical["fresh"] and set(historical["current_inputs"].values()) == {None}


def test_abort_inspection_preserves_unknown_owner_inputs(aborted_predecessor, capsys):
    from scripts.ops.inspect_shadow_slot4_rotation_v1 import main

    root, _ = aborted_predecessor
    args = ["--predecessor-profile", "slot.json", "--evidence-root", str(root)]
    assert main(args) == 2
    result = json.loads(capsys.readouterr().out)
    assert (result["status"], result["published"], result["authority"]) == (
        "BLOCKED",
        False,
        "NONE",
    )
    evidence = result["recovery"]
    history = evidence["historical_session"]
    assert history["cycle_count"] == 0 and history["portfolio_stub"] is True
    assert history["no_order_attestation"] is None  # absent differs from a zero count
    assert history["shutdown"]["killstate"]["active"] is True
    assert {r["status"] for r in evidence["reconciliation_readbacks"].values()} == {"ABSENT"}
    assert set(evidence["unproven_rotation_inputs"]) == {
        "venue_flat",
        "reconciled",
        "pending_pre_external_custody",
        "pending_external_custody",
        "lane_health_allows_replacement",
    }
    # A partial readback and loose, unsealed files cannot establish an owner decision.
    (root / "post_reconnect_reconciliation").mkdir()
    (root / "slot4_shadow_closeout_v1.json").write_text("{}")
    assert main(args) == 2
    recovery = json.loads(capsys.readouterr().out)["recovery"]
    assert recovery["reconciliation_readbacks"]["entry"]["status"] == "ABSENT"
    assert recovery["reconciliation_readbacks"]["reconnect"]["status"] == "INVALID_OR_INCOMPLETE"
    assert recovery["historical_session"]["closeout_in_manifest"] is False


def test_abort_inspection_rejects_foreign_or_tampered_archive(aborted_predecessor):
    root, config = aborted_predecessor
    config["session_id"] = "another-shadow"
    with pytest.raises(ValueError, match="POSITION_ORIGINAL_MISMATCH"):
        successor.prepare_slot4_shadow_rotation_v1("slot.json", root)
    config["session_id"] = "old-shadow"
    (root / "portfolio_snapshot.json").write_text('{"positions":[]}')
    with pytest.raises(ValueError, match="ARCHIVE_VERIFICATION_FAILED"):
        successor.prepare_slot4_shadow_rotation_v1("slot.json", root)


def test_sealed_reconciliation_pair_cannot_clear_aborted_shadow(aborted_predecessor):
    from src.ops.productive_reconciliation_runtime_binding_v1 import (
        run_productive_reconciliation_startup_gate_v1,
    )

    root, _ = aborted_predecessor
    now = sample.OBSERVED_UNIX
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=root / "post_reconnect_reconciliation",
        observed=PortfolioTruthSnapshotV1(
            source_id="foreign", event_time_unix=now, wall_time_unix=now
        ),
        session_id="other-session",
        repository_sha=sample.REPO_SHA,
        now_unix=now,
    )
    assert gate.ok
    with pytest.raises(successor.Slot4ShadowRecoveryRequired) as denied:
        successor.prepare_slot4_shadow_rotation_v1("slot.json", root, clock=lambda: now)
    evidence = denied.value.evidence
    assert evidence["reconciliation_readbacks"]["reconnect"]["status"] == "SEALED_FILES_ONLY"
    assert "venue_flat" in evidence["unproven_rotation_inputs"]


def _comparison(root, now, ranking):
    target = successor.TARGET
    from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
        swap_queries_v1,
    )

    routes = {
        target.native_id + "." + k: v
        for k, v in swap_queries_v1(target.native_id, target.base + "-USDT").items()
    }
    routes[target.native_id + ".instrument"] = (
        "/api/v5/public/instruments",
        {"instId": target.native_id, "instType": "SWAP"},
    )
    routes["fx"] = ("/api/v5/market/index-tickers", {"instId": "USDC-USDT"})
    receipts = {}
    for key, (path, query) in routes.items():
        data = dict(
            instId=query["instId"],
            ts=str(int((now - 1) * 1000)),
            fundingTime=str(int((now + 600) * 1000)),
        )
        data.update(
            markPx="1",
            idxPx="1",
            bids=[["0.99", "10", "0", "1"]],
            asks=[["1.01", "10", "0", "1"]],
            fundingRate="0",
            minFundingRate="0",
            maxFundingRate="0",
        )
        if key.endswith(".instrument"):
            data.update(
                sample._perp(target.native_id, base=target.base, ct_val="1"), maxMktSz="100"
            )
        raw = json.dumps({"code": "0", "data": [data]}).encode()
        (root / (key + ".json")).write_bytes(raw)
        receipts[key] = dict(
            sha256=sha256(raw).hexdigest(),
            url="https://eea.okx.com" + path + "?" + urlencode(query),
            started=now - 0.3 if key == "fx" else now - 0.7,
            received=now - 0.1 if key == "fx" else now - 0.5,
        )
    costs = {
        side + "_" + bound: ("1.0204020402" if bound == "lower" else "2")
        for side in ("BUY", "SELL")
        for bound in ("lower", "upper")
    }
    row = dict(
        instrument=target.native_id,
        rank=1,
        contracts="1",
        nominal_usdc="1",
        freshness_blockers=[],
        public_and_budget_screen=True,
        within_cost_envelope=True,
        costs_included_usdc=costs,
    )
    result = dict(
        ranking_digest=ranking["integrity_digest"],
        ranking_id=ranking["ranking_snapshot_id"],
        authority="NONE",
        test_limit_usdc="10",
        rows=[row],
        receipts=receipts,
    )
    path = root / "Auswahl.json"
    path.write_text(json.dumps(result))
    return path, sha256(path.read_bytes()).hexdigest()


def _fixed_shadow_sources(original_dir, slot4="PIEVERSE"):
    original_dir.mkdir()
    previous = sample._build_chain(
        original_dir,
        [
            sample._perp(name + "-USDT-SWAP", base=name)
            for name in ("AAA", "BBB", "CCC", slot4, "ZZZ")
        ],
    )
    ranking_root = previous["ranking_root"]
    ranking = json.loads((ranking_root / successor.SNAPSHOT_FILENAME).read_bytes())
    membership = successor.build_bootstrap_membership_from_cap22_snapshot_v1(
        snapshot_path=ranking_root / successor.SNAPSHOT_FILENAME,
        source_relative_path=successor.SNAPSHOT_FILENAME,
    )
    base = original_dir / "topology"
    writer = successor.DurableLaneAssignmentSingleWriterV1(
        successor.store.checkpoint_root_for(base)
    )
    writer.acquire()
    try:
        original = publish_checked_lane_selections_v1(
            membership=membership,
            ranking_snapshot=ranking,
            topology_state_root_base=base,
            repository_sha=sample.REPO_SHA,
            writer=writer,
            producer_observed_at_unix=sample.OBSERVED_UNIX,
            fixed_rank_slots=(1, 2, 4, 5),
        )
    finally:
        writer.release()
    receipt = successor.store.load_completed_fixed_rank_publication_v1(base)

    def original_config(lane):
        s = original.selections[lane]
        return dict(
            lane=lane,
            session_id="old-shadow",
            authority="NONE",
            surface="SHADOW",
            native_instrument_id=s.venue_native_id,
            canonical_instrument_id=s.instrument_id,
            n5_source=dict(
                repository_sha=sample.REPO_SHA,
                universe_root=str(previous["universe_root"]),
                ranking_root=str(ranking_root),
                topology_root=str(base),
                transition_id=receipt["transition_id"],
                selection_id=s.selection_id,
                selection_digest=s.integrity_digest,
            ),
        )

    return base, original, receipt, original_config


def test_scoped_shadow_rotation(tmp_path, monkeypatch):
    original_dir = tmp_path / "original"
    base, original, receipt, original_config = _fixed_shadow_sources(original_dir)
    old_cfg = original_config("LANE_4")
    assert old_cfg["native_instrument_id"] == "PIEVERSE-USDT-SWAP"
    old = read_ranked_run_slot_v1(old_cfg)
    predecessor = original_dir / "slot.json"
    predecessor.write_text(json.dumps(old_cfg))
    now = sample.OBSERVED_UNIX + 7200
    monkeypatch.setattr(sample, "OBSERVED_UNIX", now)
    monkeypatch.setattr(sample, "SOURCE_EVENT", str(int((now - 1) * 1000)))
    dest = tmp_path / "new"
    dest.mkdir()
    new = sample._build_chain(
        dest, [sample._perp(successor.TARGET.native_id, base=successor.TARGET.base, ct_val="1")]
    )
    prices, approved = _comparison(
        dest, now, json.loads((new["ranking_root"] / successor.SNAPSHOT_FILENAME).read_bytes())
    )
    args = dict(
        predecessor_profile=predecessor,
        predecessor_evidence_root=original_dir / "evidence",
        comparison_path=prices,
        approved_comparison_sha256=approved,
        ranking_root=new["ranking_root"],
        universe_root=new["universe_root"],
        repository_sha=sample.REPO_SHA,
        session_id="new-shadow",
        clock=lambda: now,
    )
    admit = evaluate_position_aware_rotation_v1(
        phase=RotationPhase.COMMIT,
        venue_flat=True,
        reconciled=True,
        pending_external_custody=False,
        pending_pre_external_custody=False,
        lane_health_allows_replacement=True,
    )
    flat = PortfolioTruthSnapshotV1(
        event_time_unix=now,
        wall_time_unix=now,
        max_age_seconds=5,
        source_id="SHADOW:old-shadow:LANE_4:" + "7" * 64,
    )
    with pytest.raises(ValueError, match="COMPLETED_PORTFOLIO_REQUIRED"):
        successor.publish_shadow_slot4_successor_v1(**args, rotation_admission=admit)
    for truth, decision, reason in (
        (None, admit, "POSITION_TRUTH_UNPROVEN"),
        (replace(flat, event_time_unix=now - 6), admit, "POSITION_TRUTH_UNPROVEN"),
        (
            replace(flat, source_id="SHADOW:another-shadow:LANE_4:" + "7" * 64),
            admit,
            "POSITION_SOURCE_MISMATCH",
        ),
        (
            replace(
                flat,
                positions=(
                    PositionTruthV1.from_signed(
                        instrument_id=old.selection.instrument_id, signed_quantity=1
                    ),
                ),
            ),
            admit,
            "OPEN_POSITION",
        ),
        (flat, None, "CUSTODY_ADMISSION_REQUIRED"),
    ):
        with pytest.raises(ValueError, match=reason):
            successor._check_clearance(old, old_cfg, truth, decision, now)
    assert not successor.successor_root_v1(base).exists()
    from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.idempotent_portfolio_v2 import (
        IdempotentPortfolioV2,
    )

    from types import SimpleNamespace
    from src.ops.productive_reconciliation_runtime_binding_v1 import (
        run_productive_reconciliation_startup_gate_v1,
    )
    from src.ops.ranked_shadow_entry_selection_v1 import observe_ranked_shadow_positions_v1
    from src.ops import ranked_shadow_slot4_rotation_v1 as rotation
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
        WallclockEvidenceWriterV1,
    )
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1 import (
        TerminalVerdict,
    )
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.provenance_v2 import (
        portfolio_state_hash,
    )
    from src.trading.master_v2.double_play_state import SideState
    from src.trading.master_v2.double_play_entry_exit_policy_v0 import PositionState
    from decimal import Decimal

    ev = args["predecessor_evidence_root"]
    ev.mkdir()
    account = IdempotentPortfolioV2()
    account.apply_intended_action(
        instrument_id=old.selection.instrument_id,
        side="HOLD",
        quantity=Decimal(0),
        mark_price=Decimal(1),
        intent_id="hold",
    )
    snapshot = dict(account.snapshot())
    cycle = dict(
        cycle_id="cycle",
        cycle_index=1,
        intent_id="hold",
        decision_outcome="hold",
        intended_action=dict(
            intent_id="hold", intended_side="HOLD", intended_quantity="0", intent_action="NONE"
        ),
        session_id="old-shadow",
        instrument_id=old.selection.instrument_id,
        fill=None,
        fill_id=None,
        portfolio_snapshot=snapshot,
        portfolio_state_after_hash=portfolio_state_hash(snapshot),
        shadow_decision_timing=dict(decision_cycle_ts_unix=now),
    )
    bridge = SimpleNamespace(
        session_id="old-shadow",
        instrument_id=old.selection.instrument_id,
        venue_instrument_id="PIEVERSE-USDT-SWAP",
        portfolio=account,
        cycle_ledger=[cycle],
        ranked_confirmed_entry_budget=None,
        position_state=PositionState.FLAT_RECONCILED,
        venue_flat=True,
        slot4_reconciliation_observations={},
        killstate_active=False,
        side_state=SideState.NEUTRAL_OBSERVE,
    )
    runtime = SimpleNamespace(
        bridge_state=bridge,
        clock_wall=lambda: now,
        evidence_root=ev,
        _post_reconnect_reconciliation_required=False,
        quality_fail=False,
    )
    original_truth = observe_ranked_shadow_positions_v1(
        bridge, old, session_id="old-shadow", now=now
    )
    recon = ev.parent / "entry-reconciliation" / "old-shadow"
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=recon,
        observed=original_truth,
        session_id="old-shadow",
        repository_sha=sample.REPO_SHA,
        now_unix=now,
    )
    assert gate.ok
    rotation.retain_slot4_observation_v1(bridge, old, original_truth, "entry")
    closeout = rotation.capture_slot4_shadow_closeout_v1(runtime, old, "old-shadow")
    bridge.cycle_ledger = []
    assert (
        rotation.capture_slot4_shadow_closeout_v1(runtime, old, "old-shadow")["unavailable"]
        == "SHADOW_SLOT4_NO_CONFIRMED_CYCLE"
    )
    bridge.cycle_ledger = [cycle]
    session = dict(session_id="old-shadow", n5_assignment=old.reference())
    shutdown = dict(
        state="COMPLETED", killstate=dict(active=False, events=[], last_trigger=""), blockers=[]
    )
    counters = dict(cycle_count=1, accepted_ticks=1)
    complete = dict(full_economic_reconstruction_pass=True)
    orders = dict(ok=True, orders_allowed=False, orders_submitted=0, broker_writes_performed=0)
    writer = WallclockEvidenceWriterV1(ev)
    writer.ensure_append_files()
    writer.write_immutable_text("repo_sha.txt", sample.REPO_SHA)
    writer.append_event("bridge_cycle_ledger.jsonl", cycle)
    writer.append_event(
        "portfolio_snapshots.jsonl",
        dict(
            session_id="old-shadow",
            cycle_id="cycle",
            snapshot=snapshot,
            portfolio_state_after_hash=portfolio_state_hash(snapshot),
        ),
    )
    for name, payload in {
        "authorization_consumption.json": dict(
            session_id="old-shadow",
            mode="productive_wallclock_v2",
            authorization_id="synthetic-test",
            consumed=True,
            productive_authorization=True,
            forced_wiring_fixture=False,
        ),
        "authorization_consumption_record.json": dict(
            session_id="old-shadow",
            authorization_id="synthetic-test",
            expected_repository_sha=sample.REPO_SHA,
        ),
        "portfolio_snapshot.json": snapshot,
        "session_manifest.json": session,
        "shutdown_reason.json": shutdown,
        "completion_verdict.json": complete,
        "observation_cycle_counters.json": counters,
        "no_order_attestation.json": orders,
        rotation.RECEIPT: closeout,
    }.items():
        writer.write_immutable_json(name, payload)
    writer.finalize(verdict=TerminalVerdict.PASS, incomplete=False)
    owner_args = dict(
        receipt=closeout,
        portfolio=replace(original_truth, max_age_seconds=5),
        economic=snapshot,
        cycles=[cycle],
        fills=[],
        orders=orders,
        shutdown=shutdown,
        terminal=json.loads((ev / "terminal_verdict.json").read_bytes()),
        counters=counters,
        completion=complete,
        session="old-shadow",
        slot=old,
        repository_sha=sample.REPO_SHA,
        entry_repository_sha=sample.REPO_SHA,
        now=now,
    )
    assert rotation.adjudicate_slot4_closeout_v1(**owner_args) == admit
    changed_original = dict(
        closeout["original_observations"]["entry"],
        n5_assignment=dict(old.reference(), lane_id="LANE_1"),
    )
    with pytest.raises(ValueError, match="OBSERVATION_REQUIRED"):
        rotation.adjudicate_slot4_closeout_v1(
            **(
                owner_args
                | {"receipt": dict(closeout, original_observations={"entry": changed_original})}
            )
        )
    for fields, reason in [
        (
            dict(receipt=dict(closeout, confirmed_entry_budget={"decision": "pending"})),
            "PENDING_CUSTODY_CONFLICT",
        ),
        (dict(receipt=dict(closeout, bridge_killstate_active=True)), "COMMIT_VETO"),
        (
            dict(receipt=dict(closeout, bridge_position_state="submission_unknown")),
            "PENDING_CUSTODY_CONFLICT",
        ),
        (
            dict(receipt=dict(closeout, bridge_position_state="reconciliation_required")),
            "NOT_RECONCILED",
        ),
        (dict(receipt=dict(closeout, reconnect_reconciliation_pending=True)), "COMMIT_VETO"),
        (dict(shutdown=dict(shutdown, state="ABORTED")), "COMMIT_VETO"),
        (
            dict(
                cycles=[
                    dict(
                        cycle,
                        intended_action=dict(
                            cycle["intended_action"], intended_side="BUY", intended_quantity="1"
                        ),
                    )
                ]
            ),
            "PENDING_CUSTODY_CONFLICT",
        ),
    ]:
        denied = rotation.adjudicate_slot4_closeout_v1(**(owner_args | fields))
        assert not denied.allowed and denied.reason_code == reason
    for fields, reason in [
        (dict(now=now + 5.01), "STALE"),
        (dict(receipt=dict(closeout, reconciliation={})), "READBACK_REQUIRED"),
        (dict(receipt=dict(closeout, session_id="foreign")), "SCOPE_MISMATCH"),
        (dict(fills=[{}]), "LEDGER_MISMATCH"),
        (dict(orders=dict(orders, orders_submitted=1)), "EXTERNAL_BOUNDARY"),
    ]:
        with pytest.raises(ValueError, match=reason):
            rotation.adjudicate_slot4_closeout_v1(**(owner_args | fields))
    assert (
        successor.prepare_slot4_shadow_rotation_v1(predecessor, ev, clock=lambda: now)[1] == admit
    )
    # A valid decision supplied by a caller cannot override a changed original owner.
    from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
        PORTFOLIO_STATE_FILENAME,
    )

    owner_file = recon / PORTFOLIO_STATE_FILENAME
    original_bytes = owner_file.read_bytes()
    owner_file.write_text("{}")
    with pytest.raises(ValueError, match="RECONCILIATION_READBACK_INVALID"):
        successor.publish_shadow_slot4_successor_v1(**args, rotation_admission=admit)
    assert not successor.successor_root_v1(base).exists()
    owner_file.write_bytes(original_bytes)
    original_finish = successor.store.finish_selection_publication_v1

    def crash(**kwargs):
        raise OSError("interrupted before finish")

    monkeypatch.setattr(successor.store, "finish_selection_publication_v1", crash)
    with pytest.raises(OSError, match="interrupted"):
        successor.publish_shadow_slot4_successor_v1(**args, rotation_admission=admit)
    with pytest.raises(ValueError, match="SUPERSEDED"):
        read_ranked_run_slot_v1(old_cfg)
    with pytest.raises(ValueError, match="STALE"):
        successor.publish_shadow_slot4_successor_v1(
            **(args | {"clock": lambda: now + 6}), rotation_admission=admit
        )
    monkeypatch.setattr(successor.store, "finish_selection_publication_v1", original_finish)
    economic = dest / "economic.json"
    economic.write_text(json.dumps(snapshot))
    document = dest / "observed.json"
    ticket = dict(
        schema="peaktrade.startup_portfolio_observation.v1",
        account_identity="SHADOW:old-shadow:LANE_4",
        instrument_type="SWAP",
        complete_account_scope=True,
        pending_orders=False,
        source_id="SHADOW:old-shadow:LANE_4:" + canonical_digest_v1(snapshot),
        event_time_unix=now,
        wall_time_unix=now,
        positions=[],
    )
    args.update(reconciliation_document=document, shadow_portfolio_original=economic)
    document.write_text(json.dumps(dict(ticket, pending_orders=True)))
    with pytest.raises(ValueError, match="PENDING_ORDERS"):
        successor.publish_shadow_slot4_successor_v1(**args, rotation_admission=admit)
    document.write_text(json.dumps(dict(ticket, source_id="SHADOW:old-shadow:LANE_4:" + "8" * 64)))
    with pytest.raises(ValueError, match="RECONCILIATION_ORIGINAL_MISMATCH"):
        successor.publish_shadow_slot4_successor_v1(**args, rotation_admission=admit)
    document.write_text(json.dumps(ticket))
    config = successor.publish_shadow_slot4_successor_v1(**args, rotation_admission=admit)
    assert successor.publish_shadow_slot4_successor_v1(**args, rotation_admission=None) == config
    path = successor.successor_root_v1(base) / "slot.json"
    assert json.loads(path.read_bytes()) == config
    selected = read_ranked_shadow_profile_v1(path, successor.TARGET, "new-shadow")
    assert selected.lane_id == "LANE_4" and selected.selection.selected_rank == 1
    assert selected.selection.previous_selection_id == old.selection.selection_id
    gate = sample._run_gate(
        new,
        selection_state_root=selected.selection_root,
        now_unix=now,
        session_id=config["session_id"],
        observed_portfolio=sample._empty_portfolio(now),
    )
    assert gate.ok
    selected.require_binding_v1(gate.bound)
    assert successor.recorded_shadow_rank_matches_v1(selected.reference(), successor.TARGET)
    assert not successor.recorded_shadow_rank_matches_v1(
        dict(selected.reference(), selected_rank=4), successor.TARGET
    )
    with pytest.raises(ValueError, match="SUPERSEDED"):
        read_ranked_run_slot_v1(old_cfg)
    with pytest.raises(ValueError, match="LINEAGE_MISMATCH"):
        read_ranked_run_slot_v1(dict(config, shadow_entry_cost_limit_usdc="25"))
    for lane in ("LANE_1", "LANE_2", "LANE_5"):
        assert read_ranked_run_slot_v1(original_config(lane)).selection == original.selections[lane]
    assert successor.store.load_completed_fixed_rank_publication_v1(base) == receipt
