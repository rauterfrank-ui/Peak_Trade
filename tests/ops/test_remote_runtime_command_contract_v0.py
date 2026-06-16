"""Static contract tests for Remote Runtime Command Contract v0 (taxonomy §6a.0)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
PREFLIGHT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"

COMMAND_CONTRACT_MARKERS = (
    "REMOTE_RUNTIME_COMMAND_CONTRACT_V0=true",
    "REMOTE_RUNTIME_COMMAND_CONTRACT_DOCS_TESTS_ONLY=true",
    "REMOTE_RUNTIME_IS_BACKEND_NOT_LANE=true",
    "LANE_ID_REMOTE_RUNTIME_FORBIDDEN=true",
    "REMOTE_RUNTIME_V0_PAPER_ONLY=true",
    "REMOTE_RUNTIME_V0_TESTNET_AUTHORITY=false",
    "REMOTE_RUNTIME_V0_LIVE_AUTHORITY=false",
    "REMOTE_RUNTIME_V0_BROKER_CREDENTIALS_FORBIDDEN=true",
    "REMOTE_RUNTIME_V0_REQUIRES_MAX_RUNTIME_SECONDS=true",
    "REMOTE_RUNTIME_V0_REQUIRES_REMOTE_RUN_ID=true",
    "REMOTE_RUNTIME_V0_REQUIRES_REMOTE_DURABLE_EVIDENCE_ROOT=true",
    "REMOTE_RUNTIME_V0_REQUIRES_MANIFEST_SHA256=true",
    "REMOTE_RUNTIME_V0_REQUIRES_MANIFEST_VERIFY_RC_ZERO=true",
    "REMOTE_RUNTIME_V0_REQUIRES_MANDATORY_DURABLE_CLOSEOUT=true",
    "REMOTE_RUNTIME_V0_REUSES_SCHEDULER_BOUNDARY_GUARD=true",
    "REMOTE_RUNTIME_V0_REUSES_HOLD_BINDING=true",
    "REMOTE_RUNTIME_V0_REUSES_REGISTRY_V1=true",
    "REMOTE_RUNTIME_V0_S3_AFTER_FINALIZE_ONLY=true",
    "REMOTE_RUNTIME_V0_NOTION_PROJECTION_ONLY=true",
    "REMOTE_RUNTIME_V0_MARKET_DASHBOARD_PROJECTION_ONLY=true",
    "REMOTE_RUNTIME_V0_NO_REMOTE_RUNNER_IMPLEMENTATION=true",
    "REMOTE_RUNTIME_V0_NO_AWS_RCLONE_NETWORK_EXECUTION=true",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS = (
    "REMOTE_RUNTIME_COMMAND_CONTRACT_V0.md",
    "REMOTE_RUNTIME_RUNNER_V0.md",
    "REMOTE_RUNTIME_RUNBOOK_V0.md",
)


def _section_6a0() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split("### 6a.0 Remote Runtime Command Contract v0", 1)[1].split(
        "### S3 / Object Storage", 1
    )[0]


def test_section_6a0_present_with_markers() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "### 6a.0 Remote Runtime Command Contract v0" in text
    for marker in COMMAND_CONTRACT_MARKERS:
        assert marker in text


def test_top_level_taxonomy_markers_include_command_contract() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "REMOTE_RUNTIME_COMMAND_CONTRACT_V0=true" in text.split("## 2.", 1)[0]


def test_paper_only_lane_in_v0() -> None:
    section = _section_6a0()
    assert "REMOTE_RUNTIME_V0_PAPER_ONLY=true" in section
    assert "`lane_id=paper`" in section or "lane_id=paper" in section
    assert "paper` only" in section or "paper only" in section.lower()


def test_forbidden_lane_ids_documented() -> None:
    section = _section_6a0()
    assert "lane_id=remote_runtime" in section
    assert "LANE_ID_REMOTE_RUNTIME_FORBIDDEN=true" in section
    assert "lane_id=daemon_paper_24h" in section
    assert "not a runtime lane" in section.lower() or "not a lane" in section.lower()
    assert "shadow" in section.lower()
    assert "testnet" in section.lower()


def test_required_metadata_fields_documented() -> None:
    section = _section_6a0()
    for field in (
        "runtime_host",
        "runtime_backend",
        "runtime_mode",
        "remote_run_id",
        "max_runtime_seconds",
        "evidence_root_type",
        "evidence_transport",
        "live_authority",
        "testnet_authority",
    ):
        assert field in section
    assert "`remote`" in section
    for backend in ("ec2", "vps", "gha_runner", "data_node"):
        assert backend in section
    assert "remote_durable" in section
    assert "paper_only" in section


def test_gate_chain_reuses_canonical_owners() -> None:
    section = _section_6a0()
    assert "scheduler_start_boundary_guard_v0.py" in section
    assert "paper_shadow_247_scheduler_hold_runtime_binding_v0.py" in section
    assert "primary_evidence_retention_v0.py" in section
    assert "build_generic_evidence_run_registry_v1.py" in section
    assert "preflight_s3_finalized_evidence_export_v0.py" in section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    assert "§2b.1" in section or "2b.1" in section


def test_evidence_and_closeout_semantics() -> None:
    section = _section_6a0()
    assert "outside `/tmp`" in section or "outside /tmp" in section.lower()
    assert "MANIFEST.sha256" in section
    assert "RC=0" in section
    assert "TMP_ONLY_EVIDENCE_INVALID" in section
    assert "closeout" in section.lower()


def test_forbidden_parallel_builds_documented() -> None:
    section = _section_6a0()
    assert (
        "Second scheduler authority" in section or "second scheduler authority" in section.lower()
    )
    assert "Notion as source of truth" in section or "notion as source of truth" in section.lower()
    assert "bypass" in section.lower()


def test_notion_and_dashboard_projection_only() -> None:
    section = _section_6a0()
    assert "§6a.1" in section
    assert "§6a.2" in section
    assert "NOTION_WRITE_DEFAULT=false" in section
    assert "GET &#47;market&#47;double-play" in section


def test_s3_after_finalize_only() -> None:
    section = _section_6a0()
    assert "S3_UPLOAD_BEFORE_FINALIZE_FORBIDDEN=true" in section
    assert "DOWNLOAD_VERIFY_REQUIRED_BEFORE_CLOSEOUT_ACCEPTANCE=true" in section
    assert "non-executing" in section.lower()
    assert (
        "upload does **not** authorize" in section
        or "does not authorize runtime" in section.lower()
    )


def test_no_runner_or_network_implementation() -> None:
    section = _section_6a0()
    assert "REMOTE_RUNTIME_V0_NO_REMOTE_RUNNER_IMPLEMENTATION=true" in section
    assert "REMOTE_RUNTIME_V0_NO_AWS_RCLONE_NETWORK_EXECUTION=true" in section
    assert "does **not** ship an execution script" in section or "does not" in section.lower()
    for forbidden in ("systemd", "SSH", "AWS"):
        assert forbidden in section


def test_normative_static_only() -> None:
    section = _section_6a0()
    assert "REMOTE_RUNTIME_COMMAND_CONTRACT_DOCS_TESTS_ONLY=true" in section
    assert "static" in section.lower() or "normative only" in section.lower()


def test_section_ordering_6a0_before_s3_subsection() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert text.index("### 6a.0 Remote Runtime Command Contract v0") < text.index(
        "### S3 / Object Storage"
    )
    assert text.index("### 6a.0 Remote Runtime Command Contract v0") < text.index(
        "### 6a.1 Notion post-closeout sync projection contract v0"
    )


def test_preflight_crosslinks_section_6a0() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "§6a.0 Remote Runtime Command Contract v0" in text
    assert "backend-not-lane" in text


def test_docs_truth_map_lists_section_6a0() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "§6a.0" in text
    assert "Remote Runtime Command Contract v0" in text


def test_no_duplicate_remote_command_spec_introduced() -> None:
    specs_dir = REPO_ROOT / "docs" / "ops" / "specs"
    runbooks_dir = REPO_ROOT / "docs" / "ops" / "runbooks"
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        assert list(specs_dir.glob(f"*{fragment}*")) == []
        assert list(runbooks_dir.glob(f"*{fragment}*")) == []
