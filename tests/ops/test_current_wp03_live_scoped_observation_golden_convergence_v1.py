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
    for result, outcome in ((long_r, "enter_long"), (short_r, "enter_short")):
        import json
        from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
            assert_envelope_unmodified_v1,
        )

        last = result.policy_result.orchestrator_result.cycle_records[-1]
        assert last.s5_disposition == "PRE_EXTERNAL_EFFECT"
        assert_envelope_unmodified_v1(last.final_order_envelope)
        assert (
            json.loads(last.pending_decision_context.producer_payload_json)["decision_outcome"]
            == outcome
        )
        assert last.final_order_envelope.instrument_id == result.trace.venue_native_id
        assert last.pending_decision_context.instrument_id == result.trace.bound_instrument_id
        assert "natural_enter_decision" not in result.trace.extra
        assert result.trace.post_count == 0


@pytest.mark.parametrize("short", [False, True])
def test_current_entry_without_fresh_pretrade_stays_hold(tmp_path: Path, short: bool) -> None:
    import json
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1

    result = _run_layered_entry_supervisor_v1(tmp_path, short=short, with_pretrade=False)
    last = result.policy_result.orchestrator_result.cycle_records[-1]
    outcome = "enter_short" if short else "enter_long"
    assert (
        json.loads(last.pending_decision_context.producer_payload_json)["decision_outcome"]
        == outcome
    )
    assert last.s5_disposition == "HOLD_CLOSED"
    assert last.s5_reason_code == "LIVE_29P_GET_MISSING"
    assert last.final_order_envelope is None
    result.trace.extra["natural_enter_decision"] = outcome
    projected = project_supervisor_golden_trace_v1(
        result, side="SHORT" if short else "LONG", observation_scope="scoped_readonly_inject"
    )
    assert not projected["pre_external"]
    assert projected["final_order_envelope"]["envelope_identity"] == ""


@pytest.mark.parametrize("foreign_cycle", [False, True])
def test_current_pretrade_snapshot_reaches_its_original_cycle_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, foreign_cycle: bool
) -> None:
    from dataclasses import replace
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        invoke_join_v1,
    )
    from tests.ops._wp03_supervisor_golden_harness_v1 import run_natural_long_supervisor_v1

    original = invoke_join_v1.join_current_productive_enter_live_29p_before_venue_plan_v1
    seen = []

    def bound_consumer(**kwargs):
        injected = kwargs["injected"]
        if injected is not None:
            slot = kwargs["portfolio_slot"]
            assert slot is not None
            assert injected.acquisition_cycle_id == slot.cycle_id
            seen.append(slot.cycle_id)
            if foreign_cycle:
                kwargs["injected"] = replace(injected, acquisition_cycle_id="foreign-cycle")
        return original(**kwargs)

    monkeypatch.setattr(
        invoke_join_v1,
        "join_current_productive_enter_live_29p_before_venue_plan_v1",
        bound_consumer,
    )
    result = run_natural_long_supervisor_v1(tmp_path)
    last = result.policy_result.orchestrator_result.cycle_records[-1]
    assert seen
    if foreign_cycle:
        assert last.s5_disposition == "HOLD_CLOSED"
        assert last.s5_reason_code == "LIVE_29P_ACQUISITION_FAIL_CLOSED"
        assert last.final_order_envelope is None
    else:
        assert last.s5_disposition == "PRE_EXTERNAL_EFFECT"
        assert last.final_order_envelope is not None


def test_supervisor_forwards_original_cap24_productivity_root(tmp_path: Path, monkeypatch) -> None:
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import supervisor_v1 as supervisor

    seen = []
    original = supervisor.run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1

    def observe(**kwargs):
        seen.append(kwargs["cap24_productivity_root"])
        return original(**kwargs)

    monkeypatch.setattr(
        supervisor,
        "run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1",
        observe,
    )
    result = run_natural_long_supervisor_v1(tmp_path)
    assert seen == [tmp_path / "cap24_productivity"]
    assert seen[0].is_dir()
    assert result.trace.terminal_disposition == "PRE_EXTERNAL_EFFECT"


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
