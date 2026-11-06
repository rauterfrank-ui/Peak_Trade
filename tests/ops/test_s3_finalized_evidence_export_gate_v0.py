"""Static contract tests for S3 finalized evidence export gate v0 (taxonomy §6a.3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc

REPO_ROOT = pc.REPO_ROOT
TAXONOMY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
PRIMARY_EVIDENCE_SCRIPT = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
REGISTRY_SCRIPT = pc.REGISTRY_SCRIPT
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
PHASE_T_RUNBOOK = REPO_ROOT / "docs" / "ops" / "runbooks" / "PHASE_T_DATA_NODE_EXPORT_CHANNEL.md"
PHASE_W_RUNBOOK = REPO_ROOT / "docs" / "ops" / "runbooks" / "PHASE_W_EXPORT_PACK_GH_CONSUMER.md"
REMOTE_RUNTIME_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_remote_runtime_host_metadata_contract_v0.py"
)
PROJECTION_FIXTURE_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_registry_v1_projection_consumer_smoke_fixtures_v0.py"
)

S3_GATE_SPEC_MARKERS = (
    "S3_FINALIZED_EVIDENCE_EXPORT_GATE_V0=true",
    "S3_FINALIZED_EVIDENCE_TRANSPORT_ONLY=true",
    "S3_EXPORT_GATE_DOCS_TESTS_ONLY=true",
    "S3_AUTHORITY=false",
    "S3_UPLOAD_BEFORE_FINALIZE_FORBIDDEN=true",
    "ACTIVE_STAGING_SYNC_FORBIDDEN=true",
    "DOWNLOAD_VERIFY_REQUIRED_BEFORE_CLOSEOUT_ACCEPTANCE=true",
    "MANIFEST_SHA256_REMAINS_CANONICAL=true",
    "SHA256SUMS_STABLE_PARALLEL_TRUTH_FORBIDDEN=true",
    "RUNTIME_AUTHORITY=false",
    "SCHEDULER_CLEARANCE_AUTHORITY=false",
    "LIVE_AUTHORITY=false",
    "TESTNET_AUTHORITY=false",
    "BROKER_AUTHORITY=false",
    "NOTION_AUTHORITY=false",
    "MARKET_DASHBOARD_AUTHORITY=false",
    "DOUBLE_PLAY_AUTHORITY=false",
    "EVIDENCE_TRANSPORT_DEFAULT=local_only",
)

EVIDENCE_TRANSPORT_STATES = ("local_only", "s3_export_after_finalize")

S3_ALLOWED_PROJECTION_FIELDS = (
    "run_id",
    "lane_id",
    "composition_id",
    "record_kind",
    "evidence_transport",
    "evidence_status",
    "manifest_verified",
    "archive_path",
)


def _section_6a3() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split("### 6a.3 S3 finalized evidence export gate contract v0", 1)[1].split(
        "### 6a.3.1 S3 finalized evidence export implementation preflight contract v0", 1
    )[0]


def test_taxonomy_section_6a3_present() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "### 6a.3 S3 finalized evidence export gate contract v0" in text
    for marker in S3_GATE_SPEC_MARKERS:
        assert marker in text


def test_evidence_transport_states_and_default_documented() -> None:
    section = _section_6a3()
    for state in EVIDENCE_TRANSPORT_STATES:
        assert f"`{state}`" in section
    assert "EVIDENCE_TRANSPORT_DEFAULT=local_only" in section
    assert "evidence_transport=local_only" in section
    mod = pc.load_registry_module(module_name="build_generic_evidence_run_registry_v1_s3_gate")
    assert mod.EVIDENCE_TRANSPORT_DEFAULT == "local_only"
    assert mod.REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS["evidence_transport"] == "local_only"


def test_s3_export_after_finalize_requires_finalize_and_manifest_verify() -> None:
    section = _section_6a3()
    assert "finalize_primary_evidence_root" in section
    assert "MANIFEST.sha256" in section
    assert "RC=0" in section
    assert "manifest_verified=true" in section
    primary_text = PRIMARY_EVIDENCE_SCRIPT.read_text(encoding="utf-8")
    assert "def finalize_primary_evidence_root" in primary_text


def test_active_staging_sync_forbidden() -> None:
    section = _section_6a3().lower()
    assert "active staging sync" in section
    assert "active_staging_sync_forbidden=true" in section
    assert "forbidden" in section


def test_download_verify_required_before_closeout_acceptance() -> None:
    section = _section_6a3()
    assert "DOWNLOAD_VERIFY_REQUIRED_BEFORE_CLOSEOUT_ACCEPTANCE=true" in section
    assert "download" in section.lower()
    assert "closeout acceptance" in section.lower()


def test_manifest_sha256_remains_canonical_no_sha256sums_stable_parallel_truth() -> None:
    section = _section_6a3()
    assert "MANIFEST_SHA256_REMAINS_CANONICAL=true" in section
    assert "SHA256SUMS_STABLE_PARALLEL_TRUTH_FORBIDDEN=true" in section
    assert "SHA256SUMS.stable.txt" in section
    assert "competing truth" in section.lower() or "parallel truth" in section.lower()
    taxonomy_text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "SHA256SUMS.stable.txt" in taxonomy_text
    assert "Introducing `SHA256SUMS.stable.txt` as competing truth" in taxonomy_text


def test_s3_relevant_projection_fields_covered() -> None:
    section = _section_6a3()
    for field in pc.S3_RELEVANT_PROJECTION_FIELDS:
        assert field in section
    for field in S3_ALLOWED_PROJECTION_FIELDS:
        assert field in section


def test_canonical_boundary_copy_present() -> None:
    section = _section_6a3()
    assert "S3/Object Storage is finalized evidence transport only" in section
    assert "MANIFEST.sha256 remains canonical" in section


def test_forbidden_authority_markers_and_no_new_lanes() -> None:
    section = _section_6a3().lower()
    for marker in (
        "s3_authority=false",
        "notion_authority=false",
        "market_dashboard_authority=false",
        "double_play_authority=false",
    ):
        assert marker in section
    assert "lane_id=daemon_paper_24h" in section
    assert "lane_id=remote_runtime" in section
    assert "generic_evidence_run_registry.v2" not in section


def test_phase_t_and_phase_w_cross_referenced_as_extend_only() -> None:
    section = _section_6a3()
    assert "PHASE_T_DATA_NODE_EXPORT_CHANNEL.md" in section
    assert "PHASE_W_EXPORT_PACK_GH_CONSUMER.md" in section
    assert PHASE_T_RUNBOOK.is_file()
    assert PHASE_W_RUNBOOK.is_file()
    assert "extend" in section.lower()


def test_registry_fixture_default_local_only_with_s3_fields(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    pc.write_minimal_paper_run(archive)
    payload = pc.build_registry(archive)
    run = payload["runs"][0]
    assert run["evidence_transport"] == "local_only"
    for field in pc.S3_RELEVANT_PROJECTION_FIELDS:
        assert field in run
    pc.assert_non_authorizing_run_projection_defaults(run)
    assert payload["schema"] == "peak_trade.generic_evidence_run_registry.v1"
    assert "generic_evidence_run_registry.v2" not in json.dumps(payload)


def test_registry_module_exposes_s3_gate_constants() -> None:
    mod = pc.load_registry_module(module_name="build_generic_evidence_run_registry_v1_s3_gate")
    assert mod.S3_FINALIZED_EVIDENCE_EXPORT_GATE_V0 is True
    assert mod.EVIDENCE_TRANSPORT_DEFAULT == "local_only"


def test_owner_crosslinks() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    assert REMOTE_RUNTIME_TESTS.name in owner_text
    assert PROJECTION_FIXTURE_TESTS.name in owner_text
    assert "test_remote_runtime_contract_docs_guard_v0.py" in owner_text
    remote_text = REMOTE_RUNTIME_TESTS.read_text(encoding="utf-8")
    assert "S3_FINALIZED_EVIDENCE_TRANSPORT_ONLY=true" in remote_text


def test_section_6a3_references_implemented_preflight_cli() -> None:
    section = _section_6a3()
    assert "S3_EXPORT_PREFLIGHT_CLI_IMPLEMENTED=true" in section
    assert "preflight_s3_finalized_evidence_export_v0.py" in section
    assert "§6a.3.1" in section


def test_docs_truth_map_references_s3_export_gate() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "6a.3" in text or "S3 finalized evidence export gate" in text
    assert TAXONOMY_SPEC.name in text
