"""Contract tests for pit_futures_instrument_lifecycle_registry_persistence_v1 — Slice C."""

from __future__ import annotations

import dataclasses
import itertools
import json
import os
from pathlib import Path

import pytest

from src.research.pit_futures_instrument_lifecycle_registry_persistence_v1 import (
    OverwritePolicy,
    PersistenceErrorCode,
    parse_registry_snapshot_dict_v1,
    read_registry_snapshot_v1,
    registry_snapshot_to_canonical_bytes,
    write_registry_snapshot_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    INPUT_CONTRACT_VERSION,
    REGISTRY_VERSION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    InstrumentLifecycleIntervalV1,
    LifecycleRegistryErrorCode,
    ObservationKind,
    RegistrySnapshotV1,
    SourceObservationRecordV1,
    SourceTrustLevel,
    SuspensionSubIntervalV1,
    assemble_registry_snapshot_v1,
    assemble_registry_snapshot_v1,
    attach_snapshot_digest,
    build_interval_from_observation_v1,
    compute_interval_digest,
    compute_observation_digest,
    compute_registry_snapshot_digest,
    normalize_source_observation_record_v1,
    registry_snapshot_to_dict,
)
from src.research.pit_futures_instrument_lifecycle_registry_validator_v1 import (
    ValidationVerdict,
    validate_pit_futures_instrument_lifecycle_registry_snapshot_v1,
)

_SOURCE_ID = "synthetic:test:record:v0"
_SNAPSHOT_REF = "synthetic:test:snapshot:v0"
_LISTING = "2024-01-01T00:00:00Z"
_ELIGIBLE = "2024-01-02T00:00:00Z"
_GENERATED_AT = "2026-07-03T02:00:00Z"
_CONFIG_DIGEST = "b" * 64
_IMPL_DIGEST = "c" * 64


def _observation_payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "base_asset": "ETH",
        "contract_type": "linear_perpetual",
        "correction_provenance_ref": None,
        "delisting_time": None,
        "eligible_from": _ELIGIBLE,
        "eligible_until": None,
        "expiry_time": None,
        "listing_time": _LISTING,
        "market_type": "futures",
        "native_instrument_id": None,
        "observation_kind": ObservationKind.LISTING.value,
        "quote_asset": "USDT",
        "settlement_asset": "USDT",
        "source_effective_at": _LISTING,
        "source_id": _SOURCE_ID,
        "source_observed_at": _LISTING,
        "source_priority": 1,
        "source_snapshot_digest": "a" * 64,
        "source_snapshot_ref": _SNAPSHOT_REF,
        "venue_id": "okx",
        "venue_symbol": "ETH-USDT-SWAP",
        "venue_timezone": "UTC",
    }
    base.update(overrides)
    return base


def _source_record(**overrides: object) -> SourceObservationRecordV1:
    payload = _observation_payload(**overrides)
    record = SourceObservationRecordV1(
        input_contract_version=INPUT_CONTRACT_VERSION,
        source_id=str(payload["source_id"]),
        source_trust_level=SourceTrustLevel.TRUSTED.value,
        source_priority=int(payload["source_priority"]),  # type: ignore[arg-type]
        source_snapshot_ref=str(payload["source_snapshot_ref"]),
        source_snapshot_digest=str(payload["source_snapshot_digest"]),
        source_observed_at=str(payload["source_observed_at"]),
        source_effective_at=str(payload["source_effective_at"]),
        venue_id=str(payload["venue_id"]),
        venue_timezone=str(payload["venue_timezone"]),
        market_type=str(payload["market_type"]),
        contract_type=str(payload["contract_type"]),
        base_asset=str(payload["base_asset"]),
        quote_asset=str(payload["quote_asset"]),
        settlement_asset=str(payload["settlement_asset"]),
        observation_kind=str(payload["observation_kind"]),
        observation_digest="0" * 64,
        venue_symbol=str(payload["venue_symbol"]) if payload.get("venue_symbol") else None,
        native_instrument_id=(
            str(payload["native_instrument_id"]) if payload.get("native_instrument_id") else None
        ),
        contract_expiry=str(payload["contract_expiry"]) if payload.get("contract_expiry") else None,
        listing_time=str(payload["listing_time"]) if payload.get("listing_time") else None,
        eligible_from=str(payload["eligible_from"]) if payload.get("eligible_from") else None,
        delisting_time=str(payload["delisting_time"]) if payload.get("delisting_time") else None,
        eligible_until=str(payload["eligible_until"]) if payload.get("eligible_until") else None,
        expiry_time=str(payload["expiry_time"]) if payload.get("expiry_time") else None,
        correction_provenance_ref=(
            str(payload["correction_provenance_ref"])
            if payload.get("correction_provenance_ref")
            else None
        ),
    )
    return dataclasses.replace(record, observation_digest=compute_observation_digest(record))


