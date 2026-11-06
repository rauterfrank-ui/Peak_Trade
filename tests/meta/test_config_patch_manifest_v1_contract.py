"""Contract tests for ConfigPatch-Manifest v1."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

from scripts.generate_demo_patches_for_promotion import build_demo_patches
from src.meta.learning_loop.config_patch_manifest_v1 import (
    ConfigPatchManifestV1,
    build_empty_config_patch_manifest_v1,
    compute_manifest_integrity,
    deserialize_config_patch_manifest_v1,
    manifest_to_canonical_dict,
    patch_to_mapping,
    serialize_config_patch_manifest_v1,
    validate_config_patch_manifest_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION,
    VERDICT_FUTURES_SCOPE_VIOLATION,
    canonical_futures_scope_ref,
    canonical_trading_logic_immutability_ref,
)
from src.meta.learning_loop.models import ConfigPatch, PatchStatus


FIXED_NOW = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
MANIFEST_ID = "11111111-1111-4111-8111-111111111111"
LINEAGE_ID = "22222222-2222-4222-8222-222222222222"


def _empty_manifest_dict(*, include_bad_integrity: bool = False) -> dict:
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=LINEAGE_ID,
    )
    payload = manifest_to_canonical_dict(manifest, include_integrity=True)
    if include_bad_integrity:
        payload["integrity"] = {"content_sha256": "0" * 64}
    return payload


def test_empty_patch_manifest_is_valid() -> None:
    payload = _empty_manifest_dict()
    valid, phase, errors, verdict = validate_config_patch_manifest_v1(payload)
    assert valid is True
    assert phase.value == "result"
    assert errors == ()
    assert verdict is None


def test_deterministic_json_roundtrip() -> None:
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=LINEAGE_ID,
    )
    first = serialize_config_patch_manifest_v1(manifest)
    second = serialize_config_patch_manifest_v1(manifest)
    assert first == second
    roundtrip = deserialize_config_patch_manifest_v1(json.loads(first))
    assert roundtrip.manifest_id == MANIFEST_ID
    assert roundtrip.patches == []


def test_optional_fields_and_config_patch_compatibility() -> None:
    patch = ConfigPatch(
        id="patch-1",
        target="research.offline.window_days",
        old_value=30,
        new_value=45,
        status=PatchStatus.APPLIED_OFFLINE,
        generated_at=FIXED_NOW,
        reason="offline only",
        source_experiment_id="exp-abc123",
        confidence_score=0.91,
        meta={"operator_hint": "review"},
    )
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=LINEAGE_ID,
    )
    manifest.patches = [patch]
    manifest.metadata = {"proposal_type": "OFFLINE_PROMOTE"}
    manifest.integrity = compute_manifest_integrity(manifest)

    payload = manifest_to_canonical_dict(manifest, include_integrity=True)
    valid, _, errors, _ = validate_config_patch_manifest_v1(payload)
    assert valid is True, errors
    assert payload["patches"][0]["status"] == PatchStatus.APPLIED_OFFLINE.value
    assert patch_to_mapping(patch)["source_experiment_id"] == "exp-abc123"


def test_unknown_schema_version_rejected() -> None:
    payload = _empty_manifest_dict()
    payload["schema_version"] = "9.9"
    valid, phase, errors, _ = validate_config_patch_manifest_v1(payload)
    assert valid is False
    assert phase.value == "schema_version"
    assert "unsupported schema_version" in errors[0]


def test_duplicate_patch_id_rejected() -> None:
    payload = _empty_manifest_dict()
    payload["patches"] = [
        {
            "id": "dup",
            "target": "research.offline.window_days",
            "new_value": 1,
            "status": PatchStatus.APPLIED_OFFLINE.value,
        },
        {
            "id": "dup",
            "target": "research.offline.window_days",
            "new_value": 2,
            "status": PatchStatus.APPLIED_OFFLINE.value,
        },
    ]
    payload["integrity"] = {
        "content_sha256": compute_manifest_integrity(
            deserialize_config_patch_manifest_v1(
                {**payload, "integrity": {"content_sha256": "0" * 64}}
            )
        ).content_sha256
    }
    valid, phase, errors, _ = validate_config_patch_manifest_v1(payload)
    assert valid is False
    assert phase.value == "cardinality"
    assert errors[0] == "duplicate patch id"


def test_missing_lineage_ref_rejected_outside_fixture_mode() -> None:
    payload = _empty_manifest_dict()
    payload.pop("lineage_manifest_ref")
    valid, phase, errors, _ = validate_config_patch_manifest_v1(payload)
    assert valid is False
    assert phase.value == "lineage_references"


def test_invalid_futures_scope_rejected() -> None:
    payload = _empty_manifest_dict()
    payload["source_scope"] = {"scope": "BTC_PERP", "bitcoin_direction_allowed": False}
    valid, phase, _, verdict = validate_config_patch_manifest_v1(payload)
    assert valid is False
    assert phase.value == "futures_scope"
    assert verdict == VERDICT_FUTURES_SCOPE_VIOLATION


def test_integrity_mismatch_rejected() -> None:
    payload = _empty_manifest_dict(include_bad_integrity=True)
    valid, phase, errors, _ = validate_config_patch_manifest_v1(payload)
    assert valid is False
    assert phase.value == "integrity"
    assert "integrity.content_sha256 mismatch" in errors[0]


@pytest.mark.parametrize(
    "target",
    [
        "portfolio.leverage",
        "strategy.trigger_delay",
        "risk.stop_loss",
        "macro.regime_weight",
        "master_v2.config",
        "double_play.slot",
        "signal.threshold",
        "entry.rule",
        "exit.rule",
        "sizing.fraction",
        "leverage.max",
        "stop_loss.pct",
        "take_profit.pct",
        "execution.routing",
        "order.route",
        "risk_limit.max",
        "killswitch.enabled",
        "capital_slot.id",
        "dynamic_scope.mode",
        "state_switch.enabled",
        "runtime.mode",
        "live.arming",
    ],
)
def test_forbidden_trading_logic_targets_rejected(target: str) -> None:
    payload = _empty_manifest_dict()
    payload["patches"] = [
        {
            "id": str(uuid.uuid4()),
            "target": target,
            "new_value": 1,
            "status": PatchStatus.APPLIED_OFFLINE.value,
        }
    ]
    manifest = deserialize_config_patch_manifest_v1(
        {**payload, "integrity": {"content_sha256": "0" * 64}}
    )
    payload["integrity"] = {"content_sha256": compute_manifest_integrity(manifest).content_sha256}
    valid, _, _, verdict = validate_config_patch_manifest_v1(payload)
    assert valid is False
    assert verdict == VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION


def test_demo_patch_targets_remain_fail_closed_regression() -> None:
    demo_patches = build_demo_patches(variant="diverse", base_confidence=0.85)
    for demo_patch in demo_patches:
        payload = _empty_manifest_dict()
        payload["metadata"] = {"fixture_kind": "demo_patches_for_promotion"}
        payload["patches"] = [patch_to_mapping(demo_patch)]
        manifest = deserialize_config_patch_manifest_v1(
            {**payload, "integrity": {"content_sha256": "0" * 64}}
        )
        payload["integrity"] = {
            "content_sha256": compute_manifest_integrity(manifest).content_sha256
        }
        valid, _, _, verdict = validate_config_patch_manifest_v1(payload)
        assert valid is False, demo_patch.target
        assert verdict == VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION


def test_fixture_mode_allows_missing_lineage_with_forbidden_targets_still_rejected() -> None:
    payload = _empty_manifest_dict()
    payload.pop("lineage_manifest_ref")
    payload["metadata"] = {"fixture_kind": "demo_patches_for_promotion"}
    payload["patches"] = [
        {
            "id": "demo_patch_leverage_175",
            "target": "portfolio.leverage",
            "new_value": 1.75,
            "status": PatchStatus.APPLIED_OFFLINE.value,
        }
    ]
    valid, _, _, verdict = validate_config_patch_manifest_v1(payload)
    assert valid is False
    assert verdict == VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION
