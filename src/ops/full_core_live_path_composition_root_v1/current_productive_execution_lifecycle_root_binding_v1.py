"""BU01 — canonical execution lifecycle root binding (fail-closed, no new authority).

Binds POST store_root, guard atomic_state_dir, and portfolio reconciliation_state_root
to existing CURRENT layout conventions. Does not merge persistence domains.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)

CONTRACT_ID = "CURRENT_PRODUCTIVE_EXECUTION_LIFECYCLE_ROOT_BINDING_V1"
RUNTIME_STATE_DIRNAME = "runtime_state"
RECON_DIRNAME = "recon"
GUARD_ATOMIC_SUBDIR = "full_core_enter_post_guard_atomic_v1"


class ExecutionLifecycleRootBindingError(RuntimeError):
    """Fail-closed execution lifecycle root / identity binding violation."""


def default_guard_atomic_state_dir_for_store_root_v1(*, store_root: Path | str) -> Path:
    return Path(store_root).resolve() / GUARD_ATOMIC_SUBDIR


def assert_atomic_state_dir_bound_to_store_root_v1(
    *,
    store_root: Path | str,
    atomic_state_dir: Path | str,
) -> None:
    """Atomic guard state must live under the POST durable store_root (no cross-lane dirs)."""
    store = Path(store_root).resolve()
    atomic = Path(atomic_state_dir).resolve()
    if not atomic.is_relative_to(store):
        raise ExecutionLifecycleRootBindingError("ATOMIC_STATE_DIR_OUTSIDE_STORE_ROOT")


def resolve_canonical_reconciliation_state_root_v1(*, productivity_root: Path | str) -> Path:
    """Match Cap24 / 29p productive layout: productivity/runtime_state/recon."""
    root = Path(productivity_root).resolve()
    state_root = root / RUNTIME_STATE_DIRNAME
    if state_root.is_dir():
        return (state_root / RECON_DIRNAME).resolve()
    if (root / "selection").is_dir() and (root / "universe").is_dir():
        return (root / RECON_DIRNAME).resolve()
    raise ExecutionLifecycleRootBindingError("PRODUCTIVITY_RUNTIME_STATE_LAYOUT_MISSING")


def assert_reconciliation_state_root_matches_productivity_v1(
    *,
    productivity_root: Path | str,
    reconciliation_state_root: Path | str,
) -> None:
    expected = resolve_canonical_reconciliation_state_root_v1(
        productivity_root=productivity_root,
    )
    actual = Path(reconciliation_state_root).resolve()
    if actual != expected:
        raise ExecutionLifecycleRootBindingError("RECONCILIATION_STATE_ROOT_CANONICAL_MISMATCH")


def assert_correlation_identity_matches_envelope_v1(
    *,
    correlation: dict[str, object],
    envelope: FinalOrderEnvelopeV1,
) -> None:
    """Correlation record must match envelope attempt identity (fail-closed)."""
    assert_envelope_unmodified_v1(envelope)
    digest = str(correlation.get("envelope_digest") or "")
    if digest and digest != envelope.envelope_digest:
        raise ExecutionLifecycleRootBindingError("CORRELATION_ENVELOPE_DIGEST_MISMATCH")
    clordid = str(correlation.get("clordid") or "")
    if clordid and clordid != str(envelope.client_order_id):
        raise ExecutionLifecycleRootBindingError("CORRELATION_CLORDID_MISMATCH")
    env_id = str(correlation.get("envelope_id") or "")
    if env_id and env_id != str(envelope.envelope_id):
        raise ExecutionLifecycleRootBindingError("CORRELATION_ENVELOPE_ID_MISMATCH")


__all__ = [
    "CONTRACT_ID",
    "ExecutionLifecycleRootBindingError",
    "GUARD_ATOMIC_SUBDIR",
    "assert_atomic_state_dir_bound_to_store_root_v1",
    "assert_correlation_identity_matches_envelope_v1",
    "assert_reconciliation_state_root_matches_productivity_v1",
    "default_guard_atomic_state_dir_for_store_root_v1",
    "resolve_canonical_reconciliation_state_root_v1",
]
