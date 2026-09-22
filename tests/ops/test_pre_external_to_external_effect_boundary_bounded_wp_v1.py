"""PRE_EXTERNAL → external-effect boundary bounded WP v1 — census + static proof."""

from __future__ import annotations

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


def test_census_verdict_frozen() -> None:
    assert BASELINE_ORIGIN_MAIN_SHA == "08fa64c22cfa073c2b32ee9238828b83694790c2"
    assert REQUIRED_CLOSURE_COUNT == 0
    assert UNKNOWN_BOUNDARY_PATH_COUNT == 0
    assert PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY_COMPLETE is True
    assert STANDING_LIVE_PREDICATES_ADJUDICATION_CLASS == "NON_IMPLYING_STANDING_TRUE"
    assert STEP_29Q_ADJUDICATION_CLASS == "PLAN_ONLY_FAIL_CLOSED"
    assert PERMIT_MINT_ADJUDICATION_CLASS == "INTENTIONALLY_ISOLATED_OWNER_GO"
    assert CONTINUOUS_RUN_ADJUDICATION_CLASS == "DEFINED_NOT_AUTHORIZED"
    assert len(PRE_EXTERNAL_PRODUCTIVE_ENTRY_MODULES) == 5
    assert len(INTENTIONALLY_LEGACY_PRE_EXTERNAL_CLAIM_MODULES) == 3
    assert len(INTENTIONALLY_ISOLATED_OWNER_GO_POST_SLICES) == 4


def test_static_pre_external_to_external_effect_boundary_proof() -> None:
    result = prove_pre_external_to_external_effect_boundary_v1()
    assert result.whole_system_connection_ok is True
    assert result.ok is True, (
        f"guard={result.guard_failures} pre_external={result.pre_external_sink_violations} "
        f"unclassified={result.unclassified_sink_callers} boundary={result.boundary_chain_failures}"
    )
