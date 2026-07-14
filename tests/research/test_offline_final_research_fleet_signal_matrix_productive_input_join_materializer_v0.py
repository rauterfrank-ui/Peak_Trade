"""Contract tests for offline final research fleet signal matrix productive join v0."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.signal_matrix_productive_contract_v0 import (
    AUTHORITY_EFFECT,
    EXPECTED_FLEET_SIGNAL_ORDER,
    ProductiveSignalJoinRejectionReason,
    compute_signal_matrix_digest_v0,
    validate_requested_signal_set_v0,
)
from research.linear_evidence.signal_orthogonality import analyze_signal_orthogonality
from src.research.offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0 import (
    RUNTIME_EFFECT,
    MaterializationStatus,
    join_productive_signal_matrix_v0,
    materialize_offline_final_research_fleet_signal_matrix_v0,
    materializer_to_contract_roundtrip_pass_v0,
    panel_bars_to_strategy_dataframe_v0,
    serialize_signal_matrix_rows_v0,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1

REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER_MODULE = (
    REPO_ROOT
    / "src/research/offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0.py"
)
CONTRACT_MODULE = REPO_ROOT / "src/research/linear_evidence/signal_matrix_productive_contract_v0.py"
RUNNER_MODULE = (
    REPO_ROOT
    / "scripts/research/offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0.py"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
STAGING_ROOT = (
    ARCHIVE_ROOT / "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1"
)
FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "requests",
    "httpx",
    "urllib.request",
)


def _panel_bar(ts: str, close: float) -> PanelBarV1:
    value = f"{close:.8f}"
    return PanelBarV1(
        instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
        timestamp_utc=ts,
        open=value,
        high=value,
        low=value,
        close=value,
        volume="1000.0",
        is_final=True,
    )


def _synthetic_series(count: int = 90) -> InstrumentPanelSeriesV1:
    start = pd.Timestamp("2024-05-01T00:00:00Z", tz="UTC")
    bars = tuple(
        _panel_bar(
            (start + pd.Timedelta(hours=index + 1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            100.0 + 5.0 * math.sin(index / 8.0) + float(index) * 0.05,
        )
        for index in range(count)
    )
    return InstrumentPanelSeriesV1(
        instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
        native_instrument_id="ETH-USDT-SWAP",
        bars=bars,
        series_digest="0" * 64,
    )


def _signal_row(
    *,
    instrument_id: str = "inst-a",
    decision_time: str = "2024-05-31T10:00:00Z",
    feature_time: str = "2024-05-31T09:00:00Z",
    signal_name: str = "trend_following",
    signal_value: float = 1.0,
):
    from src.research.offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0 import (
        SignalSeriesRowV0,
    )

    return SignalSeriesRowV0(
        instrument_id=instrument_id,
        decision_time=decision_time,
        feature_time=feature_time,
        signal_name=signal_name,
        signal_value=signal_value,
    )


def test_ratified_three_fleet_signals_bound_exactly() -> None:
    assert (
        validate_requested_signal_set_v0(list(EXPECTED_FLEET_SIGNAL_ORDER))
        == EXPECTED_FLEET_SIGNAL_ORDER
    )


def test_unknown_or_extra_signal_fail_closed() -> None:
    with pytest.raises(ValueError, match=ProductiveSignalJoinRejectionReason.UNKNOWN_SIGNAL.value):
        validate_requested_signal_set_v0(["trend_following", "macd"])
    with pytest.raises(ValueError, match=ProductiveSignalJoinRejectionReason.EXTRA_SIGNAL.value):
        validate_requested_signal_set_v0(["trend_following", "bollinger_bands"])


def test_missing_productive_signal_source_fail_closed() -> None:
    with pytest.raises(
        ValueError, match=ProductiveSignalJoinRejectionReason.MISSING_SIGNAL_SOURCE.value
    ):
        validate_requested_signal_set_v0([])


def test_signal_column_order_stable() -> None:
    rows, _, _ = join_productive_signal_matrix_v0(
        {
            "trend_following": (_signal_row(signal_name="trend_following"),),
            "bollinger_bands": (_signal_row(signal_name="bollinger_bands", signal_value=0.0),),
            "momentum_1h": (_signal_row(signal_name="momentum_1h", signal_value=-1.0),),
        }
    )
    assert list(rows[0].keys())[-3:] == list(EXPECTED_FLEET_SIGNAL_ORDER)


def test_time_series_strictly_ascending_after_join() -> None:
    rows, _, _ = join_productive_signal_matrix_v0(
        {
            "trend_following": (
                _signal_row(
                    decision_time="2024-05-31T11:00:00Z", feature_time="2024-05-31T10:00:00Z"
                ),
                _signal_row(
                    decision_time="2024-05-31T10:00:00Z", feature_time="2024-05-31T09:00:00Z"
                ),
            ),
            "bollinger_bands": (
                _signal_row(
                    decision_time="2024-05-31T11:00:00Z",
                    feature_time="2024-05-31T10:00:00Z",
                    signal_name="bollinger_bands",
                ),
                _signal_row(
                    decision_time="2024-05-31T10:00:00Z",
                    feature_time="2024-05-31T09:00:00Z",
                    signal_name="bollinger_bands",
                ),
            ),
            "momentum_1h": (
                _signal_row(
                    decision_time="2024-05-31T11:00:00Z",
                    feature_time="2024-05-31T10:00:00Z",
                    signal_name="momentum_1h",
                ),
                _signal_row(
                    decision_time="2024-05-31T10:00:00Z",
                    feature_time="2024-05-31T09:00:00Z",
                    signal_name="momentum_1h",
                ),
            ),
        }
    )
    decision_times = [row["decision_time"] for row in rows]
    assert decision_times == sorted(decision_times)


def test_duplicate_timestamps_rejected_in_panel_conversion() -> None:
    bar = _panel_bar("2024-05-31T10:00:00Z", 100.0)
    with pytest.raises(
        ValueError, match=ProductiveSignalJoinRejectionReason.DUPLICATE_TIMESTAMP.value
    ):
        panel_bars_to_strategy_dataframe_v0((bar, bar))


def test_unfinalized_bars_excluded() -> None:
    bar = PanelBarV1(
        instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
        timestamp_utc="2024-05-31T10:00:00Z",
        open="1",
        high="1",
        low="1",
        close="1",
        volume="1",
        is_final=False,
    )
    frame = panel_bars_to_strategy_dataframe_v0((bar,))
    assert frame.empty


def test_lookahead_prevented_on_join() -> None:
    rows, dropped, _ = join_productive_signal_matrix_v0(
        {
            "trend_following": (
                _signal_row(
                    feature_time="2024-05-31T10:00:00Z", decision_time="2024-05-31T10:00:00Z"
                ),
            ),
            "bollinger_bands": (
                _signal_row(
                    feature_time="2024-05-31T09:00:00Z",
                    decision_time="2024-05-31T10:00:00Z",
                    signal_name="bollinger_bands",
                ),
            ),
            "momentum_1h": (
                _signal_row(
                    feature_time="2024-05-31T09:00:00Z",
                    decision_time="2024-05-31T10:00:00Z",
                    signal_name="momentum_1h",
                ),
            ),
        }
    )
    assert not rows
    assert dropped.get(ProductiveSignalJoinRejectionReason.INNER_JOIN_MISS.value, 0) >= 1


def test_missing_values_only_via_contract() -> None:
    _, dropped, _ = join_productive_signal_matrix_v0(
        {
            "trend_following": (_signal_row(),),
            "bollinger_bands": (),
            "momentum_1h": (_signal_row(signal_name="momentum_1h"),),
        }
    )
    assert ProductiveSignalJoinRejectionReason.INNER_JOIN_MISS.value in dropped


def test_no_fixture_proxy_synthetic_signal_names_required() -> None:
    assert EXPECTED_FLEET_SIGNAL_ORDER == ("bollinger_bands", "momentum_1h", "trend_following")


def test_authority_and_runtime_neutral() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"


def test_import_boundary_clean() -> None:
    for path in (MATERIALIZER_MODULE, CONTRACT_MODULE, RUNNER_MODULE):
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_IMPORT_PREFIXES:
            assert token not in source
        hits = scan_file_import_boundary(path, repo_root=REPO_ROOT)
        assert hits == []


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="archive staging unavailable")
def test_productive_materialization_sample_count_positive() -> None:
    result = materialize_offline_final_research_fleet_signal_matrix_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
    )
    assert result.status == MaterializationStatus.PASS
    assert len(result.rows) > 0
    assert set(EXPECTED_FLEET_SIGNAL_ORDER).issubset(result.rows[0].keys())


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="archive staging unavailable")
def test_materializer_to_contract_roundtrip_pass() -> None:
    result = materialize_offline_final_research_fleet_signal_matrix_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
    )
    assert materializer_to_contract_roundtrip_pass_v0(result.rows) is True


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="archive staging unavailable")
def test_second_materialization_diff_empty() -> None:
    first = materialize_offline_final_research_fleet_signal_matrix_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
    )
    second = materialize_offline_final_research_fleet_signal_matrix_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
    )
    assert serialize_signal_matrix_rows_v0(first.rows) == serialize_signal_matrix_rows_v0(
        second.rows
    )
    assert first.signal_matrix_digest == second.signal_matrix_digest


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="archive staging unavailable")
def test_signal_matrix_digest_stable() -> None:
    result = materialize_offline_final_research_fleet_signal_matrix_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
    )
    assert result.signal_matrix_digest == compute_signal_matrix_digest_v0(result.rows)


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="archive staging unavailable")
def test_orthogonality_consumer_accepts_materialized_rows() -> None:
    result = materialize_offline_final_research_fleet_signal_matrix_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
    )
    evidence = analyze_signal_orthogonality(list(result.rows), EXPECTED_FLEET_SIGNAL_ORDER)
    assert evidence.n_samples == len(result.rows)
    assert evidence.authority_effect == "NONE"
    assert evidence.runtime_effect == "NONE"


def test_governance_boundary_guard_still_green() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/governance/test_economic_diagnostic_optimization_boundary_guard_v0.py",
            "-q",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
