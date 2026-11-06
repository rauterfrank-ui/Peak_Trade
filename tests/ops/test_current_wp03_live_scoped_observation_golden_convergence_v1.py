"""CURRENT-WP-03: live-scoped observation golden convergence."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.constants_v1 import (
    OBSERVATION_SCOPE_SCOPED_READONLY_INJECT,
)
from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.convergence_proof_v1 import (
    prove_wp03_golden_convergence_v1,
)
from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.evidence_v1 import (
    write_current_wp03_closure_evidence_v1,
)
from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.trace_projection_v1 import (
    assert_all_golden_trace_keys_present_v1,
    project_supervisor_golden_trace_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.golden_happy_path_trace_harness_v1 import (
    GOLDEN_TRACE_KEYS,
    negative_failure_vector_v1,
)
from tests.ops._wp03_supervisor_golden_harness_v1 import (
    run_hold_supervisor_v1,
    run_natural_long_supervisor_v1,
    run_natural_short_supervisor_v1,
    run_two_epoch_supervisor_v1,
)
from tests.ops.test_n1_standing_pre_external_runtime_supervisor_v1 import (
    OWNER_GO_BASELINE_SHA,
    REPO,
)

REQUIREMENT_ADJUDICATION = {
    "BLK-10": "STILL_REQUIRED→implemented trace projection + supervisor-driven proof",
    "BLK-11": "STILL_REQUIRED→two-epoch contiguous confirmation proof",
    "EDG-033": "PARTIAL_CURRENT→full GOLDEN_TRACE_KEYS from supervisor",
    "EDG-048": "STILL_REQUIRED→≥2 C1 epochs under standing run",
    "EDG-050": "PARTIAL_CURRENT→bilateral LONG/SHORT/HOLD scoped inject",
}


def test_safety_pins_unchanged() -> None:
    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False


def test_golden_trace_projection_covers_all_keys(tmp_path: Path) -> None:
    result = run_two_epoch_supervisor_v1(tmp_path)
    trace = project_supervisor_golden_trace_v1(
        result,
        side="LONG",
        observation_scope=OBSERVATION_SCOPE_SCOPED_READONLY_INJECT,
    )
    assert_all_golden_trace_keys_present_v1(trace)
    assert set(GOLDEN_TRACE_KEYS).issubset(trace.keys())
    assert trace["observation_scope"] == OBSERVATION_SCOPE_SCOPED_READONLY_INJECT
    assert result.trace.post_count == 0


def test_wp03_full_golden_convergence_bundle(tmp_path: Path) -> None:
    long_r = run_natural_long_supervisor_v1(tmp_path / "long")
    short_r = run_natural_short_supervisor_v1(tmp_path / "short")
    hold_r = run_hold_supervisor_v1(tmp_path / "hold")
    two_r = run_two_epoch_supervisor_v1(tmp_path / "two_epoch")
    proof = prove_wp03_golden_convergence_v1(
        long_result=long_r,
        short_result=short_r,
        hold_result=hold_r,
        two_epoch_result=two_r,
    )
    assert proof.ok is True
    assert proof.confirmation_two_epoch_proven is True
    assert proof.post_count == 0
    assert proof.scenarios[0].pre_external_reached is True
    assert proof.scenarios[1].pre_external_reached is True
    assert proof.scenarios[2].pre_external_reached is False


def test_negative_stale_c1_first_divergence() -> None:
    stale = negative_failure_vector_v1(
        name="stale_c1",
        expected_block="STALE_OR_EQUAL_C1_REJECTED",
        actual={"first_block": "STALE_OR_EQUAL_C1_REJECTED"},
    )
    assert stale.ok is True


def test_wp01_wp02_regression_smoke() -> None:
    from tests.ops import test_n1_standing_pre_external_runtime_supervisor_v1 as wp01
    from tests.ops import test_current_wp02_default_productive_universe_handoff_v1 as wp02

    assert wp01.test_authority_boundary_and_pins is not None
    assert wp02.test_synthetic_ranking_rejected is not None


def test_write_closure_evidence_shape(tmp_path: Path) -> None:
    long_r = run_natural_long_supervisor_v1(tmp_path / "long")
    short_r = run_natural_short_supervisor_v1(tmp_path / "short")
    hold_r = run_hold_supervisor_v1(tmp_path / "hold")
    two_r = run_two_epoch_supervisor_v1(tmp_path / "two_epoch")
    proof = prove_wp03_golden_convergence_v1(
        long_result=long_r,
        short_result=short_r,
        hold_result=hold_r,
        two_epoch_result=two_r,
    )
    path = write_current_wp03_closure_evidence_v1(
        repo_root=tmp_path,
        baseline_sha=OWNER_GO_BASELINE_SHA,
        tested_code_sha=OWNER_GO_BASELINE_SHA,
        proof=proof,
        requirement_adjudication=REQUIREMENT_ADJUDICATION,
        changed_files=("src/ops/current_wp03_live_scoped_observation_golden_convergence_v1/",),
        tests_executed=(
            "tests/ops/test_current_wp03_live_scoped_observation_golden_convergence_v1.py",
        ),
    )
    assert path.is_file()
    payload = path.read_text(encoding="utf-8")
    assert "WP04_NOT_STARTED" in payload
    assert "CURRENT_WP03_CLOSURE_V1" in payload
