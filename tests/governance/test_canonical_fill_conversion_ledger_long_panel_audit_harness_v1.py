"""Contract tests for non-authoritative fill-conversion long-panel audit harness."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_HARNESS = (
    _REPO
    / "docs/evidence/canonical_fill_conversion_ledger_long_panel_v1/fill_conversion_probe_v1.py"
)


def _load_harness():
    assert _HARNESS.is_file(), f"missing harness: {_HARNESS}"
    spec = importlib.util.spec_from_file_location("canonical_fill_conversion_probe_v1", _HARNESS)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def harness():
    return _load_harness()


def test_harness_is_non_authoritative(harness) -> None:
    src = _HARNESS.read_text(encoding="utf-8")
    assert "NON-AUTHORITATIVE" in src
    assert harness.AUDIT_AUTHORITY_EFFECT == "NONE"
    assert harness.AUDIT_RUNTIME_EFFECT == "NONE"
    assert "run_mv2_research_backtest_wiring_v1" in src
    assert "map_decision_evidence_to_position_signal_v1" in src


def test_harness_not_under_productive_or_boundary_research_tests() -> None:
    rel = str(_HARNESS.relative_to(_REPO))
    assert rel.startswith("docs/evidence/")
    assert not rel.startswith("tests/research/")
    assert not rel.startswith("src/")


def test_chain_binding_proof_static(harness) -> None:
    proof = harness.prove_chain_binding_static()
    assert proof["uses_run_mv2_research_backtest_wiring_v1"] is True
    assert proof["uses_map_decision_evidence_to_position_signal_v1"] is True
    assert proof["wiring_calls_replay"] is True
    assert proof["canonical_engine_signal_source"] == "mv2_decision_replay_series"
    assert proof["harness_forces_configured_strategy_bypass"] is False
    assert proof["non_authoritative_marker"] is True


def test_classify_map_drop_is_mechanical(harness) -> None:
    klass, boundary, mechanical = harness._classify_row(
        {
            "entry_intents": 5,
            "mapped_nonzero_on_enter_epochs": 3,
            "engine_nonzero_bars": 3,
            "total_trades": 0,
            "enter_map_mismatch_count": 2,
            "enter_engine_mismatch_count": 0,
            "funnel_engine_values_match": True,
        }
    )
    assert klass == harness.CLS_MAP_DROP
    assert "map_decision" in boundary
    assert mechanical is True


def test_classify_ledger_zero_not_mechanical_by_default(harness) -> None:
    klass, boundary, mechanical = harness._classify_row(
        {
            "entry_intents": 10,
            "mapped_nonzero_on_enter_epochs": 10,
            "engine_nonzero_bars": 10,
            "total_trades": 0,
            "enter_map_mismatch_count": 0,
            "enter_engine_mismatch_count": 0,
            "funnel_engine_values_match": True,
        }
    )
    assert klass == harness.CLS_LEDGER_ZERO
    assert mechanical is False
    assert "ledger" in boundary or "fill" in boundary


def test_panel_members_come_from_binding(harness) -> None:
    members = harness._panel_members()
    assert len(members) == 118
    assert all(m.startswith("okx:linear_perpetual:") for m in members)
