"""Unit tests: CMES facts canonicalization and validation (Runbook K1)."""

from __future__ import annotations

import pytest

from src.risk.cmes import (
    CMES_FACT_KEYS,
    canonicalize_facts,
    default_cmes_facts,
    validate_facts,
)
from src.risk.cmes.facts import CMESFactsValidationError


def test_required_keys_present_after_canonicalize() -> None:
    out = canonicalize_facts(default_cmes_facts())
    for k in CMES_FACT_KEYS:
        assert k in out, f"missing key {k}"


def test_sorted_lists_canonical() -> None:
    raw = {
        "risk_score": 0.0,
        "risk_decision": "ALLOW",
        "risk_reason_codes": ["B", "A", "C"],
        "no_trade_triggered": False,
        "no_trade_trigger_ids": ["Z", "Y"],
        "strategy_state": "ENABLED",
        "data_quality_flags": ["FLAG_B", "FLAG_A"],
    }
    out = canonicalize_facts(raw)
    assert out["risk_reason_codes"] == ["A", "B", "C"]
    assert out["no_trade_trigger_ids"] == ["Y", "Z"]
    assert out["data_quality_flags"] == ["FLAG_A", "FLAG_B"]


def test_invalid_enum_rejected() -> None:
    raw = dict(default_cmes_facts())
    raw["risk_decision"] = "INVALID"
    with pytest.raises(CMESFactsValidationError, match="invalid enum"):
        canonicalize_facts(raw)

    raw2 = dict(default_cmes_facts())
    raw2["strategy_state"] = "UNKNOWN"
    with pytest.raises(CMESFactsValidationError, match="invalid enum"):
        canonicalize_facts(raw2)


def test_invalid_risk_score_rejected() -> None:
    raw = dict(default_cmes_facts())
    raw["risk_score"] = 150.0
    with pytest.raises(CMESFactsValidationError, match="risk_score"):
        canonicalize_facts(raw)

    raw["risk_score"] = "not_a_number"
    with pytest.raises(CMESFactsValidationError, match="risk_score"):
        canonicalize_facts(raw)


def test_validate_facts_raises_on_missing_key() -> None:
    with pytest.raises(CMESFactsValidationError, match="missing required"):
        validate_facts({})


def test_validate_facts_accepts_canonical() -> None:
    validate_facts(default_cmes_facts())
    validate_facts(canonicalize_facts(default_cmes_facts()))


def test_default_facts_are_canonical() -> None:
    d = default_cmes_facts()
    validate_facts(d)
    assert d["risk_decision"] == "ALLOW"
    assert d["strategy_state"] == "ENABLED"
    assert d["risk_reason_codes"] == []
    assert d["no_trade_triggered"] is False
