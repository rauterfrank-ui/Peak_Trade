"""Real owner flow, per-instrument isolation and consumer-side expiry, offline."""

from dataclasses import replace
from decimal import Decimal
import json
import socket

import pytest

from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
    IRYS_PAPER_SLOT,
    UP_PAPER_SLOT,
    ZKP_PAPER_SLOT,
    XperpPaperSlotV1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.instrument_card_stream_v1 import (
    InstrumentCardStreamV1,
    read_instrument_card_v1,
    shadow_budget_source_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
)
from tests.ops.test_zkp_lane1_paper_opening_v1 import REPO, _market
from scripts.ops import run_zkp_lane1_paper_v1 as paper_cli
from tests.ops.test_integrated_paper_shadow_observation_wallclock_session_execution_v1 import (
    run_two_hour_shadow,
    SOPH_I17,
)

D = Decimal
SOPH = XperpPaperSlotV1("LANE_5", "SOPH", "310912")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def fail(*a, **kw):
        raise AssertionError("OFFLINE_ONLY")

    monkeypatch.setattr(socket.socket, "connect", fail)
    monkeypatch.setattr(socket.socket, "connect_ex", fail)


def bound(market):
    return BoundInstrumentV1(
        instrument_id=market.slot.instrument_id,
        venue_native_id=market.slot.native_id,
        ranking_snapshot_id="",
        ranking_integrity_digest="",
        universe_snapshot_id="",
        selection_id="explicit-offline-test",
        selection_integrity_digest="a" * 64,
        selection_state="EXPLICIT_SINGLE_INSTRUMENT_PAPER",
    )


def budget_source(amount):
    def capture(*, market, now):
        original = {"available_usdc": amount[0]}
        return dict(
            status="BOUND",
            owner="EXPLICIT_OFFLINE_BUDGET_FIXTURE",
            currency="USDC",
            lane_id=market.slot.lane_id,
            instrument_id=market.slot.instrument_id,
            observed_unix=now,
            available_amount=amount[0],
            available_for_new_entry=amount[0],
            original_snapshot=original,
            source_digest=canonical_digest_v1(original),
        )

    return capture


def stream(tmp_path, market, amount=None):
    return InstrumentCardStreamV1(
        root=tmp_path,
        bound=bound(market),
        lane_id=market.slot.lane_id,
        source_mode="SHADOW" if market.slot == SOPH else "PAPER",
        session_id="offline",
        budget_source=budget_source(["25"] if amount is None else amount),
    )


@pytest.mark.parametrize("slot", [ZKP_PAPER_SLOT, UP_PAPER_SLOT, IRYS_PAPER_SLOT, SOPH])
def test_successive_original_sources_change_only_their_own_card(tmp_path, slot):
    market = _market(slot=slot)
    other = _market(slot=UP_PAPER_SLOT if slot != UP_PAPER_SLOT else ZKP_PAPER_SLOT)
    current, isolated = stream(tmp_path, market), stream(tmp_path, other)
    before = isolated.update_v1(other, now=other.observed_unix)
    versions, prices = [], []
    for step in range(3):
        fresh = _market(step, slot=slot)
        card = current.update_v1(fresh, now=fresh.observed_unix)
        versions.append(card["version"])
        prices.append(card["market"]["mark_price"])
        assert card["market"]["funding_rate"] == float(fresh.funding_rate)
        assert card["market"]["open_interest_contracts"] == float(fresh.oi_contracts)
        assert card["market"]["volume_contracts_24h"] == float(fresh.volume_contracts)
        assert len(card["sources"]) == 13
        receipts = json.loads(
            (current.root / "versions" / card["version"] / "source-receipts.json").read_bytes()
        )
        for label, receipt in receipts.items():
            assert receipt["payload"] == fresh.source_observations[label].payload
            assert (current.root / "sources" / receipt["body_sha256"]).is_file()
        assert card["assignment_status"] == "EXPLICIT_ISOLATED_TEST_BINDING"
    assert len(set(versions)) == len(set(prices)) == 3
    assert isolated.current == before
    assert (
        read_instrument_card_v1(
            tmp_path, bound=bound(market), lane_id=slot.lane_id, now=fresh.observed_unix
        )["version"]
        == versions[-1]
    )


