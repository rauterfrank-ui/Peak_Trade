"""Tests for BOUNDED_PRODUCTIVE_KERNEL_COMPLETENESS_WITNESS_V1. AUTHORITY=NONE."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WITNESS_SCRIPT = REPO / "scripts/ops/bounded_productive_kernel_completeness_witness_v1.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "bounded_productive_kernel_completeness_witness_v1", WITNESS_SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_bounded_kernel_witness_passes_against_csia() -> None:
    mod = _load()
    witness = mod.load_witness_v1()
    assert witness["bounded_kernel_completeness_proven"] is True
    assert witness["global_repository_exhaustiveness_proven"] is False
    assert len(witness["bounded_kernel_object_ids"]) == 22
    assert len(witness["bounded_kernel_required_edge_ids"]) == 24
    assert mod.verify_bounded_kernel_completeness_v1() == []
