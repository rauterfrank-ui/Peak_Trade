"""System Atlas impact-checker contracts. ATLAS_AUTHORITY=NONE. Offline. No network."""

from __future__ import annotations

from pathlib import Path

from scripts.ops.system_atlas_v1.impact_v1 import (
    ATLAS_IMPACT_NONE_WITH_PROOF,
    ATLAS_IMPACT_REVIEW_REQUIRED,
    ATLAS_IMPACT_UPDATED,
    classify_atlas_impact_v1,
)
from scripts.ops.system_atlas_v1.load_v1 import load_atlas_v1

REPO_ROOT = Path(__file__).resolve().parents[2]
ELIGIBILITY = "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py"


def test_empty_diff_is_none_with_proof() -> None:
    atlas = load_atlas_v1(repo_root=REPO_ROOT)
    report = classify_atlas_impact_v1(atlas=atlas, changed_files=[])
    assert report.impact == ATLAS_IMPACT_NONE_WITH_PROOF
    assert report.drift_detected is False
    assert report.review_required_items == []


def test_unrelated_docs_are_none_with_proof() -> None:
    atlas = load_atlas_v1(repo_root=REPO_ROOT)
    report = classify_atlas_impact_v1(
        atlas=atlas,
        changed_files=["README.md", "docs/ops/registry/TRUTH_CORE.md"],
    )
    assert report.impact == ATLAS_IMPACT_NONE_WITH_PROOF
    assert report.drift_detected is False


def test_tracked_runtime_without_atlas_yaml_is_review_required() -> None:
    atlas = load_atlas_v1(repo_root=REPO_ROOT)
    report = classify_atlas_impact_v1(atlas=atlas, changed_files=[ELIGIBILITY])
    assert report.impact == ATLAS_IMPACT_REVIEW_REQUIRED
    assert report.drift_detected is True
    assert any(
        item.startswith("TRACKED_ENTITY_UNREVIEWED:") for item in report.review_required_items
    )
    assert "RUNTIME_COMPONENT:gfu_eligibility" in report.changed_entities or any(
        "gfu_eligibility" in item for item in report.review_required_items
    )


def test_tracked_runtime_with_entity_id_in_yaml_diff_is_updated() -> None:
    atlas = load_atlas_v1(repo_root=REPO_ROOT)
    yaml_diff = (
        "diff --git a/docs/system_atlas/entities/catalog.yaml "
        "b/docs/system_atlas/entities/catalog.yaml\n"
        "@@\n"
        "   - id: RUNTIME_COMPONENT:gfu_eligibility\n"
        "+    modified_by: PENDING_CHANGE\n"
    )
    report = classify_atlas_impact_v1(
        atlas=atlas,
        changed_files=[
            ELIGIBILITY,
            "docs/system_atlas/entities/catalog.yaml",
        ],
        atlas_yaml_diff=yaml_diff,
    )
    assert report.impact == ATLAS_IMPACT_UPDATED
    assert report.drift_detected is False
    assert report.review_required_items == []


def test_material_untracked_src_ops_is_review_required() -> None:
    atlas = load_atlas_v1(repo_root=REPO_ROOT)
    report = classify_atlas_impact_v1(
        atlas=atlas,
        changed_files=["src/ops/definitely_not_in_atlas_census_v1.py"],
    )
    assert report.impact == ATLAS_IMPACT_REVIEW_REQUIRED
    assert any(item.startswith("MATERIAL_UNTRACKED:") for item in report.review_required_items)


def test_stale_generated_views_fail_closed() -> None:
    atlas = load_atlas_v1(repo_root=REPO_ROOT)
    report = classify_atlas_impact_v1(
        atlas=atlas,
        changed_files=["docs/system_atlas/entities/catalog.yaml"],
        atlas_yaml_diff="   - id: SYSTEM:peak_trade\n",
        generated_current=False,
    )
    assert report.impact == ATLAS_IMPACT_REVIEW_REQUIRED
    assert "GENERATED_VIEWS_STALE" in report.review_required_items
    assert report.drift_detected is True


def test_atlas_yaml_only_is_updated() -> None:
    atlas = load_atlas_v1(repo_root=REPO_ROOT)
    report = classify_atlas_impact_v1(
        atlas=atlas,
        changed_files=["docs/system_atlas/entities/catalog.yaml"],
        atlas_yaml_diff="   - id: SCRIPT:check_system_atlas_impact\n",
    )
    assert report.impact == ATLAS_IMPACT_UPDATED
    assert report.drift_detected is False


def test_truth_gates_run_atlas_impact_checker() -> None:
    text = (REPO_ROOT / ".github" / "workflows" / "truth_gates_pr.yml").read_text(encoding="utf-8")
    assert "check_system_atlas_impact_v1.py" in text
    assert "validate_system_atlas_v1.py" in text
    assert "name: docs-drift-guard" in text
