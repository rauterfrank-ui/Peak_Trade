"""CI-focused owner for the adjudication-contract runner script."""

from __future__ import annotations

from pathlib import Path

from scripts.ops.run_forensic_structure_schema_v1_adjudication_contract import main


def test_runner_module_imports() -> None:
    assert Path("scripts/ops/run_forensic_structure_schema_v1_adjudication_contract.py").is_file()
    assert Path("docs/forensic/FORENSIC_STRUCTURE_SCHEMA_V1_ADJUDICATION_CONTRACT_V1.md").is_file()
    assert callable(main)
