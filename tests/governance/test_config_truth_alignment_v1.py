"""CONFIG_TRUTH_ALIGNMENT_V1 — Phase-1 config truth alignment contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.peak_config import PeakConfig, load_config
from src.live.risk_limits import LiveRiskLimits
from src.ops.config_truth_alignment_contract_v1 import (
    CAPABILITY_ID,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PHASE1_MAX_OPEN_POSITIONS,
    ConfigTruthAlignmentError,
    ConsumerClass,
    assert_historical_five_not_productive,
    assert_phase1_config_path_allowed,
    build_config_truth_alignment_report_v1,
    consumer_traces,
    parse_phase1_max_open_positions,
    parse_phase1_safety_flag_false,
    phase1_aligned_live_risk_max_open_positions,
    reload_phase1_effective_config_preserves_digest,
    resolve_phase1_effective_config,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_CONFIG = REPO_ROOT / "config" / "config.toml"
LEGACY_ROOT_CONFIG = REPO_ROOT / "config.toml"
TEST_ONLY_CONFIG = REPO_ROOT / "config" / "config.test.toml"


def test_capability_id_stable() -> None:
    assert CAPABILITY_ID == "CONFIG_TRUTH_ALIGNMENT_V1"


def test_canonical_entrypoint_receives_max_open_positions_one() -> None:
    effective = resolve_phase1_effective_config(config_path=CANONICAL_CONFIG)
    assert effective.max_open_positions == 1
    cfg = load_config(CANONICAL_CONFIG)
    assert phase1_aligned_live_risk_max_open_positions(cfg) == 1
    legacy = LiveRiskLimits.from_config(cfg)
    assert legacy.config.max_open_positions == 1


def test_missing_max_positions_fail_closed() -> None:
    with pytest.raises(ConfigTruthAlignmentError, match="MISSING_MAX_OPEN_POSITIONS"):
        parse_phase1_max_open_positions(None)
    cfg = PeakConfig(raw={"live_risk": {}})
    with pytest.raises(ConfigTruthAlignmentError, match="MISSING_MAX_OPEN_POSITIONS"):
        phase1_aligned_live_risk_max_open_positions(cfg)


def test_invalid_zero_max_positions_fail_closed() -> None:
    with pytest.raises(ConfigTruthAlignmentError, match="lt_one"):
        parse_phase1_max_open_positions(0)


def test_invalid_negative_max_positions_fail_closed() -> None:
    with pytest.raises(ConfigTruthAlignmentError, match="lt_one"):
        parse_phase1_max_open_positions(-1)


def test_value_greater_than_one_fail_closed() -> None:
    with pytest.raises(ConfigTruthAlignmentError, match="phase1_gt_one"):
        parse_phase1_max_open_positions(2)
    with pytest.raises(ConfigTruthAlignmentError, match="phase1_gt_one"):
        parse_phase1_max_open_positions(5)
    with pytest.raises(ConfigTruthAlignmentError, match="phase1_gt_one"):
        parse_phase1_max_open_positions(10)


def test_historical_test_only_value_five_does_not_reach_productive_runtime() -> None:
    cfg = load_config(CANONICAL_CONFIG)
    assert_historical_five_not_productive(cfg)
    with pytest.raises(ConfigTruthAlignmentError, match="TEST_ONLY_CONFIG_BLOCKED"):
        assert_phase1_config_path_allowed(TEST_ONLY_CONFIG)
    with pytest.raises(ConfigTruthAlignmentError, match="LEGACY_PARALLEL_CONFIG_AUTHORITY"):
        assert_phase1_config_path_allowed(LEGACY_ROOT_CONFIG)
    # Even if a PeakConfig object carries 5, Phase-1 adapter rejects it.
    bad = PeakConfig(raw={"live_risk": {"max_open_positions": 5}})
    with pytest.raises(ConfigTruthAlignmentError, match="phase1_gt_one"):
        phase1_aligned_live_risk_max_open_positions(bad)


def test_live_flag_missing_defaults_false() -> None:
    assert parse_phase1_safety_flag_false(None, key="enable_live_trading") is False


def test_live_flag_true_rejected_in_phase1() -> None:
    with pytest.raises(ConfigTruthAlignmentError, match="PHASE1_SAFETY_FLAG_TRUE_REJECTED"):
        parse_phase1_safety_flag_false(True, key="enable_live_trading")
    cfg = PeakConfig(
        raw={
            "live_risk": {"max_open_positions": 1},
            "environment": {"enable_live_trading": True},
        }
    )
    with pytest.raises(ConfigTruthAlignmentError, match="enable_live_trading"):
        resolve_phase1_effective_config(cfg=cfg, config_path=CANONICAL_CONFIG)


@pytest.mark.parametrize(
    "key",
    [
        "orders_authorized",
        "paper_execution_authorized",
        "testnet_authorized",
        "runtime_bridge_live_activated",
        "live_authorized",
    ],
)
def test_authorization_flags_true_rejected(key: str) -> None:
    with pytest.raises(ConfigTruthAlignmentError, match="PHASE1_SAFETY_FLAG_TRUE_REJECTED"):
        parse_phase1_safety_flag_false(True, key=key)


def test_multi_future_authorization_true_rejected() -> None:
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    with pytest.raises(ConfigTruthAlignmentError, match="PHASE1_SAFETY_FLAG_TRUE_REJECTED"):
        parse_phase1_safety_flag_false(True, key="MULTI_FUTURE_RUNTIME_AUTHORIZED")


def test_numeric_max_age_enforcement_true_rejected_and_effective_false() -> None:
    effective = resolve_phase1_effective_config(config_path=CANONICAL_CONFIG)
    assert effective.volatility_numeric_max_age_enforcement is False
    with pytest.raises(ConfigTruthAlignmentError, match="PHASE1_SAFETY_FLAG_TRUE_REJECTED"):
        parse_phase1_safety_flag_false(True, key="volatility_numeric_max_age_enforcement")


def test_conflicting_config_layers_fail_closed() -> None:
    cfg = PeakConfig(
        raw={
            "live_risk": {"max_open_positions": 1},
            "bounded_live": {
                "enabled": True,
                "limits": {"max_open_positions": 3},
            },
            "environment": {"enable_live_trading": False},
        }
    )
    with pytest.raises(ConfigTruthAlignmentError, match="CONFLICTING_CONFIG_LAYERS"):
        resolve_phase1_effective_config(cfg=cfg, config_path=CANONICAL_CONFIG)


def test_environment_override_attempt_guarded() -> None:
    with pytest.raises(ConfigTruthAlignmentError, match="ENVIRONMENT_OVERRIDE_GUARDED"):
        resolve_phase1_effective_config(
            config_path=CANONICAL_CONFIG,
            environ={"PEAK_TRADE_ENABLE_LIVE_TRADING": "true"},
        )


def test_cli_override_attempt_guarded() -> None:
    with pytest.raises(ConfigTruthAlignmentError, match="PHASE1_SAFETY_FLAG_TRUE_REJECTED"):
        resolve_phase1_effective_config(
            config_path=CANONICAL_CONFIG,
            cli_overrides={"orders_authorized": True},
        )
    with pytest.raises(ConfigTruthAlignmentError, match="phase1_gt_one"):
        resolve_phase1_effective_config(
            config_path=CANONICAL_CONFIG,
            cli_overrides={"max_open_positions": 5},
        )


def test_malformed_boolean_fail_closed() -> None:
    with pytest.raises(ConfigTruthAlignmentError, match="MALFORMED_BOOL"):
        parse_phase1_safety_flag_false("maybe", key="enable_live_trading")


def test_unknown_config_key_policy() -> None:
    # Repository policy for this capability: unknown keys allowed by default,
    # but fail-closed when allow_unknown_keys=False.
    resolve_phase1_effective_config(
        config_path=CANONICAL_CONFIG,
        unknown_keys=("totally_unknown_phase1_key",),
        allow_unknown_keys=True,
    )
    with pytest.raises(ConfigTruthAlignmentError, match="UNKNOWN_CONFIG_KEY_FAIL_CLOSED"):
        resolve_phase1_effective_config(
            config_path=CANONICAL_CONFIG,
            unknown_keys=("totally_unknown_phase1_key",),
            allow_unknown_keys=False,
        )


def test_all_canonical_productive_entrypoints_consume_aligned_values() -> None:
    effective = resolve_phase1_effective_config(config_path=CANONICAL_CONFIG)
    assert effective.max_open_positions == PHASE1_MAX_OPEN_POSITIONS
    assert effective.enable_live_trading is False
    assert effective.live_authorized is False
    assert effective.orders_authorized is False
    assert effective.paper_execution_authorized is False
    assert effective.testnet_authorized is False
    assert effective.runtime_bridge_live_activated is False
    assert effective.multi_future_runtime_authorized is False
    assert effective.volatility_numeric_max_age_enforcement is False

    traces = consumer_traces()
    productive = [t for t in traces if t.consumer_class == ConsumerClass.PRODUCTIVE_CANONICAL.value]
    assert len(productive) >= 3
    assert any("wallclock_full_canonical" in t.entrypoint for t in productive)
    assert any("integrated_offline_trading_logic_replay" in t.entrypoint for t in productive)


def test_legacy_productive_consumer_detection() -> None:
    traces = consumer_traces()
    legacy = [t for t in traces if t.consumer_class == ConsumerClass.PRODUCTIVE_LEGACY.value]
    assert legacy
    assert any("risk_limits" in t.entrypoint for t in legacy)


def test_no_permissive_fallback_on_phase1_resolver() -> None:
    with pytest.raises(ConfigTruthAlignmentError):
        parse_phase1_max_open_positions(None)
    with pytest.raises(ConfigTruthAlignmentError):
        parse_phase1_max_open_positions(5)


def test_deterministic_config_digest_and_restart_reload() -> None:
    first, second = reload_phase1_effective_config_preserves_digest(config_path=CANONICAL_CONFIG)
    assert first.digest == second.digest
    assert len(first.digest) == 64
    again = resolve_phase1_effective_config(config_path=CANONICAL_CONFIG)
    assert again.digest == first.digest


def test_report_build_and_inventory_complete() -> None:
    report = build_config_truth_alignment_report_v1(config_path=CANONICAL_CONFIG)
    assert report.capability_id == CAPABILITY_ID
    assert report.core_logic_change is False
    assert report.activation_state == "BOUND_NOT_ACTIVATED"
    keys = {row.config_key for row in report.key_inventory}
    for required in (
        "max_open_positions",
        "enable_live_trading",
        "live_authorized",
        "orders_authorized",
        "paper_execution_authorized",
        "testnet_authorized",
        "runtime_bridge_live_activated",
        "MULTI_FUTURE_RUNTIME_AUTHORIZED",
        "enforcement_enabled",
        "volatility_numeric_max_age_enforcement",
        "require_confirm_token",
    ):
        assert required in keys
    assert report.effective.max_open_positions == 1
    assert "phase1_parser_missing_fail_closed" in report.permissive_fallbacks_removed_or_blocked
