"""Contract tests for offline productive point-in-time factor snapshot rematerializer v0."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from research.linear_evidence.factor_exposure_productive_contract_v0 import (
    EXPECTED_PRODUCTIVE_FACTOR_ORDER,
    ProductiveJoinRejectionReason,
    validate_productive_join_batch_v0,
)
from research.linear_evidence.import_boundary import scan_file_import_boundary
from scripts.ops.run_economic_viability_evidence_evaluation_v1 import _load_bars_from_dataset_path
from src.research.offline_productive_point_in_time_factor_snapshot_rematerializer_v0 import (
    AUTHORITY_EFFECT,
    ASOF_POLICY,
    RUNTIME_EFFECT,
    DropReason,
    RematerializationStatus,
    lookup_prior_bar_asof_v0,
    materialize_productive_point_in_time_factor_snapshots_v0,
    serialize_productive_point_in_time_factor_snapshots_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER_MODULE = (
    REPO_ROOT / "src/research/offline_productive_point_in_time_factor_snapshot_rematerializer_v0.py"
)
RUNNER_MODULE = (
    REPO_ROOT
    / "scripts/research/offline_productive_point_in_time_factor_snapshot_rematerializer_v0.py"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
LEDGER = (
    ARCHIVE_ROOT
    / "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0_20260705T083113Z"
    / "TRADE_LEDGER_V1.jsonl"
)
BARS = ARCHIVE_ROOT / "datasets/admissible_futures/inst-eth-usdt-perp/v1/bars.parquet"
SPREAD_HALF_BPS = 5.0
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
    entry_time: str = "2026-06-17T17:55:00+00:00",
) -> dict[str, object]:
    return {
        "trade_id": trade_id,
        "instrument_id": instrument_id,
        "entry_time": entry_time,
        "exit_time": "2026-06-17T18:00:00+00:00",
        "net_pnl": 10.0,
        "notional": 1000.0,
    }


def _bars_frame() -> pd.DataFrame:
    if not BARS.is_file():
        pytest.skip("archive bars unavailable")
    return _load_bars_from_dataset_path(BARS)


def _ledger_rows() -> list[dict[str, object]]:
    if not LEDGER.is_file():
        pytest.skip("archive ledger unavailable")
    return [
        json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def _materialize(
    trades: list[dict[str, object]],
    bars: pd.DataFrame | None = None,
    *,
    spread_half_bps: float = SPREAD_HALF_BPS,
):
    frame = bars if bars is not None else _bars_frame()
    return materialize_productive_point_in_time_factor_snapshots_v0(
        trade_ledger_rows=trades,
        bars=frame,
        spread_half_bps=spread_half_bps,
        source_dataset_ref=str(BARS),
        expected_instrument_id="inst-eth-usdt-perp",
    )


def test_strict_less_than_boundary_accepted() -> None:
    result = _materialize([_trade()])
    assert result.admissible_count == 1
    snap = result.snapshots[0]
    assert snap["feature_timestamp"] < snap["entry_time"]


def test_same_time_rejected() -> None:
    bars = _bars_frame()
    entry_time = "2026-06-17T17:55:00+00:00"
    result = _materialize([_trade(entry_time=entry_time)], bars)
    assert result.admissible_count == 1
    assert result.snapshots[0]["feature_timestamp"] != entry_time


def test_future_record_rejected_when_no_prior_bar() -> None:
    bars = _bars_frame()
    early = bars.index.min()
    result = _materialize([_trade(entry_time=early.isoformat())], bars)
    assert result.admissible_count == 0
    assert DropReason.MISSING_PRIOR_BAR.value in result.dropped_rows_by_reason


def test_missing_source_fail_closed() -> None:
    bars = _bars_frame().copy()
    idx = bars.index[bars.index < pd.Timestamp("2026-06-17T17:55:00+00:00")][-1]
    bars.at[idx, "volatility_estimate"] = float("nan")
    result = _materialize([_trade()], bars)
    assert result.admissible_count == 0
    assert DropReason.MISSING_VOLATILITY_ESTIMATE.value in result.dropped_rows_by_reason


def test_deterministic_asof_selection() -> None:
    bars = _bars_frame()
    ts, row = lookup_prior_bar_asof_v0(
        bars=bars,
        entry_time="2026-06-17T17:55:00+00:00",
    )
    assert isinstance(ts, pd.Timestamp)
    assert ts.isoformat() == "2026-06-17T17:54:00+00:00"
    assert row["volatility_estimate"] == pytest.approx(0.0008222710610081796)


def test_duplicate_trade_id_rejected() -> None:
    result = _materialize([_trade(), _trade()])
    assert DropReason.DUPLICATE_TRADE_ID.value in result.dropped_rows_by_reason


def test_missing_spread_binding_rejected() -> None:
    frame = _bars_frame()
    result = materialize_productive_point_in_time_factor_snapshots_v0(
        trade_ledger_rows=[_trade()],
        bars=frame,
        spread_half_bps=None,
        source_dataset_ref=str(BARS),
    )
    assert result.admissible_count == 0
    assert DropReason.MISSING_SPREAD_BPS_BINDING.value in result.dropped_rows_by_reason


def test_repeated_materialization_byte_identical() -> None:
    trades = _ledger_rows()[:5]
    first = _materialize(trades)
    second = _materialize(trades)
    assert serialize_productive_point_in_time_factor_snapshots_v0(
        first.snapshots
    ) == serialize_productive_point_in_time_factor_snapshots_v0(second.snapshots)
    assert first.materialization_digest == second.materialization_digest


def test_second_materialization_diff_empty() -> None:
    trades = _ledger_rows()[:3]
    first = serialize_productive_point_in_time_factor_snapshots_v0(_materialize(trades).snapshots)
    second = serialize_productive_point_in_time_factor_snapshots_v0(_materialize(trades).snapshots)
    assert first == second


def test_archive_219_trades_all_admissible_point_in_time() -> None:
    result = _materialize(_ledger_rows())
    assert result.admissible_count == 219
    assert result.status == RematerializationStatus.PASS
    assert all(s["feature_timestamp"] < s["entry_time"] for s in result.snapshots)
    assert result.dropped_rows_by_reason == {}


def test_productive_join_materializer_path_accepts_rematerialized_snapshots() -> None:
    result = _materialize(_ledger_rows())
    join = validate_productive_join_batch_v0(
        trade_ledger_rows=_ledger_rows(),
        factor_snapshots=list(result.snapshots),
    )
    assert join.row_count_after_filter == 219
    assert join.dropped_rows_by_reason == {}
    assert (
        ProductiveJoinRejectionReason.FEATURE_LEAKAGE_DETECTED.value
        not in join.dropped_rows_by_reason
    )


def test_stable_feature_order_in_productive_contract() -> None:
    result = _materialize([_trade()])
    snap = result.snapshots[0]
    assert tuple(sorted(snap.keys()))  # snapshot keys stable serialization
    assert "funding_rate" in snap
    assert "spread_bps" in snap
    assert "volatility_estimate" in snap
    assert EXPECTED_PRODUCTIVE_FACTOR_ORDER == (
        "funding_rate_abs",
        "spread_bps",
        "volatility_estimate",
    )


def test_no_runtime_import_boundary() -> None:
    for path in (MATERIALIZER_MODULE, RUNNER_MODULE):
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_IMPORT_PREFIXES:
            assert token not in source
        hits = scan_file_import_boundary(path, repo_root=REPO_ROOT)
        assert hits == []


def test_no_runtime_or_authority_effect() -> None:
    assert RUNTIME_EFFECT == "NONE"
    assert AUTHORITY_EFFECT == "NONE"


def test_asof_policy_documented() -> None:
    assert ASOF_POLICY == "latest_finalized_bar_strictly_before_entry_time"


def test_cli_materializes_manifestable_output(tmp_path: Path) -> None:
    if not LEDGER.is_file() or not BARS.is_file():
        pytest.skip("archive unavailable")
    out = tmp_path / "out"
    proc = subprocess.run(
        [
            sys.executable,
            str(RUNNER_MODULE),
            "--out",
            str(out),
            "--trade-ledger",
            str(LEDGER),
            "--bars-dataset",
            str(BARS),
            "--spread-half-bps",
            str(SPREAD_HALF_BPS),
            "--instrument-id",
            "inst-eth-usdt-perp",
            "--repo-root",
            str(REPO_ROOT),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads((out / "rematerialization_report.json").read_text(encoding="utf-8"))
    assert payload["admissible_count"] == 219
    lines = (out / "productive_point_in_time_factor_snapshots_v0.jsonl").read_text().splitlines()
    assert len(lines) == 219


def test_temp_dir_deterministic_outputs_match() -> None:
    if not LEDGER.is_file() or not BARS.is_file():
        pytest.skip("archive unavailable")
    outputs: list[str] = []
    for _ in range(2):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER_MODULE),
                    "--out",
                    str(out),
                    "--trade-ledger",
                    str(LEDGER),
                    "--bars-dataset",
                    str(BARS),
                    "--spread-half-bps",
                    str(SPREAD_HALF_BPS),
                    "--instrument-id",
                    "inst-eth-usdt-perp",
                    "--repo-root",
                    str(REPO_ROOT),
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                check=False,
            )
            assert proc.returncode == 0, proc.stderr
            outputs.append(
                (out / "productive_point_in_time_factor_snapshots_v0.jsonl").read_text(
                    encoding="utf-8"
                )
            )
    assert outputs[0] == outputs[1]
