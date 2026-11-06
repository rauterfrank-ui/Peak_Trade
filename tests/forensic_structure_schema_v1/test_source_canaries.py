"""Independent Source canary tests. Sidecar cardinalities are not the source."""

from __future__ import annotations

import pytest

from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    bound_inputs_available,
    run_bound_transformer,
)
from scripts.ops.forensic_structure_schema_v1.constants import (
    EXPECTED_INNER_FENCE_LIKE_COUNT,
    EXPECTED_TICK5_OUTER_COUNT,
    EXPECTED_TRIPLE_BACKTICK_SOURCE_LINE_COUNT,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.source_canaries import (
    COUNTING_RULES,
    assert_bound_source_canaries,
    measure_source_canaries,
)


def test_counting_rules_are_bound_and_exposed() -> None:
    assert COUNTING_RULES["TRIPLE_BACKTICK_SOURCE_LINE"].startswith("source_line_")
    assert "strictly_shorter_tick_len" in COUNTING_RULES["INNER_FENCE_LIKE"]
    assert COUNTING_RULES["TICK5_OUTER"].endswith("tick_len_equal_5")


def test_synthetic_inner_fence_like_and_tick5_outer() -> None:
    source = b"`````outer\n```inner-like\n`````\n```plain\n```\n"
    report = measure_source_canaries(source)
    assert report.triple_backtick_source_line_count == 5
    assert report.inner_fence_like_count == 1
    assert report.tick5_outer_count == 1
    assert report.open_count == 2
    assert report.close_count == 2
    assert report.synthesizes_overlays is False
    assert report.closes_sw_r_006 is False


def test_contains_triple_backtick_is_not_the_bound_line_count() -> None:
    source = b"see ``` inside narrative\n```\n```\n"
    report = measure_source_canaries(source)
    assert source.count(b"```") == 3
    assert report.triple_backtick_source_line_count == 2


def test_canary_drift_is_rejected() -> None:
    source = b"```\n```\n"
    with pytest.raises(TransformationContractViolation) as exc:
        assert_bound_source_canaries(source)
    assert exc.value.rule == "SOURCE_CANARY_DRIFT"


@pytest.mark.skipif(not bound_inputs_available(), reason="bound forensic inputs absent")
def test_bound_source_reproduces_adjudicated_canaries() -> None:
    result = run_bound_transformer()
    report = assert_bound_source_canaries(result.state.source_bytes)
    assert report.inner_fence_like_count == EXPECTED_INNER_FENCE_LIKE_COUNT == 74
    assert report.tick5_outer_count == EXPECTED_TICK5_OUTER_COUNT == 13
    assert report.triple_backtick_source_line_count == (EXPECTED_TRIPLE_BACKTICK_SOURCE_LINE_COUNT)
    assert report.triple_backtick_source_line_count == 2810
    assert report.synthesizes_overlays is False
    assert report.closes_sw_r_006 is False
    residual = next(r for r in result.state.residuals if r.residual_id == "SW-R-006")
    assert residual.status == "OPEN"
    pipeline = result.state.source_canary_report
    assert pipeline is not None
    assert pipeline["inner_fence_like_count"] == 74
    assert pipeline["tick5_outer_count"] == 13
    assert pipeline["triple_backtick_source_line_count"] == 2810
    assert pipeline["counting_rules"] == COUNTING_RULES
