"""Contract + scenario tests for non-authoritative fill/roundtrip ledger boundary trace."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_HARNESS = (
    _REPO
    / "docs/evidence/canonical_fill_roundtrip_ledger_boundary_trace_v1/boundary_trace_harness_v1.py"
)
_EVIDENCE = _HARNESS.parent


def _load_harness():
    assert _HARNESS.is_file(), f"missing harness: {_HARNESS}"
    spec = importlib.util.spec_from_file_location(
        "canonical_fill_roundtrip_ledger_boundary_trace_v1", _HARNESS
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def harness():
    return _load_harness()


@pytest.fixture(scope="module")
def scenario_results(harness):
    return harness.run_all_scenarios()


def test_harness_is_non_authoritative(harness) -> None:
    src = _HARNESS.read_text(encoding="utf-8")
    assert "NON-AUTHORITATIVE" in src
    assert harness.AUDIT_AUTHORITY_EFFECT == "NONE"
    assert harness.AUDIT_RUNTIME_EFFECT == "NONE"
    assert harness.AUDIT_LIVE_AUTHORIZED is False
    assert harness.AUDIT_ORDERS is False
    assert harness.AUDIT_RUNTIME_BRIDGE_STATUS == "BOUND_NOT_ACTIVATED"
    assert "map_decision_evidence_to_position_signal_v1" in src
    assert "BacktestEngine" in src
    assert "materialize_trade_ledger_rows_v0" in src


def test_harness_not_under_productive_src() -> None:
    rel = str(_HARNESS.relative_to(_REPO))
    assert rel.startswith("docs/evidence/")
    assert not rel.startswith("src/")


def test_chain_binding_proof_static(harness) -> None:
    proof = harness.prove_chain_binding_static()
    assert proof["uses_map_decision_evidence_to_position_signal_v1"] is True
    assert proof["uses_backtest_engine"] is True
    assert proof["uses_materialize_trade_ledger_rows_v0"] is True
    assert proof["legacy_opens_on_signal_plus_one"] is True
    assert proof["legacy_exits_on_signal_minus_one_only_if_open"] is True
    assert proof["partial_reduction_supported_flag_false"] is True
    assert proof["non_authoritative_marker"] is True
    assert proof["canonical_engine_signal_source"] == "mv2_decision_replay_series"


def test_all_scenarios_pass(scenario_results) -> None:
    failed = [s.scenario_id for s in scenario_results if not s.scenario_pass]
    assert failed == [], f"failed scenarios: {failed}"
    assert len(scenario_results) == 12


def test_scenario_a_long_completes(scenario_results) -> None:
    a = next(s for s in scenario_results if s.scenario_id == "A")
    assert a.funnel.completed_roundtrips == 1
    assert a.funnel.ledger_trades == 1
    assert a.first_loss_boundary == "NONE"


def test_scenario_b_short_first_loss_at_fill_ledger(scenario_results) -> None:
    b = next(s for s in scenario_results if s.scenario_id == "B")
    assert b.funnel.fills == 0
    assert b.funnel.completed_roundtrips == 0
    assert b.first_loss_boundary == "backtest_engine_fill_or_roundtrip_ledger"
    assert b.mechanical_defect is False
    assert b.blocker_class == "E"


def test_scenario_c_entry_side_none_fail_closed(scenario_results) -> None:
    c = next(s for s in scenario_results if s.scenario_id == "C")
    assert c.funnel.completed_roundtrips == 0
    assert c.side_breakdown["entry_side"] == "NONE"
    assert c.side_breakdown["directional_cycle"] is None


def test_scenario_d_sizing_reject(scenario_results) -> None:
    d = next(s for s in scenario_results if s.scenario_id == "D")
    assert d.funnel.fills == 0
    assert d.rejection_reasons.get("position_sizing_reject", 0) >= 1


def test_write_artifacts_roundtrip(harness, scenario_results, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(harness, "EVIDENCE", tmp_path)
    paths = harness.write_evidence_artifacts(scenario_results)
    for key in (
        "representative_traces",
        "funnel_counts",
        "rejection_reasons",
        "side_breakdown",
        "instrument_breakdown",
        "first_loss_matrix",
    ):
        assert paths[key].is_file()
        json.loads(paths[key].read_text(encoding="utf-8"))


def test_evidence_json_artifacts_parse_when_present() -> None:
    required = [
        "representative_traces.json",
        "funnel_counts.json",
        "rejection_reasons.json",
        "side_breakdown.json",
        "instrument_breakdown.json",
        "first_loss_matrix.json",
        "boundary_invariants.json",
    ]
    for name in required:
        path = _EVIDENCE / name
        if not path.is_file():
            pytest.skip(f"evidence artifact not yet materialized: {name}")
        json.loads(path.read_text(encoding="utf-8"))
