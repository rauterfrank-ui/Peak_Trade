from __future__ import annotations

import importlib.util
import json
import uuid
from pathlib import Path
from typing import Any

import pytest

from scripts.ops.primary_evidence_retention_v0 import (
    parse_manifest_verify_log_rc,
    verify_manifest_sha256,
)
from src.webui.workflow_dashboard_readmodel_v1.futures_producer_packet_real_metadata_source_v1 import (
    FuturesProducerPacketRealMetadataSourceError,
    load_futures_producer_packet_governed,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BUILD = _REPO_ROOT / "scripts/ops/build_u2c_governed_snapshot_candidate_v1.py"
_U5D_FIXTURES = _REPO_ROOT / "tests/fixtures/u5d_offline_transform_v1/minimal"
_CONFIRM_BUILD = "CONFIRM_U2C_GOVERNED_SNAPSHOT_CANDIDATE_BUILD_V1"
_SCRATCH = _REPO_ROOT / "tests" / "_durable_archive_scratch"


def _load_build_mod() -> Any:
    spec = importlib.util.spec_from_file_location("_u2c_build", _BUILD)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _durable_archive_root(tmp_path: Path) -> Path:
    candidate = tmp_path / "archive_root"
    candidate.mkdir(parents=True, exist_ok=True)
    if not str(candidate).startswith("/tmp"):
        return candidate
    _SCRATCH.mkdir(parents=True, exist_ok=True)
    durable = _SCRATCH / str(uuid.uuid4())
    durable.mkdir(parents=True, exist_ok=True)
    return durable


def _complete_flat_row(symbol: str, *, vol24h: float, rank: int) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "instrument_id": symbol,
        "provider": "kraken_futures",
        "exchange": "kraken_futures",
        "market_type": "perpetual",
        "contract_type": "perpetual",
        "base_currency": symbol[3:6],
        "quote_currency": "USD",
        "active": True,
        "tick_size": 0.05,
        "contract_size": 1,
        "min_qty": 0.001,
        "min_notional": 1.0,
        "margin_asset": "USD",
        "settlement_asset": "USD",
        "max_leverage": 50,
        "fetched_at": "2026-06-08T18:00:00Z",
        "last_price": 100.0 + rank,
        "mark_price": 100.0 + rank,
        "index_price": 100.0 + rank,
        "vol24h": vol24h,
        "bid": 99.0 + rank,
        "ask": 101.0 + rank,
        "spread": 2.0,
        "funding_rate": 0.0001,
        "open_interest": 1000.0,
        "missing_fields": [],
        "degraded_fields": [],
    }


@pytest.fixture
def build_mod() -> Any:
    return _load_build_mod()


def test_per_file_ok_manifest_without_rc_line_is_rejected(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "artifact.json").write_text("{}\n", encoding="utf-8")
    (bundle_dir / "MANIFEST_VERIFY.log").write_text("./artifact.json: OK\n", encoding="utf-8")
    rc, msg, _ = parse_manifest_verify_log_rc(bundle_dir)
    assert rc is None
    assert "MANIFEST_VERIFY_RC missing" in msg


