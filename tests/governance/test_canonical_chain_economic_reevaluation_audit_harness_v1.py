"""Contract tests for the non-authoritative economic reevaluation audit harness.

Does not execute the full offline fixture panel. Validates harness markers,
canonical-chain binding proof, and classification fail-closed rules.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_HARNESS = (
    _REPO
    / "docs/evidence/canonical_chain_economic_reevaluation_v1/economic_reevaluation_probe_v1.py"
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
        "canonical_chain_economic_reevaluation_probe_v1", _HARNESS
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
    assert "LIVE_AUTHORIZED" not in src or 'live_authorized": False' in src.replace(" ", "")
    assert "run_mv2_research_backtest_wiring_v1" in src
    assert "observational_bar_hook" in src


def test_harness_does_not_live_in_productive_owners() -> None:
    rel = str(_HARNESS.relative_to(_REPO))
    assert rel.startswith("docs/evidence/")
    for g in PRODUCTIVE_GLOBS:
        assert not rel.startswith(g)


def test_chain_binding_proof_static(harness) -> None:
    proof = harness.prove_chain_binding_static()
    assert proof["uses_run_mv2_research_backtest_wiring_v1"] is True
    assert proof["uses_integrated_offline_replay"] is True
    assert proof["wiring_calls_replay"] is True
    assert proof["replay_calls_transition"] is True
    assert proof["transition_state_owner_present"] is True
    assert proof["composition_owner_present"] is True
    assert proof["canonical_engine_signal_source"] == "mv2_decision_replay_series"
    assert proof["non_authoritative_marker"] is True


def test_classification_low_sample_is_e(harness) -> None:
    klass, boundary, rationale = harness._classify_instrument(
        {
            "canonical_chain_bound": True,
            "value_loss": False,
            "classic_bypass": False,
            "second_authority": False,
            "total_trades": 1,
            "entry_intents": 9,
            "exit_intents": 2492,
            "bull_candidate_count": 100,
            "bear_candidate_count": 50,
            "noop_count": 10,
            "bars_hooked": 2953,
            "composition_selected_nonzero": 10,
        }
    )
    assert klass == harness.CLASS_E
    assert "sample" in boundary or "insufficiency" in boundary or "exit" in boundary
    assert rationale


def test_classification_chain_blocker_is_a(harness) -> None:
    klass, boundary, _ = harness._classify_instrument(
        {
            "canonical_chain_bound": False,
            "value_loss": False,
            "classic_bypass": False,
            "second_authority": False,
            "total_trades": 0,
            "entry_intents": 0,
            "exit_intents": 0,
            "bull_candidate_count": 0,
            "bear_candidate_count": 0,
            "noop_count": 0,
            "bars_hooked": 0,
            "composition_selected_nonzero": 0,
        }
    )
    assert klass == harness.CLASS_A
    assert boundary


def test_classification_negative_gross_is_g(harness) -> None:
    klass, boundary, _ = harness._classify_instrument(
        {
            "canonical_chain_bound": True,
            "value_loss": False,
            "classic_bypass": False,
            "second_authority": False,
            "total_trades": 25,
            "entry_intents": 30,
            "exit_intents": 40,
            "bull_candidate_count": 100,
            "bear_candidate_count": 100,
            "noop_count": 10,
            "bars_hooked": 3000,
            "composition_selected_nonzero": 20,
            "gross_pnl": -12.5,
            "net_pnl": -20.0,
        }
    )
    assert klass == harness.CLASS_G
    assert "gross" in boundary


def test_matrix_instruments_are_canonical_panel_members(harness) -> None:
    symbols = [m[0] for m in harness.MATRIX]
    assert symbols == ["1INCH", "BONK", "AVAX", "SOL"]
    for _, member_id, _ in harness.MATRIX:
        assert member_id.startswith("okx:linear_perpetual:")
        assert member_id.endswith(":USDT:USDT:perp")
