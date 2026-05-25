"""Static contract tests for Remote Runtime Host Metadata v0 (taxonomy §6a)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
REGISTRY_SCRIPT = REPO_ROOT / "scripts" / "ops" / "build_generic_evidence_run_registry_v1.py"
PRIMARY_EVIDENCE_HELPER = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"

REMOTE_RUNTIME_MARKERS = (
    "REMOTE_RUNTIME_HOST_METADATA_CONTRACT_V0=true",
    "REMOTE_RUNTIME_IS_BACKEND_NOT_LANE=true",
    "REMOTE_RUNTIME_HOST_METADATA_DOCS_TESTS_ONLY=true",
    "S3_FINALIZED_EVIDENCE_TRANSPORT_ONLY=true",
    "NOTION_PROJECTION_NON_AUTHORIZING=true",
    "MARKET_DASHBOARD_PROJECTION_READONLY=true",
    "REMOTE_RUNTIME_V0_LIVE_AUTHORITY=false",
    "REMOTE_RUNTIME_V0_TESTNET_AUTHORITY=false",
    "REGISTRY_V1_REMOTE_RUNTIME_HOST_METADATA_FIELDS_DEFINED=true",
)

METADATA_FIELDS = (
    "runtime_host",
    "runtime_backend",
    "runtime_mode",
    "evidence_root_type",
    "evidence_transport",
    "notion_projection",
    "market_dashboard_projection",
    "live_authority",
    "testnet_authority",
)

FIELD_VALUE_SNIPPETS = {
    "runtime_host": ("local", "remote"),
    "runtime_backend": ("laptop", "ec2", "vps", "data_node", "gha_runner"),
    "runtime_mode": ("paper_only", "paper_then_shadow"),
    "evidence_root_type": ("local_durable", "remote_durable"),
    "evidence_transport": ("local_only", "s3_export_after_finalize"),
    "notion_projection": ("disabled", "post_closeout_sync", "verified_evidence_index"),
    "market_dashboard_projection": (
        "disabled",
        "read_only_run_status",
        "read_only_evidence_status",
    ),
}

FORBIDDEN_NEW_LANE_LITERALS = (
    "lane_id=remote_runtime",
    "lane_id `remote_runtime`",
    "`remote_runtime`",
)

FORBIDDEN_AUTHORITY_PHRASES = (
    "grants approval",
    "grants gate clearance",
    "authorizes live trading",
    "authorizes testnet execution",
    "clears HOLD",
    "clears global HOLD",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS = (
    "REMOTE_RUNTIME_HOST_CONTRACT_V0.md",
    "REMOTE_RUNTIME_CONSOLIDATION_V0.md",
    "REMOTE_RUNTIME_RUNBOOK_V0.md",
)


def _taxonomy_text() -> str:
    return TAXONOMY_SPEC.read_text(encoding="utf-8")


def _load_registry_module():
    spec = importlib.util.spec_from_file_location(
        "build_generic_evidence_run_registry_v1", REGISTRY_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_generic_evidence_run_registry_v1"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_taxonomy_section_6a_present() -> None:
    text = _taxonomy_text()
    assert "## 6a. Remote Runtime Host Metadata Contract v0" in text
    for marker in REMOTE_RUNTIME_MARKERS:
        assert marker in text


def test_metadata_fields_documented_in_taxonomy() -> None:
    text = _taxonomy_text()
    for field in METADATA_FIELDS:
        assert f"`{field}`" in text, f"missing field {field!r} in taxonomy §6a"
    for field, values in FIELD_VALUE_SNIPPETS.items():
        for value in values:
            assert value in text, f"missing allowed value {value!r} for {field}"


def test_remote_described_as_backend_not_new_lane() -> None:
    text = _taxonomy_text()
    assert "backend metadata" in text.lower()
    assert "not** a new `lane_id`" in text or "not a new `lane_id`" in text
    assert "Forbidden:** introducing `lane_id=remote_runtime`" in text
    for literal in FORBIDDEN_NEW_LANE_LITERALS:
        assert literal in text or "lane_id=remote_runtime" in text


def test_s3_export_tied_to_finalized_manifest() -> None:
    text = _taxonomy_text()
    assert "s3_export_after_finalize" in text
    assert "finalize_primary_evidence_root" in text
    assert "MANIFEST.sha256" in text
    assert "active staging sync" in text.lower() or "not active staging sync" in text.lower()
    helper = PRIMARY_EVIDENCE_HELPER.read_text(encoding="utf-8")
    assert "MANIFEST_FILENAME = \"MANIFEST.sha256\"" in helper


def test_notion_projection_non_authorizing() -> None:
    text = _taxonomy_text()
    assert "NOTION_PROJECTION_NON_AUTHORIZING=true" in text
    assert "FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL" in text
    assert "navigation_only" in text or "planning_only" in text


def test_market_dashboard_projection_read_only() -> None:
    text = _taxonomy_text()
    assert "MARKET_DASHBOARD_PROJECTION_READONLY=true" in text
    assert "read_only_run_status" in text
    assert "read_only_evidence_status" in text
    assert "review input only" in text.lower()


def test_v0_live_and_testnet_authority_false() -> None:
    text = _taxonomy_text()
    assert "REMOTE_RUNTIME_V0_LIVE_AUTHORITY=false" in text
    assert "REMOTE_RUNTIME_V0_TESTNET_AUTHORITY=false" in text
    assert "live_authority=false" in text
    assert "testnet_authority=false" in text


def test_no_approval_authority_language_in_section_6a() -> None:
    text = _taxonomy_text()
    start = text.index("## 6a. Remote Runtime Host Metadata Contract v0")
    end = text.index("## 7. Scheduler lane", start)
    section = text[start:end].lower()
    for phrase in FORBIDDEN_AUTHORITY_PHRASES:
        assert phrase not in section, f"forbidden phrase {phrase!r} in §6a"


def test_no_new_remote_lane_id_in_taxonomy_lane_table() -> None:
    text = _taxonomy_text()
    assert "| `remote_runtime` |" not in text
    assert "lane_id `remote_runtime`" not in text


def test_registry_script_exposes_v0_defaults_constants() -> None:
    mod = _load_registry_module()
    assert mod.REMOTE_RUNTIME_HOST_METADATA_CONTRACT_V0 is True
    for field in METADATA_FIELDS:
        assert field in mod.REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS
    assert mod.REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS["live_authority"] is False
    assert mod.REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS["testnet_authority"] is False
    for field, allowed in mod.REMOTE_RUNTIME_HOST_METADATA_V0_FIELD_ALLOWED.items():
        default = mod.REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS[field]
        assert default in allowed


def test_registry_script_crosslinks_taxonomy_section_6a() -> None:
    text = REGISTRY_SCRIPT.read_text(encoding="utf-8")
    assert "taxonomy §6a" in text
    assert "REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS" in text


def test_no_duplicate_remote_runtime_spec_introduced() -> None:
    specs_dir = REPO_ROOT / "docs" / "ops" / "specs"
    runbooks_dir = REPO_ROOT / "docs" / "ops" / "runbooks"
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        assert list(specs_dir.glob(f"*{fragment}*")) == []
        assert list(runbooks_dir.glob(f"*{fragment}*")) == []


def test_closeout_anchor_referenced_as_example_only() -> None:
    text = _taxonomy_text()
    assert "daemon_paper_24h_20260524T205447Z" in text
    assert "non-authorizing example" in text.lower() or "example context" in text.lower()
