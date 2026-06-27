"""Integration tests for Package C manifest lineage FK propagation to proposal artifacts."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.governance.promotion_loop import (
    build_promotion_candidates_from_patches,
    build_promotion_proposals,
    materialize_promotion_proposals,
)
from src.governance.promotion_loop.models import (
    DecisionStatus,
    PromotionCandidate,
    PromotionDecision,
)
from src.governance.promotion_loop.proposal_input_refs_v1 import (
    apply_promotion_input_references_to_proposal,
    promotion_input_references_from_manifest,
)
from src.meta.learning_loop.config_patch_manifest_v1 import (
    build_empty_config_patch_manifest_v1,
    compute_manifest_integrity,
    load_promotion_input_from_manifest_path,
    serialize_config_patch_manifest_v1,
)
from src.meta.learning_loop.models import ConfigPatch, PatchStatus


FIXED_NOW = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
MANIFEST_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
LINEAGE_ID = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"


def _load_promotion_cycle_module():
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "run_promotion_proposal_cycle.py"
    module_name = "run_promotion_proposal_cycle_lineage_fk_test"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def promotion_cycle():
    return _load_promotion_cycle_module()


def _write_manifest(path: Path, *, patches: list[ConfigPatch]) -> None:
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=LINEAGE_ID,
    )
    manifest.patches = patches
    manifest.integrity = compute_manifest_integrity(manifest)
    path.write_text(serialize_config_patch_manifest_v1(manifest), encoding="utf-8")


def _accepted_decision(patch: ConfigPatch) -> PromotionDecision:
    candidate = PromotionCandidate(patch=patch, eligible_for_live=True, tags=["research"])
    return PromotionDecision(
        candidate=candidate,
        status=DecisionStatus.ACCEPTED_FOR_PROPOSAL,
        reasons=[],
    )


def test_manifest_fk_reaches_proposal_meta_json(tmp_path: Path) -> None:
    manifest_path = tmp_path / "input.json"
    patch = ConfigPatch(
        id="patch-a",
        target="research.offline.window_days",
        old_value=30,
        new_value=45,
        status=PatchStatus.APPLIED_OFFLINE,
        confidence_score=0.9,
    )
    _write_manifest(manifest_path, patches=[patch])

    promotion_input = load_promotion_input_from_manifest_path(manifest_path)
    refs = promotion_input_references_from_manifest(promotion_input.manifest)
    decisions = [_accepted_decision(patch)]
    proposals = build_promotion_proposals(decisions)
    assert len(proposals) == 1

    apply_promotion_input_references_to_proposal(proposals[0], refs)
    written = materialize_promotion_proposals(proposals, tmp_path / "out")
    meta_path = next(path for path in written if path.name == "proposal_meta.json")
    payload = json.loads(meta_path.read_text(encoding="utf-8"))

    assert payload["meta"]["config_patch_manifest_id"] == MANIFEST_ID
    assert payload["meta"]["candidate_lineage_manifest_ref"] == LINEAGE_ID
    assert "patches" not in payload["meta"]
    assert "integrity" not in payload["meta"]


def test_multiple_patches_share_single_manifest_reference(tmp_path: Path) -> None:
    manifest_path = tmp_path / "input.json"
    patches = [
        ConfigPatch(
            id="patch-1",
            target="research.offline.window_days",
            old_value=30,
            new_value=45,
            status=PatchStatus.APPLIED_OFFLINE,
        ),
        ConfigPatch(
            id="patch-2",
            target="research.offline.holdout_days",
            old_value=7,
            new_value=10,
            status=PatchStatus.APPLIED_OFFLINE,
        ),
    ]
    _write_manifest(manifest_path, patches=patches)

    promotion_input = load_promotion_input_from_manifest_path(manifest_path)
    refs = promotion_input_references_from_manifest(promotion_input.manifest)
    decisions = [_accepted_decision(patch) for patch in patches]
    proposals = build_promotion_proposals(decisions)
    apply_promotion_input_references_to_proposal(proposals[0], refs)

    written = materialize_promotion_proposals(proposals, tmp_path / "out")
    meta_path = next(path for path in written if path.name == "proposal_meta.json")
    patches_path = next(path for path in written if path.name == "config_patches.json")
    meta_payload = json.loads(meta_path.read_text(encoding="utf-8"))
    patches_payload = json.loads(patches_path.read_text(encoding="utf-8"))

    assert meta_payload["meta"]["config_patch_manifest_id"] == MANIFEST_ID
    assert len(patches_payload) == 2
    assert "manifest_id" not in patches_payload[0]["patch"]


def test_empty_manifest_does_not_create_reference_only_proposal(
    promotion_cycle,
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "empty.json"
    _write_manifest(manifest_path, patches=[])

    load_result = promotion_cycle._load_patches_for_promotion(
        promotion_input_manifest=manifest_path,
        non_canonical_demo_legacy_patches=False,
    )
    candidates = build_promotion_candidates_from_patches(load_result.patches)
    proposals = build_promotion_proposals([])

    assert load_result.patches == []
    assert load_result.input_references is not None
    assert candidates == []
    assert proposals == []


def test_legacy_demo_path_has_no_manifest_references(
    promotion_cycle,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    demo_dir = tmp_path / "reports" / "learning_snippets"
    demo_dir.mkdir(parents=True)
    demo_path = demo_dir / "demo_patches_for_promotion.json"
    demo_path.write_text(
        json.dumps(
            [
                {
                    "id": "demo-legacy-1",
                    "target": "research.offline.window_days",
                    "new_value": 45,
                    "status": PatchStatus.APPLIED_OFFLINE.value,
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    load_result = promotion_cycle._load_patches_for_promotion(
        promotion_input_manifest=None,
        non_canonical_demo_legacy_patches=True,
    )

    assert load_result.input_references is None
