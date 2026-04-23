# tests/trading/master_v2/test_scenario_matrix_v1.py
from __future__ import annotations

import pytest

from trading.master_v2.decision_packet_critic_v1 import critique_master_v2_decision_packet_v1
from trading.master_v2.decision_packet_replay_v1 import decision_packet_from_snapshot_v1
from trading.master_v2.decision_packet_snapshot_v1 import validate_decision_packet_snapshot_v1
from trading.master_v2.decision_packet_v1 import validate_master_v2_decision_packet_v1
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_MATRIX_LAYER_VERSION,
    MasterV2ScenarioCaseV1,
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_LIVE_AUTH_MISSING_ACK,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
    SCENARIO_RISK_BLOCKED,
    SCENARIO_SAFETY_BLOCKED,
    build_master_v2_scenario_matrix_v1,
    get_master_v2_scenario_case_v1,
    scenario_matrix_all_names_v1,
)


def test_matrix_version():
    assert SCENARIO_MATRIX_LAYER_VERSION == "v1"


def test_matrix_names_stable():
    m = build_master_v2_scenario_matrix_v1()
    assert scenario_matrix_all_names_v1() == frozenset(m.keys())
    assert len(m) == 5


def test_get_unknown_raises():
    with pytest.raises(KeyError, match="unbekanntes szenario"):
        get_master_v2_scenario_case_v1("no_such")


def _assert_case_matches_contracts(c: MasterV2ScenarioCaseV1) -> None:
    v = validate_master_v2_decision_packet_v1(c.packet)
    assert v.ok == c.expected.validate_ok
    for s in c.expected.expect_validate_reason_substrings:
        assert any(s in r for r in v.reason_codes), (c.name, v.reason_codes)

    cr = critique_master_v2_decision_packet_v1(c.packet)
    assert cr.has_error_findings == c.expected.critic_has_error_findings
    found = {f.code for f in cr.findings}
    for code in c.expected.expect_critic_codes:
        assert code in found, (c.name, found)
    if c.expected.expect_critic_warning_layer_missing:
        assert "LAYER_MISSING_OPTIONAL" in found

    if c.snapshot is not None:
        validate_decision_packet_snapshot_v1(c.snapshot)
        p2 = decision_packet_from_snapshot_v1(c.snapshot)
        assert p2 == c.packet


@pytest.mark.parametrize(
    "name",
    (
        SCENARIO_HAPPY_LIVE_GATED,
        SCENARIO_SAFETY_BLOCKED,
        SCENARIO_RISK_BLOCKED,
        SCENARIO_LIVE_AUTH_MISSING_ACK,
        SCENARIO_OPTIONAL_LAYERS_MISSING,
    ),
)
def test_each_scenario_matches_expectations(name: str):
    c = get_master_v2_scenario_case_v1(name)
    _assert_case_matches_contracts(c)


def test_matrix_idempotent():
    a = build_master_v2_scenario_matrix_v1()
    b = build_master_v2_scenario_matrix_v1()
    assert list(a.keys()) == list(b.keys())
