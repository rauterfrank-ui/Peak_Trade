"""Static contract for composition rebaseline evidence + next-slice authorization."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.web

EVIDENCE_GLOB = "composition_rebaseline_next_slice_v1_*"
REQUIRED_FILES = (
    "README.md",
    "browser_report.json",
    "composition_geometry.json",
    "landmark_order.json",
    "console_and_network_report.json",
    "ssot_consumer_audit.json",
    "repository_snapshot.json",
    "runbook_snapshot_drift_report.json",
    "composition_findings.md",
    "next_slice_plan.md",
    "MANIFEST.sha256",
    "screenshots/full_page_1440x900.png",
    "screenshots/full_page_1280x800.png",
    "screenshots/full_page_1728x1117.png",
)
EXPECTED_LANDMARKS = [
    "GLOBAL_HEADER",
    "PRIMARY_MARKET_SURFACE",
    "DECISION_SURFACE",
    "OBSERVABILITY_SURFACE",
    "ENGINEERING_DRAWER",
]
NEXT_SLICE = "COMPOSITION_DECISION_SURFACE_VERTICAL_COMPRESSION_V1"
# Live implementation-plan posture after post-dominance rebaseline + rhythm slice.
CURRENT_IMPLEMENTED_SLICE = "COMPOSITION_LANDMARK_VERTICAL_RHYTHM_V1"
CURRENT_NEXT_SLICE = "COMPOSITION_DECISION_SURFACE_HIERARCHY_V1"
PLAN = project_root / "docs" / "product" / "VISUAL_OPERATOR_DASHBOARD_IMPLEMENTATION_PLAN_V1.md"


def _latest_evidence_dir() -> Path:
    root = project_root / "docs" / "product" / "evidence"
    matches = sorted(root.glob(EVIDENCE_GLOB))
    assert matches, f"missing evidence dirs matching {EVIDENCE_GLOB}"
    return matches[-1]


def test_composition_rebaseline_evidence_pack_complete() -> None:
    evidence = _latest_evidence_dir()
    for rel in REQUIRED_FILES:
        path = evidence / rel
        assert path.is_file(), f"missing required artifact: {rel}"
        assert path.stat().st_size > 0, f"empty artifact: {rel}"


def test_manifest_sha256_matches_pack_files() -> None:
    evidence = _latest_evidence_dir()
    manifest = evidence / "MANIFEST.sha256"
    entries: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(None, 1)
        entries[rel.strip()] = digest.strip()
    assert entries, "MANIFEST.sha256 empty"
    for rel, expected in entries.items():
        path = evidence / rel
        assert path.is_file(), f"manifest lists missing file: {rel}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, f"digest mismatch for {rel}"
    # Required screenshots must be listed
    for shot in (
        "screenshots/full_page_1440x900.png",
        "screenshots/full_page_1280x800.png",
        "screenshots/full_page_1728x1117.png",
    ):
        assert shot in entries


def test_browser_report_real_chrome_accepted() -> None:
    evidence = _latest_evidence_dir()
    report = json.loads((evidence / "browser_report.json").read_text(encoding="utf-8"))
    assert report.get("REAL_CHROME_VERIFIED") is True
    assert report.get("CHROMIUM_FALLBACK_USED") is False
    assert report.get("BROWSER_ACTUAL") == "GOOGLE_CHROME"
    assert report.get("EVIDENCE_ACCEPTED") is True
    assert report.get("CONSOLE_ERRORS", 1) == 0
    assert report.get("PAGE_ERRORS", 1) == 0
    assert report.get("FAILED_ASSETS", 1) == 0
    assert report.get("EXTERNAL_NETWORK_REQUESTS", 1) == 0


def test_landmark_order_and_composition_gates() -> None:
    evidence = _latest_evidence_dir()
    order = json.loads((evidence / "landmark_order.json").read_text(encoding="utf-8"))
    geometry = json.loads((evidence / "composition_geometry.json").read_text(encoding="utf-8"))
    assert order.get("expected") == EXPECTED_LANDMARKS
    assert order.get("pass") is True
    for key in ("1440x900", "1280x800", "1728x1117"):
        vp = order["viewports"][key]
        assert vp["observed"] == EXPECTED_LANDMARKS
        assert vp["pass"] is True
    agg = geometry["aggregate"]
    assert agg["LANDMARK_ORDER_PASS"] is True
    assert agg["HORIZONTAL_OVERFLOW_PASS"] is True
    assert agg["PRIMARY_CHART_DOMINANCE_PASS"] is True
    assert agg["ENGINEERING_SECONDARY_PASS"] is True


def test_ssot_consumer_audit_boundaries() -> None:
    evidence = _latest_evidence_dir()
    audit = json.loads((evidence / "ssot_consumer_audit.json").read_text(encoding="utf-8"))
    assert audit["canonical_ssot"] == "MASTER_V2_AND_DOUBLE_PLAY"
    assert audit["dashboard_is_consumer_only"] is True
    assert audit["dashboard_readonly"] is True
    assert audit["dashboard_creates_second_truth"] is False
    assert audit["second_truth_created_this_run"] is False
    assert audit["productive_ui_files_changed_this_run"] is False


def test_next_slice_plan_authorizes_single_decision_compression_slice() -> None:
    evidence = _latest_evidence_dir()
    plan_text = (evidence / "next_slice_plan.md").read_text(encoding="utf-8")
    assert NEXT_SLICE in plan_text
    assert "Problem Statement" in plan_text
    assert "Explicitly excluded work" in plan_text
    assert "Acceptance criteria" in plan_text
    assert "Chrome Full-Page Evidence Plan" in plan_text
    assert "Rollback Plan" in plan_text
    # Single-slice authorization: do not bundle unrelated phase titles as co-equal next work.
    assert plan_text.count("## Chosen single slice") == 1


def test_implementation_plan_points_to_authorized_next_slice() -> None:
    text = PLAN.read_text(encoding="utf-8")
    # Historical rebaseline pack that authorized Decision compression remains referenced.
    assert "composition_rebaseline_next_slice_v1_20260717T001413Z" in text
    assert NEXT_SLICE in text
    # Active plan posture advances with the latest bounded composition slice.
    assert f"IMPLEMENTED_SLICE={CURRENT_IMPLEMENTED_SLICE}" in text
    assert f"NEXT_SLICE={CURRENT_NEXT_SLICE}" in text
    # Stale bootstrap pointer must not remain the active next slice.
    assert not re.search(r"(?m)^NEXT_SLICE=PHASE_1A_LAYOUT_AND_HEADER$", text)
    assert not re.search(
        rf"(?m)^NEXT_SLICE={re.escape(NEXT_SLICE)}$",
        text,
    )


def test_runbook_snapshot_drift_documented_not_silently_repaired() -> None:
    evidence = _latest_evidence_dir()
    drift = json.loads(
        (evidence / "runbook_snapshot_drift_report.json").read_text(encoding="utf-8")
    )
    assert drift["PART_I_NORMATIVE"] is True
    assert drift["PART_II_DISCOVERY_SNAPSHOT_ONLY"] is True
    assert drift["PART_II_TREATED_AS_LIVE_TRUTH"] is False
    assert drift["RUNBOOK_SNAPSHOT_DRIFT_FOUND"] is True
    assert drift["repair_performed_on_master_runbook"] is False
