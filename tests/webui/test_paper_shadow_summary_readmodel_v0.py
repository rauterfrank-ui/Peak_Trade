"""Tests für den fixture-only Paper/Shadow Summary Read-model Builder v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.webui.paper_shadow_summary_readmodel_v0 import (
    SCHEMA_VERSION,
    PaperShadowSummaryMetadataInput,
    PaperShadowPathPolicyV0,
    build_paper_shadow_summary_readmodel_v0,
    to_json_dict,
)

FIXTURES = project_root / "tests" / "fixtures" / "paper_shadow_summary_readmodel_v0"


def _fixture(name: str) -> Path:
    return FIXTURES / name


@pytest.fixture(autouse=True)
def _fixed_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "PEAK_TRADE_FIXED_GENERATED_AT_UTC",
        "2026-05-02T00:30:00+00:00",
    )


def test_complete_minimal_all_slots_and_counts() -> None:
    root = _fixture("complete_minimal")
    m = build_paper_shadow_summary_readmodel_v0(
        root,
        generated_at_utc="2026-05-02T00:30:00+00:00",
        metadata=PaperShadowSummaryMetadataInput(
            source_label="fixture_prj_smoke_complete_minimal",
        ),
    )

    assert m.schema_version == SCHEMA_VERSION
    assert m.generated_at_utc == "2026-05-02T00:30:00+00:00"
    assert m.source_kind == "fixture"
    assert m.stale is True
    assert m.stale_reason == "offline_bundle_scan"
    assert m.errors == ()
    assert m.warnings == ()
    assert m.operator_context_present is False

    assert m.manifest_present is True
    assert m.index_present is True
    assert m.summary_present is True
    assert m.paper_account_present is True
    assert m.paper_fills_present is True
    assert m.paper_evidence_manifest_present is True
    assert m.shadow_session_summary_present is True
    assert m.shadow_evidence_manifest_present is True
    assert m.p4c_present is True
    assert m.p5a_present is True

    assert m.artifact_count == 10
    assert m.paper_fill_count == 2
    assert m.artifact_bundle_id == "20260501T144102Z"

    d = to_json_dict(m)
    assert d["schema_version"] == SCHEMA_VERSION
    assert d["warnings"] == []
    assert d["paper_fill_count"] == 2


def test_missing_paper_fills_warning_and_absent_fill_slot() -> None:
    root = _fixture("missing_paper_fills")
    m = build_paper_shadow_summary_readmodel_v0(root)

    assert m.paper_fills_present is False
    assert m.paper_fill_count is None
    assert "paper_fills_json_missing" in m.warnings
    assert m.errors == ()
    assert m.paper_account_present is True
    assert m.index_present is True


def test_malformed_fills_error_and_absent_fill_slot() -> None:
    root = _fixture("malformed_fills")
    m = build_paper_shadow_summary_readmodel_v0(root)

    assert m.paper_fills_present is False
    assert m.paper_fill_count is None
    assert "fills_json_unreadable" in m.errors


def test_bundle_root_must_exist() -> None:
    with pytest.raises(ValueError, match="bundle_root"):
        build_paper_shadow_summary_readmodel_v0(Path("/nonexistent/paper_shadow_bundle_xyz"))


def test_policy_stamp_overrides_prj_smoke_discovery(tmp_path: Path) -> None:
    """Ein expliziter Stamp in der Policy reicht; Children unter prj_smoke werden ignoriert."""
    stamp = "20260501T144102Z"
    run = tmp_path / "prj_smoke" / stamp
    (run / "paper").mkdir(parents=True)
    (run / "shadow" / "p4c").mkdir(parents=True)
    (run / "shadow" / "p5a").mkdir(parents=True)
    pack = tmp_path / "evidence_packs" / f"pack_prj_smoke_{stamp}"
    pack.mkdir(parents=True)

    (pack / "manifest.json").write_text("{}", encoding="utf-8")
    (pack / "index.json").write_text("[]", encoding="utf-8")
    (run / "summary.json").write_text("{}", encoding="utf-8")
    (run / "paper" / "account.json").write_text("{}", encoding="utf-8")
    (run / "paper" / "fills.json").write_text("[]", encoding="utf-8")
    (run / "paper" / "evidence_manifest.json").write_text("{}", encoding="utf-8")
    (run / "shadow" / "shadow_session_summary.json").write_text("{}", encoding="utf-8")
    (run / "shadow" / "evidence_manifest.json").write_text("{}", encoding="utf-8")
    (run / "shadow" / "p4c" / "x.json").write_text("{}", encoding="utf-8")
    (run / "shadow" / "p5a" / "y.json").write_text("{}", encoding="utf-8")

    (tmp_path / "prj_smoke" / "other_stamp").mkdir()
    (tmp_path / "prj_smoke" / "another").mkdir()

    m = build_paper_shadow_summary_readmodel_v0(
        tmp_path,
        policy=PaperShadowPathPolicyV0(stamp=stamp),
    )
    assert m.errors == ()
    assert m.summary_present is True
    assert m.artifact_bundle_id == stamp


def test_metadata_workflow_fields_pass_through() -> None:
    root = _fixture("complete_minimal")
    m = build_paper_shadow_summary_readmodel_v0(
        root,
        metadata=PaperShadowSummaryMetadataInput(
            workflow_name="example_wf",
            workflow_run_id="run-123",
            source_commit="abc",
            artifact_bundle_id="override-id",
            artifact_bundle_label="override label",
        ),
    )
    assert m.workflow_name == "example_wf"
    assert m.workflow_run_id == "run-123"
    assert m.source_commit == "abc"
    assert m.artifact_bundle_id == "override-id"
    assert m.artifact_bundle_label == "override label"


def test_prj_smoke_ambiguous_stamp_errors(tmp_path: Path) -> None:
    (tmp_path / "prj_smoke" / "a").mkdir(parents=True)
    (tmp_path / "prj_smoke" / "b").mkdir(parents=True)
    m = build_paper_shadow_summary_readmodel_v0(tmp_path)
    assert "prj_smoke_stamp_ambiguous" in m.errors
    assert "stamp_unresolved_bundle_partial" in m.warnings
    assert m.manifest_present is False


_EXPECTED_SUMMARY_JSON_TOP_KEYS = frozenset(
    {
        "schema_version",
        "generated_at_utc",
        "source_label",
        "source_kind",
        "source_owner",
        "stale",
        "stale_reason",
        "snapshot_time_utc",
        "warnings",
        "errors",
        "workflow_name",
        "workflow_run_id",
        "source_commit",
        "artifact_bundle_id",
        "artifact_bundle_label",
        "manifest_present",
        "index_present",
        "summary_present",
        "operator_context_present",
        "paper_account_present",
        "paper_fills_present",
        "paper_evidence_manifest_present",
        "shadow_session_summary_present",
        "shadow_evidence_manifest_present",
        "p4c_present",
        "p5a_present",
        "artifact_count",
        "paper_fill_count",
    }
)

_FORBIDDEN_AUTHORITY_KEYS = frozenset(
    {
        "live_authorization",
        "live_ready",
        "testnet_ready",
        "trading_ready",
        "execute",
        "execution",
        "order",
        "orders",
        "approve",
        "approved",
        "promote",
        "readiness",
        "sign_off",
        "enable_live",
        "confirm_token",
    }
)


def _collect_keys(obj: object, out: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                out.add(k)
            _collect_keys(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_keys(item, out)


def test_complete_minimal_json_exact_keys_roundtrip_and_no_authority_keys() -> None:
    root = _fixture("complete_minimal")
    m = build_paper_shadow_summary_readmodel_v0(
        root,
        generated_at_utc="2026-05-02T00:30:00+00:00",
        metadata=PaperShadowSummaryMetadataInput(
            source_label="fixture_prj_smoke_complete_minimal",
        ),
    )
    d = to_json_dict(m)
    assert set(d.keys()) == _EXPECTED_SUMMARY_JSON_TOP_KEYS
    keys_flat: set[str] = set()
    _collect_keys(d, keys_flat)
    assert keys_flat.isdisjoint(_FORBIDDEN_AUTHORITY_KEYS)
    assert json.loads(json.dumps(d)) == d
