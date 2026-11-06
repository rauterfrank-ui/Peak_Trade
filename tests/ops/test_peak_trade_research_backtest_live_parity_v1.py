"""B09 research/backtest/shadow/productive parity proofs for Peak_Trade ranking."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from src.ops.economic_md_input_producer_v1.producer_v1 import (
    produce_economic_md_input_snapshot_v1,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    InjectedEconomicMdPublicSourceV1,
    InstrumentPublicMdBundleV1,
    RawMarkCandleV1,
    RawTickerQuoteV1,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.peak_trade_research_backtest_live_parity_v1.constants_v1 import (
    B10_STARTED,
    CAP23_RERANK_COUNT,
    CAP23_RESCORE_COUNT,
    CAP23_SOLE_SELECTION_OWNER,
    CROSS_UNIVERSE_AUTHORITY,
    CURRENT_PATH_CLASSIFICATION_V1,
    LIVE_EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PARITY_MODES,
    PROFILE_ONLY_SELECTION_EFFECT,
)
from src.ops.peak_trade_research_backtest_live_parity_v1.parity_v1 import (
    PeakTradeParityError,
    prove_peak_trade_research_backtest_live_parity_v1,
    validate_parity_proof_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import (
    produce_ranking_feature_production_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.single_selected_future_policy_v1.selection_v1 import (
    produce_single_selected_future_v1,
)

REPO_SHA = "b09_research_backtest_live_parity_test_sha"
OBSERVED_UNIX = 1_700_000_100.0
STARTED_UNIX = 1_700_000_000.0
COMPLETED_UNIX = 1_700_000_060.0
SOURCE_EVENT = "1700000000000"
BASE_TS_MS = 1_700_000_000_000


def _perp(inst_id: str, *, base: str) -> dict[str, Any]:
    return {
        "baseCcy": "",
        "ctMult": "1",
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": base,
        "expTime": "",
        "instFamily": f"{base}-USDT",
        "instId": inst_id,
        "instType": "SWAP",
        "lever": "5",
        "lotSz": "1",
        "minSz": "1",
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "state": "live",
        "tickSz": "0.01",
        "uly": f"{base}-USDT",
    }


def _source_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"code": "0", "msg": "", "data": rows}


def _mark_price_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "code": "0",
        "msg": "",
        "data": [{"instId": row["instId"], "markPx": "100.5"} for row in rows],
    }


def _price_path(*, start_px: float, step: float, shock_every: int = 0) -> tuple[float, ...]:
    prices: list[float] = []
    px = start_px
    for idx in range(61):
        if idx and shock_every and idx % shock_every == 0:
            px += step * 5.0
        else:
            px += step
        prices.append(px)
    return tuple(prices)


def _marks(
    venue_native_id: str,
    *,
    prices: tuple[float, ...],
    confirm: str = "1",
) -> tuple[RawMarkCandleV1, ...]:
    return tuple(
        RawMarkCandleV1(
            venue_native_id=venue_native_id,
            ts_ms=str(BASE_TS_MS + idx * 60_000),
            mark_px=f"{price:.8f}",
            confirm=confirm,
            receive_or_capture_timestamp="2023-11-14T22:14:20Z",
        )
        for idx, price in enumerate(prices)
    )


def _bundle(
    venue_native_id: str,
    *,
    prices: tuple[float, ...],
) -> InstrumentPublicMdBundleV1:
    return InstrumentPublicMdBundleV1(
        venue_native_id=venue_native_id,
        marks=_marks(venue_native_id, prices=prices),
        ticker=RawTickerQuoteV1(
            venue_native_id=venue_native_id,
            bid_px="100.00",
            ask_px="100.10",
            ticker_event_timestamp="1700000060000",
            capture_or_receive_timestamp="2023-11-14T22:14:20Z",
        ),
    )


def _flow(
    *,
    eth_prices: tuple[float, ...] | None = None,
    sol_prices: tuple[float, ...] | None = None,
    ada_prices: tuple[float, ...] | None = None,
) -> dict[str, Any]:
    rows = [
        _perp("ETH-USDT-SWAP", base="ETH"),
        _perp("SOL-USDT-SWAP", base="SOL"),
        _perp("ADA-USDT-SWAP", base="ADA"),
    ]
    universe = produce_governed_futures_universe_v1(
        source_payload=_source_payload(rows),
        mark_price_payload=_mark_price_payload(rows),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    ).snapshot
    source = InjectedEconomicMdPublicSourceV1(
        {
            "ETH-USDT-SWAP": _bundle(
                "ETH-USDT-SWAP",
                prices=eth_prices or _price_path(start_px=100.0, step=0.15, shock_every=7),
            ),
            "SOL-USDT-SWAP": _bundle(
                "SOL-USDT-SWAP",
                prices=sol_prices or _price_path(start_px=90.0, step=0.10, shock_every=11),
            ),
            "ADA-USDT-SWAP": _bundle(
                "ADA-USDT-SWAP",
                prices=ada_prices or _price_path(start_px=50.0, step=0.03),
            ),
        }
    )
    economic_md = produce_economic_md_input_snapshot_v1(
        universe_snapshot=universe.to_dict(),
        public_md_source=source,
        collection_started_at_unix=STARTED_UNIX,
        collection_completed_at_unix=COMPLETED_UNIX,
    ).snapshot
    proof = prove_peak_trade_research_backtest_live_parity_v1(
        universe_snapshot=universe,
        economic_md_snapshot=economic_md,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    return {"economic_md": economic_md, "proof": proof, "universe": universe}


def test_parity_constants_preserve_authority_bounds() -> None:
    assert CAP23_RESCORE_COUNT == 0
    assert CAP23_RERANK_COUNT == 0
    assert CAP23_SOLE_SELECTION_OWNER is True
    assert PROFILE_ONLY_SELECTION_EFFECT is False
    assert CROSS_UNIVERSE_AUTHORITY == "NONE"
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert LIVE_EXTERNAL_EFFECT_AUTHORIZED is False
    assert B10_STARTED is False
    classifications = {row["classification"] for row in CURRENT_PATH_CLASSIFICATION_V1}
    assert "DIVERGENT" not in classifications


def test_identical_canonical_inputs_prove_feature_rank_config_temporal_parity() -> None:
    proof = _flow()["proof"]
    validate_parity_proof_v1(proof)
    assert [mode.mode for mode in proof.modes] == list(PARITY_MODES)
    assert all(mode.ok for mode in proof.modes)
    assert proof.feature_formula_parity_proven is True
    assert proof.rank_order_parity_proven is True
    assert proof.config_version_parity_proven is True
    assert proof.temporal_no_lookahead_proven is True
    assert proof.productive_only_economic_formula_count == 0
    assert proof.divergent_current_path_count == 0
    productive = proof.modes[0]
    assert productive.mode == "PRODUCTIVE"
    assert productive.feature_witness
    assert productive.rank_witness
    assert [row["rank"] for row in productive.rank_witness] == [1, 2, 3]


def test_exact_economic_tie_preserves_b06_deterministic_order_across_modes() -> None:
    tied = _price_path(start_px=100.0, step=0.1)
    proof = _flow(eth_prices=tied, sol_prices=tied, ada_prices=tied)["proof"]
    validate_parity_proof_v1(proof)
    for mode in proof.modes:
        assert [row["venue_native_id"] for row in mode.rank_witness] == [
            "ADA-USDT-SWAP",
            "ETH-USDT-SWAP",
            "SOL-USDT-SWAP",
        ]


def test_missing_or_insufficient_required_input_fails_closed_not_parity_pass() -> None:
    short = _price_path(start_px=100.0, step=0.1)[:30]
    proof = _flow(eth_prices=short, sol_prices=short, ada_prices=short)["proof"]
    assert "PARITY_RANK_WITNESS_MISSING" in proof.failure_codes
    assert "PARITY_FEATURE_WITNESS_NOT_READY" in proof.failure_codes
    with pytest.raises(PeakTradeParityError, match="PARITY_PROOF_FAILURE_CODES_PRESENT"):
        validate_parity_proof_v1(proof)


def test_config_version_mismatch_is_detected() -> None:
    proof = _flow()["proof"]
    bad_mode = replace(
        proof.modes[1],
        config_identity={**dict(proof.modes[1].config_identity), "ranking_policy_version": "v2"},
    )
    bad = replace(proof, modes=(proof.modes[0], bad_mode, *proof.modes[2:]), integrity_digest="")
    bad = bad.with_integrity_digest()
    assert bad.modes[0].config_identity != bad.modes[1].config_identity
    recomputed = replace(bad, config_version_parity_proven=False).with_integrity_digest()
    with pytest.raises(PeakTradeParityError, match="CONFIG_VERSION_PARITY_NOT_PROVEN"):
        validate_parity_proof_v1(recomputed)


def test_corrupt_input_digest_fails_closed_before_formula_use() -> None:
    flow = _flow()
    corrupt = replace(flow["economic_md"], payload_digest="corrupt")
    with pytest.raises(PeakTradeParityError, match="ECONOMIC_MD_DIGEST_MISMATCH"):
        prove_peak_trade_research_backtest_live_parity_v1(
            universe_snapshot=flow["universe"],
            economic_md_snapshot=corrupt,
            repository_sha=REPO_SHA,
            producer_observed_at_unix=OBSERVED_UNIX,
        )


def test_cap23_selection_consumes_productive_rank_without_rescore_or_rerank() -> None:
    flow = _flow()
    b05_features = produce_ranking_feature_production_snapshot_v1(flow["economic_md"])
    productive_ranking = produce_productive_futures_ranking_v1(
        universe_snapshot=flow["universe"].to_dict(),
        feature_production_snapshot=b05_features,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    ).snapshot
    proof = flow["proof"]
    top_rank = proof.modes[0].rank_witness[0]
    selection = produce_single_selected_future_v1(
        ranking_snapshot=productive_ranking.to_dict(),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert selection.ok is True
    assert top_rank["rank"] == 1
    assert selection.selection.instrument_id == top_rank["canonical_instrument_id"]
    assert selection.selection.venue_native_id == top_rank["venue_native_id"]
    assert CAP23_RESCORE_COUNT == 0
    assert CAP23_RERANK_COUNT == 0


def test_downstream_selection_uses_b09_rank_winner_identity() -> None:
    flow = _flow()
    features = produce_ranking_feature_production_snapshot_v1(flow["economic_md"])
    ranking = produce_productive_futures_ranking_v1(
        universe_snapshot=flow["universe"].to_dict(),
        feature_production_snapshot=features,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    ).snapshot
    selection = produce_single_selected_future_v1(
        ranking_snapshot=ranking.to_dict(),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert selection.ok is True
    assert selection.selection.selected_future_count == 1
    assert selection.selection.max_positions_effective == 1
    assert selection.selection.instrument_id == ranking.ranked_candidates[0].canonical_instrument_id
    assert selection.selection.venue_native_id == ranking.ranked_candidates[0].venue_native_id
