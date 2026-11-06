"""Tests for ConfigPatch-Manifest v1 promotion input file loader (Package B)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.meta.learning_loop.config_patch_manifest_v1 import (
    ConfigPatchManifestError,
    ConfigPatchManifestValidationError,
    build_empty_config_patch_manifest_v1,
    compute_manifest_integrity,
    deserialize_config_patch_manifest_v1,
    load_config_patch_manifest_v1_from_json_path,
    load_config_patches_for_promotion_from_manifest_path,
    manifest_to_canonical_dict,
    patch_to_mapping,
    serialize_config_patch_manifest_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION,
    VERDICT_FUTURES_SCOPE_VIOLATION,
)
from src.meta.learning_loop.models import ConfigPatch, PatchStatus


FIXED_NOW = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
MANIFEST_ID = "11111111-1111-4111-8111-111111111111"
LINEAGE_ID = "22222222-2222-4222-8222-222222222222"


def _build_manifest(*, patches: list[ConfigPatch] | None = None) -> object:
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=LINEAGE_ID,
    )
    if patches is not None:
        manifest.patches = patches
    manifest.integrity = compute_manifest_integrity(manifest)
    return manifest


def _write_manifest(path: Path, *, patches: list[ConfigPatch] | None = None) -> None:
    manifest = _build_manifest(patches=patches)
    path.write_text(serialize_config_patch_manifest_v1(manifest), encoding="utf-8")


def _allowed_patch() -> ConfigPatch:
    return ConfigPatch(
        id="patch-research-window",
        target="research.offline.window_days",
        old_value=30,
        new_value=45,
        status=PatchStatus.APPLIED_OFFLINE,
        generated_at=FIXED_NOW,
        confidence_score=0.91,
    )


def test_loader_reads_valid_manifest_with_allowed_patch(tmp_path: Path) -> None:
    manifest_path = tmp_path / "promotion_input.json"
    _write_manifest(manifest_path, patches=[_allowed_patch()])

    patches = load_config_patches_for_promotion_from_manifest_path(manifest_path)

    assert len(patches) == 1
    assert patches[0].target == "research.offline.window_days"
    assert patches[0].status is PatchStatus.APPLIED_OFFLINE


def test_loader_supports_patch_empty_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "empty.json"
    _write_manifest(manifest_path, patches=[])

    patches = load_config_patches_for_promotion_from_manifest_path(manifest_path)

    assert patches == []


def test_loader_returns_deterministic_config_patch_objects(tmp_path: Path) -> None:
    manifest_path = tmp_path / "deterministic.json"
    _write_manifest(manifest_path, patches=[_allowed_patch()])

    first = load_config_patches_for_promotion_from_manifest_path(manifest_path)
    second = load_config_patches_for_promotion_from_manifest_path(manifest_path)

    assert first[0].id == second[0].id
    assert first[0].target == second[0].target
    assert first[0].status == second[0].status


def test_loader_returns_full_manifest_object(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, patches=[_allowed_patch()])

    manifest = load_config_patch_manifest_v1_from_json_path(manifest_path)

    assert manifest.manifest_id == MANIFEST_ID
    assert manifest.lineage_manifest_ref == LINEAGE_ID
    assert len(manifest.patches) == 1


def test_loader_missing_file_fail_closed(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    with pytest.raises(ConfigPatchManifestError, match="manifest file not found"):
        load_config_patches_for_promotion_from_manifest_path(missing)


def test_loader_invalid_json_fail_closed(tmp_path: Path) -> None:
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ConfigPatchManifestError, match="invalid JSON"):
        load_config_patches_for_promotion_from_manifest_path(bad_json)


def test_loader_rejects_raw_patch_list_as_canonical_input(tmp_path: Path) -> None:
    raw_list = tmp_path / "raw_list.json"
    raw_list.write_text(
        json.dumps([patch_to_mapping(_allowed_patch())]),
        encoding="utf-8",
    )
    with pytest.raises(ConfigPatchManifestError, match="JSON object"):
        load_config_patches_for_promotion_from_manifest_path(raw_list)


def test_loader_rejects_toml_fail_closed(tmp_path: Path) -> None:
    toml_path = tmp_path / "legacy.toml"
    toml_path.write_text("[patch]\ntarget = 'research.offline.window_days'\n", encoding="utf-8")
    with pytest.raises(ConfigPatchManifestError, match="invalid JSON"):
        load_config_patches_for_promotion_from_manifest_path(toml_path)


def test_loader_rejects_unknown_schema_version(tmp_path: Path) -> None:
    manifest_path = tmp_path / "bad_schema.json"
    manifest = _build_manifest(patches=[_allowed_patch()])
    payload = json.loads(serialize_config_patch_manifest_v1(manifest))
    payload["schema_version"] = "9.9"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigPatchManifestValidationError) as exc_info:
        load_config_patches_for_promotion_from_manifest_path(manifest_path)
    assert exc_info.value.phase.value == "schema_version"


def test_loader_rejects_duplicate_patch_ids(tmp_path: Path) -> None:
    manifest_path = tmp_path / "dup.json"
    manifest = _build_manifest(
        patches=[
            _allowed_patch(),
            ConfigPatch(
                id="patch-research-window",
                target="research.offline.window_days",
                old_value=20,
                new_value=25,
                status=PatchStatus.APPLIED_OFFLINE,
            ),
        ]
    )
    manifest_path.write_text(serialize_config_patch_manifest_v1(manifest), encoding="utf-8")

    with pytest.raises(ConfigPatchManifestValidationError) as exc_info:
        load_config_patches_for_promotion_from_manifest_path(manifest_path)
    assert exc_info.value.phase.value == "cardinality"


def test_loader_rejects_unknown_patch_status(tmp_path: Path) -> None:
    manifest_path = tmp_path / "bad_status.json"
    manifest = _build_manifest(patches=[_allowed_patch()])
    payload = json.loads(serialize_config_patch_manifest_v1(manifest))
    payload["patches"][0]["status"] = "UNKNOWN_STATUS"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigPatchManifestValidationError) as exc_info:
        load_config_patches_for_promotion_from_manifest_path(manifest_path)
    assert exc_info.value.phase.value == "schema"


@pytest.mark.parametrize(
    "target",
    [
        "portfolio.leverage",
        "strategy.trigger_delay",
        "master_v2.config",
        "double_play.slot",
        "signal.threshold",
        "sizing.fraction",
        "execution.routing",
        "risk.stop_loss",
        "killswitch.enabled",
    ],
)
def test_loader_rejects_forbidden_targets(tmp_path: Path, target: str) -> None:
    manifest_path = tmp_path / f"forbidden_{uuid.uuid4().hex}.json"
    patch = ConfigPatch(
        id=str(uuid.uuid4()),
        target=target,
        old_value=None,
        new_value=1,
        status=PatchStatus.APPLIED_OFFLINE,
    )
    manifest = _build_manifest(patches=[patch])
    manifest_path.write_text(serialize_config_patch_manifest_v1(manifest), encoding="utf-8")

    with pytest.raises(ConfigPatchManifestValidationError) as exc_info:
        load_config_patches_for_promotion_from_manifest_path(manifest_path)
    assert exc_info.value.verdict in {
        VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION,
        "TARGET_NOT_ALLOWED",
    }


def test_loader_rejects_empty_target_fail_closed(tmp_path: Path) -> None:
    manifest_path = tmp_path / "empty_target.json"
    patch = ConfigPatch(
        id=str(uuid.uuid4()),
        target="",
        old_value=None,
        new_value=1,
        status=PatchStatus.APPLIED_OFFLINE,
    )
    manifest = _build_manifest(patches=[patch])
    manifest_path.write_text(serialize_config_patch_manifest_v1(manifest), encoding="utf-8")

    with pytest.raises(ConfigPatchManifestValidationError) as exc_info:
        load_config_patches_for_promotion_from_manifest_path(manifest_path)
    assert exc_info.value.phase.value == "target_policy"

    manifest_path = tmp_path / "btc_scope.json"
    manifest = _build_manifest(patches=[_allowed_patch()])
    payload = json.loads(serialize_config_patch_manifest_v1(manifest))
    payload["source_scope"] = {
        "scope": "BTC_PERP",
        "bitcoin_direction_allowed": False,
        "autonomous_live_promotion": False,
        "autonomous_order_authority": False,
    }
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigPatchManifestValidationError) as exc_info:
        load_config_patches_for_promotion_from_manifest_path(manifest_path)
    assert exc_info.value.verdict == VERDICT_FUTURES_SCOPE_VIOLATION


def test_loader_rejects_invalid_lineage_reference(tmp_path: Path) -> None:
    manifest_path = tmp_path / "bad_lineage.json"
    manifest = _build_manifest(patches=[_allowed_patch()])
    payload = json.loads(serialize_config_patch_manifest_v1(manifest))
    payload["lineage_manifest_ref"] = "not-a-uuid"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigPatchManifestValidationError) as exc_info:
        load_config_patches_for_promotion_from_manifest_path(manifest_path)
    assert exc_info.value.phase.value == "lineage_references"


def test_loader_rejects_integrity_mismatch(tmp_path: Path) -> None:
    manifest_path = tmp_path / "bad_integrity.json"
    manifest = _build_manifest(patches=[_allowed_patch()])
    payload = manifest_to_canonical_dict(manifest, include_integrity=True)
    payload["integrity"] = {"content_sha256": "0" * 64}
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigPatchManifestValidationError) as exc_info:
        load_config_patches_for_promotion_from_manifest_path(manifest_path)
    assert exc_info.value.phase.value == "integrity"


def test_loader_rejects_missing_required_top_level_field(tmp_path: Path) -> None:
    manifest_path = tmp_path / "missing_field.json"
    manifest = _build_manifest(patches=[_allowed_patch()])
    payload = json.loads(serialize_config_patch_manifest_v1(manifest))
    payload.pop("integrity")
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigPatchManifestValidationError) as exc_info:
        load_config_patches_for_promotion_from_manifest_path(manifest_path)
    assert exc_info.value.phase.value == "schema"
