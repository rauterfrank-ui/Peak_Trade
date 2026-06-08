"""Unit tests for universe_selection_producer_v1 (Slice 2 — helper-only, no runtime)."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from scripts.ops.primary_evidence_retention_v0 import is_under_tmp, verify_manifest_sha256
from src.webui.workflow_dashboard_readmodel_v1 import (
    ProducerWriteError,
    UniverseSelectionContractError,
    build_missing_truth_universe_selection_readmodel,
    load_universe_selection_contract,
    validate_universe_selection_payload,
    write_missing_truth_universe_selection_readmodel,
    write_universe_selection_readmodel,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1 import (
    MISSING_TRUTH_SELECTED,
    MISSING_TRUTH_UNIVERSE,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    READMODEL_FILENAME,
    READMODELS_DIRNAME,
)

SCRATCH_ROOT = project_root / "tests" / "_durable_archive_scratch"


@pytest.fixture
def archive_root(tmp_path: Path) -> Path:
    candidate = tmp_path / "archive_root"
    candidate.mkdir(parents=True, exist_ok=True)
    if not is_under_tmp(candidate):
        return candidate
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    durable = SCRATCH_ROOT / str(uuid.uuid4())
    durable.mkdir(parents=True, exist_ok=True)
    return durable


def test_build_missing_truth_payload_validates() -> None:
    payload = build_missing_truth_universe_selection_readmodel(
        source_run_id="p1_short_bounded_paper_test",
        source_stage="paper",
        generated_at="2026-06-08T14:00:00Z",
        run_bundle_path="/archive/runs/p1_short_bounded_paper_test",
    )
    contract = validate_universe_selection_payload(payload)
    assert contract.universe == ()
    assert contract.ranking == ()
    assert contract.selected_future is None
    assert contract.missing_truth.universe == MISSING_TRUTH_UNIVERSE
    assert contract.missing_truth.selected_future == MISSING_TRUTH_SELECTED
    assert payload["evidence"]["links"] == ["/archive/runs/p1_short_bounded_paper_test"]


def test_write_missing_truth_creates_readmodel_and_manifest(archive_root: Path) -> None:
    run_bundle = str(archive_root / "runs" / "p1_short_bounded_paper_test")
    result = write_missing_truth_universe_selection_readmodel(
        archive_root,
        source_run_id="p1_short_bounded_paper_test",
        source_stage="paper",
        generated_at="2026-06-08T14:00:00Z",
        run_bundle_path=run_bundle,
    )

    readmodels_dir = archive_root / READMODELS_DIRNAME
    readmodel_path = readmodels_dir / READMODEL_FILENAME
    manifest_path = readmodels_dir / "MANIFEST.sha256"

    assert readmodel_path.is_file()
    assert manifest_path.is_file()
    assert result.manifest_verify_ok is True
    assert result.manifest_verify_rc == 0
    assert result.readmodel_path == str(readmodel_path)

    contract = load_universe_selection_contract(readmodel_path)
    assert contract.source_run_id == "p1_short_bounded_paper_test"
    assert contract.source_stage == "paper"
    assert run_bundle in contract.evidence["links"]

    ok, msg = verify_manifest_sha256(readmodels_dir)
    assert ok, msg


def test_atomic_write_leaves_no_tmp_files(archive_root: Path) -> None:
    write_missing_truth_universe_selection_readmodel(
        archive_root,
        source_run_id="s1_shadow_test",
        source_stage="shadow",
        run_bundle_path=str(archive_root / "runs" / "s1_shadow_test"),
    )
    readmodels_dir = archive_root / READMODELS_DIRNAME
    leftovers = [
        p.name
        for p in readmodels_dir.iterdir()
        if p.name.startswith(f".{READMODEL_FILENAME}.") and p.name.endswith(".tmp")
    ]
    assert leftovers == []


def test_evidence_links_include_run_bundle_and_stage_metadata(archive_root: Path) -> None:
    run_bundle = str(archive_root / "runs" / "t2_medium_testnet_test")
    payload = build_missing_truth_universe_selection_readmodel(
        source_run_id="t2_medium_testnet_test",
        source_stage="testnet",
        run_bundle_path=run_bundle,
        run_bundle_uri="file:///archive/runs/t2_medium_testnet_test",
    )
    assert run_bundle in payload["evidence"]["links"]
    assert "file:///archive/runs/t2_medium_testnet_test" in payload["evidence"]["links"]
    assert payload["source_run_id"] == "t2_medium_testnet_test"
    assert payload["source_stage"] == "testnet"


def test_btc_usd_selected_truth_rejected_on_write(archive_root: Path) -> None:
    payload = build_missing_truth_universe_selection_readmodel(
        source_run_id="reject_btc",
        source_stage="paper",
        run_bundle_path="/archive/runs/reject_btc",
    )
    payload["selected_future"] = {
        "row_id": "row-1",
        "symbol": "BTC/USD",
        "rank": 1,
        "truth_status": "PERSISTED",
    }
    payload["missing_truth"]["selected_future"] = "PERSISTED"
    with pytest.raises(ProducerWriteError, match="forbidden"):
        write_universe_selection_readmodel(archive_root, payload)


def test_live_source_stage_rejected_on_write(archive_root: Path) -> None:
    payload = build_missing_truth_universe_selection_readmodel(
        source_run_id="reject_live",
        source_stage="paper",
        run_bundle_path="/archive/runs/reject_live",
    )
    payload["source_stage"] = "live"
    with pytest.raises(ProducerWriteError, match="forbidden"):
        write_universe_selection_readmodel(archive_root, payload)


def test_dry_run_does_not_mutate_archive(archive_root: Path) -> None:
    result = write_missing_truth_universe_selection_readmodel(
        archive_root,
        source_run_id="dry_run_only",
        source_stage="paper",
        run_bundle_path=str(archive_root / "runs" / "dry_run_only"),
        dry_run=True,
    )
    assert result.dry_run is True
    assert not (archive_root / READMODELS_DIRNAME).exists()


def test_tmp_archive_root_rejected() -> None:
    import tempfile

    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        tmp_archive = Path(tmp_dir) / "archive_root"
        tmp_archive.mkdir()
        with pytest.raises(ProducerWriteError, match="outside /tmp"):
            write_missing_truth_universe_selection_readmodel(
                tmp_archive,
                source_run_id="tmp_reject",
                source_stage="paper",
                run_bundle_path=str(tmp_archive / "runs" / "tmp_reject"),
            )


def test_written_payload_is_valid_json(archive_root: Path) -> None:
    write_missing_truth_universe_selection_readmodel(
        archive_root,
        source_run_id="json_ok",
        source_stage="testnet",
        run_bundle_path=str(archive_root / "runs" / "json_ok"),
    )
    raw = (archive_root / READMODELS_DIRNAME / READMODEL_FILENAME).read_text(encoding="utf-8")
    loaded = json.loads(raw)
    validate_universe_selection_payload(loaded)


def test_missing_inputs_write_explicit_missing_truth_not_rows(archive_root: Path) -> None:
    write_missing_truth_universe_selection_readmodel(
        archive_root,
        source_run_id="explicit_missing",
        source_stage="paper",
        run_bundle_path=str(archive_root / "runs" / "explicit_missing"),
    )
    contract = load_universe_selection_contract(
        archive_root / READMODELS_DIRNAME / READMODEL_FILENAME
    )
    assert contract.universe == ()
    assert contract.ranking == ()
    assert contract.missing_truth.universe == MISSING_TRUTH_UNIVERSE
    with pytest.raises(UniverseSelectionContractError):
        payload = json.loads(
            (archive_root / READMODELS_DIRNAME / READMODEL_FILENAME).read_text(encoding="utf-8")
        )
        payload["universe"] = [
            {"row_id": "u1", "symbol": "BTC/USD", "rank": 1},
        ]
        validate_universe_selection_payload(payload)
