"""Contract: reconciliation boundary backtest state-file binding v0 (offline only)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from meta.learning_loop.runtime_state_reconciliation_v1 import RECONCILIATION_CONTRACT_VERSION
from src.backtest.mv2_research_wiring_v1 import (
    ReconciliationBacktestStateFileBindingConfigV1,
    run_mv2_research_backtest_wiring_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    NEXT_RECOMMENDED_SLICE,
    parity_surface_assessments_v0,
)
from trading.master_v2.killswitch_boundary_backtest_state_file_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0 as killswitch_digest,
    parse_killswitch_backtest_state_file_v0,
)
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KillSwitchBoundaryMode,
)
from trading.master_v2.reconciliation_boundary_backtest_state_file_binding_adapter_v0 import (
    RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
    RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    apply_backtest_reconciliation_exposure_gate_v0,
    backtest_reconciliation_state_file_binding_non_authority_ok_v0,
    bind_reconciliation_boundary_backtest_state_file_evidence_v0,
    compute_backtest_state_file_digest_from_payload_v0,
    evaluate_backtest_reconciliation_state_file_boundary_only_v0,
    parse_reconciliation_backtest_state_file_v0,
    verify_reconciliation_backtest_state_file_digest_v0,
)
from trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0 import (
    RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg

REPO_ROOT = Path(__file__).resolve().parents[3]

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/reconciliation_boundary_backtest_state_file_binding_adapter_v0.py",
    REPO_ROOT / "scripts/ops/run_backtest_reconciliation_state_file_wiring_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_reconciliation_boundary_backtest_state_file_binding_contract_v0.py",
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


def _state_file_payload(
    *,
    reconciliation_state: str = ReconciliationState.RECONCILED.value,
    position_state: str = PositionState.FLAT_RECONCILED.value,
    venue_flat: bool = True,
    existing_position_side: str = ExistingPositionSide.NONE.value,
    intent_snapshot_unresolved: bool = False,
    order_snapshot_unresolved: bool = False,
    fill_snapshot_unresolved: bool = False,
) -> dict[str, object]:
    base = {
        "schema_version": RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "reconciliation_state": reconciliation_state,
        "position_state": position_state,
        "venue_flat": venue_flat,
        "existing_position_side": existing_position_side,
        "intent_snapshot_unresolved": intent_snapshot_unresolved,
        "order_snapshot_unresolved": order_snapshot_unresolved,
        "fill_snapshot_unresolved": fill_snapshot_unresolved,
        "reconciliation_owner_digest_ref": RECONCILIATION_CONTRACT_VERSION,
    }
    digest = compute_backtest_state_file_digest_from_payload_v0(base)
    return {**base, "state_file_digest_ref": digest}


def _base_evidence(*, decision_outcome: str = DecisionOutcome.OBSERVE.value):
    return build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-reconciliation-state-file-decision",
        replay_id="backtest-reconciliation-state-file-replay",
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=1,
        composition_result_id="composition",
        entry_exit_policy_ref="policy",
        selected_side="long",
        decision_outcome=decision_outcome,
        reason_codes=("PASS",),
        decision_precedence_trace=("observe",),
        config_digest="config",
        implementation_digest="impl",
    )


def _record(**kwargs: object):
    return parse_reconciliation_backtest_state_file_v0(payload=_state_file_payload(**kwargs))


def test_owner_constants_reuse_surface_l_adapter_v0() -> None:
    assert RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER.endswith(
        "reconciliation_boundary_backtest_state_file_binding_adapter_v0"
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


def test_reconciled_flat_state_permits_parity_representation_v0() -> None:
    evidence = evaluate_backtest_reconciliation_state_file_boundary_only_v0(_record())
    assert evidence.reconciliation_state == ReconciliationState.RECONCILED.value
    assert evidence.position_state == PositionState.FLAT_RECONCILED.value
    assert apply_backtest_reconciliation_exposure_gate_v0(1, evidence=evidence) == 1


def test_reconciliation_required_blocks_new_exposure_v0() -> None:
    evidence = evaluate_backtest_reconciliation_state_file_boundary_only_v0(
        _record(reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED.value)
    )
    assert evidence.reconciliation_required_maps_to_reconcile_only is True
    assert apply_backtest_reconciliation_exposure_gate_v0(1, evidence=evidence) == 0


def test_submission_unknown_blocks_new_exposure_v0() -> None:
    evidence = evaluate_backtest_reconciliation_state_file_boundary_only_v0(
        _record(position_state=PositionState.SUBMISSION_UNKNOWN.value)
    )
    assert evidence.submission_unknown_blocks_new_exposure is True
    assert evidence.unknown_outcome_never_auto_resubmits is True
    assert apply_backtest_reconciliation_exposure_gate_v0(1, evidence=evidence) == 0


def test_opposite_side_entry_blocked_until_reconciled_flat_v0() -> None:
    evidence = evaluate_backtest_reconciliation_state_file_boundary_only_v0(
        _record(
            position_state=PositionState.EXIT_PENDING.value,
            existing_position_side=ExistingPositionSide.LONG.value,
        )
    )
    assert evidence.reconciled_flat_required_before_opposite_side is True
    assert apply_backtest_reconciliation_exposure_gate_v0(1, evidence=evidence) == 0


def test_missing_state_file_input_fails_closed_v0() -> None:
    with pytest.raises(ValueError, match="reconciliation_backtest_state_file_input_missing"):
        parse_reconciliation_backtest_state_file_v0()


def test_corrupted_state_file_digest_fails_closed_v0() -> None:
    payload = _state_file_payload()
    payload["state_file_digest_ref"] = "0" * 64
    with pytest.raises(ValueError, match="reconciliation_backtest_state_file_digest_mismatch"):
        parse_reconciliation_backtest_state_file_v0(payload=payload)


def test_malformed_state_file_fails_closed_v0() -> None:
    with pytest.raises(ValueError, match="reconciliation_backtest_state_file_corrupt"):
        parse_reconciliation_backtest_state_file_v0(raw_bytes=b"not-json")


def test_invalid_reconciliation_state_fails_closed_v0() -> None:
    payload = _state_file_payload()
    payload["reconciliation_state"] = "not_a_state"
    with pytest.raises(ValueError, match="reconciliation_state_invalid"):
        parse_reconciliation_backtest_state_file_v0(payload=payload)


def test_backtest_binding_uses_surface_l_adapter_not_duplicate_semantics_v0() -> None:
    evidence = _base_evidence(decision_outcome=DecisionOutcome.ENTER_LONG.value)
    bound = bind_reconciliation_boundary_backtest_state_file_evidence_v0(
        evidence,
        state_file=_record(reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED.value),
    )
    assert (
        bound.surface_l_adapter_owner_ref
        == RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
    )
    assert bound.offline_binding.binding_applied is True


def test_non_authority_invariants_v0() -> None:
    evidence = evaluate_backtest_reconciliation_state_file_boundary_only_v0(
        _record(position_state=PositionState.SUBMISSION_UNKNOWN.value)
    )
    assert evidence.runtime_authority is False
    assert evidence.orders_allowed is False
    assert evidence.credentials_used is False
    assert evidence.economic_evaluation is False
    assert backtest_reconciliation_state_file_binding_non_authority_ok_v0(evidence)

    assert (
        NEXT_RECOMMENDED_SLICE == "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_4_WAY_PARITY_REWIRE_V0"
    )


def test_semantic_flags_represented_for_reconciliation_states_v0() -> None:
    evidence = evaluate_backtest_reconciliation_state_file_boundary_only_v0(
        _record(reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED.value)
    )
    assert evidence.reconciliation_semantics_represented_in_backtest is True
    assert evidence.reconciliation_failure_blocks_new_exposure_represented_in_backtest is True


def test_parity_gap_assessment_surface_l_backtest_state_file_pass_v0() -> None:
    reconciliation = next(
        item for item in parity_surface_assessments_v0() if item.surface_id == "L"
    )
    assert reconciliation.parity_status == "PASS"
    assert reconciliation.missing_binding_if_any == ""
    assert "bind_reconciliation_boundary_backtest_state_file_evidence_v0" in (
        reconciliation.current_backtest_binding
    )
    assert (
        NEXT_RECOMMENDED_SLICE == "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_4_WAY_PARITY_REWIRE_V0"
    )


def test_mv2_research_wiring_binds_state_file_and_blocks_unresolved_v0(tmp_path: Path) -> None:
    payload = _state_file_payload(
        reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED.value
    )
    state_path = tmp_path / "reconciliation_backtest_state.json"
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        reconciliation_state_file_binding=ReconciliationBacktestStateFileBindingConfigV1(
            state_file_path=state_path,
            expected_state_file_digest_ref=str(payload["state_file_digest_ref"]),
        ),
    )
    assert result.bar_outcomes
    bound = [o for o in result.bar_outcomes if o.reconciliation_backtest_state_file_evidence]
    assert len(bound) == len(result.bar_outcomes)
    sample = bound[0].reconciliation_backtest_state_file_evidence
    assert sample is not None
    assert sample.reconciliation_boundary_backtest_state_file_bound is True
    assert sample.reconciliation_required_maps_to_reconcile_only is True
    assert all(o.position_signal == 0 for o in result.bar_outcomes)


def test_mv2_research_wiring_legacy_without_state_file_unchanged_v0() -> None:
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
    )
    assert all(o.reconciliation_backtest_state_file_evidence is None for o in result.bar_outcomes)


def test_required_state_file_missing_fails_closed_v0() -> None:
    with pytest.raises(ValueError, match="reconciliation_backtest_state_file_missing"):
        run_mv2_research_backtest_wiring_v1(
            _bars(n=4),
            strategy_id="ma_crossover",
            cfg=_cfg(),
            explicit_zero_cost_non_economic=True,
            reconciliation_state_file_binding=ReconciliationBacktestStateFileBindingConfigV1(
                require_state_file=True,
            ),
        )


def test_verify_state_file_digest_ref_v0() -> None:
    record = _record()
    verify_reconciliation_backtest_state_file_digest_v0(
        record,
        expected_digest_ref=record.state_file_digest_ref,
    )
    with pytest.raises(ValueError, match="reconciliation_backtest_state_file_digest_mismatch"):
        verify_reconciliation_backtest_state_file_digest_v0(record, expected_digest_ref="0" * 64)


def test_killswitch_state_file_binding_remains_compatible_v0(tmp_path: Path) -> None:
    """PR #4957 KillSwitch state-file path unchanged when reconciliation binding added."""
    from src.backtest.mv2_research_wiring_v1 import KillSwitchBacktestStateFileBindingConfigV1
    from src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1 import (
        KILL_SWITCH_CONTRACT_DIGEST,
    )

    ks_base = {
        "schema_version": KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "killswitch_boundary_mode": KillSwitchBoundaryMode.BLOCK_NEW.value,
        "fencing_digest_ref": KILL_SWITCH_CONTRACT_DIGEST,
        "prior_killswitch_active": False,
    }
    ks_payload = {**ks_base, "state_file_digest_ref": killswitch_digest(ks_base)}
    ks_path = tmp_path / "killswitch_backtest_state.json"
    ks_path.write_text(json.dumps(ks_payload, indent=2), encoding="utf-8")

    rec_payload = _state_file_payload()
    rec_path = tmp_path / "reconciliation_backtest_state.json"
    rec_path.write_text(json.dumps(rec_payload, indent=2), encoding="utf-8")

    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        killswitch_state_file_binding=KillSwitchBacktestStateFileBindingConfigV1(
            state_file_path=ks_path,
            expected_state_file_digest_ref=str(ks_payload["state_file_digest_ref"]),
        ),
        reconciliation_state_file_binding=ReconciliationBacktestStateFileBindingConfigV1(
            state_file_path=rec_path,
            expected_state_file_digest_ref=str(rec_payload["state_file_digest_ref"]),
        ),
    )
    assert all(o.killswitch_backtest_state_file_evidence is not None for o in result.bar_outcomes)
    assert all(
        o.reconciliation_backtest_state_file_evidence is not None for o in result.bar_outcomes
    )
    assert all(o.position_signal == 0 for o in result.bar_outcomes)
    assert parse_killswitch_backtest_state_file_v0(path=ks_path).killswitch_boundary_mode == (
        KillSwitchBoundaryMode.BLOCK_NEW.value
    )
