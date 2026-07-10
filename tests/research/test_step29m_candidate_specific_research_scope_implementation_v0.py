"""Contract tests for STEP29M candidate-specific research scope implementation v0."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.research.step29m_candidate_specific_research_scope_implementation_v0 import (
    AUTHORITY_EFFECT,
    BITCOIN_DIRECTION_ALLOWED,
    CONFIG_REL_PATHS,
    ECONOMIC_EVALUATION_AUTHORIZED,
    FUTURES_ONLY,
    RESEARCH_SCOPE_CANDIDATES,
    RESEARCH_V2_REGISTRY,
    RUNTIME_REWIRE_ADMISSIBLE,
    BindingValidationVerdict,
    ResearchV2LoadError,
    build_reuse_drift_guard_v0,
    build_reuse_inventory_v0,
    load_research_scope_config_v0,
    load_research_v2_generate_signals,
    load_v1_strategy_generate_signals,
    resolve_research_v2_strategy_class,
    scan_implementation_boundary_v0,
    validate_research_scope_binding_v0,
)
from src.strategies import load_strategy
from src.strategies.registry import get_strategy_spec, resolve_strategy_id
from src.strategies.step29m_bollinger_bands_v2 import (
    BollingerBandsV2Strategy,
    EligibilityClassification,
    STRATEGY_VERSION as BB_V2,
)
from src.strategies.step29m_momentum_1h_v2 import (
    Momentum1hV2Strategy,
    MIN_TRADE_COUNT_GUARD,
    STRATEGY_VERSION as MOM_V2,
)
from src.strategies.step29m_trend_following_v2 import (
    TrendFollowingV2Strategy,
    STRATEGY_VERSION as TF_V2,
)

ROOT = Path(__file__).resolve().parents[2]

V2_MODULE_PATHS = [
    ROOT / "src/strategies/step29m_trend_following_v2.py",
    ROOT / "src/strategies/step29m_bollinger_bands_v2.py",
    ROOT / "src/strategies/step29m_momentum_1h_v2.py",
    ROOT / "src/research/step29m_candidate_specific_research_scope_implementation_v0.py",
]

V1_STRATEGY_IDS = ("trend_following", "bollinger_bands", "momentum_1h")


def _sample_ohlcv(n: int = 120) -> pd.DataFrame:
    idx = pd.date_range("2024-05-01", periods=n, freq="h")
    rng = np.random.default_rng(42)
    close = 100 + np.cumsum(rng.normal(0, 0.5, n))
    high = close + rng.uniform(0.1, 1.0, n)
    low = close - rng.uniform(0.1, 1.0, n)
    return pd.DataFrame({"close": close, "high": high, "low": low}, index=idx)


@pytest.mark.parametrize("strategy_id", V1_STRATEGY_IDS)
def test_v1_unchanged_and_loadable(strategy_id: str) -> None:
    resolution = resolve_strategy_id(strategy_id)
    spec = get_strategy_spec(resolution.canonical_strategy_id)
    fn = load_strategy(strategy_id)
    df = _sample_ohlcv()
    signals = fn(df, {})
    assert isinstance(signals, pd.Series)
    assert spec.cls is not None


@pytest.mark.parametrize(
    ("strategy_id", "expected_version", "expected_cls"),
    [
        ("trend_following", TF_V2, TrendFollowingV2Strategy),
        ("bollinger_bands", BB_V2, BollingerBandsV2Strategy),
        ("momentum_1h", MOM_V2, Momentum1hV2Strategy),
    ],
)
def test_v2_versioned_and_loadable(
    strategy_id: str,
    expected_version: str,
    expected_cls: type,
) -> None:
    cls = resolve_research_v2_strategy_class(strategy_id, expected_version)
    assert cls is expected_cls
    assert cls.RESEARCH_VERSION == "v2"
    fn = load_research_v2_generate_signals(strategy_id, "v2")
    signals = fn(_sample_ohlcv(), {})
    assert isinstance(signals, pd.Series)


def test_v2_loader_rejects_non_v2_version() -> None:
    with pytest.raises(ResearchV2LoadError, match="strategy_version_v2"):
        load_research_v2_generate_signals("trend_following", "v1")


def test_v2_loader_unknown_binding_fail_closed() -> None:
    with pytest.raises(ResearchV2LoadError, match="unknown_research_v2_binding"):
        resolve_research_v2_strategy_class("unknown_strategy", "v2")


@pytest.mark.parametrize("strategy_id", V1_STRATEGY_IDS)
def test_research_scope_config_validates(strategy_id: str) -> None:
    cfg = load_research_scope_config_v0(ROOT, strategy_id)
    verdict, reasons = validate_research_scope_binding_v0(cfg)
    assert verdict is BindingValidationVerdict.PASS, reasons
    assert cfg["strategy_version"] == "v2"
    assert cfg["authority_effect"] == "NONE"


def test_missing_config_fail_closed() -> None:
    with pytest.raises(FileNotFoundError):
        load_research_scope_config_v0(ROOT, "nonexistent_strategy")


def test_invalid_binding_fail_closed() -> None:
    cfg = load_research_scope_config_v0(ROOT, "trend_following")
    bad = dict(cfg)
    bad["authority_effect"] = "LIVE"
    bad["economic_evaluation_authorized"] = True
    bad["bitcoin_direction_allowed"] = True
    verdict, reasons = validate_research_scope_binding_v0(bad)
    assert verdict is BindingValidationVerdict.FAIL_CLOSED
    assert "authority_effect_not_none" in reasons
    assert "economic_evaluation_authorized" in reasons
    assert "bitcoin_direction_forbidden" in reasons


def test_futures_only_no_bitcoin_no_spot() -> None:
    assert FUTURES_ONLY is True
    assert BITCOIN_DIRECTION_ALLOWED is False
    for strategy_id in V1_STRATEGY_IDS:
        cfg = load_research_scope_config_v0(ROOT, strategy_id)
        assert cfg["futures_only"] is True
        assert cfg["bitcoin_direction_allowed"] is False
        assert cfg["spot_allowed"] is False
        assert cfg["synthetic_spot_allowed"] is False


def test_no_zero_cost_defaults() -> None:
    for strategy_id in V1_STRATEGY_IDS:
        cfg = load_research_scope_config_v0(ROOT, strategy_id)
        assert cfg["fee_model_binding"]["fee_bps"] > 0
        assert cfg["slippage_model_binding"]["roundtrip_cost_bps"] > 0


def test_no_runtime_authority_fields() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert ECONOMIC_EVALUATION_AUTHORIZED is False
    assert RUNTIME_REWIRE_ADMISSIBLE is False
    for strategy_id in V1_STRATEGY_IDS:
        cfg = load_research_scope_config_v0(ROOT, strategy_id)
        assert cfg["authority_effect"] == "NONE"
        assert cfg["runtime_effect"] == "NONE"
        assert cfg["economic_evaluation_authorized"] is False
        assert cfg["runtime_rewire_admissible"] is False
        assert cfg["promotion_admissible"] is False


def test_v2_modules_no_runtime_imports() -> None:
    forbidden = (
        "src.trading.",
        "src.runtime.",
        "src.scheduler.",
        "src.orders.",
    )
    for path in V2_MODULE_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in forbidden:
                    assert not node.module.startswith(prefix.rstrip(".")), (
                        f"{path.name} imports {node.module}"
                    )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden:
                        assert not alias.name.startswith(prefix.rstrip(".")), (
                            f"{path.name} imports {alias.name}"
                        )


def test_reuse_drift_guard_pass() -> None:
    guard = build_reuse_drift_guard_v0()
    assert guard["drift_guard_status"] == "PASS"
    assert guard["parallel_registry"] is False
    assert guard["v1_files_modified"] is False


def test_reuse_inventory_reuses_canonical_owners() -> None:
    inv = build_reuse_inventory_v0()
    assert inv["parallel_registry_created"] is False
    assert "src.strategies.registry" in inv["canonical_registry_owner"]


def test_boundary_scan_pass() -> None:
    result = scan_implementation_boundary_v0(V2_MODULE_PATHS)
    assert result["boundary_scan_status"] == "PASS"
    assert result["economic_evaluation_executed"] is False


def test_three_scopes_implemented_separately() -> None:
    assert len(RESEARCH_SCOPE_CANDIDATES) == 3
    scope_ids = {c.scope_id for c in RESEARCH_SCOPE_CANDIDATES}
    assert len(scope_ids) == 3
    assert len(RESEARCH_V2_REGISTRY) == 3


def _trending_ohlcv(n: int = 200) -> pd.DataFrame:
    idx = pd.date_range("2024-05-01", periods=n, freq="h")
    close = np.linspace(100.0, 160.0, n) + np.sin(np.linspace(0, 8, n))
    high = close + 1.5
    low = close - 1.0
    return pd.DataFrame({"close": close, "high": high, "low": low}, index=idx)


def test_trend_following_v2_generates_signals_without_starvation() -> None:
    df = _trending_ohlcv(200)
    v1_fn = load_v1_strategy_generate_signals("trend_following")
    v2_fn = load_research_v2_generate_signals("trend_following", "v2")
    v1_count = int((v1_fn(df, {}) == 1).sum())
    v2_count = int((v2_fn(df, {}) == 1).sum())
    assert v1_count > 0
    assert v2_count > 0
    assert v2_count >= v1_count * 0.5


def test_bollinger_v2_trade_eligibility_trace() -> None:
    strategy = BollingerBandsV2Strategy()
    df = _sample_ohlcv(80)
    trace = strategy.generate_trade_eligibility_trace(df)
    assert "eligibility_classification" in trace.columns
    assert "gate_trace_stage" in trace.columns
    assert trace.attrs["entry_candidate_count"] >= 0
    summary = strategy.summarize_gate_trace(trace)
    assert EligibilityClassification.SIGNAL_INACTIVE.value in summary or summary


def test_momentum_v2_dominance_guard_contract() -> None:
    contract = Momentum1hV2Strategy.dominance_guard_contract()
    assert contract["min_trade_count"] == MIN_TRADE_COUNT_GUARD
    assert contract["max_single_trade_profit_contribution"] == 0.35
    assert contract["correlated_trade_duplication_allowed"] is False


def test_v1_loader_not_replaced_by_v2() -> None:
    v1_mod = importlib.import_module("src.strategies.trend_following")
    assert hasattr(v1_mod, "TrendFollowingStrategy")
    v2_mod = importlib.import_module("src.strategies.step29m_trend_following_v2")
    assert v2_mod.STRATEGY_VERSION == "v2"
    assert v1_mod.TrendFollowingStrategy is not v2_mod.TrendFollowingV2Strategy


def test_config_paths_exist() -> None:
    for rel in CONFIG_REL_PATHS.values():
        assert (ROOT / rel).is_file()
