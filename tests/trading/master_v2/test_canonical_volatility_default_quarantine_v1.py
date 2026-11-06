"""Tests for MASTER_V2_CANONICAL_VOLATILITY_DEFAULT_QUARANTINE_V1 (C2)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from trading.master_v2.canonical_volatility_default_quarantine_v1 import (
    CAPABILITY_ID,
    LEGACY_DYNAMIC_SCOPE_RULES_CONSTRUCTOR_DEFAULT_VALUE,
    LEGACY_HISTORICAL_BIND_DEFAULT_VALUE,
    LEGACY_REPLAY_RULES_DEFAULT_VALUE,
    LEGACY_STRATEGY_FLOOR_VALUE,
    PACKAGE_MARKER,
    VolatilityQuarantineDispositionV1,
    admit_positive_volatility_without_strategy_floor_v1,
    assert_architecture_guards_v1,
    assert_capability_non_goals_v1,
    quarantine_explicit_replay_default_volatility_v1,
    quarantine_explicit_test_fixture_volatility_v1,
    quarantine_historical_bar_volatility_v1,
    quarantine_legacy_volatility_input_v1,
    quarantine_research_fleet_join_volatility_v1,
    quarantine_result_to_evidence_provenance_v1,
    reject_strategy_authority_volatility_floor_v1,
    require_admitted_legacy_volatility_float_v1,
    CanonicalVolatilityQuarantineError,
    CanonicalVolatilityQuarantineErrorCode,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    build_canonical_volatility_estimate_v1,
)
from trading.master_v2.double_play_state import DynamicScopeRules
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    _DEFAULT_SCOPE_RULES,
    _REPLAY_DEFAULT_VOL_QUARANTINE,
    _rules_for_cycle_v1,
)
from trading.master_v2.canonical_scope_initialization_v1 import CanonicalScopeSnapshotV1
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    _DEFAULT_RULES,
    _SCENARIO_REPLAY_DEFAULT_VOL_QUARANTINE,
)

ROOT = Path(__file__).resolve().parents[3]
AS_OF = datetime(2026, 6, 1, 1, 0, tzinfo=timezone.utc)


def _typed(**overrides: object):
    base: dict[str, object] = {
        "value": 0.004321,
        "observation_count": 60,
        "as_of_event_time": AS_OF,
        "fallback_used": False,
    }
    base.update(overrides)
    return build_canonical_volatility_estimate_v1(**base)  # type: ignore[arg-type]


def _snapshot(*, volatility_estimate: float) -> CanonicalScopeSnapshotV1:
    return CanonicalScopeSnapshotV1(
        scope_id="scope-q",
        instrument_id="inst-eth-usdt-perp",
        initialized_at_trading_epoch=1,
        source_market_context_id="ctx",
        source_input_digest="a" * 64,
        lifecycle_state=__import__(
            "trading.master_v2.canonical_scope_initialization_v1",
            fromlist=["CanonicalScopeLifecycleState"],
        ).CanonicalScopeLifecycleState.SCOPE_VALID,
        reference_price=100.0,
        volatility_estimate=volatility_estimate,
        initial_volatility_distance=volatility_estimate * 100.0,
        scope_band=max(volatility_estimate * 100.0, 1.0),
        neutral_upper_boundary=100.0 + max(volatility_estimate * 100.0, 1.0),
        neutral_lower_boundary=100.0 - max(volatility_estimate * 100.0, 1.0),
        trailing_anchor=100.0,
        min_scope_band=1.0,
        max_scope_band=50.0,
        policy_version="v1",
        semantic_digest="b" * 64,
        reason_codes=(),
    )


# --- Historical 0.2 ---


def test_historical_missing_column_rejected() -> None:
    with pytest.raises(CanonicalVolatilityQuarantineError) as exc:
        quarantine_historical_bar_volatility_v1(
            bar_has_volatility_estimate=False,
            raw_value=None,
        )
    assert exc.value.code is CanonicalVolatilityQuarantineErrorCode.MISSING_INPUT


def test_historical_explicit_0_2_quarantined_and_visible() -> None:
    result = quarantine_historical_bar_volatility_v1(
        bar_has_volatility_estimate=True,
        raw_value=LEGACY_HISTORICAL_BIND_DEFAULT_VALUE,
    )
    assert result.disposition is VolatilityQuarantineDispositionV1.EXPLICIT_LEGACY_QUARANTINED
    assert result.legacy_value == pytest.approx(0.2)
    assert result.canonical_estimate_present is False
    assert result.quarantine_digest
    evidence = quarantine_result_to_evidence_provenance_v1(result)
    assert evidence.legacy_value == pytest.approx(0.2)
    assert evidence.disposition == "EXPLICIT_LEGACY_QUARANTINED"


def test_historical_typed_uses_c1() -> None:
    estimate = _typed(value=0.2)
    result = quarantine_historical_bar_volatility_v1(
        bar_has_volatility_estimate=True,
        raw_value=0.2,
        typed_estimate=estimate,
    )
    assert result.disposition is VolatilityQuarantineDispositionV1.TYPED_BOUND
    assert result.typed_binding_present is True
    assert result.canonical_estimate_present is True
    assert result.legacy_value == pytest.approx(0.2)


def test_historical_typed_legacy_conflict_rejected() -> None:
    estimate = _typed(value=0.2)
    with pytest.raises(CanonicalVolatilityQuarantineError) as exc:
        quarantine_historical_bar_volatility_v1(
            bar_has_volatility_estimate=True,
            raw_value=0.25,
            typed_estimate=estimate,
        )
    assert exc.value.code is CanonicalVolatilityQuarantineErrorCode.TYPED_LEGACY_MISMATCH


def test_no_silent_0_2_in_historical_bind_source() -> None:
    wiring = (ROOT / "src/backtest/mv2_research_wiring_v1.py").read_text(encoding="utf-8")
    assert 'bar.get("volatility_estimate", 0.2)' not in wiring


def test_bind_historical_missing_raises() -> None:
    from src.backtest.mv2_research_wiring_v1 import (
        bind_historical_bar_to_canonical_market_context_v1,
    )

    idx = pd.Timestamp("2026-06-01T00:00:00Z")
    bar = pd.Series(
        {
            "mark_price": 100.0,
            "index_price": 100.0,
            "best_bid": 99.9,
            "best_ask": 100.1,
            "is_final": True,
        },
        name=idx,
    )
    with pytest.raises(CanonicalVolatilityQuarantineError):
        bind_historical_bar_to_canonical_market_context_v1(
            bar=bar,
            instrument_id="inst-eth-usdt-perp",
            trading_epoch=1,
        )


def test_bind_historical_explicit_0_2_admitted() -> None:
    from src.backtest.mv2_research_wiring_v1 import (
        bind_historical_bar_to_canonical_market_context_v1,
    )

    idx = pd.Timestamp("2026-06-01T00:00:00Z")
    bar = pd.Series(
        {
            "mark_price": 100.0,
            "index_price": 100.0,
            "best_bid": 99.9,
            "best_ask": 100.1,
            "volatility_estimate": 0.2,
            "is_final": True,
        },
        name=idx,
    )
    ctx = bind_historical_bar_to_canonical_market_context_v1(
        bar=bar,
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=1,
    )
    assert ctx.volatility_estimate == pytest.approx(0.2)
    assert ctx.canonical_volatility_estimate is None


def test_research_fleet_join_no_bypass() -> None:
    result = quarantine_research_fleet_join_volatility_v1()
    assert result.disposition is VolatilityQuarantineDispositionV1.EXPLICIT_LEGACY_QUARANTINED
    assert result.legacy_value == pytest.approx(0.2)
    src = (
        ROOT
        / "src/research/offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0.py"
    ).read_text(encoding="utf-8")
    assert "quarantine_research_fleet_join_volatility_v1" in src


# --- Replay 0.02 ---


def test_implicit_productive_0_02_rejected() -> None:
    with pytest.raises(CanonicalVolatilityQuarantineError) as exc:
        quarantine_legacy_volatility_input_v1(
            raw_value=0.02,
            semantic_name="implicit_replay",
            source_kind="IMPLICIT",
            source_file_or_component="test",
            explicit_or_implicit="IMPLICIT",
            productive_or_test_only="PRODUCTIVE",
            fallback_or_default_or_floor="DEFAULT",
        )
    assert exc.value.code is CanonicalVolatilityQuarantineErrorCode.SILENT_DEFAULT_FORBIDDEN


def test_explicit_replay_0_02_quarantined_with_evidence() -> None:
    result = quarantine_explicit_replay_default_volatility_v1(source_file_or_component="test")
    assert result.disposition is VolatilityQuarantineDispositionV1.EXPLICIT_LEGACY_QUARANTINED
    assert result.legacy_value == pytest.approx(LEGACY_REPLAY_RULES_DEFAULT_VALUE)
    assert result.canonical_estimate_present is False
    assert len(result.quarantine_digest) == 64
    assert _DEFAULT_RULES.volatility_estimate == pytest.approx(0.02)
    assert _DEFAULT_SCOPE_RULES.volatility_estimate == pytest.approx(0.02)
    assert _SCENARIO_REPLAY_DEFAULT_VOL_QUARANTINE.quarantine_digest
    assert _REPLAY_DEFAULT_VOL_QUARANTINE.quarantine_digest


def test_replay_default_not_spoofed_as_typed() -> None:
    assert _SCENARIO_REPLAY_DEFAULT_VOL_QUARANTINE.typed_binding_present is False
    assert _REPLAY_DEFAULT_VOL_QUARANTINE.canonical_estimate_present is False


# --- Rules 1.0 ---


def test_bare_dynamic_scope_rules_unmaterialized() -> None:
    rules = DynamicScopeRules()
    assert rules.volatility_estimate is None
    assert rules.downscope_band_multiplier == pytest.approx(1.0)
    assert rules.upscope_band_multiplier == pytest.approx(1.0)


def test_explicit_test_fixture_1_0_allowed() -> None:
    result = quarantine_explicit_test_fixture_volatility_v1(
        value=LEGACY_DYNAMIC_SCOPE_RULES_CONSTRUCTOR_DEFAULT_VALUE,
        source_file_or_component="test",
    )
    assert result.disposition is VolatilityQuarantineDispositionV1.TEST_FIXTURE_ALLOWED
    assert require_admitted_legacy_volatility_float_v1(result) == pytest.approx(1.0)


# --- Floor 1e-9 ---


def test_zero_volatility_floor_rejected() -> None:
    with pytest.raises(CanonicalVolatilityQuarantineError) as exc:
        admit_positive_volatility_without_strategy_floor_v1(
            value=0.0,
            source_file_or_component="test",
        )
    assert exc.value.code is CanonicalVolatilityQuarantineErrorCode.INVALID_VALUE


def test_strategy_floor_rejected() -> None:
    with pytest.raises(CanonicalVolatilityQuarantineError) as exc:
        reject_strategy_authority_volatility_floor_v1()
    assert exc.value.code is CanonicalVolatilityQuarantineErrorCode.FLOOR_FORBIDDEN
    assert LEGACY_STRATEGY_FLOOR_VALUE == 1e-9


def test_admissible_positive_unchanged_by_rules_for_cycle() -> None:
    snap = _snapshot(volatility_estimate=0.02)
    rules = _rules_for_cycle_v1(provided=None, snapshot=snap)
    assert rules.volatility_estimate == pytest.approx(0.02)


def test_rules_for_cycle_rejects_zero_snapshot() -> None:
    snap = _snapshot(volatility_estimate=0.0)
    with pytest.raises(CanonicalVolatilityQuarantineError):
        _rules_for_cycle_v1(provided=None, snapshot=snap)


def test_floor_policy_none_enforced() -> None:
    goals = assert_capability_non_goals_v1()
    assert goals["floor_policy"] == "NONE"
    integrated = (
        ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    ).read_text(encoding="utf-8")
    assert "max(float(snapshot.volatility_estimate), 1e-9)" not in integrated


# --- Architecture / C1 reuse ---


def test_architecture_guards_pass() -> None:
    result = assert_architecture_guards_v1(repo_root=ROOT)
    assert result["guards_pass"] is True
    assert result["c1_reused"] is True
    assert result["silent_0_2_removed"] is True
    assert result["strategy_floor_removed"] is True
    assert result["productive_1_0_default_removed"] is True


def test_capability_manifest() -> None:
    goals = assert_capability_non_goals_v1()
    assert goals["capability_id"] == CAPABILITY_ID
    assert goals["runtime_wiring"] is False
    assert goals["runtime_producer_cutover"] is False
    assert goals["parameter_research"] is False
    assert goals["live_authorization"] is False
    assert goals["mv2_fallback_0_2_admissible"] is False
    assert PACKAGE_MARKER in goals["package_marker"]
    assert "G1_SILENT_FALLBACK_PATH_EXISTS" in goals["gaps_closed"]
    assert "G10_NUMERIC_FLOOR_SEMANTIC_LEAK_EXISTS" in goals["gaps_closed"]


def test_spec_exists() -> None:
    path = ROOT / "docs/ops/specs/MASTER_V2_CANONICAL_VOLATILITY_DEFAULT_QUARANTINE_V1.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_DEFAULT_QUARANTINE_V1" in text
    assert "RUNTIME_WIRING=false" in text
    assert "G1_SILENT_FALLBACK_PATH_EXISTS" in text


def test_no_second_adapter_in_quarantine_module() -> None:
    src = (ROOT / "src/trading/master_v2/canonical_volatility_default_quarantine_v1.py").read_text(
        encoding="utf-8"
    )
    assert "def adapt_canonical_volatility_estimate_to_legacy_float_v1(" not in src
    assert "canonical_volatility_binding_and_provenance_transport_v1" in src
