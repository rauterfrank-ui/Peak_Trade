"""Contract tests for pit_futures_universe_manifest_v1 schema and digests."""

from __future__ import annotations

import pytest

from src.execution.replay_pack.canonical import dumps_canonical
from src.research.pit_futures_universe_manifest_v1 import (
    compute_manifest_digest,
    compute_membership_digest,
    format_pit_universe_manifest_reference_v1,
    manifest_from_dict,
    manifest_to_dict,
    parse_pit_universe_manifest_reference_v1,
)
from tests.research.fixtures.pit_futures_universe_manifest_v1.fixture_builder import (
    build_synthetic_epoch,
    build_synthetic_manifest,
    manifest_to_fixture_dict,
    synthetic_eligible_members,
)


def test_valid_single_epoch_fixture() -> None:
    manifest = build_synthetic_manifest()
    data = manifest_to_fixture_dict(manifest)
    round_trip = manifest_from_dict(data)
    assert round_trip.manifest_id == manifest.manifest_id
    assert len(round_trip.epochs) == 1
    assert round_trip.epochs[0].eligible_member_count == 6


def test_valid_multi_epoch_fixture() -> None:
    members = synthetic_eligible_members()
    manifest = build_synthetic_manifest(
        epochs=(
            build_synthetic_epoch(
                score_epoch=0,
                finalized_bar_close="2024-06-01T01:00:00Z",
                members=members,
            ),
            build_synthetic_epoch(
                score_epoch=1,
                finalized_bar_close="2024-06-01T02:00:00Z",
                members=members,
            ),
        )
    )
    assert len(manifest.epochs) == 2


def test_deterministic_digest() -> None:
    first = build_synthetic_manifest()
    second = build_synthetic_manifest()
    assert first.manifest_digest == second.manifest_digest
    assert first.membership_digest == second.membership_digest


def test_deterministic_canonical_json() -> None:
    manifest = build_synthetic_manifest()
    first = dumps_canonical(manifest_to_dict(manifest))
    second = dumps_canonical(manifest_to_dict(manifest))
    assert first == second


def test_unsorted_membership_rejected_by_validator() -> None:
    from src.research.pit_futures_universe_manifest_validator_v1 import (
        ValidatorErrorCode,
        validate_pit_futures_universe_manifest_v1,
    )

    shuffled = tuple(reversed(synthetic_eligible_members()))
    epoch = build_synthetic_epoch(
        score_epoch=0,
        finalized_bar_close="2024-06-01T01:00:00Z",
        members=shuffled,
    )
    manifest = build_synthetic_manifest(epochs=(epoch,))
    result = validate_pit_futures_universe_manifest_v1(manifest)
    assert result.verdict.value == "REJECTED"
    assert ValidatorErrorCode.UNSORTED_MEMBERSHIP.value in result.reason_codes


def test_serialization_round_trip() -> None:
    manifest = build_synthetic_manifest()
    data = manifest_to_dict(manifest)
    restored = manifest_from_dict(data)
    assert restored.manifest_digest == manifest.manifest_digest


def test_repeated_construction_identical_output() -> None:
    assert manifest_to_fixture_dict(build_synthetic_manifest()) == manifest_to_fixture_dict(
        build_synthetic_manifest()
    )


def test_one_bit_mutation_changes_digest() -> None:
    from dataclasses import replace

    manifest = build_synthetic_manifest()
    member = manifest.epochs[0].members[0]
    mutated_member = replace(member, base_asset="ETX")
    mutated_epoch = replace(
        manifest.epochs[0],
        members=(mutated_member, *manifest.epochs[0].members[1:]),
    )
    mutated = replace(manifest, epochs=(mutated_epoch,))
    assert compute_manifest_digest(mutated) != manifest.manifest_digest


def test_self_digest_exclusion() -> None:
    manifest = build_synthetic_manifest()
    payload = manifest_to_dict(manifest, include_manifest_digest=False)
    assert "manifest_digest" not in payload
    assert compute_manifest_digest(manifest) == compute_manifest_digest(
        manifest_from_dict({**payload, "manifest_digest": manifest.manifest_digest})
    )


def test_generated_at_does_not_change_membership_digest() -> None:
    first = build_synthetic_manifest(generated_at="2026-07-03T00:00:00Z")
    second = build_synthetic_manifest(generated_at="2026-07-04T00:00:00Z")
    assert compute_membership_digest(first) == compute_membership_digest(second)


def test_reference_parse_format_round_trip() -> None:
    manifest = build_synthetic_manifest()
    token = format_pit_universe_manifest_reference_v1(
        artifact_id=manifest.manifest_id,
        manifest_digest=manifest.manifest_digest,
    )
    parsed = parse_pit_universe_manifest_reference_v1(token)
    assert parsed.success is True
    assert parsed.reference is not None
    assert parsed.reference.manifest_digest == manifest.manifest_digest


@pytest.mark.parametrize(
    "token,expected",
    [
        ("pit_universe_manifest_v1::sha256:" + "a" * 64, "EMPTY_ARTIFACT_ID"),
        ("pit_universe_manifest_v1:id:md5:" + "a" * 64, "INVALID_DIGEST_ALGORITHM"),
        ("pit_universe_manifest_v1:id:sha256:abc", "INVALID_DIGEST_FORMAT"),
        ("pit_universe_manifest_v1:id:sha256:" + "A" * 64, "INVALID_DIGEST_FORMAT"),
        ("/datasets/foo/manifest.json", "ABSOLUTE_HOST_PATH_FORBIDDEN"),
        ("pit_universe_manifest_v1:../bad:sha256:" + "a" * 64, "TRAVERSAL_FORBIDDEN"),
        (" pit_universe_manifest_v1:id:sha256:" + "a" * 64, "WHITESPACE_FORBIDDEN"),
    ],
)
def test_reference_negative_cases(token: str, expected: str) -> None:
    parsed = parse_pit_universe_manifest_reference_v1(token)
    assert parsed.success is False
    assert expected in parsed.error_codes
