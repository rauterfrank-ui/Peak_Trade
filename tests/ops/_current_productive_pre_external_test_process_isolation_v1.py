"""Authoritative PRE_EXTERNAL same-process test isolation (idempotent establish + reset)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest

from tests.ops._current_productive_f1_m9_durable_seam_fixture_v1 import (
    materialize_f1_m9_runtime_applied_seam_ledgers_v1,
)
from tests.ops._current_productive_pre_external_shared_process_state_v1 import (
    reseed_workspace_canonical_f1_m9_runtime_ledgers_v1,
    reset_current_productive_pre_external_shared_test_process_state_v1,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_master_v2_runtime_cycle_v1 as master_v2_cycle_v1,
)

# Mutable F1 seam injected into all Master-V2 consumer import bindings.
_ISOLATION_F1_KWARGS_V1: dict[str, object] = {}
_RUN_CYCLE_PATCH_TARGETS_V1: tuple[str, ...] = (
    "src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1",
    "src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1",
    "tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1",
)
# Capture before any test monkeypatch (import-time binding is the real runtime function).
_ORIGINAL_RUN_CYCLE_V1: Callable[..., Any] = (
    master_v2_cycle_v1.run_current_productive_master_v2_runtime_cycle_v1
)


def _run_cycle_with_isolated_f1_m9_ledgers_v1(**kwargs: object) -> object:
    if kwargs.get("f1_m9_productive_apply_ledger_paths") is None and _ISOLATION_F1_KWARGS_V1:
        kwargs = {**kwargs, **_ISOLATION_F1_KWARGS_V1}
    return _ORIGINAL_RUN_CYCLE_V1(**kwargs)


def _ensure_run_cycle_consumer_patches_v1(*, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    wrapped = _run_cycle_with_isolated_f1_m9_ledgers_v1
    for module_name in _RUN_CYCLE_PATCH_TARGETS_V1:
        mod = importlib.import_module(module_name)
        monkeypatch.setattr(
            mod,
            "run_current_productive_master_v2_runtime_cycle_v1",
            wrapped,
        )


def clear_pre_external_test_isolation_f1_binding_v1() -> None:
    """Drop in-process F1 kwargs binding (safe at test boundaries; idempotent)."""
    _ISOLATION_F1_KWARGS_V1.clear()


def active_pre_external_test_f1_m9_cycle_ledger_kwargs_v1() -> dict[str, object] | None:
    if not _ISOLATION_F1_KWARGS_V1:
        return None
    return dict(_ISOLATION_F1_KWARGS_V1)


def _sync_f1_m9_test_ledger_cache_v1(
    *,
    apply_paths: object,
    threshold_paths: object,
) -> None:
    import tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 as oneshot_g17_join_v1

    oneshot_g17_join_v1._F1_M9_LEDGER_CACHE = {
        "apply_ledger_paths": apply_paths,
        "threshold_ledger_paths": threshold_paths,
    }


def establish_current_productive_pre_external_test_process_isolation_v1(
    *,
    monkeypatch: pytest.MonkeyPatch,
    f1_root: Path,
    reseed_workspace_f1_m9: bool = False,
) -> None:
    """Reset shared caches, bind tmp F1/M9 ledgers, patch all Master-V2 import consumers."""
    reset_current_productive_pre_external_shared_test_process_state_v1()
    if reseed_workspace_f1_m9:
        reseed_workspace_canonical_f1_m9_runtime_ledgers_v1()
    f1_root.mkdir(parents=True, exist_ok=True)
    materialized = materialize_f1_m9_runtime_applied_seam_ledgers_v1(f1_root)
    apply_paths = materialized["apply_ledger_paths"]
    threshold_paths = materialized["threshold_ledger_paths"]

    _ISOLATION_F1_KWARGS_V1.clear()
    _ISOLATION_F1_KWARGS_V1.update(
        {
            "f1_m9_productive_apply_ledger_paths": apply_paths,
            "f1_m9_threshold_ledger_paths": threshold_paths,
        }
    )

    import src.governance.f1_m9_productive_apply_durable_ledger_paths_v1 as f1_paths_v1

    monkeypatch.setattr(
        f1_paths_v1,
        "resolve_canonical_f1_m9_productive_apply_ledger_paths_v1",
        lambda *, repo_root=None, _apply=apply_paths: _apply,
    )
    monkeypatch.setattr(
        f1_paths_v1,
        "resolve_canonical_f1_m9_threshold_value_authorization_ledger_paths_v1",
        lambda *, repo_root=None, _threshold=threshold_paths: _threshold,
    )
    _sync_f1_m9_test_ledger_cache_v1(
        apply_paths=apply_paths,
        threshold_paths=threshold_paths,
    )
    _ensure_run_cycle_consumer_patches_v1(monkeypatch=monkeypatch)


__all__ = [
    "active_pre_external_test_f1_m9_cycle_ledger_kwargs_v1",
    "clear_pre_external_test_isolation_f1_binding_v1",
    "establish_current_productive_pre_external_test_process_isolation_v1",
    "reset_current_productive_pre_external_shared_test_process_state_v1",
]
