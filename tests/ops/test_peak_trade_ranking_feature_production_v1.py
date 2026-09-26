"""B05 Cap-2.1 ranking feature production contracts and proofs."""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path

import pytest

from src.ops.economic_md_input_producer_v1.models_v1 import (
    EconomicMdInputSnapshotV1,
    EconomicMdInstrumentRawInputV1,
    FinalizedPt1mMarkObservationV1,
    UnresolvedValidityDimensionsV1,
    authority_block as economic_md_authority_block,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (
    CAPABILITY_ID as EMD_CAPABILITY_ID,
    PRODUCER_VERSION as EMD_PRODUCER_VERSION,
    SCHEMA_VERSION as EMD_SCHEMA_VERSION,
)
from src.ops.peak_trade_ranking_feature_contract_v1 import (
    INPUT2_MAX_AGE_SECONDS,
    INPUT2_MAX_AGE_SECONDS_RATIFIED,
    RankingFeatureValueState,
)
from src.ops.peak_trade_ranking_feature_production_v1 import (
    classify_peak_trade_ranking_feature_production_v1,
    compute_b03_ratified_raw_features_pure_v1,
    produce_ranking_feature_production_snapshot_v1,
    produce_raw_ranking_features_for_instrument_v1,
    validate_ranking_feature_production_snapshot_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.constants_v1 import (
    B05_IMPLEMENTED,
    CALL_GRAPH,
    CAPABILITY_ID,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    FORBIDDEN_OUTPUT_FIELDS,
    MARK_COUNT,
    OBSERVATION_WINDOW_ID,
    PRODUCTIVE_ECONOMIC_RANK_ACTIVATION,
    ECONOMIC_RANK_ACTIVATED,
    RANKING_ACTIVATION,
    SELECTION_AUTHORITY_CREATED,
    BINDING_EFFECT,
)
from src.ops.peak_trade_ranking_feature_production_v1.pure_compute_v1 import (
    population_sigma_log_returns_v1,
    pt1m_mid_relative_range_v1,
)
from src.ops.peak_trade_ranking_matrix_policy_v1 import (
    AMPLITUDE_POLICY_ID,
    AMPLITUDE_UNITS,
    B05_IMPLEMENTED as MATRIX_B05_IMPLEMENTED,
    VOLATILITY_POLICY_ID,
    VOLATILITY_UNITS,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / "src/ops/peak_trade_ranking_feature_production_v1"
BASE_TS_MS = 1_700_000_000_000
SOURCE_CLASS = "VENUE_NATIVE_OKX_PUBLIC_HISTORY_MARK_PRICE_CANDLES_PT1M_CONFIRM_1"
SOURCE_ENDPOINT = "/api/v5/market/history-mark-price-candles"


def _marks(
    n: int = MARK_COUNT,
    *,
    start_px: float = 100.0,
    step: float = 1.0,
    gap_at: int | None = None,
    bad_px_at: int | None = None,
    bad_px: str = "0",
    unfinalized_at: int | None = None,
) -> tuple[FinalizedPt1mMarkObservationV1, ...]:
    rows: list[FinalizedPt1mMarkObservationV1] = []
    for i in range(n):
        ts = BASE_TS_MS + i * 60_000
        if gap_at is not None and i >= gap_at:
            ts += 60_000
        px = bad_px if bad_px_at == i else str(start_px + i * step)
        status = "FINALIZED" if unfinalized_at != i else "OPEN"
        rows.append(
            FinalizedPt1mMarkObservationV1(
                mark_px=px,
                event_timestamp=str(ts),
                receive_or_capture_timestamp=str(BASE_TS_MS + 60_000),
                finalization_status=status,
                source_class=SOURCE_CLASS,
                source_endpoint=SOURCE_ENDPOINT,
            )
        )
    return tuple(rows)


def _instrument(
    *,
    cid: str = "okx_eea:ETH-USDT-SWAP",
    vid: str = "ETH-USDT-SWAP",
    marks: tuple[FinalizedPt1mMarkObservationV1, ...] | None = None,
) -> EconomicMdInstrumentRawInputV1:
    row = EconomicMdInstrumentRawInputV1(
        canonical_instrument_id=cid,
        venue_native_id=vid,
        raw_input_eligible=True,
        exclusion_reason_codes=(),
        finalized_pt1m_marks=_marks() if marks is None else marks,
        ticker=None,
        unresolved_validity_dimensions=UnresolvedValidityDimensionsV1(
            locked_market="NOT_OBSERVED",
            near_zero_spread="RAW_OBSERVATION_UNRESOLVED_UNRATIFIED_BOUND",
            stale_seconds="UNRATIFIED_NUMERIC_BOUND",
            collection_skew="UNRATIFIED_NUMERIC_BOUND",
        ),
        raw_input_digest="",
        provenance={"source": "test"},
    )
    return row.with_raw_input_digest()


def _economic_snapshot(
    instruments: tuple[EconomicMdInstrumentRawInputV1, ...],
) -> EconomicMdInputSnapshotV1:
    ordered = tuple(sorted(instruments, key=lambda r: r.canonical_instrument_id))
    snap = EconomicMdInputSnapshotV1(
        schema_version=EMD_SCHEMA_VERSION,
        producer_version=EMD_PRODUCER_VERSION,
        capability_id=EMD_CAPABILITY_ID,
        economic_input_snapshot_id="emd_test_snap_1",
        universe_snapshot_reference={"universe_snapshot_id": "gfu_test"},
        collection_cycle_identity="emd_cycle_test",
        collection_started_at="2026-09-26T00:00:00Z",
        collection_completed_at="2026-09-26T00:01:00Z",
        instrument_count_requested=len(ordered),
        instrument_count_rankable_raw_input=sum(1 for row in ordered if row.raw_input_eligible),
        payload_digest="",
        provenance={"test": True},
        instruments=ordered,
        authority=economic_md_authority_block(),
        call_graph=(),
        failure_codes=(),
    )
    return snap.with_payload_digest()


def test_classify_and_pins() -> None:
    summary = classify_peak_trade_ranking_feature_production_v1()
    assert summary["b05_implemented"] is True
    assert summary["capability_id"] == CAPABILITY_ID
    assert MATRIX_B05_IMPLEMENTED is True
    assert B05_IMPLEMENTED is True
    assert PRODUCTIVE_ECONOMIC_RANK_ACTIVATION is False
    assert ECONOMIC_RANK_ACTIVATED is False
    assert RANKING_ACTIVATION is False
    assert SELECTION_AUTHORITY_CREATED is False
    assert BINDING_EFFECT is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert INPUT2_MAX_AGE_SECONDS_RATIFIED is False
    assert INPUT2_MAX_AGE_SECONDS == "UNRATIFIED"


def test_produces_b03_features_from_canonical_marks() -> None:
    snap = produce_ranking_feature_production_snapshot_v1(_economic_snapshot((_instrument(),)))
    validate_ranking_feature_production_snapshot_v1(snap)
    assert snap.instrument_count_feature_ready == 1
    row = snap.instruments[0]
    assert row.feature_production_ready is True
    assert row.raw_features[0].feature_policy_id == VOLATILITY_POLICY_ID
    assert row.raw_features[1].feature_policy_id == AMPLITUDE_POLICY_ID
    assert row.raw_features[0].units == VOLATILITY_UNITS
    assert row.raw_features[1].units == AMPLITUDE_UNITS
    assert row.raw_features[0].observation_window_id == OBSERVATION_WINDOW_ID
    assert row.raw_features[0].state == RankingFeatureValueState.READY
    assert row.raw_features[1].state == RankingFeatureValueState.READY
    assert row.mark_window_provenance is not None
    assert row.mark_window_provenance.source_class == SOURCE_CLASS
    assert row.mark_window_provenance.mark_count == MARK_COUNT


def test_deterministic_repeat_identical_inputs() -> None:
    emd = _economic_snapshot((_instrument(),))
    a = produce_ranking_feature_production_snapshot_v1(emd)
    b = produce_ranking_feature_production_snapshot_v1(emd)
    assert a.to_dict() == b.to_dict()
    assert a.production_digest == b.production_digest
    marks = tuple(str(100 + i) for i in range(MARK_COUNT))
    f1 = compute_b03_ratified_raw_features_pure_v1(marks)
    f2 = compute_b03_ratified_raw_features_pure_v1(marks)
    assert [x.to_dict() for x in f1] == [x.to_dict() for x in f2]


def test_pure_compute_matches_manual_formulas() -> None:
    marks = tuple(str(100 + i) for i in range(MARK_COUNT))
    logs = [math.log((100 + i + 1) / (100 + i)) for i in range(60)]
    mean = sum(logs) / 60.0
    var = sum((x - mean) ** 2 for x in logs) / 60.0
    expected_vol = math.sqrt(var)
    p_min, p_max = 100.0, 160.0
    expected_amp = (p_max - p_min) / ((p_max + p_min) / 2.0)
    vol = float(population_sigma_log_returns_v1(marks))
    amp = float(pt1m_mid_relative_range_v1(marks))
    assert abs(vol - expected_vol) < 1e-12
    assert abs(amp - expected_amp) < 1e-12


def test_b04_dto_population_and_provenance() -> None:
    snap = produce_ranking_feature_production_snapshot_v1(
        _economic_snapshot((_instrument(),)),
        observed_age_seconds=42.0,
    )
    assert snap.input2_provenance.observed_age_seconds == 42.0
    assert snap.input2_provenance.input2_max_age_seconds == "UNRATIFIED"
    assert snap.input2_provenance.input2_max_age_seconds_ratified is False
    assert snap.policy_identity.ranking_policy_id == "PEAK_TRADE_RANKING_MATRIX_POLICY_V1"
    for row in snap.instruments[0].raw_features:
        assert row.raw_feature_normalization == "NONE"


def test_missing_marks_fail_closed() -> None:
    produced = produce_raw_ranking_features_for_instrument_v1(_instrument(marks=()))
    assert produced.feature_production_ready is False
    assert all(row.state == RankingFeatureValueState.MISSING for row in produced.raw_features)
    assert all(row.raw_value is None for row in produced.raw_features)


def test_insufficient_warmup_fail_closed() -> None:
    produced = produce_raw_ranking_features_for_instrument_v1(_instrument(marks=_marks(30)))
    assert produced.feature_production_ready is False
    assert all(
        row.state == RankingFeatureValueState.INCOMPLETE_WARMUP for row in produced.raw_features
    )


def test_invalid_nonpositive_and_gap_fail_closed() -> None:
    bad = produce_raw_ranking_features_for_instrument_v1(
        _instrument(marks=_marks(bad_px_at=10, bad_px="0"))
    )
    assert bad.feature_production_ready is False
    assert all(row.state == RankingFeatureValueState.INVALID for row in bad.raw_features)
    assert all(row.raw_value is None for row in bad.raw_features)

    gap = produce_raw_ranking_features_for_instrument_v1(_instrument(marks=_marks(gap_at=20)))
    assert gap.feature_production_ready is False
    assert all(row.state == RankingFeatureValueState.INVALID for row in gap.raw_features)

    unfinal = produce_raw_ranking_features_for_instrument_v1(
        _instrument(marks=_marks(unfinalized_at=5))
    )
    assert unfinal.feature_production_ready is False
    assert all(row.state == RankingFeatureValueState.INVALID for row in unfinal.raw_features)


def test_nan_and_none_like_marks_not_valid_features() -> None:
    for bad in ("nan", "NaN", "inf", "-inf", ""):
        produced = produce_raw_ranking_features_for_instrument_v1(
            _instrument(marks=_marks(bad_px_at=3, bad_px=bad))
        )
        assert produced.feature_production_ready is False
        assert all(row.raw_value is None for row in produced.raw_features)


def test_flat_prices_zero_features_are_ready_not_guessed() -> None:
    marks = _marks(start_px=100.0, step=0.0)
    produced = produce_raw_ranking_features_for_instrument_v1(_instrument(marks=marks))
    assert produced.feature_production_ready is True
    assert produced.raw_features[0].raw_value == 0.0
    assert produced.raw_features[1].raw_value == 0.0


def test_no_rank_order_selection_or_binding_fields() -> None:
    snap = produce_ranking_feature_production_snapshot_v1(
        _economic_snapshot(
            (
                _instrument(cid="okx_eea:AAA-USDT-SWAP", vid="AAA-USDT-SWAP"),
                _instrument(
                    cid="okx_eea:ZZZ-USDT-SWAP", vid="ZZZ-USDT-SWAP", marks=_marks(start_px=200.0)
                ),
            )
        )
    )
    validate_ranking_feature_production_snapshot_v1(snap)
    payload = snap.to_dict()
    for forbidden in FORBIDDEN_OUTPUT_FIELDS:
        assert forbidden not in payload
        for instrument in payload["instruments"]:
            assert forbidden not in instrument
    # Instrument order is identity-sorted, not economic rank.
    assert [r["canonical_instrument_id"] for r in payload["instruments"]] == sorted(
        r["canonical_instrument_id"] for r in payload["instruments"]
    )
    assert snap.authority["CAP23_SOLE_SELECTION_OWNER"] is True
    assert snap.authority["PRODUCTIVE_ECONOMIC_RANK_ACTIVATION"] is False


def test_no_cross_sectional_normalization_in_b05() -> None:
    snap = produce_ranking_feature_production_snapshot_v1(_economic_snapshot((_instrument(),)))
    text = json.dumps(snap.to_dict())
    assert "normalized_features" not in text
    assert "balanced_movement_score" not in text
    assert "midrank" not in text
    assert "percentile" not in text


def test_config_pins_and_docs_token() -> None:
    config = json.loads(
        (REPO / "config/governance/peak_trade_ranking_feature_production_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert config["b05_implemented"] is True
    assert config["input2_max_age_seconds"] == "UNRATIFIED"
    assert config["input2_max_age_seconds_ratified"] is False
    assert config["productive_economic_rank_activation"] is False
    assert config["cross_sectional_normalization_in_b05"] is False
    docs = (REPO / "docs/ops/specs/PEAK_TRADE_RANKING_FEATURE_PRODUCTION_V1.md").read_text(
        encoding="utf-8"
    )
    assert "DOCS_TOKEN_PEAK_TRADE_RANKING_FEATURE_PRODUCTION_V1" in docs
    assert "INPUT2_MAX_AGE_SECONDS_RATIFIED=false" in docs


def test_call_graph_present_and_forbidden_imports_absent() -> None:
    assert "compute_b03_ratified_raw_features_pure_v1" in CALL_GRAPH
    paths = sorted(PKG.glob("*.py"))
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for module in modules:
                lowered = module.lower()
                for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
                    assert forbidden.lower() not in lowered


def test_productive_ranking_runtime_still_unwired() -> None:
    from src.ops.productive_futures_ranking_producer_v1 import constants_v1 as ranking_c

    producer = (REPO / "src/ops/productive_futures_ranking_producer_v1/producer_v1.py").read_text(
        encoding="utf-8"
    )
    ranking = (REPO / "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py").read_text(
        encoding="utf-8"
    )
    text = producer + ranking
    assert "peak_trade_ranking_feature_production_v1" not in text
    assert ranking_c.RANKING_POLICY_ID == "productive_futures_universe_structural_ranking_v1"


def test_round_trip_snapshot() -> None:
    snap = produce_ranking_feature_production_snapshot_v1(_economic_snapshot((_instrument(),)))
    restored = type(snap).from_dict(json.loads(json.dumps(snap.to_dict())))
    assert restored.to_dict() == snap.to_dict()
    validate_ranking_feature_production_snapshot_v1(restored)
