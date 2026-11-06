"""Tests for Package D offline learning manifest bridge v1."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.generate_demo_patches_for_promotion import build_demo_patches
from scripts.run_learning_manifest_bridge_v1 import (
    EXIT_BRIDGE_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.meta.learning_loop.config_patch_manifest_v1 import (
    ConfigPatchManifestValidationError,
    load_config_patch_manifest_v1_from_json_path,
    validate_config_patch_manifest_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION,
)
from src.meta.learning_loop.manifest_bridge_v1 import (
    LearningManifestBridgeError,
    build_config_patch_manifest_v1_from_learning_input,
    build_config_patches_from_learning_input,
    load_learning_input_from_path,
    produce_config_patch_manifest_v1_from_paths,
    write_config_patch_manifest_v1_atomic,
)
from src.meta.learning_loop.models import PatchStatus


FIXED_NOW = datetime(2026, 6, 27, 14, 0, 0, tzinfo=timezone.utc)
MANIFEST_ID = "11111111-1111-4111-8111-111111111111"
LINEAGE_ID = "22222222-2222-4222-8222-222222222222"


def _valid_patch_payload() -> dict:
    return {
        "patches": [
            {
                "id": "patch-1",
                "target": "research.offline.window_days",
                "old_value": 30,
                "new_value": 45,
                "status": PatchStatus.APPLIED_OFFLINE.value,
                "reason": "offline bridge test",
                "source_experiment_id": "exp-bridge-1",
            }
        ]
    }


def test_build_manifest_from_explicit_input_uses_normalize_patches() -> None:
    raw = _valid_patch_payload()
    with patch(
        "src.meta.learning_loop.manifest_bridge_v1.normalize_patches",
        wraps=__import__(
            "src.meta.learning_loop.bridge", fromlist=["normalize_patches"]
        ).normalize_patches,
    ) as normalize_mock:
        manifest = build_config_patch_manifest_v1_from_learning_input(
            raw,
            manifest_id=MANIFEST_ID,
            lineage_manifest_ref=LINEAGE_ID,
            generated_at=FIXED_NOW,
        )
        assert normalize_mock.call_count >= 1
        assert normalize_mock.call_args_list[0].args[0] == raw

    assert manifest.manifest_id == MANIFEST_ID
    assert manifest.lineage_manifest_ref == LINEAGE_ID
    assert len(manifest.patches) == 1
    assert manifest.patches[0].target == "research.offline.window_days"


def test_deterministic_json_roundtrip_and_package_a_validation(tmp_path: Path) -> None:
    raw = _valid_patch_payload()
    manifest = build_config_patch_manifest_v1_from_learning_input(
        raw,
        manifest_id=MANIFEST_ID,
        lineage_manifest_ref=LINEAGE_ID,
        generated_at=FIXED_NOW,
    )
    out = tmp_path / "manifest.json"
    write_config_patch_manifest_v1_atomic(manifest, out)
    loaded = load_config_patch_manifest_v1_from_json_path(out)
    assert loaded.manifest_id == MANIFEST_ID
    payload = json.loads(out.read_text(encoding="utf-8"))
    valid, phase, errors, _ = validate_config_patch_manifest_v1(payload)
    assert valid is True, (phase, errors)


def test_empty_input_produces_valid_patch_empty_manifest() -> None:
    manifest = build_config_patch_manifest_v1_from_learning_input(
        {"patches": []},
        manifest_id=MANIFEST_ID,
        lineage_manifest_ref=LINEAGE_ID,
        generated_at=FIXED_NOW,
    )
    assert manifest.patches == []
    payload = json.loads(
        __import__(
            "src.meta.learning_loop.config_patch_manifest_v1",
            fromlist=["serialize_config_patch_manifest_v1"],
        ).serialize_config_patch_manifest_v1(manifest)
    )
    valid, _, errors, _ = validate_config_patch_manifest_v1(payload)
    assert valid is True, errors


def test_lineage_manifest_ref_preserved_unchanged() -> None:
    manifest = build_config_patch_manifest_v1_from_learning_input(
        _valid_patch_payload(),
        manifest_id=MANIFEST_ID,
        lineage_manifest_ref=LINEAGE_ID,
        generated_at=FIXED_NOW,
    )
    assert manifest.lineage_manifest_ref == LINEAGE_ID


def test_cli_produces_validated_manifest_file(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    input_path.write_text(json.dumps(_valid_patch_payload()) + "\n", encoding="utf-8")

    rc = main(
        [
            "--input-path",
            str(input_path),
            "--output-path",
            str(output_path),
            "--manifest-id",
            MANIFEST_ID,
            "--lineage-manifest-ref",
            LINEAGE_ID,
            "--generated-at",
            FIXED_NOW.isoformat(),
        ]
    )
    assert rc == EXIT_OK
    loaded = load_config_patch_manifest_v1_from_json_path(output_path)
    assert loaded.manifest_id == MANIFEST_ID
    assert loaded.lineage_manifest_ref == LINEAGE_ID


def test_jsonl_input_supported(tmp_path: Path) -> None:
    input_path = tmp_path / "input.jsonl"
    patch = _valid_patch_payload()["patches"][0]
    input_path.write_text(json.dumps(patch) + "\n", encoding="utf-8")
    raw = load_learning_input_from_path(input_path)
    patches = build_config_patches_from_learning_input(raw)
    assert len(patches) == 1


def test_invalid_json_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(LearningManifestBridgeError, match="invalid JSON"):
        load_learning_input_from_path(bad)


def test_missing_patch_id_rejected() -> None:
    raw = {
        "patches": [
            {
                "target": "research.offline.window_days",
                "new_value": 45,
                "status": PatchStatus.APPLIED_OFFLINE.value,
            }
        ]
    }
    with pytest.raises(LearningManifestBridgeError, match="patch id is required"):
        build_config_patches_from_learning_input(raw)


def test_missing_patch_status_rejected() -> None:
    raw = {
        "patches": [
            {
                "id": "patch-1",
                "target": "research.offline.window_days",
                "new_value": 45,
            }
        ]
    }
    with pytest.raises(LearningManifestBridgeError, match="patch status is required"):
        build_config_patches_from_learning_input(raw)


def test_duplicate_patch_id_rejected() -> None:
    raw = {
        "patches": [
            {
                "id": "dup",
                "target": "research.offline.window_days",
                "new_value": 45,
                "status": PatchStatus.APPLIED_OFFLINE.value,
            },
            {
                "id": "dup",
                "target": "research.offline.other_field",
                "new_value": 1,
                "status": PatchStatus.APPLIED_OFFLINE.value,
            },
        ]
    }
    with pytest.raises(LearningManifestBridgeError, match="duplicate patch id"):
        build_config_patches_from_learning_input(raw)


@pytest.mark.parametrize(
    "target",
    [
        "master_v2.config",
        "double_play.lane",
        "strategy.trigger_delay",
        "portfolio.leverage",
        "risk.stop_loss",
        "execution.routing.mode",
        "killswitch.enabled",
    ],
)
def test_forbidden_trading_logic_targets_rejected(target: str) -> None:
    raw = {
        "patches": [
            {
                "id": "patch-forbidden",
                "target": target,
                "new_value": 1,
                "status": PatchStatus.APPLIED_OFFLINE.value,
            }
        ]
    }
    with pytest.raises(ConfigPatchManifestValidationError) as exc:
        build_config_patch_manifest_v1_from_learning_input(
            raw,
            manifest_id=MANIFEST_ID,
            lineage_manifest_ref=LINEAGE_ID,
            generated_at=FIXED_NOW,
        )
    assert exc.value.verdict == VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION


def test_demo_patches_remain_fail_closed_regression() -> None:
    from src.meta.learning_loop.config_patch_manifest_v1 import patch_to_mapping

    demo_patches = build_demo_patches(variant="diverse", base_confidence=0.85)
    raw = {"patches": [patch_to_mapping(demo_patches[0])]}
    with pytest.raises(ConfigPatchManifestValidationError) as exc:
        build_config_patch_manifest_v1_from_learning_input(
            raw,
            manifest_id=MANIFEST_ID,
            lineage_manifest_ref=LINEAGE_ID,
            generated_at=FIXED_NOW,
        )
    assert exc.value.verdict == VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION


def test_invalid_lineage_reference_rejected() -> None:
    with pytest.raises(LearningManifestBridgeError, match="lineage_manifest_ref must be a UUID"):
        build_config_patch_manifest_v1_from_learning_input(
            _valid_patch_payload(),
            manifest_id=MANIFEST_ID,
            lineage_manifest_ref="not-a-uuid",
            generated_at=FIXED_NOW,
        )


def test_invalid_manifest_id_rejected() -> None:
    with pytest.raises(LearningManifestBridgeError, match="manifest_id must be a UUID"):
        build_config_patch_manifest_v1_from_learning_input(
            _valid_patch_payload(),
            manifest_id="bad-id",
            lineage_manifest_ref=LINEAGE_ID,
            generated_at=FIXED_NOW,
        )


def test_no_partial_output_on_validation_failure(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    input_path.write_text(
        json.dumps(
            {
                "patches": [
                    {
                        "id": "patch-1",
                        "target": "strategy.trigger_delay",
                        "new_value": 1,
                        "status": PatchStatus.APPLIED_OFFLINE.value,
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigPatchManifestValidationError):
        produce_config_patch_manifest_v1_from_paths(
            input_path=input_path,
            output_path=output_path,
            manifest_id=MANIFEST_ID,
            lineage_manifest_ref=LINEAGE_ID,
            generated_at=FIXED_NOW,
        )
    assert not output_path.exists()


def test_cli_missing_input_path_is_usage_error(tmp_path: Path) -> None:
    rc = main(
        [
            "--input-path",
            str(tmp_path / "missing.json"),
            "--output-path",
            str(tmp_path / "out.json"),
            "--manifest-id",
            MANIFEST_ID,
            "--lineage-manifest-ref",
            LINEAGE_ID,
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_unknown_patch_status_rejected() -> None:
    raw = {
        "patches": [
            {
                "id": "patch-1",
                "target": "research.offline.window_days",
                "new_value": 45,
                "status": "NOT_A_STATUS",
            }
        ]
    }
    with pytest.raises(LearningManifestBridgeError, match="unknown PatchStatus"):
        build_config_patches_from_learning_input(raw)


def test_emit_learning_snippet_optional_adapter_only(tmp_path: Path) -> None:
    """emit_learning_snippet is optional; bridge reads explicit files directly."""
    from src.meta.learning_loop.emitter import emit_learning_snippet

    snippet_path = tmp_path / "snippet.json"
    emit_learning_snippet(_valid_patch_payload(), out_path=snippet_path)
    manifest = produce_config_patch_manifest_v1_from_paths(
        input_path=snippet_path,
        output_path=tmp_path / "manifest.json",
        manifest_id=MANIFEST_ID,
        lineage_manifest_ref=LINEAGE_ID,
        generated_at=FIXED_NOW,
    )
    assert manifest.patches[0].id == "patch-1"


def test_manifest_ids_must_be_unique_per_call() -> None:
    manifest = build_config_patch_manifest_v1_from_learning_input(
        _valid_patch_payload(),
        manifest_id=str(uuid.uuid4()),
        lineage_manifest_ref=str(uuid.uuid4()),
        generated_at=FIXED_NOW,
    )
    assert manifest.manifest_id != manifest.lineage_manifest_ref
