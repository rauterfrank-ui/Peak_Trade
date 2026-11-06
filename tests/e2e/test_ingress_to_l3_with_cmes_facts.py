"""E2E: Ingress -> capsule with CMES facts -> L3 dry-run; no raw (Runbook K5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ai_orchestration.l3_contracts import accepts_l3_pointer_only_input
from src.ai_orchestration.l3_runner import L3Runner
from src.risk.cmes import CMES_FACT_KEYS
from src.ingress.orchestrator import OrchestratorConfig, run_ingress


@pytest.fixture
def e2e_out_dir(tmp_path: Path) -> Path:
    return tmp_path / "e2e_cmes_out"


@pytest.fixture
def fixed_clock():
    from datetime import datetime, timezone

    return datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)


def test_run_ingress_empty_produces_capsule_with_facts(e2e_out_dir: Path) -> None:
    ops_base = e2e_out_dir / "ops"
    config = OrchestratorConfig(base_dir=ops_base, run_id="e2e_cmes", input_jsonl_path="")
    fv_path, cap_path = run_ingress(config)
    assert cap_path.exists()
    cap_data = json.loads(cap_path.read_text(encoding="utf-8"))
    assert "facts" in cap_data
    for k in CMES_FACT_KEYS:
        assert k in cap_data["facts"], f"missing fact {k}"
    assert accepts_l3_pointer_only_input(cap_data)


def test_feed_capsule_to_l3_dry_run_artifacts_no_raw(e2e_out_dir: Path, fixed_clock) -> None:
    ops_base = e2e_out_dir / "ops"
    l3_out = e2e_out_dir / "l3_out"
    l3_out.mkdir(parents=True, exist_ok=True)
    config = OrchestratorConfig(base_dir=ops_base, run_id="e2e_cmes_l3", input_jsonl_path="")
    _, cap_path = run_ingress(config)
    capsule_dict = json.loads(cap_path.read_text(encoding="utf-8"))
    assert accepts_l3_pointer_only_input(capsule_dict)
    runner = L3Runner(clock=fixed_clock)
    result = runner.run(inputs=capsule_dict, mode="dry-run", out_dir=l3_out)
    assert result.layer_id == "L3"
    assert any("run_manifest.json" in p for p in result.artifacts)
    assert any("operator_output.md" in p for p in result.artifacts)
    assert (l3_out / "run_manifest.json").exists()
    assert (l3_out / "operator_output.md").exists()
