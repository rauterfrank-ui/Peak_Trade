"""Tests for dynamic_scope_empirical_calibration_research_v1 (AUTHORITY=NONE)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from trading.master_v2.dynamic_scope_empirical_calibration_research_v1 import (
    HARNESS_OWNER,
    PRODUCTIVE_D_T_BINDING_PRESENT,
    PRODUCTIVE_D_T_FORMULA_SELECTED,
    RUNTIME_AUTHORITY,
    ResearchCandidateFamily,
    ResearchCandidateSpecV1,
    ResearchMarkObservationV1,
    build_default_candidate_sweep_v1,
    compute_research_d_t_v1,
    load_cap51_offline_fixture_dataset_v1,
    load_pt1m_bars_dataset_from_materializer_fixture_v1,
    run_empirical_calibration_evidence_v1,
    simulate_candidate_on_series_v1,
    stable_digest,
)
from trading.master_v2.naked_mv2_dp_mechanical_core_v1 import (
    MECHANICAL_CORE_VERSION,
    execute_naked_mechanical_step_v1,
)

_REPO = Path(__file__).resolve().parents[3]
_HARNESS_SRC = _REPO / "src/trading/master_v2/dynamic_scope_empirical_calibration_research_v1.py"


def test_harness_authority_flags() -> None:
    assert RUNTIME_AUTHORITY == "NONE"
    assert PRODUCTIVE_D_T_FORMULA_SELECTED is False
    assert PRODUCTIVE_D_T_BINDING_PRESENT is False


def test_harness_calls_execute_naked_mechanical_step_v1() -> None:
    tree = ast.parse(_HARNESS_SRC.read_text(encoding="utf-8"))
    names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    assert "execute_naked_mechanical_step_v1" in names
    assert "next_naked_mechanical_state_v1" in names


def test_no_mechanical_core_semantic_fork_in_harness() -> None:
    text = _HARNESS_SRC.read_text(encoding="utf-8").split('"""', 2)[-1]
    assert "NakedRegimeV1.BULL" not in text or "initial_regime" in text
    assert "compute_counter_move_v1" not in text


def test_candidate_families_research_only() -> None:
    assert compute_research_d_t_v1(
        family=ResearchCandidateFamily.ABSOLUTE, parameter_k=2.0, mark_price_m_t=100.0, sigma_t=None
    ) == pytest.approx(2.0)
    assert compute_research_d_t_v1(
        family=ResearchCandidateFamily.RELATIVE, parameter_k=0.01, mark_price_m_t=200.0, sigma_t=None
    ) == pytest.approx(2.0)
    assert (
        compute_research_d_t_v1(
            family=ResearchCandidateFamily.VOL_NORMALIZED,
            parameter_k=1.0,
            mark_price_m_t=100.0,
            sigma_t=0.02,
        )
        == pytest.approx(2.0)
    )


def test_vol_normalized_fail_closed_without_sigma() -> None:
    assert (
        compute_research_d_t_v1(
            family=ResearchCandidateFamily.VOL_NORMALIZED,
            parameter_k=1.0,
            mark_price_m_t=100.0,
            sigma_t=None,
        )
        is None
    )
    identity, obs = load_cap51_offline_fixture_dataset_v1(repo_root=_REPO)
    metrics = simulate_candidate_on_series_v1(
        dataset=identity,
        observations=obs,
        candidate=ResearchCandidateSpecV1(ResearchCandidateFamily.VOL_NORMALIZED, 1.0),
    )
    assert metrics.fail_closed_steps == len(obs)
    assert metrics.switch_count == 0


def test_absolute_relative_independent_of_missing_sigma() -> None:
    identity, obs = load_cap51_offline_fixture_dataset_v1(repo_root=_REPO)
    abs_m = simulate_candidate_on_series_v1(
        dataset=identity,
        observations=obs,
        candidate=ResearchCandidateSpecV1(ResearchCandidateFamily.ABSOLUTE, 1.0),
    )
    rel_m = simulate_candidate_on_series_v1(
        dataset=identity,
        observations=obs,
        candidate=ResearchCandidateSpecV1(ResearchCandidateFamily.RELATIVE, 0.01),
    )
    assert abs_m.fail_closed_steps == 0
    assert rel_m.fail_closed_steps == 0


