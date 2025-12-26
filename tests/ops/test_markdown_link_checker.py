from pathlib import Path

from scripts.ops.check_markdown_links import _github_slugify, check_links


def test_github_slugify_basic():
    assert _github_slugify("Hello World") == "hello-world"
    assert _github_slugify("  Hello   World  ") == "hello-world"
    assert _github_slugify("Hello, World!") == "hello-world"
    assert _github_slugify("X/Y + Z") == "xy-z"


def test_check_links_file_and_anchor(tmp_path: Path):
    root = tmp_path

    (root / "docs").mkdir()
    (root / "docs" / "ops").mkdir(parents=True, exist_ok=True)

    a = root / "docs" / "ops" / "a.md"
    b = root / "docs" / "ops" / "b.md"

    a.write_text(
        "# A Doc\n\n"
        "Link OK: [b](b.md)\n"
        "Anchor OK: [b#h](b.md#heading)\n"
        "Inpage OK: [self](#a-doc)\n",
        encoding="utf-8",
    )
    b.write_text("# Heading\n\nText.\n", encoding="utf-8")

    broken = check_links(root=root, paths=["docs/ops"])
    assert broken == []


def test_check_links_detects_broken(tmp_path: Path):
    root = tmp_path
    (root / "docs" / "ops").mkdir(parents=True, exist_ok=True)

    a = root / "docs" / "ops" / "a.md"
    a.write_text(
        "# A\n\nBroken file: [x](missing.md)\nBroken anchor: [y](a.md#nope)\n",
        encoding="utf-8",
    )

    broken = check_links(root=root, paths=["docs/ops"])
    reasons = [b.reason for b in broken]
    assert any("does not exist" in r for r in reasons)
    assert any("anchor" in r for r in reasons)
