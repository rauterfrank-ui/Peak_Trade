"""Original Slot 3 TESTNET journal in a temporary directory. No network or signer."""

from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
import json

import pytest

from src.ops import btc_demo_testnet_entry_reservation_v1 as draft
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    PORTFOLIO_STATE_FILENAME,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from tests.ops import test_btc_demo_offline_trading_host_v1 as btc
from tests.ops import test_current_usdc_xperp_financial_admission_v1 as financial
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network


@pytest.fixture
def case(tmp_path, monkeypatch, request):
    direction = request.param
    monkeypatch.setattr(financial, "ACCOUNT", btc.budget_fixture.ACCOUNT)
    original = btc.instrument
    monkeypatch.setattr(
        btc,
        "instrument",
        lambda **kw: dict(original(**kw), ctVal="1", lotSz="0.0001", minSz="0.0001"),
    )
    policy = replace(
        financial.policy(),
        allowed_slot_ids=("LANE_3",),
        aggregate_reserved_notional_limit=Decimal(25),
    )
    host, candles, admission, public = btc.setup_host(
        tmp_path, monkeypatch, direction, policy=policy, testnet_v2=True
    )
    try:
        entry, _ = btc.enter(host, candles, admission, direction)
        profile = host.budget.root / "btc-lane3-testnet.json"
        profile.write_text(
            json.dumps(dict(json.loads(profile.read_bytes()), reservation_fixture=draft.SOURCE))
        )
        real_clock = draft.cost.utc_now_iso_v1
        _, args, clock = financial.prepare(
            tmp_path,
            monkeypatch,
            slot="LANE_3",
            host_context=(host.budget, None),
            slot_entry=(host.budget.bound, entry.cycle, dict(public, settleCcy="USDC")),
            fixture_transport=draft.SOURCE,
        )
        inj = args["injected"]
        raw = json.loads(inj.opening_cost_observation.sources_json)
        raw.update(json.loads(inj.native_initial_margin_observation.sources_json))
        raw["funding"] = json.loads(inj.funding_cost_observation.source_json)
        rows = {key: draft.cost.FreshPretradeGetTransportResultV1(**v) for key, v in raw.items()}
        empty = {"code": "0", "data": []}
        for key in ("positions", "pending"):
            rows[key] = replace(
                rows["account"],
                endpoint=draft._ENDPOINTS[key],
                payload=empty,
                body_sha256=draft.cost.digest(empty),
            )
        stamp = datetime.fromisoformat(clock[0]).timestamp()
        persisted = draft.PortfolioTruthSnapshotV1(
            source_id=draft.SOURCE, event_time_unix=stamp, wall_time_unix=stamp, max_age_seconds=5
        )
        folder = host.budget.root / "testnet-state/budget-owner/reconciliation"
        folder.mkdir()
        (folder / PORTFOLIO_STATE_FILENAME).write_text(json.dumps(persisted.to_dict()))
        kwargs = dict(
            entry=entry,
            sources=rows,
            movement_input=financial.raw_input(args),
            expected_revision=host.budget.budget_revision_ref_v1(),
            clock=lambda: clock[0],
        )
        monkeypatch.setattr(draft.cost, "utc_now_iso_v1", real_clock)
        yield host, kwargs
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize("case", [1, -1], indirect=True)
def test_offline_testnet_hold_survives_cold_read(case):
    host, kwargs = case
    budget = host.budget
    rid, checksum = host.reserve_offline_testnet_entry_v1(**kwargs)
    original = budget.owner.local_commitment_readback_v1()
    (hold,) = original.commitments
    assert (
        hold.reservation_id == rid
        and hold.state == "RESERVED"
        and hold.execution_phase == "NO_EXECUTION_LINK"
    )
    assert (
        hold.canonical_quantity == "0.0003"
        and hold.decision_id == kwargs["entry"].cycle.replay.evidence.decision_id
    )
    assert (
        hold.instrument_id == budget.bound.instrument_id
        and hold.venue_native_id == btc.demo._NATIVE
    )
    assert (
        original.active_commitment_sum
        == hold.amount
        + hold.opening_fee_reserve
        + hold.closing_cost_reserve
        + hold.funding_cost_reserve
        <= Decimal(25)
    )
    assert min(hold.opening_fee_reserve, hold.closing_cost_reserve, hold.funding_cost_reserve) > 0
    with pytest.raises(ValueError, match="NO_EXECUTION_AUTHORITY"):
        budget.owner.bind_execution_plan_v1(rid, None)
    with pytest.raises(ValueError, match="FRESH_FIRST_ENTRY"):
        host.reserve_offline_testnet_entry_v1(**kwargs)
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        read_budget_revision_read_only_v1,
    )
    from pathlib import Path

    seq, head = budget.budget_revision_ref_v1()
    row = read_budget_revision_read_only_v1(
        Path(budget.owner.durable_scope_identity_v1()["root"]),
        account_identity=budget.account,
        sequence=seq,
        expected_digest=head,
    )
    saved = row["state"]["sizing_bindings"][rid]
    assert (
        saved["schema"] == "reservation_sizing_binding.v10"
        and saved["offline_testnet_source_digest"] == checksum
    )
    binding = budget.owner.risk_snapshot_v1()["state"]["sizing_bindings"][rid]
    assert binding["offline_testnet_source_digest"] == checksum
    evidence = json.loads(
        (
            budget.root / "testnet-state/LANE_3/entry-reservation-sources" / (checksum + ".json")
        ).read_bytes()
    )
    assert (
        draft.cost.digest(evidence) == checksum and evidence["execution_environment"] == "TESTNET"
    )
    assert evidence["evaluated_at_utc"] == kwargs["clock"]()
    assert evidence["parent_revision"] == list(kwargs["expected_revision"])
    side = kwargs["entry"].cycle.decision_outcome.removeprefix("enter_").upper()
    assert binding["native_initial_margin_binding"]["receipt"]["side"] == side
    mark = Decimal(str(kwargs["entry"].cycle.replay.intermediate.market_context.mark_price))
    sign = 1 if side == "LONG" else -1
    notional = (mark + sign * Decimal("0.1")) * Decimal("0.0001") + (
        mark + sign * Decimal("0.2")
    ) * Decimal("0.0002")
    assert Decimal(binding["entry_cost_binding"]["receipt"]["book_vwap"]) == notional / Decimal(
        hold.canonical_quantity
    )
    assert hold.opening_fee_reserve == notional * Decimal("0.0005")
    root = budget.owner.durable_scope_identity_v1()["root"]
    budget.owner.close()
    reopened = PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=root,
        durable_account_identity=budget.account,
        durable_mode="recover",
        durable_lane_bindings={"LANE_3": budget.bound},
    )
    try:
        assert reopened.local_commitment_readback_v1().commitments == (hold,)
        assert (
            reopened.local_commitment_readback_v1().active_commitment_sum
            == original.active_commitment_sum
        )
        assert reopened.risk_snapshot_v1()["state"]["sizing_bindings"][rid] == binding
    finally:
        reopened.close()


