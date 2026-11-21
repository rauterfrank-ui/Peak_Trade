"""Offline contracts for the exact public-data-to-Paper opening route."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path
import socket
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest

from scripts.ops import run_zkp_lane1_paper_v1 as paper_cli
from scripts.ops import run_recurrent_offline_research_v1 as research
from scripts.ops.run_zkp_lane1_paper_v1 import preflight_zkp_paper_v1
from src.ops.bounded_peaktrade_system_composition_v1 import (
    zkp_paper_continuation_v1 as continuation,
)
from src.ops.bounded_peaktrade_system_composition_v1.paper_episode_outcome_v1 import (
    closed_paper_episode_ids_v1,
    read_paper_episode_outcome_v1,
)
from src.experiments.canonical_experiment_identity_v1 import CanonicalCodeProvenanceV1
from tests.learning.test_offline_ddo_research_cycle_v1 import native_research_fixture
from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (
    collect_bound_paper_liquidity_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_entry_v1 import ZkpPaperEntryV1
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
    INSTRUMENT_ID,
    IRYS_PAPER_SLOT,
    NATIVE_ID,
    PAPER_FEE_RATE,
    UP_PAPER_SLOT,
    ZKP_PAPER_SLOT,
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
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    SCHEMA_VERSION,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.single_selected_future_runtime_binding_v1.persistence_v1 import (
    persist_binding_evidence_atomic_v1,
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
    step=0,
    *,
    direction=1,
    price=None,
    depth=100,
    spread_ticks=1,
    book_offset=Decimal(0),
    funding_cut=C1 + 1200,
    settled_rate=None,
    slot=ZKP_PAPER_SLOT,
):
    policy = load_paper_liquidity_policy_v1(REPO)
    now = C1 + 62 + step * 2 + 0.2
    event = str(int((now - 0.2) * 1000))
    acquired = datetime.fromtimestamp(now - 0.1, timezone.utc).isoformat()
    start_mark = Decimal("0.2032") if slot == UP_PAPER_SLOT else Decimal("0.0335")
    movement = Decimal("0.0018") if slot == UP_PAPER_SLOT else Decimal("0.00030")
    contract_size = 10
    if slot == IRYS_PAPER_SLOT:
        start_mark = Decimal("0.01765")
        movement = Decimal("0.00016")
        contract_size = 100
    mark = price if price is not None else start_mark + step * direction * movement
    tick = Decimal("0.00001")
    bid = mark + book_offset - spread_ticks * tick
    ask = mark + book_offset + spread_ticks * tick
    inst = {
        "instId": slot.native_id,
        "instType": "FUTURES",
        "instFamily": slot.family,
        "uly": slot.index_id,
        "ctType": "linear",
        "ctValCcy": slot.base_currency,
        "ctVal": str(contract_size),
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
        str(start_mark * (1 + direction * Decimal("0.002") * (i - 99 + minute))) for i in range(100)
    ]
    trade = [
        [
            str((C1 + (i - 99 + minute) * 60) * 1000),
            *([price] * 4),
            "5",
            str(5 * contract_size),
            str(5 * contract_size * Decimal(price)),
            "1",
        ]
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
            str(10000 * contract_size),
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
                "instFamily": slot.family,
                "imr": "0.05",
                "mmr": "0.02",
                "maxLever": "20",
                "maxSz": "100000",
            }
        ],
        "adv": daily,
        "funding": [
            {
                "instId": slot.native_id,
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
                "instId": slot.native_id,
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
        "open-interest": [
            {
                "instId": slot.native_id,
                "ts": event,
                "oi": "2000",
                "oiCcy": str(2000 * contract_size),
            }
        ],
        "ticker": [
            {
                "instId": slot.native_id,
                "ts": event,
                "vol24h": "10000",
                "volCcy24h": str(10000 * contract_size),
            }
        ],
        "usdc-index": [{"instId": "USDC-USD", "ts": event, "idxPx": "1"}],
        "index": [{"instId": slot.index_id, "ts": event, "idxPx": str(mark)}],
        "book": [
            {
                "ts": event,
                "bids": [[str(bid), "5"]] + ([[str(bid - tick), str(depth)]] if depth else []),
                "asks": [[str(ask), "5"]] + ([[str(ask + tick), str(depth)]] if depth else []),
            }
        ],
        "mark": [{"instId": slot.native_id, "ts": event, "markPx": str(mark)}],
    }
    receipts = {}
    for name, (path, query) in zkp_public_queries_v1(policy.adv_days, slot=slot).items():
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


def _market(step=0, *, slot=ZKP_PAPER_SLOT, **kwargs):
    receipts, policy, observed = _observations(step, slot=slot, **kwargs)
    return bind_zkp_paper_market_v1(receipts, policy=policy, observed_unix=observed, slot=slot)


def _against_position(cursor_root, direction):
    scope = restore_layered_core_episode_v1(cursor_root)
    move = max(3 * scope.scope.d_t, 0.00003)
    return Decimal(str(round(scope.running_reference.reference_price_r_t - direction * move, 5)))


def _seal_fixture(root, booking):
    paper_cli.immutable_json_v1(root / "window.json", {"started_at": C1, "duration_seconds": 7200})
    closeout = {
        "status": "WINDOW_ENDED_OCCUPIED",
        "authority": "NONE",
        "last_booking": booking,
        "orders_sent": 0,
        "permits_created": 0,
    }
    paper_cli.immutable_json_v1(root / "closeout.json", closeout)
    paper_cli.seal_xperp_paper_archive_v1(root, closeout)


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


def test_opening_quantity_is_limited_to_executable_depth(tmp_path):
    market = _market()
    root = tmp_path.resolve() / "paper-thin"
    session = ZkpPaperEntryV1(
        root=root, repo=REPO, revision="f" * 40, initial_market=market, duration=7200
    )
    for step in range(7):
        market = _market(step, depth=0)
        result = session.step_v1(market, clock=lambda: market.observed_unix + 0.01)
        if result["status"] == "FIRST_FILL_BOOKED":
            break
    assert result["status"] == "FIRST_FILL_BOOKED", result
    opening = json.loads((root / "opening-plan.json").read_bytes())
    assert Decimal(result["fill"]["quantity"]) == 5
    assert Decimal(opening["market_precheck"]["BUY"]["quantity_cap_contracts"]) == 5
    assert opening["liquidity"]["risk_admitted"]
    assert session.accounting.portfolio_state().fill_count == 1


def test_wide_spread_and_stale_market_wait_before_core(tmp_path):
    root = tmp_path.resolve() / "paper-market-wait"
    wide = _market(spread_ticks=15)
    session = ZkpPaperEntryV1(
        root=root, repo=REPO, revision="f" * 40, initial_market=wide, duration=7200
    )
    stale = _market()
    expired = session.step_v1(stale, clock=lambda: stale.observed_unix + 60)
    assert expired["reason"] == "ZKP_PAPER_MARKET_EXPIRED_AT_CHECK"
    for step in range(3):
        wide = _market(step, spread_ticks=15)
        result = session.step_v1(wide, clock=lambda: wide.observed_unix + 0.01)
        assert result["status"] == "WAITING_FOR_LIQUID_MARKET"
        for check in result["market_precheck"].values():
            assert Decimal(check["spread_bps"]) > Decimal(check["spread_limit_bps"]) == 25
            assert check["reason_codes"] == ["ZKP_PAPER_SPREAD_LIMIT"]
            assert check["quantity_cap_contracts"] is None
    assert session.accounting.portfolio_state().fill_count == 0
    assert not (root / "opening-plan.json").exists()
    assert not (root / "decisions").exists()
    assert not session.cursor_root.exists()

    for step in range(3, 10):
        market = _market(step)
        result = session.step_v1(market, clock=lambda: market.observed_unix + 0.01)
        if result["status"] == "FIRST_FILL_BOOKED":
            break
        assert session.accounting.portfolio_state().fill_count == 0
    assert result["status"] == "FIRST_FILL_BOOKED", result
    assert result["fill"]["side"] == "BUY"


def test_liquid_opposite_side_does_not_override_core(tmp_path):
    root = tmp_path.resolve() / "paper-asymmetric-book"
    market = _market()
    session = ZkpPaperEntryV1(
        root=root, repo=REPO, revision="f" * 40, initial_market=market, duration=7200
    )
    for step in range(7):
        market = _market(step, book_offset=Decimal("0.00025"))
        result = session.step_v1(market, clock=lambda: market.observed_unix + 0.01)
        if result.get("decision_outcome") == "enter_long":
            break
    assert result["decision_outcome"] == "enter_long", result
    assert result["status"] == "BLOCKED"
    assert result["market_precheck"]["SELL"]["risk_admitted"]
    assert result["reason_codes"] == ["ZKP_PAPER_SLIPPAGE_LIMIT"]
    assert session.accounting.portfolio_state().fill_count == 0
    assert not (root / "opening-plan.json").exists()


def test_liquidity_rejects_adverse_book_impact_and_volume_participation():
    market = _market()
    asks = (market.book.asks[0], (market.mark + Decimal("0.00050"), Decimal(100)))
    market = replace(market, book=replace(market.book, asks=asks))
    check = market.assess_opening_liquidity_v1(side="BUY")
    quantity = Decimal(check["quantity_cap_contracts"])
    assert quantity > 5
    assert market.assess_quantity_v1(side="BUY", quantity=quantity)["risk_admitted"]
    assert market.assess_quantity_v1(side="BUY", quantity=quantity + 1)["reason_codes"] == [
        "ZKP_PAPER_SLIPPAGE_LIMIT"
    ]
    market = replace(market, adv_usd=Decimal("10"))
    assert market.assess_opening_liquidity_v1(side="BUY")["quantity_cap_contracts"] == "2"
    result = market.assess_quantity_v1(side="BUY", quantity=Decimal(50))
    assert result["risk_admitted"] is False
    assert result["reason_codes"] == [
        "ZKP_PAPER_SLIPPAGE_LIMIT",
        "ZKP_PAPER_ADV_PARTICIPATION_LIMIT",
    ]


@pytest.mark.parametrize("slot", [ZKP_PAPER_SLOT, UP_PAPER_SLOT, IRYS_PAPER_SLOT])
def test_operator_preflight_stays_outside_paper_state(tmp_path, monkeypatch, capsys, slot):
    root = tmp_path.resolve() / "input-evidence"

    def capture(*args, slot=ZKP_PAPER_SLOT, **kwargs):
        return _market(slot=slot)

    monkeypatch.setattr(paper_cli, "_capture", capture)

    def reject_run(*args, **kwargs):
        pytest.fail("the preflight entrypoint attempted to open a session")

    monkeypatch.setattr(paper_cli, "_run", reject_run)
    args = ["preflight", "--evidence-root", str(root)]
    if slot != ZKP_PAPER_SLOT:
        config = tmp_path / "slot-config.json"
        selection = {
            "lane": slot.lane_id,
            "canonical_instrument_id": slot.instrument_id,
            "native_instrument_id": slot.native_id,
            "surface": "PAPER_EXCHANGE",
            "authority": "NONE",
        }
        config.write_text(
            json.dumps({**selection, "native_instrument_id": ZKP_PAPER_SLOT.native_id})
        )
        with pytest.raises(SystemExit) as error:
            paper_cli.main([*args, "--slot-config", str(config)])
        assert error.value.code == 2
        assert f"{slot.base_currency}_PAPER_SLOT_CONFIG_MISMATCH" in capsys.readouterr().err
        assert not root.exists()
        config.write_text(json.dumps(selection))
        args += ["--slot-config", str(config)]
    assert paper_cli.main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["session_started"] is False
    assert result["lane_id"] == slot.lane_id
    assert result["native_instrument_id"] == slot.native_id
    assert set(path.name for path in root.iterdir()) == {"preflight.json"}


def _persist_cap24_selection(root, *, alternate=False):
    bound = BoundInstrumentV1(
        instrument_id=(
            "okx_eea:linear_perpetual:MMT:USDT:USDT:perp" if alternate else INSTRUMENT_ID
        ),
        venue_native_id="MMT-USDT-SWAP" if alternate else NATIVE_ID,
        ranking_snapshot_id="ranking",
        ranking_integrity_digest="d" * 64,
        universe_snapshot_id="universe",
        selection_id="second-selection" if alternate else "first-selection",
        selection_integrity_digest=("b" if alternate else "a") * 64,
        selection_state="SELECTED_ACTIVE",
    )
    persist_binding_evidence_atomic_v1(
        evidence_root=root,
        evidence={
            **bound.to_dict(),
            "capability_id": CAPABILITY_ID,
            "schema_version": SCHEMA_VERSION,
            "ok": True,
            "hard_stop": False,
            "bound": bound.to_dict(),
        },
        result={"ok": True},
    )
    return bound


def test_cap24_preflight_measures_the_new_contract_after_selection(tmp_path, monkeypatch, capsys):
    cap24 = tmp_path / "cap24"
    requests = []
    current = _persist_cap24_selection(cap24)
    observations, _, now = _observations()

    class FixtureTransport:
        def __init__(self, *, timeout_seconds, max_request_count):
            assert max_request_count == 4

        def get(self, *, endpoint, auth_required, pretrade_decision_id, get_cache_policy):
            assert auth_required is False
            url = urlsplit(endpoint)
            native = current.venue_native_id
            assert parse_qs(url.query)["instId"] == [native]
            requests.append((native, url.path, pretrade_decision_id))
            key = {
                "/api/v5/public/instruments": "instrument",
                "/api/v5/public/mark-price": "mark",
                "/api/v5/market/candles": "adv",
                "/api/v5/market/books": "book",
            }[url.path]
            payload = json.loads(json.dumps(observations[key].payload))
            row = payload["data"][0]
            if key in {"instrument", "mark", "book"}:
                row["instId"] = native
            if native != NATIVE_ID and key == "instrument":
                assert parse_qs(url.query)["instType"] == ["SWAP"]
                row.update(
                    instType="SWAP", ctValCcy="MMT", settleCcy="USDT", lotSz=".5", minSz=".5"
                )
            body = json.dumps(payload).encode()
            result = replace(
                observations[key],
                endpoint=endpoint,
                pretrade_decision_id=pretrade_decision_id,
                payload=payload,
                body_sha256=sha256(body).hexdigest(),
            )
            self.raw_response_sink_v1(result=result, body=body)
            return result

    def collect(*args, **kwargs):
        return collect_bound_paper_liquidity_v1(*args, **kwargs, clock=lambda: now)

    monkeypatch.setattr(paper_cli, "FullCoreProductiveReadOnlyGetTransportV1", FixtureTransport)
    monkeypatch.setattr(paper_cli, "collect_bound_paper_liquidity_v1", collect)
    for alternate in (False, True):
        if alternate:
            current = _persist_cap24_selection(cap24, alternate=True)
            observations, _, now = _observations(spread_ticks=15)
        output = tmp_path / current.selection_id
        assert (
            paper_cli.main(
                ["preflight", "--cap24-evidence-root", str(cap24), "--evidence-root", str(output)]
            )
            == 0
        )
        actual = json.loads(capsys.readouterr().out)
        assert actual == json.loads((output / "preflight.json").read_bytes())
        assert actual["lane_id"] == "LANE_1"
        assert actual["instrument_id"] == current.instrument_id
        assert actual["selection_integrity_digest"] == current.selection_integrity_digest
        assert actual["session_started"] is False
        assert actual["authority"] == "NONE"
        assert actual["quote_asset"] == ("USDT" if alternate else "USD")
        check = actual["liquidity_at_minimum_quantity"]["BUY"]
        assert Decimal(check["quantity_contracts"]) == (Decimal(".5") if alternate else Decimal(1))
        assert check["risk_admitted"] is not alternate
        assert check["reason_codes"] == (["ZKP_PAPER_SPREAD_LIMIT"] if alternate else [])
        assert {native for native, _, _ in requests[-4:]} == {current.venue_native_id}
    assert len(requests) == 8 and requests[0][2] != requests[4][2]


def test_cap24_preflight_discards_measurement_if_binding_changes_during_capture(
    tmp_path, monkeypatch, capsys
):
    cap24 = tmp_path / "cap24"
    first = _persist_cap24_selection(cap24)

    def capture(policy, *, label, output, bound):
        assert bound == first
        _persist_cap24_selection(cap24, alternate=True)
        return {}

    monkeypatch.setattr(paper_cli, "_capture", capture)
    output = tmp_path / "output"
    with pytest.raises(SystemExit, match="2"):
        paper_cli.main(
            ["preflight", "--cap24-evidence-root", str(cap24), "--evidence-root", str(output)]
        )
    assert "PAPER_LIQUIDITY_CAP24_SELECTION_CHANGED" in capsys.readouterr().err
    assert not (output / "preflight.json").exists()


@pytest.mark.parametrize("direction", [1, -1])
@pytest.mark.parametrize("slot", [ZKP_PAPER_SLOT, UP_PAPER_SLOT, IRYS_PAPER_SLOT])
def test_occupied_paper_books_one_net_fill_and_cold_resumes(tmp_path, direction, slot):
    root = tmp_path.resolve() / "paper-net"
    args = dict(root=root, repo=REPO, revision="f" * 40, slot=slot)
    opened = ZkpPaperEntryV1(
        **args, initial_market=_market(direction=direction, slot=slot), duration=7200
    )
    for i in range(7):
        market = _market(i, direction=direction, slot=slot)
        initial = opened.step_v1(market, clock=lambda: market.observed_unix + 0.01)
        if initial["status"] == "FIRST_FILL_BOOKED":
            break
    assert initial["status"] == "FIRST_FILL_BOOKED"
    session = continuation.ZkpPaperContinuationV1(**args)
    assert session.last_receipt == initial
    assert session.cursor_root.name == slot.lane_id
    assert set(path.name for path in session.cursor_root.parent.iterdir()) == {slot.lane_id}
    if slot != ZKP_PAPER_SLOT:
        with pytest.raises(ValueError, match="ZKP_PAPER_ORIGINAL_PROFILE_REQUIRED"):
            continuation.ZkpPaperContinuationV1(**{**args, "slot": ZKP_PAPER_SLOT})
    held = _market(i + 1, direction=direction, slot=slot)
    hold = session.step_v1(held, clock=lambda: held.observed_unix + 0.01)
    assert hold["status"] == "WAIT", hold
    switch_price = _against_position(session.cursor_root, direction)
    thin = _market(i + 2, direction=direction, slot=slot, price=switch_price, depth=0)
    blocked = session.step_v1(thin, clock=lambda: thin.observed_unix + 0.01)
    assert blocked["status"] == "REVERSAL_BLOCKED", blocked
    assert blocked["reason_codes"] == ["ZKP_PAPER_EXECUTABLE_DEPTH_INSUFFICIENT"]
    assert session.accounting.fill_order == [initial["fill"]["fill_id"]]
    retry = _market(i + 3, direction=direction, slot=slot, price=switch_price, depth=1000)

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
    assert receipt["lane_id"] == slot.lane_id and receipt["fill"]["instrument_id"] == slot.native_id
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
    following = _market(i + 4, direction=direction, slot=slot, price=switch_price)
    resumed = repeated.step_v1(following, clock=lambda: following.observed_unix + 0.01)
    assert resumed["status"] == "WAIT", resumed
    assert resumed["episode_id"] == receipt["episode_id"]
    assert resumed["trading_epoch"] == receipt["trading_epoch"] + 1
    assert repeated.accounting.portfolio_state().fill_count == 2
    back = _market(
        i + 5,
        direction=direction,
        slot=slot,
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
    _seal_fixture(root, second)
    assert closed_paper_episode_ids_v1(root) == (initial["episode_id"], receipt["episode_id"])
    first, following = (
        read_paper_episode_outcome_v1(root, episode, expected_lane_id=slot.lane_id)
        for episode in (initial["episode_id"], receipt["episode_id"])
    )
    close_leg, open_leg = first["fill_bindings"][-1], following["fill_bindings"][0]
    assert close_leg["fill_id"] == open_leg["fill_id"] == receipt["fill"]["fill_id"]
    assert close_leg["decision_id"] == open_leg["decision_id"] == receipt["decision_id"]
    assert (close_leg["episode_fill_role"], open_leg["episode_fill_role"]) == ("CLOSE", "OPEN")
    for field, original_field in (
        ("fee", "fee"),
        ("episode_contracts", "quantity"),
        ("notional", "notional"),
        ("slippage", "slippage_cost"),
    ):
        assert Decimal(close_leg[field]) + Decimal(open_leg[field]) == Decimal(
            receipt["fill"][original_field]
        )


@pytest.mark.parametrize("slot", [ZKP_PAPER_SLOT, UP_PAPER_SLOT, IRYS_PAPER_SLOT])
def test_bounded_driver_continues_after_opening_and_leaves_position_at_end(
    tmp_path, monkeypatch, slot
):
    tmp_path = tmp_path.resolve()
    root = tmp_path / "paper" / (slot.lane_id.lower() + "-fixture")
    root.parent.mkdir()
    elapsed = 0
    index = 0
    initial = _market(slot=slot)
    latest = initial
    lane = root / "flat-entry-mark-v2" / slot.lane_id

    def capture(policy, *, label, output):
        nonlocal index, latest
        index += 1
        price = None
        if (root / "opening-fill.json").is_file():
            price = latest.mark if (root / "reversals").exists() else _against_position(lane, 1)
        latest = _market(index, price=price, depth=1000, slot=slot)
        return latest

    def sleep(seconds):
        nonlocal elapsed
        elapsed += seconds

    monkeypatch.setattr(paper_cli, "monotonic", lambda: elapsed)
    monkeypatch.setattr(paper_cli, "time", lambda: latest.observed_unix + 0.01)
    monkeypatch.setattr(paper_cli, "sleep", sleep)
    assignment = BoundInstrumentV1(
        instrument_id=slot.instrument_id,
        venue_native_id=slot.native_id,
        selection_id="original-cap24-fixture",
        selection_integrity_digest="1" * 64,
        ranking_snapshot_id="original-ranking",
        ranking_integrity_digest="2" * 64,
        universe_snapshot_id="original-universe",
        selection_state="SELECTED",
    )
    result = paper_cli._run(
        root,
        initial,
        policy=initial.policy,
        duration=40,
        started_at=initial.observed_unix,
        deadline=40,
        revision="f" * 40,
        capture=capture,
        card_assignment=assignment,
    )
    assert result["status"] == "WINDOW_ENDED_OCCUPIED", result
    cards = root / "instrument-cards" / slot.lane_id
    retained = [
        json.loads(p.read_bytes())["body"] for p in (cards / "versions").glob("*/decision.json")
    ]
    evaluated = [row for row in retained if row["master_v2"] is not None]
    assert len(evaluated) > 1
    assert len({row["version"] for row in retained}) > 1
    for row in evaluated:
        assert row["ranking_binding"] == assignment.to_dict()
        assert row["slot_identity"]["lane_id"] == slot.lane_id
        assert row["assignment_status"] == "ORIGINAL_CAP24_ASSIGNMENT_CARRIED"
        context = row["master_v2"]["prepared_input"]["canonical_market_context"]
        assert context["instrument_id"] == slot.instrument_id
        assert context["mark_price"] == row["market"]["mark_price"]
        assert context["index_price"] == row["market"]["index_price"]
        assert context["volume"] == row["market"]["volume_contracts_24h"]
        assert context["open_interest"] == row["market"]["open_interest_contracts"]
        assert context["funding_rate"] == row["market"]["funding_rate"]
        assert row["master_v2"]["decision"] is not None
    assert json.loads((cards / "latest.json").read_bytes())["body"]["status"] == "BLOCKED"
    initial_result = json.loads((root / "initial-result.json").read_bytes())
    assert initial_result["market_precheck"]["BUY"]["risk_admitted"]
    booking = result["last_booking"]
    assert booking["status"] == "NET_REVERSAL_BOOKED", booking
    assert booking["accounting"]["fill_count"] == 2
    assert booking["accounting"]["positions"][0]["side"].lower() == "short"
    assert booking["fill"]["instrument_id"] == slot.native_id
    assert len(list((root / "reversals").glob("*.json"))) == 1
    before = load_current_productive_sidestate_confirmation_cursor_v1(lane)
    manifest = root / "MANIFEST.sha256"
    original = manifest.read_bytes()
    manifest.unlink()
    recovered = paper_cli._resume(
        root, policy=initial.policy, revision="f" * 40, capture=capture, slot=slot
    )
    assert recovered == result
    assert manifest.read_bytes() == original
    assert load_current_productive_sidestate_confirmation_cursor_v1(lane) == before

    (episode_id,) = closed_paper_episode_ids_v1(root)
    assert episode_id == booking["previous_episode_id"]
    with pytest.raises(ValueError, match="EPISODE_NOT_CLOSED"):
        read_paper_episode_outcome_v1(root, booking["episode_id"])
    measurement = read_paper_episode_outcome_v1(root, episode_id, expected_lane_id=slot.lane_id)
    assert (measurement["lane_id"], measurement["instrument_id"]) == (
        slot.lane_id,
        slot.instrument_id,
    )
    assert measurement["fill_bindings"][-1]["decision_id"] == booking["decision_id"]
    assert Decimal(measurement["fees"]) < Decimal(booking["accounting"]["cumulative_fees"])

    from scripts.ops import paper_episode_learning_handoff_v1 as learning
    from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
        LEDGER_FILENAME_DEFAULT,
        AppendOnlyDdoLedgerV0,
    )

    handoff_args = dict(archive_root=root, episode_id=episode_id, expected_lane_id=slot.lane_id)
    # A prior import must retain its original ledger/measurement identities.
    legacy_root = tmp_path / "legacy-learning"
    original_reader = learning.read_paper_episode_outcome_v1
    with monkeypatch.context() as patch:

        def legacy_reader(*args, **kwargs):
            return original_reader(*args, **{**kwargs, "include_decision_evidence": False})

        patch.setattr(learning, "read_paper_episode_outcome_v1", legacy_reader)
        legacy = learning.paper_episode_learning_handoff_v1(output_root=legacy_root, **handoff_args)
    legacy_bytes = {p: p.read_bytes() for p in legacy_root.rglob("*") if p.is_file()}
    for verify in (True, False):
        assert (
            learning.paper_episode_learning_handoff_v1(
                output_root=legacy_root, verify=verify, **handoff_args
            )
            == legacy
        )
    assert {p: p.read_bytes() for p in legacy_bytes} == legacy_bytes

    bars, config, request = native_research_fixture(slot.instrument_id, "b" * 64)
    csv_path, cfg_path, template_path = (
        tmp_path / name for name in ("bars.csv", "config.json", "input.json")
    )
    bars.to_csv(csv_path)
    cfg_path.write_text(json.dumps(config))
    profile = request.model_dump(mode="json", exclude={"learning_evidence_digest", "times"})
    profile.update(schema_version="offline_ddo_research_profile.v1", gap_dimensions=[])
    template_path.write_text(
        json.dumps(
            {
                "schema_version": "offline_research_input.v1",
                "instrument_id": slot.instrument_id,
                "bars_csv_sha256": sha256(csv_path.read_bytes()).hexdigest(),
                "backtest_json_sha256": sha256(cfg_path.read_bytes()).hexdigest(),
                "profile": profile,
            }
        )
    )
    scope = research.ResearchSlotScopeV1(
        lane_id=slot.lane_id,
        surface="PAPER_EXCHANGE",
        session_id=root.name,
        instrument_id=slot.instrument_id,
        venue_native_id=slot.native_id,
        starts_at=datetime.fromtimestamp(C1, timezone.utc),
        ends_at=datetime.fromtimestamp(C1, timezone.utc) + timedelta(hours=2),
    )
    campaign = research.ResearchCampaignV1(
        state=tmp_path / "gvef",
        paper_runs=root.parent,
        shadow_runs=tmp_path / "shadow",
        shadow_follow_ups=tmp_path / "followups",
        slot=scope,
        jobs_per_tick=2,
        history_jobs=1,
        retry_seconds=1,
        research_inputs={
            slot.instrument_id: [
                research.ResearchInputV1(template=template_path, bars=csv_path, config=cfg_path)
            ]
        },
    )
    campaign.shadow_runs.mkdir()
    campaign.shadow_follow_ups.mkdir()
    tick_args = dict(
        code=CanonicalCodeProvenanceV1("f" * 40, "CLEAN"),
        now=datetime(2026, 11, 18, tzinfo=timezone.utc),
    )
    other = IRYS_PAPER_SLOT if slot == ZKP_PAPER_SLOT else ZKP_PAPER_SLOT
    for name, update in (
        ("lane", {"lane_id": other.lane_id}),
        ("instrument", {"venue_native_id": other.native_id}),
        ("window", {"starts_at": scope.starts_at - timedelta(hours=2), "ends_at": scope.starts_at}),
    ):
        wrong = campaign.model_copy(
            update={"slot": scope.model_copy(update=update), "state": tmp_path / name}
        )
        (rejected,) = research.tick_research_campaign_v1(wrong, **tick_args)["jobs"]
        assert rejected["status"] == "BLOCKED" and "SCOPE_MISMATCH" in rejected["reason"]
        assert not (wrong.state / "paper-learning").exists()

    (job,) = research.tick_research_campaign_v1(campaign, **tick_args)["jobs"]
    assert job["status"] == "MECHANISM_PASS", job
    assert job["source"]["slot"] == scope.model_dump(mode="json")
    (receipt_path,) = (campaign.state / "completed").glob("*.json")
    receipt = research.read_v1(receipt_path)
    assert receipt["source"]["episode"] == episode_id
    assert receipt["instrument_id"] == slot.instrument_id
    learning_root = campaign.state / "paper-learning" / "paper-episodes" / episode_id
    handoff = research.read_v1(learning_root / "result.json")
    enriched = handoff["measurement"]
    for field in ("simulated_net_pnl", "realized_pnl", "fees", "funding_pnl"):
        assert enriched[field] == measurement[field]
    original_cursor = json.loads((root / "opening-plan.json").read_bytes())["decision_cursor"]
    original_frame = original_cursor["entry_assessment_frame"]
    assert enriched["fill_bindings"][0]["decision_evidence"]["cursor"] == original_cursor
    assert "decision_evidence" in enriched["fill_bindings"][-1]
    ledger = AppendOnlyDdoLedgerV0(learning_root / LEDGER_FILENAME_DEFAULT)
    # Follow the actual LearningState -> decision link, not just the result JSON.
    state = next(row for row in ledger.read_all() if row["schema_name"] == "learning_state_record")
    decision = ledger.get(state["decision_event_ref"])
    market_ref = f"paper.archive.market:{original_frame['market_context']['input_digest']}"
    assert decision["market_snapshot_ref"] == market_ref
    assert market_ref in decision["evidence_source_refs"]
    assert (
        f"paper.archive.assessment:{original_frame['digest']}" in decision["evidence_source_refs"]
    )
    assert decision["decision_type"] == decision["decision_result"] == "UNKNOWN"
    assert decision["decision_time_information_set_ref"] is None
    assert state["last_decision_score"] == state["last_economic_score"] == "UNKNOWN"
    assert (
        learning.paper_episode_learning_handoff_v1(
            output_root=campaign.state / "paper-learning", verify=True, **handoff_args
        )
        == handoff
    )
    measurement_path = learning_root / "measurement.json"
    saved_measurement = measurement_path.read_bytes()
    ledger_path = learning_root / LEDGER_FILENAME_DEFAULT
    saved_ledger = ledger_path.read_bytes()
    for fault in ("changed_original", "downgrade"):
        bad = json.loads(saved_measurement)["body"]
        if fault == "changed_original":
            bad["fill_bindings"][0]["decision_evidence"]["cursor"]["entry_assessment_frame"][
                "market_context"
            ]["input_digest"] = "0" * 64
        else:
            for binding in bad["fill_bindings"]:
                del binding["decision_evidence"]
        bad["outcome_digest"] = research.digest_v1(
            {key: value for key, value in bad.items() if key != "outcome_digest"}
        )
        # A new transport hash cannot replace the original source or remove
        # references already bound into the LearningState's decision.
        measurement_path.write_text(json.dumps({"body": bad, "sha256": research.digest_v1(bad)}))
        try:
            with pytest.raises(ValueError, match="PAPER_LEARNING_.*MISMATCH"):
                learning.paper_episode_learning_handoff_v1(
                    output_root=campaign.state / "paper-learning", verify=True, **handoff_args
                )
            assert ledger_path.read_bytes() == saved_ledger
        finally:
            measurement_path.write_bytes(saved_measurement)
    evaluation = research.read_v1(
        campaign.state / "offline-ddo-research" / receipt["learning_digest"] / "result.json"
    )
    assert evaluation["evaluation"]["economic_status"] == "BLOCKED"
    assert research.tick_research_campaign_v1(campaign, **tick_args)["jobs"] == []
    assert manifest.read_bytes() == original
    (reversal_path,) = (root / "reversals").glob("*.json")
    reversal_path.write_bytes(reversal_path.read_bytes() + b"\n")
    tainted = campaign.model_copy(update={"state": tmp_path / "tampered"})
    (rejected,) = research.tick_research_campaign_v1(tainted, **tick_args)["jobs"]
    assert rejected["status"] == "BLOCKED" and "MANIFEST_INVALID" in rejected["reason"]
    assert not (tainted.state / "paper-learning").exists()


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
    _seal_fixture(root, reversal)
    measurement = read_paper_episode_outcome_v1(
        root, initial["episode_id"], expected_lane_id="LANE_1"
    )
    assert Decimal(measurement["funding_pnl"]) == expected
    assert Decimal(measurement["simulated_net_pnl"]) == (
        Decimal(measurement["realized_pnl"]) + expected - Decimal(measurement["fees"])
    )
