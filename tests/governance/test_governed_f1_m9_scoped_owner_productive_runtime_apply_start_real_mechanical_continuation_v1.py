"""F1/M9 governed productive runtime apply start continuation tests."""

from __future__ import annotations

from pathlib import Path

from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    initialize_empty_threshold_revocation_ledger_v1,
)
from src.governance.governed_f1_m9_scoped_owner_productive_runtime_apply_start_closure_v1 import (
    prove_governed_f1_m9_scoped_owner_productive_runtime_apply_start_v1,
)
from src.governance.governed_f1_m9_scoped_owner_productive_runtime_apply_start_evidence_v1 import (
    F1M9RuntimeApplyStartPhaseStateV1,
)
from src.governance.governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1 import (
    GovernedF1M9RuntimeApplyStartRequestV1,
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
    RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS,
    REAL_P4_TO_F1_M9_JOIN_STATUS,
    run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    EXTERNAL_EFFECT,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BOUND_APPLY = "3f0895951d0708d017326a8b4f779c433d609d09d67459fe47f1239f214a2f95"
BOUND_THRESHOLD = "e556ea63f68df3651cf38ef4d49d675f94a0e20f67c5b72f9044f9492b9bf109"


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


def test_runtime_apply_start_continuation_complete(tmp_path: Path) -> None:
    result = run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1(
        GovernedF1M9RuntimeApplyStartRequestV1(
            apply_ledger_paths=_apply_ledger_paths(tmp_path),
            threshold_ledger_paths=_threshold_ledger_paths(tmp_path),
            repo_root=REPO_ROOT,
            persist_durable_evidence=False,
        )
    )
    assert result.status == "CONTINUATION_COMPLETE", result.blocking_reasons
    assert result.productive_apply_occurred is True
    assert result.runtime_apply_started is True
    assert result.configuration_runtime_applied is True
    assert result.owner_apply_record_digest == BOUND_APPLY
    assert result.owner_threshold_record_digest == BOUND_THRESHOLD
    assert result.ratified_value_lineage_valid is True
    assert result.real_p4_to_f1_m9_join_status == REAL_P4_TO_F1_M9_JOIN_STATUS
    assert result.productive_activation_authorized is False
    assert result.presence_gate_transport_ready is True
    assert result.threshold_enforcement_mechanical_continuation is True
    assert result.apply_start_evidence.phase_state == F1M9RuntimeApplyStartPhaseStateV1.COMPLETED
    assert result.apply_start_evidence.threshold_numeric_max_age_seconds == float(
        RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS
    )


def test_apply_start_idempotent_replay_after_durable_apply(tmp_path: Path) -> None:
    ledger_root = tmp_path / "durable"
    ledger_root.mkdir()
    first = run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1(
        GovernedF1M9RuntimeApplyStartRequestV1(
            apply_ledger_paths=_apply_ledger_paths(ledger_root),
            threshold_ledger_paths=_threshold_ledger_paths(ledger_root),
            repo_root=REPO_ROOT,
        )
    )
    assert first.status == "CONTINUATION_COMPLETE"
    second = run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1(
        GovernedF1M9RuntimeApplyStartRequestV1(
            apply_ledger_paths=_apply_ledger_paths(ledger_root),
            threshold_ledger_paths=_threshold_ledger_paths(ledger_root),
            repo_root=REPO_ROOT,
        )
    )
    assert second.status == "CONTINUATION_COMPLETE", second.blocking_reasons
    assert second.bound_seam_record is not None
    assert second.bound_seam_record.get("runtime_applied") is True


def test_threshold_enforcement_closure_still_reachable_after_apply_start(tmp_path: Path) -> None:
    from src.governance.f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1 import (
        STATUS_CLOSURE_COMPLETE,
        evaluate_f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1,
    )

    apply_result = run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1(
        GovernedF1M9RuntimeApplyStartRequestV1(
            apply_ledger_paths=_apply_ledger_paths(tmp_path / "start"),
            threshold_ledger_paths=_threshold_ledger_paths(tmp_path / "start"),
            repo_root=REPO_ROOT,
        )
    )
    assert apply_result.status == "CONTINUATION_COMPLETE"

    from tests.governance.test_f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1 import (
        _fresh_pair,
        _stale_pair,
    )

    fresh_ctx, fresh_est = _fresh_pair()
    stale_ctx, stale_est = _stale_pair()
    closure = evaluate_f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1(
        repo_root=REPO_ROOT,
        apply_ledger_paths=_apply_ledger_paths(tmp_path / "closure"),
        threshold_ledger_paths=_threshold_ledger_paths(tmp_path / "closure"),
        market_context_fresh=fresh_ctx,
        market_context_stale=stale_ctx,
        estimate_fresh=fresh_est,
        estimate_stale=stale_est,
    )
    assert closure.closure_status == STATUS_CLOSURE_COMPLETE
    assert closure.external_order_effect_authorized is False


def test_global_invariants_and_closure_proof() -> None:
    assert PRODUCTIVE_ACTIVATION_AUTHORIZED is False
    assert EXTERNAL_EFFECT is False
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False
    assert prove_governed_f1_m9_scoped_owner_productive_runtime_apply_start_v1(repo_root=REPO_ROOT)
