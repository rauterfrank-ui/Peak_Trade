"""Contract: canonical order intent boundary backtest state-file binding v0 (offline only)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.backtest.mv2_research_wiring_v1 import (
    CanonicalOrderIntentBacktestStateFileBindingConfigV1,
    CapitalRiskSizingBacktestStateFileBindingConfigV1,
    run_mv2_research_backtest_wiring_v1,
)
from src.governance.canonical_order_intent_v1 import (
    CONTRACT_VERSION as CANONICAL_ORDER_INTENT_CONTRACT_VERSION,
)
from src.governance.capital_risk_sizing_v1 import (
    CONTRACT_VERSION as CAPITAL_RISK_SIZING_CONTRACT_VERSION,
)
from trading.master_v2.canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0 import (
    CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
    CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    ORDER_INTENT_EFFECT_BOUND_OFFLINE,
    apply_backtest_canonical_order_intent_exposure_gate_v0,
    backtest_canonical_order_intent_state_file_binding_non_authority_ok_v0,
    bind_canonical_order_intent_boundary_backtest_state_file_evidence_v0,
    compute_backtest_state_file_digest_from_payload_v0,
    evaluate_backtest_canonical_order_intent_state_file_boundary_only_v0,
    parse_canonical_order_intent_backtest_state_file_v0,
    verify_canonical_order_intent_backtest_state_file_digest_v0,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    CANONICAL_ORDER_INTENT_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0 as sizing_digest,
    evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0,
    parse_capital_risk_sizing_backtest_state_file_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    NEXT_RECOMMENDED_SLICE,
    parity_surface_assessments_v0,
)
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg

REPO_ROOT = Path(__file__).resolve().parents[1]

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0.py",
    REPO_ROOT / "scripts/ops/run_backtest_canonical_order_intent_wiring_v0.py",
    REPO_ROOT / "tests/test_backtest_canonical_order_intent_wiring_v0.py",
)


def _scan_forbidden_imports(path: Path, forbidden_tokens: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in forbidden_tokens):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden_tokens):
                hits.append(node.module)
    return hits


def _sizing_state_file_payload(**kwargs: object) -> dict[str, object]:
    base = {
        "schema_version": CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "instrument_id": "inst-eth-usdt-perp",
        "reference_price": "3500",
        "protective_stop_price": "3400",
        "account_equity": "10000",
        "scope_capital_limit": "500",
        "per_trade_risk_limit": "25",
        "total_capital_limit": "500",
        "daily_loss_remaining_budget": "25",
        "current_reconciled_exposure": "0",
        "lot_size": "0.01",
        "minimum_quantity": "0.01",
        "maximum_quantity": "100",
        "minimum_notional": "5",
        "tick_size": "0.01",
        "capital_risk_sizing_owner_digest_ref": CAPITAL_RISK_SIZING_CONTRACT_VERSION,
        **kwargs,
    }
    digest = sizing_digest(base)
    return {**base, "state_file_digest_ref": digest}


def _order_intent_state_file_payload(**kwargs: object) -> dict[str, object]:
    base = {
        "schema_version": CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "instrument_id": "inst-eth-usdt-perp",
        "reference_price": "3500",
        "protective_stop_price": "3400",
        "account_equity": "10000",
        "scope_capital_limit": "500",
        "per_trade_risk_limit": "25",
        "total_capital_limit": "500",
        "daily_loss_remaining_budget": "25",
        "current_reconciled_exposure": "0",
        "lot_size": "0.01",
        "minimum_quantity": "0.01",
        "maximum_quantity": "100",
        "minimum_notional": "5",
        "tick_size": "0.01",
        "canonical_order_intent_owner_digest_ref": CANONICAL_ORDER_INTENT_CONTRACT_VERSION,
        **kwargs,
    }
    digest = compute_backtest_state_file_digest_from_payload_v0(base)
    return {**base, "state_file_digest_ref": digest}


def _sizing_record(**kwargs: object):
    return parse_capital_risk_sizing_backtest_state_file_v0(
        payload=_sizing_state_file_payload(**kwargs)
    )


def _order_intent_record(**kwargs: object):
    return parse_canonical_order_intent_backtest_state_file_v0(
        payload=_order_intent_state_file_payload(**kwargs)
    )


def _base_evidence(*, decision_outcome: str = DecisionOutcome.ENTER_LONG.value):
    return build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-canonical-order-intent-state-file-decision",
        replay_id="backtest-canonical-order-intent-state-file-replay",
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=1,
        composition_result_id="composition",
        entry_exit_policy_ref="policy",
        selected_side="long",
        decision_outcome=decision_outcome,
        reason_codes=("PASS",),
        decision_precedence_trace=("enter_long",),
        config_digest="config",
        implementation_digest="impl",
    )


def test_owner_constants_reuse_surface_i_adapter_v0() -> None:
    assert CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER.endswith(
        "canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0"
    )


def test_slice_sources_exclude_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "scheduler",
            "credentials",
            "live_runtime",
            "testnet",
            "shadow",
            "paper_lane",
            "risk_layer.kill_switch.core",
        }
    )
    for path in _FORBIDDEN_IMPORT_SCAN_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_valid_caps_bind_order_intent_provenance_v0() -> None:
    sizing_evidence = evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0(
        _sizing_record()
    )
    evidence = evaluate_backtest_canonical_order_intent_state_file_boundary_only_v0(
        _order_intent_record(),
        sizing_evidence=sizing_evidence,
    )
    assert evidence.order_intent_provenance_represented is True
    assert evidence.order_intent_ref
    assert evidence.order_intent_effect == ORDER_INTENT_EFFECT_BOUND_OFFLINE
    assert evidence.adapter_compatible is False
    assert apply_backtest_canonical_order_intent_exposure_gate_v0(1, evidence=evidence) == 1


def test_observe_decision_without_provenance_remains_non_executable_v0() -> None:
    sizing_evidence = evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0(
        _sizing_record(),
        decision_outcome=DecisionOutcome.OBSERVE.value,
    )
    evidence = evaluate_backtest_canonical_order_intent_state_file_boundary_only_v0(
        _order_intent_record(),
        sizing_evidence=sizing_evidence,
        decision_outcome=DecisionOutcome.OBSERVE.value,
    )
    assert evidence.order_intent_provenance_represented is False
    assert evidence.offline_binding.binding_applied is False
    assert apply_backtest_canonical_order_intent_exposure_gate_v0(1, evidence=evidence) == 0


def test_blocked_sizing_blocks_order_intent_exposure_v0() -> None:
    sizing_evidence = evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0(
        _sizing_record(daily_loss_remaining_budget="0")
    )
    evidence = evaluate_backtest_canonical_order_intent_state_file_boundary_only_v0(
        _order_intent_record(),
        sizing_evidence=sizing_evidence,
    )
    assert evidence.intent_outcome == "BLOCKED"
    assert apply_backtest_canonical_order_intent_exposure_gate_v0(1, evidence=evidence) == 0


def test_missing_owner_digest_fails_closed_v0() -> None:
    payload = _order_intent_state_file_payload()
    del payload["canonical_order_intent_owner_digest_ref"]
    with pytest.raises(ValueError, match="canonical_order_intent_owner_digest_ref_missing"):
        parse_canonical_order_intent_backtest_state_file_v0(payload=payload)


def test_corrupted_state_file_digest_fails_closed_v0() -> None:
    payload = _order_intent_state_file_payload()
    payload["state_file_digest_ref"] = "0" * 64
    with pytest.raises(
        ValueError, match="canonical_order_intent_backtest_state_file_digest_mismatch"
    ):
        parse_canonical_order_intent_backtest_state_file_v0(payload=payload)


def test_backtest_binding_uses_surface_i_adapter_not_duplicate_semantics_v0() -> None:
    sizing_evidence = evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0(
        _sizing_record(daily_loss_remaining_budget="0")
    )
    bound = bind_canonical_order_intent_boundary_backtest_state_file_evidence_v0(
        _base_evidence(decision_outcome=DecisionOutcome.ENTER_LONG.value),
        state_file=_order_intent_record(),
        sizing_evidence=sizing_evidence,
    )
    assert (
        bound.surface_i_adapter_owner_ref
        == CANONICAL_ORDER_INTENT_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
    )


def test_non_authority_invariants_v0() -> None:
    sizing_evidence = evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0(
        _sizing_record()
    )
    evidence = evaluate_backtest_canonical_order_intent_state_file_boundary_only_v0(
        _order_intent_record(),
        sizing_evidence=sizing_evidence,
    )
    assert evidence.runtime_authority is False
    assert evidence.orders_allowed is False
    assert evidence.credentials_used is False
    assert evidence.economic_evaluation is False
    assert evidence.adapter_compatible is False
    assert backtest_canonical_order_intent_state_file_binding_non_authority_ok_v0(evidence)


def test_parity_gap_assessment_surface_i_backtest_state_file_pass_v0() -> None:
    order_intent = next(item for item in parity_surface_assessments_v0() if item.surface_id == "I")
    assert order_intent.parity_status == "PASS"
    assert order_intent.missing_binding_if_any == ""
    assert "bind_canonical_order_intent_boundary_backtest_state_file_evidence_v0" in (
        order_intent.current_backtest_binding
    )
    assert NEXT_RECOMMENDED_SLICE == "FULL_CANONICAL_BACKTEST_BOUNDARY_CHAIN_REASSESSMENT_V0"


def test_mv2_research_wiring_binds_state_file_and_represents_order_intent_v0(
    tmp_path: Path,
) -> None:
    sizing_payload = _sizing_state_file_payload()
    sizing_path = tmp_path / "capital_risk_sizing_backtest_state.json"
    sizing_path.write_text(json.dumps(sizing_payload, indent=2), encoding="utf-8")

    intent_payload = _order_intent_state_file_payload()
    intent_path = tmp_path / "canonical_order_intent_backtest_state.json"
    intent_path.write_text(json.dumps(intent_payload, indent=2), encoding="utf-8")

    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        capital_risk_sizing_state_file_binding=CapitalRiskSizingBacktestStateFileBindingConfigV1(
            state_file_path=sizing_path,
            expected_state_file_digest_ref=str(sizing_payload["state_file_digest_ref"]),
        ),
        canonical_order_intent_state_file_binding=CanonicalOrderIntentBacktestStateFileBindingConfigV1(
            state_file_path=intent_path,
            expected_state_file_digest_ref=str(intent_payload["state_file_digest_ref"]),
        ),
    )
    assert result.bar_outcomes
    bound = [
        o for o in result.bar_outcomes if o.canonical_order_intent_backtest_state_file_evidence
    ]
    assert len(bound) == len(result.bar_outcomes)
    sample = bound[0].canonical_order_intent_backtest_state_file_evidence
    assert sample is not None
    assert sample.canonical_order_intent_boundary_backtest_state_file_bound is True


def test_mv2_research_wiring_legacy_without_state_file_unchanged_v0() -> None:
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
    )
    assert all(
        o.canonical_order_intent_backtest_state_file_evidence is None for o in result.bar_outcomes
    )


def test_order_intent_without_sizing_state_file_fails_closed_v0(tmp_path: Path) -> None:
    intent_payload = _order_intent_state_file_payload()
    intent_path = tmp_path / "canonical_order_intent_backtest_state.json"
    intent_path.write_text(json.dumps(intent_payload, indent=2), encoding="utf-8")
    with pytest.raises(
        ValueError, match="canonical_order_intent_backtest_state_file_requires_sizing_state_file"
    ):
        run_mv2_research_backtest_wiring_v1(
            _bars(n=4),
            strategy_id="ma_crossover",
            cfg=_cfg(),
            explicit_zero_cost_non_economic=True,
            canonical_order_intent_state_file_binding=CanonicalOrderIntentBacktestStateFileBindingConfigV1(
                state_file_path=intent_path,
                expected_state_file_digest_ref=str(intent_payload["state_file_digest_ref"]),
            ),
        )


def test_verify_state_file_digest_ref_v0() -> None:
    record = _order_intent_record()
    verify_canonical_order_intent_backtest_state_file_digest_v0(
        record,
        expected_digest_ref=record.state_file_digest_ref,
    )
    with pytest.raises(
        ValueError, match="canonical_order_intent_backtest_state_file_digest_mismatch"
    ):
        verify_canonical_order_intent_backtest_state_file_digest_v0(
            record, expected_digest_ref="0" * 64
        )
