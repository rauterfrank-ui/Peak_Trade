"""Contract tests for docs reference-target helpers (v0).

Pure string semantics — no subprocess, gates, filesystem, or network.

Subject module (unchanged): ``src.ops.docs_reference_targets_common``.
"""

from __future__ import annotations

import pytest

from src.ops import docs_reference_targets_common as rtc


def test_ignore_marker_public_constant_contract_v0() -> None:
    assert "<!-- pt:ref-target-ignore -->" == rtc.IGNORE_MARKER


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://example.test/path", True),
        ("http://localhost:8000/", True),
        (" mailto:user@example.test ", True),
        ("ftp://files.example/asset", True),
        ("scheme://anything", True),
        ("relative/docs/foo.md", False),
        ("docs/foo.md", False),
        ("./docs/foo.md", False),
        ("/docs/foo.md", False),
        # Scheme not lower-case: fails startswith(http/https/mailto) but "://" sentinel matches.
        ("HTTPS://EXAMPLE.TEST", True),
    ],
)
def test_is_url_contract_v0(raw: str, expected: bool) -> None:
    assert rtc.is_url(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("docs/ops/guide.md", "docs/ops/guide.md"),
        ("  docs/ops/guide.md  ", "docs/ops/guide.md"),
        ("(docs/ops/guide.md)", "docs/ops/guide.md"),
        ('"docs/ops/guide.md"', "docs/ops/guide.md"),
        ("docs/ops/guide.md#section", "docs/ops/guide.md"),
        ("docs/ops/guide.md?plain=1", "docs/ops/guide.md"),
        ("docs/ops/guide.md?plain=1#sec", "docs/ops/guide.md"),
        ("https://example.test/doc.md", None),
        ("#only-anchor", None),
        ("", None),
        ("   ", None),
        ("/docs/ops/guide.md", "docs/ops/guide.md"),
        ("scripts&#47;ops&#47;verify.sh", "scripts/ops/verify.sh"),
        ("./scripts/ops/helpers.sh", "./scripts/ops/helpers.sh"),
        ("../docs/ops/other.md", "../docs/ops/other.md"),
        ("config/peaks.toml", "config/peaks.toml"),
        (".github/workflows/ci.yml", ".github/workflows/ci.yml"),
        ("src/__init__.py", "src/__init__.py"),
        ("not-a-root/file.md", None),
        ("readme.md", None),
        ("docs/glob *.md", None),
        # "?" is treated like query split; stem before ? must still be repo-root-valid.
        ("docs/x?.md", "docs/x"),
        ("docs/glob*.md", None),
        ("docs/dir/", None),
        ("docs/with space/file.md", None),
    ],
)
def test_normalize_target_contract_v0(raw: str, expected: str | None) -> None:
    assert rtc.normalize_target(raw) == expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("", []),
        ("no backticks here", []),
        ("plain `single` trailing", [(6, 14)]),
        ("`first` middle `second` end", [(0, 7), (15, 23)]),
    ],
)
def test_inline_code_spans_contract_v0(
    line: str,
    expected: list[tuple[int, int]],
) -> None:
    assert rtc.inline_code_spans(line) == expected