def test_build_writes_manifest_verify_rc_zero(build_mod: Any, tmp_path: Path) -> None:
    archive = _durable_archive_root(tmp_path)
    u5d_path = archive / "runtime" / "u5d" / "u5d_u2c_candidate_validation.v1.json"
    u5d_path.parent.mkdir(parents=True)
    rows = [
        _complete_flat_row("PF_ETHUSD", vol24h=200.0, rank=1),
        _complete_flat_row("PF_XBTUSD", vol24h=100.0, rank=2),
    ]
    u5d_path.write_text(
        json.dumps(
            {
                "schema": "u5d_u2c_candidate_validation_v1",
                "provider": "kraken_futures",
                "fetched_at": "2026-06-08T18:00:00Z",
                "packet_candidates": rows,
                "top20_ranking_candidate": [
                    {"rank": 1, "symbol": "PF_ETHUSD", "vol24h": 200.0},
                    {"rank": 2, "symbol": "PF_XBTUSD", "vol24h": 100.0},
                ],
                "input_paths": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = archive / "governed_metadata" / "test_bundle_v1"
    summary = build_mod.build_governed_snapshot_candidate_bundle(
        confirm=_CONFIRM_BUILD,
        u5d_validation_path=u5d_path,
        output_dir=out_dir,
        archive_root=archive,
        bundle_id="test_bundle_v1",
    )
    assert summary["manifest_verify_rc"] == 0
    rc, _, _ = parse_manifest_verify_log_rc(out_dir)
    assert rc == 0
    ok, msg = verify_manifest_sha256(out_dir)
    assert ok, msg

    governed = json.loads((out_dir / "futures_producer_packet_governed.v1.json").read_text())
    packet = governed["packets"][0]
    assert "candidate" in packet
    assert "instrument" in packet
    assert "provenance" in packet
    assert governed["selected_future"]["symbol"] is None
    assert governed["GOVERNED_SNAPSHOT_ACCEPTED_FOR_INTAKE"] is False
    assert governed["u2b_candidate_validation_only"] is True
    assert governed["instrument_completeness_mode"] == "candidate_validation"


def test_u2b_validate_only_parses_built_fixture_bundle(build_mod: Any, tmp_path: Path) -> None:
    archive = _durable_archive_root(tmp_path)
    u5d_path = archive / "runtime" / "u5d" / "u5d_u2c_candidate_validation.v1.json"
    u5d_path.parent.mkdir(parents=True)
    rows = [
        _complete_flat_row("PF_ETHUSD", vol24h=300.0, rank=1),
        _complete_flat_row("PF_XBTUSD", vol24h=200.0, rank=2),
    ]
    u5d_path.write_text(
        json.dumps(
            {
                "schema": "u5d_u2c_candidate_validation_v1",
                "provider": "kraken_futures",
                "fetched_at": "2026-06-08T18:00:00Z",
                "packet_candidates": rows,
                "top20_ranking_candidate": [
                    {"rank": 1, "symbol": "PF_ETHUSD", "vol24h": 300.0},
                    {"rank": 2, "symbol": "PF_XBTUSD", "vol24h": 200.0},
                ],
                "input_paths": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    evidence = archive / "runs" / "paper" / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "CLOSEOUT.md").write_text("# evidence\n", encoding="utf-8")

    out_dir = archive / "governed_metadata" / "u2b_fixture_bundle_v1"
    build_mod.build_governed_snapshot_candidate_bundle(
        confirm=_CONFIRM_BUILD,
        u5d_validation_path=u5d_path,
        output_dir=out_dir,
        archive_root=archive,
        bundle_id="u2b_fixture_bundle_v1",
        evidence_links=(str(evidence.resolve()),),
    )
    bundle_path = out_dir / "futures_producer_packet_governed.v1.json"
    bundle = load_futures_producer_packet_governed(bundle_path, archive_root=archive)
    assert len(bundle.packets) == 2
    assert bundle.source_stage == "paper"
    assert bundle.non_authorizing is True
    assert bundle.observability_truth_allowed is False
    assert bundle.selected_candidate_id is None


def test_u2b_rejects_per_file_ok_only_manifest_on_fixture_path(
    build_mod: Any, tmp_path: Path
) -> None:
    archive = _durable_archive_root(tmp_path)
    u5d_path = archive / "runtime" / "u5d" / "u5d_u2c_candidate_validation.v1.json"
    u5d_path.parent.mkdir(parents=True)
    rows = [_complete_flat_row("PF_ETHUSD", vol24h=100.0, rank=1)]
    u5d_path.write_text(
        json.dumps(
            {
                "schema": "u5d_u2c_candidate_validation_v1",
                "provider": "kraken_futures",
                "fetched_at": "2026-06-08T18:00:00Z",
                "packet_candidates": rows,
                "top20_ranking_candidate": [{"rank": 1, "symbol": "PF_ETHUSD", "vol24h": 100.0}],
                "input_paths": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = archive / "governed_metadata" / "bad_manifest_bundle_v1"
    build_mod.build_governed_snapshot_candidate_bundle(
        confirm=_CONFIRM_BUILD,
        u5d_validation_path=u5d_path,
        output_dir=out_dir,
        archive_root=archive,
        bundle_id="bad_manifest_bundle_v1",
    )
    (out_dir / "MANIFEST_VERIFY.log").write_text("./README.md: OK\n", encoding="utf-8")
    bundle_path = out_dir / "futures_producer_packet_governed.v1.json"
    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError,
        match="MANIFEST_VERIFY_RC_INVALID",
    ):
        load_futures_producer_packet_governed(bundle_path, archive_root=archive)


def test_build_from_u5d_minimal_fixture_nested_shape(build_mod: Any, tmp_path: Path) -> None:
    transform = importlib.util.spec_from_file_location(
        "_u5d",
        _REPO_ROOT / "scripts/ops/transform_kraken_futures_raw_to_u2c_candidate_v1.py",
    )
    assert transform is not None and transform.loader is not None
    u5d_mod = importlib.util.module_from_spec(transform)
    transform.loader.exec_module(u5d_mod)

    archive = _durable_archive_root(tmp_path)
    u5d_out = archive / "runtime" / "u5d_minimal"
    artifact = u5d_mod.run_offline_transform_validation(
        confirm="CONFIRM_U5D_OFFLINE_TRANSFORM_VALIDATION_V1",
        raw_instruments=_U5D_FIXTURES / "kraken_futures_instruments.raw.v1.json",
        raw_tickers=_U5D_FIXTURES / "kraken_futures_tickers.raw.v1.json",
        probe_report=_U5D_FIXTURES / "kraken_futures_public_market_data_probe_report.v1.json",
        output_dir=u5d_out,
    )
    assert len(artifact["packet_candidates"]) == 3

    out_dir = archive / "governed_metadata" / "from_minimal_u5d_v1"
    summary = build_mod.build_governed_snapshot_candidate_bundle(
        confirm=_CONFIRM_BUILD,
        u5d_validation_path=u5d_out / "u5d_u2c_candidate_validation.v1.json",
        output_dir=out_dir,
        archive_root=archive,
        bundle_id="from_minimal_u5d_v1",
    )
    assert summary["nested_packet_shape"] is True
    governed = json.loads((out_dir / "futures_producer_packet_governed.v1.json").read_text())
    assert all("candidate" in p for p in governed["packets"])
    assert "BTC/USD" not in json.dumps(governed)
    assert governed["u2b_candidate_validation_only"] is True
    assert all(p["instrument"]["candidate_validation_complete"] for p in governed["packets"])
    assert all(p["instrument"]["complete"] is False for p in governed["packets"])

    evidence = archive / "runs" / "paper" / "minimal_evidence"
    evidence.mkdir(parents=True)
    (evidence / "CLOSEOUT.md").write_text("# evidence\n", encoding="utf-8")
    u5d_for_u2b = archive / "runtime" / "u5d_minimal_u2b"
    u5d_for_u2b.mkdir(parents=True)
    artifact = json.loads((u5d_out / "u5d_u2c_candidate_validation.v1.json").read_text())
    artifact.pop("input_paths", None)
    (u5d_for_u2b / "u5d_u2c_candidate_validation.v1.json").write_text(
        json.dumps(artifact) + "\n",
        encoding="utf-8",
    )
    out_dir2 = archive / "governed_metadata" / "from_minimal_u5d_u2b_v1"
    build_mod.build_governed_snapshot_candidate_bundle(
        confirm=_CONFIRM_BUILD,
        u5d_validation_path=u5d_for_u2b / "u5d_u2c_candidate_validation.v1.json",
        output_dir=out_dir2,
        archive_root=archive,
        bundle_id="from_minimal_u5d_u2b_v1",
        evidence_links=(str(evidence.resolve()),),
    )
    bundle = load_futures_producer_packet_governed(
        out_dir2 / "futures_producer_packet_governed.v1.json",
        archive_root=archive,
    )
    assert len(bundle.packets) == 3
    assert all(
        raw["instrument"]["candidate_validation_complete"]
        for raw in json.loads((out_dir2 / "futures_producer_packet_governed.v1.json").read_text())[
            "packets"
        ]
    )
