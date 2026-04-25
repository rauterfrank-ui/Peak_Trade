# tests/trading/master_v2/test_double_play_suitability.py
from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.double_play_suitability import (
    DOUBLE_PLAY_SUITABILITY_LAYER_VERSION,
    InstrumentIntelligenceSummary,
    SideCompatibility,
    StrategyMetadata,
    SuitabilityBlockReason,
    SuitabilityClass,
    SuitabilityProjectionInput,
    instrument_intelligence_complete,
    metadata_has_authoritative_side_evidence,
    project_strategy_suitability,
    survival_allows_projection,
)


def _ii_all_present() -> InstrumentIntelligenceSummary:
    return InstrumentIntelligenceSummary(
        volatility_profile_present=True,
        liquidity_profile_present=True,
        spread_profile_present=True,
        funding_profile_present=True,
        freshness_profile_present=True,
    )


def _ii_incomplete() -> InstrumentIntelligenceSummary:
    return InstrumentIntelligenceSummary(
        volatility_profile_present=True,
        liquidity_profile_present=False,
        spread_profile_present=True,
        funding_profile_present=True,
        freshness_profile_present=True,
    )


def _base_meta(**kwargs: object) -> StrategyMetadata:
    defaults: dict = {
        "strategy_id": "sid",
        "strategy_family": "trend",
        "declared_side": SideCompatibility.UNKNOWN,
        "explicit_side_evidence": False,
        "registry_label": None,
        "name_surface": None,
        "ecm_or_armstrong_surface": None,
        "dashboard_label": None,
        "ai_summary": None,
        "disabled": False,
        "blockers": (),
    }
    defaults.update(kwargs)
    return StrategyMetadata(**defaults)  # type: ignore[arg-type]


def _inp(
    meta: StrategyMetadata,
    inst: InstrumentIntelligenceSummary | None = None,
    surv: bool = True,
    reasons: tuple[str, ...] = (),
) -> SuitabilityProjectionInput:
    return SuitabilityProjectionInput(
        strategy=meta,
        instrument=inst,
        survival_envelope_allows=surv,
        survival_block_reasons=reasons,
    )


def test_1_registry_name_only_is_unknown() -> None:
    m = _base_meta(
        registry_label="ma_crossover",
        name_surface="MA Cross",
    )
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.suitability_class is SuitabilityClass.UNKNOWN_SUITABILITY
    assert d.can_enter_long_bull_pool is False
    assert d.projection.live_authorization is False


def test_2_ecm_or_armstrong_name_surface_cannot_grant() -> None:
    m = _base_meta(ecm_or_armstrong_surface="armstrong_cycle", registry_label="r")
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.suitability_class is SuitabilityClass.UNKNOWN_SUITABILITY
    assert SuitabilityBlockReason.INSUFFICIENT_EXPLICIT_EVIDENCE in d.projection.block_reasons


