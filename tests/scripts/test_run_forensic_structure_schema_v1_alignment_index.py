"""CI-focused owner for the alignment-index runner script."""

from __future__ import annotations

from pathlib import Path

from scripts.ops.run_forensic_structure_schema_v1_alignment_index import main


def test_runner_module_imports() -> None:
    assert Path("scripts/ops/run_forensic_structure_schema_v1_alignment_index.py").is_file()
    assert Path(
        "docs/forensic/FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_CANDIDATE_ALIGNMENT_INDEX_V1.md"
    ).is_file()
    assert callable(main)