def test_current_budget_change_clears_previous_evaluation_and_reader_expires(tmp_path):
    market = _market()
    amount = ["25"]
    card = stream(tmp_path, market, amount)
    before = card.update_v1(market, now=market.observed_unix)
    card.current["master_v2"] = {"decision": "PREVIOUS_ORIGINAL_DECISION"}
    amount[0] = "7"
    changed = card.current_v1(now=market.observed_unix)
    assert changed["version"] != before["version"]
    assert changed["master_v2"] is None
    assert D(changed["budget_assessment"]["BUY"]["available_budget_usdc"]) == 7
    expired = read_instrument_card_v1(
        tmp_path, bound=bound(market), lane_id=market.slot.lane_id, now=market.observed_unix + 6
    )
    assert (
        expired["status"] == "BLOCKED"
        and expired["market"] is None
        and expired["master_v2"] is None
    )
    assert expired["budget_assessment"] is None
    # Cold reader never declares a stored version current without fresh inputs.
    cold = stream(tmp_path, market)
    assert cold.current_v1(now=market.observed_unix)["status"] == "BLOCKED"


@pytest.mark.parametrize("fault", ["foreign", "derived", "bytes", "clock", "budget"])
def test_invalid_update_removes_previous_values_and_does_not_touch_other_slot(tmp_path, fault):
    market, other = _market(), _market(slot=UP_PAPER_SLOT)
    amount = ["25"]
    current, isolated = stream(tmp_path, market, amount), stream(tmp_path, other)
    current.update_v1(market, now=market.observed_unix)
    before = isolated.update_v1(other, now=other.observed_unix)
    update = market
    now = market.observed_unix
    if fault == "foreign":
        update = other
    if fault == "derived":
        update = replace(market, oi_contracts=market.oi_contracts + 1)
    if fault == "bytes":
        update = replace(market, original_bodies={"mark": b"{}"})
    if fault == "clock":
        now += 6
    if fault == "budget":
        amount[0] = "NaN"
    with pytest.raises((ValueError, ArithmeticError)):
        current.update_v1(update, now=now)
    assert current.current["status"] == "BLOCKED" and current.current["market"] is None
    assert isolated.current == before


def test_shadow_budget_reads_original_portfolio_and_does_not_offer_occupied_capital_twice(tmp_path):
    market = _market(slot=SOPH)
    state = HardenedBridgeSessionStateV2(
        instrument_id=market.slot.instrument_id, venue_instrument_id=market.slot.native_id
    )
    source = shadow_budget_source_v1(state, repo=REPO)
    budget = source(market=market, now=market.observed_unix)
    assert D(budget["available_amount"]) == 25
    assert D(state.portfolio.snapshot()["params"]["initial_equity"]) == 25
    state.portfolio.apply_intended_action(
        instrument_id=state.instrument_id,
        side="BUY",
        quantity=D(1),
        mark_price=market.mark,
        intent_id="original-analytical-intent",
        fill_id="original-analytical-fill",
    )
    original = state.portfolio.snapshot()
    current = source(market=_market(1, slot=SOPH), now=market.observed_unix + 2)
    assert D(current["available_amount"]) <= 25 and current["available_for_new_entry"] == "0"
    assert current["reserved_amount"] is None
    assert state.portfolio.snapshot() == original


def test_reader_rejects_changed_bytes_and_foreign_binding(tmp_path):
    market = _market()
    card = stream(tmp_path, market)
    card.update_v1(market, now=market.observed_unix)
    with pytest.raises(ValueError, match="IDENTITY"):
        read_instrument_card_v1(
            tmp_path,
            bound=bound(_market(slot=UP_PAPER_SLOT)),
            lane_id=market.slot.lane_id,
            now=market.observed_unix,
        )
    latest = card.root / "latest.json"
    record = json.loads(latest.read_bytes())
    record["body"]["market"]["mark_price"] += 1
    latest.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="DIGEST"):
        read_instrument_card_v1(
            tmp_path, bound=bound(market), lane_id=market.slot.lane_id, now=market.observed_unix
        )