def _normalize(**overrides: object):
    result = normalize_source_observation_record_v1(_source_record(**overrides))
    assert result.success, result.error_codes
    assert result.observation is not None
    return result.observation


def _assembled_snapshot(*records: SourceObservationRecordV1) -> RegistrySnapshotV1:
    result = assemble_registry_snapshot_v1(
        records,
        generated_at=_GENERATED_AT,
        venue_scope=("okx",),
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
    )
    assert result.success, result.error_codes
    assert result.snapshot is not None
    return result.snapshot


def _manual_snapshot(*intervals: InstrumentLifecycleIntervalV1) -> RegistrySnapshotV1:
    snap = RegistrySnapshotV1(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        registry_snapshot_version=1,
        policy_version=REGISTRY_VERSION,
        source_priority_policy_version="source_priority_policy.v1",
        conflict_resolution_policy_version="conflict_resolution_policy.v1",
        venue_scope=("okx",),
        generated_at=_GENERATED_AT,
        intervals=intervals,
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
        registry_snapshot_digest="0" * 64,
    )
    return attach_snapshot_digest(snap)


def test_write_read_roundtrip_semantically_identical(tmp_path: Path) -> None:
    original = _assembled_snapshot(_source_record())
    write_result = write_registry_snapshot_v1(
        original,
        root_dir=tmp_path,
        relative_path=Path("registry/v1/snapshot.json"),
    )
    assert write_result.success is True
    assert write_result.bytes_written > 0

    read_result = read_registry_snapshot_v1(
        root_dir=tmp_path,
        relative_path=Path("registry/v1/snapshot.json"),
    )
    assert read_result.success is True
    assert read_result.snapshot is not None
    assert read_result.snapshot == original


