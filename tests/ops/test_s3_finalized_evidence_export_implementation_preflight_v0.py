"""Static contract tests for S3 finalized evidence export implementation preflight v0 (taxonomy §6a.3.1)."""

from __future__ import annotations

import json
from pathlib import Path

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
S3_GATE_TESTS = REPO_ROOT / "tests" / "ops" / "test_s3_finalized_evidence_export_gate_v0.py"
REMOTE_RUNTIME_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_remote_runtime_host_metadata_contract_v0.py"
)
PROJECTION_FIXTURE_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_registry_v1_projection_consumer_smoke_fixtures_v0.py"
)

PREFLIGHT_SPEC_MARKERS = (
    "S3_FINALIZED_EVIDENCE_EXPORT_IMPLEMENTATION_PREFLIGHT_V0=true",
    "S3_EXPORT_PREFLIGHT_DOCS_TESTS_ONLY=true",
    "S3_EXPORT_DRY_RUN_DEFAULT=true",
    "S3_EXPORT_NO_NETWORK_DEFAULT=true",
    "LOCAL_ONLY_DRY_ADAPTER_CONTRACT_DOCUMENTED=true",
    "PHASE_T_W_EXTEND_ONLY=true",
    "PHASE_T_W_RECONCILED_TO_MANIFEST_SHA256=true",
    "MANIFEST_SHA256_REMAINS_CANONICAL=true",
    "SHA256SUMS_STABLE_PARALLEL_TRUTH_FORBIDDEN=true",
    "S3_UPLOAD_BEFORE_FINALIZE_FORBIDDEN=true",
    "ACTIVE_STAGING_SYNC_FORBIDDEN=true",
    "DOWNLOAD_VERIFY_REQUIRED_BEFORE_CLOSEOUT_ACCEPTANCE=true",
    "S3_AUTHORITY=false",
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

DRY_ADAPTER_INPUTS = (
    "--durable-evidence-root",
    "--registry-json",
    "--run-id",
    "--manifest-sha256",
    "--export-prefix-plan",
    "--dry-run",
    "--no-network",
)


def _section_6a3_1() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split(
        "### 6a.3.1 S3 finalized evidence export implementation preflight contract v0", 1
    )[1].split("### v0 authority posture", 1)[0]


def test_taxonomy_section_6a3_1_present() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "### 6a.3.1 S3 finalized evidence export implementation preflight contract v0" in text
    for marker in PREFLIGHT_SPEC_MARKERS:
        assert marker in text


def test_local_only_dry_adapter_contract_documented() -> None:
    section = _section_6a3_1()
    assert "LOCAL_ONLY_DRY_ADAPTER_CONTRACT_DOCUMENTED=true" in section
    assert "preflight_s3_finalized_evidence_export_v0" in section
    for flag in DRY_ADAPTER_INPUTS:
        assert flag in section
    assert "S3_EXPORT_DRY_RUN_DEFAULT=true" in section
    assert "S3_EXPORT_NO_NETWORK_DEFAULT=true" in section
    assert "non-executing" in section.lower() or "non executing" in section.lower()
    assert "no upload" in section.lower() or "does not** upload" in section.lower()


def test_preflight_checklist_requires_finalize_and_manifest_verify() -> None:
    section = _section_6a3_1()
    assert "finalize_primary_evidence_root" in section
    assert "MANIFEST.sha256" in section
    assert "RC=0" in section
    assert "manifest_verified=true" in section
    assert "outside" in section.lower() and "/tmp" in section
    primary_text = PRIMARY_EVIDENCE_SCRIPT.read_text(encoding="utf-8")
    assert "def finalize_primary_evidence_root" in primary_text
    assert "verify_manifest_sha256" in primary_text or "MANIFEST.sha256" in primary_text


def test_phase_t_w_extend_only_reconciled_to_manifest_sha256() -> None:
    section = _section_6a3_1()
    assert "PHASE_T_W_EXTEND_ONLY=true" in section
    assert "PHASE_T_W_RECONCILED_TO_MANIFEST_SHA256=true" in section
    assert "PHASE_T_DATA_NODE_EXPORT_CHANNEL.md" in section
    assert "PHASE_W_EXPORT_PACK_GH_CONSUMER.md" in section
    assert PHASE_T_RUNBOOK.is_file()
    assert PHASE_W_RUNBOOK.is_file()
    assert "extend-only" in section.lower() or "Extend-only" in section
    phase_t_text = PHASE_T_RUNBOOK.read_text(encoding="utf-8")
    phase_w_text = PHASE_W_RUNBOOK.read_text(encoding="utf-8")
    assert "SHA256SUMS.stable.txt" in phase_t_text
    assert "SHA256SUMS.stable.txt" in phase_w_text
    assert "MANIFEST.sha256 remains canonical" in section


def test_sha256sums_stable_not_competing_truth_or_authority() -> None:
    section = _section_6a3_1()
    assert "SHA256SUMS_STABLE_PARALLEL_TRUTH_FORBIDDEN=true" in section
    assert "SHA256SUMS.stable.txt" in section
    assert "competing truth" in section.lower() or "parallel truth" in section.lower()
    assert (
        "non-authoritative compatibility" in section.lower()
        or "non-authoritative" in section.lower()
    )


def test_evidence_transport_transition_local_only_to_s3_export_gated() -> None:
    section = _section_6a3_1()
    assert "local_only" in section
    assert "s3_export_after_finalize" in section
    assert "evidence_transport=local_only" in section
    assert "before" in section.lower()
    assert "upload success" in section.lower()
    assert "does not" in section.lower() or "do not" in section.lower()


def test_download_verify_required_before_closeout_acceptance_fail_closed() -> None:
    section = _section_6a3_1()
    assert "DOWNLOAD_VERIFY_REQUIRED_BEFORE_CLOSEOUT_ACCEPTANCE=true" in section
    assert "download" in section.lower()
    assert "closeout acceptance" in section.lower()
    assert "fail-closed" in section.lower() or "fail closed" in section.lower()


def test_canonical_boundary_copy_present() -> None:
    section = _section_6a3_1()
    assert "S3 export implementation preflight is non-executing" in section
    assert "MANIFEST.sha256 remains canonical" in section


def test_forbidden_authority_markers_and_no_new_lanes() -> None:
    section = _section_6a3_1().lower()
    for marker in (
        "s3_authority=false",
        "notion_authority=false",
        "market_dashboard_authority=false",
        "double_play_authority=false",
        "runtime_authority=false",
        "scheduler_clearance_authority=false",
    ):
        assert marker in section
    assert "lane_id=daemon_paper_24h" in section
    assert "lane_id=remote_runtime" in section
    assert "generic_evidence_run_registry.v2" not in section
    assert "aws cli" in section.lower() or "aws/rclone" in section.lower()


def test_active_staging_sync_forbidden_and_no_secrets_in_projections() -> None:
    section = _section_6a3_1().lower()
    assert "active staging sync" in section
    assert "active_staging_sync_forbidden=true" in section
    assert "secrets" in section


def test_s3_relevant_projection_fields_referenced() -> None:
    section = _section_6a3_1()
    for field in pc.S3_RELEVANT_PROJECTION_FIELDS:
        assert field in section or field in TAXONOMY_SPEC.read_text(encoding="utf-8")


def test_registry_module_exposes_preflight_constants() -> None:
    mod = pc.load_registry_module(module_name="build_generic_evidence_run_registry_v1_s3_preflight")
    assert mod.S3_FINALIZED_EVIDENCE_EXPORT_IMPLEMENTATION_PREFLIGHT_V0 is True
    assert mod.S3_EXPORT_PREFLIGHT_DOCS_TESTS_ONLY is True
    assert mod.S3_EXPORT_DRY_RUN_DEFAULT is True
    assert mod.S3_EXPORT_NO_NETWORK_DEFAULT is True
    assert mod.EVIDENCE_TRANSPORT_DEFAULT == "local_only"


def test_registry_fixture_still_local_only_non_authorizing(tmp_path: Path) -> None:
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


def test_owner_crosslinks() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    assert S3_GATE_TESTS.name in owner_text
    assert REMOTE_RUNTIME_TESTS.name in owner_text
    assert PROJECTION_FIXTURE_TESTS.name in owner_text


def test_docs_truth_map_references_s3_export_implementation_preflight() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "6a.3.1" in text or "S3 finalized evidence export implementation preflight" in text
    assert TAXONOMY_SPEC.name in text