def test_ranking_assignment_carries_original_generation_and_rejects_rebinding(tmp_path):
    market = _market()
    original = bound(market)
    ranked = replace(
        original,
        ranking_snapshot_id="ranking-fixture",
        ranking_integrity_digest="2" * 64,
        universe_snapshot_id="universe-fixture",
        selection_id="cap23-original-selection",
    )
    args = dict(
        root=tmp_path,
        bound=original,
        lane_id=market.slot.lane_id,
        source_mode="PAPER",
        session_id="offline",
        budget_source=budget_source(["25"]),
    )
    card = InstrumentCardStreamV1(**args, ranking_bound=ranked)
    row = card.update_v1(market, now=market.observed_unix)
    assert row["ranking_binding"] == ranked.to_dict()
    assert row["slot_identity"]["selection_id"] == ranked.selection_id
    assert row["slot_identity"]["instrument_epoch"]
    assert (
        read_instrument_card_v1(
            tmp_path,
            bound=original,
            lane_id=market.slot.lane_id,
            now=market.observed_unix,
            ranking_bound=ranked,
        )["version"]
        == row["version"]
    )
    with pytest.raises(ValueError, match="IDENTITY"):
        read_instrument_card_v1(
            tmp_path,
            bound=original,
            lane_id=market.slot.lane_id,
            now=market.observed_unix,
            ranking_bound=replace(ranked, ranking_snapshot_id="other"),
        )
    with pytest.raises(ValueError, match="RANKING_ASSIGNMENT_CHANGED"):
        InstrumentCardStreamV1(**args, ranking_bound=replace(ranked, ranking_snapshot_id="other"))
    with pytest.raises(ValueError, match="RANKING_ASSIGNMENT_MISMATCH"):
        InstrumentCardStreamV1(**args, ranking_bound=replace(ranked, instrument_id="wrong"))