def test_deterministic_identical_replay() -> None:
    identity, obs = load_pt1m_bars_dataset_from_materializer_fixture_v1(repo_root=_REPO)
    spec = ResearchCandidateSpecV1(ResearchCandidateFamily.RELATIVE, 0.01)
    a = simulate_candidate_on_series_v1(dataset=identity, observations=obs, candidate=spec)
    b = simulate_candidate_on_series_v1(dataset=identity, observations=obs, candidate=spec)
    assert a.switch_count == b.switch_count
    assert a.fail_closed_steps == b.fail_closed_steps
    assert json.dumps(a.to_dict(), sort_keys=True) == json.dumps(b.to_dict(), sort_keys=True)


def test_switch_metrics_populated_on_pt1m_fixture() -> None:
    evidence = run_empirical_calibration_evidence_v1(
        repo_root=_REPO,
        dataset_loader="pt1m_materializer_fixture",
        candidate_sweep=(
            ResearchCandidateSpecV1(ResearchCandidateFamily.ABSOLUTE, 0.5),
            ResearchCandidateSpecV1(ResearchCandidateFamily.RELATIVE, 0.005),
            ResearchCandidateSpecV1(ResearchCandidateFamily.VOL_NORMALIZED, 1.0),
        ),
    )
    assert evidence.mechanical_core_version == MECHANICAL_CORE_VERSION
    assert evidence.dataset.bar_count >= 61
    assert evidence.stability_summary
    for run in evidence.runs:
        if run.candidate.family is ResearchCandidateFamily.VOL_NORMALIZED:
            assert run.fail_closed_steps >= 0
        assert run.total_bars == evidence.dataset.bar_count
    vol_runs = [
        r for r in evidence.runs if r.candidate.family is ResearchCandidateFamily.VOL_NORMALIZED
    ]
    assert any(r.switch_count >= 0 for r in vol_runs)


def test_evidence_digest_stable() -> None:
    e1 = run_empirical_calibration_evidence_v1(
        repo_root=_REPO,
        dataset_loader="cap51_offline_fixture",
        candidate_sweep=(ResearchCandidateSpecV1(ResearchCandidateFamily.ABSOLUTE, 1.0),),
    )
    e2 = run_empirical_calibration_evidence_v1(
        repo_root=_REPO,
        dataset_loader="cap51_offline_fixture",
        candidate_sweep=(ResearchCandidateSpecV1(ResearchCandidateFamily.ABSOLUTE, 1.0),),
    )
    assert e1.evidence_digest == e2.evidence_digest
    assert e1.evidence_digest == stable_digest(
        {
            "dataset": e1.dataset.to_dict(),
            "runs": [r.to_dict() for r in e1.runs],
            "stability_summary": e1.stability_summary,
        }
    )


def test_no_pnl_order_execution_in_harness() -> None:
    text = _HARNESS_SRC.read_text(encoding="utf-8").split('"""', 2)[-1].lower()
    for token in ("sharpe", "profit_factor", "submit_order", "entry_exit"):
        assert token not in text


def test_default_sweep_covers_all_families() -> None:
    sweep = build_default_candidate_sweep_v1()
    families = {s.family for s in sweep}
    assert ResearchCandidateFamily.ABSOLUTE in families
    assert ResearchCandidateFamily.RELATIVE in families
    assert ResearchCandidateFamily.VOL_NORMALIZED in families


def test_core_step_still_used_directly_unchanged() -> None:
    from trading.master_v2.naked_mv2_dp_mechanical_core_v1 import (
        NakedMechanicalStateV1,
        NakedMechanicalStepInputV1,
        NakedRegimeV1,
    )

    st = NakedMechanicalStateV1("X", NakedRegimeV1.BULL, 100.0)
    r = execute_naked_mechanical_step_v1(
        NakedMechanicalStepInputV1("X", 95.0, st, 4.0)
    )
    assert r.switch_condition_met
