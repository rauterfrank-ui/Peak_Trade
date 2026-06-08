"""U2b — futures_producer_packet_real_metadata_source_v1 contract/static tests."""

from __future__ import annotations

import ast
import json
import uuid
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.webui.workflow_dashboard_readmodel_v1.futures_producer_packet_real_metadata_source_v1 import (
    GOVERNED_PRODUCER_ID,
    GOVERNED_SOURCE_KIND,
    REASON_EVIDENCE_LINKS_EMPTY,
    REASON_FIXTURE_ONLY_MUST_BE_FALSE,
    REASON_FORBIDDEN_GOVERNANCE_FIELD,
    REASON_FORBIDDEN_UPSTREAM_SOURCE,
    REASON_FRESHNESS_NOT_FRESH,
    REASON_INELIGIBLE_SPOT_SYMBOL,
    REASON_MANIFEST_VERIFY_RC_INVALID,
    REASON_PATH_UNDER_REPO_FIXTURES,
    REASON_PATH_UNDER_TMP,
    FuturesProducerPacketRealMetadataSourceError,
    assert_governed_not_observability_truth,
    bundle_to_upstream_input,
    governed_root_under,
    load_futures_producer_packet_governed,
)
from src.webui.workflow_dashboard_readmodel_v1.futures_universe_upstream_adapter_v1 import (
    map_futures_packets_to_universe_selection_readmodel,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_TEMPLATE_ROOT = governed_root_under(PROJECT_ROOT)
SOURCE_MODULE = (
    PROJECT_ROOT
    / "src"
    / "webui"
    / "workflow_dashboard_readmodel_v1"
    / "futures_producer_packet_real_metadata_source_v1.py"
)
SCRATCH_ROOT = PROJECT_ROOT / "tests" / "_durable_archive_scratch"
FORBIDDEN_SPOT_SYMBOLS = ("BTC/USD", "BTC/EUR", "ETH/USD")


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


def test_tc1_valid_governed_bundle_loads_and_preserves_non_authorizing(
    tmp_path: Path,
) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")

    bundle = load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)

    assert bundle.source_kind == GOVERNED_SOURCE_KIND
    assert bundle.producer_id == GOVERNED_PRODUCER_ID
    assert bundle.fixture_only is False
    assert bundle.observability_truth_allowed is False
    assert bundle.non_authorizing is True
    assert bundle.real_metadata_source_marked is True
    assert len(bundle.packets) == 1
    assert_governed_not_observability_truth(bundle)

    upstream = bundle_to_upstream_input(bundle)
    assert upstream.fixture_marked is False
    result = map_futures_packets_to_universe_selection_readmodel(upstream)
    assert result.status == "ok"
    assert result.payload["non_authorizing"] is True
    assert result.payload.get("observability_truth_allowed") is not True


def test_tc2_rejects_tmp_archive_root(tmp_path: Path) -> None:
    tmp_archive = Path("/tmp") / f"u2b_archive_{uuid.uuid4()}"
    tmp_archive.mkdir(parents=True, exist_ok=True)
    try:
        bundle_path = _install_governed_bundle(tmp_archive, "governed_packet_valid_minimal.json")
        with pytest.raises(
            FuturesProducerPacketRealMetadataSourceError,
            match=REASON_PATH_UNDER_TMP,
        ):
            load_futures_producer_packet_governed(bundle_path, archive_root=tmp_archive)
    finally:
        import shutil

        shutil.rmtree(tmp_archive, ignore_errors=True)


def test_tc2b_rejects_repo_fixture_path_directly(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    fixture_path = FIXTURE_TEMPLATE_ROOT / "governed_packet_valid_minimal.json"

    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError,
        match=REASON_PATH_UNDER_REPO_FIXTURES,
    ):
        load_futures_producer_packet_governed(fixture_path, archive_root=archive_root)


def test_tc3_rejects_fixture_source_kind(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_fixture_source_kind.json")

    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError,
        match=REASON_FORBIDDEN_UPSTREAM_SOURCE,
    ):
        load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)


def test_tc4_rejects_market_ranking_funnel_source_kind(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(
        archive_root, "governed_packet_forbidden_source_kind.json"
    )

    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError,
        match=REASON_FORBIDDEN_UPSTREAM_SOURCE,
    ):
        load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)


def test_tc5_rejects_spot_selected_symbol(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_spot_invalid.json")

    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError,
        match=REASON_INELIGIBLE_SPOT_SYMBOL,
    ):
        load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)


def test_tc6_rejects_stale_freshness(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_stale_provenance.json")

    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError,
        match=REASON_FRESHNESS_NOT_FRESH,
    ):
        load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)


def test_tc7_rejects_missing_evidence_links(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
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

    data = json.loads(
        (FIXTURE_TEMPLATE_ROOT / "governed_packet_missing_evidence_links.json").read_text(
            encoding="utf-8"
        )
    )
    data["metadata_table_ref"] = str(snapshot_path.resolve())
    bundle_path = metadata_dir / "missing_evidence_installed.json"
    bundle_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError,
        match=REASON_EVIDENCE_LINKS_EMPTY,
    ):
        load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)


def test_tc8_rejects_manifest_verify_rc_not_zero(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    metadata_dir = archive_root / "metadata"
    (metadata_dir / "MANIFEST_VERIFY.log").write_text(
        "verify_ok=false\nmessage=forced\nMANIFEST_VERIFY_RC=1\nSTATUS=FAILED\n",
        encoding="utf-8",
    )

    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError,
        match=REASON_MANIFEST_VERIFY_RC_INVALID,
    ):
        load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)


def test_tc9_rejects_approval_field(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_approval_field.json")

    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError,
        match=REASON_FORBIDDEN_GOVERNANCE_FIELD,
    ):
        load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)


def test_tc10_rejects_fixture_only_true(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    data = json.loads(bundle_path.read_text(encoding="utf-8"))
    data["fixture_only"] = True
    bundle_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(
        FuturesProducerPacketRealMetadataSourceError,
        match=REASON_FIXTURE_ONLY_MUST_BE_FALSE,
    ):
        load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)


def test_tc11_no_forbidden_network_imports() -> None:
    forbidden_import_roots = ("urllib", "requests", "httpx", "aiohttp", "socket")
    tree = ast.parse(SOURCE_MODULE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots


def test_tc12_spot_symbols_not_in_valid_bundle(tmp_path: Path) -> None:
    archive_root = _durable_archive_root(tmp_path)
    bundle_path = _install_governed_bundle(archive_root, "governed_packet_valid_minimal.json")
    bundle = load_futures_producer_packet_governed(bundle_path, archive_root=archive_root)
    for packet in bundle.packets:
        assert packet.candidate.symbol not in FORBIDDEN_SPOT_SYMBOLS