def test_shadow_runtime_projects_real_full_inputs_to_actual_core_with_own_budget(
    run_two_hour_shadow,
    monkeypatch,
):
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1 import (
        session_runtime_v1 as shadow_runtime,
    )
    from trading.master_v2 import capital_risk_sizing_offline_replay_binding_adapter_v0 as sizing

    first = _market(slot=SOPH)
    captures = []
    consumed_assignments = []
    consumed_capital = []
    original_cycle = shadow_runtime.run_hardened_wallclock_bridge_observation_cycle_v2
    original_sizing = sizing.bind_capital_risk_sizing_offline_replay_evidence_v0

    def observe_capital(evidence, *, capital_context=None):
        consumed_capital.append(capital_context)
        return original_sizing(evidence, capital_context=capital_context)

    monkeypatch.setattr(
        sizing, "bind_capital_risk_sizing_offline_replay_evidence_v0", observe_capital
    )

    def observe_consumer(**kwargs):
        state = kwargs["bridge_state"]
        market = kwargs["instrument_card_market"]
        consumed_assignments.append(
            (market.slot.lane_id, state.instrument_id, state.venue_instrument_id)
        )
        return original_cycle(**kwargs)

    monkeypatch.setattr(
        shadow_runtime, "run_hardened_wallclock_bridge_observation_cycle_v2", observe_consumer
    )

    def source(*, slot, capture_id, clock):
        assert slot == SOPH
        step = round((clock() - first.observed_unix) / 2)
        market = _market(step, slot=slot, funding_cut=(int(clock()) // 3600 + 1) * 3600)
        captures.append(market)
        return market

    root, result, _ = run_two_hour_shadow(
        flat=False, instrument=SOPH_I17, card_source=source, start_wall=first.observed_unix + 0.01
    )
    assert result.terminal_verdict == "PASS", result.to_dict()
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (
        verify_wallclock_evidence_bundle_v1,
    )

    verified = verify_wallclock_evidence_bundle_v1(
        evidence_root=root, select_first_typed_shadow_decision=True
    )
    assert verified.typed_ddo_requirement_met, verified.to_dict()
    assert verified.selected_shadow_decision["lane_id"] == "LANE_5"
    cycles = [
        json.loads(line) for line in (root / "bridge_cycle_ledger.jsonl").read_text().splitlines()
    ]
    marks = [
        json.loads(line) for line in (root / "market_data_sequence.jsonl").read_text().splitlines()
    ]
    for cycle, mark in zip(cycles, marks, strict=True):
        assert cycle["price_basis"]["price_field"] == mark["mark_price_field"] == "markPx"
        assert cycle["price_basis"]["mid_price"] == mark["mark_px"]
        assert cycle["price_basis"]["best_bid"] == mark["price_basis_quote"]["bid_px"]
        assert cycle["price_basis"]["best_ask"] == mark["price_basis_quote"]["ask_px"]
        assert cycle["price_basis"]["bid_ask_policy"] == "EXPLICIT_BID_ASK_FROM_PUBLIC_BOOK"
    cards = (
        root.parent / "instrument-card-stream" / root.parent.name / "instrument-cards" / "LANE_5"
    )
    # The runtime places projections beside, not into, the sealed source archive.
    if not cards.exists():
        (cards,) = root.parent.glob("instrument-card-stream/*/instrument-cards/LANE_5")
    versions = [
        json.loads(p.read_bytes())["body"] for p in (cards / "versions").glob("*/decision.json")
    ]
    evaluated = [row for row in versions if row["master_v2"] is not None]
    assert len(evaluated) > 1
    assert len(captures) > 1
    assert len(consumed_assignments) > 1
    assert len(consumed_capital) == len(cycles)
    assert all(context is not None for context in consumed_capital)
    for context, cycle in zip(consumed_capital, cycles, strict=True):
        assert context.reference_price == D(str(cycle["price_basis"]["mid_price"]))
        assert context.instrument.lot_size == context.instrument.minimum_quantity == 1
        assert context.instrument.contract_multiplier == 10
        assert context.total_capital_limit == 25
        assert context.capital_risk_mode == "OFFLINE_ALGEBRA"
        assert "CAPITAL_RISK_CONTEXT_UNRESOLVED" not in cycle["reason_codes"]
        assert cycle["soph_shadow_capital_binding"]["authority"] == "NONE"
    assert set(consumed_assignments) == {(SOPH.lane_id, SOPH.instrument_id, SOPH.native_id)}
    for row in evaluated:
        assert (
            row["lane_id"],
            row["instrument_id"],
            row["venue_native_id"],
        ) in consumed_assignments
        assert row["binding"]["instrument_id"] == SOPH.instrument_id
        assert row["binding"]["venue_native_id"] == SOPH.native_id
        assert row["budget"]["lane_id"] == SOPH.lane_id
        assert row["budget"]["instrument_id"] == SOPH.instrument_id
        assert row["ranking_binding"] is None
        assert row["assignment_status"] == "EXPLICIT_ISOLATED_TEST_BINDING"
        inp = row["master_v2"]["prepared_input"]
        assert inp["instrument_id"] == SOPH.instrument_id
        boundary = inp["current_instrument_capital_risk_sizing_boundary_state_file"]
        marked = row["budget"]["original_snapshot"]["marked_portfolio"]["economic_metrics"]
        assert D(boundary["account_equity"]) == D(marked["equity"])
        assert D(boundary["total_capital_limit"]) == 25
        assert D(boundary["scope_capital_limit"]) <= 25
        assert D(boundary["lot_size"]) == 1
        assert D(boundary["instrument_quantity_constraints"]["contract_multiplier"]) == 10
        assert boundary["raw_payload"]["budget_source_digest"] == row["budget"]["source_digest"]
        assert (
            inp["productive_offline_simulated_portfolio_position_observation_v1"]["instrument_id"]
            == SOPH.instrument_id
        )
        ctx = inp["canonical_market_context"]
        assert ctx["market_type"] == "futures" and ctx["bar_interval"] == "1m"
        assert ctx["mark_price"] == row["market"]["mark_price"]
        assert ctx["index_price"] == row["market"]["index_price"]
        assert ctx["volume"] == row["market"]["volume_contracts_24h"]
        assert ctx["open_interest"] == row["market"]["open_interest_contracts"]
        assert ctx["funding_rate"] == row["market"]["funding_rate"]
        assert D(row["budget"]["available_amount"]) <= 25
        assert ctx["canonical_volatility_estimate"] is not None
        assert row["master_v2"]["decision"] is not None
    prepared = {
        row["master_v2"]["decision"]["cycle_id"]: row["master_v2"]["prepared_input"]
        for row in evaluated
    }
    # The first observed long is a natural C3 decision in this ascending fixture.
    entry_idx = next(i for i, c in enumerate(cycles) if c["fill"])
    entry = cycles[entry_idx]
    assert entry["decision_outcome"] == "enter_long" and not entry["forced_wiring"]
    assert all(
        prepared[c["cycle_id"]]["runtime_scope_state"] is None for c in cycles[: entry_idx + 1]
    )
    anchor = float(entry["fill"]["fill_price"])
    for c in cycles[entry_idx + 1 :]:
        inp = prepared[c["cycle_id"]]
        assert c["instrument_card_geometry"]["position_anchor_before"] == anchor
        assert inp["runtime_scope_state"]["anchor_price"] == max(
            anchor, c["price_basis"]["mid_price"]
        )
        assert inp["runtime_scope_bound_instrument_id"] == SOPH.instrument_id
        assert c["instrument_card_entry_review"] is None
        anchor = max(anchor, c["price_basis"]["mid_price"])
        if c["fill"]:
            break
    assert json.loads((root / "full_economic_reconstruction_verifier.json").read_bytes())["ok"]
    assert json.loads((cards / "latest.json").read_bytes())["body"]["status"] == "BLOCKED"


@pytest.mark.parametrize("slot", [ZKP_PAPER_SLOT, UP_PAPER_SLOT, IRYS_PAPER_SLOT])
@pytest.mark.parametrize(
    "carry_ranking", [False, True], ids=["consumer-binding", "existing-ranking"]
)
def test_interrupted_paper_driver_resumes_cards_with_original_opening_and_cursor(
    tmp_path, monkeypatch, slot, carry_ranking
):
    root = tmp_path.resolve() / "original-session"
    initial = _market(slot=slot, depth=1000)
    latest = initial
    elapsed, index = 0, 0
    interrupted = False
    assignment = (
        replace(
            bound(initial),
            selection_id="original-cap23-fixture",
            ranking_snapshot_id="original-ranking-fixture",
            ranking_integrity_digest="2" * 64,
            universe_snapshot_id="original-universe-fixture",
        )
        if carry_ranking
        else None
    )
    consumer_calls = []

    def observe_consumer(original, stage):
        def step(consumer, market, **kwargs):
            row = json.loads(
                (root / "instrument-cards" / slot.lane_id / "latest.json").read_bytes()
            )["body"]
            assert row["binding"] == consumer.bound.to_dict()
            assert (row["lane_id"], row["instrument_id"], row["venue_native_id"]) == (
                consumer.slot.lane_id,
                consumer.bound.instrument_id,
                consumer.bound.venue_native_id,
            )
            assert row["ranking_binding"] == (None if assignment is None else assignment.to_dict())
            consumer_calls.append((stage, consumer.bound.to_dict()))
            return original(consumer, market, **kwargs)

        return step

    for owner, stage in (
        (paper_cli.ZkpPaperEntryV1, "opening"),
        (paper_cli.ZkpPaperContinuationV1, "occupied"),
    ):
        monkeypatch.setattr(owner, "step_v1", observe_consumer(owner.step_v1, stage))

    def capture(policy, *, label, output):
        nonlocal latest, index
        index += 1
        latest = _market(index, slot=slot, depth=1000)
        return latest

    def pause(seconds):
        nonlocal elapsed, interrupted
        elapsed += seconds
        if (root / "opening-fill.json").exists() and not interrupted:
            interrupted = True
            raise OSError("SIMULATED_PROCESS_INTERRUPTION")

    monkeypatch.setattr(paper_cli, "monotonic", lambda: elapsed)
    monkeypatch.setattr(paper_cli, "time", lambda: latest.observed_unix + 0.01)
    monkeypatch.setattr(paper_cli, "sleep", pause)
    with pytest.raises(OSError, match="SIMULATED_PROCESS_INTERRUPTION"):
        paper_cli._run(
            root,
            initial,
            policy=initial.policy,
            duration=60,
            started_at=initial.observed_unix,
            deadline=60,
            revision="f" * 40,
            capture=capture,
            card_assignment=assignment,
        )
    original = (root / "opening-fill.json").read_bytes()
    cursor = (
        root
        / "flat-entry-mark-v2"
        / slot.lane_id
        / "current_productive_sidestate_confirmation_cursor_v1.json"
    )
    assert cursor.exists() and not (root / "closeout.json").exists()
    cards = root / "instrument-cards" / slot.lane_id
    versions = set((cards / "versions").iterdir())
    if assignment is not None:
        preserved = {p: p.read_bytes() for p in (cursor, cards / "latest.json")}
        calls_before = list(consumer_calls)
        with pytest.raises(ValueError, match="PAPER_ORIGINAL_CARD_ASSIGNMENT_CHANGED"):
            paper_cli._resume(
                root,
                policy=initial.policy,
                revision="f" * 40,
                capture=capture,
                slot=slot,
                card_assignment=replace(assignment, ranking_snapshot_id="foreign-generation"),
            )
        assert {p: p.read_bytes() for p in preserved} == preserved
        assert consumer_calls == calls_before
    paper_cli._resume(root, policy=initial.policy, revision="f" * 40, capture=capture, slot=slot)
    assert (root / "opening-fill.json").read_bytes() == original
    assert len(set((cards / "versions").iterdir()) - versions) > 0
    assert json.loads((cards / "latest.json").read_bytes())["body"]["status"] == "BLOCKED"
    assert {stage for stage, _ in consumer_calls} == {"opening", "occupied"}
    original_binding = json.loads((root / "paper-profile.json").read_bytes())["instrument_binding"]
    assert all(binding == original_binding for _, binding in consumer_calls)
    assert not (root / "instrument-cards" / "LANE_3").exists()
    if assignment is not None:
        assert json.loads((root / "card-assignment.json").read_bytes()) == assignment.to_dict()
    for decision in (cards / "versions").glob("*/decision.json"):
        row = json.loads(decision.read_bytes())["body"]
        assert row["binding"] == original_binding
        assert row["ranking_binding"] == (None if assignment is None else assignment.to_dict())
        if row["master_v2"] is not None:
            assert row["master_v2"]["prepared_input"]["instrument_id"] == slot.instrument_id


@pytest.mark.parametrize("legacy", [False, True])
def test_irys_starter_reads_both_explicit_slot_config_formats(tmp_path, legacy):
    original = dict(
        lane=IRYS_PAPER_SLOT.lane_id,
        canonical_instrument_id=IRYS_PAPER_SLOT.instrument_id,
        native_instrument_id=IRYS_PAPER_SLOT.native_id,
        authority="NONE",
    )
    original.update({"environment": "PAPER"} if legacy else {"surface": "PAPER_EXCHANGE"})
    path = tmp_path / "slot-config.json"
    path.write_text(json.dumps(original))
    before = path.read_bytes()
    assert paper_cli._read_paper_slot(path) == IRYS_PAPER_SLOT
    assert path.read_bytes() == before
    original["environment"] = "LIVE"
    path.write_text(json.dumps(original))
    with pytest.raises(ValueError, match="ENVIRONMENT_MISMATCH"):
        paper_cli._read_paper_slot(path)


def test_card_observer_cannot_mutate_original_governed_input():
    from dataclasses import dataclass
    from types import MappingProxyType
    from src.ops.instrument_card_input_observation_v1 import (
        observe_instrument_card_input_v1,
        record_instrument_card_input_v1,
    )

    @dataclass(frozen=True)
    class Input:
        seam: object

    original = Input(MappingProxyType({"parameters": {"value": 7}}))

    def mutate(snapshot):
        snapshot.seam["parameters"]["value"] = 999

    with observe_instrument_card_input_v1(mutate):
        record_instrument_card_input_v1(original)
    assert original.seam["parameters"]["value"] == 7


@pytest.mark.parametrize(
    "action", ["native", "off_grid", "over_budget", "expired_before_fill", "cost_envelope", "close"]
)
def test_shadow_exact_quantity_guard_uses_native_units_and_preserves_close_owner(tmp_path, action):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
        prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
    )
    from trading.master_v2.canonical_volatility_productive_runtime_cmc_typed_binding_v1 import (
        CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1,
    )
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
        run_hardened_bridge_cycle_v2,
    )

    market = _market(
        slot=SOPH, depth=1000, **({"price": D("0.02498")} if action == "cost_envelope" else {})
    )
    state = HardenedBridgeSessionStateV2(
        instrument_id=market.slot.instrument_id, venue_instrument_id=market.slot.native_id
    )
    source = shadow_budget_source_v1(state, repo=REPO)
    budget = source(market=market, now=market.observed_unix)
    g17 = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
        evidence_store_root=tmp_path,
        bound_instrument=bound(market),
        mark_candles_payload=market.g17_payload,
        receive_or_capture_timestamp=market.g17_acquired_at,
    )
    assert g17.estimate_present
    state.typed_volatility_cmc_binding_host = (
        CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1(producer=g17.producer)
    )
    base = market.native_contract.contract_size
    quantity = (
        base / 2 if action == "off_grid" else base * 1000 if action == "over_budget" else base
    )
    if action == "cost_envelope":
        quantity = D(1000)
    side = "BUY"
    if action == "close":
        state.portfolio.apply_intended_action(
            instrument_id=state.instrument_id,
            side="BUY",
            quantity=base,
            mark_price=market.mark,
            intent_id="seed",
            fill_id="seed-fill",
        )
        budget = source(market=market, now=market.observed_unix)
        assert budget["available_for_new_entry"] == "0"
        quantity, side = base, "SELL"
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=float(market.mark),
        event_ts_unix=market.observed_unix,
        session_id="explicit-forced-wiring-fixture",
        instrument_card_market=market,
        instrument_card_budget=budget,
        instrument_card_execution_clock=lambda: (
            market.observed_unix + (6 if action == "expired_before_fill" else 0)
        ),
        forced_actionable={"intended_side": side, "intended_quantity": str(quantity)},
    )
    if action in {"off_grid", "over_budget", "expired_before_fill", "cost_envelope"}:
        assert cycle["fill"] is None
        assert not cycle["instrument_card_execution_check"]["measurement_admitted"]
        if action == "cost_envelope":
            assert cycle["instrument_card_execution_check"]["reason_codes"] == [
                "SOPH_SHADOW_MODEL_COST_ENVELOPE_EXCEEDED"
            ]
    else:
        assert cycle["fill"]["side"] == side
        if action == "native":
            assert D(cycle["instrument_card_execution_check"]["quantity_contracts"]) == 1
        else:
            assert cycle["instrument_card_execution_check"] is None


