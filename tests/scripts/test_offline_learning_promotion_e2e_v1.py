"""Offline E2E contract test: Learning-Bridge → ConfigPatchManifest → Promotion artifacts (GAP-007)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.governance.promotion_loop import (
    build_promotion_candidates_from_patches,
    build_promotion_proposals,
    filter_candidates_for_live,
    materialize_promotion_proposals,
)
from src.governance.promotion_loop.models import DecisionStatus
from src.governance.promotion_loop.policy import AutoApplyPolicy
from src.governance.promotion_loop.proposal_input_refs_v1 import (
    apply_promotion_input_references_to_proposal,
    promotion_input_references_from_manifest,
)
from src.meta.learning_loop.config_patch_manifest_v1 import load_promotion_input_from_manifest_path
from src.meta.learning_loop.manifest_bridge_v1 import (
    LearningManifestBridgeError,
    produce_config_patch_manifest_v1_from_paths,
)
from src.meta.learning_loop.models import PatchStatus


FIXED_NOW = datetime(2026, 6, 27, 16, 0, 0, tzinfo=timezone.utc)
MANIFEST_ID = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
LINEAGE_ID = "ffffffff-ffff-4fff-8fff-ffffffffffff"


def _write_learning_input(path: Path) -> None:
    payload = {
        "patches": [
            {
                "id": "e2e-patch-1",
                "target": "research.offline.window_days",
                "old_value": 30,
                "new_value": 45,
                "status": PatchStatus.APPLIED_OFFLINE.value,
                "reason": "offline e2e contract",
                "source_experiment_id": "exp-e2e-1",
                "confidence_score": 0.91,
            }
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_offline_learning_to_promotion_e2e_contract(tmp_path: Path) -> None:
    input_path = tmp_path / "learning_input.json"
    manifest_path = tmp_path / "promotion_input_manifest.json"
    proposal_root = tmp_path / "live_promotion"
    live_override_path = tmp_path / "config" / "live_overrides" / "auto.toml"

    _write_learning_input(input_path)
    produce_config_patch_manifest_v1_from_paths(
        input_path=input_path,
        output_path=manifest_path,
        manifest_id=MANIFEST_ID,
        lineage_manifest_ref=LINEAGE_ID,
        generated_at=FIXED_NOW,
    )

    promotion_input = load_promotion_input_from_manifest_path(manifest_path)
    refs = promotion_input_references_from_manifest(promotion_input.manifest)
    patches = promotion_input.patches
    assert len(patches) == 1

    candidates = build_promotion_candidates_from_patches(patches)
    assert len(candidates) == 1
    candidates[0].eligible_for_live = True

    decisions = filter_candidates_for_live(candidates, safety_config=None, mode="manual_only")
    accepted = [d for d in decisions if d.status is DecisionStatus.ACCEPTED_FOR_PROPOSAL]
    assert len(accepted) == 1

    proposals = build_promotion_proposals(accepted, proposal_id_prefix="offline_e2e")
    assert len(proposals) == 1
    proposal = proposals[0]
    apply_promotion_input_references_to_proposal(proposal, refs)

    materialize_promotion_proposals(proposals, proposal_root)

    meta_path = proposal_root / proposal.proposal_id / "proposal_meta.json"
    meta_payload = json.loads(meta_path.read_text(encoding="utf-8"))
    meta_fields = meta_payload["meta"]
    assert meta_fields["config_patch_manifest_id"] == MANIFEST_ID
    assert meta_fields["candidate_lineage_manifest_ref"] == LINEAGE_ID
    assert "patches" not in meta_fields
    assert "config_patch_manifest" not in meta_fields

    from src.governance.promotion_loop.engine import apply_proposals_to_live_overrides

    applied = apply_proposals_to_live_overrides(
        proposals,
        policy=AutoApplyPolicy(mode="manual_only"),
        live_override_path=live_override_path,
    )
    assert applied is None
    assert not live_override_path.exists()


def test_offline_e2e_patch_empty_manifest_produces_zero_proposals(tmp_path: Path) -> None:
    input_path = tmp_path / "empty_input.json"
    manifest_path = tmp_path / "empty_manifest.json"
    input_path.write_text(json.dumps({"patches": []}), encoding="utf-8")

    produce_config_patch_manifest_v1_from_paths(
        input_path=input_path,
        output_path=manifest_path,
        manifest_id=MANIFEST_ID,
        lineage_manifest_ref=LINEAGE_ID,
        generated_at=FIXED_NOW,
    )

    promotion_input = load_promotion_input_from_manifest_path(manifest_path)
    candidates = build_promotion_candidates_from_patches(promotion_input.patches)
    assert candidates == []

    decisions = filter_candidates_for_live(candidates, safety_config=None, mode="manual_only")
    proposals = build_promotion_proposals(decisions)
    assert proposals == []


def test_offline_e2e_rejects_forbidden_strategy_target_at_bridge(tmp_path: Path) -> None:
    input_path = tmp_path / "forbidden_input.json"
    manifest_path = tmp_path / "forbidden_manifest.json"
    payload = {
        "patches": [
            {
                "id": "bad-patch",
                "target": "strategy.selection.mode",
                "new_value": "bull",
                "status": PatchStatus.APPLIED_OFFLINE.value,
            }
        ]
    }
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises((LearningManifestBridgeError, Exception)):
        produce_config_patch_manifest_v1_from_paths(
            input_path=input_path,
            output_path=manifest_path,
            manifest_id=MANIFEST_ID,
            lineage_manifest_ref=LINEAGE_ID,
            generated_at=FIXED_NOW,
        )
