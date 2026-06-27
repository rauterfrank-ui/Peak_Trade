"""Contract tests for promotion input reference propagation (Package C)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.governance.promotion_loop.models import PromotionProposal
from src.governance.promotion_loop.proposal_input_refs_v1 import (
    PromotionInputReferencesError,
    PromotionInputReferencesV1,
    apply_promotion_input_references_to_proposal,
    promotion_input_references_from_manifest,
    validate_proposal_reference_meta_fields,
)
from src.meta.learning_loop.config_patch_manifest_v1 import build_empty_config_patch_manifest_v1
from src.meta.learning_loop.contract_safety_v1 import SCHEMA_VERSION_V1


FIXED_NOW = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
MANIFEST_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
LINEAGE_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


def _manifest(*, lineage_ref: str | None = LINEAGE_ID):
    return build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=lineage_ref or LINEAGE_ID,
    )


def test_references_from_manifest_extracts_ids() -> None:
    refs = promotion_input_references_from_manifest(_manifest())

    assert refs.config_patch_manifest_id == MANIFEST_ID
    assert refs.candidate_lineage_manifest_ref == LINEAGE_ID
    assert refs.config_patch_manifest_schema_version == SCHEMA_VERSION_V1
    assert refs.candidate_lineage_manifest_schema_version == SCHEMA_VERSION_V1


def test_references_to_proposal_meta_fields_are_reference_only() -> None:
    refs = promotion_input_references_from_manifest(_manifest())
    fields = refs.to_proposal_meta_fields()

    assert set(fields) == {
        "config_patch_manifest_id",
        "candidate_lineage_manifest_ref",
        "config_patch_manifest_schema_version",
        "candidate_lineage_manifest_schema_version",
    }
    assert "patches" not in fields
    assert "integrity" not in fields


def test_apply_references_to_proposal_is_deterministic() -> None:
    refs = promotion_input_references_from_manifest(_manifest())
    proposal = PromotionProposal(
        proposal_id="live_promotion_test",
        title="t",
        description="d",
        meta={"generated_at": "20260627T120000Z", "num_candidates": 1},
    )

    apply_promotion_input_references_to_proposal(proposal, refs)
    apply_promotion_input_references_to_proposal(proposal, refs)

    assert proposal.meta["config_patch_manifest_id"] == MANIFEST_ID
    assert proposal.meta["candidate_lineage_manifest_ref"] == LINEAGE_ID


def test_apply_references_rejects_conflicting_manifest_id() -> None:
    refs = promotion_input_references_from_manifest(_manifest())
    proposal = PromotionProposal(
        proposal_id="live_promotion_test",
        title="t",
        description="d",
        meta={"config_patch_manifest_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc"},
    )

    with pytest.raises(PromotionInputReferencesError, match="conflicting"):
        apply_promotion_input_references_to_proposal(proposal, refs)


def test_validate_rejects_embedded_manifest_payload_key() -> None:
    with pytest.raises(PromotionInputReferencesError, match="embedded manifest payload"):
        validate_proposal_reference_meta_fields(
            {
                "config_patch_manifest_id": MANIFEST_ID,
                "config_patch_manifest_schema_version": SCHEMA_VERSION_V1,
                "patches": "[]",
            }
        )


def test_validate_rejects_trading_logic_token_in_reference() -> None:
    with pytest.raises(PromotionInputReferencesError, match="forbidden trading-logic token"):
        validate_proposal_reference_meta_fields(
            {
                "config_patch_manifest_id": MANIFEST_ID,
                "config_patch_manifest_schema_version": SCHEMA_VERSION_V1,
                "candidate_lineage_manifest_ref": "strategy-injection-attempt",
            }
        )


def test_validate_rejects_invalid_manifest_uuid() -> None:
    with pytest.raises(PromotionInputReferencesError, match="must be a UUID"):
        validate_proposal_reference_meta_fields(
            {
                "config_patch_manifest_id": "not-a-uuid",
                "config_patch_manifest_schema_version": SCHEMA_VERSION_V1,
            }
        )


def test_validate_rejects_unknown_schema_version() -> None:
    with pytest.raises(PromotionInputReferencesError, match="unsupported"):
        validate_proposal_reference_meta_fields(
            {
                "config_patch_manifest_id": MANIFEST_ID,
                "config_patch_manifest_schema_version": "9.9",
            }
        )


def test_validate_rejects_lineage_schema_without_lineage_ref() -> None:
    with pytest.raises(
        PromotionInputReferencesError, match="without candidate_lineage_manifest_ref"
    ):
        validate_proposal_reference_meta_fields(
            {
                "config_patch_manifest_id": MANIFEST_ID,
                "config_patch_manifest_schema_version": SCHEMA_VERSION_V1,
                "candidate_lineage_manifest_schema_version": SCHEMA_VERSION_V1,
            }
        )


def test_references_from_manifest_rejects_invalid_manifest_id() -> None:
    manifest = _manifest()
    manifest.manifest_id = "invalid"

    with pytest.raises(PromotionInputReferencesError, match="must be a UUID"):
        promotion_input_references_from_manifest(manifest)


def test_direct_reference_model_rejects_missing_manifest_id() -> None:
    with pytest.raises(PromotionInputReferencesError, match="config_patch_manifest_id is required"):
        validate_proposal_reference_meta_fields(
            {"config_patch_manifest_schema_version": SCHEMA_VERSION_V1}
        )
