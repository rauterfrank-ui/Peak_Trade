"""Dedicated engine characterization tests for manifest-era offline promotion (GAP-007)."""

from __future__ import annotations

import json
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


FIXED_NOW = datetime(2026, 6, 27, 15, 0, 0, tzinfo=timezone.utc)
MANIFEST_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
LINEAGE_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


def _immutability_compliant_patch(*, patch_id: str = "patch-engine-1") -> ConfigPatch:
    return ConfigPatch(
        id=patch_id,
        target="research.offline.window_days",
        old_value=30,
        new_value=45,
        status=PatchStatus.APPLIED_OFFLINE,
        generated_at=FIXED_NOW,
        confidence_score=0.92,
        source_experiment_id="exp-engine-1",
    )


def _write_manifest(path: Path, *, patches: list[ConfigPatch]) -> None:
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=LINEAGE_ID,
    )
    manifest.patches = patches
    manifest.integrity = compute_manifest_integrity(manifest)
    path.write_text(serialize_config_patch_manifest_v1(manifest), encoding="utf-8")


def test_build_candidates_only_includes_applied_offline_or_promoted() -> None:
    patches = [
        _immutability_compliant_patch(patch_id="applied"),
        ConfigPatch(
            id="proposed",
            target="research.offline.feature_flag",
            old_value=False,
            new_value=True,
            status=PatchStatus.PROPOSED,
        ),
        ConfigPatch(
            id="rejected",
            target="research.offline.other_flag",
            old_value=True,
            new_value=False,
            status=PatchStatus.REJECTED,
        ),
    ]
    candidates = build_promotion_candidates_from_patches(patches)
    assert [c.patch.id for c in candidates] == ["applied"]


def test_build_candidates_default_ineligible_and_tag_heuristics_unchanged() -> None:
    patch = _immutability_compliant_patch()
    candidates = build_promotion_candidates_from_patches([patch])
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.eligible_for_live is False
    assert candidate.patch.target == patch.target
    assert candidate.patch.new_value == patch.new_value
    assert "trigger" not in candidate.tags


def test_manifest_fk_refs_do_not_change_candidate_count(tmp_path: Path) -> None:
    patch = _immutability_compliant_patch()
    manifest_path = tmp_path / "input.json"
    _write_manifest(manifest_path, patches=[patch])

    direct_candidates = build_promotion_candidates_from_patches([patch])
    loaded = load_promotion_input_from_manifest_path(manifest_path)
    manifest_candidates = build_promotion_candidates_from_patches(loaded.patches)
    refs = promotion_input_references_from_manifest(loaded.manifest)

    assert len(manifest_candidates) == len(direct_candidates)
    assert refs.config_patch_manifest_id == MANIFEST_ID
    assert refs.candidate_lineage_manifest_ref == LINEAGE_ID


def test_build_proposals_returns_empty_without_accepted_decisions() -> None:
    patch = _immutability_compliant_patch()
    candidate = PromotionCandidate(patch=patch, eligible_for_live=False)
    decision = PromotionDecision(
        candidate=candidate,
        status=DecisionStatus.REJECTED_BY_POLICY,
        reasons=["candidate not marked as eligible_for_live"],
    )
    assert build_promotion_proposals([decision]) == []


def test_materialize_proposal_meta_carries_fk_refs_without_payload_duplication(
    tmp_path: Path,
) -> None:
    patch = _immutability_compliant_patch()
    manifest_path = tmp_path / "input.json"
    _write_manifest(manifest_path, patches=[patch])
    loaded = load_promotion_input_from_manifest_path(manifest_path)
    refs = promotion_input_references_from_manifest(loaded.manifest)

    candidate = PromotionCandidate(patch=patch, eligible_for_live=True, tags=["research"])
    decision = PromotionDecision(
        candidate=candidate,
        status=DecisionStatus.ACCEPTED_FOR_PROPOSAL,
        reasons=[],
    )
    proposals = build_promotion_proposals([decision], proposal_id_prefix="offline_promotion_test")
    assert len(proposals) == 1
    proposal = proposals[0]
    apply_promotion_input_references_to_proposal(proposal, refs)

    output_dir = tmp_path / "proposals"
    materialize_promotion_proposals(proposals, output_dir)

    meta_path = output_dir / proposal.proposal_id / "proposal_meta.json"
    meta_payload = json.loads(meta_path.read_text(encoding="utf-8"))
    meta_fields = meta_payload["meta"]
    assert meta_fields["config_patch_manifest_id"] == MANIFEST_ID
    assert meta_fields["candidate_lineage_manifest_ref"] == LINEAGE_ID
    forbidden = {
        "patches",
        "manifest",
        "lineage_manifest",
        "config_patch_manifest",
        "candidate_lineage_manifest",
        "integrity",
    }
    assert forbidden.isdisjoint(meta_fields.keys())


def test_patch_empty_manifest_yields_zero_candidates_and_zero_proposals(tmp_path: Path) -> None:
    manifest_path = tmp_path / "empty.json"
    _write_manifest(manifest_path, patches=[])
    loaded = load_promotion_input_from_manifest_path(manifest_path)
    candidates = build_promotion_candidates_from_patches(loaded.patches)
    assert candidates == []
    assert build_promotion_proposals([]) == []
