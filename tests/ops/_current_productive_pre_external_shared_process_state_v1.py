"""Reset mutable PRE_EXTERNAL test process state (G17/F1-M9 caches; no runtime authority)."""

from __future__ import annotations

from tests.ops._current_productive_f1_m9_durable_seam_fixture_v1 import REPO_ROOT


def reseed_workspace_canonical_f1_m9_runtime_ledgers_v1() -> None:
    """Re-empty workspace ``runtime/governance`` F1/M9 ledgers and re-materialize apply-start seam."""
    from src.governance.f1_m9_productive_apply_durable_ledger_paths_v1 import (
        resolve_canonical_f1_m9_productive_apply_ledger_paths_v1,
        resolve_canonical_f1_m9_threshold_value_authorization_ledger_paths_v1,
    )
    from src.governance.f1_m9_productive_apply_ledger_v1 import (
        initialize_empty_revocation_ledger_v1,
    )
    from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
        initialize_empty_threshold_revocation_ledger_v1,
    )
    from src.governance.governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1 import (
        GovernedF1M9RuntimeApplyStartRequestV1,
        run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1,
    )

    apply_paths = resolve_canonical_f1_m9_productive_apply_ledger_paths_v1(repo_root=REPO_ROOT)
    threshold_paths = resolve_canonical_f1_m9_threshold_value_authorization_ledger_paths_v1(
        repo_root=REPO_ROOT
    )
    apply_paths.apply_ledger_path.parent.mkdir(parents=True, exist_ok=True)
    apply_paths.apply_ledger_path.write_text("", encoding="utf-8")
    initialize_empty_revocation_ledger_v1(apply_paths.revocation_ledger_path)
    threshold_paths.threshold_ledger_path.write_text("", encoding="utf-8")
    initialize_empty_threshold_revocation_ledger_v1(
        threshold_paths.threshold_revocation_ledger_path
    )
    result = run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1(
        GovernedF1M9RuntimeApplyStartRequestV1(
            apply_ledger_paths=apply_paths,
            threshold_ledger_paths=threshold_paths,
            repo_root=REPO_ROOT,
        )
    )
    if result.status != "CONTINUATION_COMPLETE":
        raise RuntimeError(
            "F1_M9_CANONICAL_RUNTIME_RESEED_FAILED:" + ",".join(result.blocking_reasons)
        )


def reset_current_productive_pre_external_shared_test_process_state_v1() -> None:
    """Drop cross-test producer/ledger caches so CURRENT PRE_EXTERNAL batches stay order-independent."""
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_base_binding_v1 import (
        clear_current_productive_base_binding_state_v1,
    )
    from src.ops.treasury_phase_2_read_only_reconciliation_v1 import (
        clear_treasury_reconciliation_idempotency_cache_v1,
    )
    import tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 as oneshot_g17_join_v1

    oneshot_g17_join_v1._PRODUCED_G17_CACHE.clear()
    oneshot_g17_join_v1._F1_M9_LEDGER_CACHE = None
    clear_current_productive_base_binding_state_v1()
    clear_treasury_reconciliation_idempotency_cache_v1()


__all__ = [
    "reseed_workspace_canonical_f1_m9_runtime_ledgers_v1",
    "reset_current_productive_pre_external_shared_test_process_state_v1",
]
