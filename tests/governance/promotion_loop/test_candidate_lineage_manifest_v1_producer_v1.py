"""Producer tests for Package F CandidateLineageManifest v1 offline production."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    CandidateLineageManifestError,
    CandidateLineageManifestValidationError,
    LineageRefType,
    LineageRelation,
    build_candidate_lineage_manifest_v1_from_producer_input,
    compute_lineage_manifest_integrity,
    deserialize_candidate_lineage_manifest_v1,
    load_lineage_producer_input_from_path,
    produce_candidate_lineage_manifest_v1_from_paths,
    serialize_candidate_lineage_manifest_v1,
    validate_candidate_lineage_manifest_v1,
    write_candidate_lineage_manifest_v1_atomic,
)
from src.meta.learning_loop.contract_safety_v1 import (
    VERDICT_FUTURES_SCOPE_VIOLATION,
    VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION,
    canonical_futures_scope_ref,
    canonical_trading_logic_immutability_ref,
)


FIXED_NOW = datetime(2026, 6, 27, 16, 30, 0, tzinfo=timezone.utc)
LINEAGE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
CONTRACT_REF = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
PARENT_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def _minimal_ref(*, ref_id: str = "exp-md5-12-abc") -> dict:
    return {
        "ref_type": LineageRefType.EXPERIMENT.value,
        "ref_id": ref_id,
        "relation": LineageRelation.SOURCES.value,
        "owner_domain": "experiments/base",
        "required": True,
    }


def _minimal_input(*, refs: list[dict] | None = None) -> dict:
    payload = {
        "lineage_manifest_id": LINEAGE_ID,
        "candidate_id": "candidate-bundle-f-001",
        "candidate_type": "config_patch_bundle",
        "candidate_contract_ref": CONTRACT_REF,
        "refs": refs if refs is not None else [_minimal_ref()],
        "created_at": FIXED_NOW.isoformat(),
        "created_by": "package_f_producer_tests",
    }
    return payload


def _full_input() -> dict:
    return {
        **_minimal_input(),
        "parent_lineage_manifest_ids": [PARENT_ID],
        "metadata": {"proposal_type": "OFFLINE_PROMOTE"},
        "refs": [
            _minimal_ref(),
            {
                "ref_type": LineageRefType.BACKTEST.value,
                "ref_id": "run-001",
                "relation": LineageRelation.EVALUATES.value,
                "owner_domain": "experiments/tracking",
                "required": False,
            },
            {
                "ref_type": LineageRefType.EVIDENCE_OPS.value,
                "ref_id": "manifest-digest-ref",
                "relation": LineageRelation.RETAINS.value,
                "owner_domain": "primary_evidence_retention",
                "required": True,
                "digest": "a" * 64,
            },
        ],
    }


def test_minimal_explicit_ref_input_produces_valid_manifest() -> None:
    manifest = build_candidate_lineage_manifest_v1_from_producer_input(
        _minimal_input(),
        created_at=FIXED_NOW,
    )
    assert manifest.lineage_manifest_id == LINEAGE_ID
    assert manifest.candidate_contract_ref == CONTRACT_REF
    assert len(manifest.refs) == 1


def test_full_ref_input_passes_contract_validation() -> None:
    manifest = build_candidate_lineage_manifest_v1_from_producer_input(
        _full_input(),
        created_at=FIXED_NOW,
    )
    payload = json.loads(serialize_candidate_lineage_manifest_v1(manifest))
    valid, phase, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is True, (phase, errors)


def test_deterministic_manifest_id_and_byte_identical_serialization() -> None:
    raw = _full_input()
    first = build_candidate_lineage_manifest_v1_from_producer_input(raw, created_at=FIXED_NOW)
    second = build_candidate_lineage_manifest_v1_from_producer_input(raw, created_at=FIXED_NOW)
    first_json = serialize_candidate_lineage_manifest_v1(first)
    second_json = serialize_candidate_lineage_manifest_v1(second)
    assert first.lineage_manifest_id == LINEAGE_ID
    assert first_json == second_json


def test_permuted_ref_input_order_yields_identical_canonical_json() -> None:
    refs_a = [
        _minimal_ref(ref_id="exp-a"),
        {
            "ref_type": LineageRefType.BACKTEST.value,
            "ref_id": "run-001",
            "relation": LineageRelation.EVALUATES.value,
            "owner_domain": "experiments/tracking",
            "required": False,
        },
    ]
    refs_b = list(reversed(refs_a))
    manifest_a = build_candidate_lineage_manifest_v1_from_producer_input(
        _minimal_input(refs=refs_a),
        created_at=FIXED_NOW,
    )
    manifest_b = build_candidate_lineage_manifest_v1_from_producer_input(
        _minimal_input(refs=refs_b),
        created_at=FIXED_NOW,
    )
    assert serialize_candidate_lineage_manifest_v1(
        manifest_a
    ) == serialize_candidate_lineage_manifest_v1(manifest_b)


def test_unknown_top_level_field_rejected() -> None:
    raw = _minimal_input()
    raw["unexpected_field"] = True
    with pytest.raises(CandidateLineageManifestError, match="unknown producer input fields"):
        build_candidate_lineage_manifest_v1_from_producer_input(raw, created_at=FIXED_NOW)


def test_invalid_ref_form_rejected() -> None:
    raw = _minimal_input(refs=[{"ref_type": "experiment"}])
    with pytest.raises(CandidateLineageManifestError, match="missing required field"):
        build_candidate_lineage_manifest_v1_from_producer_input(raw, created_at=FIXED_NOW)


def test_missing_required_input_field_rejected() -> None:
    raw = _minimal_input()
    raw.pop("candidate_id")
    with pytest.raises(
        CandidateLineageManifestError, match="missing required producer input field"
    ):
        build_candidate_lineage_manifest_v1_from_producer_input(raw, created_at=FIXED_NOW)


def test_duplicate_ref_entry_rejected_by_contract() -> None:
    ref = _minimal_ref()
    raw = _minimal_input(refs=[ref, dict(ref)])
    with pytest.raises(CandidateLineageManifestValidationError, match="validation failed"):
        build_candidate_lineage_manifest_v1_from_producer_input(raw, created_at=FIXED_NOW)


def test_payload_duplication_attempt_in_metadata_rejected() -> None:
    raw = _minimal_input()
    raw["metadata"] = {"patches": [{"target": "strategy.leverage"}]}
    with pytest.raises(CandidateLineageManifestError, match="forbidden payload key"):
        build_candidate_lineage_manifest_v1_from_producer_input(raw, created_at=FIXED_NOW)


def test_payload_duplication_attempt_in_ref_rejected() -> None:
    ref = _minimal_ref()
    ref["strategy"] = {"param": 1}
    with pytest.raises(CandidateLineageManifestError, match="forbidden payload key"):
        build_candidate_lineage_manifest_v1_from_producer_input(
            _minimal_input(refs=[ref]),
            created_at=FIXED_NOW,
        )


def test_futures_scope_violation_rejected() -> None:
    raw = _minimal_input()
    raw["futures_scope_ref"] = {**canonical_futures_scope_ref(), "scope": "BTC_ONLY"}
    with pytest.raises(CandidateLineageManifestValidationError) as exc:
        build_candidate_lineage_manifest_v1_from_producer_input(raw, created_at=FIXED_NOW)
    assert exc.value.verdict == VERDICT_FUTURES_SCOPE_VIOLATION


def test_trading_logic_immutability_violation_rejected() -> None:
    raw = _minimal_input()
    raw["trading_logic_immutability_ref"] = {
        **canonical_trading_logic_immutability_ref(),
        "reference_only": False,
    }
    with pytest.raises(CandidateLineageManifestValidationError) as exc:
        build_candidate_lineage_manifest_v1_from_producer_input(raw, created_at=FIXED_NOW)
    assert exc.value.verdict == VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION


def test_empty_refs_without_fixture_mode_rejected() -> None:
    with pytest.raises(CandidateLineageManifestValidationError, match="validation failed"):
        build_candidate_lineage_manifest_v1_from_producer_input(
            _minimal_input(refs=[]),
            created_at=FIXED_NOW,
        )


def test_empty_refs_allowed_in_fixture_mode() -> None:
    raw = _minimal_input(refs=[])
    raw["metadata"] = {"fixture_kind": "lineage_fixture"}
    manifest = build_candidate_lineage_manifest_v1_from_producer_input(raw, created_at=FIXED_NOW)
    assert manifest.refs == []


def test_serialized_output_has_no_runtime_authority_fields() -> None:
    manifest = build_candidate_lineage_manifest_v1_from_producer_input(
        _full_input(),
        created_at=FIXED_NOW,
    )
    payload = json.loads(serialize_candidate_lineage_manifest_v1(manifest))
    forbidden = {
        "runtime",
        "live",
        "arming",
        "order_authority",
        "auto_apply",
        "promotion_engine",
    }
    assert forbidden.isdisjoint(set(payload))
    assert "patches" not in payload


def test_atomic_writer_success(tmp_path: Path) -> None:
    manifest = build_candidate_lineage_manifest_v1_from_producer_input(
        _full_input(),
        created_at=FIXED_NOW,
    )
    out = tmp_path / "lineage.json"
    write_candidate_lineage_manifest_v1_atomic(manifest, out)
    loaded = deserialize_candidate_lineage_manifest_v1(json.loads(out.read_text(encoding="utf-8")))
    assert loaded.lineage_manifest_id == LINEAGE_ID


def test_atomic_writer_validation_failure_leaves_existing_output_unchanged(tmp_path: Path) -> None:
    out = tmp_path / "lineage.json"
    good = build_candidate_lineage_manifest_v1_from_producer_input(
        _full_input(),
        created_at=FIXED_NOW,
    )
    write_candidate_lineage_manifest_v1_atomic(good, out)
    original = out.read_text(encoding="utf-8")

    bad = build_candidate_lineage_manifest_v1_from_producer_input(
        _full_input(),
        created_at=FIXED_NOW,
    )
    bad.integrity = compute_lineage_manifest_integrity(bad)
    bad.integrity = type(bad.integrity)(content_sha256="0" * 64)

    with pytest.raises(CandidateLineageManifestValidationError):
        write_candidate_lineage_manifest_v1_atomic(bad, out)

    assert out.read_text(encoding="utf-8") == original
    assert not out.with_name(out.name + ".tmp").exists()


def test_produce_from_paths_end_to_end(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    input_path.write_text(json.dumps(_full_input()), encoding="utf-8")

    manifest = produce_candidate_lineage_manifest_v1_from_paths(
        input_path=input_path,
        output_path=output_path,
        created_at=FIXED_NOW,
    )
    assert output_path.is_file()
    assert manifest.lineage_manifest_id == LINEAGE_ID
    roundtrip = deserialize_candidate_lineage_manifest_v1(
        json.loads(output_path.read_text(encoding="utf-8"))
    )
    assert roundtrip.candidate_contract_ref == CONTRACT_REF


def test_no_partial_output_on_production_validation_failure(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    bad_input = _minimal_input()
    bad_input["refs"] = [
        {
            "ref_type": LineageRefType.EVIDENCE_OPS.value,
            "ref_id": "missing-digest",
            "relation": LineageRelation.RETAINS.value,
            "owner_domain": "primary_evidence_retention",
            "required": True,
        }
    ]
    input_path.write_text(json.dumps(bad_input), encoding="utf-8")

    with pytest.raises(CandidateLineageManifestValidationError):
        produce_candidate_lineage_manifest_v1_from_paths(
            input_path=input_path,
            output_path=output_path,
            created_at=FIXED_NOW,
        )

    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".tmp").exists()


def test_writer_replace_failure_cleans_temp_and_preserves_existing(
    tmp_path: Path, monkeypatch
) -> None:
    out = tmp_path / "lineage.json"
    good = build_candidate_lineage_manifest_v1_from_producer_input(
        _full_input(),
        created_at=FIXED_NOW,
    )
    write_candidate_lineage_manifest_v1_atomic(good, out)
    original = out.read_text(encoding="utf-8")

    def _fail_replace(self, target):  # type: ignore[no-untyped-def]
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", _fail_replace, raising=True)

    with pytest.raises(OSError, match="replace failed"):
        write_candidate_lineage_manifest_v1_atomic(good, out)

    assert out.read_text(encoding="utf-8") == original
    assert not out.with_name(out.name + ".tmp").exists()


def test_load_input_rejects_non_json_suffix(tmp_path: Path) -> None:
    path = tmp_path / "input.jsonl"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(CandidateLineageManifestError, match="unsupported input format"):
        load_lineage_producer_input_from_path(path)


def test_load_input_unknown_field_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "input.json"
    path.write_text(json.dumps({**_minimal_input(), "patches": []}), encoding="utf-8")
    with pytest.raises(CandidateLineageManifestError, match="unknown producer input fields"):
        load_lineage_producer_input_from_path(path)


def test_producer_does_not_mutate_registry_or_external_files(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    registry = tmp_path / "registry.json"
    registry.write_text('{"unchanged": true}', encoding="utf-8")
    input_path.write_text(json.dumps(_full_input()), encoding="utf-8")

    before = registry.read_text(encoding="utf-8")
    produce_candidate_lineage_manifest_v1_from_paths(
        input_path=input_path,
        output_path=output_path,
        created_at=FIXED_NOW,
    )
    assert registry.read_text(encoding="utf-8") == before
