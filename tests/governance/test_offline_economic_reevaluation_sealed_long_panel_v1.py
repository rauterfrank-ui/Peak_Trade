"""Contract tests for sealed long-panel offline economic reevaluation harness.

Does not execute the full 65-member panel. Validates harness markers,
chain-binding proof, classification fail-closed rules, and evidence path hygiene.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_EVIDENCE = _REPO / "docs/evidence/offline_economic_reevaluation_sealed_long_panel_v1"
_HARNESS = _EVIDENCE / "economic_reevaluation_probe_v1.py"

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
        "offline_economic_reevaluation_sealed_long_panel_probe_v1", _HARNESS
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
    assert harness.DATASET_ID.endswith("chrono_3y_v1")
    assert harness.CLASS_PASS == "PASS_ECONOMIC_EVIDENCE_ONLY"
    assert harness.CLASS_INVALID == "INVALID_MEASUREMENT"


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


def test_classification_invalid_measurement(harness) -> None:
    klass, status, rationale = harness.classify_economic(
        period_extension_available=True,
        agg={
            "total_trades": 40,
            "net_return": 0.02,
            "profit_factor": 1.2,
            "cost_application": "NOT_APPLIED",
            "economic_measurement_valid": False,
        },
        walk_forward_rows=[],
        stress_rows=[],
    )
    assert klass == harness.CLASS_INVALID
    assert status == "FAIL"
    assert "INVALID_MEASUREMENT" in rationale


def test_classification_fail_economic(harness) -> None:
    klass, status, rationale = harness.classify_economic(
        period_extension_available=True,
        agg={
            "total_trades": 40,
            "net_return": -0.12,
            "profit_factor": 0.4,
            "cost_application": "APPLIED",
            "ledger_reconciliation": "PASS",
            "equity_reconciliation": "PASS",
            "economic_measurement_valid": True,
        },
        walk_forward_rows=[
            {"net_return": -0.04},
            {"net_return": -0.03},
            {"net_return": -0.05},
        ],
        stress_rows=[{"net_return": -0.15}],
    )
    assert klass == harness.CLASS_FAIL
    assert rationale


def test_classification_unstable_on_fold_sign_flip(harness) -> None:
    klass, status, _ = harness.classify_economic(
        period_extension_available=True,
        agg={
            "total_trades": 50,
            "net_return": 0.02,
            "profit_factor": 1.2,
            "cost_application": "APPLIED",
            "ledger_reconciliation": "PASS",
            "equity_reconciliation": "PASS",
            "economic_measurement_valid": True,
        },
        walk_forward_rows=[
            {"net_return": 0.05},
            {"net_return": -0.04},
            {"net_return": 0.03},
        ],
        stress_rows=[{"net_return": 0.01}],
    )
    assert klass == harness.CLASS_UNSTABLE
    assert status == "PARTIAL"


def test_evidence_pack_paths_exist() -> None:
    assert (_EVIDENCE / "shared_portfolio_equity_research_v1.py").is_file()
    assert (_EVIDENCE / "materialize_sealed_long_panel_bars_v1.py").is_file()
    assert "PROMOTION_ELIGIBLE" not in _HARNESS.read_text(encoding="utf-8") or (
        "promotion_eligible" in _HARNESS.read_text(encoding="utf-8").lower()
    )