def test_3_long_only_with_explicit_goes_to_long_bull() -> None:
    m = _base_meta(
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.suitability_class is SuitabilityClass.LONG_ONLY_CANDIDATE
    assert d.projection.eligible_for_long_bull_pool is True
    assert d.projection.eligible_for_short_bear_pool is False
    assert d.projection.eligible_for_neutral_pool is False
    assert d.projection.is_signal is False
    assert d.projection.is_authority is False


def test_4_short_only_with_explicit_goes_to_short_bear() -> None:
    m = _base_meta(
        declared_side=SideCompatibility.SHORT_BEAR,
        explicit_side_evidence=True,
    )
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.suitability_class is SuitabilityClass.SHORT_ONLY_CANDIDATE
    assert d.projection.eligible_for_short_bear_pool is True
    assert d.projection.eligible_for_long_bull_pool is False


def test_5_both_sides_needs_explicit_evidence() -> None:
    m = _base_meta(
        declared_side=SideCompatibility.BOTH,
        explicit_side_evidence=False,
    )
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.suitability_class is SuitabilityClass.UNKNOWN_SUITABILITY
    assert d.can_enter_any_candidate_pool is False
    assert "Both-side" in d.projection.reason or "evidence" in d.projection.reason


def test_6_neutral_range_not_directional() -> None:
    m = _base_meta(
        declared_side=SideCompatibility.NEUTRAL_RANGE,
        explicit_side_evidence=True,
    )
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.suitability_class is SuitabilityClass.NEUTRAL_RANGE_CANDIDATE
    assert d.projection.eligible_for_neutral_pool is True
    assert d.projection.eligible_for_long_bull_pool is False
    assert d.projection.eligible_for_short_bear_pool is False


def test_7_disabled_is_disabled_for_candidate() -> None:
    m = _base_meta(
        disabled=True, declared_side=SideCompatibility.LONG_BULL, explicit_side_evidence=True
    )
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.suitability_class is SuitabilityClass.DISABLED_FOR_CANDIDATE
    assert d.can_enter_any_candidate_pool is False
    assert SuitabilityBlockReason.STRATEGY_DISABLED in d.projection.block_reasons


def test_8_metadata_blockers_is_disabled() -> None:
    m = _base_meta(
        blockers=(SuitabilityBlockReason.INSUFFICIENT_EXPLICIT_EVIDENCE,),
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.suitability_class is SuitabilityClass.DISABLED_FOR_CANDIDATE
    assert d.can_enter_long_bull_pool is False


def test_9_declared_side_unknown_is_unknown_even_if_explicit() -> None:
    m = _base_meta(
        declared_side=SideCompatibility.UNKNOWN,
        explicit_side_evidence=True,
    )
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.suitability_class is SuitabilityClass.UNKNOWN_SUITABILITY
    assert d.can_enter_any_candidate_pool is False


def test_10_instrument_incomplete_is_unknown() -> None:
    m = _base_meta(
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    d = project_strategy_suitability(_inp(m, _ii_incomplete(), True))
    assert d.projection.suitability_class is SuitabilityClass.UNKNOWN_SUITABILITY
    assert d.projection.missing_inputs


def test_11_instrument_none_is_unknown() -> None:
    m = _base_meta(
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    d = project_strategy_suitability(
        SuitabilityProjectionInput(
            strategy=m,
            instrument=None,
            survival_envelope_allows=True,
        )
    )
    assert d.projection.suitability_class is SuitabilityClass.UNKNOWN_SUITABILITY
    assert SuitabilityBlockReason.INSTRUMENT_INTELLIGENCE_INCOMPLETE in d.projection.block_reasons


def test_12_survival_blocks_pools() -> None:
    m = _base_meta(
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    d = project_strategy_suitability(_inp(m, _ii_all_present(), False, ("path_survival",)))
    assert d.projection.suitability_class is SuitabilityClass.UNKNOWN_SUITABILITY
    assert d.projection.eligible_for_long_bull_pool is False
    assert SuitabilityBlockReason.SURVIVAL_ENVELOPE_BLOCKED in d.projection.block_reasons


def test_13_ai_summary_alone_cannot_grant() -> None:
    m = _base_meta(ai_summary="Bullish narrative from AI.")
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.suitability_class is SuitabilityClass.UNKNOWN_SUITABILITY


def test_14_dashboard_label_alone_cannot_grant() -> None:
    m = _base_meta(dashboard_label="ELIGIBLE")
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.suitability_class is SuitabilityClass.UNKNOWN_SUITABILITY


def test_15_never_live_authorization() -> None:
    m = _base_meta(
        declared_side=SideCompatibility.BOTH,
        explicit_side_evidence=True,
    )
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.live_authorization is False
    assert d.live_authorization is False


def test_16_both_sides_both_pools() -> None:
    m = _base_meta(
        declared_side=SideCompatibility.BOTH,
        explicit_side_evidence=True,
    )
    d = project_strategy_suitability(_inp(m, _ii_all_present(), True))
    assert d.projection.suitability_class is SuitabilityClass.BOTH_SIDES_CANDIDATE
    assert d.projection.eligible_for_long_bull_pool is True
    assert d.projection.eligible_for_short_bear_pool is True
    assert d.projection.eligible_for_neutral_pool is False


def test_17_layer_version_constant() -> None:
    assert DOUBLE_PLAY_SUITABILITY_LAYER_VERSION == "v0"


def test_18_helper_survival_allows() -> None:
    m = _base_meta(
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    i = _inp(m, _ii_all_present(), True)
    assert survival_allows_projection(i) is True
    assert instrument_intelligence_complete(_ii_all_present()) is True
    assert instrument_intelligence_complete(None) is False
    assert (
        metadata_has_authoritative_side_evidence(
            _base_meta(
                declared_side=SideCompatibility.LONG_BULL,
                explicit_side_evidence=True,
            )
        )
        is True
    )
    assert (
        metadata_has_authoritative_side_evidence(
            _base_meta(explicit_side_evidence=False, declared_side=SideCompatibility.UNKNOWN)
        )
        is False
    )


def test_19_no_network_imports_in_module() -> None:
    p = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "trading"
        / "master_v2"
        / "double_play_suitability.py"
    )
    tree = ast.parse(p.read_text(encoding="utf-8"))
    bad = {"requests", "urllib3", "ccxt", "httpx", "socket", "aiohttp"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                assert n.name.split(".")[0] not in bad
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in bad
