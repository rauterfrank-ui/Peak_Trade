"""CI-focused owner for the read-only transformer runner script."""

from __future__ import annotations

from pathlib import Path

from scripts.ops.forensic_structure_schema_v1.constants import STAGE_ORDER
from scripts.ops.run_forensic_structure_schema_v1_transformer import main


def test_runner_module_imports_and_stage_contract() -> None:
    assert len(STAGE_ORDER) == 12
    assert Path("scripts/ops/run_forensic_structure_schema_v1_transformer.py").is_file()
    assert callable(main)
