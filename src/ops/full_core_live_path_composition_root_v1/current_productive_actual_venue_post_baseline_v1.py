"""Versioned execution baseline for CURRENT productive actual-venue POST slice.

Binds the POST Owner-GO path to a recorded merge-stable origin/main SHA and
requires live ``origin/main`` (and synchronized ``HEAD``) to match before real
mutation. Prevents stale hard-coded pins from implying compatibility without
live git proof.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    CurrentProductive29PChainBaselineError,
    CurrentProductive29PRuntimeIntegrityBackendV1,
    GitCurrentProductive29PRuntimeIntegrityBackendV1,
)

if TYPE_CHECKING:
    from pathlib import Path

# Post-#6930 PRE_EXTERNAL E2E handoff composition merge currency (cf3aa15f0).
EXPECTED_BASELINE_ORIGIN_MAIN_SHA = "cf3aa15f098827a9e60de8eb84e5bdd9eb54cca2"
BASELINE_AUTHORITY_CLASS = "VERSIONED_POST_SLICE_MERGE_STABLE_ORIGIN_MAIN_PIN"


class CurrentProductiveActualVenuePostBaselineError(RuntimeError):
    """Fail-closed actual-venue POST baseline violation."""


def assert_declared_baseline_matches_slice_pin_v1(
    *, declared_baseline_origin_main_sha: str
) -> None:
    declared = str(declared_baseline_origin_main_sha or "").strip().lower()
    expected = EXPECTED_BASELINE_ORIGIN_MAIN_SHA.lower()
    if declared != expected:
        raise CurrentProductiveActualVenuePostBaselineError("BASELINE_SHA_MISMATCH")


def resolve_and_assert_live_post_execution_baseline_v1(
    *,
    declared_baseline_origin_main_sha: str,
    integrity_backend: CurrentProductive29PRuntimeIntegrityBackendV1 | None = None,
    repo_root: Path | None = None,
) -> str:
    """Validate declared pin, live origin/main, and HEAD synchronization."""

    assert_declared_baseline_matches_slice_pin_v1(
        declared_baseline_origin_main_sha=declared_baseline_origin_main_sha
    )
    backend = integrity_backend
    if backend is None:
        from pathlib import Path as _Path

        root = repo_root or _Path(__file__).resolve().parents[3]
        backend = GitCurrentProductive29PRuntimeIntegrityBackendV1(repo_root=root)
    live = str(backend.resolve_origin_main_sha_v1() or "").strip().lower()
    head = str(backend.resolve_head_sha_v1() or "").strip().lower()
    expected = EXPECTED_BASELINE_ORIGIN_MAIN_SHA.lower()
    if live != expected:
        raise CurrentProductiveActualVenuePostBaselineError("LIVE_ORIGIN_MAIN_DRIFT_FROM_SLICE_PIN")
    if head != live:
        raise CurrentProductiveActualVenuePostBaselineError(
            "HEAD_NOT_SYNCHRONIZED_WITH_ORIGIN_MAIN"
        )
    return live


__all__ = [
    "BASELINE_AUTHORITY_CLASS",
    "EXPECTED_BASELINE_ORIGIN_MAIN_SHA",
    "CurrentProductiveActualVenuePostBaselineError",
    "assert_declared_baseline_matches_slice_pin_v1",
    "resolve_and_assert_live_post_execution_baseline_v1",
]
