"""Contract tests for ``extract_targets_from_line`` (v0).

String-only markdown lines — no filesystem, subprocess, gates, or network.

Complements normalize-focused tests in ``test_docs_reference_targets_normalize_contract_v0``.
Prod (unchanged): ``src.ops.docs_reference_targets_common``.
"""

from __future__ import annotations

import pytest

from src.ops import docs_reference_targets_common as rtc


def test_extract_targets_from_line_single_markdown_link_contract_v0() -> None:
    # Link phase then bare phase matches the same path inside parentheses again.
    assert rtc.extract_targets_from_line("[overview](docs/ops/guide.md)") == [
        "docs/ops/guide.md",
        "docs/ops/guide.md",
    ]


def test_extract_targets_from_line_multiple_links_preserve_scan_order_contract_v0() -> None:
    line = "[a](docs/a.md) mid [b](src/b.py) tail"
    assert rtc.extract_targets_from_line(line) == [
        "docs/a.md",
        "src/b.py",
        "docs/a.md",
        "src/b.py",
    ]


def test_extract_targets_from_line_link_url_targets_dropped_contract_v0() -> None:
    assert rtc.extract_targets_from_line("[x](https://example.test/doc.md)") == []


def test_extract_targets_from_line_link_anchor_stripped_via_normalize_contract_v0() -> None:
    assert rtc.extract_targets_from_line("[t](docs/c.md#section)") == ["docs/c.md", "docs/c.md"]


def test_extract_targets_from_line_inline_code_span_contract_v0() -> None:
    assert rtc.extract_targets_from_line("run `scripts/ops/check.sh` now") == [
        "scripts/ops/check.sh"
    ]


def test_extract_targets_from_line_bare_repo_path_contract_v0() -> None:
    assert rtc.extract_targets_from_line("See docs/root.md for more.") == ["docs/root.md"]


def test_extract_targets_from_line_bare_skipped_when_overlaps_inline_code_contract_v0() -> None:
    # Inner `docs/in_code.md` is extracted via CODE_RE only; overlapping BARE hit is suppressed.
    line = "Use `docs/in_code.md` or docs/outside.md option"
    assert rtc.extract_targets_from_line(line) == ["docs/in_code.md", "docs/outside.md"]


def test_extract_targets_from_line_link_then_code_order_contract_v0() -> None:
    line = "Link [here](docs/first.md) and `docs/second.md` inline"
    assert rtc.extract_targets_from_line(line) == [
        "docs/first.md",
        "docs/second.md",
        "docs/first.md",
    ]


@pytest.mark.parametrize(
    ("a0", "a1", "spans", "expected"),
    [
        (0, 10, [(2, 4)], True),
        (0, 2, [(5, 6)], False),
        # Half-open touching at boundary: no overlap with [5,10)
        (0, 5, [(5, 10)], False),
        # Partial overlap end
        (4, 6, [(5, 7)], True),
    ],
)
def test_range_overlaps_contract_v0(
    a0: int,
    a1: int,
    spans: list[tuple[int, int]],
    expected: bool,
) -> None:
    assert rtc.range_overlaps(a0, a1, spans) is expected
