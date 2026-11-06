"""Bounded closure: threshold enforcement → MV2+DP → offline order intent."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.governance.f1_m9_bounded_threshold_enforcement_mv2_consumer_v1 import (
    THRESHOLD_ENFORCEMENT_AUTHORIZED,
    threshold_enforcement_authorized_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1 import (
    DECISION_CONFIG,
    EARLIEST_BLOCKER_EXTERNAL,
    STATUS_CLOSURE_COMPLETE,
    evaluate_f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    initialize_empty_threshold_revocation_ledger_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)
from src.trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    NUMERIC_MAX_AGE_DECIDED,
)
from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
    _context,
    _valid_estimate,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    build_canonical_volatility_estimate_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _apply_ledger_paths(tmp_path: Path) -> F1M9ProductiveApplyLedgerPathsV1:
    rev = tmp_path / "apply_revocation.jsonl"
    initialize_empty_revocation_ledger_v1(rev)
    return F1M9ProductiveApplyLedgerPathsV1(
        apply_ledger_path=tmp_path / "apply.jsonl",
        revocation_ledger_path=rev,
    )


def _threshold_ledger_paths(tmp_path: Path) -> F1M9ThresholdValueAuthorizationLedgerPathsV1:
    rev = tmp_path / "threshold_revocation.jsonl"
    initialize_empty_threshold_revocation_ledger_v1(rev)
    return F1M9ThresholdValueAuthorizationLedgerPathsV1(
        threshold_ledger_path=tmp_path / "threshold.jsonl",
        threshold_revocation_ledger_path=rev,
    )


def _fresh_pair():
    ctx = _context()
    estimate = _valid_estimate()
    return ctx, estimate


def _stale_pair():
    ctx = _context()
    estimate = build_canonical_volatility_estimate_v1(
        value=0.004321,
        observation_count=61,
        as_of_event_time=datetime(2026, 6, 30, 10, 0, tzinfo=timezone.utc),
        fallback_used=False,
        source_digest="b" * 64,
    )
    return ctx, estimate


def test_decision_and_global_invariants() -> None:
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["workpackage_id"] == "THRESHOLD_ENFORCEMENT_TO_TRADING_ORDER_EFFECT_CLOSURE_V1"
    assert decision["threshold_enforcement_authorized"] is True
    assert decision["external_order_effect_authorized"] is False
    assert decision["new_authority_introduced"] is False
    assert threshold_enforcement_authorized_v1(repo_root=REPO_ROOT) is True
    assert THRESHOLD_ENFORCEMENT_AUTHORIZED is True
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert NUMERIC_MAX_AGE_DECIDED is False


def test_bounded_closure_complete_through_order_intent(tmp_path: Path) -> None:
    fresh_ctx, fresh_est = _fresh_pair()
    stale_ctx, stale_est = _stale_pair()
    result = evaluate_f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1(
        repo_root=REPO_ROOT,
        apply_ledger_paths=_apply_ledger_paths(tmp_path),
        threshold_ledger_paths=_threshold_ledger_paths(tmp_path),
        market_context_fresh=fresh_ctx,
        market_context_stale=stale_ctx,
        estimate_fresh=fresh_est,
        estimate_stale=stale_est,
    )
    assert result.closure_status == STATUS_CLOSURE_COMPLETE
    assert result.handoff_complete is True
    assert result.threshold_value_authorized is True
    assert result.threshold_enforcement_authorized is True
    assert result.threshold_enforcement_occurred is True
    assert result.trading_decision_effect_occurred is True
    assert result.order_intent_effect_occurred is True
    assert result.external_order_effect_authorized is False
    assert result.earliest_blocker == EARLIEST_BLOCKER_EXTERNAL
    assert result.alpha_after_enforcement is True
    assert result.order_intent_authority_effect == "NONE"
