"""Deterministic synthetic GLB-019 A2/B patch builder for selector contract tests (v0)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from scripts.ops.durable_completion_integration_partitions_v0 import (
    GLB019_A2B_ALLOWED_FILES,
    collect_glb019_a2b_patch_text,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def synthetic_glb019_a2b_positive_patch_text() -> str:
    """Repo-grounded additive GLB-019 A2/B patch from origin/main...HEAD."""
    patch = collect_glb019_a2b_patch_text(
        base_ref="origin/main",
        repo_root=_REPO_ROOT,
        changed_files=sorted(GLB019_A2B_ALLOWED_FILES),
    )
    if not patch:
        raise RuntimeError(
            "unable to collect GLB-019 A2/B synthetic positive patch from origin/main...HEAD"
        )
    return patch


def synthetic_glb019_a2b_reject_patch_text() -> str:
    patch = synthetic_glb019_a2b_positive_patch_text()
    return patch.replace(
        "    glb019_result = evaluate_glb019_event_stream_validation(validation_input)",
        "    pe21_result = evaluate_glb019_event_stream_validation(validation_input)",
        1,
    )
