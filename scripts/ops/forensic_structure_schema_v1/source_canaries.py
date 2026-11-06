"""Independent Source-byte structural canaries.

These are drift detectors only. They do not synthesize overlays, infer
nested-fence semantics, or close SW-R-006.

Bound counting rules (previously adjudicated; not chosen silently):

TRIPLE_BACKTICK_SOURCE_LINE_COUNT
  Count of Source lines, after stripping a terminating LF and at most one
  trailing CR, whose remaining bytes start at column 0 with three or more
  backtick characters. Indent-stripped and unstripped counts match on the
  bound corpus; the bound rule is column-0 start.

INNER_FENCE_LIKE_COUNT
  Walk those fence-like lines in Source order. Maintain a stack of open
  tick lengths. Empty stack -> OPEN (push tick_len). Non-empty and
  tick_len >= current open tick_len -> CLOSE (pop). Otherwise count one
  INNER_FENCE_LIKE line and do not push or pop. No overlay is created.

TICK5_OUTER_COUNT
  Number of OPEN events whose tick_len == 5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scripts.ops.forensic_structure_schema_v1.constants import (
    EXPECTED_INNER_FENCE_LIKE_COUNT,
    EXPECTED_TICK5_OUTER_COUNT,
    EXPECTED_TRIPLE_BACKTICK_SOURCE_LINE_COUNT,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)

COUNTING_RULES = {
    "TRIPLE_BACKTICK_SOURCE_LINE": (
        "source_line_after_lf_cr_strip_starts_at_column_0_with_three_or_more_backticks"
    ),
    "INNER_FENCE_LIKE": (
        "fence_like_line_while_stack_open_with_strictly_shorter_tick_len_no_push_no_pop"
    ),
    "TICK5_OUTER": "open_event_on_empty_stack_with_tick_len_equal_5",
}


@dataclass(frozen=True)
class SourceCanaryReport:
    passed: bool
    triple_backtick_source_line_count: int
    inner_fence_like_count: int
    tick5_outer_count: int
    open_count: int
    close_count: int
    unclosed_count: int
    synthesizes_overlays: bool
    closes_sw_r_006: bool
    detail: str

    def to_canonical(self) -> dict[str, Any]:
        return {
            "role": "SOURCE_DERIVED_STRUCTURAL_CANARY",
            "authority": "NONE",
            "status": "PASS" if self.passed else "FAIL",
            "passed": self.passed,
            "counting_rules": dict(COUNTING_RULES),
            "triple_backtick_source_line_count": self.triple_backtick_source_line_count,
            "inner_fence_like_count": self.inner_fence_like_count,
            "tick5_outer_count": self.tick5_outer_count,
            "open_count": self.open_count,
            "close_count": self.close_count,
            "unclosed_count": self.unclosed_count,
            "expected_triple_backtick_source_line_count": (
                EXPECTED_TRIPLE_BACKTICK_SOURCE_LINE_COUNT
            ),
            "expected_inner_fence_like_count": EXPECTED_INNER_FENCE_LIKE_COUNT,
            "expected_tick5_outer_count": EXPECTED_TICK5_OUTER_COUNT,
            "synthesizes_overlays": self.synthesizes_overlays,
            "closes_sw_r_006": self.closes_sw_r_006,
            "sw_r_006_status": "OPEN",
            "detail": self.detail,
        }


def _line_without_terminator(line: bytes) -> bytes:
    if line.endswith(b"\n"):
        line = line[:-1]
    if line.endswith(b"\r"):
        line = line[:-1]
    return line


def _tick_len_if_fence_like(line: bytes) -> int | None:
    stripped = _line_without_terminator(line)
    if not stripped.startswith(b"```"):
        return None
    ticks = 0
    for char in stripped:
        if char == 0x60:
            ticks += 1
        else:
            break
    if ticks < 3:
        return None
    return ticks


def measure_source_canaries(source_bytes: bytes) -> SourceCanaryReport:
    """Measure canaries from Source bytes only. Sidecar cardinalities are unused."""
    lines = source_bytes.splitlines(keepends=True)
    triple = 0
    inner = 0
    tick5_outer = 0
    opens = 0
    closes = 0
    stack: list[int] = []
    for line in lines:
        tick_len = _tick_len_if_fence_like(line)
        if tick_len is None:
            continue
        triple += 1
        if not stack:
            stack.append(tick_len)
            opens += 1
            if tick_len == 5:
                tick5_outer += 1
            continue
        if tick_len >= stack[-1]:
            stack.pop()
            closes += 1
        else:
            inner += 1
    return SourceCanaryReport(
        passed=True,
        triple_backtick_source_line_count=triple,
        inner_fence_like_count=inner,
        tick5_outer_count=tick5_outer,
        open_count=opens,
        close_count=closes,
        unclosed_count=len(stack),
        synthesizes_overlays=False,
        closes_sw_r_006=False,
        detail="measured",
    )


def assert_bound_source_canaries(source_bytes: bytes) -> SourceCanaryReport:
    report = measure_source_canaries(source_bytes)
    expected = (
        EXPECTED_TRIPLE_BACKTICK_SOURCE_LINE_COUNT,
        EXPECTED_INNER_FENCE_LIKE_COUNT,
        EXPECTED_TICK5_OUTER_COUNT,
    )
    observed = (
        report.triple_backtick_source_line_count,
        report.inner_fence_like_count,
        report.tick5_outer_count,
    )
    if observed != expected:
        raise TransformationContractViolation(
            "SOURCE_CANARY_DRIFT",
            (
                "source canaries "
                f"triple={observed[0]} inner={observed[1]} tick5_outer={observed[2]} "
                f"!= expected triple={expected[0]} inner={expected[1]} "
                f"tick5_outer={expected[2]}"
            ),
        )
    if report.synthesizes_overlays or report.closes_sw_r_006:
        raise TransformationContractViolation(
            "SW-R-006",
            "source canaries must not synthesize overlays or close SW-R-006",
        )
    return SourceCanaryReport(
        passed=True,
        triple_backtick_source_line_count=report.triple_backtick_source_line_count,
        inner_fence_like_count=report.inner_fence_like_count,
        tick5_outer_count=report.tick5_outer_count,
        open_count=report.open_count,
        close_count=report.close_count,
        unclosed_count=report.unclosed_count,
        synthesizes_overlays=False,
        closes_sw_r_006=False,
        detail="bound source canaries matched",
    )
