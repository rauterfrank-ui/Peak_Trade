"""Contract tests for post-#5348 canonical economic reevaluation audit harness.

Does not execute the full offline 118-member panel. Validates harness markers,
chain-binding proof, classification fail-closed rules, and evidence path hygiene.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_HARNESS = (
    _REPO
    / "docs/evidence/canonical_economic_reevaluation_post_5348_v1"
    / "economic_reevaluation_probe_v1.py"
)

PRODUCTIVE_GLOBS = (
    "src/trading/",
    "src/execution/",
    "src/risk/",
    "src/strategies/",
    "src/governance/",
)


def _load_harness():
    assert _HARNESS.is_file(), f"missing harness: {_HARNESS}"
    spec = importlib.util.spec_from_file_location(
        "canonical_economic_reevaluation_post_5348_probe_v1", _HARNESS
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def harness():
    return _load_harness()


def test_harness_is_non_authoritative_and_offline_only(harness) -> None:
    src = _HARNESS.read_text(encoding="utf-8")
    assert "NON-AUTHORITATIVE" in src
    assert harness.AUDIT_AUTHORITY_EFFECT == "NONE"
    assert harness.AUDIT_RUNTIME_EFFECT == "NONE"
    assert "run_mv2_research_backtest_wiring_v1" in src
    assert harness.SEED == 42
    assert harness.FEE_BPS == 10.0
    assert harness.SLIPPAGE_BPS == 5.0
    assert harness.STOP_PCT == 0.025


def test_harness_does_not_live_in_productive_owners() -> None:
    rel = str(_HARNESS.relative_to(_REPO))
    assert rel.startswith("docs/evidence/")
    for g in PRODUCTIVE_GLOBS:
        assert not rel.startswith(g)


def test_chain_binding_proof_static(harness) -> None:
    proof = harness.prove_chain_binding_static()
    assert proof["uses_run_mv2_research_backtest_wiring_v1"] is True
    assert proof["uses_integrated_offline_replay"] is True
    assert proof["transition_state_owner_present"] is True
    assert proof["composition_owner_present"] is True
    assert proof["short_bound_via_execution_pipeline"] is True
    assert proof["canonical_engine_signal_source"] == "mv2_decision_replay_series"
    assert proof["economic_gate_opened"] is False
    assert proof["promotion_eligible"] is False
    assert proof["live_authorized"] is False
    assert proof["orders"] is False
    assert proof["direction_authority"] == "trading.master_v2.double_play_state.transition_state"


def test_classification_low_sample(harness) -> None:
    klass, status, rationale = harness.classify_economic(
        period_extension_available=False,
        agg={"total_trades": 14, "net_return": -0.05, "profit_factor": 0.0},
        walk_forward_rows=[],
        stress_rows=[],
    )
    assert klass == harness.CLASS_LOW
    assert status == "PARTIAL"
    assert "NO_LONGER" in rationale or "trades=" in rationale


def test_classification_fail_economic(harness) -> None:
    klass, status, rationale = harness.classify_economic(
        period_extension_available=False,
        agg={"total_trades": 40, "net_return": -0.12, "profit_factor": 0.4},
        walk_forward_rows=[
            {"net_return": -0.04},
            {"net_return": -0.03},
            {"net_return": -0.05},
        ],
        stress_rows=[{"net_return": -0.15}],
    )
    assert klass == harness.CLASS_FAIL
    assert status == "PARTIAL"
    assert rationale


def test_classification_unstable(harness) -> None:
    klass, status, _ = harness.classify_economic(
        period_extension_available=False,
        agg={
            "total_trades": 50,
            "net_return": 0.02,
            "profit_factor": 1.2,
            "cost_application": "PASS",
            "economic_measurement_valid": True,
        },
        walk_forward_rows=[
            {"net_return": 0.10},
            {"net_return": -0.08},
            {"net_return": 0.05},
        ],
        stress_rows=[{"net_return": -0.01}],
    )
    assert klass == harness.CLASS_UNSTABLE
    assert status == "PARTIAL"


def test_classification_invalid_when_costs_not_applied(harness) -> None:
    klass, status, rationale = harness.classify_economic(
        period_extension_available=False,
        agg={
            "total_trades": 464,
            "net_return": 0.004,
            "profit_factor": 1.2,
            "cost_application": "NOT_APPLIED",
            "economic_measurement_valid": False,
        },
        walk_forward_rows=[],
        stress_rows=[],
    )
    assert klass == harness.CLASS_INVALID
    assert status == "FAIL"
    assert "INVALID_ECONOMIC_MEASUREMENT" in rationale


def test_aggregate_rows_does_not_sum_instrument_returns(harness) -> None:
    rows = [
        {
            "gross_pnl": 100.0,
            "net_pnl": 100.0,
            "fees": 0.0,
            "slippage_drag": 0.0,
            "cost_drag": 0.0,
            "net_return": 0.01,
            "max_drawdown": -0.01,
            "avg_hold_hours": 1.0,
            "win_rate": 1.0,
            "total_trades": 1,
            "long_trades": 1,
            "short_trades": 0,
            "stop_triggers": 0,
            "exit_reasons": {},
            "canonical_chain_bound": True,
            "classic_bypass": False,
            "entry_side_other": 0,
        },
        {
            "gross_pnl": 200.0,
            "net_pnl": 200.0,
            "fees": 0.0,
            "slippage_drag": 0.0,
            "cost_drag": 0.0,
            "net_return": 0.02,
            "max_drawdown": -0.02,
            "avg_hold_hours": 2.0,
            "win_rate": 1.0,
            "total_trades": 1,
            "long_trades": 0,
            "short_trades": 1,
            "stop_triggers": 0,
            "exit_reasons": {},
            "canonical_chain_bound": True,
            "classic_bypass": False,
            "entry_side_other": 0,
        },
    ]
    agg = harness._aggregate_rows(rows)
    # Equal-capital proxy: 300 / (2 * 10000) = 0.015 — not 0.01+0.02=0.03.
    assert abs(float(agg["net_return"]) - 0.015) < 1e-12
    assert agg["net_return_sum_instrument_returns_forensic"] == 0.03
    assert agg["sharpe"] == harness.NA
    assert agg["cost_application"] == "NOT_APPLIED"


def test_dataset_manifest_documents_period_blocker(harness) -> None:
    if not harness.PANEL_MANIFEST.is_file():
        pytest.skip("panel manifest archive not mounted")
    man = harness._dataset_manifest()
    assert man["longer_period_than_prior_sample_available"] is False
    assert "NO_LONGER_CHRONOLOGICAL" in man["period_extension_blocker"]
    assert man["bitcoin_excluded"] is True
    assert man["okx_linear_usdt_futures_only"] is True
    assert man["btc_in_binding"] is False