def test_five_slot_card_review_isolates_missing_wrong_and_unaffordable(tmp_path):
    from src.ops.master_v2_card_precheck_v1 import review_entry_cards_v1

    cards = {"LANE_3": None}
    for slot in (ZKP_PAPER_SLOT, UP_PAPER_SLOT, IRYS_PAPER_SLOT, SOPH):
        market = _market(slot=slot)
        source = stream(tmp_path, market, ["0"] if slot == ZKP_PAPER_SLOT else ["25"])
        source.update_v1(market, now=market.observed_unix)
        cards[slot.lane_id] = source.entry_card_v1()
    cards["LANE_2"] = replace(cards["LANE_2"], bound=cards["LANE_5"].bound)
    results = review_entry_cards_v1(cards, now=market.observed_unix)
    assert not any(side["eligible"] for side in results["LANE_1"]["sides"].values())
    assert not results["LANE_2"]["sides"] and not results["LANE_3"]["sides"]
    for lane in ("LANE_4", "LANE_5"):
        assert all(side["eligible"] for side in results[lane]["sides"].values())
        assert results[lane]["binding"] == cards[lane].bound.to_dict()


@pytest.mark.parametrize(
    ("side", "marks", "expected"),
    [
        ("long", [103, 102, 104], [103, 103, 104]),
        ("short", [97, 98, 96], [97, 97, 96]),
        ("neutral", [103, 97, 104], [100, 100, 100]),
    ],
)
def test_scope_anchor_follows_position_side(side, marks, expected):
    from trading.market_state.time_sample_epoch_semantics_v1 import InstrumentObservationKeyV1
    from trading.master_v2.analytical_card_scope_v1 import AnalyticalCardGeometryV1
    from trading.master_v2.double_play_state import ActiveSide, RuntimeScopeState

    scope = RuntimeScopeState(anchor_price=100)
    geometry = AnalyticalCardGeometryV1(
        InstrumentObservationKeyV1("OKX", SOPH.instrument_id, SOPH.native_id),
        ActiveSide[side.upper()],
        0.5,
        "test",
    )
    for mark, anchor in zip(marks, expected, strict=True):
        scope = geometry.advance(scope, mark)
        assert (
            scope.anchor_price,
            scope.current_downscope_boundary,
            scope.current_upscope_boundary,
        ) == (anchor, anchor - 0.5, anchor + 0.5)


