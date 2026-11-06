"""CLI contract tests for scripts/ops/verify_docs_reference_targets_trend.sh (fixture repo + fake scanner)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SOURCE_VERIFY = ROOT / "scripts" / "ops" / "verify_docs_reference_targets_trend.sh"

_FAKE_SCANNER = '''#!/usr/bin/env python3
"""Test double: emit deterministic JSON for trend verify (contract tests only)."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", dest="output", required=True)
    args = parser.parse_args()
    count = int(os.environ["PT_TREND_FAKE_MISSING_COUNT"])
    items = json.loads(os.environ.get("PT_TREND_FAKE_MISSING_ITEMS", "[]"))
    payload = {"missing_count": count, "missing_items": items}
    Path(args.output).write_text(json.dumps(payload) + "\\n", encoding="utf-8")


if __name__ == "__main__":
    main()
'''


def _install_ops_tree(fake_repo: Path) -> Path:
    ops = fake_repo / "scripts" / "ops"
    ops.mkdir(parents=True, exist_ok=True)
    verify = ops / "verify_docs_reference_targets_trend.sh"
    shutil.copyfile(_SOURCE_VERIFY, verify)
    verify.chmod(0o755)
    scanner = ops / "collect_docs_reference_targets_fullscan.py"
    scanner.write_text(_FAKE_SCANNER.lstrip(), encoding="utf-8")
    scanner.chmod(0o755)
    return verify


def _baseline_path(fake_repo: Path) -> Path:
    p = fake_repo / "docs" / "ops" / "baseline.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _run(
    verify: Path,
    *,
    extra_args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = {**os.environ, **(env or {})}
    return subprocess.run(
        ["bash", str(verify), *(extra_args or [])],
        cwd=verify.parent.parent.parent,
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def test_help_exits_zero(tmp_path: Path) -> None:
    verify = _install_ops_tree(tmp_path)
    p = _run(verify, extra_args=["--help"])
    assert p.returncode == 0
    assert "verify_docs_reference_targets_trend.sh" in p.stdout
    assert "Exit codes:" in p.stdout
    assert p.stderr == ""


def test_help_short_flag_exits_zero(tmp_path: Path) -> None:
    verify = _install_ops_tree(tmp_path)
    p = _run(verify, extra_args=["-h"])
    assert p.returncode == 0
    assert "Usage:" in p.stdout
    assert p.stderr == ""


def test_unknown_arg_exits_nonzero(tmp_path: Path) -> None:
    verify = _install_ops_tree(tmp_path)
    p = _run(verify, extra_args=["--not-a-real-flag"])
    assert p.returncode == 1
    assert "Unknown arg:" in p.stdout
    assert "Usage:" in p.stdout


def test_warn_when_baseline_missing(tmp_path: Path) -> None:
    verify = _install_ops_tree(tmp_path)
    missing = tmp_path / "docs" / "ops" / "nope.json"
    p = _run(
        verify,
        extra_args=["--repo-root", str(tmp_path), "--baseline", str(missing)],
    )
    assert p.returncode == 2
    assert "WARN: Baseline not found:" in p.stdout
    assert str(missing) in p.stdout
    assert p.stderr == ""


def test_warn_when_baseline_json_invalid(tmp_path: Path) -> None:
    verify = _install_ops_tree(tmp_path)
    bl = _baseline_path(tmp_path)
    bl.write_text("not json", encoding="utf-8")
    p = _run(
        verify,
        extra_args=["--repo-root", str(tmp_path), "--baseline", str(bl)],
    )
    assert p.returncode == 2
    assert "WARN: Failed to parse baseline JSON:" in p.stdout
    assert p.stderr == ""


def test_fail_when_current_scan_json_unreadable(tmp_path: Path) -> None:
    verify = _install_ops_tree(tmp_path)
    bl = _baseline_path(tmp_path)
    bl.write_text(
        json.dumps({"missing_count": 0, "missing_items": []}),
        encoding="utf-8",
    )

    scanner = tmp_path / "scripts" / "ops" / "collect_docs_reference_targets_fullscan.py"
    scanner.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import argparse",
                "from pathlib import Path",
                "p = argparse.ArgumentParser()",
                'p.add_argument("--output", "-o", required=True)',
                "args = p.parse_args()",
                'Path(args.output).write_text("%%%not-json%%%\\n", encoding="utf-8")',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    scanner.chmod(0o755)

    p = _run(
        verify,
        extra_args=["--repo-root", str(tmp_path), "--baseline", str(bl)],
        env={"PT_TREND_FAKE_MISSING_COUNT": "0"},
    )
    assert p.returncode == 1
    assert "FAIL: Could not parse current scan results" in p.stdout
    assert p.stderr == ""


def test_pass_debt_stable_when_counts_equal(tmp_path: Path) -> None:
    verify = _install_ops_tree(tmp_path)
    bl = _baseline_path(tmp_path)
    bl.write_text(
        json.dumps({"missing_count": 2, "missing_items": []}),
        encoding="utf-8",
    )
    p = _run(
        verify,
        extra_args=["--repo-root", str(tmp_path), "--baseline", str(bl)],
        env={
            "PT_TREND_FAKE_MISSING_COUNT": "2",
            "PT_TREND_FAKE_MISSING_ITEMS": "[]",
        },
    )
    assert p.returncode == 0
    assert "Baseline: 2 missing targets" in p.stdout
    assert "Current:  2 missing targets" in p.stdout
    assert "PASS: No new missing targets (debt stable)" in p.stdout
    assert p.stderr == ""


def test_pass_when_debt_improved(tmp_path: Path) -> None:
    verify = _install_ops_tree(tmp_path)
    bl = _baseline_path(tmp_path)
    items = [
        {"source_file": "docs/a.md", "line_number": 1, "target": "t1", "link_text": None},
        {"source_file": "docs/b.md", "line_number": 2, "target": "t2", "link_text": None},
    ]
    bl.write_text(json.dumps({"missing_count": 2, "missing_items": items}), encoding="utf-8")
    p = _run(
        verify,
        extra_args=["--repo-root", str(tmp_path), "--baseline", str(bl)],
        env={
            "PT_TREND_FAKE_MISSING_COUNT": "1",
            "PT_TREND_FAKE_MISSING_ITEMS": json.dumps([items[0]]),
        },
    )
    assert p.returncode == 0
    assert "Current:  1 missing targets" in p.stdout
    assert "PASS: Docs debt IMPROVED!" in p.stdout
    assert p.stderr == ""


def test_fail_when_new_missing_targets(tmp_path: Path) -> None:
    verify = _install_ops_tree(tmp_path)
    bl = _baseline_path(tmp_path)
    base_items = [
        {"source_file": "docs/a.md", "line_number": 1, "target": "t1", "link_text": None},
    ]
    bl.write_text(
        json.dumps({"missing_count": 1, "missing_items": base_items}),
        encoding="utf-8",
    )
    cur_items = base_items + [
        {
            "source_file": "docs/new.md",
            "line_number": 9,
            "target": "missing",
            "link_text": None,
        },
    ]
    p = _run(
        verify,
        extra_args=["--repo-root", str(tmp_path), "--baseline", str(bl)],
        env={
            "PT_TREND_FAKE_MISSING_COUNT": "2",
            "PT_TREND_FAKE_MISSING_ITEMS": json.dumps(cur_items),
        },
    )
    assert p.returncode == 1
    assert "FAIL: NEW missing targets introduced" in p.stdout
    assert "New Missing Targets" in p.stdout
    assert "docs/new.md:9" in p.stdout
    assert p.stderr == ""


def test_verbose_runs_scan_with_stderr_suppressed_from_scanner(tmp_path: Path) -> None:
    verify = _install_ops_tree(tmp_path)
    bl = _baseline_path(tmp_path)
    bl.write_text(
        json.dumps({"missing_count": 0, "missing_items": []}),
        encoding="utf-8",
    )
    noisy = tmp_path / "scripts" / "ops" / "collect_docs_reference_targets_fullscan.py"
    noisy.write_text(
        """#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--output", "-o", required=True)
args = parser.parse_args()
print("scanner noise", file=sys.stderr)
count = int(os.environ["PT_TREND_FAKE_MISSING_COUNT"])
payload = {"missing_count": count, "missing_items": []}
Path(args.output).write_text(json.dumps(payload) + "\\n", encoding="utf-8")
""",
        encoding="utf-8",
    )
    noisy.chmod(0o755)
    p = _run(
        verify,
        extra_args=["--repo-root", str(tmp_path), "--baseline", str(bl), "--verbose"],
        env={"PT_TREND_FAKE_MISSING_COUNT": "0"},
    )
    assert p.returncode == 0
    assert "Running current full-scan" in p.stdout
    assert "scanner noise" in p.stderr