@pytest.mark.parametrize("case", [1], indirect=True)
@pytest.mark.parametrize(
    ("fault", "reason"),
    [
        ("foreign-private", "WRONG_SOURCE:pending"),
        ("balance-account", "WRONG_ACCOUNT"),
        ("missing-funding", "COMPLETE_BATCH"),
        ("cycle", "WRONG_SOURCE:book"),
        ("digest", "WRONG_SOURCE:fees"),
        ("uncovered", "BUDGET_UNCOVERED"),
        ("positions", "COMPLETE_FLAT_INVENTORY"),
        ("pending", "COMPLETE_FLAT_INVENTORY"),
        ("mode", "NET_POSITION_MODE"),
        ("stale", "ACQUISITION_STALE"),
        ("depth", "DEPTH"),
        ("profile", "ISOLATED_FIXTURE"),
        ("reconciliation", "RECON"),
        ("parent", "FRESH_FIRST_ENTRY"),
        ("race", "DURABLE_HEAD_CHANGED"),
        ("writer-clock", "ORIGINAL_JOURNAL_SOURCE_REQUIRED"),
        ("tampered-capture", "ORIGINAL_JOURNAL_SOURCE_REQUIRED"),
        ("settlement", "USDC_SETTLEMENT_SOURCE_REQUIRED"),
    ],
)
def test_invalid_source_or_journal_cannot_create_hold(case, fault, reason, monkeypatch):
    host, kwargs = case
    rows = kwargs["sources"]
    owner = host.budget.owner
    if fault == "foreign-private":
        rows["pending"] = replace(rows["pending"], transport_class=f"{draft.SOURCE}:foreign")
    elif fault == "missing-funding":
        del rows["funding"]
    elif fault == "cycle":
        rows["book"] = replace(rows["book"], pretrade_decision_id="other-cycle")
    elif fault == "digest":
        rows["fees"] = replace(rows["fees"], body_sha256="0" * 64)
    elif fault == "stale":
        initial = kwargs["clock"]()
        later = datetime.fromisoformat(initial) + timedelta(seconds=6)
        ticks = iter([initial, later.isoformat()])
        kwargs["clock"] = lambda: next(ticks)
    elif fault == "profile":
        path = host.budget.root / "btc-lane3-testnet.json"
        original = json.loads(path.read_bytes())
        del original["reservation_fixture"]
        path.write_text(json.dumps(original))
    elif fault == "parent":
        kwargs["expected_revision"] = (0, "0" * 64)
    elif fault == "reconciliation":
        path = (
            host.budget.root
            / "testnet-state/budget-owner/reconciliation"
            / PORTFOLIO_STATE_FILENAME
        )
        path.unlink()
    elif fault == "tampered-capture":
        write_source = draft.immutable_json_v1

        def corrupt_source(path, packet):
            return write_source(path, dict(packet, decision="other-fixture-decision"))

        monkeypatch.setattr(draft, "immutable_json_v1", corrupt_source)
    elif fault == "writer-clock":
        reserve = owner.reserve_fixture_v2

        def wrong_receipt_time(**arguments):
            arguments["offline_testnet_evaluated_at"] = (
                datetime.fromisoformat(kwargs["clock"]()) + timedelta(seconds=1)
            ).isoformat()
            return reserve(**arguments)

        monkeypatch.setattr(owner, "reserve_fixture_v2", wrong_receipt_time)
    elif fault == "race":
        writer = owner.reserve_fixture_v2

        def intervening_writer(**arguments):
            owner.restart_fail_closed_v1()
            return writer(**arguments)

        monkeypatch.setattr(owner, "reserve_fixture_v2", intervening_writer)
    else:
        key = {
            "balance-account": "balance",
            "uncovered": "balance",
            "depth": "book",
            "mode": "account",
            "settlement": "instruments",
        }.get(fault, fault)
        payload = json.loads(draft.cost.canonical(rows[key].payload))
        if fault in ("positions", "pending"):
            payload["data"].append({"instId": btc.demo._NATIVE})
        elif fault == "balance-account":
            payload["data"][0]["uid"] = "foreign"
        elif fault == "uncovered":
            next(row for row in payload["data"][0]["details"] if row["ccy"] == "USDC")[
                "availEq"
            ] = "24.99"
        elif fault == "settlement":
            payload["data"][0]["settleCcy"] = "USD"
        elif fault == "mode":
            payload["data"][0]["posMode"] = "long_short_mode"
        elif fault == "depth":
            payload["data"][0]["asks"] = payload["data"][0]["asks"][:1]
        rows[key] = replace(rows[key], payload=payload, body_sha256=draft.cost.digest(payload))
    with pytest.raises(ValueError, match=reason):
        host.reserve_offline_testnet_entry_v1(**kwargs)
    assert owner.stored_reservation_count_v1() == 0
    assert owner.local_commitment_readback_v1().active_commitment_sum == 0
    assert not owner.risk_snapshot_v1()["state"]["execution_links"]


@pytest.mark.parametrize("case", [1, -1], indirect=True)
def test_fixture_reservation_cannot_be_reconciled_as_a_submit(case):
    host, kwargs = case
    rid, _ = host.reserve_offline_testnet_entry_v1(**kwargs)
    revision = host.budget.budget_revision_ref_v1()
    commitments = host.budget.owner.local_commitment_readback_v1()
    for _ in range(2):
        with pytest.raises(ValueError, match="NO_EXECUTION_AUTHORITY"):
            host.reconcile_confirmed_entry_v1(reads=None, reservation_id=rid, clock=None)
    assert host.budget.budget_revision_ref_v1() == revision
    assert host.budget.owner.local_commitment_readback_v1() == commitments
    assert rid not in host.budget.owner.execution_links_v1()
    lane = btc.demo._demo_lane_root(host.budget.root)
    assert not (lane / "confirmed-first-fills").exists()
    assert not (lane / "position-episodes").exists()
