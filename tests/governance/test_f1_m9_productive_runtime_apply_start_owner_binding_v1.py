"""F1/M9 productive runtime apply start Owner-WP binding tests."""

from __future__ import annotations

from pathlib import Path

from src.governance.f1_m9_productive_runtime_apply_start_owner_binding_v1 import (
    evaluate_productive_runtime_apply_start_owner_binding_v1,
    evaluate_real_productive_apply_with_runtime_apply_start_precedence_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BOUND_APPLY = "3f0895951d0708d017326a8b4f779c433d609d09d67459fe47f1239f214a2f95"
HANDOFF_APPLY = "c0eb6c20c535fe839646254a6bfaaddff9b28bfb16799801cbca91b87c2bade3"


def test_runtime_apply_start_owner_wp_permits_post_6887_apply_digest() -> None:
    result = evaluate_productive_runtime_apply_start_owner_binding_v1(
        owner_apply_authorization_record_digest=BOUND_APPLY,
        repo_root=REPO_ROOT,
    )
    assert result.apply_permitted is True
    assert result.runtime_apply_start_owner_authorized is True


def test_precedence_prefers_runtime_apply_start_over_handoff_digest() -> None:
    start = evaluate_real_productive_apply_with_runtime_apply_start_precedence_v1(
        owner_apply_authorization_record_digest=BOUND_APPLY,
        repo_root=REPO_ROOT,
    )
    assert start.apply_permitted is True

    handoff_only = evaluate_real_productive_apply_with_runtime_apply_start_precedence_v1(
        owner_apply_authorization_record_digest=HANDOFF_APPLY,
        repo_root=REPO_ROOT,
    )
    assert handoff_only.apply_permitted is True
