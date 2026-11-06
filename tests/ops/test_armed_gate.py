from __future__ import annotations

import pytest
from src.ops.gates.armed_gate import ArmedGate, ArmedState


def test_token_roundtrip_ok():
    g = ArmedGate(secret=b"unit-test-secret", token_ttl_seconds=10)
    now = 1_700_000_000
    tok = g.issue_token(now)
    assert g.verify_token(tok, now) is True
    assert g.verify_token(tok, now + 9) is True


def test_token_expired():
    g = ArmedGate(secret=b"unit-test-secret", token_ttl_seconds=10)
    now = 1_700_000_000
    tok = g.issue_token(now)
    assert g.verify_token(tok, now + 11) is False


def test_arm_requires_enabled_and_valid_token():
    g = ArmedGate(secret=b"unit-test-secret", token_ttl_seconds=10)
    now = 1_700_000_000
    tok = g.issue_token(now)

    s0 = ArmedState(enabled=False, armed=False, armed_since_epoch=None, token_issued_epoch=None)
    s1 = g.arm(s0, tok, now)
    assert s1.armed is False

    s2 = ArmedState(enabled=True, armed=False, armed_since_epoch=None, token_issued_epoch=None)
    s3 = g.arm(s2, "bad.token", now)
    assert s3.armed is False

    s4 = g.arm(s2, tok, now)
    assert s4.armed is True
    assert s4.armed_since_epoch == now


def test_require_armed_blocks():
    s = ArmedState(enabled=True, armed=False, armed_since_epoch=None, token_issued_epoch=None)
    with pytest.raises(RuntimeError):
        ArmedGate.require_armed(s)
