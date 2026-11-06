# src/trading/master_v2/local_evaluator_scenarios_v1.py
"""
Master V2 — scenario harness: Scenario-Matrix gegen local_evaluator (Dry-Flow) verdrahten.

Kein I/O, keine neue Business-Semantik: nur Ablauf + Checks gegen
ScenarioExpectedOutcomeV1.
"""

from __future__ import annotations

from typing import Dict

from .decision_packet_replay_v1 import decision_packet_from_snapshot_v1
from .decision_packet_snapshot_v1 import validate_decision_packet_snapshot_v1
from .decision_packet_v1 import validate_master_v2_decision_packet_v1
from .local_evaluator_v1 import (
    LOCAL_FLOW_LAYER_VERSION,
    MasterV2LocalFlowResultV1,
    evaluate_master_v2_local_flow_v1,
)
from .scenario_matrix_v1 import (
    MasterV2ScenarioCaseV1,
    build_master_v2_scenario_matrix_v1,
    get_master_v2_scenario_case_v1,
)

SCENARIO_HARNESS_LAYER_VERSION = "v1"


def run_master_v2_scenario_case_v1(
    name: str,
) -> MasterV2LocalFlowResultV1:
    """
    Baut die gleiche Paket-Assembly aus der Szenario-Definition like die Matrix
    (packet-Felder) und wertet mit dem lokalen Evaluator aus. `with_snapshot` ist
    True genau dann, wenn die Matrix fuer den Fall ein Snapshot-Objekt haelt.
    """
    c = get_master_v2_scenario_case_v1(name)
    return _local_flow_for_scenario_case(c)


def _local_flow_for_scenario_case(c: MasterV2ScenarioCaseV1) -> MasterV2LocalFlowResultV1:
    p = c.packet
    with_snap = c.snapshot is not None
    return evaluate_master_v2_local_flow_v1(
        p.correlation_id,
        p.staged,
        universe=p.universe,
        doubleplay=p.doubleplay,
        scope_envelope=p.scope_envelope,
        risk_cap=p.risk_cap,
        safety=p.safety,
        with_snapshot=with_snap,
    )


def run_master_v2_scenario_matrix_v1() -> Dict[str, MasterV2LocalFlowResultV1]:
    m = build_master_v2_scenario_matrix_v1()
    return {k: _local_flow_for_scenario_case(c) for k, c in m.items()}


def assert_master_v2_scenario_harness_outcome_v1(
    c: MasterV2ScenarioCaseV1,
    r: MasterV2LocalFlowResultV1,
) -> None:
    """
    Prueft: Evaluator-`flow_ok` == Matrix-`validate_ok`, plus dieselben stabilen
    Validate-/Critic-Erwartungen wie die kanonische Matrix, optional Snapshot-Replay.
    """
    exp = c.expected
    assert r.layer_version == LOCAL_FLOW_LAYER_VERSION, c.name
    assert r.rejection_reason is None, (c.name, r.rejection_reason)
    assert r.flow_ok is exp.validate_ok, (c.name, r.flow_ok, exp.validate_ok)
    assert r.packet is not None, c.name
    assert r.critic_report is not None, c.name
    assert r.validation is not None, c.name
    p = c.packet
    assert r.packet == p, c.name

    v = r.validation
    assert v.ok is exp.validate_ok, c.name
    for s in exp.expect_validate_reason_substrings:
        assert any(s in code for code in v.reason_codes), (c.name, v.reason_codes)

    cr = r.critic_report
    assert cr.has_error_findings is exp.critic_has_error_findings, (c.name, cr)
    found = {f.code for f in cr.findings}
    for code in exp.expect_critic_codes:
        assert code in found, (c.name, found)
    if exp.expect_critic_warning_layer_missing:
        assert "LAYER_MISSING_OPTIONAL" in found, c.name

    if c.snapshot is not None:
        assert r.snapshot is not None, c.name
        assert r.snapshot == c.snapshot, c.name
        validate_decision_packet_snapshot_v1(c.snapshot)
        validate_decision_packet_snapshot_v1(r.snapshot)
        d_a = decision_packet_from_snapshot_v1(c.snapshot)
        d_b = decision_packet_from_snapshot_v1(r.snapshot)
        assert d_a == p and d_b == p, c.name
    else:
        assert r.snapshot is None, c.name

    v_direct = validate_master_v2_decision_packet_v1(p)
    assert v_direct.ok is v.ok and v_direct.reason_codes == v.reason_codes, c.name
