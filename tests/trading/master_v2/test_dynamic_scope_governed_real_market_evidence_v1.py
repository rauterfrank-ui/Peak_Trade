"""Tests for governed REAL market Dynamic Scope evidence v1 (AUTHORITY=NONE)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from trading.master_v2.dynamic_scope_empirical_calibration_research_v1 import (
    LineageClass,
    PRODUCTIVE_D_T_BINDING_PRESENT,
    PRODUCTIVE_D_T_FORMULA_SELECTED,
    RUNTIME_AUTHORITY,
    build_default_candidate_sweep_v1,
)
from trading.master_v2.dynamic_scope_governed_real_market_evidence_v1 import (
    DEFAULT_BINDING_ID,
    EVIDENCE_OWNER,
    GovernedRealMarketEvidenceError,
    load_governed_real_market_observation_series_v1,
    run_governed_real_market_evidence_v1,
)
from trading.master_v2.naked_mv2_dp_mechanical_core_v1 import MECHANICAL_CORE_VERSION

_REPO = Path(__file__).resolve().parents[3]
_EVIDENCE_SRC = _REPO / "src/trading/master_v2/dynamic_scope_governed_real_market_evidence_v1.py"
_ARTIFACT_DIR = _REPO / "docs/evidence/dynamic_scope_governed_real_market_evidence_v1"
_SUMMARY = _ARTIFACT_DIR / "SUMMARY.json"
_FULL = _ARTIFACT_DIR / "governed_real_market_calibration_evidence_v1.json"


def test_evidence_module_authority_flags() -> None:
    assert RUNTIME_AUTHORITY == "NONE"
    assert PRODUCTIVE_D_T_FORMULA_SELECTED is False
    assert PRODUCTIVE_D_T_BINDING_PRESENT is False


def test_governed_loader_uses_mechanical_core_via_research_harness() -> None:
    tree = ast.parse(_EVIDENCE_SRC.read_text(encoding="utf-8"))
    names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    assert "simulate_candidate_on_series_v1" in names
    assert "execute_naked_mechanical_step_v1" not in names


def test_real_dataset_lineage_complete() -> None:
    lineage, identity, observations = load_governed_real_market_observation_series_v1(
        repo_root=_REPO,
        binding_id=DEFAULT_BINDING_ID,
    )
    assert lineage.lineage_labels["market_observations"] == LineageClass.OBSERVED.value
    assert identity.lineage_class is LineageClass.OBSERVED
    assert lineage.observation_count == len(observations)
    assert lineage.observation_count >= 200
    assert lineage.volatility_valid_observations >= 100
    assert "fixture" not in lineage.source_path.lower()
    assert identity.source_path.startswith("docs/ops/artifacts/")


def test_dataset_digest_deterministic() -> None:
    e1 = run_governed_real_market_evidence_v1(repo_root=_REPO)
    e2 = run_governed_real_market_evidence_v1(repo_root=_REPO)
    assert e1.lineage.dataset_digest == e2.lineage.dataset_digest
    assert e1.evidence_digest == e2.evidence_digest


def test_identical_input_identical_evidence_payload() -> None:
    e1 = run_governed_real_market_evidence_v1(repo_root=_REPO)
    e2 = run_governed_real_market_evidence_v1(repo_root=_REPO)
    assert json.dumps(e1.to_dict(), sort_keys=True) == json.dumps(e2.to_dict(), sort_keys=True)


def test_all_candidate_families_on_same_series() -> None:
    evidence = run_governed_real_market_evidence_v1(repo_root=_REPO)
    families = {r["candidate_family"] for r in evidence.calibration_runs}
    assert families == {"absolute", "relative", "vol_normalized"}
    bar_counts = {r["total_bars"] for r in evidence.calibration_runs}
    assert len(bar_counts) == 1
    assert evidence.lineage.observation_count in bar_counts


def test_vol_normalized_fail_closed_during_warmup_only() -> None:
    evidence = run_governed_real_market_evidence_v1(repo_root=_REPO)
    vol_runs = [r for r in evidence.calibration_runs if r["candidate_family"] == "vol_normalized"]
    assert vol_runs
    assert all(r["fail_closed_steps"] > 0 for r in vol_runs)
    abs_runs = [r for r in evidence.calibration_runs if r["candidate_family"] == "absolute"]
    assert all(r["fail_closed_steps"] == 0 for r in abs_runs)


def test_committed_artifacts_match_regenerated_digest() -> None:
    if not _SUMMARY.is_file() or not _FULL.is_file():
        pytest.skip("evidence artifacts not materialized in workspace")
    evidence = run_governed_real_market_evidence_v1(repo_root=_REPO)
    summary = json.loads(_SUMMARY.read_text(encoding="utf-8"))
    assert summary["EVIDENCE_DIGEST"] == evidence.evidence_digest
    assert summary["DATASET_DIGEST"] == evidence.lineage.dataset_digest
    full = json.loads(_FULL.read_text(encoding="utf-8"))
    assert full["evidence_digest"] == evidence.evidence_digest
    assert full["mechanical_core_version"] == MECHANICAL_CORE_VERSION


def test_no_pnl_or_execution_tokens_in_evidence_owner() -> None:
    text = _EVIDENCE_SRC.read_text(encoding="utf-8").split('"""', 2)[-1].lower()
    for token in ("sharpe", "profit_factor", "submit_order", "testnet", "live_order"):
        assert token not in text


def test_unknown_binding_fail_closed() -> None:
    with pytest.raises(GovernedRealMarketEvidenceError, match="unknown_binding"):
        load_governed_real_market_observation_series_v1(
            repo_root=_REPO,
            binding_id="does_not_exist",
        )


def test_evidence_owner_constant() -> None:
    assert EVIDENCE_OWNER.endswith("dynamic_scope_governed_real_market_evidence_v1")


def test_stability_and_sensitivity_present() -> None:
    evidence = run_governed_real_market_evidence_v1(repo_root=_REPO)
    assert evidence.stability_summary
    for fam in ("absolute", "relative", "vol_normalized"):
        assert fam in evidence.family_summaries
        assert evidence.family_summaries[fam]["sensitivity_results"]
    assert evidence.factual_comparison["families"]


def test_parameter_grid_matches_default_sweep() -> None:
    evidence = run_governed_real_market_evidence_v1(repo_root=_REPO)
    sweep = build_default_candidate_sweep_v1()
    assert len(evidence.parameter_grid) == len(sweep)
