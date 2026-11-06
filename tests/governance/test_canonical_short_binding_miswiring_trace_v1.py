"""Contract tests for non-authoritative SHORT binding miswiring audit harness."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_HARNESS = (
    _REPO
    / "docs/evidence/canonical_short_binding_miswiring_trace_v1/short_binding_miswiring_harness_v1.py"
)
_EVIDENCE = _HARNESS.parent


def _load_harness():
    assert _HARNESS.is_file(), f"missing harness: {_HARNESS}"
    spec = importlib.util.spec_from_file_location(
        "canonical_short_binding_miswiring_trace_v1", _HARNESS
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


def test_harness_not_under_src() -> None:
    rel = str(_HARNESS.relative_to(_REPO))
    assert rel.startswith("docs/evidence/")


def test_static_binding_proof(harness) -> None:
    proof = harness.prove_static_binding()
    # Post-repair: MV2 wiring binds short-capable pipeline consumer.
    assert proof["wiring_use_execution_pipeline_true_count"] >= 2
    assert proof["wiring_use_execution_pipeline_false_count"] == 0
    assert proof["honor_mapped_short_entry_bound"] is True
    assert proof["engine_default_use_execution_pipeline"] is True
    assert proof["map_enter_short_to_minus_one"] is True
    assert proof["pipeline_has_is_entry_short"] is True
    assert proof["wiring_calls_integrated_replay"] is True


def test_all_scenarios_pass(scenario_results) -> None:
    failed = [s.scenario_id for s in scenario_results if not s.scenario_pass]
    assert failed == []
    assert len(scenario_results) == 19


def test_short_canonical_zero_trades(scenario_results) -> None:
    # Explicit legacy engine (use_pipeline=False) still no-ops flat -1.
    s05 = next(s for s in scenario_results if s.scenario_id == "S05")
    assert s05.trade_count == 0
    assert s05.final_classification == "CONTRACT_CAPABILITY_MISMATCH"


def test_pipeline_short_bound_on_mv2_path(scenario_results) -> None:
    s17 = next(s for s in scenario_results if s.scenario_id == "S17")
    assert s17.trade_count >= 1
    assert s17.final_classification == "HEALTHY_PATH"


def test_entry_side_none_fail_closed(scenario_results) -> None:
    s01 = next(s for s in scenario_results if s.scenario_id == "S01")
    assert s01.entry_side == "NONE"
    assert s01.emitted_execution_intent is None


def test_write_artifacts(harness, scenario_results, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(harness, "EVIDENCE", tmp_path)
    paths = harness.write_artifacts(scenario_results)
    for name in (
        "scenario_results.json",
        "canonical_binding_matrix.json",
        "long_short_call_graph.json",
        "consumer_capability_matrix.json",
        "blocker_classification.json",
        "first_divergence_analysis.json",
        "invariants.json",
    ):
        assert (tmp_path / name).is_file() or name in {Path(p).name for p in paths}
        json.loads((tmp_path / name).read_text(encoding="utf-8"))


def test_evidence_json_parse_when_present() -> None:
    required = [
        "scenario_results.json",
        "canonical_binding_matrix.json",
        "long_short_call_graph.json",
        "consumer_capability_matrix.json",
        "binding_decision_trace.json",
        "invariants.json",
        "blocker_classification.json",
        "first_divergence_analysis.json",
        "legacy_bypass_inventory.json",
        "manifest.json",
    ]
    for name in required:
        path = _EVIDENCE / name
        if not path.is_file():
            pytest.skip(f"evidence artifact not yet materialized: {name}")
        json.loads(path.read_text(encoding="utf-8"))
