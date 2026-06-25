"""Deterministic synthetic GLB-019 A2/B patch builder for selector contract tests (v0)."""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

from scripts.ops.durable_completion_integration_partitions_v0 import (
    GLB019_A2B_ALLOWED_FILES,
    collect_glb019_a2b_patch_text,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ARCHIVED_GLB019_BASE_REF = "origin/main~1"
_ARCHIVED_GLB019_HEAD_REF = "origin/main"


def _archived_glb019_merge_patch_text() -> str:
    """Branch-independent archived GLB-019 merge diff (pre-merge parent → origin/main)."""
    paths = sorted(GLB019_A2B_ALLOWED_FILES)
    proc = subprocess.run(
        [
            "git",
            "diff",
            _ARCHIVED_GLB019_BASE_REF,
            _ARCHIVED_GLB019_HEAD_REF,
            "--",
            *paths,
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in {0, 1}:
        raise RuntimeError(
            "unable to build archived GLB-019 A2/B synthetic positive patch from "
            f"{_ARCHIVED_GLB019_BASE_REF}..{_ARCHIVED_GLB019_HEAD_REF}"
        )
    patch = proc.stdout
    if not patch.strip():
        raise RuntimeError(
            "archived GLB-019 A2/B synthetic positive patch is empty for "
            f"{_ARCHIVED_GLB019_BASE_REF}..{_ARCHIVED_GLB019_HEAD_REF}"
        )
    return patch


@lru_cache(maxsize=1)
def synthetic_glb019_a2b_positive_patch_text() -> str:
    """Repo-grounded additive GLB-019 A2/B patch; branch-independent on merged main."""
    patch = collect_glb019_a2b_patch_text(
        base_ref="origin/main",
        repo_root=_REPO_ROOT,
        changed_files=sorted(GLB019_A2B_ALLOWED_FILES),
    )
    if patch:
        return patch
    return _archived_glb019_merge_patch_text()


def synthetic_glb019_a2b_reject_patch_text() -> str:
    patch = synthetic_glb019_a2b_positive_patch_text()
    return patch.replace(
        "    glb019_result = evaluate_glb019_event_stream_validation(validation_input)",
        "    pe21_result = evaluate_glb019_event_stream_validation(validation_input)",
        1,
    )
