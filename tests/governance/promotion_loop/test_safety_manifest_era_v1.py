"""Dedicated safety characterization tests for manifest-era offline promotion (GAP-007)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.governance.promotion_loop import filter_candidates_for_live
from src.governance.promotion_loop.models import DecisionStatus, PromotionCandidate
from src.governance.promotion_loop.policy import AutoApplyBounds
from src.governance.promotion_loop.safety import (
    SafetyConfig,
    apply_safety_filters,
    check_blacklist,
    check_bounded_auto_guardrails,
    check_global_promotion_lock,
)
from src.meta.learning_loop.config_patch_manifest_v1 import (
    build_empty_config_patch_manifest_v1,
    compute_manifest_integrity,
    load_promotion_input_from_manifest_path,
    manifest_to_canonical_dict,
    serialize_config_patch_manifest_v1,
    validate_config_patch_manifest_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION,
    VERDICT_TARGET_NOT_ALLOWED,
    canonical_futures_scope_ref,
    canonical_trading_logic_immutability_ref,
)
from src.meta.learning_loop.models import ConfigPatch, PatchStatus


FIXED_NOW = datetime(2026, 6, 27, 15, 30, 0, tzinfo=timezone.utc)
MANIFEST_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
LINEAGE_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"


def _candidate(
    *,
    target: str = "research.offline.window_days",
    new_value: object = 45,
    eligible: bool = True,
    confidence: float | None = 0.9,
    tags: list[str] | None = None,
) -> PromotionCandidate:
    patch = ConfigPatch(
        id="patch-safety-1",
        target=target,
        old_value=30,
        new_value=new_value,
        status=PatchStatus.APPLIED_OFFLINE,
        confidence_score=confidence,
    )
    return PromotionCandidate(
        patch=patch,
        eligible_for_live=eligible,
        tags=tags or ["research"],
    )


def test_filter_rejects_candidates_not_eligible_for_live() -> None:
    candidate = _candidate(eligible=False)
    decisions = filter_candidates_for_live([candidate], safety_config=None, mode="manual_only")
    assert len(decisions) == 1
    assert decisions[0].status is DecisionStatus.REJECTED_BY_POLICY


def test_blacklist_target_adds_p0_flag() -> None:
    config = SafetyConfig(blacklist_targets=["live.api_keys"])
    candidate = _candidate(target="live.api_keys.binance")
    violations = check_blacklist(candidate, config)
    assert violations
    apply_safety_filters(candidate, config, mode="manual_only")
    assert any(flag.startswith("P0_BLACKLIST") for flag in candidate.safety_flags)


def test_bounded_auto_guardrails_only_apply_in_bounded_auto_mode() -> None:
    config = SafetyConfig(global_promotion_lock=True, min_confidence_for_auto_apply=0.95)
    candidate = _candidate(confidence=0.5)
    manual_violations = check_bounded_auto_guardrails(candidate, config, mode="manual_only")
    bounded_violations = check_bounded_auto_guardrails(candidate, config, mode="bounded_auto")
    assert manual_violations == []
    assert bounded_violations


def test_global_promotion_lock_warning_is_non_blocking_for_manual_only() -> None:
    config = SafetyConfig(global_promotion_lock=True)
    warning = check_global_promotion_lock(config)
    assert warning is not None
    candidate = _candidate(eligible=True)
    decisions = filter_candidates_for_live([candidate], safety_config=config, mode="manual_only")
    assert decisions[0].status is DecisionStatus.ACCEPTED_FOR_PROPOSAL


def test_bounds_violation_characterization() -> None:
    config = SafetyConfig(
        bounds={
            "research": AutoApplyBounds(min_value=10.0, max_value=40.0, max_step=5.0),
        }
    )
    candidate = _candidate(new_value=50.0, tags=["research"])
    apply_safety_filters(candidate, config, mode="bounded_auto")
    assert any(flag.startswith("P0_BOUNDS") for flag in candidate.safety_flags)


@pytest.mark.parametrize(
    "target",
    [
        "master_v2.config",
        "double_play.slot",
        "strategy.selection.mode",
        "signal.generation.threshold",
        "entry.logic.window",
        "exit.logic.window",
        "sizing.position.max",
        "portfolio.leverage",
        "stop_loss.default",
        "take_profit.default",
        "execution.routing.default",
        "orders.routing.primary",
        "risk.limits.max_drawdown",
        "killswitch.enabled",
        "live.arming.enabled",
    ],
)
def test_forbidden_targets_fail_manifest_validation(target: str) -> None:
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=LINEAGE_ID,
    )
    manifest.patches = [
        ConfigPatch(
            id="patch-negative",
            target=target,
            old_value=0,
            new_value=1,
            status=PatchStatus.APPLIED_OFFLINE,
        )
    ]
    manifest.integrity = compute_manifest_integrity(manifest)
    payload = manifest_to_canonical_dict(manifest, include_integrity=True)
    valid, _, errors, verdict = validate_config_patch_manifest_v1(payload)
    assert valid is False, (target, errors, verdict)
    assert verdict in {
        VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION,
        VERDICT_TARGET_NOT_ALLOWED,
    }


def test_btc_and_spot_patch_targets_not_individually_blocked_at_target_policy() -> None:
    """Characterization: BTC/spot prohibition is enforced via source_scope, not patch target."""
    for target in (
        "btc.futures.direction",
        "xbt.spot.enabled",
        "bitcoin.direction.allowed",
        "spot.market.enabled",
    ):
        manifest = build_empty_config_patch_manifest_v1(
            manifest_id=MANIFEST_ID,
            generated_at=FIXED_NOW,
            lineage_manifest_ref=LINEAGE_ID,
        )
        manifest.patches = [
            ConfigPatch(
                id=f"patch-{target}",
                target=target,
                old_value=False,
                new_value=True,
                status=PatchStatus.APPLIED_OFFLINE,
            )
        ]
        manifest.integrity = compute_manifest_integrity(manifest)
        payload = manifest_to_canonical_dict(manifest, include_integrity=True)
        valid, _, _, _ = validate_config_patch_manifest_v1(payload)
        assert valid is True, target


def test_non_forbidden_unknown_target_currently_allowed_by_contract() -> None:
    """Characterization: only forbidden-prefix targets are fail-closed today."""
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=LINEAGE_ID,
    )
    manifest.patches = [
        ConfigPatch(
            id="patch-unknown-allowed",
            target="experimental.config.flag",
            old_value=False,
            new_value=True,
            status=PatchStatus.APPLIED_OFFLINE,
        )
    ]
    manifest.integrity = compute_manifest_integrity(manifest)
    payload = manifest_to_canonical_dict(manifest, include_integrity=True)
    valid, _, errors, verdict = validate_config_patch_manifest_v1(payload)
    assert valid is True, (errors, verdict)


def test_invalid_manifest_rejected_by_loader(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(Exception):
        load_promotion_input_from_manifest_path(bad_path)


def test_invalid_lineage_uuid_rejected_at_manifest_build() -> None:
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref="not-a-uuid",
    )
    manifest.integrity = compute_manifest_integrity(manifest)
    payload = manifest_to_canonical_dict(manifest, include_integrity=True)
    valid, _, errors, _ = validate_config_patch_manifest_v1(payload)
    assert valid is False
    assert errors


def test_learning_override_toml_is_not_valid_promotion_manifest(tmp_path: Path) -> None:
    toml_path = tmp_path / "learning.override.toml"
    toml_path.write_text("[auto]\nflag = true\n", encoding="utf-8")
    with pytest.raises(Exception):
        load_promotion_input_from_manifest_path(toml_path)


def test_btc_scope_in_source_scope_rejected() -> None:
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=LINEAGE_ID,
    )
    bad_scope = dict(canonical_futures_scope_ref())
    bad_scope["scope"] = "BTC_FUTURES"
    manifest.source_scope = bad_scope
    manifest.trading_logic_immutability_ref = canonical_trading_logic_immutability_ref()
    manifest.integrity = compute_manifest_integrity(manifest)
    payload = manifest_to_canonical_dict(manifest, include_integrity=True)
    valid, _, _, verdict = validate_config_patch_manifest_v1(payload)
    assert valid is False
    assert verdict is not None


def test_patch_empty_manifest_loads_with_zero_patches(tmp_path: Path) -> None:
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=LINEAGE_ID,
    )
    manifest.integrity = compute_manifest_integrity(manifest)
    path = tmp_path / "empty.json"
    path.write_text(serialize_config_patch_manifest_v1(manifest), encoding="utf-8")
    loaded = load_promotion_input_from_manifest_path(path)
    assert list(loaded.patches) == []
