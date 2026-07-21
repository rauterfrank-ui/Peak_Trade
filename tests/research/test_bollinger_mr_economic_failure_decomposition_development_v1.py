"""Contract tests for Bollinger/MR economic failure decomposition (DEVELOPMENT_ONLY) v1.

No holdout access. No full panel backtest in unit tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.research.bollinger_mr_economic_failure_decomposition_development_v1.binding_v1 import (
    DecompositionBindingError,
    assert_baseline_binding_digests,
    assert_contract_gates,
    assert_parent_baseline_ledger_binding,
    assert_trade_ledger_fields,
    load_contract,
    reject_holdout_access,
)
from src.research.bollinger_mr_economic_failure_decomposition_development_v1.classify_v1 import (
    classify_economic_failure,
)
from src.research.bollinger_mr_economic_failure_decomposition_development_v1.constants_v1 import (
    BASELINE_CONFIG_ID,
    COST_STRESS_MULTIPLIERS,
    DATASET_ID,
    DEVELOPMENT_SPLIT_DIGEST,
    DIAGNOSTIC_CLASSES,
    EVIDENCE_CLASS_ID,
    EXECUTION_ID,
    SCOPE_ID,
)
from src.research.bollinger_mr_economic_failure_decomposition_development_v1.metrics_v1 import (
    aggregate_core_metrics,
    compute_mfe_mae_from_bars,
    concentration_stats,
    cost_stress_table,
    enrich_trade_excursions,
    instrument_attribution,
    profit_factor,
    side_attribution,
)
from src.research.entry_effective_mr_eligibility_hypothesis_preregistration_v1 import (
    HypothesisPreregistrationError,
)

REPO = Path(__file__).resolve().parents[2]


def _sample_trades() -> list[dict]:
    return [
        {
            "instrument_id": "ETH",
            "side": "long",
            "entry_time": "2023-06-01T00:00:00Z",
            "exit_time": "2023-06-01T05:00:00Z",
            "entry_price": 100.0,
            "exit_price": 101.0,
            "size": 1.0,
            "gross_pnl": 1.0,
            "fees": 0.2,
            "slippage": 0.1,
            "net_pnl": 0.7,
            "exit_reason": "take_profit",
        },
        {
            "instrument_id": "ETH",
            "side": "short",
            "entry_time": "2023-06-02T00:00:00Z",
            "exit_time": "2023-06-02T04:00:00Z",
            "entry_price": 100.0,
            "exit_price": 102.0,
            "size": 1.0,
            "gross_pnl": -2.0,
            "fees": 0.2,
            "slippage": 0.1,
            "net_pnl": -2.3,
            "exit_reason": "stop_loss",
        },
        {
            "instrument_id": "SOL",
            "side": "short",
            "entry_time": "2023-06-03T00:00:00Z",
            "exit_time": "2023-06-03T03:00:00Z",
            "entry_price": 50.0,
            "exit_price": 51.0,
            "size": 2.0,
            "gross_pnl": -2.0,
            "fees": 0.1,
            "slippage": 0.05,
            "net_pnl": -2.15,
            "exit_reason": "stop_loss",
        },
    ]


def test_contract_core_fields() -> None:
    config = load_contract(REPO)
    assert config["scope_id"] == SCOPE_ID
    assert config["execution_id"] == EXECUTION_ID
    assert config["evidence_class_id"] == EVIDENCE_CLASS_ID
    assert config["dataset_id"] == DATASET_ID
    assert config["baseline_config_id"] == BASELINE_CONFIG_ID
    assert config["development_split_digest"] == DEVELOPMENT_SPLIT_DIGEST
    assert config["cost_stress_multipliers"] == list(COST_STRESS_MULTIPLIERS)
    assert config["diagnostic_classes"] == list(DIAGNOSTIC_CLASSES)
    assert config["economic_validity_offline_gate_pass"] is False
    assert config["promotion_eligible"] is False
    assert config["holdout_access_authorized"] is False
    assert config["new_hypothesis_authorized"] is False
    assert_contract_gates(config)


def test_baseline_digest_binding() -> None:
    config = load_contract(REPO)
    digests = assert_baseline_binding_digests(REPO, config)
    assert len(digests["binding_semantic_digest"]) == 64
    assert len(digests["config_digest"]) == 64


def test_baseline_digest_mismatch_fail_closed() -> None:
    config = load_contract(REPO)
    bad = dict(config)
    bad["baseline_binding_digests"] = dict(config["baseline_binding_digests"])
    bad["baseline_binding_digests"]["config_digest"] = "0" * 64
    with pytest.raises(DecompositionBindingError, match="BASELINE_DIGEST_MISMATCH"):
        assert_baseline_binding_digests(REPO, bad)


def test_parent_ledger_binding_and_mismatch() -> None:
    ok = {
        "trade_count": 3,
        "long_trades": 1,
        "short_trades": 2,
        "gross_pnl": -10.0,
        "fees": 2.0,
        "slippage": 1.0,
        "net_pnl": -13.0,
    }
    assert_parent_baseline_ledger_binding(observed=ok)
    bad = dict(ok)
    bad["net_pnl"] = -99.0
    with pytest.raises(DecompositionBindingError, match="LEDGER_GROSS_COST_NET_INCONSISTENT"):
        assert_parent_baseline_ledger_binding(observed=bad)
    bad2 = dict(ok)
    bad2["long_trades"] = 0
    with pytest.raises(DecompositionBindingError, match="LEDGER_SIDE_COUNT_MISMATCH"):
        assert_parent_baseline_ledger_binding(observed=bad2)


def test_holdout_path_rejected() -> None:
    with pytest.raises((DecompositionBindingError, HypothesisPreregistrationError)):
        reject_holdout_access("offline_economic_reevaluation_sealed_long_panel_v1")


def test_trade_ledger_missing_field_fail_closed() -> None:
    trade = _sample_trades()[0]
    del trade["fees"]
    with pytest.raises(DecompositionBindingError, match="TRADE_LEDGER_FIELD_MISSING"):
        assert_trade_ledger_fields(trade)


def test_profit_factor_and_cost_stress_determinism() -> None:
    trades = _sample_trades()
    a = cost_stress_table(trades)
    b = cost_stress_table(trades)
    assert a == b
    assert [r["cost_multiplier"] for r in a] == list(COST_STRESS_MULTIPLIERS)
    assert a[1]["gross_pnl"] == sum(t["gross_pnl"] for t in trades)
    assert a[1]["net_pnl"] == pytest.approx(sum(t["net_pnl"] for t in trades))
    # 2x costs deepen drag relative to 1x when gross fixed.
    assert a[3]["net_pnl"] < a[1]["net_pnl"]
    assert profit_factor([1.0, -2.0]) == pytest.approx(0.5)


def test_side_and_instrument_attribution() -> None:
    trades = _sample_trades()
    side = side_attribution(trades)
    assert side["long"]["trade_count"] == 1
    assert side["short"]["trade_count"] == 2
    assert side["short"]["net_pnl"] < side["long"]["net_pnl"]
    instruments = instrument_attribution(trades)
    assert {r["instrument_id"] for r in instruments} == {"ETH", "SOL"}
    conc = concentration_stats(instruments)
    assert "worst1_abs_net_share" in conc


def test_mfe_mae_and_capture_ratio() -> None:
    idx = pd.date_range("2023-06-01", periods=6, freq="h", tz="UTC")
    bars = pd.DataFrame(
        {
            "open": [100, 101, 102, 101, 100, 99],
            "high": [101, 103, 104, 102, 101, 100],
            "low": [99, 100, 101, 100, 99, 98],
            "close": [100, 102, 103, 101, 100, 99],
        },
        index=idx,
    )
    exc = compute_mfe_mae_from_bars(
        side="long",
        entry_price=100.0,
        entry_time=idx[0],
        exit_time=idx[4],
        bars=bars,
    )
    assert exc["status"] == "COMPUTED"
    assert exc["mfe"] == pytest.approx(4.0)
    assert exc["mae"] == pytest.approx(1.0)

    trades = [
        {
            "instrument_id": "ETH",
            "side": "long",
            "entry_time": str(idx[0]),
            "exit_time": str(idx[4]),
            "entry_price": 100.0,
            "size": 1.0,
            "gross_pnl": 1.0,
            "fees": 0.1,
            "slippage": 0.05,
            "net_pnl": 0.85,
        }
    ]
    enriched = enrich_trade_excursions(trades, {"ETH": bars})
    assert enriched[0]["realized_pnl_over_mfe_capture_ratio"] == pytest.approx(0.25)
    assert enriched[0]["mfe_to_exit_leakage"] == pytest.approx(3.0)
    core = aggregate_core_metrics(enriched)
    assert core["trade_count"] == 1


def test_classification_entry_has_no_gross_edge() -> None:
    core = {
        "trade_count": 10,
        "gross_pnl": -100.0,
        "net_pnl": -150.0,
        "gross_profit_factor": 0.5,
        "net_profit_factor": 0.4,
        "mean_realized_pnl_over_mfe_capture_ratio": None,
        "mean_mfe_to_exit_leakage": None,
        "trades_missing_mfe_mae": 0,
    }
    side = {
        "long": {"trade_count": 2, "net_pnl": -10.0},
        "short": {"trade_count": 8, "net_pnl": -140.0},
    }
    stress = [
        {
            "cost_multiplier": m,
            "gross_pnl": -100.0,
            "net_pnl": -100.0 - 50.0 * m,
        }
        for m in COST_STRESS_MULTIPLIERS
    ]
    result = classify_economic_failure(
        core=core,
        side=side,
        cost_stress=stress,
        concentration={"dominated_by_single": False, "worst1_abs_net_share": 0.1},
    )
    assert result["diagnostic_class"] == "ENTRY_HAS_NO_GROSS_EDGE"
    assert result["flags"]["ENTRY_GROSS_EDGE_PRESENT"] is False
    assert result["action_recommendation"] is None
    assert result["new_hypothesis"] is None


def test_classification_costs_destroy_marginal_edge() -> None:
    core = {
        "trade_count": 20,
        "gross_pnl": 10.0,
        "net_pnl": -5.0,
        "gross_profit_factor": 1.2,
        "net_profit_factor": 0.8,
        "mean_realized_pnl_over_mfe_capture_ratio": 0.8,
        "mean_mfe_to_exit_leakage": 1.0,
        "trades_missing_mfe_mae": 0,
    }
    side = {
        "long": {"trade_count": 10, "net_pnl": -2.0},
        "short": {"trade_count": 10, "net_pnl": -3.0},
    }
    stress = [
        {"cost_multiplier": 0.5, "gross_pnl": 10.0, "net_pnl": 2.0},
        {"cost_multiplier": 1.0, "gross_pnl": 10.0, "net_pnl": -5.0},
        {"cost_multiplier": 1.5, "gross_pnl": 10.0, "net_pnl": -12.0},
        {"cost_multiplier": 2.0, "gross_pnl": 10.0, "net_pnl": -20.0},
    ]
    # Adjust 0.5x so cost_drag_material condition holds (net <= 0.25*gross)
    stress[0]["net_pnl"] = 1.0
    result = classify_economic_failure(
        core=core,
        side=side,
        cost_stress=stress,
        concentration={"dominated_by_single": False, "worst1_abs_net_share": 0.1},
    )
    assert result["diagnostic_class"] == "COSTS_DESTROY_MARGINAL_EDGE"
    assert result["flags"]["ENTRY_GROSS_EDGE_PRESENT"] is True
    assert result["flags"]["COST_DRAG_MATERIAL"] is True


def test_classification_short_side_structural_drag() -> None:
    core = {
        "trade_count": 30,
        "gross_pnl": 20.0,
        "net_pnl": -5.0,
        "gross_profit_factor": 1.3,
        "net_profit_factor": 0.9,
        "mean_realized_pnl_over_mfe_capture_ratio": 0.7,
        "mean_mfe_to_exit_leakage": 2.0,
        "trades_missing_mfe_mae": 0,
    }
    side = {
        "long": {"trade_count": 5, "net_pnl": 8.0},
        "short": {"trade_count": 25, "net_pnl": -13.0},
    }
    stress = [
        {"cost_multiplier": 0.5, "gross_pnl": 20.0, "net_pnl": 12.0},
        {"cost_multiplier": 1.0, "gross_pnl": 20.0, "net_pnl": 5.0},
        {"cost_multiplier": 1.5, "gross_pnl": 20.0, "net_pnl": -2.0},
        {"cost_multiplier": 2.0, "gross_pnl": 20.0, "net_pnl": -10.0},
    ]
    result = classify_economic_failure(
        core=core,
        side=side,
        cost_stress=stress,
        concentration={"dominated_by_single": False, "worst1_abs_net_share": 0.2},
    )
    assert result["diagnostic_class"] == "SHORT_SIDE_STRUCTURAL_DRAG"
    assert result["flags"]["SHORT_SIDE_DRAG_MATERIAL"] is True


def test_classification_determinism() -> None:
    payload = {
        "core": {
            "trade_count": 10,
            "gross_pnl": -50.0,
            "net_pnl": -80.0,
            "gross_profit_factor": 0.6,
            "net_profit_factor": 0.5,
            "mean_realized_pnl_over_mfe_capture_ratio": None,
            "mean_mfe_to_exit_leakage": None,
            "trades_missing_mfe_mae": 0,
        },
        "side": {
            "long": {"trade_count": 3, "net_pnl": -10.0},
            "short": {"trade_count": 7, "net_pnl": -70.0},
        },
        "cost_stress": [
            {"cost_multiplier": m, "gross_pnl": -50.0, "net_pnl": -50.0 - 10 * m}
            for m in COST_STRESS_MULTIPLIERS
        ],
        "concentration": {"dominated_by_single": False, "worst1_abs_net_share": 0.15},
    }
    a = classify_economic_failure(**payload)
    b = classify_economic_failure(**payload)
    assert a == b
    assert a["diagnostic_class"] in DIAGNOSTIC_CLASSES


def test_governance_doc_and_owner_map_present() -> None:
    gov = REPO / "docs/governance/BOLLINGER_MR_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_V1.md"
    text = gov.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_BOLLINGER_MR_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_V1" in text
    assert "HOLDOUT_ACCESS_AUTHORIZED" in text
    owner_map = json.loads(
        (
            REPO
            / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
        ).read_text(encoding="utf-8")
    )
    owners = owner_map["allowed_optimization_surfaces"]
    assert "BOLLINGER_MR_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_V1" in owners
    paths = owners["BOLLINGER_MR_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_V1"]["path_prefixes"]
    assert any("bollinger_mr_economic_failure_decomposition_development_v1" in p for p in paths)


def test_wiring_authorization_includes_new_paths() -> None:
    auth = json.loads(
        (REPO / "config/governance/technical_canonical_wiring_authorization_v1.json").read_text(
            encoding="utf-8"
        )
    )
    allowed = set(auth["allowed_paths"])
    required = {
        "config/research/bollinger_mr_economic_failure_decomposition_development_v1.json",
        "src/research/bollinger_mr_economic_failure_decomposition_development_v1/__init__.py",
        "src/research/bollinger_mr_economic_failure_decomposition_development_v1/constants_v1.py",
        "src/research/bollinger_mr_economic_failure_decomposition_development_v1/binding_v1.py",
        "src/research/bollinger_mr_economic_failure_decomposition_development_v1/metrics_v1.py",
        "src/research/bollinger_mr_economic_failure_decomposition_development_v1/classify_v1.py",
        "src/research/bollinger_mr_economic_failure_decomposition_development_v1/decompose_v1.py",
        "scripts/research/run_bollinger_mr_economic_failure_decomposition_development_v1.py",
        "tests/research/test_bollinger_mr_economic_failure_decomposition_development_v1.py",
        "docs/governance/BOLLINGER_MR_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_V1.md",
        "docs/evidence/bollinger_mr_economic_failure_decomposition_development_v1/summary.json",
        "docs/evidence/bollinger_mr_economic_failure_decomposition_development_v1/MANIFEST.sha256",
    }
    missing = required - allowed
    assert not missing, f"missing wiring paths: {sorted(missing)}"
    assert (
        "TECHNICAL_BOLLINGER_MR_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_WIRING"
        in auth["allowed_surface_classes"]
    )
