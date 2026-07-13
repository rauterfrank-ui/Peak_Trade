"""Contract tests for offline factor exposure productive input join materializer v0."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research.linear_evidence.factor_exposure import (
    REASON_FACTOR_LOOKAHEAD_DETECTED,
    build_factor_matrix,
    fit_factor_exposure,
)
from research.linear_evidence.factor_exposure_productive_contract_v0 import (
    EXPECTED_PRODUCTIVE_FACTOR_ORDER,
    ProductiveJoinRejectionReason,
)
from research.linear_evidence.import_boundary import scan_file_import_boundary
from src.research.offline_factor_exposure_productive_input_join_materializer_v0 import (
    AUTHORITY_EFFECT,
    CANONICAL_JOIN_KEY,
    RUNTIME_EFFECT,
    MaterializationStatus,
    compute_source_rows_digest,
    materialize_offline_factor_exposure_productive_inputs_v0,
    serialize_materialized_productive_inputs_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER_MODULE = (
    REPO_ROOT / "src/research/offline_factor_exposure_productive_input_join_materializer_v0.py"
)
RUNNER_MODULE = (
    REPO_ROOT / "scripts/research/offline_factor_exposure_productive_input_join_materializer_v0.py"
)
DIAGNOSTICS_RUNNER = REPO_ROOT / "scripts/research/offline_factor_exposure_diagnostics_v0.py"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
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
    exit_time: str = "2026-01-01T01:00:00+00:00",
    net_pnl: float = 10.0,
    notional: float = 1000.0,
) -> dict[str, object]:
    return {
        "trade_id": trade_id,
        "instrument_id": instrument_id,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "net_pnl": net_pnl,
        "notional": notional,
    }


def _snapshot(
    *,
    trade_id: str = "t-1",
    instrument_id: str = "inst-eth-usdt-perp",
    entry_time: str = "2026-01-01T00:00:00+00:00",
    bar_timestamp: str = "2026-01-01T00:00:00+00:00",
    feature_timestamp: str = "2025-12-31T23:00:00+00:00",
    spread_bps: float = 10.0,
    volatility_estimate: float = 0.02,
    funding_rate: float = -0.0001,
    is_finalized: bool = True,
) -> dict[str, object]:
    return {
        "trade_id": trade_id,
        "instrument_id": instrument_id,
        "entry_time": entry_time,
        "bar_timestamp": bar_timestamp,
        "feature_timestamp": feature_timestamp,
        "spread_bps": spread_bps,
        "volatility_estimate": volatility_estimate,
        "funding_rate": funding_rate,
        "is_finalized": is_finalized,
    }


def _materialize(
    trades: list[dict[str, object]],
    snapshots: list[dict[str, object]],
):
    return materialize_offline_factor_exposure_productive_inputs_v0(
        trade_ledger_rows=trades,
        factor_snapshot_rows=snapshots,
    )


def test_productive_contract_accepted() -> None:
    result = _materialize([_trade()], [_snapshot()])
    assert result.status == MaterializationStatus.PASS
    assert len(result.records) == 1
    assert result.records[0].factor_time < result.records[0].decision_time


def test_missing_required_input_rejected() -> None:
    trade = _trade()
    trade.pop("trade_id")
    result = _materialize([trade], [_snapshot()])
    assert result.status == MaterializationStatus.TARGET_BINDING_MISSING
    assert (
        ProductiveJoinRejectionReason.MISSING_TRADE_ID.value
        in result.join_result.dropped_rows_by_reason
    )


def test_duplicate_join_partner_rejected() -> None:
    result = _materialize(
        [_trade(trade_id="t-1"), _trade(trade_id="t-1")],
        [_snapshot(trade_id="t-1")],
    )
    assert (
        ProductiveJoinRejectionReason.DUPLICATE_TRADE_ID.value
        in result.join_result.dropped_rows_by_reason
    )


def test_ambiguous_join_partner_rejected() -> None:
    trade = _trade()
    trade["notional"] = 1000.0
    trade["entry_notional"] = 2000.0
    result = _materialize([trade], [_snapshot()])
    assert (
        ProductiveJoinRejectionReason.TARGET_NOTIONAL_OWNER_AMBIGUOUS.value
        in result.join_result.dropped_rows_by_reason
    )


def test_conflicting_partner_rejected() -> None:
    result = _materialize(
        [_trade(trade_id="t-1", instrument_id="inst-a")],
        [_snapshot(trade_id="t-1", instrument_id="inst-b")],
    )
    assert (
        ProductiveJoinRejectionReason.INSTRUMENT_ID_MISMATCH.value
        in result.join_result.dropped_rows_by_reason
    )


def test_many_to_many_join_rejected() -> None:
    result = _materialize(
        [_trade(trade_id="t-1")],
        [_snapshot(trade_id="t-1"), _snapshot(trade_id="t-1")],
    )
    assert (
        ProductiveJoinRejectionReason.DUPLICATE_FACTOR_SNAPSHOT.value
        in result.join_result.dropped_rows_by_reason
    )


def test_stale_or_future_dated_input_rejected() -> None:
    result = _materialize(
        [_trade(entry_time="2026-01-01T00:00:00+00:00", exit_time="2026-01-01T01:00:00+00:00")],
        [
            _snapshot(
                entry_time="2026-01-01T01:00:00+00:00",
                bar_timestamp="2026-01-01T01:00:00+00:00",
                feature_timestamp="2025-12-31T23:00:00+00:00",
            )
        ],
    )
    assert (
        ProductiveJoinRejectionReason.ENTRY_TIME_MISMATCH.value
        in result.join_result.dropped_rows_by_reason
    )


def test_lookahead_rejected() -> None:
    result = _materialize(
        [_trade()],
        [_snapshot(feature_timestamp="2026-01-01T01:00:00+00:00")],
    )
    assert (
        ProductiveJoinRejectionReason.FEATURE_LEAKAGE_DETECTED.value
        in result.join_result.dropped_rows_by_reason
    )


def test_deterministic_row_order() -> None:
    trades = [
        _trade(
            trade_id="t-2",
            entry_time="2026-01-01T02:00:00+00:00",
            exit_time="2026-01-01T03:00:00+00:00",
        ),
        _trade(
            trade_id="t-1",
            entry_time="2026-01-01T00:00:00+00:00",
            exit_time="2026-01-01T01:00:00+00:00",
        ),
    ]
    snapshots = [
        _snapshot(
            trade_id="t-2",
            entry_time="2026-01-01T02:00:00+00:00",
            bar_timestamp="2026-01-01T02:00:00+00:00",
            feature_timestamp="2026-01-01T01:00:00+00:00",
        ),
        _snapshot(trade_id="t-1"),
    ]
    result = _materialize(trades, snapshots)
    decision_times = [record.decision_time for record in result.records]
    assert decision_times == sorted(decision_times)


def test_deterministic_feature_order() -> None:
    result = _materialize([_trade()], [_snapshot()])
    assert tuple(sorted(result.records[0].factor_values.keys())) == EXPECTED_PRODUCTIVE_FACTOR_ORDER
    _, _, names, _, _ = build_factor_matrix(result.records)
    assert names == EXPECTED_PRODUCTIVE_FACTOR_ORDER


def test_repeated_materialization_identical() -> None:
    trades = [
        _trade(trade_id="t-1"),
        _trade(
            trade_id="t-2",
            entry_time="2026-01-01T02:00:00+00:00",
            exit_time="2026-01-01T03:00:00+00:00",
        ),
    ]
    snapshots = [
        _snapshot(trade_id="t-1"),
        _snapshot(
            trade_id="t-2",
            entry_time="2026-01-01T02:00:00+00:00",
            bar_timestamp="2026-01-01T02:00:00+00:00",
            feature_timestamp="2026-01-01T01:00:00+00:00",
        ),
    ]
    first = _materialize(trades, snapshots)
    second = _materialize(trades, snapshots)
    assert first.output_digest == second.output_digest
    assert first.materialization_digest == second.materialization_digest


def test_second_materialization_diff_empty() -> None:
    trades = [_trade()]
    snapshots = [_snapshot()]
    first = serialize_materialized_productive_inputs_v0(_materialize(trades, snapshots).records)
    second = serialize_materialized_productive_inputs_v0(_materialize(trades, snapshots).records)
    assert first == second


def test_dropped_row_accounting_complete() -> None:
    trades = [
        _trade(trade_id="t-1"),
        _trade(trade_id="t-2"),
        _trade(trade_id="t-3", instrument_id="inst-a"),
    ]
    snapshots = [
        _snapshot(trade_id="t-1"),
        _snapshot(trade_id="t-3", instrument_id="inst-b"),
        _snapshot(trade_id="orphan"),
    ]
    result = _materialize(trades, snapshots)
    dropped = result.join_result.dropped_rows_by_reason
    assert dropped.get(ProductiveJoinRejectionReason.MISSING_FACTOR_SNAPSHOT.value, 0) >= 1
    assert dropped.get(ProductiveJoinRejectionReason.INSTRUMENT_ID_MISMATCH.value, 0) >= 1
    assert dropped.get(ProductiveJoinRejectionReason.ORPHAN_FACTOR_ROW.value, 0) >= 1
    assert sum(dropped.values()) == len(result.join_result.rejected)


def test_input_digests_stable() -> None:
    trades = [_trade()]
    snapshots = [_snapshot()]
    first = compute_source_rows_digest(trades)
    second = compute_source_rows_digest(trades)
    assert first == second


def test_output_digest_stable() -> None:
    result = _materialize([_trade()], [_snapshot()])
    assert result.output_digest
    assert len(result.output_digest) == 64


def test_materializer_to_contract_roundtrip_pass() -> None:
    trades = [
        _trade(
            trade_id=f"t-{i}",
            entry_time=f"2026-01-01T{i:02d}:00:00+00:00",
            exit_time=f"2026-01-01T{i + 1:02d}:00:00+00:00",
        )
        for i in range(1, 12)
    ]
    snapshots = [
        _snapshot(
            trade_id=f"t-{i}",
            entry_time=f"2026-01-01T{i:02d}:00:00+00:00",
            bar_timestamp=f"2026-01-01T{i:02d}:00:00+00:00",
            feature_timestamp=f"2026-01-01T{i - 1:02d}:00:00+00:00",
        )
        for i in range(1, 12)
    ]
    result = _materialize(trades, snapshots)
    assert result.status == MaterializationStatus.PASS
    assert len(result.records) == 11
    evidence = fit_factor_exposure(result.records)
    assert evidence.status in {"DIAGNOSTIC_ONLY", "INSUFFICIENT_DATA", "RANK_DEFICIENT_BLOCKED"}
    assert evidence.feature_names == EXPECTED_PRODUCTIVE_FACTOR_ORDER


def test_diagnostics_runner_consumes_materializer_output(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    snapshot_path = tmp_path / "snapshots.jsonl"
    ledger_path.write_text(json.dumps(_trade(), sort_keys=True) + "\n", encoding="utf-8")
    snapshot_path.write_text(json.dumps(_snapshot(), sort_keys=True) + "\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            str(DIAGNOSTICS_RUNNER),
            "--out",
            str(out_dir),
            "--trade-ledger",
            str(ledger_path),
            "--factor-snapshots",
            str(snapshot_path),
            "--repo-root",
            str(REPO_ROOT),
        ],
        check=False,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads((out_dir / "factor_exposure_evidence_v1.json").read_text(encoding="utf-8"))
    assert payload["INPUT_MODE"] == "PRODUCTIVE_JOIN_MATERIALIZED"
    assert payload["PRODUCTIVE_BINDING_RESOLVED"] is True
    assert payload["dataset_digest"]


def test_cli_materializer_writes_manifestable_report(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    snapshot_path = tmp_path / "snapshots.jsonl"
    ledger_path.write_text(json.dumps(_trade(), sort_keys=True) + "\n", encoding="utf-8")
    snapshot_path.write_text(json.dumps(_snapshot(), sort_keys=True) + "\n", encoding="utf-8")
    out_dir = tmp_path / "materialized"
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER_MODULE),
            "--out",
            str(out_dir),
            "--trade-ledger",
            str(ledger_path),
            "--factor-snapshots",
            str(snapshot_path),
            "--repo-root",
            str(REPO_ROOT),
        ],
        check=False,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((out_dir / "materialization_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["join_keys"]["primary"] == CANONICAL_JOIN_KEY


def test_archive_binding_fail_closed_on_equal_feature_and_entry_time() -> None:
    ledger_path = (
        ARCHIVE_ROOT
        / "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0_20260705T083113Z"
        / "TRADE_LEDGER_V1.jsonl"
    )
    snapshot_path = (
        ARCHIVE_ROOT
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
    snapshot_rows = [
        json.loads(line)
        for line in snapshot_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    result = _materialize(ledger_rows, snapshot_rows)
    assert result.join_result.row_count_before_filter == 219
    assert result.join_result.row_count_after_filter == 0
    assert result.join_result.dropped_rows_by_reason == {
        ProductiveJoinRejectionReason.FEATURE_LEAKAGE_DETECTED.value: 219
    }


def test_no_runtime_order_or_scheduler_imports_in_owner() -> None:
    for path in (MATERIALIZER_MODULE, RUNNER_MODULE, DIAGNOSTICS_RUNNER):
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_IMPORT_PREFIXES:
            assert token not in source
        hits = scan_file_import_boundary(path, repo_root=REPO_ROOT)
        assert hits == []


def test_no_trading_semantics_mutation_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"


def test_lookahead_blocks_build_factor_matrix() -> None:
    result = _materialize(
        [_trade()],
        [_snapshot(feature_timestamp="2026-01-01T01:00:00+00:00")],
    )
    assert not result.records
    good = _materialize([_trade()], [_snapshot()])
    with pytest.raises(ValueError, match=REASON_FACTOR_LOOKAHEAD_DETECTED):
        build_factor_matrix(
            [
                type(good.records[0])(
                    good.records[0].instrument_id,
                    good.records[0].timestamp,
                    good.records[0].target_return,
                    good.records[0].factor_values,
                    factor_time="2026-01-01T01:00:00+00:00",
                    decision_time="2026-01-01T00:00:00+00:00",
                )
            ]
        )
