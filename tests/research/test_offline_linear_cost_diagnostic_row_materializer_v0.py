"""Contract tests for offline linear cost diagnostic row materializer v0."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.research.linear_evidence.import_boundary import scan_file_import_boundary
from src.research.offline_linear_cost_diagnostic_row_materializer_v0 import (
    AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
    CANONICAL_FILL_OWNER,
    MaterializationStatus,
    RejectionReason,
    TARGET_NAME,
    TARGET_PROVENANCE_CLASS,
    compute_simulated_backtest_fill_price_v0,
    compute_simulated_backtest_slippage_bps,
    materialize_offline_linear_cost_diagnostic_rows_v0,
    serialize_materialized_rows_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER_MODULE = (
    REPO_ROOT / "src/research/offline_linear_cost_diagnostic_row_materializer_v0.py"
)
RUNNER_MODULE = REPO_ROOT / "scripts/research/offline_linear_cost_model_diagnostics_v0.py"
FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "requests",
    "httpx",
    "urllib.request",
)


def _trade(
    *,
    trade_id: str = "t-1",
    instrument_id: str = "inst-eth-usdt-perp",
    entry_time: str = "2026-01-01T00:00:00+00:00",
    side: str = "long",
    entry_price: float = 100.5,
    notional: float = 1000.0,
) -> dict[str, object]:
    return {
        "trade_id": trade_id,
        "instrument_id": instrument_id,
        "entry_time": entry_time,
        "side": side,
        "entry_price": entry_price,
        "notional": notional,
    }


def _snapshot(
    *,
    instrument_id: str = "inst-eth-usdt-perp",
    bar_timestamp: str = "2026-01-01T00:00:00+00:00",
    close: float = 100.0,
    spread_bps: float = 10.0,
    volatility_estimate: float = 0.02,
    is_finalized: bool = True,
    feature_timestamp: str | None = None,
    **extra: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "instrument_id": instrument_id,
        "bar_timestamp": bar_timestamp,
        "close": close,
        "spread_bps": spread_bps,
        "volatility_estimate": volatility_estimate,
        "is_finalized": is_finalized,
        "feature_timestamp": feature_timestamp or bar_timestamp,
    }
    payload.update(extra)
    return payload


def test_buy_slippage_formula_exact() -> None:
    result = compute_simulated_backtest_slippage_bps(
        side="long",
        fill_price=100.5,
        execution_reference_price=100.0,
    )
    assert result == pytest.approx(50.0)


def test_sell_slippage_formula_exact() -> None:
    result = compute_simulated_backtest_slippage_bps(
        side="short",
        fill_price=99.5,
        execution_reference_price=100.0,
    )
    assert result == pytest.approx(50.0)


def test_long_short_symmetry() -> None:
    ref = 200.0
    fill = 201.0
    buy = compute_simulated_backtest_slippage_bps(
        side="long", fill_price=fill, execution_reference_price=ref
    )
    sell = compute_simulated_backtest_slippage_bps(
        side="short", fill_price=199.0, execution_reference_price=ref
    )
    assert buy == pytest.approx(sell)


def test_zero_slippage_at_reference_price() -> None:
    assert (
        compute_simulated_backtest_slippage_bps(
            side="long", fill_price=100.0, execution_reference_price=100.0
        )
        == 0.0
    )
    assert (
        compute_simulated_backtest_slippage_bps(
            side="short", fill_price=100.0, execution_reference_price=100.0
        )
        == 0.0
    )


def test_deterministic_trade_id_join() -> None:
    trade = _trade()
    snapshot = _snapshot()
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=[snapshot],
    )
    assert result.admissible_count == 1
    assert result.rows[0]["trade_id"] == "t-1"


def test_instrument_id_entry_time_snapshot_join() -> None:
    trade = _trade(entry_time="2026-01-01T01:00:00+00:00")
    snapshots = [
        _snapshot(bar_timestamp="2026-01-01T00:00:00+00:00"),
        _snapshot(bar_timestamp="2026-01-01T01:00:00+00:00", close=101.0),
    ]
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=snapshots,
    )
    assert result.admissible_count == 1
    assert result.rows[0]["execution_reference_price"] == 101.0


def test_duplicate_join_candidate_rejected() -> None:
    trade = _trade()
    snapshots = [_snapshot(), _snapshot()]
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=snapshots,
    )
    assert result.admissible_count == 0
    assert result.rejected[0].reason == RejectionReason.DUPLICATE_JOIN_CANDIDATE


def test_missing_reference_snapshot_rejected() -> None:
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[_trade()],
        entry_bar_reference_snapshots=[],
    )
    assert result.admissible_count == 0
    assert result.rejected[0].reason == RejectionReason.MISSING_REFERENCE_SNAPSHOT


def test_nonpositive_reference_price_rejected() -> None:
    trade = _trade()
    snapshot = _snapshot(close=0.0)
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=[snapshot],
    )
    assert result.admissible_count == 0
    assert result.rejected[0].reason == RejectionReason.NONPOSITIVE_REFERENCE_PRICE


def test_feature_after_target_time_rejected() -> None:
    trade = _trade(entry_time="2026-01-01T00:00:00+00:00")
    snapshot = _snapshot(feature_timestamp="2026-01-01T01:00:00+00:00")
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=[snapshot],
    )
    assert result.admissible_count == 0
    assert result.rejected[0].reason == RejectionReason.FEATURE_AFTER_TARGET_TIME


def test_unfinalized_bar_rejected() -> None:
    trade = _trade()
    snapshot = _snapshot(is_finalized=False)
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=[snapshot],
    )
    assert result.admissible_count == 0
    assert result.rejected[0].reason == RejectionReason.UNFINALIZED_BAR


def test_optional_depth_absent_admissible() -> None:
    trade = _trade()
    snapshot = _snapshot()
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=[snapshot],
    )
    assert result.admissible_count == 1
    assert "depth_near_touch" not in result.rows[0]


def test_order_notional_used_without_synthetic_depth_ratio() -> None:
    trade = _trade(notional=1234.5)
    snapshot = _snapshot()
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=[snapshot],
    )
    row = result.rows[0]
    assert row["order_notional"] == pytest.approx(1234.5)
    assert "order_notional_to_depth" not in row


def test_stable_row_order() -> None:
    trades = [
        _trade(trade_id="t-2", entry_time="2026-01-01T02:00:00+00:00"),
        _trade(trade_id="t-1", entry_time="2026-01-01T01:00:00+00:00"),
    ]
    snapshots = [
        _snapshot(bar_timestamp="2026-01-01T01:00:00+00:00"),
        _snapshot(bar_timestamp="2026-01-01T02:00:00+00:00"),
    ]
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=trades,
        entry_bar_reference_snapshots=snapshots,
    )
    assert [row["trade_id"] for row in result.rows] == ["t-1", "t-2"]


def test_repeated_materialization_byte_identical() -> None:
    trades = [
        _trade(trade_id="t-1"),
        _trade(trade_id="t-2", entry_time="2026-01-01T01:00:00+00:00"),
    ]
    snapshots = [
        _snapshot(bar_timestamp="2026-01-01T00:00:00+00:00"),
        _snapshot(bar_timestamp="2026-01-01T01:00:00+00:00"),
    ]
    first = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=trades,
        entry_bar_reference_snapshots=snapshots,
    )
    second = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=trades,
        entry_bar_reference_snapshots=snapshots,
    )
    assert serialize_materialized_rows_v0(first.rows) == serialize_materialized_rows_v0(second.rows)


def test_second_materialization_diff_empty() -> None:
    trades = [_trade()]
    snapshots = [_snapshot()]
    first = serialize_materialized_rows_v0(
        materialize_offline_linear_cost_diagnostic_rows_v0(
            trade_ledger_rows=trades,
            entry_bar_reference_snapshots=snapshots,
        ).rows
    )
    second = serialize_materialized_rows_v0(
        materialize_offline_linear_cost_diagnostic_rows_v0(
            trade_ledger_rows=trades,
            entry_bar_reference_snapshots=snapshots,
        ).rows
    )
    assert first == second


def test_diagnostics_runner_consumes_materializer_output(tmp_path: Path) -> None:
    trade = _trade()
    snapshot = _snapshot()
    ledger_path = tmp_path / "ledger.jsonl"
    snapshot_path = tmp_path / "snapshots.jsonl"
    ledger_path.write_text(json.dumps(trade, sort_keys=True) + "\n", encoding="utf-8")
    snapshot_path.write_text(json.dumps(snapshot, sort_keys=True) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER_MODULE),
            "--out",
            str(tmp_path / "out"),
            "--trade-ledger",
            str(ledger_path),
            "--entry-bar-snapshots",
            str(snapshot_path),
        ],
        check=False,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(
        (tmp_path / "out" / "offline_linear_cost_model_diagnostics_v0.json").read_text()
    )
    assert report["n_productive_samples"] == 1
    assert report["target_name"] == TARGET_NAME
    assert report["ols_executed"] is False
    assert report["materialization_status"] == "PASS"


def test_fixture_rows_not_counted_as_productive_samples(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER_MODULE),
            "--out",
            str(tmp_path),
            "--fixture-scaffold",
        ],
        check=False,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    assert report["fixture_scaffold_only"] is True
    assert report["n_productive_samples"] == 0


def test_zero_admissible_rows_fail_closed(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(RUNNER_MODULE), "--out", str(tmp_path)],
        check=False,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    assert report["n_productive_samples"] == 0
    assert report["ols_executed"] is False
    assert report["verdict"] == "OFFLINE_LINEAR_COST_MODEL_DIAGNOSTICS_V0_FAIL_CLOSED"


def test_no_runtime_import_boundary() -> None:
    for path in (MATERIALIZER_MODULE, RUNNER_MODULE):
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_IMPORT_PREFIXES:
            assert token not in source
        hits = scan_file_import_boundary(path, repo_root=REPO_ROOT)
        assert hits == []


def test_no_order_adapter_import_boundary() -> None:
    source = MATERIALIZER_MODULE.read_text(encoding="utf-8")
    for token in ("order_adapter", "src.orders", "src.trading.orders"):
        assert token not in source


def test_no_scheduler_import_boundary() -> None:
    source = MATERIALIZER_MODULE.read_text(encoding="utf-8")
    assert "src.scheduler" not in source


def test_no_runtime_effect() -> None:
    assert RUNTIME_EFFECT == "NONE"


def test_no_authority_effect() -> None:
    assert AUTHORITY_EFFECT == "NONE"


def test_target_provenance_class() -> None:
    trade = _trade()
    snapshot = _snapshot()
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=[snapshot],
    )
    assert result.rows[0]["target_provenance_class"] == TARGET_PROVENANCE_CLASS
    assert result.rows[0]["target_name"] == TARGET_NAME


def test_inline_snapshot_join() -> None:
    trade = _trade()
    trade["entry_bar_reference_snapshot"] = _snapshot()
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=[],
    )
    assert result.admissible_count == 1


def test_zero_admissible_rows_status() -> None:
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[],
        entry_bar_reference_snapshots=[],
    )
    assert result.status == MaterializationStatus.INSUFFICIENT_DATA
    assert result.admissible_count == 0


def test_identity_binding_uses_canonical_simulated_fill_owner() -> None:
    trade = _trade(entry_price=100.0)
    snapshot = _snapshot(close=100.0)
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=[snapshot],
        entry_slippage_bps=5.0,
    )
    assert result.admissible_count == 1
    row = result.rows[0]
    assert row["fill_price_owner"] == CANONICAL_FILL_OWNER
    assert row["simulated_or_realized_fill_price"] == pytest.approx(100.05)
    assert row[TARGET_NAME] == pytest.approx(5.0)


def test_identity_binding_rejected_without_slippage_binding() -> None:
    trade = _trade(entry_price=100.0)
    snapshot = _snapshot(close=100.0)
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=[snapshot],
    )
    assert result.admissible_count == 0
    assert result.rejected[0].reason == RejectionReason.ENTRY_SLIPPAGE_BINDING_MISSING


def test_truth_pack_target_not_constant_or_all_zero() -> None:
    trades = [
        _trade(trade_id="t-identity", entry_price=100.0),
        _trade(trade_id="t-observed", entry_price=100.5, entry_time="2026-01-01T01:00:00+00:00"),
    ]
    snapshots = [
        _snapshot(bar_timestamp="2026-01-01T00:00:00+00:00", close=100.0),
        _snapshot(bar_timestamp="2026-01-01T01:00:00+00:00", close=100.0),
    ]
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=trades,
        entry_bar_reference_snapshots=snapshots,
        entry_slippage_bps=5.0,
    )
    targets = [row[TARGET_NAME] for row in result.rows]
    assert len(set(targets)) > 1
    assert all(value != 0.0 for value in targets)


def test_zero_slippage_only_when_binding_explicitly_zero() -> None:
    trade = _trade(entry_price=100.0)
    snapshot = _snapshot(close=100.0)
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=[trade],
        entry_bar_reference_snapshots=[snapshot],
        entry_slippage_bps=0.0,
    )
    assert result.rows[0][TARGET_NAME] == 0.0


def test_simulated_fill_price_formula_long_short() -> None:
    assert compute_simulated_backtest_fill_price_v0(
        side="long", execution_reference_price=100.0, entry_slippage_bps=5.0
    ) == pytest.approx(100.05)
    assert compute_simulated_backtest_fill_price_v0(
        side="short", execution_reference_price=100.0, entry_slippage_bps=5.0
    ) == pytest.approx(99.95)


def test_trend_following_archive_rows_remain_joinable_with_repo_binding() -> None:
    archive_root = Path(
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
    )
    ledger_path = (
        archive_root
        / "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0_20260705T083113Z"
        / "TRADE_LEDGER_V1.jsonl"
    )
    snapshot_path = (
        archive_root
        / "research/offline_linear_cost_entry_bar_reference_snapshot_materialization_v0_for_trend_following_v1_trade_ledger_binding_20260713T055132Z"
        / "entry_bar_snapshots.jsonl"
    )
    if not ledger_path.is_file() or not snapshot_path.is_file():
        pytest.skip("archive evidence unavailable in this environment")

    ledger_rows = [
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    snapshots = [
        json.loads(line)
        for line in snapshot_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    result = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=ledger_rows,
        entry_bar_reference_snapshots=snapshots,
        repo_root=REPO_ROOT,
    )
    assert result.admissible_count == 219
    assert result.rejected == ()
    targets = [row[TARGET_NAME] for row in result.rows]
    assert all(value > 0.0 for value in targets)
    assert all(value == pytest.approx(5.0, rel=1e-9, abs=1e-9) for value in targets)
    assert all(row.get("market_type", "perp") == "perp" for row in ledger_rows)
    assert not any("btc" in str(row.get("instrument_id", "")).lower() for row in ledger_rows)
