"""Fixtures: D26 native baseline evidence for D27 test-entry lifecycle tests."""

from __future__ import annotations

from typing import Any

from src.governance.platform_unified_native_vs_candidate_baseline_evidence_v1 import (
    classify_canonical_trading_decision_evidence_v1,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _replay_input
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)

_CACHED_NATIVE_BASELINE: dict[str, Any] | None = None


def build_fixture_native_baseline_evidence_v1() -> dict[str, Any]:
    global _CACHED_NATIVE_BASELINE
    if _CACHED_NATIVE_BASELINE is not None:
        return dict(_CACHED_NATIVE_BASELINE)
    replay = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    record = classify_canonical_trading_decision_evidence_v1(replay.evidence)
    _CACHED_NATIVE_BASELINE = record.to_dict()
    return dict(_CACHED_NATIVE_BASELINE)
