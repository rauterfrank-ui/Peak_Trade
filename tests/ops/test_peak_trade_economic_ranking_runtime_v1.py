"""B06 Cap 2.2 Peak_Trade economic ranking runtime proofs."""

from __future__ import annotations

from typing import Any

from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.constants_v1 import (
    B06_IMPLEMENTED,
    CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
    ECONOMIC_RANK_ACTIVATED,
    LIVE_EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PRODUCTIVE_ECONOMIC_RANK_ACTIVATION_PIN,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.synthesize_ready_features_v1 import (
    synthesize_ready_feature_production_snapshot_v1,
)
from src.ops.peak_trade_ranking_feature_contract_v1 import (
    RankingFeatureValueState,
    RawRankingFeatureValueV1,
    RATIFIED_FEATURE_DIRECTIONS,
    RATIFIED_FEATURE_UNITS,
    RATIFIED_RAW_NORMALIZATION,
)
from src.ops.peak_trade_ranking_feature_production_v1.constants_v1 import OBSERVATION_WINDOW_ID
from src.ops.peak_trade_ranking_matrix_policy_v1 import (
    AMPLITUDE_POLICY_ID,
    B06_IMPLEMENTED as B03_B06,
    CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED as B03_WIRED,
    ECONOMIC_RANK_ACTIVATED as B03_ACTIVATED,
    PRODUCTIVE_ECONOMIC_RANK_ACTIVATION,
    VOLATILITY_POLICY_ID,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    RANKING_POLICY_ID,
    SELECTION_AUTHORITY_ADDED,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.productive_futures_ranking_producer_v1.reason_codes_v1 import RankingFailureCodeV1
from src.ops.single_selected_future_policy_v1.selection_v1 import (
    produce_single_selected_future_v1,
)

REPO_SHA = "b06_cap22_economic_rank_test_sha"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"


def _perp(inst_id: str = "ETH-USDT-SWAP", *, base: str = "ETH", **extra: object) -> dict:
    row = {
        "instId": inst_id,
        "instType": "SWAP",
        "state": "live",
        "tickSz": "0.01",
        "lotSz": "1",
        "minSz": "1",
        "ctVal": "0.01",
        "ctValCcy": base,
        "ctMult": "1",
        "ctType": "linear",
        "baseCcy": "",
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "uly": f"{base}-USDT",
        "instFamily": f"{base}-USDT",
        "category": "1",
        "expTime": "",
        "lever": "5",
        "maxLmtSz": "1000000",
        "maxMktSz": "10000",
        "maxTwapSz": "1000000",
        "maxIcebergSz": "1000000",
        "maxTriggerSz": "1000000",
        "maxStopSz": "1000000",
        "listTime": "1600000000000",
    }
    row.update(extra)
    return row


def _payload(rows: list[dict]) -> dict:
    return {"code": "0", "msg": "", "data": rows}


def _marks(*inst_ids: str) -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [{"instId": i, "markPx": "100.5"} for i in inst_ids],
    }


def _universe(rows: list[dict]) -> dict[str, Any]:
    mark_ids = [r["instId"] for r in rows]
    return produce_governed_futures_universe_v1(
        source_payload=_payload(rows),
        mark_price_payload=_marks(*mark_ids),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    ).snapshot.to_dict()


def _cid(uni: dict[str, Any], native: str) -> str:
    for row in uni["instruments"]:
        vid = row.get("venue_native_inst_id") or row.get("venue_native_id")
        if vid == native:
            return str(row["canonical_instrument_id"])
    raise AssertionError(native)


def test_b03_b06_flags_and_safety_pins() -> None:
    assert B06_IMPLEMENTED is True
    assert B03_B06 is True
    assert ECONOMIC_RANK_ACTIVATED is True
    assert B03_ACTIVATED is True
    assert CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED is True
    assert B03_WIRED is True
    assert PRODUCTIVE_ECONOMIC_RANK_ACTIVATION is False
    assert PRODUCTIVE_ECONOMIC_RANK_ACTIVATION_PIN is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert LIVE_EXTERNAL_EFFECT_AUTHORIZED is False
    assert SELECTION_AUTHORITY_ADDED is False
    assert RANKING_POLICY_ID == "PEAK_TRADE_RANKING_MATRIX_POLICY_V1"


def test_economic_ordering_by_ratified_features() -> None:
    uni = _universe(
        [
            _perp("SOL-USDT-SWAP", base="SOL", ctValCcy="SOL"),
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA", ctValCcy="ADA"),
        ]
    )
    feats = synthesize_ready_feature_production_snapshot_v1(
        uni,
        volatility_by_id={
            _cid(uni, "ETH-USDT-SWAP"): 0.05,
            _cid(uni, "SOL-USDT-SWAP"): 0.02,
            _cid(uni, "ADA-USDT-SWAP"): 0.01,
        },
        amplitude_by_id={
            _cid(uni, "ETH-USDT-SWAP"): 0.04,
            _cid(uni, "SOL-USDT-SWAP"): 0.02,
            _cid(uni, "ADA-USDT-SWAP"): 0.01,
        },
    )
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        feature_production_snapshot=feats,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert result.ok is True
    natives = [c.venue_native_id for c in result.snapshot.ranked_candidates]
    assert natives == ["ETH-USDT-SWAP", "SOL-USDT-SWAP", "ADA-USDT-SWAP"]
    assert (
        result.snapshot.ranked_candidates[0].total_score
        > result.snapshot.ranked_candidates[1].total_score
    )
    assert result.snapshot.authority["ECONOMIC_RANK_ACTIVATED"] is True
    assert result.snapshot.authority["economic_rank_state"] == "S_STAR_N_GE_2"
    assert result.snapshot.selection_authority_created is False


def test_venue_input_order_independence() -> None:
    rows_a = [
        _perp("ADA-USDT-SWAP", base="ADA", ctValCcy="ADA"),
        _perp("ETH-USDT-SWAP"),
        _perp("SOL-USDT-SWAP", base="SOL", ctValCcy="SOL"),
    ]
    rows_b = list(reversed(rows_a))
    uni_a = _universe(rows_a)
    uni_b = _universe(rows_b)
    vol = {
        _cid(uni_a, "ETH-USDT-SWAP"): 0.05,
        _cid(uni_a, "SOL-USDT-SWAP"): 0.02,
        _cid(uni_a, "ADA-USDT-SWAP"): 0.01,
    }
    amp = {
        _cid(uni_a, "ETH-USDT-SWAP"): 0.04,
        _cid(uni_a, "SOL-USDT-SWAP"): 0.02,
        _cid(uni_a, "ADA-USDT-SWAP"): 0.01,
    }
    vol_b = {
        _cid(uni_b, n): vol[_cid(uni_a, n)]
        for n in ("ETH-USDT-SWAP", "SOL-USDT-SWAP", "ADA-USDT-SWAP")
    }
    amp_b = {
        _cid(uni_b, n): amp[_cid(uni_a, n)]
        for n in ("ETH-USDT-SWAP", "SOL-USDT-SWAP", "ADA-USDT-SWAP")
    }
    ra = produce_productive_futures_ranking_v1(
        universe_snapshot=uni_a,
        feature_production_snapshot=synthesize_ready_feature_production_snapshot_v1(
            uni_a, volatility_by_id=vol, amplitude_by_id=amp
        ),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    rb = produce_productive_futures_ranking_v1(
        universe_snapshot=uni_b,
        feature_production_snapshot=synthesize_ready_feature_production_snapshot_v1(
            uni_b, volatility_by_id=vol_b, amplitude_by_id=amp_b
        ),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert [c.venue_native_id for c in ra.snapshot.ranked_candidates] == [
        c.venue_native_id for c in rb.snapshot.ranked_candidates
    ]


def test_final_deterministic_tie_uses_venue_native_fallback() -> None:
    uni = _universe(
        [
            _perp("SOL-USDT-SWAP", base="SOL", ctValCcy="SOL"),
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA", ctValCcy="ADA"),
        ]
    )
    feats = synthesize_ready_feature_production_snapshot_v1(uni)  # identical features
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        feature_production_snapshot=feats,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    natives = [c.venue_native_id for c in result.snapshot.ranked_candidates]
    assert natives == sorted(natives)
    assert all(c.total_score == 0.5 for c in result.snapshot.ranked_candidates)


def test_missing_and_invalid_required_feature_fail_closed() -> None:
    uni = _universe([_perp("ETH-USDT-SWAP"), _perp("SOL-USDT-SWAP", base="SOL", ctValCcy="SOL")])
    missing = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        feature_production_snapshot=None,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert RankingFailureCodeV1.ECONOMIC_FEATURE_PRODUCTION_SNAPSHOT_MISSING.value in (
        missing.failure_codes
    )

    from dataclasses import replace

    feats = synthesize_ready_feature_production_snapshot_v1(uni)
    eth_rows = tuple(r for r in feats.instruments if "ETH" in r.venue_native_id)
    eth_only = replace(
        feats,
        instruments=eth_rows,
        instrument_count_requested=len(eth_rows),
        instrument_count_feature_ready=len(eth_rows),
        production_digest="",
    ).with_production_digest()
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        feature_production_snapshot=eth_only,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert result.ok is True
    assert len(result.snapshot.ranked_candidates) == 1
    assert result.snapshot.ranked_candidates[0].venue_native_id == "ETH-USDT-SWAP"
    excluded_natives = {c.venue_native_id for c in result.snapshot.excluded_candidates}
    assert "SOL-USDT-SWAP" in excluded_natives

    bad_row = next(r for r in feats.instruments if "ETH" in r.venue_native_id)
    invalid_feature = RawRankingFeatureValueV1(
        feature_policy_id=VOLATILITY_POLICY_ID,
        state=RankingFeatureValueState.INVALID,
        raw_value=None,
        units=RATIFIED_FEATURE_UNITS[VOLATILITY_POLICY_ID],
        direction=RATIFIED_FEATURE_DIRECTIONS[VOLATILITY_POLICY_ID],
        observation_window_id=OBSERVATION_WINDOW_ID,
        raw_feature_normalization=RATIFIED_RAW_NORMALIZATION[VOLATILITY_POLICY_ID],
        reason_code="SYNTH_INVALID",
    )
    amp = next(r for r in bad_row.raw_features if r.feature_policy_id == AMPLITUDE_POLICY_ID)
    broken = replace(
        bad_row,
        raw_features=(invalid_feature, amp),
        feature_production_ready=False,
        exclusion_reason_codes=("SYNTH_INVALID",),
    )
    other = tuple(
        r for r in feats.instruments if r.canonical_instrument_id != broken.canonical_instrument_id
    )
    invalid_snap = replace(
        feats,
        instruments=tuple(sorted((broken, *other), key=lambda r: r.canonical_instrument_id)),
        instrument_count_feature_ready=sum(
            1 for r in (broken, *other) if r.feature_production_ready
        ),
        production_digest="",
    ).with_production_digest()
    inv = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        feature_production_snapshot=invalid_snap,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert inv.ok is True
    assert broken.venue_native_id not in {c.venue_native_id for c in inv.snapshot.ranked_candidates}


def test_determinism_and_explainability_witness() -> None:
    uni = _universe(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("SOL-USDT-SWAP", base="SOL", ctValCcy="SOL"),
        ]
    )
    feats = synthesize_ready_feature_production_snapshot_v1(
        uni,
        volatility_by_id={
            _cid(uni, "ETH-USDT-SWAP"): 0.05,
            _cid(uni, "SOL-USDT-SWAP"): 0.01,
        },
        amplitude_by_id={
            _cid(uni, "ETH-USDT-SWAP"): 0.04,
            _cid(uni, "SOL-USDT-SWAP"): 0.01,
        },
    )
    a = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        feature_production_snapshot=feats,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    b = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        feature_production_snapshot=feats,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 99.0,
    )
    assert a.snapshot.integrity_digest == b.snapshot.integrity_digest
    assert a.snapshot.authority["economic_explainability_digest"]
    assert (
        a.snapshot.authority["economic_explainability_digest"]
        == (b.snapshot.authority["economic_explainability_digest"])
    )
    assert "balanced_movement_score" in a.snapshot.ranked_candidates[0].tie_break_values


def test_eligibility_separation_structural_gates_vs_economic_score() -> None:
    uni = _universe([_perp("ETH-USDT-SWAP"), _perp("SOL-USDT-SWAP", base="SOL", ctValCcy="SOL")])
    feats = synthesize_ready_feature_production_snapshot_v1(
        uni,
        volatility_by_id={
            _cid(uni, "ETH-USDT-SWAP"): 0.01,
            _cid(uni, "SOL-USDT-SWAP"): 0.09,
        },
        amplitude_by_id={
            _cid(uni, "ETH-USDT-SWAP"): 0.01,
            _cid(uni, "SOL-USDT-SWAP"): 0.08,
        },
    )
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        feature_production_snapshot=feats,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    top = result.snapshot.ranked_candidates[0]
    assert top.venue_native_id == "SOL-USDT-SWAP"
    assert set(top.score_components) == {
        "universe_eligibility",
        "data_quality_pass",
        "mark_price_supported",
        "market_data_supported",
        "trading_status_live",
        "metadata_complete",
    }
    assert sum(top.score_components.values()) == 6.0
    assert top.total_score == 1.0  # economic attractiveness, not structural sum


def test_cap22_does_not_select_cap23_consumes_order_without_rerank() -> None:
    uni = _universe(
        [
            _perp("ADA-USDT-SWAP", base="ADA", ctValCcy="ADA"),
            _perp("ETH-USDT-SWAP"),
            _perp("SOL-USDT-SWAP", base="SOL", ctValCcy="SOL"),
        ]
    )
    feats = synthesize_ready_feature_production_snapshot_v1(
        uni,
        volatility_by_id={
            _cid(uni, "ETH-USDT-SWAP"): 0.05,
            _cid(uni, "SOL-USDT-SWAP"): 0.02,
            _cid(uni, "ADA-USDT-SWAP"): 0.01,
        },
        amplitude_by_id={
            _cid(uni, "ETH-USDT-SWAP"): 0.04,
            _cid(uni, "SOL-USDT-SWAP"): 0.02,
            _cid(uni, "ADA-USDT-SWAP"): 0.01,
        },
    )
    ranking = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        feature_production_snapshot=feats,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert ranking.snapshot.selection_authority_created is False
    selected = produce_single_selected_future_v1(
        ranking_snapshot=ranking.snapshot.to_dict(),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    # Cap 2.3 picks rank-1 without economic rerank.
    assert selected.ok is True
    assert selected.selection.venue_native_id == "ETH-USDT-SWAP"
    assert ranking.snapshot.ranked_candidates[0].venue_native_id == "ETH-USDT-SWAP"
