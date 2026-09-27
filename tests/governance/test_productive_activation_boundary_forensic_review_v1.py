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
    assert GLOBAL_PRODUCTIVE_ACTIVATION_ADJUDICATION_CLASS == "DEFINED_NOT_AUTHORIZED"
    assert F1_M9_CONSUMER_REACHABILITY_ADJUDICATION_CLASS == "WIRED_NOT_ACTIVATION"


def test_static_productive_activation_boundary_forensic_proof() -> None:
    result = prove_productive_activation_boundary_forensic_review_v1()
    assert result.ok is True, (
        f"guard={result.guard_failures} decisions={result.decision_failures} "
        f"runtime={result.runtime_path_failures} semantic={result.semantic_collision_failures} "
        f"upstream={result.upstream_closure_failures}"
    )


def test_governed_closure() -> None:
    assert prove_governed_productive_activation_boundary_forensic_review_v1() is True
