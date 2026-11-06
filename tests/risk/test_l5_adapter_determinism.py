"""L5 adapter: same facts => same decision + same reason_codes ordering (Runbook K6)."""

from __future__ import annotations

import pytest

from src.risk.cmes import l5_decision_from_facts, L5Decision


def test_same_facts_same_decision() -> None:
    facts = {
        "risk_score": 0.0,
        "risk_decision": "ALLOW",
        "risk_reason_codes": [],
        "no_trade_triggered": False,
        "no_trade_trigger_ids": [],
        "strategy_state": "ENABLED",
        "data_quality_flags": [],
    }
    d1 = l5_decision_from_facts(facts)
    d2 = l5_decision_from_facts(facts)
    assert d1.allow == d2.allow
    assert d1.reason_codes == d2.reason_codes


def test_reason_codes_sorted_deterministic() -> None:
    facts = {
        "risk_score": 10.0,
        "risk_decision": "REDUCE",
        "risk_reason_codes": ["C", "A", "B"],
        "no_trade_triggered": False,
        "no_trade_trigger_ids": [],
        "strategy_state": "ENABLED",
        "data_quality_flags": [],
    }
    d = l5_decision_from_facts(facts)
    assert d.reason_codes == sorted(d.reason_codes)
    assert d.allow is False


def test_block_when_no_trade_triggered() -> None:
    facts = {
        "risk_score": 0.0,
        "risk_decision": "ALLOW",
        "risk_reason_codes": [],
        "no_trade_triggered": True,
        "no_trade_trigger_ids": ["KILL_SWITCH"],
        "strategy_state": "ENABLED",
        "data_quality_flags": [],
    }
    d = l5_decision_from_facts(facts)
    assert d.allow is False
    assert "KILL_SWITCH" in d.reason_codes


def test_block_when_strategy_disabled() -> None:
    facts = {
        "risk_score": 0.0,
        "risk_decision": "ALLOW",
        "risk_reason_codes": [],
        "no_trade_triggered": False,
        "no_trade_trigger_ids": [],
        "strategy_state": "DISABLED",
        "data_quality_flags": [],
    }
    d = l5_decision_from_facts(facts)
    assert d.allow is False


def test_invalid_facts_fail_closed() -> None:
    invalid = {"risk_decision": "ALLOW"}  # missing keys
    d = l5_decision_from_facts(invalid)
    assert d.allow is False
    assert "FACTS_INVALID" in d.reason_codes
