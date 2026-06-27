"""Contract tests for CandidateLineageManifest v1."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    CandidateLineageManifestV1,
    CandidateType,
    LineageRef,
    LineageRefType,
    LineageRelation,
    compute_lineage_manifest_integrity,
    deserialize_candidate_lineage_manifest_v1,
    manifest_to_canonical_dict,
    serialize_candidate_lineage_manifest_v1,
    validate_candidate_lineage_manifest_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    VERDICT_FUTURES_SCOPE_VIOLATION,
    canonical_futures_scope_ref,
    canonical_trading_logic_immutability_ref,
)


FIXED_NOW = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
LINEAGE_ID = "33333333-3333-4333-8333-333333333333"
MANIFEST_ID = "44444444-4444-4444-8444-444444444444"
PARENT_LINEAGE_ID = "55555555-5555-4555-8555-555555555555"


def _sample_refs() -> list[LineageRef]:
    return [
        LineageRef(
            ref_type=LineageRefType.EXPERIMENT,
            ref_id="exp-md5-12-abc",
            relation=LineageRelation.SOURCES,
            owner_domain="experiments/base",
            required=True,
        ),
        LineageRef(
            ref_type=LineageRefType.BACKTEST,
            ref_id="run-001",
            relation=LineageRelation.EVALUATES,
            owner_domain="experiments/tracking",
            required=False,
        ),
        LineageRef(
            ref_type=LineageRefType.EVIDENCE_OPS,
            ref_id="manifest-digest-ref",
            relation=LineageRelation.RETAINS,
            owner_domain="primary_evidence_retention",
            required=True,
            digest="a" * 64,
        ),
    ]


def _valid_manifest(*, refs: list[LineageRef] | None = None) -> CandidateLineageManifestV1:
    manifest = CandidateLineageManifestV1(
        schema_version="1.0",
        lineage_manifest_id=LINEAGE_ID,
        candidate_id="candidate-bundle-001",
        candidate_type=CandidateType.CONFIG_PATCH_BUNDLE,
        candidate_contract_ref=MANIFEST_ID,
        refs=refs if refs is not None else _sample_refs(),
        created_at=FIXED_NOW,
        created_by="package_a_contract_tests",
        parent_lineage_manifest_ids=[PARENT_LINEAGE_ID],
        futures_scope_ref=canonical_futures_scope_ref(),
        trading_logic_immutability_ref=canonical_trading_logic_immutability_ref(),
        metadata={"proposal_type": "OFFLINE_PROMOTE"},
    )
    manifest.integrity = compute_lineage_manifest_integrity(manifest)
    return manifest


def test_valid_candidate_lineage_manifest_with_typed_refs() -> None:
    payload = manifest_to_canonical_dict(_valid_manifest(), include_integrity=True)
    valid, phase, errors, verdict = validate_candidate_lineage_manifest_v1(payload)
    assert valid is True, errors
    assert phase.value == "result"
    assert verdict is None


def test_deterministic_json_roundtrip() -> None:
    manifest = _valid_manifest()
    first = serialize_candidate_lineage_manifest_v1(manifest)
    second = serialize_candidate_lineage_manifest_v1(manifest)
    assert first == second
    roundtrip = deserialize_candidate_lineage_manifest_v1(json.loads(first))
    assert roundtrip.lineage_manifest_id == LINEAGE_ID
    assert len(roundtrip.refs) == 3


def test_parent_lineage_reference_supported() -> None:
    payload = manifest_to_canonical_dict(_valid_manifest(), include_integrity=True)
    assert payload["parent_lineage_manifest_ids"] == [PARENT_LINEAGE_ID]


def test_unknown_schema_version_rejected() -> None:
    payload = manifest_to_canonical_dict(_valid_manifest(), include_integrity=True)
    payload["schema_version"] = "2.0"
    valid, phase, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is False
    assert phase.value == "schema_version"
    assert "unsupported schema_version" in errors[0]


def test_unknown_ref_type_rejected() -> None:
    payload = manifest_to_canonical_dict(_valid_manifest(), include_integrity=True)
    payload["refs"][0]["ref_type"] = "unknown_ref"
    valid, phase, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is False
    assert phase.value == "lineage_references"
    assert "unknown ref_type" in errors[0]


def test_unknown_relation_rejected() -> None:
    payload = manifest_to_canonical_dict(_valid_manifest(), include_integrity=True)
    payload["refs"][0]["relation"] = "unknown_relation"
    valid, phase, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is False
    assert phase.value == "lineage_references"
    assert "unknown relation" in errors[0]


def test_duplicate_ref_entry_rejected() -> None:
    refs = _sample_refs()
    refs.append(
        LineageRef(
            ref_type=LineageRefType.EXPERIMENT,
            ref_id=refs[0].ref_id,
            relation=refs[0].relation,
            owner_domain=refs[0].owner_domain,
            required=False,
        )
    )
    payload = manifest_to_canonical_dict(_valid_manifest(refs=refs), include_integrity=True)
    valid, phase, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is False
    assert phase.value == "cardinality"
    assert "duplicate ref entry" in errors[0]


def test_experiment_cardinality_exceeded_rejected() -> None:
    refs = _sample_refs()
    refs.append(
        LineageRef(
            ref_type=LineageRefType.EXPERIMENT,
            ref_id="exp-second",
            relation=LineageRelation.EXTENDS,
            owner_domain="experiments/base",
            required=False,
        )
    )
    payload = manifest_to_canonical_dict(_valid_manifest(refs=refs), include_integrity=True)
    valid, phase, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is False
    assert phase.value == "cardinality"
    assert "experiment" in errors[0]


def test_evidence_ops_required_digest_missing_rejected() -> None:
    refs = [
        LineageRef(
            ref_type=LineageRefType.EVIDENCE_OPS,
            ref_id="missing-digest",
            relation=LineageRelation.RETAINS,
            owner_domain="primary_evidence_retention",
            required=True,
        )
    ]
    payload = manifest_to_canonical_dict(_valid_manifest(refs=refs), include_integrity=True)
    valid, phase, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is False
    assert phase.value == "lineage_references"
    assert "evidence_ops ref requires digest" in errors[0]


def test_invalid_digest_rejected() -> None:
    payload = manifest_to_canonical_dict(_valid_manifest(), include_integrity=True)
    payload["refs"][2]["digest"] = "not-a-digest"
    valid, phase, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is False
    assert phase.value == "integrity"


@pytest.mark.parametrize(
    "scope_value",
    [
        {"scope": "BTC_ONLY"},
        {"scope": "XBT_PERP"},
        {"scope": "BITCOIN_FUTURES"},
        {"scope": "SPOT_ONLY"},
        {"scope": "SYNTHETIC_SPOT"},
    ],
)
def test_invalid_futures_scope_rejected(scope_value: dict[str, str]) -> None:
    payload = manifest_to_canonical_dict(_valid_manifest(), include_integrity=True)
    payload["futures_scope_ref"] = {
        **canonical_futures_scope_ref(),
        **scope_value,
    }
    valid, phase, _, verdict = validate_candidate_lineage_manifest_v1(payload)
    assert valid is False
    assert phase.value == "futures_scope"
    assert verdict == VERDICT_FUTURES_SCOPE_VIOLATION


def test_empty_refs_only_allowed_in_fixture_mode() -> None:
    manifest = _valid_manifest(refs=[])
    payload = manifest_to_canonical_dict(manifest, include_integrity=True)
    valid, phase, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is False
    assert phase.value == "lineage_references"
    assert "fixture mode" in errors[0]

    payload["metadata"] = {"fixture_kind": "lineage_fixture"}
    manifest = deserialize_candidate_lineage_manifest_v1(
        {**payload, "integrity": {"content_sha256": "0" * 64}}
    )
    payload["integrity"] = {
        "content_sha256": compute_lineage_manifest_integrity(manifest).content_sha256
    }
    valid, phase, _, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is True, phase
