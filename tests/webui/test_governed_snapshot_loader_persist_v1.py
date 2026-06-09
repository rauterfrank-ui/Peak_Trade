"""U2b — governed snapshot loader persist surface v1 tests."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    parse_manifest_verify_log_rc,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from scripts.ops import persist_u2b_governed_snapshot_loader_run_v1 as persist_cli
from src.webui.workflow_dashboard_readmodel_v1.futures_producer_packet_real_metadata_source_v1 import (
    LOADER_PERSIST_CONFIRM_TOKEN,
    REASON_CONFIRM_TOKEN_INVALID,
    REASON_INSTRUMENT_INCOMPLETE,
    FuturesProducerPacketRealMetadataSourceError,
    bundle_to_upstream_input,
    governed_root_under,
    load_futures_producer_packet_governed,
    persist_governed_snapshot_loader_run_v1,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_TEMPLATE_ROOT = governed_root_under(PROJECT_ROOT)
SCRATCH_ROOT = PROJECT_ROOT / "tests" / "_durable_archive_scratch"


def _durable_archive_root(tmp_path: Path) -> Path:
    candidate = tmp_path / "archive_root"
    candidate.mkdir(parents=True, exist_ok=True)
    if not is_under_tmp(candidate):
        return candidate
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    durable = SCRATCH_ROOT / str(uuid.uuid4())
    durable.mkdir(parents=True, exist_ok=True)
    return durable


def _seed_metadata_manifest(metadata_dir: Path) -> None:
    write_manifest_sha256(metadata_dir)
    verify_ok, verify_msg = verify_manifest_sha256(metadata_dir)
    assert verify_ok, verify_msg
    (metadata_dir / "MANIFEST_VERIFY.log").write_text(
        f"verify_ok=true\nmessage={verify_msg}\nMANIFEST_VERIFY_RC=0\nSTATUS=OK\n",
        encoding="utf-8",
    )
    write_manifest_sha256(metadata_dir)


def _install_governed_bundle(archive_root: Path, template_name: str) -> Path:
    data = json.loads((FIXTURE_TEMPLATE_ROOT / template_name).read_text(encoding="utf-8"))
    metadata_dir = archive_root / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = metadata_dir / "futures_instrument_metadata_snapshot.v1.json"
    snapshot_path.write_text(
        (FIXTURE_TEMPLATE_ROOT / "futures_instrument_metadata_snapshot.v1.json").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    _seed_metadata_manifest(metadata_dir)

    evidence_link = archive_root / "runs" / "paper" / "u2b_evidence"
    evidence_link.mkdir(parents=True, exist_ok=True)
    (evidence_link / "CLOSEOUT.md").write_text("# u2b evidence\n", encoding="utf-8")

    data["metadata_table_ref"] = str(snapshot_path.resolve())
    data["evidence_links"] = [str(evidence_link.resolve())]

    bundle_path = metadata_dir / f"installed_{template_name}"
    bundle_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return bundle_path.resolve()


def test_persist_requires_confirm_token(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    out_dir = archive_root / "runtime" / "loader_persist_v1"
    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError, match=REASON_CONFIRM_TOKEN_INVALID
    ):
        persist_governed_snapshot_loader_run_v1(
            confirm_token="WRONG_TOKEN",
            candidate_bundle_path=bundle_path,
            output_dir=out_dir,
            archive_root=archive_root,
        )


def test_persist_writes_record_and_manifest(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    out_dir = archive_root / "runtime" / "loader_persist_v1"
    summary = persist_governed_snapshot_loader_run_v1(
        confirm_token=LOADER_PERSIST_CONFIRM_TOKEN,
        candidate_bundle_path=bundle_path,
        output_dir=out_dir,
        archive_root=archive_root,
    )
    assert summary["manifest_verify_rc"] == 0
    rc, _, _ = parse_manifest_verify_log_rc(out_dir)
    assert rc == 0
    safety = json.loads((out_dir / "loader_safety_flags.v1.json").read_text(encoding="utf-8"))
    assert safety["LOADER_PERSIST_EXECUTED"] is True
    assert safety["READMODEL_WRITE_EXECUTED"] is False
    assert safety["TRUTH_GO_GRANTED"] is False
    assert not (archive_root / "readmodels").exists()


def test_persist_does_not_invoke_readmodel_write(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    out_dir = archive_root / "runtime" / "loader_persist_no_readmodel_v1"

    with patch(
        "src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1.write_universe_selection_readmodel",
        side_effect=AssertionError("readmodel write must not be called"),
    ):
        persist_governed_snapshot_loader_run_v1(
            confirm_token=LOADER_PERSIST_CONFIRM_TOKEN,
            candidate_bundle_path=bundle_path,
            output_dir=out_dir,
            archive_root=archive_root,
        )


def test_persist_candidate_validation_bundle_and_upstream_still_blocked(
    tmp_path: Path,
) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    data = json.loads(bundle_path.read_text(encoding="utf-8"))
    packet = data["packets"][0]
    instrument = packet["instrument"]
    instrument["complete"] = False
    instrument["candidate_validation_complete"] = True
    instrument["min_notional_known"] = False
    instrument["missing_provider_metadata"] = ["min_notional"]
    data["u2b_candidate_validation_only"] = True
    data["instrument_completeness_mode"] = "candidate_validation"
    data["missing_provider_metadata_policy"] = {
        "allowed_missing_provider_metadata": ["min_notional"],
        "reason": "fixture_only_candidate_validation",
        "not_loader_write_eligible": True,
        "not_observability_truth": True,
    }
    bundle_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    out_dir = archive_root / "runtime" / "loader_persist_candidate_validation_v1"
    summary = persist_governed_snapshot_loader_run_v1(
        confirm_token=LOADER_PERSIST_CONFIRM_TOKEN,
        candidate_bundle_path=bundle_path,
        output_dir=out_dir,
        archive_root=archive_root,
    )
    assert summary["completeness_summary"]["candidate_validation_complete_count"] == 1

    bundle = load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)
    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError, match=REASON_INSTRUMENT_INCOMPLETE
    ):
        bundle_to_upstream_input(bundle)


def test_persist_cli_rejects_bad_confirm_token(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    out_dir = archive_root / "runtime" / "loader_persist_cli_bad_token_v1"
    with pytest.raises(SystemExit) as exc:
        persist_cli.main(
            [
                "--candidate-bundle",
                str(bundle_path),
                "--output-dir",
                str(out_dir),
                "--archive-root",
                str(archive_root),
                "--confirm-token",
                "WRONG",
            ]
        )
    assert exc.value.code != 0
    assert not out_dir.exists()


def test_persist_cli_success(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    out_dir = archive_root / "runtime" / "loader_persist_cli_success_v1"
    rc = persist_cli.main(
        [
            "--candidate-bundle",
            str(bundle_path),
            "--output-dir",
            str(out_dir),
            "--archive-root",
            str(archive_root),
            "--confirm-token",
            LOADER_PERSIST_CONFIRM_TOKEN,
        ]
    )
    assert rc == 0
    assert (out_dir / "loader_persist_record.v1.json").is_file()
