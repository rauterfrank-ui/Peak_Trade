"""PRE_EXTERNAL → external-effect boundary bounded WP v1 — census + static proof."""

from __future__ import annotations

from shutil import copyfile

import pytest

from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    CONTINUOUS_RUN_ADJUDICATION_CLASS,
    INTENTIONALLY_ISOLATED_OWNER_GO_POST_SLICES,
    INTENTIONALLY_LEGACY_PRE_EXTERNAL_CLAIM_MODULES,
    PERMIT_MINT_ADJUDICATION_CLASS,
    PRE_EXTERNAL_PRODUCTIVE_ENTRY_MODULES,
    PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY_COMPLETE,
    REQUIRED_CLOSURE_COUNT,
    STANDING_LIVE_PREDICATES_ADJUDICATION_CLASS,
    STEP_29Q_ADJUDICATION_CLASS,
    UNKNOWN_BOUNDARY_PATH_COUNT,
    prove_pre_external_to_external_effect_boundary_v1,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1 import proof_v1


def test_census_verdict_frozen() -> None:
    assert BASELINE_ORIGIN_MAIN_SHA == "08fa64c22cfa073c2b32ee9238828b83694790c2"
    assert REQUIRED_CLOSURE_COUNT == 0
    assert UNKNOWN_BOUNDARY_PATH_COUNT == 0
    assert PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY_COMPLETE is True
    assert STANDING_LIVE_PREDICATES_ADJUDICATION_CLASS == "NON_IMPLYING_STANDING_TRUE"
    assert STEP_29Q_ADJUDICATION_CLASS == "PLAN_ONLY_FAIL_CLOSED"
    assert PERMIT_MINT_ADJUDICATION_CLASS == "INTENTIONALLY_ISOLATED_OWNER_GO"
    assert CONTINUOUS_RUN_ADJUDICATION_CLASS == "POLICY_AUTHORIZED_ORCHESTRATOR_MODULE_PIN_FALSE"
    assert len(PRE_EXTERNAL_PRODUCTIVE_ENTRY_MODULES) == 5
    assert len(INTENTIONALLY_LEGACY_PRE_EXTERNAL_CLAIM_MODULES) == 3
    assert len(INTENTIONALLY_ISOLATED_OWNER_GO_POST_SLICES) == 10


def test_simulated_post_isolation_does_not_change_policy_admission() -> None:
    result = prove_pre_external_to_external_effect_boundary_v1()
    assert result.whole_system_connection_ok is True
    assert not result.guard_failures
    assert not result.pre_external_sink_violations
    assert not result.boundary_chain_failures
    simulation = proof_v1.read_simulated_post_isolation_v1()
    assert simulation.source_binding_verified
    assert simulation.policy_authority_effect == "NONE"
    assert result.unclassified_sink_callers == (simulation.path,)
    assert not result.ok


@pytest.mark.parametrize("drifted", [0, 1, 2, 3])
def test_simulated_post_isolation_refuses_changes_in_each_reviewed_source(
    tmp_path, monkeypatch, drifted
) -> None:
    paths = [path for path, _ in proof_v1._FUTURES_SIM_POST_SOURCES]
    for path in paths:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(proof_v1._REPO_ROOT / path, target)
    changed = tmp_path / paths[drifted]
    changed.write_bytes(changed.read_bytes() + b"\n# changed after review\n")
    monkeypatch.setattr(proof_v1, "_REPO_ROOT", tmp_path)
    result = proof_v1.read_simulated_post_isolation_v1()
    assert not result.source_binding_verified
    assert result.mismatched_paths == (paths[drifted],)
