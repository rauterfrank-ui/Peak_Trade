"""Candidate-validation projection bridge — non-truth readmodel prep (bounded PR)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest import mock

import pytest

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.webui.workflow_dashboard_readmodel_v1.futures_producer_packet_real_metadata_source_v1 import (
    CANDIDATE_VALIDATION_PROJECTION_SOURCE,
    REASON_INSTRUMENT_INCOMPLETE,
    FuturesProducerPacketRealMetadataSourceError,
    bundle_to_upstream_input,
    governed_root_under,
    load_futures_producer_packet_governed,
    project_governed_candidate_validation_bundle_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.futures_universe_upstream_adapter_v1 import (
    REASON_INELIGIBLE_INSTRUMENT_METADATA_INCOMPLETE,
    evaluate_packet_eligibility,
    evaluate_packet_eligibility_candidate_validation,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1 import (
    validate_universe_selection_payload,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    build_real_metadata_mapped_universe_selection_readmodel_candidate_validation,
    write_universe_selection_readmodel,
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


def _install_cvc_governed_bundle(archive_root: Path) -> Path:
    data = json.loads(
        (FIXTURE_TEMPLATE_ROOT / "governed_packet_valid_minimal.json").read_text(encoding="utf-8")
    )
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

    evidence_link = archive_root / "runs" / "paper" / "cvc_evidence"
    evidence_link.mkdir(parents=True, exist_ok=True)
    (evidence_link / "CLOSEOUT.md").write_text("# cvc evidence\n", encoding="utf-8")

    packet = data["packets"][0]
    instrument = packet["instrument"]
    instrument["complete"] = False
    instrument["candidate_validation_complete"] = True
    instrument["min_notional_known"] = False
    instrument["missing_provider_metadata"] = ["min_notional"]
    data["selected_candidate_id"] = None
    data["selected_future"] = {
        "candidate_id": None,
        "symbol": None,
        "notes": "no selected tradable future",
    }
    data["u2b_candidate_validation_only"] = True
    data["instrument_completeness_mode"] = "candidate_validation"
    data["missing_provider_metadata_policy"] = {
        "allowed_missing_provider_metadata": ["min_notional"],
        "reason": "fixture_only_candidate_validation",
        "not_loader_write_eligible": True,
        "not_observability_truth": True,
    }
    data["metadata_table_ref"] = str(snapshot_path.resolve())
    data["evidence_links"] = [str(evidence_link.resolve())]

    bundle_path = metadata_dir / "governed_packet_candidate_validation.json"
    bundle_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return bundle_path.resolve()


def test_strict_bundle_to_upstream_input_still_blocked_for_cvc(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_cvc_governed_bundle(archive_root)
    bundle = load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)
    assert bundle.packets[0].instrument.complete is False
    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError,
        match=REASON_INSTRUMENT_INCOMPLETE,
    ):
        bundle_to_upstream_input(bundle)


def test_strict_evaluate_packet_eligibility_still_blocked_for_cvc(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_cvc_governed_bundle(archive_root)
    bundle = load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)
    packet = bundle.packets[0]
    raw = json.loads(bundle_path.read_text(encoding="utf-8"))["packets"][0]["instrument"]
    eligible_strict, reason_strict = evaluate_packet_eligibility(packet)
    eligible_cvc, reason_cvc = evaluate_packet_eligibility_candidate_validation(
        packet,
        raw_instrument=raw,
    )
    assert eligible_strict is False
    assert reason_strict == REASON_INELIGIBLE_INSTRUMENT_METADATA_INCOMPLETE
    assert eligible_cvc is True
    assert reason_cvc is None


def test_candidate_validation_projection_populates_universe_without_selected_future(
    tmp_path: Path,
) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_cvc_governed_bundle(archive_root)
    projection = project_governed_candidate_validation_bundle_v1(
        bundle_path,
        archive_root=archive_root,
    )
    assert projection.projection_source == CANDIDATE_VALIDATION_PROJECTION_SOURCE
    assert projection.observability_truth_allowed is False
    assert projection.selected_tradable_future_created is False
    assert projection.instrument_complete_forced is False
    assert projection.readmodel_write_executed is False
    assert projection.strict_upstream_blocked is True
    assert projection.packet_count == 1
    assert projection.candidate_validation_eligible_count == 1
    assert projection.adapter_status == "candidate_validation_projection"

    payload = projection.readmodel_payload
    validate_universe_selection_payload(payload)
    assert len(payload["universe"]) == 1
    assert len(payload["ranking"]) == 1
    assert payload["selected_future"]["truth_status"] == "NOT_PERSISTED"
    assert payload["observability_truth_allowed"] is False
    assert payload["evidence"]["projection_source"] == CANDIDATE_VALIDATION_PROJECTION_SOURCE


def test_build_candidate_validation_readmodel_payload_without_write(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_cvc_governed_bundle(archive_root)
    with mock.patch(
        "src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1.write_universe_selection_readmodel",
        side_effect=AssertionError("readmodel write must not run"),
    ):
        payload = build_real_metadata_mapped_universe_selection_readmodel_candidate_validation(
            archive_root=archive_root,
            governed_bundle_path=bundle_path,
        )
    validate_universe_selection_payload(payload)
    assert payload["observability_truth_allowed"] is False
    assert payload["selected_future"]["truth_status"] == "NOT_PERSISTED"
    assert payload["evidence"]["candidate_validation_projection"] is True


def test_write_universe_selection_readmodel_not_called_by_projection_path(
    tmp_path: Path,
) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_cvc_governed_bundle(archive_root)
    with mock.patch.object(
        write_universe_selection_readmodel,
        "__call__",
        side_effect=AssertionError("readmodel write must not run"),
    ):
        build_real_metadata_mapped_universe_selection_readmodel_candidate_validation(
            archive_root=archive_root,
            governed_bundle_path=bundle_path,
        )
