"""U2a — futures_producer_packet_fixture_source_v1 contract/static tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.webui.workflow_dashboard_readmodel_v1.futures_producer_packet_fixture_source_v1 import (
    FIXTURE_PRODUCER_ID,
    FIXTURE_SOURCE_KIND,
    REASON_FORBIDDEN_UPSTREAM_SOURCE,
    REASON_OBSERVABILITY_TRUTH_CLAIMED,
    FuturesProducerPacketFixtureBundleV1,
    FuturesProducerPacketFixtureSourceError,
    assert_fixture_not_observability_truth,
    bundle_to_upstream_input,
    fixture_root_under,
    load_futures_producer_packet_fixture,
)
from src.webui.workflow_dashboard_readmodel_v1.futures_universe_upstream_adapter_v1 import (
    REASON_MARKET_SURFACE_NOT_OBSERVABILITY_TRUTH,
    REASON_SELECTED_FUTURE_NOT_IN_ELIGIBLE_UNIVERSE,
    REASON_SPOT_OR_NON_DERIVATIVE_SELECTED_FUTURE_REJECTED,
    REASON_UPSTREAM_SOURCE_EMPTY,
    map_futures_packets_to_universe_selection_readmodel,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1 import (
    MISSING_TRUTH_SELECTED,
    MISSING_TRUTH_UNIVERSE,
    validate_universe_selection_payload,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = fixture_root_under(PROJECT_ROOT)
SOURCE_MODULE = (
    PROJECT_ROOT
    / "src"
    / "webui"
    / "workflow_dashboard_readmodel_v1"
    / "futures_producer_packet_fixture_source_v1.py"
)

FORBIDDEN_SPOT_SYMBOLS = ("BTC/USD", "BTC/EUR", "ETH/USD")


def _fixture_path(name: str) -> Path:
    return FIXTURE_ROOT / name


def test_tc1_valid_fixture_loads_and_u1_accepts() -> None:
    bundle = load_futures_producer_packet_fixture(
        _fixture_path("futures_packet_valid_minimal.json")
    )

    assert bundle.source_kind == FIXTURE_SOURCE_KIND
    assert bundle.producer_id == FIXTURE_PRODUCER_ID
    assert bundle.fixture_only is True
    assert bundle.observability_truth_allowed is False
    assert bundle.non_authorizing is True
    assert len(bundle.packets) == 3
    assert all(
        packet.candidate.market_type
        in (FuturesMarketType.PERPETUAL, FuturesMarketType.FUTURES, FuturesMarketType.SWAP)
        for packet in bundle.packets
    )

    upstream = bundle_to_upstream_input(bundle)
    assert upstream.fixture_marked is True
    result = map_futures_packets_to_universe_selection_readmodel(upstream)

    assert result.status == "ok"
    contract = validate_universe_selection_payload(result.payload)
    assert contract.selected_future is not None
    assert contract.selected_future.symbol == "ETHUSDT"
    assert contract.selected_future.symbol not in FORBIDDEN_SPOT_SYMBOLS
    assert result.payload["fixture_marked"] is True


def test_tc2_fixture_only_is_not_real_truth() -> None:
    bundle = load_futures_producer_packet_fixture(
        _fixture_path("futures_packet_valid_minimal.json")
    )

    assert bundle.observability_truth_allowed is False
    assert_fixture_not_observability_truth(bundle)

    bad_bundle = FuturesProducerPacketFixtureBundleV1(
        source_kind=FIXTURE_SOURCE_KIND,
        producer_id=FIXTURE_PRODUCER_ID,
        generated_at=bundle.generated_at,
        source_run_id=bundle.source_run_id,
        source_stage=bundle.source_stage,
        fixture_only=True,
        observability_truth_allowed=True,
        non_authorizing=True,
        universe=bundle.universe,
        ranking=bundle.ranking,
        selected_future=bundle.selected_future,
        packets=bundle.packets,
    )
    with pytest.raises(
        FuturesProducerPacketFixtureSourceError, match=REASON_OBSERVABILITY_TRUTH_CLAIMED
    ):
        assert_fixture_not_observability_truth(bad_bundle)

    with pytest.raises(
        FuturesProducerPacketFixtureSourceError, match=REASON_OBSERVABILITY_TRUTH_CLAIMED
    ):
        bundle_to_upstream_input(bad_bundle)


def test_tc3_spot_invalid_fixture_rejected_by_u1_without_dummy_selected() -> None:
    bundle = load_futures_producer_packet_fixture(_fixture_path("futures_packet_spot_invalid.json"))
    result = map_futures_packets_to_universe_selection_readmodel(bundle_to_upstream_input(bundle))

    assert result.payload["selected_future"]["truth_status"] == "NOT_PERSISTED"
    assert REASON_SPOT_OR_NON_DERIVATIVE_SELECTED_FUTURE_REJECTED in result.rejection_reasons
    assert result.payload["missing_truth"]["selected_future"] == MISSING_TRUTH_SELECTED
    assert all(row["symbol"] != "BTC/USD" for row in result.payload["universe"])
    assert "BTC/USD" not in {row["symbol"] for row in result.payload["ranking"]}


def test_tc4_forbidden_market_surface_rejected_at_load() -> None:
    with pytest.raises(
        FuturesProducerPacketFixtureSourceError, match=REASON_FORBIDDEN_UPSTREAM_SOURCE
    ):
        load_futures_producer_packet_fixture(
            _fixture_path("futures_packet_forbidden_market_surface.json")
        )


def test_tc4b_forbidden_source_also_rejected_by_u1_if_bypassed() -> None:
    valid = load_futures_producer_packet_fixture(_fixture_path("futures_packet_valid_minimal.json"))
    upstream = bundle_to_upstream_input(valid)
    bypassed = type(upstream)(
        source_run_id=upstream.source_run_id,
        source_stage=upstream.source_stage,
        generated_at=upstream.generated_at,
        packets=upstream.packets,
        upstream_source_kind="market_ranking_funnel_readmodel.v0",
        upstream_producer_id="market_surface",
        selected_candidate_id=upstream.selected_candidate_id,
        evidence_links=upstream.evidence_links,
        fixture_marked=upstream.fixture_marked,
    )
    result = map_futures_packets_to_universe_selection_readmodel(bypassed)

    assert result.status == "missing_truth"
    assert REASON_MARKET_SURFACE_NOT_OBSERVABILITY_TRUTH in result.rejection_reasons
    assert result.payload["missing_truth"]["universe"] == MISSING_TRUTH_UNIVERSE


def test_tc5_selected_not_in_universe_rejected() -> None:
    bundle = load_futures_producer_packet_fixture(
        _fixture_path("futures_packet_selected_not_in_universe.json")
    )
    result = map_futures_packets_to_universe_selection_readmodel(bundle_to_upstream_input(bundle))

    assert result.payload["selected_future"]["truth_status"] == "NOT_PERSISTED"
    assert REASON_SELECTED_FUTURE_NOT_IN_ELIGIBLE_UNIVERSE in result.rejection_reasons
    assert result.payload["missing_truth"]["selected_future"] == MISSING_TRUTH_SELECTED


def test_tc6_empty_fixture_returns_missing_truth_no_dummy() -> None:
    bundle = load_futures_producer_packet_fixture(
        _fixture_path("futures_packet_missing_empty.json")
    )
    assert bundle.packets == ()

    result = map_futures_packets_to_universe_selection_readmodel(bundle_to_upstream_input(bundle))

    assert result.status == "missing_truth"
    assert REASON_UPSTREAM_SOURCE_EMPTY in result.rejection_reasons
    assert result.payload["universe"] == []
    assert result.payload["ranking"] == []
    assert result.payload["selected_future"] == {"truth_status": "NOT_PERSISTED"}
    validate_universe_selection_payload(result.payload)


def test_tc6b_missing_packets_key_raises() -> None:
    path = _fixture_path("futures_packet_missing_empty.json")
    raw = path.read_text(encoding="utf-8").replace('"packets": []', '"packets_removed": []')
    broken = path.parent / "_broken_missing_packets.json"
    broken.write_text(raw, encoding="utf-8")
    try:
        with pytest.raises(FuturesProducerPacketFixtureSourceError, match="packets"):
            load_futures_producer_packet_fixture(broken)
    finally:
        broken.unlink(missing_ok=True)


def test_tc7_no_forbidden_imports_in_fixture_source_module() -> None:
    tree = ast.parse(SOURCE_MODULE.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    forbidden_fragments = (
        "market_ranking_funnel",
        "market_surface",
        "scan_markets",
        "run_market_scan",
        "src.execution",
        "src.risk",
        "src.governance",
        "universe_selection_producer_v1",
    )
    for fragment in forbidden_fragments:
        assert not any(fragment in name for name in imported), fragment


def test_tc7b_loader_is_read_only_no_archive_producer_import() -> None:
    source_text = SOURCE_MODULE.read_text(encoding="utf-8")
    assert "write_universe_selection_readmodel" not in source_text
    assert "maybe_write_missing_truth_after_bounded_closeout" not in source_text
    assert "build_exchange_client" not in source_text