def test_duplicate_mark_preserves_cursor_and_blocked_side_cannot_confirm(tmp_path):
    from types import SimpleNamespace
    from src.ops.master_v2_card_precheck_v1 import CardEntryDeferredV1
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
        _prepare_card_observation,
    )
    from trading.market_state.distinct_market_observation_acceptor_v1 import (
        commit_observation_acceptance_v1,
    )

    state = HardenedBridgeSessionStateV2(
        instrument_id=SOPH.instrument_id, venue_instrument_id=SOPH.native_id
    )
    first = _market(slot=SOPH)
    card = stream(tmp_path, first)

    def prepare(market, *, amount="25"):
        budget = budget_source([amount])(market=market, now=market.observed_unix)
        basis = SimpleNamespace(
            event_ts_unix=market.market_event_unix,
            receive_ts_unix=market.observed_unix,
            mid_price=float(market.mark),
        )
        return _prepare_card_observation(
            state,
            market=market,
            budget=budget,
            bound=card.bound,
            observation=SimpleNamespace(venue_flat=True),
            price_basis=basis,
            now=market.observed_unix,
        )

    _, accepted, _ = prepare(first)
    before = commit_observation_acceptance_v1(current_state=accepted.state_before, result=accepted)
    state.card_observations = before
    with pytest.raises(CardEntryDeferredV1) as duplicate:
        prepare(first)
    assert "duplicate" in duplicate.value.args[0]["reasons"][0]
    assert state.card_observations is before
    assert state.cycle_index == 0 and state.card_position_scope is None
    with pytest.raises(CardEntryDeferredV1) as blocked:
        prepare(_market(1, slot=SOPH), amount="0")
    assert not any(r["eligible"] for r in blocked.value.args[0]["sides"].values())
    assert state.card_confirmation is None and state.card_position_scope is None
    assert state.card_observations.market_observation_epoch != before.market_observation_epoch


