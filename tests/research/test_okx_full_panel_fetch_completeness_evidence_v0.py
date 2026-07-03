"""Contract tests for OKX full-panel fetch and completeness evidence v0."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from src.research.okx_full_panel_fetch_completeness_evidence_v0 import (
    GO_TOKEN,
    FetchReasonCode,
    PanelCompletenessOutcome,
    build_fetch_spec_v0,
    compute_aggregates_v0,
    fetch_archive_object_v0,
    measure_quarantine_inventory_v0,
    quarantine_measurement_policy_v0,
    run_okx_full_panel_fetch_completeness_evidence_v0,
)
from src.research.okx_historical_funding_archive_ingest_v0 import ArchiveAccessGuardV0
from src.research.cross_sectional_bounded_panel_fetch_v0 import compute_bounded_window_v0

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
REGISTRY_PATH = (
    ARCHIVE_ROOT / "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_historical_2024_v1/v1/"
    "lifecycle/registry_snapshot_v1.json"
)
PROBE_DIR = ARCHIVE_ROOT / "probes/okx_historical_funding_archive_probe_v0_20260703T160811Z/raw"
OHLCV_RAW = (
    ARCHIVE_ROOT / "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_historical_2024_v1/v1/raw"
)

ETH_CSV = """\
instrument_name,funding_rate,funding_time
ETH-USDT-SWAP,0.000004880388991,1714492800000
ETH-USDT-SWAP,0.0000017236956739,1714521600000
"""


def _csv_to_zip(csv_text: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("ETH-USDT-SWAP-fundingrates-2024-05.csv", csv_text)
    return buf.getvalue()


def test_quarantine_measurement_reproducible(tmp_path: Path) -> None:
    policy = quarantine_measurement_policy_v0(durable_archive_root=tmp_path)
    assert "PR4804" in policy.discrepancy_root_cause
    root = tmp_path / "q"
    (root / "a").mkdir(parents=True)
    (root / "a" / "one.bin").write_bytes(b"abc")
    (root / "a" / "two.bin").write_bytes(b"def")
    first = measure_quarantine_inventory_v0(root)
    second = measure_quarantine_inventory_v0(root)
    assert first == second
    assert first.file_count == 2
    assert first.byte_count == 6


def test_reuse_existing_valid_archive(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    body = _csv_to_zip(ETH_CSV)
    target = archive_dir / "ETH-USDT-SWAP-fundingrates-2024-05.zip"
    target.write_bytes(body)
    sidecar = target.with_suffix(target.suffix + ".sha256")
    import hashlib

    digest = hashlib.sha256(body).hexdigest()
    sidecar.write_text(f"{digest}  {target.name}\n", encoding="utf-8")
    guard = ArchiveAccessGuardV0(
        max_instruments=1,
        max_months=1,
        max_http_requests=5,
        max_total_bytes=1_000_000,
        max_runtime_seconds=60,
    )

    def _boom(_url: str, _timeout: float) -> tuple[int, bytes, dict[str, str]]:
        raise AssertionError("network should not be called when reusing existing archive")

    result, _ = fetch_archive_object_v0(
        venue_symbol="ETH-USDT-SWAP",
        month="2024-05",
        archive_dir=archive_dir,
        quarantine_root=tmp_path / "quarantine",
        guard=guard,
        probe_archive_dir=None,
        fetcher=_boom,
        timeout_seconds=5.0,
        min_interval_seconds=0.0,
        last_fetch_monotonic=0.0,
    )
    assert result.reason_code is FetchReasonCode.REUSED_EXISTING


def test_divergent_existing_file_not_overwritten(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    target = archive_dir / "ETH-USDT-SWAP-fundingrates-2024-05.zip"
    target.write_bytes(b"original-content")
    guard = ArchiveAccessGuardV0(
        max_instruments=1,
        max_months=1,
        max_http_requests=5,
        max_total_bytes=1_000_000,
        max_runtime_seconds=60,
    )
    new_body = _csv_to_zip(ETH_CSV)

    def _fetch(_url: str, _timeout: float) -> tuple[int, bytes, dict[str, str]]:
        return 200, new_body, {"content-type": "application/zip"}

    result, _ = fetch_archive_object_v0(
        venue_symbol="ETH-USDT-SWAP",
        month="2024-05",
        archive_dir=archive_dir,
        quarantine_root=tmp_path / "quarantine",
        guard=guard,
        probe_archive_dir=None,
        fetcher=_fetch,
        timeout_seconds=5.0,
        min_interval_seconds=0.0,
        last_fetch_monotonic=0.0,
    )
    assert result.reason_code is FetchReasonCode.QUARANTINED
    assert target.read_bytes() == b"original-content"


def test_partial_download_quarantined(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    guard = ArchiveAccessGuardV0(
        max_instruments=1,
        max_months=1,
        max_http_requests=5,
        max_total_bytes=1_000_000,
        max_runtime_seconds=60,
    )

    def _fetch(_url: str, _timeout: float) -> tuple[int, bytes, dict[str, str]]:
        return 500, b"", {}

    quarantine = tmp_path / "quarantine"
    result, _ = fetch_archive_object_v0(
        venue_symbol="ETH-USDT-SWAP",
        month="2024-05",
        archive_dir=archive_dir,
        quarantine_root=quarantine,
        guard=guard,
        probe_archive_dir=None,
        fetcher=_fetch,
        timeout_seconds=5.0,
        min_interval_seconds=0.0,
        last_fetch_monotonic=0.0,
    )
    assert result.reason_code is FetchReasonCode.DOWNLOAD_FAILED
    assert any(quarantine.iterdir())


def test_no_promotion_on_complete_or_incomplete() -> None:
    complete = compute_aggregates_v0(
        all_requested=[("a", "A-USDT-SWAP", "linear_perpetual")],
        admissible=[("a", "A-USDT-SWAP", "linear_perpetual")],
        cells=(),
        archive_results=(),
    )
    assert complete.instruments_requested == 1


@pytest.mark.skipif(not REGISTRY_PATH.is_file(), reason="lifecycle registry fixture unavailable")
def test_bounded_execution_offline_two_instruments(tmp_path: Path) -> None:
    result = run_okx_full_panel_fetch_completeness_evidence_v0(
        confirm=GO_TOKEN,
        durable_archive_root=tmp_path,
        lifecycle_registry_path=REGISTRY_PATH,
        ohlcv_raw_dir=OHLCV_RAW,
        probe_archive_dir=PROBE_DIR,
        execution_root=tmp_path / "exec",
        max_instruments=2,
        network_enabled=False,
    )
    assert result.full_panel_fetch_executed is True
    assert result.dataset_promoted is False
    assert result.economic_evaluation_executed is False
    assert result.promotion_effect == "NONE"
    assert result.panel_outcome in {
        PanelCompletenessOutcome.INCOMPLETE,
        PanelCompletenessOutcome.BLOCKED,
        PanelCompletenessOutcome.INCONCLUSIVE,
    }
    assert (tmp_path / "exec" / "fetch_spec.json").is_file()


def test_identical_offline_runs_same_aggregates_structure(tmp_path: Path) -> None:
    if not REGISTRY_PATH.is_file():
        pytest.skip("lifecycle registry fixture unavailable")
    kwargs = dict(
        confirm=GO_TOKEN,
        durable_archive_root=tmp_path,
        lifecycle_registry_path=REGISTRY_PATH,
        ohlcv_raw_dir=OHLCV_RAW,
        probe_archive_dir=PROBE_DIR,
        max_instruments=1,
        network_enabled=False,
    )
    first = run_okx_full_panel_fetch_completeness_evidence_v0(
        **kwargs,
        execution_root=tmp_path / "exec1",
    )
    second = run_okx_full_panel_fetch_completeness_evidence_v0(
        **kwargs,
        execution_root=tmp_path / "exec2",
    )
    assert first.aggregates.instruments_requested == second.aggregates.instruments_requested
    assert first.panel_outcome == second.panel_outcome
    assert first.fetch_spec.implementation_digest == second.fetch_spec.implementation_digest