def test_identical_input_produces_byte_identical_output(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    path_a = tmp_path / "a"
    path_b = tmp_path / "b"
    path_a.mkdir()
    path_b.mkdir()

    write_registry_snapshot_v1(snap, root_dir=path_a, relative_path=Path("snap.json"))
    write_registry_snapshot_v1(snap, root_dir=path_b, relative_path=Path("snap.json"))

    assert (path_a / "snap.json").read_bytes() == (path_b / "snap.json").read_bytes()
    assert registry_snapshot_to_canonical_bytes(snap) == (path_a / "snap.json").read_bytes()


def test_writer_rejects_invalid_snapshot_without_file_mutation(tmp_path: Path) -> None:
    interval = build_interval_from_observation_v1(_normalize())
    assert interval is not None
    snap = _manual_snapshot(interval)
    bad = dataclasses.replace(snap, registry_snapshot_digest="f" * 64)
    target = Path("registry/bad.json")

    result = write_registry_snapshot_v1(bad, root_dir=tmp_path, relative_path=target)
    assert result.success is False
    assert PersistenceErrorCode.VALIDATOR_REJECTED_BEFORE_WRITE.value in result.error_codes
    assert LifecycleRegistryErrorCode.DIGEST_MISMATCH.value in result.error_codes
    assert not (tmp_path / target).exists()
    assert list(tmp_path.glob(".tmp_*")) == []


def test_reader_rejects_manipulated_snapshot(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    target = tmp_path / "registry" / "snap.json"
    write_registry_snapshot_v1(snap, root_dir=tmp_path, relative_path=Path("registry/snap.json"))

    raw = json.loads(target.read_text(encoding="utf-8"))
    raw["intervals"][0]["eligible_from"] = "2024-01-09T00:00:00Z"
    target.write_text(json.dumps(raw), encoding="utf-8")

    result = read_registry_snapshot_v1(root_dir=tmp_path, relative_path=Path("registry/snap.json"))
    assert result.success is False
    assert PersistenceErrorCode.VALIDATOR_REJECTED_AFTER_READ.value in result.error_codes
    assert LifecycleRegistryErrorCode.DIGEST_MISMATCH.value in result.error_codes


def test_reader_rejects_truncated_file(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    rel = Path("registry/snap.json")
    write_registry_snapshot_v1(snap, root_dir=tmp_path, relative_path=rel)
    path = tmp_path / rel
    path.write_bytes(path.read_bytes()[:20])

    result = read_registry_snapshot_v1(root_dir=tmp_path, relative_path=rel)
    assert result.success is False
    assert PersistenceErrorCode.INVALID_JSON.value in result.error_codes


def test_reader_rejects_empty_file(tmp_path: Path) -> None:
    rel = Path("registry/empty.json")
    (tmp_path / "registry").mkdir(parents=True)
    (tmp_path / rel).write_text("", encoding="utf-8")

    result = read_registry_snapshot_v1(root_dir=tmp_path, relative_path=rel)
    assert result.success is False
    assert PersistenceErrorCode.TRUNCATED_FILE.value in result.error_codes


def test_reader_rejects_unknown_schema_version(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    payload = registry_snapshot_to_dict(snap)
    payload["schema_version"] = "v99"
    (tmp_path / "snap.json").write_text(json.dumps(payload), encoding="utf-8")

    result = read_registry_snapshot_v1(root_dir=tmp_path, relative_path=Path("snap.json"))
    assert result.success is False
    assert PersistenceErrorCode.UNKNOWN_SCHEMA_VERSION.value in result.error_codes


def test_reader_rejects_unknown_top_level_field(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    payload = registry_snapshot_to_dict(snap)
    payload["unexpected_field"] = True
    (tmp_path / "snap.json").write_text(json.dumps(payload), encoding="utf-8")

    result = read_registry_snapshot_v1(root_dir=tmp_path, relative_path=Path("snap.json"))
    assert result.success is False
    assert PersistenceErrorCode.UNKNOWN_FIELD.value in result.error_codes


def test_reader_rejects_unknown_interval_field(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    payload = registry_snapshot_to_dict(snap)
    payload["intervals"][0]["extra"] = "x"
    (tmp_path / "snap.json").write_text(json.dumps(payload), encoding="utf-8")

    result = read_registry_snapshot_v1(root_dir=tmp_path, relative_path=Path("snap.json"))
    assert result.success is False
    assert PersistenceErrorCode.UNKNOWN_FIELD.value in result.error_codes


def test_reader_rejects_digest_mismatch(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    payload = registry_snapshot_to_dict(snap)
    payload["registry_snapshot_digest"] = "f" * 64
    (tmp_path / "snap.json").write_text(json.dumps(payload), encoding="utf-8")

    result = read_registry_snapshot_v1(root_dir=tmp_path, relative_path=Path("snap.json"))
    assert result.success is False
    assert LifecycleRegistryErrorCode.DIGEST_MISMATCH.value in result.error_codes


def test_writer_rejects_path_traversal(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    result = write_registry_snapshot_v1(
        snap,
        root_dir=tmp_path,
        relative_path=Path("../escape.json"),
    )
    assert result.success is False
    assert PersistenceErrorCode.PATH_TRAVERSAL_FORBIDDEN.value in result.error_codes


def test_writer_rejects_absolute_path(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    result = write_registry_snapshot_v1(
        snap,
        root_dir=tmp_path,
        relative_path=Path("/etc/passwd"),
    )
    assert result.success is False
    assert PersistenceErrorCode.PATH_OUTSIDE_ROOT.value in result.error_codes


def test_existing_snapshot_immutable_without_overwrite_policy(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    rel = Path("registry/v1.json")
    first = write_registry_snapshot_v1(snap, root_dir=tmp_path, relative_path=rel)
    assert first.success is True
    original_bytes = (tmp_path / rel).read_bytes()

    second = write_registry_snapshot_v1(snap, root_dir=tmp_path, relative_path=rel)
    assert second.success is False
    assert PersistenceErrorCode.TARGET_EXISTS.value in second.error_codes
    assert (tmp_path / rel).read_bytes() == original_bytes


def test_correction_writes_new_version_path(tmp_path: Path) -> None:
    prior = _assembled_snapshot(_source_record())
    revised_result = assemble_registry_snapshot_v1(
        (
            _source_record(),
            _source_record(base_asset="SOL", venue_symbol="SOL-USDT-SWAP"),
        ),
        generated_at="2026-07-03T03:00:00Z",
        venue_scope=("okx",),
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
        registry_snapshot_version=2,
    )
    assert revised_result.success is True
    assert revised_result.snapshot is not None
    revised = revised_result.snapshot

    v1_path = Path("registry/v1.json")
    v2_path = Path("registry/v2.json")
    assert write_registry_snapshot_v1(prior, root_dir=tmp_path, relative_path=v1_path).success
    v1_bytes = (tmp_path / v1_path).read_bytes()
    assert write_registry_snapshot_v1(revised, root_dir=tmp_path, relative_path=v2_path).success

    v1_read = read_registry_snapshot_v1(root_dir=tmp_path, relative_path=v1_path)
    v2_read = read_registry_snapshot_v1(root_dir=tmp_path, relative_path=v2_path)
    assert v1_read.success and v2_read.success
    assert v1_read.snapshot is not None and v2_read.snapshot is not None
    assert v1_read.snapshot.registry_snapshot_version == 1
    assert v2_read.snapshot.registry_snapshot_version == 2
    assert (tmp_path / v1_path).read_bytes() == v1_bytes


def test_atomic_write_leaves_no_partial_target_on_validation_failure(tmp_path: Path) -> None:
    interval = build_interval_from_observation_v1(_normalize())
    assert interval is not None
    snap = _manual_snapshot(interval)
    bad = dataclasses.replace(snap, registry_snapshot_digest="f" * 64)
    rel = Path("registry/partial.json")
    (tmp_path / "registry").mkdir(parents=True)
    sentinel = tmp_path / "registry" / ".sentinel"
    sentinel.write_text("ok", encoding="utf-8")

    result = write_registry_snapshot_v1(bad, root_dir=tmp_path, relative_path=rel)
    assert result.success is False
    assert not (tmp_path / rel).exists()
    assert sentinel.read_text(encoding="utf-8") == "ok"


def test_atomic_replace_no_tmp_leftover(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    rel = Path("registry/snap.json")
    result = write_registry_snapshot_v1(snap, root_dir=tmp_path, relative_path=rel)
    assert result.success is True
    assert list(tmp_path.rglob(".tmp_*")) == []


def test_deterministic_serialization_independent_of_interval_input_order() -> None:
    listing = _source_record()
    sol = _source_record(base_asset="SOL", venue_symbol="SOL-USDT-SWAP")
    digests: set[bytes] = set()
    for batch in itertools.permutations((listing, sol)):
        snap = _assembled_snapshot(*batch)
        digests.add(registry_snapshot_to_canonical_bytes(snap))
    assert len(digests) == 1


def test_reader_result_revalidates_with_slice_b_validator(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    rel = Path("registry/snap.json")
    write_registry_snapshot_v1(snap, root_dir=tmp_path, relative_path=rel)
    read_result = read_registry_snapshot_v1(root_dir=tmp_path, relative_path=rel)
    assert read_result.success is True
    assert read_result.snapshot is not None
    validation = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(
        read_result.snapshot
    )
    assert validation.verdict == ValidationVerdict.ACCEPTED


def test_allow_replace_explicit_overwrite_policy(tmp_path: Path) -> None:
    snap = _assembled_snapshot(_source_record())
    rel = Path("registry/snap.json")
    assert write_registry_snapshot_v1(snap, root_dir=tmp_path, relative_path=rel).success
    first_bytes = (tmp_path / rel).read_bytes()

    assert write_registry_snapshot_v1(
        snap,
        root_dir=tmp_path,
        relative_path=rel,
        overwrite_policy=OverwritePolicy.ALLOW_REPLACE,
    ).success
    second_bytes = (tmp_path / rel).read_bytes()
    assert first_bytes == second_bytes


def test_parse_registry_snapshot_dict_roundtrip() -> None:
    snap = _assembled_snapshot(_source_record())
    payload = registry_snapshot_to_dict(snap)
    parsed, errors = parse_registry_snapshot_dict_v1(payload)
    assert errors == ()
    assert parsed == snap


def test_reader_rejects_current_state_fallback_marker_in_persisted_file(
    tmp_path: Path,
) -> None:
    interval = build_interval_from_observation_v1(_normalize())
    assert interval is not None
    bad = dataclasses.replace(
        interval,
        instrument_id="okx:linear_perpetual:current_state:USDT:USDT:perp",
    )
    bad = dataclasses.replace(bad, record_digest=compute_interval_digest(bad))
    snap = _manual_snapshot(bad)
    payload = registry_snapshot_to_dict(snap)
    (tmp_path / "snap.json").write_text(json.dumps(payload), encoding="utf-8")

    result = read_registry_snapshot_v1(root_dir=tmp_path, relative_path=Path("snap.json"))
    assert result.success is False
    assert LifecycleRegistryErrorCode.UNKNOWN_LIFECYCLE_STATE.value in result.error_codes


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics required")
def test_writer_rejects_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}_outside"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "link.json"
    link.symlink_to(outside / "target.json")
    snap = _assembled_snapshot(_source_record())

    result = write_registry_snapshot_v1(snap, root_dir=tmp_path, relative_path=Path("link.json"))
    assert result.success is False
    assert PersistenceErrorCode.SYMLINK_FORBIDDEN.value in result.error_codes


def test_registry_snapshot_digest_stable_across_to_dict_and_bytes() -> None:
    snap = _assembled_snapshot(_source_record())
    payload = registry_snapshot_to_dict(snap)
    parsed, _ = parse_registry_snapshot_dict_v1(payload)
    assert parsed is not None
    assert parsed.registry_snapshot_digest == snap.registry_snapshot_digest
    assert compute_registry_snapshot_digest(parsed) == snap.registry_snapshot_digest