@pytest.mark.parametrize("side,close,delta", [("BUY", "SELL", "0.001"), ("SELL", "BUY", "-0.001")])
def test_soph_model_marks_linear_collateral_on_both_sides(side, close, delta):
    from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
        PortfolioEconomicsModelParamsV1,
        SimulatedPortfolioEconomicsModelV1,
    )

    model = SimulatedPortfolioEconomicsModelV1(
        PortfolioEconomicsModelParamsV1(initial_equity=D("25"), linear_futures_collateral=True)
    )
    mark, qty = D("0.024"), D("1000")
    first = model.apply_intended_action(
        instrument_id=SOPH.instrument_id, side=side, quantity=qty, mark_price=mark
    )
    assert model.state.cash == D(25) - first.fee
    assert model.state.equity == D(25) - first.fee - first.slippage_cost
    last = model.apply_intended_action(
        instrument_id=SOPH.instrument_id, side=close, quantity=qty, mark_price=mark + D(delta)
    )
    assert model.state.unrealized_pnl == 0
    assert (
        model.state.equity
        == model.state.cash
        == D(25)
        + abs(D(delta)) * qty
        - first.slippage_cost
        - last.slippage_cost
        - first.fee
        - last.fee
    )


def test_card_geometry_rejects_foreign_native_and_divergent_measured_distance():
    from types import SimpleNamespace as NS
    from trading.market_state.time_sample_epoch_semantics_v1 import InstrumentObservationKeyV1
    from trading.master_v2.analytical_card_scope_v1 import AnalyticalCardGeometryV1
    from trading.master_v2.double_play_state import ActiveSide

    key = InstrumentObservationKeyV1("OKX", SOPH.instrument_id, SOPH.native_id)
    foreign = replace(key, venue_instrument_id="other-native-id")
    identity = NS(instrument_key=lambda: foreign, mark_price=1.0)
    context = NS(instrument_id=SOPH.instrument_id, mark_price=1.0)
    with pytest.raises(ValueError, match="CARD_GEOMETRY_INSTRUMENT_MISMATCH"):
        AnalyticalCardGeometryV1.from_context(
            key=key, context=context, position=None, acceptance=NS(observation_identity=identity)
        )
    geometry = AnalyticalCardGeometryV1(key, ActiveSide.NEUTRAL, 0.2, "fixture")
    inter = NS(
        market_context=context,
        scope_event=NS(instrument_id=SOPH.instrument_id, semantic_binding=NS(current_price=1.0)),
        effective_scope_magnitude=0.1,
    )
    with pytest.raises(ValueError, match="CARD_GEOMETRY_CONSUMPTION_MISMATCH"):
        geometry.verify_consumption(inter, mark=1.0, carried=None)
