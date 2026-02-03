from __future__ import annotations

import pytest

from src.infra.escalation.network_gate import ensure_may_use_network_escalation


def test_allow_network_false_is_ok() -> None:
    ensure_may_use_network_escalation(allow_network=False)


def test_allow_network_true_is_blocked_by_default() -> None:
    with pytest.raises(RuntimeError, match="Network escalation blocked"):
        ensure_may_use_network_escalation(allow_network=True, context="pagerduty")
