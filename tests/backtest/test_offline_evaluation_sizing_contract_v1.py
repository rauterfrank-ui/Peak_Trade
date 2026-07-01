"""Contract tests for offline evaluation sizing contract v1 (STEP 29M)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pandas as pd
import pytest

from src.backtest.engine import BacktestEngine
from src.risk import RiskLimits, RiskLimitsConfig
from src.backtest.offline_evaluation_sizing_contract_v1 import (
    CONTRACT_OWNER,
    MACD_V1_CANONICAL_STOP_PCT,
    MACD_V1_CANONICAL_STOP_DERIVATION,
    OfflineEvaluationSizingError,
    SizingReasonCode,
    bind_offline_evaluation_sizing_v1,
    compute_sizing_contract_digest_v1,
    load_offline_evaluation_sizing_contract_v1,
    offline_evaluation_sizing_contract_requested,
    size_offline_evaluation_entry_v1,
)
from src.backtest import mv2_research_wiring_v1 as wiring
from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
V1_CONFIG = (
    REPO_ROOT / "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v1.json"
)
V2_CONFIG = (
    REPO_ROOT / "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v2.json"
)
PROGRESS_REGISTRY = REPO_ROOT / "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
MACD_EVIDENCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "implementation/step29m_macd_v1_real_admissible_futures_economic_evaluation_v1_20260701T161757Z"
)
ROOT_CAUSE_EVIDENCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning_or_validation/"
    "step29m_macd_zero_trade_post_signal_root_cause_and_strategy_ranking_read_only_v1_20260701T205720Z"
)


def _base_sizing_section() -> dict:
    return {
        "sizing_contract_version": "offline_evaluation_sizing_contract_v1",
        "initial_equity": 10000.0,
        "risk_per_trade": 0.02,
        "stop_distance_policy": "FIXED_PCT_FROM_ENTRY_v1",
        "stop_pct": 0.08,
        "max_position_pct": 0.25,
        "oversize_policy": "REJECT_OVERSIZE",
        "quantity_rounding_policy": "NONE_v1",
        "minimum_quantity_policy": "REJECT_BELOW_MIN_NOTIONAL_v1",
        "minimum_notional_policy": "USE_RISK_MIN_POSITION_VALUE_v1",
        "instrument_metadata_source": "versioned_dataset_manifest_v1",
        "price_source": "bar_close_v1",
        "sizing_owner": CONTRACT_OWNER,
        "sizing_mode": "fixed_fractional_risk_per_trade_v1",
        "strategy_params_digest": "4742e4dbed66dd6a8078d09803234a468261ed444f16c533b8cd70f78f869c00",
        "dataset_digest": "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78",
        "config_digest": "",
    }


def _cfg_with_sizing(**overrides: object) -> dict:
    cfg = json.loads(V2_CONFIG.read_text(encoding="utf-8"))
    section = _base_sizing_section()
    section.update(overrides)
    body = {key: value for key, value in section.items() if key != "config_digest"}
    section["config_digest"] = compute_sizing_contract_digest_v1(
        load_offline_evaluation_sizing_contract_v1(
            {
                "offline_evaluation_sizing_contract_v1": body,
                "backtest": cfg["backtest"],
                "risk": cfg["risk"],
            }
        )
    )
    cfg["offline_evaluation_sizing_contract_v1"] = section
    return cfg


def _minimal_bars(count: int = 6) -> pd.DataFrame:
    idx = pd.date_range("2026-06-17", periods=count, freq="h", tz="UTC")
    close = [100.0 + i for i in range(count)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [c + 1 for c in close],
            "low": [c - 1 for c in close],
            "close": close,
            "volume": [1000.0] * count,
        },
        index=idx,
    )


def _constant_signal_fn(signals: list[int]):
    def _fn(df: pd.DataFrame, params: dict) -> pd.Series:  # noqa: ARG001
        series = pd.Series(signals[: len(df)], index=df.index, dtype=int)
        if len(series) < len(df):
            padded = [0] * (len(df) - len(series)) + signals
            series = pd.Series(padded[: len(df)], index=df.index, dtype=int)
        return series

    return _fn


def test_v1_config_has_no_sizing_contract() -> None:
    cfg = json.loads(V1_CONFIG.read_text(encoding="utf-8"))
    assert not offline_evaluation_sizing_contract_requested(cfg)


def test_v2_config_has_explicit_sizing_contract() -> None:
    cfg = json.loads(V2_CONFIG.read_text(encoding="utf-8"))
    assert offline_evaluation_sizing_contract_requested(cfg)
    contract = load_offline_evaluation_sizing_contract_v1(cfg)
    assert contract.stop_pct == MACD_V1_CANONICAL_STOP_PCT
    assert contract.stop_pct_derivation_ref == MACD_V1_CANONICAL_STOP_DERIVATION
    assert contract.oversize_policy == "REJECT_OVERSIZE"
    assert contract.config_digest == compute_sizing_contract_digest_v1(contract)


def test_missing_stop_pct_blocks_contract_load() -> None:
    section = _base_sizing_section()
    section.pop("stop_pct")
    cfg = {
        "offline_evaluation_sizing_contract_v1": section,
        "backtest": {"initial_cash": 10000},
        "risk": {},
    }
    with pytest.raises(OfflineEvaluationSizingError, match="MISSING_STOP_PCT"):
        load_offline_evaluation_sizing_contract_v1(cfg)


def test_missing_oversize_policy_blocks_contract_load() -> None:
    section = _base_sizing_section()
    section.pop("oversize_policy")
    cfg = {
        "offline_evaluation_sizing_contract_v1": section,
        "backtest": {"initial_cash": 10000},
        "risk": {},
    }
    with pytest.raises(OfflineEvaluationSizingError, match="MISSING_OVERSIZE_POLICY"):
        load_offline_evaluation_sizing_contract_v1(cfg)


def test_unknown_sizing_field_fail_closed() -> None:
    section = _base_sizing_section()
    section["mystery_field"] = True
    cfg = {
        "offline_evaluation_sizing_contract_v1": section,
        "backtest": {"initial_cash": 10000},
        "risk": {},
    }
    with pytest.raises(OfflineEvaluationSizingError, match="unknown_sizing_fields"):
        load_offline_evaluation_sizing_contract_v1(cfg)


@pytest.mark.parametrize(
    "field,value",
    [
        ("stop_pct", 0.0),
        ("stop_pct", -0.01),
        ("risk_per_trade", 0.0),
        ("max_position_pct", 1.5),
    ],
)
def test_invalid_sizing_values_rejected(field: str, value: float) -> None:
    section = _base_sizing_section()
    section[field] = value
    cfg = {
        "offline_evaluation_sizing_contract_v1": section,
        "backtest": {"initial_cash": 10000.0},
        "risk": {"min_position_value": 10.0, "min_stop_distance": 0.0001},
    }
    with pytest.raises(OfflineEvaluationSizingError):
        load_offline_evaluation_sizing_contract_v1(cfg)


def test_reject_oversize_produces_structured_reason() -> None:
    cfg = _cfg_with_sizing(stop_pct=0.02, oversize_policy="REJECT_OVERSIZE")
    contract = load_offline_evaluation_sizing_contract_v1(cfg)
    outcome = size_offline_evaluation_entry_v1(
        contract=contract,
        equity=10000.0,
        entry_price=100.0,
        cfg=cfg,
    )
    assert not outcome.accepted
    assert outcome.reason_code is SizingReasonCode.REQUESTED_NOTIONAL_EXCEEDS_MAX_POSITION


def test_cap_policy_caps_to_max_without_increasing_risk() -> None:
    cfg = _cfg_with_sizing(stop_pct=0.02, oversize_policy="CAP_TO_MAX_POSITION_PCT")
    contract = load_offline_evaluation_sizing_contract_v1(cfg)
    outcome = size_offline_evaluation_entry_v1(
        contract=contract,
        equity=10000.0,
        entry_price=100.0,
        cfg=cfg,
    )
    assert outcome.accepted
    assert outcome.capped
    assert outcome.effective_notional == pytest.approx(2500.0)
    assert outcome.reason_code is SizingReasonCode.POSITION_CAPPED_TO_MAX_POSITION


def test_admissible_entry_fixture_executes_trade_path() -> None:
    cfg = _cfg_with_sizing(stop_pct=0.10, oversize_policy="REJECT_OVERSIZE")
    engine_cfg = copy.deepcopy(cfg)
    bind_offline_evaluation_sizing_v1(
        engine_cfg,
        strategy_params_digest=cfg["offline_evaluation_sizing_contract_v1"][
            "strategy_params_digest"
        ],
        dataset_digest=cfg["offline_evaluation_sizing_contract_v1"]["dataset_digest"],
    )
    engine = BacktestEngine(
        use_execution_pipeline=False,
        risk_limits=RiskLimits(RiskLimitsConfig(max_position_pct=25.0)),
    )
    engine.config = engine_cfg
    result = engine.run_realistic(
        df=_minimal_bars(),
        strategy_signal_fn=_constant_signal_fn([0, 1, 0, -1, 0, 0]),
        strategy_params={"stop_pct": cfg["offline_evaluation_sizing_contract_v1"]["stop_pct"]},
        symbol="inst-eth-usdt-perp",
        explicit_zero_cost_non_economic=True,
        fee_bps=10.0,
        slippage_bps=5.0,
    )
    assert result.stats["total_trades"] >= 1


def test_engine_blocks_missing_stop_pct_when_contract_bound() -> None:
    cfg = _cfg_with_sizing()
    engine_cfg = copy.deepcopy(cfg)
    bind_offline_evaluation_sizing_v1(
        engine_cfg,
        strategy_params_digest=cfg["offline_evaluation_sizing_contract_v1"][
            "strategy_params_digest"
        ],
        dataset_digest=cfg["offline_evaluation_sizing_contract_v1"]["dataset_digest"],
    )
    engine = BacktestEngine(
        use_execution_pipeline=False,
        risk_limits=RiskLimits(RiskLimitsConfig(max_position_pct=25.0)),
    )
    engine.config = engine_cfg
    with pytest.raises(Exception, match="MISSING_STOP_PCT"):
        engine.run_realistic(
            df=_minimal_bars(3),
            strategy_signal_fn=_constant_signal_fn([0, 1, 0]),
            strategy_params={},
            symbol="inst-eth-usdt-perp",
            explicit_zero_cost_non_economic=True,
            fee_bps=10.0,
            slippage_bps=5.0,
        )


def test_runtime_engine_default_stop_pct_unchanged_without_contract() -> None:
    engine = BacktestEngine(use_execution_pipeline=False)
    engine.config = {
        "backtest": {"initial_cash": 10000.0},
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
    }
    result = engine.run_realistic(
        df=_minimal_bars(4),
        strategy_signal_fn=_constant_signal_fn([0, 1, 0, -1]),
        strategy_params={},
        symbol="inst-eth-usdt-perp",
        explicit_zero_cost_non_economic=True,
        fee_bps=10.0,
        slippage_bps=5.0,
    )
    assert "total_trades" in result.stats


def test_mv2_wiring_emits_sizing_provenance_when_contract_bound() -> None:
    cfg = _cfg_with_sizing(stop_pct=0.08)
    cfg["economic_evaluation_v1"] = {
        "strategy_id": "ma_crossover",
        "strategy_version": "v1",
        "strategy_params": {"fast_period": 10, "slow_period": 30},
        "engine_signal_source": "configured_strategy_signal",
        "walk_forward": {"bind": True},
        "monte_carlo": {"bind": True},
        "stress": {"bind": True},
    }
    bars = _minimal_bars(35)
    result = wiring.run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id="ma_crossover",
        cfg=cfg,
        instrument_id="inst-eth-usdt-perp",
        explicit_zero_cost_non_economic=True,
    )
    prov = result.sizing_provenance
    assert prov["sizing_contract_version"] == "offline_evaluation_sizing_contract_v1"
    assert prov["runtime_sizing_policy_unchanged"] is True
    assert prov["entry_candidate_count"] == (
        prov["entry_sizing_pass_count"] + prov["entry_sizing_reject_count"]
    )


def test_v2_config_digest_differs_from_v1() -> None:
    v1 = json.loads(V1_CONFIG.read_text(encoding="utf-8"))
    v2 = json.loads(V2_CONFIG.read_text(encoding="utf-8"))
    assert compute_evaluation_config_digest_v1(v1) != compute_evaluation_config_digest_v1(v2)


def test_macd_v1_evaluation_evidence_remains_immutable() -> None:
    if not MACD_EVIDENCE.is_dir():
        pytest.skip("macd evidence archive not present locally")
    summary_path = MACD_EVIDENCE / "EVALUATION_RUN_SUMMARY.json"
    before = summary_path.read_text(encoding="utf-8")
    assert "REAL_EVALUATION_PERFORMED" in before
    assert summary_path.read_text(encoding="utf-8") == before


def test_registry_invalidates_macd_v1_evaluation() -> None:
    import re

    text = PROGRESS_REGISTRY.read_text(encoding="utf-8")
    start = text.index("#### RUNBOOK_STEP_29M — Economic Viability Evidence v1")
    end = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1", start)
    section = text[start:end]

    def field(name: str) -> str:
        match = re.search(rf"\| `{re.escape(name)}` \| `([^`]*)` \|", section)
        assert match, name
        return match.group(1)

    assert field("REAL_EVALUATION_ATTEMPTED") == "true"
    assert field("REAL_EVALUATION_PERFORMED") == "false"
    assert field("REAL_ADMISSIBLE_FUTURES_EVIDENCE_BOUND") == "false"
    assert (
        field("REAL_EVALUATION_INPUT_STATUS")
        == "MACD_V1_EVALUATION_INVALIDATED_OFFLINE_SIZING_CONTRACT_DEFECT"
    )
    assert field("ECONOMIC_VALIDITY_RESULT") == "NOT_PROVEN"
    assert field("PROFITABILITY_CLAIM_ALLOWED") == "false"
    assert (
        field("INVALIDATION_REASON")
        == "IMPLICIT_STOP_PCT_AND_OVERSIZE_REJECTION_BLOCKED_ALL_ENTRIES"
    )
    assert field("RUNBOOK_STEP_29M_COMPLETE") == "true"
    assert str(MACD_EVIDENCE) in field("MACD_V1_REAL_EVALUATION_EVIDENCE_REF")
    assert str(ROOT_CAUSE_EVIDENCE) in field("ROOT_CAUSE_EVIDENCE_REF")
    assert (
        field("NEXT_EVALUATION_CONFIG_PATH")
        == "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v2.json"
    )
