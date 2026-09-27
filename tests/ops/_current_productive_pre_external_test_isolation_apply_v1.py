"""Apply per-test F1/M9 + Master-V2 isolation (PRE_EXTERNAL ops tests only)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.ops._current_productive_f1_m9_durable_seam_fixture_v1 import (
    materialize_f1_m9_runtime_applied_seam_ledgers_v1,
)


def apply_current_productive_pre_external_f1_m9_test_isolation_v1(
    *,
    monkeypatch: pytest.MonkeyPatch,
    f1_root: Path,
) -> None:
    """Route canonical F1/M9 resolution and Master-V2 cycles through isolated ledger paths."""
    materialized = materialize_f1_m9_runtime_applied_seam_ledgers_v1(f1_root)
    apply_paths = materialized["apply_ledger_paths"]
    threshold_paths = materialized["threshold_ledger_paths"]

    import src.governance.f1_m9_productive_apply_durable_ledger_paths_v1 as f1_paths_v1
    import src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 as master_v2_cycle_v1
    import tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 as oneshot_g17_join_v1

    monkeypatch.setattr(
        f1_paths_v1,
        "resolve_canonical_f1_m9_productive_apply_ledger_paths_v1",
        lambda *, repo_root=None: apply_paths,
    )
    monkeypatch.setattr(
        f1_paths_v1,
        "resolve_canonical_f1_m9_threshold_value_authorization_ledger_paths_v1",
        lambda *, repo_root=None: threshold_paths,
    )
    oneshot_g17_join_v1._F1_M9_LEDGER_CACHE = {
        "apply_ledger_paths": apply_paths,
        "threshold_ledger_paths": threshold_paths,
    }

    _original_run_cycle = master_v2_cycle_v1.run_current_productive_master_v2_runtime_cycle_v1

    def _run_cycle_with_isolated_f1_m9_ledgers_v1(**kwargs: object):
        if kwargs.get("f1_m9_productive_apply_ledger_paths") is None:
            kwargs = {
                **kwargs,
                "f1_m9_productive_apply_ledger_paths": apply_paths,
                "f1_m9_threshold_ledger_paths": threshold_paths,
            }
        return _original_run_cycle(**kwargs)

    monkeypatch.setattr(
        master_v2_cycle_v1,
        "run_current_productive_master_v2_runtime_cycle_v1",
        _run_cycle_with_isolated_f1_m9_ledgers_v1,
    )


__all__ = ["apply_current_productive_pre_external_f1_m9_test_isolation_v1"]
