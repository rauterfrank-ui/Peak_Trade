"""Offline contracts for the exact public-data-to-Paper opening route."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import socket
from urllib.parse import urlencode

import pytest

from scripts.ops import run_zkp_lane1_paper_v1 as paper_cli
from scripts.ops.run_zkp_lane1_paper_v1 import preflight_zkp_paper_v1
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

REPO = Path(__file__).resolve().parents[2]
C1 = 1_700_000_040
DAY = 86400


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def deny(*args, **kwargs):
        pytest.fail("ZKP opening contract fixtures must remain offline")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)


def _observations(step=0, *, direction=1):
    policy = load_paper_liquidity_policy_v1(REPO)
    now = C1 + 62 + step * 2 + 0.2
    event = str(int((now - 0.2) * 1000))
    acquired = datetime.fromtimestamp(now - 0.1, timezone.utc).isoformat()
    mark = Decimal("0.0335") + step * direction * Decimal("0.00030")
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
    closes = [
        str(Decimal("0.0335") * (1 + direction * Decimal("0.002") * (i - 99))) for i in range(100)
    ]
    trade = [
        [str((C1 + (i - 99) * 60) * 1000), *([price] * 4), "5", "50", "1.6", "1"]
        for i, price in enumerate(closes)
    ]
    mark_history = [row[:5] + ["1"] for row in trade[-61:]]
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
                "prevFundingTime": str((C1 - 1000) * 1000),
                "fundingTime": str((C1 + 1200) * 1000),
                "nextFundingTime": str((C1 + 2400) * 1000),
                "ts": event,
            }
        ],
        "trade-candles": trade,
        "mark-candles": mark_history,
        "open-interest": [{"instId": NATIVE_ID, "ts": event, "oi": "2000", "oiCcy": "20000"}],
        "ticker": [{"instId": NATIVE_ID, "ts": event, "vol24h": "10000", "volCcy24h": "100000"}],
        "usdc-index": [{"instId": "USDC-USD", "ts": event, "idxPx": "1"}],
        "index": [{"instId": INDEX_ID, "ts": event, "idxPx": str(mark)}],
        "book": [
            {
                "ts": event,
                "bids": [[str(mark - tick), "5"], [str(mark - 2 * tick), "100"]],
                "asks": [[str(mark + tick), "5"], [str(mark + 2 * tick), "100"]],
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


def _market(step=0, *, direction=1):
    receipts, policy, observed = _observations(step, direction=direction)
    return bind_zkp_paper_market_v1(receipts, policy=policy, observed_unix=observed)


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
