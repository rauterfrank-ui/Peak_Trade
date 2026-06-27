"""Source binding and digest tests for comparison_metric_input.v1."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from src.meta.learning_loop.comparison_metric_input_v1.models import ComparisonMetricInputError
from src.meta.learning_loop.comparison_metric_input_v1.source_binding import (
    binding_records_to_mapping,
    compute_equity_series_digest,
    compute_source_digest,
    compute_trade_ledger_digest,
    load_json_object,
    load_trades_from_parquet,
    serialize_binding_snapshot,
    sha256_file,
    verify_digest_matches_file,
    verify_source_ref,
)
from tests.meta.comparison_metric_input_v1_fixtures import (
    GOLDEN_EQUITY_SERIES_DIGEST,
    GOLDEN_SOURCE_DIGEST,
    GOLDEN_TRADE_LEDGER_DIGEST,
    build_backtest_run_dir,
    comparison_source_ref,
    write_equity_csv,
    write_trades_parquet,
)


def _equity_series() -> pd.Series:
    values = [10000.0, 10100.0, 10050.0, 10200.0, 10300.0, 10150.0, 10400.0]
    index = pd.date_range("2025-01-01", periods=len(values), freq="D")
    return pd.Series(values, index=index)


def test_compute_equity_series_digest_golden(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    write_equity_csv(run_dir)
    frame = pd.read_csv(run_dir / "equity.csv")
    equity = pd.Series(frame["equity"].values, index=pd.to_datetime(frame["timestamp"]))
    assert compute_equity_series_digest(equity) == GOLDEN_EQUITY_SERIES_DIGEST


def test_compute_trade_ledger_digest_golden() -> None:
    trades = [{"pnl": 100.0}, {"pnl": -50.0}, {"pnl": 75.0}, {"pnl": 25.0}]
    assert compute_trade_ledger_digest(trades) == GOLDEN_TRADE_LEDGER_DIGEST


def test_compute_source_digest_golden() -> None:
    digest = compute_source_digest(
        equity_series_digest=GOLDEN_EQUITY_SERIES_DIGEST,
        trade_ledger_digest=GOLDEN_TRADE_LEDGER_DIGEST,
    )
    assert digest == GOLDEN_SOURCE_DIGEST


def test_verify_source_ref_accepts_backtest_mapping(tmp_path) -> None:
    _, ref = build_backtest_run_dir(tmp_path)
    parsed = verify_source_ref(ref, expected_domain="BACKTEST")
    assert parsed.ref_type == "BACKTEST"


def test_verify_source_ref_rejects_domain_mismatch(tmp_path) -> None:
    _, ref = build_backtest_run_dir(tmp_path)
    with pytest.raises(ComparisonMetricInputError, match="must match domain"):
        verify_source_ref(ref, expected_domain="EXPERIMENT")


def test_verify_source_ref_rejects_invalid_digest(tmp_path) -> None:
    _, ref = build_backtest_run_dir(tmp_path)
    bad = dict(ref)
    bad["digest"] = "not-a-digest"
    with pytest.raises(ComparisonMetricInputError, match="lowercase sha256 hex"):
        verify_source_ref(bad, expected_domain="BACKTEST")


def test_load_trades_from_parquet_roundtrip(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    write_trades_parquet(run_dir)
    trades = load_trades_from_parquet(run_dir / "trades.parquet")
    assert trades == [{"pnl": 100.0}, {"pnl": -50.0}, {"pnl": 75.0}, {"pnl": 25.0}]


def test_load_trades_from_parquet_missing_column_fail_closed(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    pd.DataFrame({"x": [1.0]}).to_parquet(run_dir / "trades.parquet")
    with pytest.raises(ComparisonMetricInputError, match="missing pnl column"):
        load_trades_from_parquet(run_dir / "trades.parquet")


def test_sha256_file_and_verify_digest_matches_file(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    write_equity_csv(run_dir)
    path = run_dir / "equity.csv"
    digest = sha256_file(path)
    verify_digest_matches_file(path, digest, label="equity.csv")


def test_verify_digest_matches_file_rejects_mismatch(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    write_equity_csv(run_dir)
    with pytest.raises(ComparisonMetricInputError, match="digest mismatch"):
        verify_digest_matches_file(run_dir / "equity.csv", "0" * 64, label="equity.csv")


def test_load_json_object_requires_object_root(tmp_path) -> None:
    path = tmp_path / "payload.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ComparisonMetricInputError, match="root must be object"):
        load_json_object(path, label="payload")


def test_binding_snapshot_serialization_is_deterministic() -> None:
    from src.meta.learning_loop.comparison_metric_input_v1.models import SourceBindingRecord

    records = (
        SourceBindingRecord("a.json", "a" * 64),
        SourceBindingRecord("b.json", "b" * 64),
    )
    first = serialize_binding_snapshot(records)
    second = serialize_binding_snapshot(records)
    assert first == second
    assert binding_records_to_mapping(records) == json.loads(first)
