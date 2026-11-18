"""Offline contracts for the exact public-data-to-Paper opening route."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path
import socket
from urllib.parse import urlencode

import pytest

from scripts.ops import run_zkp_lane1_paper_v1 as paper_cli
from scripts.ops.run_zkp_lane1_paper_v1 import preflight_zkp_paper_v1
from src.ops.bounded_peaktrade_system_composition_v1 import (
    zkp_paper_continuation_v1 as continuation,
)
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_entry_v1 import ZkpPaperEntryV1
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
    FAMILY,
    INDEX_ID,
    NATIVE_ID,
    PAPER_FEE_RATE,
    bind_zkp_paper_market_v1,
    load_paper_liquidity_policy_v1,
    zkp_public_queries_v1,
)
from src.ops.exit_policy_producer_binding_v1.current_cursor_recovery_v1 import (
    require_current_cursor_continuity_v1,
)
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    IDENTITY_FILENAME,
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    recover_position_episode_from_simulated_accounting_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
    restore_layered_core_episode_v1,
)

REPO = Path(__file__).resolve().parents[2]
C1 = 1_700_000_040
DAY = 86400


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def deny(*args, **kwargs):
        pytest.fail("ZKP opening contract fixtures must remain offline")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)


def _observations(
    step=0, *, direction=1, price=None, depth=100, funding_cut=C1 + 1200, settled_rate=None
):
    policy = load_paper_liquidity_policy_v1(REPO)
    now = C1 + 62 + step * 2 + 0.2
    event = str(int((now - 0.2) * 1000))
    acquired = datetime.fromtimestamp(now - 0.1, timezone.utc).isoformat()
    mark = price if price is not None else Decimal("0.0335") + step * direction * Decimal("0.00030")
    tick = Decimal("0.00001")
    inst = {
        "instId": NATIVE_ID,
        "instType": "FUTURES",
        "instFamily": FAMILY,
        "uly": INDEX_ID,
        "ctType": "linear",
        "ctValCcy": "ZKP",
        "ctVal": "10",
        "ctMult": "1",
        "settleCcy": "USD",
        "state": "live",
        "lotSz": "1",
        "minSz": "1",
        "tickSz": str(tick),
        "maxMktSz": "400000",
    }
    minute = (int(now) - C1 - 60) // 60
    closes = [
        str(Decimal("0.0335") * (1 + direction * Decimal("0.002") * (i - 99 + minute)))
        for i in range(100)
    ]
    trade = [
        [str((C1 + (i - 99 + minute) * 60) * 1000), *([price] * 4), "5", "50", "1.6", "1"]
        for i, price in enumerate(closes)
    ]
    mark_history = [row[:5] + ["1"] for row in trade[-61:]]
    previous_funding = funding_cut if now >= funding_cut else funding_cut - 3600
    upcoming_funding = previous_funding + 3600
    midnight = int(now) // DAY * DAY
    daily = [
        [
            str((midnight - day * DAY) * 1000),
            "0.033",
            "0.034",
            "0.032",
            "0.033",
            "10000",
            "100000",
            "3300",
            "1",
        ]
        for day in range(1, policy.adv_days + 1)
    ]
    rows = {
        "instrument": [inst],
        "tiers": [
            {
                "tier": "1",
                "instFamily": FAMILY,
                "imr": "0.05",
                "mmr": "0.02",
                "maxLever": "20",
                "maxSz": "100000",
            }
        ],
        "adv": daily,
        "funding": [
            {
                "instId": NATIVE_ID,
                "instType": "FUTURES",
                "method": "current_period",
                "minFundingRate": "-0.003",
                "maxFundingRate": "0.003",
                "fundingRate": "0.0001",
                "prevFundingTime": str(previous_funding * 1000),
                "fundingTime": str(upcoming_funding * 1000),
                "nextFundingTime": str((upcoming_funding + 3600) * 1000),
                "ts": event,
            }
        ],
        "funding-history": [
            {
                "instId": NATIVE_ID,
                "instType": "FUTURES",
                "fundingTime": str(funding_cut * 1000),
                "fundingRate": "0.0001",
                "realizedRate": settled_rate,
            }
        ]
        if settled_rate is not None
        else [],
        "trade-candles": trade,
        "mark-candles": mark_history,
        "open-interest": [{"instId": NATIVE_ID, "ts": event, "oi": "2000", "oiCcy": "20000"}],
        "ticker": [{"instId": NATIVE_ID, "ts": event, "vol24h": "10000", "volCcy24h": "100000"}],
        "usdc-index": [{"instId": "USDC-USD", "ts": event, "idxPx": "1"}],
        "index": [{"instId": INDEX_ID, "ts": event, "idxPx": str(mark)}],
        "book": [
            {
                "ts": event,
                "bids": [[str(mark - tick), "5"]]
                + ([[str(mark - 2 * tick), str(depth)]] if depth else []),
                "asks": [[str(mark + tick), "5"]]
                + ([[str(mark + 2 * tick), str(depth)]] if depth else []),
            }
        ],
        "mark": [{"instId": NATIVE_ID, "ts": event, "markPx": str(mark)}],
    }
    receipts = {}
    for name, (path, query) in zkp_public_queries_v1(policy.adv_days).items():
        payload = {"code": "0", "data": rows[name]}
        receipts[name] = FreshPretradeGetTransportResultV1(
            get_performed=True,
            method="GET",
            endpoint=f"{path}?{urlencode(query)}",
            http_status=200,
            payload=payload,
            auth_header_sent=False,
            transport_class="FIXTURE",
            venue_live_contact=True,
            historical_reuse=False,
            error_class="",
            body_sha256=sha256(json.dumps(payload).encode()).hexdigest(),
            acquired_at_utc=acquired,
        )
    return receipts, policy, now


def _market(step=0, **kwargs):
    receipts, policy, observed = _observations(step, **kwargs)
    return bind_zkp_paper_market_v1(receipts, policy=policy, observed_unix=observed)


def _against_position(cursor_root, direction):
    scope = restore_layered_core_episode_v1(cursor_root)
    move = max(3 * scope.scope.d_t, 0.00003)
    return Decimal(str(round(scope.running_reference.reference_price_r_t - direction * move, 5)))


@pytest.mark.parametrize("fault", ["gap", "units", "book-age", "wrong-query"])
def test_paper_inputs_reject_incompatible_evidence(fault):
    receipts, policy, observed = _observations()
    if fault == "gap":
        receipts["adv"].payload["data"].pop(3)
    elif fault == "units":
        receipts["adv"].payload["data"][0][6] = "1"
    elif fault == "book-age":
        receipts["book"].payload["data"][0]["ts"] = str((C1 - 1) * 1000)
    else:
        book = receipts["book"]
        receipts["book"] = replace(book, endpoint=book.endpoint.replace(NATIVE_ID, "BTC-USDT-SWAP"))
    with pytest.raises(ValueError, match="ZKP_PAPER_"):
        bind_zkp_paper_market_v1(receipts, policy=policy, observed_unix=observed)


@pytest.mark.parametrize("direction", [1, -1])
def test_original_double_play_entry_books_one_liquid_paper_fill(tmp_path, direction):
    first = _market(direction=direction)
    preflight = preflight_zkp_paper_v1(market=first)
    assert preflight["session_started"] is False
    assert preflight["current_book_admitted_on_both_sides"]
    root = tmp_path.resolve() / "paper-unit"
    session = ZkpPaperEntryV1(
        root=root,
        repo=REPO,
        revision="f" * 40,
        initial_market=first,
        duration=7200,
    )
    for step in range(7):
        market = _market(step, direction=direction)
        result = session.step_v1(market, clock=lambda: market.observed_unix + 0.01)
        if result["status"] == "FIRST_FILL_BOOKED":
            break
    assert result["status"] == "FIRST_FILL_BOOKED", result
    fill = result["fill"]
    assert fill["side"] == ("BUY" if direction == 1 else "SELL")
    assert Decimal(fill["fee"]) == Decimal(fill["notional"]) * PAPER_FEE_RATE
    assert Decimal(fill["quantity"]) > 5
    opening = json.loads((root / "opening-plan.json").read_bytes())
    assert opening["liquidity"]["risk_admitted"] is True
    assert opening["intent"]["submission_authorized"] is False
    assert fill["fill_price"] == opening["liquidity"]["open_price_usd"]
    assert result["accounting"]["fill_count"] == 1
    assert result["orders_sent"] == result["permits_created"] == 0
    (source,) = tuple((root / "episode-sources").glob("*.json"))
    episode_root = root / "episodes" / result["episode_id"]
    raw_identity = json.loads((episode_root / IDENTITY_FILENAME).read_bytes())["identity"]
    raw_identity["account_scope"] = PositionEpisodeScopeV1(**raw_identity["account_scope"])
    episode = recover_position_episode_from_simulated_accounting_v1(
        identity=PositionEpisodeIdentityV1(**raw_identity),
        source_path=source,
        state_root=episode_root,
        repository_sha=session.revision,
        config_digest=session.episode_config_digest,
        writer_session_id=root.name,
    )
    cursor = load_current_productive_sidestate_confirmation_cursor_v1(session.cursor_root)
    require_current_cursor_continuity_v1(
        episode=episode, incoming=cursor, store_root=session.cursor_root
    )
    assert result["c1_publication"]["c1_open_unix"] == C1
    saved = (root / "opening-fill.json").read_bytes()
    with pytest.raises(ValueError, match="OPENING_ALREADY_RETAINED"):
        session.step_v1(market, clock=lambda: market.observed_unix)
    assert (root / "opening-fill.json").read_bytes() == saved


def test_double_play_enter_cannot_book_when_exact_quantity_exceeds_depth(tmp_path):
    market = _market()
    root = tmp_path.resolve() / "paper-thin"
    session = ZkpPaperEntryV1(
        root=root, repo=REPO, revision="f" * 40, initial_market=market, duration=7200
    )
    reached = False
    for step in range(7):
        market = _market(step)
        thin = replace(market.book, bids=market.book.bids[:1], asks=market.book.asks[:1])
        market = replace(market, book=thin)
        result = session.step_v1(market, clock=lambda: market.observed_unix + 0.01)
        if "liquidity" in result:
            reached = True
            assert "ZKP_PAPER_EXECUTABLE_DEPTH_INSUFFICIENT" in result["reason_codes"]
            break
    assert reached, result
    assert session.accounting.portfolio_state().fill_count == 0
    assert not (root / "opening-plan.json").exists()
    assert not (root / "episodes").exists()


def test_liquidity_rejects_adverse_book_impact_and_volume_participation():
    market = _market()
    asks = (market.book.asks[0], (market.mark + Decimal("0.00050"), Decimal(100)))
    market = replace(market, book=replace(market.book, asks=asks), adv_usd=Decimal("10"))
    result = market.assess_quantity_v1(side="BUY", quantity=Decimal(50))
    assert result["risk_admitted"] is False
    assert result["reason_codes"] == [
        "ZKP_PAPER_SLIPPAGE_LIMIT",
        "ZKP_PAPER_ADV_PARTICIPATION_LIMIT",
    ]


def test_operator_preflight_stays_outside_paper_state(tmp_path, monkeypatch, capsys):
    root = tmp_path.resolve() / "input-evidence"
    monkeypatch.setattr(paper_cli, "_capture", lambda *args, **kwargs: _market())

    def reject_run(*args, **kwargs):
        pytest.fail("the preflight entrypoint attempted to open a session")

    monkeypatch.setattr(paper_cli, "_run", reject_run)
    assert paper_cli.main(["preflight", "--evidence-root", str(root)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["session_started"] is False
    assert set(path.name for path in root.iterdir()) == {"preflight.json"}


@pytest.mark.parametrize("direction", [1, -1])
def test_occupied_paper_books_one_net_fill_and_cold_resumes(tmp_path, direction):
    root = tmp_path.resolve() / "paper-net"
    args = dict(root=root, repo=REPO, revision="f" * 40)
    opened = ZkpPaperEntryV1(**args, initial_market=_market(direction=direction), duration=7200)
    for i in range(7):
        market = _market(i, direction=direction)
        initial = opened.step_v1(market, clock=lambda: market.observed_unix + 0.01)
        if initial["status"] == "FIRST_FILL_BOOKED":
            break
    assert initial["status"] == "FIRST_FILL_BOOKED"
    session = continuation.ZkpPaperContinuationV1(**args)
    assert session.last_receipt == initial
    held = _market(i + 1, direction=direction)
    hold = session.step_v1(held, clock=lambda: held.observed_unix + 0.01)
    assert hold["status"] == "WAIT", hold
    switch_price = _against_position(session.cursor_root, direction)
    thin = _market(i + 2, direction=direction, price=switch_price, depth=0)
    blocked = session.step_v1(thin, clock=lambda: thin.observed_unix + 0.01)
    assert blocked["status"] == "REVERSAL_BLOCKED", blocked
    assert blocked["reason_codes"] == ["ZKP_PAPER_EXECUTABLE_DEPTH_INSUFFICIENT"]
    assert session.accounting.fill_order == [initial["fill"]["fill_id"]]
    retry = _market(i + 3, direction=direction, price=switch_price, depth=1000)

    def interrupted_writer():
        session = continuation.ZkpPaperContinuationV1(**args)
        retain = continuation.immutable_json_v1

        def exit_after_commit(path, value):
            retain(path, value)
            if path.parent.name == "reversals":
                os._exit(73)

        continuation.immutable_json_v1 = exit_after_commit
        session.step_v1(retry, clock=lambda: retry.observed_unix + 0.01)

    process = multiprocessing.get_context("fork").Process(target=interrupted_writer)
    process.start()
    process.join(10)
    if process.is_alive():
        process.kill()
        process.join()
    assert process.exitcode == 73
    (booking_path,) = (root / "reversals").glob("*.json")
    assert sorted(p.name for p in (root / "episodes").iterdir()) == [initial["episode_id"]]
    before_recovery = load_current_productive_sidestate_confirmation_cursor_v1(session.cursor_root)
    booked_bytes = booking_path.read_bytes()
    cold = continuation.ZkpPaperContinuationV1(**args)
    receipt = cold.last_receipt
    assert receipt["status"] == "NET_REVERSAL_BOOKED"
    assert receipt["lane_id"] == "LANE_1" and receipt["fill"]["instrument_id"] == NATIVE_ID
    assert receipt["previous_episode_id"] == initial["episode_id"]
    assert receipt["episode_id"] != initial["episode_id"]
    assert Decimal(receipt["current_contracts"]) * direction > 0
    assert Decimal(receipt["target_contracts"]) * direction < 0
    assert Decimal(receipt["fill"]["quantity"]) == abs(
        Decimal(receipt["target_contracts"]) - Decimal(receipt["current_contracts"])
    )
    assert receipt["accounting"]["fill_count"] == 2
    assert Decimal(receipt["accounting"]["cumulative_fees"]) == (
        Decimal(initial["fill"]["fee"]) + Decimal(receipt["fill"]["fee"])
    )
    assert Decimal(receipt["fill"]["fee"]) == Decimal(receipt["fill"]["notional"]) * PAPER_FEE_RATE
    assert receipt["orders_sent"] == receipt["permits_created"] == 0
    assert (
        load_current_productive_sidestate_confirmation_cursor_v1(cold.cursor_root)
        == before_recovery
    )
    repeated = continuation.ZkpPaperContinuationV1(**args)
    assert repeated.last_receipt == receipt
    assert repeated.step_v1(retry)["status"] == "WAITING_FOR_NEW_MARK"
    assert booking_path.read_bytes() == booked_bytes
    following = _market(i + 4, direction=direction, price=switch_price)
    resumed = repeated.step_v1(following, clock=lambda: following.observed_unix + 0.01)
    assert resumed["status"] == "WAIT", resumed
    assert resumed["episode_id"] == receipt["episode_id"]
    assert resumed["trading_epoch"] == receipt["trading_epoch"] + 1
    assert repeated.accounting.portfolio_state().fill_count == 2
    back = _market(
        i + 5,
        direction=direction,
        price=_against_position(cold.cursor_root, -direction),
        depth=1000,
    )
    second = repeated.step_v1(back, clock=lambda: back.observed_unix + 0.01)
    assert second["status"] == "NET_REVERSAL_BOOKED", second
    assert Decimal(second["target_contracts"]) * direction > 0
    assert second["current_contracts"] == receipt["target_contracts"]
    assert second["previous_episode_id"] == receipt["episode_id"]
    assert second["accounting"]["fill_count"] == 3
    assert continuation.ZkpPaperContinuationV1(**args).last_receipt == second


def test_bounded_driver_continues_after_opening_and_leaves_position_at_end(tmp_path, monkeypatch):
    root = tmp_path.resolve() / "paper-driver"
    elapsed = 0
    index = 0
    initial = _market()
    latest = initial
    lane = root / "flat-entry-mark-v2" / "LANE_1"

    def capture(policy, *, label, output):
        nonlocal index, latest
        index += 1
        price = None
        if (root / "opening-fill.json").is_file():
            price = latest.mark if (root / "reversals").exists() else _against_position(lane, 1)
        latest = _market(index, price=price, depth=1000)
        return latest

    def sleep(seconds):
        nonlocal elapsed
        elapsed += seconds

    monkeypatch.setattr(paper_cli, "monotonic", lambda: elapsed)
    monkeypatch.setattr(paper_cli, "time", lambda: latest.observed_unix + 0.01)
    monkeypatch.setattr(paper_cli, "sleep", sleep)
    result = paper_cli._run(
        root,
        initial,
        policy=initial.policy,
        duration=40,
        started_at=initial.observed_unix,
        deadline=40,
        revision="f" * 40,
        capture=capture,
    )
    assert result["status"] == "WINDOW_ENDED_OCCUPIED", result
    booking = result["last_booking"]
    assert booking["status"] == "NET_REVERSAL_BOOKED", booking
    assert booking["accounting"]["fill_count"] == 2
    assert booking["accounting"]["positions"][0]["side"].lower() == "short"
    assert len(list((root / "reversals").glob("*.json"))) == 1
    before = load_current_productive_sidestate_confirmation_cursor_v1(lane)
    recovered = paper_cli._resume(root, policy=initial.policy, revision="f" * 40, capture=capture)
    assert recovered == result
    assert load_current_productive_sidestate_confirmation_cursor_v1(lane) == before


@pytest.mark.parametrize("direction", [1, -1])
def test_funding_at_settlement_survives_process_loss_and_double_play_continues(tmp_path, direction):
    root = tmp_path.resolve() / "paper-funded"
    args = dict(root=root, repo=REPO, revision="f" * 40)
    cut = C1 + 120

    def market(step, **kwargs):
        return _market(step, direction=direction, funding_cut=cut, **kwargs)

    opened = ZkpPaperEntryV1(**args, initial_market=market(0), duration=7200)
    for i in range(7):
        opening_tick = market(i)
        initial = opened.step_v1(opening_tick, clock=lambda: opening_tick.observed_unix + 0.01)
        if initial["status"] == "FIRST_FILL_BOOKED":
            break
    assert initial["status"] == "FIRST_FILL_BOOKED"
    occupied = continuation.ZkpPaperContinuationV1(**args)
    held = market(28, price=market(i + 1).mark, settled_rate="0.0012")
    waiting = occupied.step_v1(held, clock=lambda: held.observed_unix + 0.01)
    assert waiting["status"] == "WAIT", waiting
    before = load_current_productive_sidestate_confirmation_cursor_v1(occupied.cursor_root)
    before_equity = occupied.accounting.portfolio_state().equity
    # Even a published history row before the cut never creates a debit/credit.
    assert not occupied.accounting.funding_events
    after_cut = market(29, price=held.mark, settled_rate="")
    assert occupied.step_v1(after_cut)["status"] == "FUNDING_WAIT"
    assert not (root / "funding").exists()
    assert load_current_productive_sidestate_confirmation_cursor_v1(occupied.cursor_root) == before

    settlement_tick = market(30, price=held.mark, settled_rate="0.0012")

    def interrupted_writer():
        session = continuation.ZkpPaperContinuationV1(**args)
        retain = continuation.immutable_json_v1

        def exit_after_commit(path, value):
            retain(path, value)
            if path.parent.name == "funding":
                os._exit(74)

        continuation.immutable_json_v1 = exit_after_commit
        session.step_v1(settlement_tick, clock=lambda: settlement_tick.observed_unix + 0.01)

    process = multiprocessing.get_context("fork").Process(target=interrupted_writer)
    process.start()
    process.join(10)
    if process.is_alive():
        process.kill()
        process.join()
    assert process.exitcode == 74
    (funding_path,) = (root / "funding").glob("*.json")
    booked = funding_path.read_bytes()
    cold = continuation.ZkpPaperContinuationV1(**args)
    assert load_current_productive_sidestate_confirmation_cursor_v1(cold.cursor_root) == before
    receipt = cold.last_funding
    original_position = Decimal(initial["fill"]["quantity"])
    boundary_mark = Decimal("0.033567" if direction == 1 else "0.033433")
    expected = -direction * original_position * 10 * boundary_mark * Decimal("0.0012")
    assert receipt["terms"]["event_time_unix"] == cut
    assert receipt["terms"]["observed_unix"] > cut
    assert Decimal(receipt["terms"]["preceding_mark_close_usd"]) == boundary_mark
    assert Decimal(receipt["amount_usd"]) == expected
    assert cold.accounting.portfolio_state().equity == before_equity + expected
    assert list(cold.accounting.funding_events) == [receipt["event_id"]]
    assert cold.accounting.funding_events[receipt["event_id"]]["applied_after_fill_count"] == 1
    assert cold.accounting.portfolio_state().fill_count == 1

    # A second readback plus the same official history advances Core, not funding.
    replay = continuation.ZkpPaperContinuationV1(**args)
    assert replay.last_funding == receipt
    resumed = replay.step_v1(settlement_tick, clock=lambda: settlement_tick.observed_unix + 0.01)
    assert resumed["status"] == "WAIT", resumed
    assert resumed["trading_epoch"] == before["trading_epoch"] + 1
    assert resumed["episode_id"] == initial["episode_id"]
    switch = market(
        31,
        price=_against_position(replay.cursor_root, direction),
        depth=1000,
        settled_rate="0.0012",
    )
    reversal = replay.step_v1(switch, clock=lambda: switch.observed_unix + 0.01)
    assert reversal["status"] == "NET_REVERSAL_BOOKED", reversal
    assert Decimal(reversal["target_contracts"]) * direction < 0
    assert Decimal(reversal["accounting"]["funding_pnl"]) == expected
    restarted = continuation.ZkpPaperContinuationV1(**args)
    assert restarted.last_funding == receipt and restarted.last_receipt == reversal
    assert len(restarted.accounting.funding_events) == 1
    assert list((root / "funding").glob("*.json")) == [funding_path]
    assert funding_path.read_bytes() == booked
