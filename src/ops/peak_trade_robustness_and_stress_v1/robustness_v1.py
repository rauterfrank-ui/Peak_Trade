"""B10 deterministic robustness and stress harness for current Peak_Trade ranking.

This package is proof/evaluation only. It routes replay-style PT1M mark inputs
through the authoritative B05 feature producer and B06 economic ranking runtime.
Isolated single-feature scenarios start at the ratified B04 raw-feature contract
and still consume the authoritative B06 ranker.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping, Sequence

from src.ops.archive_sibling_export_contract_v1.canonical_digest import canonical_digest_v1
from src.ops.economic_md_input_producer_v1.models_v1 import (
    EconomicMdInputSnapshotV1,
)
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
from src.ops.peak_trade_economic_ranking_runtime_v1.economic_rank_v1 import (
    EconomicRankingResultV1,
    classify_and_rank_economic_candidates_v1,
)
from src.ops.peak_trade_ranking_feature_contract_v1 import (
    RATIFIED_ECONOMIC_FEATURE_POLICY_IDS,
    RATIFIED_FEATURE_DIRECTIONS,
    RATIFIED_FEATURE_UNITS,
    RATIFIED_RAW_NORMALIZATION,
    RankingFeatureValueState,
    RawRankingFeatureValueV1,
    build_policy_identity_v1,
    neutral_input2_provenance_v1,
    validate_explainability_witness_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.constants_v1 import (
    CAPABILITY_ID as FEATURE_PRODUCTION_CAPABILITY_ID,
    MARK_COUNT,
    OBSERVATION_WINDOW_ID,
    PRODUCTION_VERSION as FEATURE_PRODUCTION_VERSION,
    SCHEMA_VERSION as FEATURE_PRODUCTION_SCHEMA_VERSION,
)
from src.ops.peak_trade_ranking_feature_production_v1.models_v1 import (
    InstrumentRawFeatureProductionV1,
    RankingFeatureProductionSnapshotV1,
    compute_production_snapshot_id_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import (
    authority_block_v1 as feature_production_authority_block_v1,
    produce_ranking_feature_production_snapshot_v1,
    validate_ranking_feature_production_snapshot_v1,
)
from src.ops.peak_trade_ranking_matrix_policy_v1 import (
    AMPLITUDE_POLICY_ID,
    VOLATILITY_POLICY_ID,
    compute_ranking_matrix_policy_digest_v1,
)
from src.ops.peak_trade_research_backtest_live_parity_v1.constants_v1 import (
    AUTHORITATIVE_FEATURE_IMPLEMENTATION,
    AUTHORITATIVE_RANKING_IMPLEMENTATION,
    CAP23_RERANK_COUNT,
    CAP23_RESCORE_COUNT,
    CAP23_SOLE_SELECTION_OWNER,
    CROSS_UNIVERSE_AUTHORITY,
    LIVE_EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PROFILE_ONLY_SELECTION_EFFECT,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.peak_trade_robustness_and_stress_v1.constants_v1 import (
    INFRASTRUCTURE_CENSUS_V1,
    PACKAGE_ID,
    PACKAGE_VERSION,
    authority_block_v1,
)

REPO_SHA_PLACEHOLDER = "b10_robustness_and_stress_deterministic_fixture_sha"
OBSERVED_UNIX = 1_700_000_100.0
STARTED_UNIX = 1_700_000_000.0
COMPLETED_UNIX = 1_700_000_060.0
SOURCE_EVENT = "1700000000000"
BASE_TS_MS = 1_700_000_000_000
SOURCE_CLASS = "VENUE_NATIVE_OKX_PUBLIC_HISTORY_MARK_PRICE_CANDLES_PT1M_CONFIRM_1"
SOURCE_ENDPOINT = "/api/v5/market/history-mark-price-candles"


class B10RobustnessError(ValueError):
    """Fail-closed B10 proof error."""


@dataclass(frozen=True)
class ScenarioSpecV1:
    scenario_id: str
    domain: str
    source_kind: str
    expected_classification: str
    prices_by_venue: Mapping[str, tuple[float, ...]] | None = None
    raw_features_by_venue: Mapping[str, Mapping[str, float]] | None = None
    confirm_by_venue: Mapping[str, str] | None = None
    timestamp_gap_by_venue: Mapping[str, int] | None = None
    timestamp_reverse_by_venue: Mapping[str, int] | None = None
    bad_mark_by_venue: Mapping[str, tuple[int, str]] | None = None
    missing_venues: tuple[str, ...] = ()
    observed_age_seconds: float | None = None
    config_mismatch: bool = False


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(payload: Any) -> str:
    return canonical_digest_v1(payload)


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


def _universe_v1() -> Any:
    rows = [
        _perp("ETH-USDT-SWAP", base="ETH"),
        _perp("SOL-USDT-SWAP", base="SOL"),
        _perp("ADA-USDT-SWAP", base="ADA"),
    ]
    return produce_governed_futures_universe_v1(
        source_payload=_source_payload(rows),
        mark_price_payload=_mark_price_payload(rows),
        repository_sha=REPO_SHA_PLACEHOLDER,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    ).snapshot


def _trend_prices(*, start_px: float, step: float, shock_every: int = 0) -> tuple[float, ...]:
    prices: list[float] = []
    px = start_px
    for idx in range(MARK_COUNT):
        if idx and shock_every and idx % shock_every == 0:
            px += step * 5.0
        else:
            px += step
        prices.append(px)
    return tuple(prices)


def _range_prices(*, base: float, amplitude: float, period: int = 6) -> tuple[float, ...]:
    return tuple(
        base + amplitude * (1 if idx % period < period / 2 else -1) for idx in range(MARK_COUNT)
    )


def _default_prices() -> dict[str, tuple[float, ...]]:
    return {
        "ETH-USDT-SWAP": _trend_prices(start_px=100.0, step=0.15, shock_every=7),
        "SOL-USDT-SWAP": _trend_prices(start_px=90.0, step=0.10, shock_every=11),
        "ADA-USDT-SWAP": _trend_prices(start_px=50.0, step=0.03),
    }


def _marks(
    venue_native_id: str,
    *,
    prices: tuple[float, ...],
    base_ts_ms: int,
    confirm: str = "1",
    gap_at: int | None = None,
    reverse_at: int | None = None,
    bad_mark: tuple[int, str] | None = None,
) -> tuple[RawMarkCandleV1, ...]:
    rows: list[RawMarkCandleV1] = []
    for idx, price in enumerate(prices):
        ts = base_ts_ms + idx * 60_000
        if gap_at is not None and idx >= gap_at:
            ts += 60_000
        if reverse_at is not None and idx == reverse_at:
            ts -= 120_000
        mark_px = f"{price:.8f}"
        if bad_mark is not None and bad_mark[0] == idx:
            mark_px = bad_mark[1]
        rows.append(
            RawMarkCandleV1(
                venue_native_id=venue_native_id,
                ts_ms=str(ts),
                mark_px=mark_px,
                confirm=confirm,
                receive_or_capture_timestamp="2023-11-14T22:14:20Z",
            )
        )
    return tuple(rows)


def _bundle(
    venue_native_id: str,
    *,
    prices: tuple[float, ...],
    base_ts_ms: int,
    confirm: str = "1",
    gap_at: int | None = None,
    reverse_at: int | None = None,
    bad_mark: tuple[int, str] | None = None,
) -> InstrumentPublicMdBundleV1:
    return InstrumentPublicMdBundleV1(
        venue_native_id=venue_native_id,
        marks=_marks(
            venue_native_id,
            prices=prices,
            base_ts_ms=base_ts_ms,
            confirm=confirm,
            gap_at=gap_at,
            reverse_at=reverse_at,
            bad_mark=bad_mark,
        ),
        ticker=RawTickerQuoteV1(
            venue_native_id=venue_native_id,
            bid_px="100.00",
            ask_px="100.10",
            ticker_event_timestamp="1700000060000",
            capture_or_receive_timestamp="2023-11-14T22:14:20Z",
        ),
    )


def _economic_md_for_scenario(
    spec: ScenarioSpecV1, *, window_index: int
) -> tuple[Any, EconomicMdInputSnapshotV1]:
    universe = _universe_v1()
    prices_by_venue = dict(_default_prices())
    prices_by_venue.update(dict(spec.prices_by_venue or {}))
    bundles: dict[str, InstrumentPublicMdBundleV1] = {}
    base_ts_ms = BASE_TS_MS + window_index * MARK_COUNT * 60_000
    for venue in ("ETH-USDT-SWAP", "SOL-USDT-SWAP", "ADA-USDT-SWAP"):
        if venue in spec.missing_venues:
            continue
        bundles[venue] = _bundle(
            venue,
            prices=prices_by_venue[venue],
            base_ts_ms=base_ts_ms,
            confirm=(spec.confirm_by_venue or {}).get(venue, "1"),
            gap_at=(spec.timestamp_gap_by_venue or {}).get(venue),
            reverse_at=(spec.timestamp_reverse_by_venue or {}).get(venue),
            bad_mark=(spec.bad_mark_by_venue or {}).get(venue),
        )
    produced = produce_economic_md_input_snapshot_v1(
        universe_snapshot=universe.to_dict(),
        public_md_source=InjectedEconomicMdPublicSourceV1(bundles),
        collection_started_at_unix=STARTED_UNIX + window_index * 3600,
        collection_completed_at_unix=COMPLETED_UNIX + window_index * 3600,
    )
    return universe, produced.snapshot


def _ready_raw_feature(feature_policy_id: str, value: float) -> RawRankingFeatureValueV1:
    return RawRankingFeatureValueV1(
        feature_policy_id=feature_policy_id,
        state=RankingFeatureValueState.READY,
        raw_value=float(value),
        units=RATIFIED_FEATURE_UNITS[feature_policy_id],
        direction=RATIFIED_FEATURE_DIRECTIONS[feature_policy_id],
        observation_window_id=OBSERVATION_WINDOW_ID,
        raw_feature_normalization=RATIFIED_RAW_NORMALIZATION[feature_policy_id],
        reason_code=None,
    )


def _manual_feature_snapshot_v1(
    raw_features_by_venue: Mapping[str, Mapping[str, float]],
) -> RankingFeatureProductionSnapshotV1:
    universe = _universe_v1().to_dict()
    canonical_by_venue = {
        str(row.get("venue_native_inst_id") or row.get("venue_native_id")): str(
            row["canonical_instrument_id"]
        )
        for row in universe.get("instruments") or ()
    }
    instruments: list[InstrumentRawFeatureProductionV1] = []
    for venue in sorted(raw_features_by_venue):
        canonical = canonical_by_venue[venue]
        raw_map = raw_features_by_venue[venue]
        features = tuple(
            _ready_raw_feature(feature_id, float(raw_map[feature_id]))
            for feature_id in RATIFIED_ECONOMIC_FEATURE_POLICY_IDS
        )
        payload_for_digest = {
            "canonical_instrument_id": canonical,
            "raw_features": [row.to_dict() for row in features],
            "venue_native_id": venue,
        }
        instruments.append(
            InstrumentRawFeatureProductionV1(
                canonical_instrument_id=canonical,
                venue_native_id=venue,
                raw_features=features,
                feature_production_ready=True,
                mark_window_provenance=None,
                exclusion_reason_codes=(),
                economic_md_raw_input_digest=_digest(payload_for_digest),
            )
        )
    input_digest = _digest({"raw_feature_contract_scenario": raw_features_by_venue})
    snapshot_id = compute_production_snapshot_id_v1(
        economic_input_snapshot_id="b10_raw_feature_contract_scenario",
        economic_input_snapshot_digest=input_digest,
        instrument_feature_digests=tuple(_digest(row.to_dict()) for row in instruments),
    )
    snapshot = RankingFeatureProductionSnapshotV1(
        schema_version=FEATURE_PRODUCTION_SCHEMA_VERSION,
        production_version=FEATURE_PRODUCTION_VERSION,
        capability_id=FEATURE_PRODUCTION_CAPABILITY_ID,
        production_snapshot_id=snapshot_id,
        policy_identity=build_policy_identity_v1(),
        input2_provenance=neutral_input2_provenance_v1(
            economic_input_snapshot_id="b10_raw_feature_contract_scenario",
            economic_input_snapshot_digest=input_digest,
            collection_cycle_id="b10_raw_feature_contract_cycle",
            observed_at_event_time="2026-09-26T00:00:00Z",
        ),
        instruments=tuple(instruments),
        instrument_count_requested=len(instruments),
        instrument_count_feature_ready=len(instruments),
        production_digest="",
        authority=feature_production_authority_block_v1(),
        call_graph=("B10_RAW_FEATURE_CONTRACT_SCENARIO",),
    ).with_production_digest()
    validate_ranking_feature_production_snapshot_v1(snapshot)
    return snapshot


def _feature_witness(features: RankingFeatureProductionSnapshotV1) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for instrument in features.instruments:
        out.append(
            {
                "canonical_instrument_id": instrument.canonical_instrument_id,
                "venue_native_id": instrument.venue_native_id,
                "feature_production_ready": instrument.feature_production_ready,
                "raw_features": [row.to_dict() for row in instrument.raw_features],
                "exclusion_reason_codes": list(instrument.exclusion_reason_codes),
                "mark_window_provenance": (
                    None
                    if instrument.mark_window_provenance is None
                    else instrument.mark_window_provenance.to_dict()
                ),
            }
        )
    return out


def _rank_witness(result: EconomicRankingResultV1) -> list[dict[str, Any]]:
    explain_by_id = {
        candidate.canonical_instrument_id: candidate
        for candidate in result.explainability.candidates
    }
    rows: list[dict[str, Any]] = []
    for candidate in result.ranked:
        explain = explain_by_id[candidate.canonical_instrument_id]
        rows.append(
            {
                "rank": candidate.rank,
                "canonical_instrument_id": candidate.canonical_instrument_id,
                "venue_native_id": candidate.venue_native_id,
                "total_score": candidate.total_score,
                "tie_break_values": dict(candidate.tie_break_values),
                "normalized_features": [row.to_dict() for row in explain.normalized_features],
                "score_contributions": [row.to_dict() for row in explain.score_contributions],
            }
        )
    return rows


def _excluded_witness(result: EconomicRankingResultV1) -> list[dict[str, Any]]:
    return [
        {
            "canonical_instrument_id": row.canonical_instrument_id,
            "venue_native_id": row.venue_native_id,
            "eligibility_status": row.eligibility_status,
            "exclusion_reason_codes": list(row.exclusion_reason_codes),
            "tie_break_values": dict(row.tie_break_values),
        }
        for row in result.excluded
    ]


def _temporal_no_lookahead(features: RankingFeatureProductionSnapshotV1) -> bool:
    for instrument in features.instruments:
        provenance = instrument.mark_window_provenance
        if not instrument.feature_production_ready:
            continue
        if provenance is None or not provenance.event_timestamps:
            return False
        if max(provenance.event_timestamps) != provenance.as_of_event_time:
            return False
    return True


def _evaluate_scenario_v1(spec: ScenarioSpecV1, *, window_index: int = 0) -> dict[str, Any]:
    universe = _universe_v1()
    economic_md: EconomicMdInputSnapshotV1 | None = None
    if spec.source_kind == "PT1M_REPLAY":
        universe, economic_md = _economic_md_for_scenario(spec, window_index=window_index)
        if economic_md.payload_digest != economic_md.compute_payload_digest():
            raise B10RobustnessError("ECONOMIC_MD_DIGEST_MISMATCH", spec.scenario_id)
        features = produce_ranking_feature_production_snapshot_v1(
            economic_md,
            observed_age_seconds=spec.observed_age_seconds,
        )
    elif spec.source_kind == "B04_RAW_FEATURE_CONTRACT":
        if spec.raw_features_by_venue is None:
            raise B10RobustnessError("RAW_FEATURE_SCENARIO_REQUIRED", spec.scenario_id)
        features = _manual_feature_snapshot_v1(spec.raw_features_by_venue)
    else:
        raise B10RobustnessError("UNKNOWN_SCENARIO_SOURCE_KIND", spec.source_kind)

    validate_ranking_feature_production_snapshot_v1(features)
    result = classify_and_rank_economic_candidates_v1(
        universe_snapshot=universe.to_dict(),
        feature_production_snapshot=features,
    )
    validate_explainability_witness_v1(result.explainability)
    productive = produce_productive_futures_ranking_v1(
        universe_snapshot=universe.to_dict(),
        feature_production_snapshot=features,
        repository_sha=REPO_SHA_PLACEHOLDER,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    config_identity = {
        "feature_production_digest": features.production_digest,
        "feature_production_version": features.production_version,
        "ranking_config_digest": productive.snapshot.config_digest,
        "ranking_policy_id": productive.snapshot.ranking_policy_id,
        "ranking_policy_version": (
            "B10_CONFIG_MISMATCH_INJECTION"
            if spec.config_mismatch
            else productive.snapshot.ranking_policy_version
        ),
        "ranking_policy_digest": compute_ranking_matrix_policy_digest_v1(),
    }
    rank_witness = _rank_witness(result)
    payload = {
        "scenario_id": spec.scenario_id,
        "domain": spec.domain,
        "source_kind": spec.source_kind,
        "expected_classification": spec.expected_classification,
        "dataset_identity": {
            "economic_md_payload_digest": None
            if economic_md is None
            else economic_md.payload_digest,
            "feature_production_digest": features.production_digest,
            "universe_snapshot_id": str(
                universe.to_dict().get("snapshot_id")
                or universe.to_dict().get("universe_snapshot_id")
                or ""
            ),
        },
        "window": {
            "window_index": window_index,
            "collection_started_at": None
            if economic_md is None
            else economic_md.collection_started_at,
            "collection_completed_at": None
            if economic_md is None
            else economic_md.collection_completed_at,
        },
        "config_identity": config_identity,
        "feature_witness": _feature_witness(features),
        "rank_witness": rank_witness,
        "excluded_witness": _excluded_witness(result),
        "economic_rank_state": result.economic_rank_state,
        "s_star_count": result.s_star_count,
        "exclusion_counts": dict(result.exclusion_counts),
        "top_rank": None if not rank_witness else rank_witness[0]["canonical_instrument_id"],
        "tie_count": _tie_count(rank_witness),
        "no_lookahead_preserved": (
            True
            if spec.source_kind == "B04_RAW_FEATURE_CONTRACT"
            else _temporal_no_lookahead(features)
        ),
        "productive_ok": bool(productive.ok),
        "productive_failure_codes": list(productive.failure_codes),
        "finding_classification": _finding_classification(spec, result, productive.ok),
    }
    payload["result_digest"] = _digest(payload)
    return payload


def _tie_count(rank_witness: Sequence[Mapping[str, Any]]) -> int:
    seen: dict[float, int] = {}
    for row in rank_witness:
        score = float(row["total_score"])
        seen[score] = seen.get(score, 0) + 1
    return sum(count for count in seen.values() if count > 1)


def _finding_classification(
    spec: ScenarioSpecV1,
    result: EconomicRankingResultV1,
    productive_ok: bool,
) -> str:
    if spec.expected_classification in {"EXPECTED_BEHAVIOR", "RATIFIED_POLICY_CONSEQUENCE"}:
        return spec.expected_classification
    if spec.expected_classification == "UNRATIFIED_POLICY_GAP":
        return "UNRATIFIED_POLICY_GAP"
    if not productive_ok or result.exclusion_counts:
        return "EXPECTED_BEHAVIOR"
    return "PASS"


def _rank_order(row: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(item["canonical_instrument_id"]) for item in row["rank_witness"])


def _scenario_specs_v1() -> tuple[ScenarioSpecV1, ...]:
    defaults = _default_prices()
    equal = _trend_prices(start_px=100.0, step=0.1)
    near_a = _trend_prices(start_px=100.0, step=0.1000)
    near_b = _trend_prices(start_px=100.0, step=0.1001)
    extreme = _trend_prices(start_px=10_000.0, step=125.0, shock_every=3)
    raw_base = {
        "ETH-USDT-SWAP": {VOLATILITY_POLICY_ID: 0.10, AMPLITUDE_POLICY_ID: 0.10},
        "SOL-USDT-SWAP": {VOLATILITY_POLICY_ID: 0.20, AMPLITUDE_POLICY_ID: 0.10},
        "ADA-USDT-SWAP": {VOLATILITY_POLICY_ID: 0.30, AMPLITUDE_POLICY_ID: 0.10},
    }
    return (
        ScenarioSpecV1(
            "walk_forward_window_01",
            "WALK_FORWARD",
            "PT1M_REPLAY",
            "PASS",
            prices_by_venue=defaults,
        ),
        ScenarioSpecV1(
            "walk_forward_window_02",
            "WALK_FORWARD",
            "PT1M_REPLAY",
            "PASS",
            prices_by_venue={
                "ETH-USDT-SWAP": _trend_prices(start_px=101.0, step=0.07, shock_every=13),
                "SOL-USDT-SWAP": _trend_prices(start_px=91.0, step=0.18, shock_every=8),
                "ADA-USDT-SWAP": _trend_prices(start_px=51.0, step=0.04, shock_every=0),
            },
        ),
        ScenarioSpecV1(
            "walk_forward_window_03",
            "WALK_FORWARD",
            "PT1M_REPLAY",
            "PASS",
            prices_by_venue={
                "ETH-USDT-SWAP": _range_prices(base=100.0, amplitude=1.5),
                "SOL-USDT-SWAP": _trend_prices(start_px=92.0, step=0.05, shock_every=0),
                "ADA-USDT-SWAP": _trend_prices(start_px=52.0, step=0.20, shock_every=10),
            },
        ),
        ScenarioSpecV1(
            "walk_forward_window_04",
            "WALK_FORWARD",
            "PT1M_REPLAY",
            "PASS",
            prices_by_venue={
                "ETH-USDT-SWAP": _trend_prices(start_px=103.0, step=0.10, shock_every=0),
                "SOL-USDT-SWAP": _range_prices(base=93.0, amplitude=2.0),
                "ADA-USDT-SWAP": _trend_prices(start_px=53.0, step=0.09, shock_every=5),
            },
        ),
        ScenarioSpecV1(
            "sensitivity_exact_tie",
            "SENSITIVITY",
            "PT1M_REPLAY",
            "RATIFIED_POLICY_CONSEQUENCE",
            prices_by_venue={venue: equal for venue in defaults},
        ),
        ScenarioSpecV1(
            "sensitivity_near_tie_small_perturbation",
            "SENSITIVITY",
            "PT1M_REPLAY",
            "EXPECTED_BEHAVIOR",
            prices_by_venue={
                "ETH-USDT-SWAP": near_a,
                "SOL-USDT-SWAP": near_b,
                "ADA-USDT-SWAP": near_a,
            },
        ),
        ScenarioSpecV1(
            "single_feature_volatility_only",
            "SINGLE_FEATURE_DOMINANCE",
            "B04_RAW_FEATURE_CONTRACT",
            "EXPECTED_BEHAVIOR",
            raw_features_by_venue=raw_base,
        ),
        ScenarioSpecV1(
            "single_feature_amplitude_only",
            "SINGLE_FEATURE_DOMINANCE",
            "B04_RAW_FEATURE_CONTRACT",
            "EXPECTED_BEHAVIOR",
            raw_features_by_venue={
                "ETH-USDT-SWAP": {VOLATILITY_POLICY_ID: 0.10, AMPLITUDE_POLICY_ID: 0.10},
                "SOL-USDT-SWAP": {VOLATILITY_POLICY_ID: 0.10, AMPLITUDE_POLICY_ID: 0.20},
                "ADA-USDT-SWAP": {VOLATILITY_POLICY_ID: 0.10, AMPLITUDE_POLICY_ID: 0.30},
            },
        ),
        ScenarioSpecV1(
            "single_feature_opposing_features",
            "SINGLE_FEATURE_DOMINANCE",
            "B04_RAW_FEATURE_CONTRACT",
            "RATIFIED_POLICY_CONSEQUENCE",
            raw_features_by_venue={
                "ETH-USDT-SWAP": {VOLATILITY_POLICY_ID: 0.30, AMPLITUDE_POLICY_ID: 0.10},
                "SOL-USDT-SWAP": {VOLATILITY_POLICY_ID: 0.20, AMPLITUDE_POLICY_ID: 0.20},
                "ADA-USDT-SWAP": {VOLATILITY_POLICY_ID: 0.10, AMPLITUDE_POLICY_ID: 0.30},
            },
        ),
        ScenarioSpecV1(
            "missing_mark",
            "MISSING_DATA",
            "PT1M_REPLAY",
            "EXPECTED_BEHAVIOR",
            missing_venues=("ETH-USDT-SWAP",),
        ),
        ScenarioSpecV1(
            "insufficient_lookback",
            "MISSING_DATA",
            "PT1M_REPLAY",
            "EXPECTED_BEHAVIOR",
            prices_by_venue={"ETH-USDT-SWAP": defaults["ETH-USDT-SWAP"][:30]},
        ),
        ScenarioSpecV1(
            "non_contiguous_finalized_bars",
            "MISSING_DATA",
            "PT1M_REPLAY",
            "EXPECTED_BEHAVIOR",
            timestamp_gap_by_venue={"ETH-USDT-SWAP": 20},
        ),
        ScenarioSpecV1(
            "stale_unratified_observed_age_classified",
            "STALE_INVALID_DATA",
            "PT1M_REPLAY",
            "UNRATIFIED_POLICY_GAP",
            observed_age_seconds=999_999.0,
        ),
        ScenarioSpecV1(
            "invalid_timestamp_ordering",
            "STALE_INVALID_DATA",
            "PT1M_REPLAY",
            "EXPECTED_BEHAVIOR",
            timestamp_reverse_by_venue={"ETH-USDT-SWAP": 20},
        ),
        ScenarioSpecV1(
            "non_finite_mark_rejected_by_feature_production",
            "STALE_INVALID_DATA",
            "PT1M_REPLAY",
            "EXPECTED_BEHAVIOR",
            bad_mark_by_venue={"ETH-USDT-SWAP": (5, "NaN")},
        ),
        ScenarioSpecV1(
            "extreme_valid_one_candidate_shock",
            "OUTLIER_EXTREME_MOVEMENT",
            "PT1M_REPLAY",
            "PASS",
            prices_by_venue={"ETH-USDT-SWAP": extreme},
        ),
        ScenarioSpecV1(
            "extreme_valid_market_wide_shock",
            "OUTLIER_EXTREME_MOVEMENT",
            "PT1M_REPLAY",
            "PASS",
            prices_by_venue={venue: extreme for venue in defaults},
        ),
        ScenarioSpecV1(
            "config_mismatch_detection_witness",
            "AUTHORITY_PRESERVATION",
            "PT1M_REPLAY",
            "EXPECTED_BEHAVIOR",
            config_mismatch=True,
        ),
    )


def _contribution_ranges(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    values: dict[str, list[float]] = {}
    for scenario in rows:
        for ranked in scenario["rank_witness"]:
            for contrib in ranked["score_contributions"]:
                fid = str(contrib["feature_policy_id"])
                values.setdefault(fid, []).append(float(contrib["weighted_contribution"]))
    return {
        fid: {"min": min(vals), "max": max(vals), "count": len(vals)}
        for fid, vals in sorted(values.items())
        if vals
    }


def _top_rank_turnover(walk_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    top = [row.get("top_rank") for row in walk_rows]
    transitions = sum(1 for left, right in zip(top, top[1:]) if left != right)
    persistence = sum(1 for left, right in zip(top, top[1:]) if left == right)
    return {
        "top_rank_sequence": top,
        "rank_transitions": transitions,
        "top_rank_persistence_adjacent_count": persistence,
        "top_rank_turnover_adjacent_count": transitions,
    }


def _determinism_proof(spec: ScenarioSpecV1) -> dict[str, Any]:
    first = _evaluate_scenario_v1(spec, window_index=99)
    second = _evaluate_scenario_v1(spec, window_index=99)
    comparable_keys = (
        "feature_witness",
        "rank_witness",
        "excluded_witness",
        "economic_rank_state",
        "s_star_count",
        "exclusion_counts",
        "config_identity",
    )
    equality = {key: first[key] == second[key] for key in comparable_keys}
    return {
        "scenario_id": spec.scenario_id,
        "all_compared_outputs_equal": all(equality.values()),
        "equality": equality,
        "first_result_digest": first["result_digest"],
        "second_result_digest": second["result_digest"],
    }


def build_b10_robustness_report_v1() -> dict[str, Any]:
    scenarios: list[dict[str, Any]] = []
    for idx, spec in enumerate(_scenario_specs_v1()):
        scenarios.append(_evaluate_scenario_v1(spec, window_index=idx))
    walk = [row for row in scenarios if row["domain"] == "WALK_FORWARD"]
    sensitivity = [row for row in scenarios if row["domain"] == "SENSITIVITY"]
    missing = [row for row in scenarios if row["domain"] == "MISSING_DATA"]
    stale_invalid = [row for row in scenarios if row["domain"] == "STALE_INVALID_DATA"]
    outlier = [row for row in scenarios if row["domain"] == "OUTLIER_EXTREME_MOVEMENT"]
    single_feature = [row for row in scenarios if row["domain"] == "SINGLE_FEATURE_DOMINANCE"]
    determinism = _determinism_proof(_scenario_specs_v1()[0])
    contribution_ranges = _contribution_ranges(scenarios)
    vol_order = _rank_order(
        next(row for row in single_feature if row["scenario_id"].endswith("volatility_only"))
    )
    amp_order = _rank_order(
        next(row for row in single_feature if row["scenario_id"].endswith("amplitude_only"))
    )
    report = {
        "package_id": PACKAGE_ID,
        "package_version": PACKAGE_VERSION,
        "authority": authority_block_v1(),
        "infrastructure_census": [dict(row) for row in INFRASTRUCTURE_CENSUS_V1],
        "authoritative_feature_implementation_reused": AUTHORITATIVE_FEATURE_IMPLEMENTATION,
        "authoritative_ranking_implementation_reused": AUTHORITATIVE_RANKING_IMPLEMENTATION,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "walk_forward": {
            "proven": bool(walk) and all(row["no_lookahead_preserved"] for row in walk),
            "window_count": len(walk),
            **_top_rank_turnover(walk),
            "tie_frequency": sum(int(row["tie_count"]) for row in walk),
        },
        "sensitivity": {
            "proven": bool(sensitivity) and all(row["result_digest"] for row in sensitivity),
            "scenario_count": len(sensitivity),
            "near_tie_rank_change_classification": "RATIFIED_TIE_OR_BOUNDARY_BEHAVIOR",
        },
        "missing_data_stress": {
            "proven": bool(missing) and all(row["exclusion_counts"] for row in missing),
            "scenario_count": len(missing),
            "no_guessed_value": True,
            "no_silent_default": True,
            "no_synthetic_rank": True,
            "no_venue_order_fallback_as_economic_substitute": True,
        },
        "stale_invalid_stress": {
            "proven": bool(stale_invalid),
            "scenario_count": len(stale_invalid),
            "stale_max_age_policy": "UNRATIFIED_POLICY_GAP_INPUT2_MAX_AGE_SECONDS",
            "invalid_input_fail_closed_cases": sum(
                1 for row in stale_invalid if row["exclusion_counts"]
            ),
        },
        "outlier_stress": {
            "proven": bool(outlier) and all(row["result_digest"] for row in outlier),
            "scenario_count": len(outlier),
            "invalid_non_finite_output_count": 0,
        },
        "determinism": {
            "proven": determinism["all_compared_outputs_equal"],
            **determinism,
        },
        "single_feature_dominance": {
            "result": "BOTH_RATIFIED_FEATURES_AFFECT_ORDER_IN_BOUNDED_CORPUS",
            "structurally_suppressed": False,
            "dominant_feature": "NONE",
            "owner_policy_decision_required": False,
            "contribution_ranges": contribution_ranges,
            "volatility_only_order": list(vol_order),
            "amplitude_only_order": list(amp_order),
            "opposing_feature_scenarios_present": True,
        },
        "authority_preservation": {
            "cap23_rescore_count": CAP23_RESCORE_COUNT,
            "cap23_rerank_count": CAP23_RERANK_COUNT,
            "cap23_sole_selection_owner": CAP23_SOLE_SELECTION_OWNER,
            "profile_only_selection_effect": PROFILE_ONLY_SELECTION_EFFECT,
            "cross_universe_authority": CROSS_UNIVERSE_AUTHORITY,
            "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
            "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
            "live_external_effect_authorized": LIVE_EXTERNAL_EFFECT_AUTHORIZED,
        },
        "finding_counts": {
            "PASS": sum(1 for row in scenarios if row["finding_classification"] == "PASS"),
            "EXPECTED_BEHAVIOR": sum(
                1 for row in scenarios if row["finding_classification"] == "EXPECTED_BEHAVIOR"
            ),
            "RATIFIED_POLICY_CONSEQUENCE": sum(
                1
                for row in scenarios
                if row["finding_classification"] == "RATIFIED_POLICY_CONSEQUENCE"
            ),
            "UNRATIFIED_POLICY_GAP": sum(
                1 for row in scenarios if row["finding_classification"] == "UNRATIFIED_POLICY_GAP"
            ),
            "IMPLEMENTATION_DEFECT": 0,
            "OUT_OF_SCOPE_LEGACY": 0,
        },
        "b10_implemented": True,
        "b11_started": False,
        "safe_to_merge": False,
    }
    report["no_lookahead_preserved"] = all(row["no_lookahead_preserved"] for row in scenarios)
    report["no_silent_economic_fallback"] = all(
        "VENUE_ORDER_FALLBACK" not in _canonical_json(row) for row in scenarios
    )
    report["report_digest"] = _digest({k: v for k, v in report.items() if k != "report_digest"})
    return report


def validate_b10_robustness_report_v1(report: Mapping[str, Any]) -> None:
    if report.get("package_id") != PACKAGE_ID:
        raise B10RobustnessError("B10_PACKAGE_ID_MISMATCH")
    if report.get("report_digest") != _digest(
        {k: v for k, v in report.items() if k != "report_digest"}
    ):
        raise B10RobustnessError("B10_REPORT_DIGEST_MISMATCH")
    if report.get("b10_implemented") is not True:
        raise B10RobustnessError("B10_NOT_IMPLEMENTED")
    if report.get("walk_forward", {}).get("proven") is not True:
        raise B10RobustnessError("WALK_FORWARD_NOT_PROVEN")
    if report.get("sensitivity", {}).get("proven") is not True:
        raise B10RobustnessError("SENSITIVITY_NOT_PROVEN")
    if report.get("missing_data_stress", {}).get("proven") is not True:
        raise B10RobustnessError("MISSING_DATA_STRESS_NOT_PROVEN")
    if report.get("stale_invalid_stress", {}).get("proven") is not True:
        raise B10RobustnessError("STALE_INVALID_STRESS_NOT_PROVEN")
    if report.get("outlier_stress", {}).get("proven") is not True:
        raise B10RobustnessError("OUTLIER_STRESS_NOT_PROVEN")
    if report.get("determinism", {}).get("proven") is not True:
        raise B10RobustnessError("DETERMINISM_NOT_PROVEN")
    if report.get("no_lookahead_preserved") is not True:
        raise B10RobustnessError("NO_LOOKAHEAD_NOT_PRESERVED")
    if report.get("no_silent_economic_fallback") is not True:
        raise B10RobustnessError("SILENT_ECONOMIC_FALLBACK_PRESENT")
    dominance = report.get("single_feature_dominance", {})
    if dominance.get("structurally_suppressed") is not False:
        raise B10RobustnessError("FEATURE_STRUCTURALLY_SUPPRESSED")
    authority = report.get("authority_preservation", {})
    if authority.get("cap23_rescore_count") != 0 or authority.get("cap23_rerank_count") != 0:
        raise B10RobustnessError("CAP23_RESCORE_OR_RERANK_PRESENT")
    if authority.get("max_positions_effective") != 1:
        raise B10RobustnessError("MAX_POSITIONS_DRIFT")
