"""Productive Activation boundary forensic review v1 — census + static proof."""

from __future__ import annotations

from src.governance.governed_productive_activation_boundary_forensic_review_closure_v1 import (
    prove_governed_productive_activation_boundary_forensic_review_v1,
)
from src.governance.productive_activation_boundary_forensic_review_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    F1_M9_CONSUMER_REACHABILITY_ADJUDICATION_CLASS,
    GLOBAL_PRODUCTIVE_ACTIVATION_ADJUDICATION_CLASS,
    PRODUCTIVE_ACTIVATION_BOUNDARY_REVIEW_COMPLETE,
    prove_productive_activation_boundary_forensic_review_v1,
)


def test_census_verdict_frozen() -> None:
    assert BASELINE_ORIGIN_MAIN_SHA == "d590b8142210680805f8dc159c5a2fb684e87737"
    assert PRODUCTIVE_ACTIVATION_BOUNDARY_REVIEW_COMPLETE is True
    assert GLOBAL_PRODUCTIVE_ACTIVATION_ADJUDICATION_CLASS == "POLICY_AUTHORIZED_BOUNDED_ADMISSION"
    assert F1_M9_CONSUMER_REACHABILITY_ADJUDICATION_CLASS == "WIRED_NOT_ACTIVATION"


def test_static_productive_activation_review_reports_open_pre_external_proof() -> None:
    result = prove_productive_activation_boundary_forensic_review_v1()
    assert result.ok is False
    assert "PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY" in result.upstream_closure_failures
    assert all(reason.startswith("RUNBOOK_MISSING:") for reason in result.guard_failures)
    assert not result.decision_failures
    assert not result.runtime_path_failures
    assert not result.semantic_collision_failures


def test_governed_closure_fail_closed() -> None:
    assert prove_governed_productive_activation_boundary_forensic_review_v1() is False
